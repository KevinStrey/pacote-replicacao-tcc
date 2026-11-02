"""Inventory step A: mapped releases, duplicates, linearity per feature (read-only git)."""
import json, subprocess, sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(r'C:\Users\Kevin Strey\Desktop\TCC-LPS-Prediction')
REPOS = ROOT / '1-Repositorios'
MAP = ROOT / '3-Mapeamento_features_simrel' / 'simrel_mapper' / 'output'
ALIAS = {'eclipse.cvs': 'org.eclipse.team.cvs'}
OUT = Path(sys.argv[1])

def git(repo, *a):
    return subprocess.run(['git', '-C', str(repo), *a], capture_output=True, text=True, encoding='utf-8', errors='replace')

feats = defaultdict(list)
for f in sorted(MAP.glob('*.json')):
    d = json.loads(f.read_text(encoding='utf-8'))
    for k, m in d['mappings'].items():
        feats[k].append((d['release'], d['date'], m.get('status'), m.get('commit'), m.get('version'), m.get('repository')))

res = {}
for feat, rows in sorted(feats.items()):
    repo_name = rows[0][5]
    folder = ALIAS.get(repo_name, repo_name)
    repo = REPOS / folder
    r = {'feature': feat, 'repository': repo_name, 'folder': folder, 'exists': repo.exists(),
         'n_releases': len(rows), 'bad_status': [x[0] for x in rows if x[2] != 'SUCCESS' or not x[3]]}
    ok = [x for x in rows if x[2] == 'SUCCESS' and x[3]]
    missing = [x[0] for x in ok if git(repo, 'cat-file', '-e', x[3] + '^{commit}').returncode]
    r['missing_commit'] = missing
    ok = [x for x in ok if x[0] not in missing]
    by = defaultdict(list)
    for x in ok:
        by[x[3]].append(x)
    ts = {c: int(git(repo, 'show', '-s', '--format=%ct', c).stdout.strip()) for c in by}
    # keep earliest simrel release per commit (as pilot: sorted by commit_ts, simrel_date)
    uniq = sorted(by, key=lambda c: (ts[c], min(x[1] for x in by[c])))
    r['n_unique'] = len(uniq)
    r['duplicates'] = {c[:8]: [x[0] for x in sorted(by[c], key=lambda x: x[1])] for c in uniq if len(by[c]) > 1}
    rel = {c: sorted(by[c], key=lambda x: x[1])[0][0] for c in uniq}
    anc = lambda a, b: git(repo, 'merge-base', '--is-ancestor', a, b).returncode == 0
    breaks = []
    for i in range(len(uniq) - 1):
        if not anc(uniq[i], uniq[i + 1]):
            breaks.append(i)
    r['n_breaks'] = len(breaks)
    # longest ancestor chain (DP), only if non-linear
    chain = uniq
    if breaks:
        n = len(uniq)
        A = [[False] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                A[i][j] = anc(uniq[i], uniq[j])
        best = [1] * n; prv = [-1] * n
        for j in range(n):
            for i in range(j):
                if A[i][j] and best[i] + 1 > best[j]:
                    best[j], prv[j] = best[i] + 1, i
        j = max(range(n), key=lambda k: (best[k], k)); chain = []
        while j >= 0:
            chain.append(uniq[j]); j = prv[j]
        chain = chain[::-1]
    off = [c for c in uniq if c not in chain]
    det = []
    for c in off:
        br = git(repo, 'branch', '-a', '--contains', c, '--format=%(refname:short)').stdout.split()
        tag = git(repo, 'describe', '--tags', '--contains', c).stdout.strip()
        ptag = git(repo, 'describe', '--tags', '--abbrev=0', c).stdout.strip()
        det.append({'release': rel[c], 'all': [x[0] for x in by[c]], 'commit': c[:8],
                    'date': subprocess.run(['git', '-C', str(repo), 'show', '-s', '--format=%cs', c], capture_output=True, text=True).stdout.strip(),
                    'branches': br[:6], 'n_branches': len(br), 'contained_in_tag': tag, 'prev_tag': ptag})
    r['off_mainline'] = det
    r['n_linear'] = len(chain)
    r['chain'] = [(rel[c], c) for c in chain]
    r['first'] = (rel[chain[0]], chain[0]); r['last'] = (rel[chain[-1]], chain[-1])
    gaps = [int(git(repo, 'rev-list', '--count', f'{a}..{b}').stdout) for a, b in zip(chain, chain[1:])]
    r['gaps_zero_or_small'] = sum(g == 0 for g in gaps)
    r['commits_total_interval'] = sum(gaps)
    res[feat] = r
    print(feat, folder, r['n_unique'], 'breaks', len(breaks), 'linear', len(chain), 'off', [d['release'] for d in det], flush=True)

OUT.write_text(json.dumps(res, indent=1), encoding='utf-8')
