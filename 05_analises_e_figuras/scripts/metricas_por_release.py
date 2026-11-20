"""PR-AUC and ROC-AUC of every saved prediction, per test release (local; nothing is retrained).

Unit of observation of the Kruskal-Wallis analysis (testes_kruskal.py): one value per test release.
 - every configuration (158 predictions): one row per release, over all the features;
 - the best configuration of each protocol (fase3_selecao.json), the phase-3 variants and the main models
   restricted to the variant's rows: also one row per feature x release;
 - a random classifier (scores drawn uniformly, seed 42) on the test set of each protocol: id ALEATORIO__<protocolo>.
The whole-test-set metrics are checked against resultados_teste.csv (difference < 1e-9).
Output: resultados_e_logs/saida/resultados/metricas_por_release.csv
Usage: python metricas_por_release.py
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[2]
PRED = ROOT / 'predições'
RES = ROOT / 'resultados_e_logs' / 'saida' / 'resultados'
SEED = 42

y_all = np.load(PRED / 'prep' / 'y.npy')
REL = np.load(PRED / 'prep' / 'release.npy')
FEAT = np.load(PRED / 'prep' / 'feature.npy')
META = json.loads((PRED / 'prep' / 'meta.json').read_text(encoding='utf-8'))
NAMES = META['features']
EXCL = [NAMES.index(f) for f in ('PTP', 'Scout', 'Mylyn')]


def ap_auc(y, s):
    """Average precision and ROC-AUC with the same definitions as scikit-learn (ties share one threshold)."""
    n, p = len(y), int(y.sum())
    if p == 0 or p == n:
        return np.nan, np.nan
    order = np.argsort(-s, kind='stable')
    ys, ss = y[order], s[order]
    thr = np.r_[np.flatnonzero(np.diff(ss)), n - 1]
    tps = np.cumsum(ys)[thr]
    precision = tps / (thr + 1)
    recall = tps / p
    ap = float(np.sum(np.diff(np.r_[0.0, recall]) * precision))
    r = rankdata(s)
    auc = float((r[y == 1].sum() - p * (p + 1) / 2) / (p * (n - p)))
    return ap, auc


def split(proto, var):
    te = np.load(PRED / 'prep' / 'splits' / f'{proto}__principal__test.npy')
    if var != 'principal':
        te = te[~np.isin(FEAT[te], EXCL)]
    return te


def rows_for(jid, info, y, s, rel, feat, by_feature, restrito=''):
    out = []
    base = dict(id=jid, restrito=restrito, **info)
    for r in np.unique(rel):
        m = rel == r
        ap, auc = ap_auc(y[m], s[m])
        out.append(dict(base, release=int(r), feature='TODAS', linhas=int(m.sum()), positivos=int(y[m].sum()),
                        pr_auc=ap, roc_auc=auc))
        if by_feature:
            for f in np.unique(feat[m]):
                mf = m & (feat == f)
                ap, auc = ap_auc(y[mf], s[mf])
                out.append(dict(base, release=int(r), feature=NAMES[int(f)], linhas=int(mf.sum()),
                                positivos=int(y[mf].sum()), pr_auc=ap, roc_auc=auc))
    return out


if __name__ == '__main__':
    t0 = time.time()
    tests = pd.read_csv(RES / 'resultados_teste.csv')
    best = {b['protocolo']: b['origem'] for b in json.loads((RES / 'fase3_selecao.json').read_text(encoding='utf-8'))}
    rows = []
    cache = {}
    for t in tests.itertuples(index=False):
        key = (t.protocolo, t.variante)
        if key not in cache:
            te = split(*key)
            cache[key] = (te, y_all[te].astype(np.int8), REL[te], FEAT[te])
        te, y, rel, feat = cache[key]
        s = np.load(PRED / 'predicoes' / f'{t.id}.npz')['score'].astype(np.float64)
        assert len(s) == len(y), t.id
        ap, auc = ap_auc(y, s)
        ref = tests.loc[tests.id == t.id].iloc[0]
        assert abs(ap - ref['PR AUC (AP)']) < 1e-9 and abs(auc - ref['ROC AUC score']) < 1e-9, \
            f'{t.id}: {ap} {ref["PR AUC (AP)"]} {auc} {ref["ROC AUC score"]}'
        info = dict(fase=t.fase, protocolo=t.protocolo, variante=t.variante, conjunto=t.conjunto,
                    reamostragem=t.reamostragem, algoritmo=t.algoritmo)
        is_best = t.id in best.values() or t.variante != 'principal'
        rows += rows_for(t.id, info, y, s, rel, feat, by_feature=is_best)
        if t.id in best.values():           # main model on the rows of the phase-3 variant (same rows as the variant)
            keep = ~np.isin(feat, EXCL)
            rows += rows_for(t.id, info, y[keep], s[keep], rel[keep], feat[keep], by_feature=False,
                             restrito='sem_PTP_Scout_Mylyn')
        print(f'{len(rows):7d} linhas  {t.id}  ({time.time() - t0:.0f}s)', flush=True)
    rng = np.random.default_rng(SEED)
    for proto in ('temporal', 'random'):
        te, y, rel, feat = cache[(proto, 'principal')]
        s = rng.random(len(y))
        info = dict(fase='', protocolo=proto, variante='principal', conjunto='', reamostragem='', algoritmo='Aleatório')
        rows += rows_for(f'ALEATORIO__{proto}', info, y, s, rel, feat, by_feature=True)
    pd.DataFrame(rows).to_csv(RES / 'metricas_por_release.csv', index=False)
    print('gravado', (RES / 'metricas_por_release.csv').relative_to(ROOT), len(rows), f'({time.time() - t0:.0f}s)')
