"""Inventory step C: per unique mapped commit -> history roots reached, .java count, test-like count, top dirs."""
import json, re, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT = Path(r'C:\Users\Kevin Strey\Desktop\TCC-LPS-Prediction')
REPOS = ROOT / '1-Repositorios'
MAP = ROOT / '3-Mapeamento_features_simrel' / 'simrel_mapper' / 'output'
inv = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
out = {}
TESTISH = re.compile(r'(test|junit)', re.I)

def git(repo, *a):
    return subprocess.run(['git', '-C', str(repo), *a], capture_output=True, text=True, encoding='utf-8', errors='replace').stdout

rels = {}
for f in sorted(MAP.glob('*.json')):
    d = json.loads(f.read_text(encoding='utf-8'))
    for k, m in d['mappings'].items():
        rels.setdefault(k, []).append((d['date'], d['release'], m['commit']))

for feat, r in inv.items():
    repo = REPOS / r['folder']
    chain = {c for _, c in r['chain']}
    seen, rows = set(), []
    for date, rel, c in sorted(rels[feat]):
        if c in seen or git(repo, 'cat-file', '-t', c).strip() != 'commit':
            continue
        seen.add(c)
        roots = sorted(x[:8] for x in git(repo, 'rev-list', '--max-parents=0', c).split())
        fs = [p for p in git(repo, 'ls-tree', '-r', '--name-only', c).splitlines() if p.endswith('.java')]
        testish = [p for p in fs if any(TESTISH.search(x) for x in p.split('/')[:-1])]
        tops = Counter(p.split('/')[0] for p in fs)
        rows.append({'release': rel, 'commit': c[:8], 'in_chain': c in chain,
                     'date': git(repo, 'show', '-s', '--format=%cs', c).strip(),
                     'roots': roots, 'java': len(fs), 'testish': len(testish),
                     'tops': dict(tops.most_common(8)), 'n_tops': len(tops)})
    out[feat] = rows
    print(feat, len(rows), flush=True)
Path(sys.argv[2]).write_text(json.dumps(out, indent=1), encoding='utf-8')
