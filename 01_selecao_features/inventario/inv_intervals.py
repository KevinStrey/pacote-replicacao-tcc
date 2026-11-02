"""Inventory step F: per chain interval, non-merge commits and how many are older than the previous snapshot
(signature of histories imported by merge, which would be counted in that interval by `rev-list prev..cur`)."""
import json, subprocess, sys
from pathlib import Path

REPOS = Path(r'C:\Users\Kevin Strey\Desktop\TCC-LPS-Prediction\1-Repositorios')
inv = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))

def git(repo, *a):
    return subprocess.run(['git', '-C', str(repo), *a], capture_output=True, text=True, encoding='utf-8', errors='replace').stdout

out = {}
for feat, r in inv.items():
    repo = REPOS / r['folder']
    chain = r['chain']
    rows = []
    for (ra, a), (rb, b) in zip(chain, chain[1:]):
        ta = int(git(repo, 'show', '-s', '--format=%ct', a).strip())
        cts = [int(x) for x in git(repo, 'rev-list', '--no-merges', '--format=%ct', f'{a}..{b}').split() if x.isdigit() and len(x) == 10]
        old = sum(t <= ta for t in cts)
        rows.append((rb, len(cts), old))
    out[feat] = rows
    bad = [x for x in rows if x[2] > 0.2 * max(x[1], 1) and x[2] > 50]
    print(f'{feat}: intervals={len(rows)} commits={sum(x[1] for x in rows)} older_than_prev={sum(x[2] for x in rows)} suspicious={bad}', flush=True)
Path(sys.argv[2]).write_text(json.dumps(out), encoding='utf-8')
