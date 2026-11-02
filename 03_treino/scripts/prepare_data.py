"""Builds the training matrices from the 19 parquets (run once; idempotent).

Outputs in trabalho/prep/ (or prep_amostra/ with --amostra):
  X.npy        float64 [n x colunas] (estruturais + evolutivas, config order), NaN -> 0 (fillna(0), as in the pilot);
               float64 as in the pilot: float32 storage changed tree splits (validacao/EQUIVALENCIA_PILOTO.md)
  y.npy        int8 will_change;  release.npy int16 (global calendar index);  feature.npy int8 (code, meta.features)
  splits/<protocolo>__<variante>__{train,test}.npy   row indices (int64)
  meta.json    columns, features, counts, cut T, NaN/inf counts per column, data hashes, versions
Row order is deterministic: features in alphabetical order, rows sorted by (release, method_uid) within each feature.
Protocols (PLANO_TREINO.md, seção 6):
  temporal: train = release <= T, test = release > T; T = first release where the cumulative rows reach 70%.
  random  : stratified 70/30 (train_test_split, random_state = seed), as in the pilot; CV folds are drawn inside
            each job from the training indices (StratifiedKFold, shuffle, random_state = seed).
Variant sem_PTP_Scout_Mylyn (fase 3): same train/test assignment and same T, without the rows of those features.
Usage: python prepare_data.py [--amostra 0.01]
"""
import argparse
import sys
import time

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.model_selection import train_test_split

from common import DADOS, Log, Run, load_config, sha256, versions, write_json, read_json

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--amostra', type=float, default=None, help='fração da amostra estratificada (teste rápido)')
args = ap.parse_args()
cfg = load_config()
SEED = cfg['semente']
run = Run('teste_rapido' if args.amostra else 'principal')
log = Log(run.logs / 'prepare_data.log')
cols = cfg['colunas']
done = run.prep / 'meta.json'
if done.exists():
    log('preparação já concluída:', done)
    sys.exit(0)


def make_splits(prep, y, release, feat, features, log):
    (prep / 'splits').mkdir(exist_ok=True)
    counts = pd.Series(release).value_counts().sort_index()
    cum = counts.cumsum() / counts.sum()
    T = int(cum[cum >= cfg['protocolos']['temporal']['fracao_treino']].index[0])
    idx = np.arange(len(y))
    splits = {'temporal': (idx[release <= T], idx[release > T])}
    tr, te = train_test_split(idx, test_size=cfg['protocolos']['random']['fracao_teste'], random_state=SEED,
                              stratify=y)
    splits['random'] = (np.sort(tr), np.sort(te))
    f3 = cfg['fases']['fase3']
    excl = [features.index(f) for f in f3['excluir_features']]
    keep = ~np.isin(feat, excl)
    info = {}
    for proto, (tr, te) in splits.items():
        for var, (a, b) in {'principal': (tr, te), f3['variante']: (tr[keep[tr]], te[keep[te]])}.items():
            np.save(prep / 'splits' / f'{proto}__{var}__train.npy', a)
            np.save(prep / 'splits' / f'{proto}__{var}__test.npy', b)
            info[f'{proto}__{var}'] = {'treino': int(len(a)), 'treino_pos': int(y[a].sum()),
                                       'teste': int(len(b)), 'teste_pos': int(y[b].sum())}
            log(f'split {proto}__{var}: treino={len(a)} (pos={int(y[a].sum())}) teste={len(b)} '
                f'(pos={int(y[b].sum())})')
    return T, info


t0 = time.time()
if args.amostra:
    # stratified sample (feature x label) of the full prepared data
    full = Run('principal').prep
    if not (full / 'meta.json').exists():
        raise SystemExit('prepare a matriz completa antes da amostra')
    meta = read_json(full / 'meta.json')
    y = np.load(full / 'y.npy')
    feat = np.load(full / 'feature.npy')
    rng = np.random.default_rng(SEED)
    pick = []
    for code in np.unique(feat):
        for lab in (0, 1):
            g = np.nonzero((feat == code) & (y == lab))[0]
            k = max(1, int(round(len(g) * args.amostra))) if len(g) else 0
            pick.append(np.sort(rng.choice(g, k, replace=False)))
    pick = np.sort(np.concatenate(pick))
    X = np.load(full / 'X.npy', mmap_mode='r')
    np.save(run.prep / 'X.npy', np.ascontiguousarray(X[pick]))
    y, feat = y[pick], feat[pick]
    release = np.load(full / 'release.npy')[pick]
    for name, arr in (('y', y), ('feature', feat), ('release', release)):
        np.save(run.prep / f'{name}.npy', arr)
    meta.update({'amostra': args.amostra, 'linhas': int(len(y)), 'positivos': int(y.sum())})
    log(f'amostra {args.amostra}: {len(y)} linhas, {int(y.sum())} positivos')
