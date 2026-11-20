"""Hypothesis tests of the thesis: Kruskal-Wallis, pairwise Mann-Whitney with Bonferroni and Vargha-Delaney A12.

Replaces testes_hipoteses.py (permutation and paired bootstrap). Unit of observation: one value per test release
(metricas_por_release.py); at the feature level, one Spearman correlation per test release.
Same procedure as cpmp/9.history_ml/statistical_analysis.py (roses): Kruskal-Wallis over the groups, pairwise
two-sided Mann-Whitney (Wilcoxon rank-sum) with Bonferroni correction, and A12 as effect size.

Analyses (each for PR-AUC and ROC-AUC unless noted):
 QP1  metodo_acaso__<protocolo>   best configuration of each algorithm + random classifier
 QP2  fator_<fator>__temporal     the 84 temporal configurations grouped by algorithm / metric set / resampling
 QP3  feature_ordem               Spearman per release: best configuration of each algorithm at the feature level,
                                  persistence, historical mean and a random order
 QP4  fator_<fator>__feature      Spearman per release of the 84 temporal configurations, grouped by algorithm /
                                  metric set / resampling
 QP5  identidade__<protocolo>     main model restricted to the rows of the variant x variant without PTP/Scout/Mylyn
(Research questions as numbered in the thesis after the 2026-11-11 revision.)
Outputs (resultados/kruskal/): kw.csv (one row per Kruskal-Wallis test), pares.csv (every pairwise comparison),
grupos.csv (mean, sd, median, n of each group) and valores.csv (the values of each group, for the box plots).
Usage: python testes_kruskal.py
"""
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kruskal, mannwhitneyu

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / 'resultados_e_logs' / 'saida' / 'resultados'
OUT = RES / 'kruskal'
OUT.mkdir(exist_ok=True)
SEED, ALPHA = 42, 0.05
METS = {'pr_auc': 'PR-AUC', 'roc_auc': 'ROC-AUC'}

kw_rows, pair_rows, group_rows, value_rows = [], [], [], []


