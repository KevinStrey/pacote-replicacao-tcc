"""Audit of the code scope (M9, M10, M14): for the first and last snapshot of each feature, counts .java per class
(prod / test / example / out of the CVS scope) and lists the excluded directories (the component that triggered the
rule). Output: output/escopo.csv and output/escopo_excluidos.txt"""
import csv
import subprocess
from collections import Counter, defaultdict

from features import FEATURES, OUT, PKG_ROOTS, REPOS, classify, is_production_java

rows = list(csv.DictReader(open(OUT / 'mapeamento.csv', encoding='utf-8')))
snaps = defaultdict(list)
for r in rows:
    if r['status'] == 'snapshot':
        snaps[r['feature']].append(r)


def trigger(path):
    """Directory component that made the file non-production."""
    parts = path.split('/')[:-1]
    for i, c in enumerate(parts):
        if c in PKG_ROOTS or c.startswith('src'):
            return '/'.join(parts[:i + 1])
        if classify('/'.join(parts[:i + 1]) + '/X.java', FEAT[0]) != 'prod':
            return c
    return '/'.join(parts)


out, txt = [], []
FEAT = [None]
for feat in FEATURES:
    ss = snaps.get(feat)
    if not ss:
        continue
    txt.append(f'\n######## {feat}')
    for lab, r in (('primeiro', ss[0]), ('ultimo', ss[-1])):
        files = [p for p in subprocess.run(['git', '-C', str(REPOS / r['repository']), 'ls-tree', '-r', '--name-only',
                                            r['commit']], capture_output=True, text=True, encoding='utf-8',
                                           errors='replace').stdout.splitlines() if p.endswith('.java')]
        cnt, exc = Counter(), defaultdict(Counter)
        for p in files:
            k = classify(p, feat)
            if k == 'prod' and not is_production_java(p, feat):
                k = 'fora_escopo'
            cnt[k] += 1
            if k in ('test', 'example'):
                exc[k][trigger(p)] += 1
        out.append(dict(feature=feat, snapshot=lab, tag=r['tag'], commit=r['commit'][:9], java=len(files),
                        prod=cnt['prod'], test=cnt['test'], example=cnt['example'], fora_escopo=cnt['fora_escopo']))
        txt.append(f'  {lab} {r["tag"]}: java={len(files)} prod={cnt["prod"]} test={cnt["test"]} '
                   f'example={cnt["example"]} fora_escopo={cnt["fora_escopo"]}')
        if exc['example']:
            txt.append('    exemplos/releng excluidos: ' + ', '.join(f'{k}:{v}' for k, v in exc['example'].most_common()))
with open(OUT / 'escopo.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)
(OUT / 'escopo_excluidos.txt').write_text('\n'.join(txt), encoding='utf-8')
print('\n'.join(txt))
