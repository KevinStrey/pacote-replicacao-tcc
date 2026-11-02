"""Measures equivalent commits (same change applied twice: cherry-pick, rebase, "squashed merge") among the commits
counted by s04/s05 in each feature. Two commits are equivalent when `git patch-id --stable` of their diff (restricted to
the production .java files that the feature counts) is identical.
Output: data/commit_duplicates.csv per feature and a summary line per feature."""
import subprocess
import sys
from collections import defaultdict

import pandas as pd

from config import FEATURES, Paths

feats = sys.argv[1:] or list(FEATURES)
for f in feats:
    P = Paths(f)
    cc_path = P.data / 'methods' / 'commit_changes.csv'
    mc_path = P.data / 'method_changes.parquet'
    if not cc_path.exists() or not mc_path.exists():
        continue
    cc = pd.read_csv(cc_path)
    mc = pd.read_parquet(mc_path)
    counted = set(mc['commit'])                    # commits that changed at least one method
    rows = []
    for c, g in cc[cc['commit'].isin(counted)].groupby('commit'):
        paths = sorted(set(g['old_path'].dropna()) | set(g['new_path'].dropna()))
        # very large commits: whole-commit diff (avoids the Windows command-line limit; stricter equivalence)
        spec = ['--', *paths] if sum(len(p) for p in paths) < 20000 else []
        diff = subprocess.run(['git', '-C', str(P.repo), 'diff', '-M', g['parent'].iloc[0], c, *spec],
                              capture_output=True).stdout
        pid = subprocess.run(['git', '-C', str(P.repo), 'patch-id', '--stable'], input=diff,
                             capture_output=True).stdout.decode().split()
        rows.append((c, int(g['release'].iloc[0]), pid[0] if pid else ''))
    d = pd.DataFrame(rows, columns=['commit', 'release', 'patch_id'])
    d['ts'] = [int(subprocess.run(['git', '-C', str(P.repo), 'show', '-s', '--format=%ct', c], capture_output=True,
                                  text=True).stdout or 0) for c in d['commit']]
    d = d.sort_values('ts')
    d['duplicate_of'] = ''
    first = {}
    for i, r in d.iterrows():
        if r.patch_id and r.patch_id in first:
            d.at[i, 'duplicate_of'] = first[r.patch_id]
        elif r.patch_id:
            first[r.patch_id] = r.commit
    d.to_csv(P.data / 'commit_duplicates.csv', index=False)
    dup = d[d.duplicate_of != '']
    ev = mc[mc['commit'].isin(dup['commit'])]
    print(f'{f}: commits que mudaram métodos={len(d)} | equivalentes (repetidos)={len(dup)} '
          f'({100 * len(dup) / max(len(d), 1):.1f}%) | mudanças método×commit afetadas={len(ev)} de {len(mc)} '
          f'({100 * len(ev) / max(len(mc), 1):.1f}%)', flush=True)
