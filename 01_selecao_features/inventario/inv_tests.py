"""Inventory step B: test-like directories and .java counts at the first and last linear snapshot."""
import json, re, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT = Path(r'C:\Users\Kevin Strey\Desktop\TCC-LPS-Prediction')
REPOS = ROOT / '1-Repositorios'
inv = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
only = sys.argv[2:]

TESTISH = re.compile(r'(test|junit|mock|fixture)', re.I)

def files(repo, c):
    return [p for p in subprocess.run(['git', '-C', str(repo), 'ls-tree', '-r', '--name-only', c],
            capture_output=True, text=True, encoding='utf-8', errors='replace').stdout.splitlines() if p.endswith('.java')]

for feat, r in inv.items():
    if only and feat not in only:
        continue
    repo = REPOS / r['folder']
    print(f'\n######## {feat} ({r["folder"]})')
    for lab, (rel, c) in (('FIRST', r['first']), ('LAST', r['last'])):
        fs = files(repo, c)
        # first test-like path component, with its prefix depth
        comp = Counter()
        for p in fs:
            parts = p.split('/')[:-1]
            for i, x in enumerate(parts):
                if TESTISH.search(x):
                    # generalize bundle names: keep suffix after last dot
                    comp[(i, re.sub(r'^.*\.', '*.', x) if '.' in x else x)] += 1
                    break
        n_testish = sum(comp.values())
        print(f'  {lab} {rel} {c[:8]}: java={len(fs)} testish={n_testish}')
        for (i, x), n in comp.most_common(25):
            print(f'     depth{i} {x!r}: {n}')
        tops = Counter(p.split('/')[0] for p in fs)
        print('     top-level dirs:', dict(tops.most_common(12)))
