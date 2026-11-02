"""Feature-level change proneness (PLANO_TREINO.md, seção 6.2), temporal protocol only.

Unit: feature F at test release r (r > T). Real change rate = methods of F that change in r -> next / methods of F in r
(change of EXISTING code; new methods are not counted). Real volume = number of methods that change.
Predictions are aggregations of the method-level model (no feature-level model is trained):
  score_medio   mean predicted probability of the methods of F (main measure: ranking)
  taxa_prevista methods predicted to change / methods
  risco_topo5   share of F's methods among the 5% highest scores of the whole SPL in r
  volume        methods predicted to change (compared with the real volume)
Naive baselines (no learning; information available at time r):
  persistencia     real rate (or volume) of F in its previous labelled release
  media_historica  mean real rate (or volume) of F in the training releases (<= T)
Evaluation per test release, among the features present (>= MIN_FEATURES): Spearman correlation between predicted and
real ordering and top-3 hit (|top3 predicted & top3 real| / 3); summary = mean over releases with a 95% bootstrap
interval over releases, and the paired difference to the persistence baseline (same releases, same resamples).
"""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

MIN_FEATURES = 3
MEASURES = {  # name -> (predicted column, real column)
    'taxa (score_medio)': ('score_medio', 'taxa_real'),
    'taxa (taxa_prevista)': ('taxa_prevista', 'taxa_real'),
    'taxa (risco_topo5)': ('risco_topo5', 'taxa_real'),
    'volume (mudancas_previstas)': ('mudancas_previstas', 'mudancas_reais'),
}
BASELINES = {
    'taxa (persistencia)': ('persist_taxa', 'taxa_real'),
    'taxa (media_historica)': ('hist_taxa', 'taxa_real'),
    'volume (persistencia)': ('persist_volume', 'mudancas_reais'),
    'volume (media_historica)': ('hist_volume', 'mudancas_reais'),
}


def real_table(y, feat, release, names, T):
    d = pd.DataFrame({'f': feat, 'release': release, 'y': y})
    g = d.groupby(['f', 'release']).y.agg(metodos_real='size', mudancas_reais='sum').reset_index()
    g['feature'] = [names[int(c)] for c in g.f]
    g['taxa_real'] = g.mudancas_reais / g.metodos_real
    g = g.drop(columns='f').sort_values(['feature', 'release'])
    g['persist_taxa'] = g.groupby('feature').taxa_real.shift(1)
    g['persist_volume'] = g.groupby('feature').mudancas_reais.shift(1)
    hist = g[g.release <= T].groupby('feature').agg(hist_taxa=('taxa_real', 'mean'), hist_volume=('mudancas_reais', 'mean'))
    return g.merge(hist, on='feature', how='left')


def per_release(d, pcol, rcol):
    out = []
    for r, g in d.dropna(subset=[pcol, rcol]).groupby('release'):
        if len(g) < MIN_FEATURES:
            continue
        rho = spearmanr(g[pcol], g[rcol]).statistic if g[pcol].nunique() > 1 and g[rcol].nunique() > 1 else np.nan
        top_p = set(g.nlargest(3, pcol).feature)
        top_r = set(g.nlargest(3, rcol).feature)
        out.append({'release': int(r), 'features': len(g), 'spearman': rho, 'acerto_top3': len(top_p & top_r) / 3})
    return pd.DataFrame(out, columns=['release', 'features', 'spearman', 'acerto_top3'])


def boot_mean(v, rng, n_boot):
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    if len(v) < 2:
        return np.nan, np.nan
    m = v[rng.integers(0, len(v), (n_boot, len(v)))].mean(axis=1)
    return float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))


def summarize(pr, ref, seed, n_boot):
    rng = np.random.default_rng(seed)
    lo, hi = boot_mean(pr.spearman, rng, n_boot)
    out = {'releases': len(pr), 'spearman_medio': pr.spearman.mean(), 'spearman_IC95_inf': lo, 'spearman_IC95_sup': hi,
           'acerto_top3_medio': pr.acerto_top3.mean()}
    if ref is not None:
        j = pr.merge(ref, on='release', suffixes=('', '_ref')).dropna(subset=['spearman', 'spearman_ref'])
        diff = (j.spearman - j.spearman_ref).to_numpy()
        lo, hi = boot_mean(diff, np.random.default_rng(seed), n_boot)
        out.update({'dif_vs_persistencia': diff.mean() if len(diff) else np.nan, 'dif_IC95_inf': lo,
                    'dif_IC95_sup': hi})
    return out


def analyse(jobs, y, feat, release, names, T, seed, n_boot):
    """jobs: list of job results (dicts) of the temporal protocol with 'por_feature_release'.
    Returns (summary, detail, ranking) DataFrames."""
    real = real_table(y, feat, release, names, T)
    test = real[real.release > T]
    refs = {'taxa': per_release(test, 'persist_taxa', 'taxa_real'),
            'volume': per_release(test, 'persist_volume', 'mudancas_reais')}
    summary, detail = [], []
    for name, (pcol, rcol) in BASELINES.items():
        pr = per_release(test, pcol, rcol)
        kind = name.split(' ')[0]
        summary.append({'id': 'BASELINE', 'medida': name, **summarize(
            pr, None if 'persistencia' in name else refs[kind], seed, n_boot)})
    for r in jobs:
        d = pd.DataFrame(r['por_feature_release']).merge(test.drop(columns='mudancas_reais'), on=['feature', 'release'],
                                                         how='left')
        assert (d.metodos == d.metodos_real).all(), 'contagem de métodos do job difere dos dados preparados'
        d['taxa_prevista'] = d.mudancas_previstas / d.metodos
        d['risco_topo5'] = d.topo5 / d.metodos
        base = {k: r[k] for k in ('id', 'fase', 'variante', 'conjunto', 'reamostragem', 'algoritmo')}
        detail.append(d.assign(**base))
        for name, (pcol, rcol) in MEASURES.items():
            pr = per_release(d, pcol, rcol)
            summary.append({**base, 'medida': name, **summarize(pr, refs[name.split(' ')[0]], seed, n_boot)})
    summary = pd.DataFrame(summary)
    detail = pd.concat(detail, ignore_index=True) if detail else pd.DataFrame()
    ranking = pd.DataFrame()
    main = summary[(summary.medida == 'taxa (score_medio)') & (summary.id != 'BASELINE')]
    if len(main) and main.spearman_medio.notna().any():
        best = main.loc[main.spearman_medio.idxmax(), 'id']
        b = detail[detail.id == best]
        ranking = b.groupby('feature').agg(taxa_real_media=('taxa_real', 'mean'),
                                           score_medio=('score_medio', 'mean'),
                                           mudancas_reais=('mudancas_reais', 'sum'),
                                           mudancas_previstas=('mudancas_previstas', 'sum'),
                                           releases=('release', 'nunique')).reset_index()
        hist = test.groupby('feature').agg(persistencia_media=('persist_taxa', 'mean'), hist_taxa=('hist_taxa', 'first'))
        ranking = ranking.merge(hist, on='feature', how='left')
        ranking['posicao_real'] = ranking.taxa_real_media.rank(ascending=False, method='min').astype(int)
        ranking['posicao_prevista'] = ranking.score_medio.rank(ascending=False, method='min').astype(int)
        ranking = ranking.sort_values('posicao_real').assign(id_modelo=best)
    return summary, detail, ranking
