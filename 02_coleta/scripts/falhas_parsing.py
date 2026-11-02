"""Files the JavaParser could not parse (s04) and the methods they removed from the training dataset.

Read-only over the collection outputs of each feature:
  data/methods/blob_methods.jsonl   failed file versions ("ok": false) and the exception
  data/methods/snapshot_files.csv   file version -> release and path
  data/methods/commit_changes.csv   file versions touched by commits (label / evolutionary metrics)
  data/ck/NN_<commit>_method.csv    methods of each snapshot by CK (JDT parser, reads the newer syntax)
  work/blobs/<sha>.java             source of each file version (to classify the cause by the failing line)
Only the releases present in each feature's training parquet (<feature>-all-releases.parquet) are counted.

Writes 5-Coleta_features/falhas_parsing/: arquivos.csv (one row per feature x file), metodos.csv (one row per
feature x release x method) and resumo.csv (per feature and cause).
Usage: python 5-Coleta_features/scripts/falhas_parsing.py
"""
import ast
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent
sys.path.insert(0, str(BASE / 'mapeamento'))
from features import is_template  # noqa: E402

OUT = BASE / 'falhas_parsing'
OUT.mkdir(exist_ok=True)
meta = json.loads((ROOT / 'predições' / 'prep' / 'meta.json').read_text(encoding='utf-8'))
por_feature = meta['por_feature'] if isinstance(meta['por_feature'], dict) else ast.literal_eval(meta['por_feature'])
DIRS = {f: f.replace(' ', '_') for f in meta['features']}

RULES = [(r'^(<<<<<<<|=======|>>>>>>>)', 'marcador de conflito de merge'),
         (r'\bsealed\b|\bpermits\b', 'sealed/permits (Java 17)'),
         (r'"[^"]*\\s', 'escape \\s em texto (Java 15)'),
         (r'case\s+null\b', 'case null em switch (Java 21)'),
         (r'case\s+[A-Z]\w*(<[^>]*>)?\s+\w+\s*(->|:|when)', 'padrão de tipo em switch (Java 21)'),
         (r'(^|[(,\s])_\s*(->|[,)])', '_ como parâmetro de lambda (Java 22)')]


def cause(err, path, blob_file):
    """Cause of the failure, from the source line the exception points to."""
    if is_template(path):
        return 'modelo de geração de código (M22)', ''
    if not path.endswith('.java'):
        return 'arquivo não Java', ''
    m = re.search(r'line (\d+)', err.split('\n')[0])
    try:
        src = blob_file.read_text(encoding='utf-8', errors='replace').split('\n')
        line = src[int(m.group(1)) - 1].strip() if m else ''
    except (OSError, IndexError):
        line = ''
    for rx, name in RULES:
        if re.search(rx, line):
            return name, line
    return 'erro de sintaxe no próprio código', line


arquivos, metodos, amostras = [], [], {}
for feat, d in DIRS.items():
    m = BASE / d / 'data' / 'methods'
    failed = {}
    with open(m / 'blob_methods.jsonl', encoding='utf-8') as fh:
        for line in fh:
            if '"ok":false' in line[:80]:
                r = json.loads(line)
                failed[r['id']] = r['error']
    if not failed:
        continue
    rels_treino = set(pd.read_parquet(BASE / d / 'data' / por_feature[feat]['arquivo'], columns=['release']).release.unique())
    sf = pd.read_csv(m / 'snapshot_files.csv')
    sf = sf[sf.blob.isin(failed.keys())]
    cc = pd.read_csv(m / 'commit_changes.csv')
    cc = cc[cc.old_blob.isin(failed.keys()) | cc.new_blob.isin(failed.keys())]

    # methods of the failed files, read from CK in each affected release of the training dataset
    ck_files = {int(p.name[:2]): p for p in (BASE / d / 'data' / 'ck').glob('*_method.csv')}
    n_met = defaultdict(int)
    rel_used = defaultdict(set)
    for rel, g in sf.groupby('release'):
        if rel not in rels_treino:
            continue
        paths = set(g.path)
        ck = pd.read_csv(ck_files[rel], usecols=['file', 'class', 'method'], dtype=str).dropna(subset=['file'])
        rp = ck.file.str.replace('\\', '/', regex=False).str.extract(r'/work/[^/]+/[^/]+/(.*)$', expand=False)
        keep = rp.isin(paths) & ~ck['class'].str.contains(r'\$\d', regex=True)   # without anonymous classes
        hit = ck[keep].assign(path=rp[keep])
        for p, h in hit.groupby('path'):
            n_met[p] += len(h)
        for p in paths:
            rel_used[p].add(rel)
        metodos.append(hit.assign(feature=feat, release=rel)[['feature', 'release', 'path', 'class', 'method']])

    # every path with a failed version, in a snapshot or in a commit (old or new side)
    blobs_of = defaultdict(set)
    for p, b in zip(sf.path, sf.blob):
        blobs_of[p].add(b)
    for side in ('old', 'new'):
        for p, b in zip(cc[f'{side}_path'], cc[f'{side}_blob']):
            if b in failed:
                blobs_of[p].add(b)
    for p, blobs in blobs_of.items():
        b0 = sorted(blobs)[0]
        c, src_line = cause(failed[b0], p, BASE / d / 'work' / 'blobs' / f'{b0}.java')
        amostras.setdefault((feat, c), (p, failed[b0].split('\n')[0][:120], src_line[:120]))
        rels = sorted(rel_used.get(p, ()))
        arquivos.append({'feature': feat, 'path': p, 'causa': c, 'linha_com_erro': src_line[:200],
                         'releases_no_treino': len(rels), 'primeira': rels[0] if rels else None,
                         'ultima': rels[-1] if rels else None, 'metodos_linhas': n_met.get(p, 0),
                         'mudancas_em_commits': int(((cc.new_path == p) | (cc.old_path == p)).sum())})
    print(f'{feat:15} versões com falha: {len(failed):4} | arquivos: {len(blobs_of):4}', flush=True)

arq = pd.DataFrame(arquivos)
arq.to_csv(OUT / 'arquivos.csv', index=False)
met = pd.concat(metodos) if metodos else pd.DataFrame()
met.to_csv(OUT / 'metodos.csv', index=False)
linhas = {f: por_feature[f]['linhas'] for f in DIRS}
res = (arq.groupby(['feature', 'causa'])
          .agg(arquivos=('path', 'size'), arquivos_no_treino=('releases_no_treino', lambda s: int((s > 0).sum())),
               linhas_removidas=('metodos_linhas', 'sum'), mudancas_em_commits=('mudancas_em_commits', 'sum'))
          .reset_index())
if len(met):
    distintos = met.drop_duplicates(['feature', 'path', 'class', 'method']).merge(arq[['feature', 'path', 'causa']])
    res = res.merge(distintos.groupby(['feature', 'causa']).size().rename('metodos_distintos').reset_index(), how='left')
    res['metodos_distintos'] = res.metodos_distintos.fillna(0).astype(int)
res['linhas_feature'] = res.feature.map(linhas)
res['pct_linhas'] = 100 * res.linhas_removidas / res.linhas_feature
res.to_csv(OUT / 'resumo.csv', index=False)
pd.set_option('display.width', 220)
print(res.to_string())
print('total de linhas removidas:', int(res.linhas_removidas.sum()), 'de', meta['linhas'])
for k, v in amostras.items():
    print(k, *v, sep='\n    ')
