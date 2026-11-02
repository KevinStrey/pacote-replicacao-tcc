"""Share of the counted method changes (method_changes.parquet, after M26) that come from commits whose committer
date is earlier than the previous snapshot's commit date, i.e. branches merged into the main line late. Their change
is attributed to the interval in which the merge happened."""
import subprocess, sys
import pandas as pd
from config import FEATURES, Paths
for f in sys.argv[1:] or FEATURES:
    P = Paths(f)
    mc_p = P.data / 'method_changes.parquet'
    if not mc_p.exists():
        continue
    mc = pd.read_parquet(mc_p); tl = pd.read_csv(P.data / 'timeline.csv')
    ts = lambda c: int(subprocess.run(['git', '-C', str(P.repo), 'show', '-s', '--format=%ct', c], capture_output=True, text=True).stdout or 0)
    prev_ts = {int(r): ts(p) for r, p in zip(tl.release[1:], tl.commit[:-1])}
    commits = mc.commit.unique()
    out = subprocess.run(['git', '-C', str(P.repo), 'show', '-s', '--format=%H %ct', *commits[:1]], capture_output=True, text=True)
    cts = {}
    for i in range(0, len(commits), 200):
        o = subprocess.run(['git', '-C', str(P.repo), 'show', '-s', '--format=%H %ct', *commits[i:i + 200]], capture_output=True, text=True).stdout.split()
        cts.update({o[j]: int(o[j + 1]) for j in range(0, len(o), 2)})
    mc['late'] = [cts[c] < prev_ts.get(int(r), 0) for c, r in zip(mc.commit, mc.release)]
    late_days = [(prev_ts[int(r)] - cts[c]) / 86400 for c, r, l in zip(mc.commit, mc.release, mc.late) if l]
    med = pd.Series(late_days).median() if late_days else 0
    print(f'{f}: mudanças método×commit={len(mc)} | de commits anteriores ao snapshot anterior={int(mc.late.sum())} '
          f'({100 * mc.late.mean():.1f}%) | atraso mediano={med:.0f} dias', flush=True)