else:
    manifest = {}
    mf = DADOS / 'MANIFESTO.sha256'
    if mf.exists():
        for line in mf.read_text(encoding='utf-8').splitlines():
            if line.strip():
                h, name = line.split(None, 1)
                manifest[name.strip().lstrip('*')] = h
    files = sorted(DADOS.glob('*-all-releases.parquet'))
    if len(files) != 19:
        raise SystemExit(f'esperados 19 parquets em {DADOS}, encontrados {len(files)}')
    need = ['feature', 'release', 'method_uid', 'will_change'] + cols
    sizes, features = [], []
    for p in files:
        names = set(pq.read_schema(p).names)
        miss = [c for c in need if c not in names]
        if miss:
            raise SystemExit(f'{p.name}: colunas ausentes {miss}')
        t = pq.read_table(p, columns=['feature'])
        fs = t.column('feature').unique().to_pylist()
        if len(fs) != 1:
            raise SystemExit(f'{p.name}: mais de uma feature {fs}')
        sizes.append(t.num_rows)
        features.append(fs[0])
    order = sorted(range(len(files)), key=lambda i: features[i])
    files, sizes, features = [files[i] for i in order], [sizes[i] for i in order], [features[i] for i in order]
    n = sum(sizes)
    log(f'{len(files)} parquets, {n} linhas, {len(cols)} colunas de entrada')
    X = np.lib.format.open_memmap(run.prep / 'X.npy.tmp', mode='w+', dtype=np.float64, shape=(n, len(cols)))
    y = np.empty(n, np.int8)
    release = np.empty(n, np.int16)
    feat = np.empty(n, np.int8)
    nan_counts = dict.fromkeys(cols, 0)
    inf_counts = dict.fromkeys(cols, 0)
    per_feature = {}
    pos = 0
    for code, (p, size, fname) in enumerate(zip(files, sizes, features)):
        df = pd.read_parquet(p, columns=need)
        if df['will_change'].isna().any():
            raise SystemExit(f'{p.name}: will_change com nulos')
        if not set(df['will_change'].unique()) <= {0, 1}:
            raise SystemExit(f'{p.name}: will_change fora de {{0,1}}')
        if df.duplicated(['release', 'method_uid']).any():
            raise SystemExit(f'{p.name}: (release, method_uid) duplicado')
        df = df.sort_values(['release', 'method_uid'], kind='mergesort').reset_index(drop=True)
        y[pos:pos + size] = df['will_change'].to_numpy()
        release[pos:pos + size] = df['release'].to_numpy()
        feat[pos:pos + size] = code
        per_feature[fname] = {'arquivo': p.name, 'linhas': int(size), 'positivos': int(df['will_change'].sum()),
                              'release_min': int(df['release'].min()), 'release_max': int(df['release'].max()),
                              'sha256_manifesto': manifest.get(p.name)}
        for j, c in enumerate(cols):                      # column by column: low peak memory
            v = pd.to_numeric(df[c], errors='coerce').to_numpy(dtype=np.float64)
            nan_counts[c] += int(np.isnan(v).sum())
            inf_counts[c] += int(np.isinf(v).sum())
            X[pos:pos + size, j] = np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0)
            del df[c]
        log(f'{fname}: {size} linhas, {per_feature[fname]["positivos"]} positivos')
        pos += size
        del df
    X.flush()
    del X
    import os
    os.replace(run.prep / 'X.npy.tmp', run.prep / 'X.npy')
    for name, arr in (('y', y), ('feature', feat), ('release', release)):
        np.save(run.prep / f'{name}.npy', arr)
    meta = {'colunas': cols, 'features': features, 'linhas': int(n), 'positivos': int(y.sum()),
            'por_feature': per_feature, 'nan_por_coluna': {k: v for k, v in nan_counts.items() if v},
            'inf_por_coluna': {k: v for k, v in inf_counts.items() if v}, 'versoes': versions(),
            'sha256_manifesto': sha256(mf) if mf.exists() else None}
    log(f'NaN substituídos por 0: {meta["nan_por_coluna"] or "nenhum"}; inf: {meta["inf_por_coluna"] or "nenhum"}')

T, info = make_splits(run.prep, y, release, feat, meta['features'], log)
cal = DADOS / 'calendario.csv'
meta['corte_temporal'] = T
if cal.exists():
    c = pd.read_csv(cal)
    meta['calendario'] = c.to_dict(orient='records')
meta['splits'] = info
meta['segundos'] = round(time.time() - t0, 1)
write_json(done, meta)
log(f'corte temporal T = {T}; preparação concluída em {meta["segundos"]} s')