def a12(x, y):
    """Vargha-Delaney A12: probability that a value of x is larger than a value of y (ties count one half)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    gt = (x[:, None] > y[None, :]).sum()
    eq = (x[:, None] == y[None, :]).sum()
    return float((gt + 0.5 * eq) / (len(x) * len(y)))


def magnitude(a):
    d = abs(a - 0.5)
    return 'insignificante' if d < 0.06 else 'pequeno' if d < 0.14 else 'médio' if d < 0.21 else 'grande'


def analyse(name, pergunta, metrica, groups, pairs=None):
    """groups: {label: values}. pairs: list of (a, b) to compare (default: every pair); Bonferroni over them."""
    groups = {k: np.asarray(v, float) for k, v in groups.items()}
    groups = {k: v[~np.isnan(v)] for k, v in groups.items()}
    for k, v in groups.items():
        group_rows.append(dict(analise=name, metrica=metrica, grupo=k, n=len(v), media=v.mean(), dp=v.std(ddof=1),
                               mediana=np.median(v), minimo=v.min(), maximo=v.max()))
        value_rows.extend(dict(analise=name, metrica=metrica, grupo=k, valor=x) for x in v)
    if len(groups) > 2:
        h, p = kruskal(*groups.values())
    else:                                            # two groups: Kruskal-Wallis reduces to Mann-Whitney
        h, p = kruskal(*groups.values())
    kw_rows.append(dict(analise=name, pergunta=pergunta, metrica=metrica, grupos=len(groups),
                        n_total=int(sum(len(v) for v in groups.values())), H=h, gl=len(groups) - 1, p=p,
                        rejeita=bool(p < ALPHA)))
    pairs = pairs or list(itertools.combinations(groups, 2))
    for a, b in pairs:
        u, pu = mannwhitneyu(groups[a], groups[b], alternative='two-sided')
        e = a12(groups[a], groups[b])
        pair_rows.append(dict(analise=name, metrica=metrica, a=a, b=b, n_a=len(groups[a]), n_b=len(groups[b]), U=u,
                              p=pu, comparacoes=len(pairs), p_bonferroni=min(1.0, pu * len(pairs)),
                              significativo=bool(min(1.0, pu * len(pairs)) < ALPHA), A12=e, magnitude=magnitude(e)))
    print(f'{name:34} {metrica:8} k={len(groups):2d} H={h:8.2f} p={p:.2e}', flush=True)


m = pd.read_csv(RES / 'metricas_por_release.csv', keep_default_na=False, na_values=[''])
m['restrito'] = m['restrito'].fillna('')
tests = pd.read_csv(RES / 'resultados_teste.csv')
best = {b['protocolo']: b['origem'] for b in json.loads((RES / 'fase3_selecao.json').read_text(encoding='utf-8'))}
allf = m[(m.feature == 'TODAS') & (m.restrito == '')]
ALG = {'LightGBM': 'LightGBM', 'MLP': 'MLP', 'LogisticRegression': 'Regr. log.', 'XGBoost': 'XGBoost',
       'LinearSVC': 'SVM linear', 'RandomForest': 'RF', 'DT': 'DT'}

# ---------------------------------------------------------------- QP1: best configuration of each algorithm x chance
for proto in ('temporal', 'random'):
    t = tests[(tests.protocolo == proto) & (tests.variante == 'principal')]
    top = t.sort_values('PR AUC (AP)', ascending=False).drop_duplicates('algoritmo')
    for met in METS:
        g = {ALG[r.algoritmo]: allf[allf.id == r.id].sort_values('release')[met].to_numpy() for r in top.itertuples()}
        g['Aleatório'] = allf[allf.id == f'ALEATORIO__{proto}'].sort_values('release')[met].to_numpy()
        analyse(f'metodo_acaso__{proto}', 'QP1', met, g)
    top[['id', 'algoritmo', 'conjunto', 'reamostragem', 'PR AUC (AP)', 'ROC AUC score']].to_csv(
        OUT / f'melhores__{proto}.csv', index=False)

# ---------------------------------------------------------------- QP2: factors (all the temporal configurations)
tp = allf[(allf.protocolo == 'temporal') & (allf.variante == 'principal') & (allf.algoritmo != 'Aleatório')]
assert tp.id.nunique() == 84, tp.id.nunique()
for fator in ('algoritmo', 'conjunto', 'reamostragem'):
    for met in METS:
        g = {(ALG[k] if fator == 'algoritmo' else k): v[met].to_numpy() for k, v in tp.groupby(fator)}
        analyse(f'fator_{fator}__temporal', 'QP2', met, g)

# ---------------------------------------------------------------- QP3: order of the features (Spearman per release)
fr = pd.read_csv(RES / 'nivel_feature_por_release.csv')
summ = pd.read_csv(RES / 'nivel_feature_resumo.csv')


def rho_by_release(df, pcol, rcol='taxa_real'):
    out = {}
    for rel, gr in df.dropna(subset=[pcol, rcol]).groupby('release'):
        if gr[pcol].nunique() > 1 and gr[rcol].nunique() > 1:
            out[rel] = gr[pcol].rank().corr(gr[rcol].rank())
    return out


cfgs = summ[(summ.id != 'BASELINE') & (summ.medida == 'taxa (score_medio)')].copy()
# best configuration of each algorithm = highest MEDIAN Spearman over the test releases (advisor review, 2026-11-19;
# before: highest mean). Ties are broken by the mean.
cfgs['spearman_mediana'] = [float(np.median(list(rho_by_release(fr[fr.id == i], 'score_medio').values())))
                            for i in cfgs.id]
top_f = cfgs.sort_values(['spearman_mediana', 'spearman_medio'], ascending=False).drop_duplicates('algoritmo')
g = {}
for r in top_f.itertuples():
    rho = rho_by_release(fr[fr.id == r.id], 'score_medio')
    assert abs(np.mean(list(rho.values())) - r.spearman_medio) < 1e-9, r.id
    g[ALG[r.algoritmo]] = np.array([rho[k] for k in sorted(rho)])
fb = fr[fr.id == top_f.iloc[0].id]
for label, col, med in (('Persistência', 'persist_taxa', 'taxa (persistencia)'),
                        ('Média histórica', 'hist_taxa', 'taxa (media_historica)')):
    rho = rho_by_release(fb, col)
    assert abs(np.mean(list(rho.values())) - summ[summ.medida == med].spearman_medio.iloc[0]) < 1e-9, label
    g[label] = np.array([rho[k] for k in sorted(rho)])
rng = np.random.default_rng(SEED)
rnd = fb.dropna(subset=['taxa_real']).copy()
rnd['sorteio'] = rng.random(len(rnd))
rho = rho_by_release(rnd, 'sorteio')
g['Aleatório'] = np.array([rho[k] for k in sorted(rho)])
analyse('feature_ordem', 'QP3', 'spearman', g)
top_f[['id', 'algoritmo', 'conjunto', 'reamostragem', 'spearman_medio', 'spearman_mediana']].to_csv(
    OUT / 'melhores__feature.csv', index=False)

# ---------------------------------------------------------------- QP4: factors at the feature level
rows = []
for r in cfgs.itertuples():
    rho = rho_by_release(fr[fr.id == r.id], 'score_medio')
    assert abs(np.mean(list(rho.values())) - r.spearman_medio) < 1e-9, r.id
    rows += [dict(algoritmo=r.algoritmo, conjunto=r.conjunto, reamostragem=r.reamostragem, release=k, spearman=v)
             for k, v in rho.items()]
sp = pd.DataFrame(rows)
assert len(cfgs) == 84 and len(sp) == 84 * 17, (len(cfgs), len(sp))
for fator in ('algoritmo', 'conjunto', 'reamostragem'):
    g = {(ALG[k] if fator == 'algoritmo' else k): v.spearman.to_numpy() for k, v in sp.groupby(fator)}
    analyse(f'fator_{fator}__feature', 'QP4', 'spearman', g)

# ---------------------------------------------------------------- impact of the identity breaks
for proto in ('temporal', 'random'):
    var = tests[(tests.protocolo == proto) & (tests.variante != 'principal')].id.iloc[0]
    for met in METS:
        a = m[(m.id == best[proto]) & (m.restrito != '') & (m.feature == 'TODAS')].sort_values('release')[met]
        b = m[(m.id == var) & (m.feature == 'TODAS')].sort_values('release')[met]
        analyse(f'identidade__{proto}', 'QP5', met, {'Principal (restrito)': a.to_numpy(), 'Sem PTP, Scout e Mylyn': b.to_numpy()})

pd.DataFrame(kw_rows).to_csv(OUT / 'kw.csv', index=False)
pd.DataFrame(pair_rows).to_csv(OUT / 'pares.csv', index=False)
pd.DataFrame(group_rows).to_csv(OUT / 'grupos.csv', index=False)
pd.DataFrame(value_rows).to_csv(OUT / 'valores.csv', index=False)
print('gravado', OUT.relative_to(ROOT))
