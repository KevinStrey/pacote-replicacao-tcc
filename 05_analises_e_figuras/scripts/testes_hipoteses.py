"""Explicit hypothesis tests for the thesis (local, over the downloaded predictions; nothing is retrained).

1. Method level x chance (best configuration of each protocol x algorithm, Table 5):
   H0: the scores are independent of the labels (classifier at chance), i.e. PR-AUC = rate of positives and
   ROC-AUC = 0.5. Permutation test: the labels of the test set are shuffled B times (seed 42) and the metrics are
   recomputed; one-sided p = (1 + #{null >= observed}) / (B + 1).
2. Sensitivity analysis (phase 3): H0: delta = 0, delta = metric(variant) - metric(main model restricted to the same
   test rows). Paired bootstrap with the same resamples as the server (seed 42, B = 1000, metrics.bootstrap), checked
   against resultados/bootstrap/par__*.json; two-sided p = min(1, 2 (1 + #{delta <= 0}) / (B + 1)).
   The bootstrap of the best temporal model on the full test set is also replicated (check of the CI in Table 5).
3. Feature level x chance: H0: the predicted order of the features is unrelated to the real one (mean Spearman = 0).
   Permutation test: the predicted rates are shuffled among the features of each test release (10,000 times).
   Done for the best configuration, the persistence and the historical mean.
Outputs: resultados_e_logs/saida/resultados/testes_hipoteses.csv and testes_hipoteses_draws.npz (draws for the figures).
Usage: python testes_hipoteses.py
"""
import json
import os

import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
# Sorted, bootstrap and ci are taken verbatim from the server's metrics.py (the rest of that module needs sklearn)
_src = (ROOT / '6-Treino' / 'scripts' / 'metrics.py').read_text(encoding='utf-8')
exec(_src[_src.index('class Sorted'):], globals())

PRED = ROOT / 'predições'
RES = ROOT / 'resultados_e_logs' / 'saida' / 'resultados'
SEED, B, B_FEAT = 42, 1000, 10000
METS = ('PR AUC (AP)', 'ROC AUC score')

y_all = np.load(PRED / 'prep' / 'y.npy')
META = json.loads((PRED / 'prep' / 'meta.json').read_text(encoding='utf-8'))
FEAT = np.load(PRED / 'prep' / 'feature.npy')
EXCL = [META['features'].index(f) for f in ('PTP', 'Scout', 'Mylyn')]  # experimentos.yaml, fase3.excluir_features


def split(proto, var):
    """Test indices; the variant split was not downloaded and is rebuilt as in prepare_data.make_splits."""
    te = np.load(PRED / 'prep' / 'splits' / f'{proto}__principal__test.npy')
    if var != 'principal':
        te = te[~np.isin(FEAT[te], EXCL)]
        info = META['splits'][f'{proto}__{var}']
        assert len(te) == info['teste'] and int(y_all[te].sum()) == info['teste_pos'], f'split {proto}__{var}'
    return te


CACHE = RES / 'testes_hipoteses_cache'
CACHE.mkdir(exist_ok=True)
score = lambda jid: np.load(PRED / 'predicoes' / f'{jid}.npz')['score'].astype(np.float64)  # noqa: E731
tests = pd.read_csv(RES / 'resultados_teste.csv')
rows, draws = [], {}
t0 = time.time()


def permutation(srt, n_perm, seed):
    """Null distribution of the metrics with the labels shuffled (scores kept): no new sort is needed."""
    rng = np.random.default_rng(seed)
    y = srt.y.copy()
    out = {m: np.empty(n_perm) for m in METS}
    w = np.ones(len(y))
    for b in range(n_perm):
        srt.y = rng.permutation(y)
        for m, v in srt.metrics(w).items():
            if m in out:
                out[m][b] = v
    srt.y = y
    return out


# ---------------------------------------------------------------- 1. method level x chance
ic = pd.read_csv(RES / 'bootstrap_ic.csv')
SHARD = os.environ.get('SHARD')  # 'i/n': only fill the stage-1 cache for configurations i, i+n, ... and stop
for k, r in enumerate(ic.itertuples()):
    if SHARD and k % int(SHARD.split('/')[1]) != int(SHARD.split('/')[0]):
        continue
    cf = CACHE / f'{r.id}.npz'
    if cf.exists():  # stage 1 is slow (~5 min per configuration): reuse what a previous run computed
        z = np.load(cf, allow_pickle=True)
        rows += list(z['rows'])
        draws.update({k: z[k] for k in z.files if k != 'rows'})
        print('cache', r.id, flush=True)
        continue
    n_rows = len(rows)
    te = split(r.protocolo, 'principal')
    y = y_all[te]
    srt = Sorted(y, score(r.id))
    obs = srt.metrics(np.ones(len(y)))
    null = permutation(srt, B, SEED)
    for m in METS:
        ref = y.mean() if m == 'PR AUC (AP)' else 0.5
        n_ge = int((null[m] >= obs[m]).sum())
        rows.append({'teste': 'acaso_metodo', 'protocolo': r.protocolo, 'algoritmo': r.algoritmo, 'id': r.id,
                     'metrica': m, 'observado': obs[m], 'referencia_acaso': ref, 'nulo_media': null[m].mean(),
                     'nulo_p2.5': np.quantile(null[m], .025), 'nulo_p97.5': np.quantile(null[m], .975),
                     'nulo_max': null[m].max(), 'permutacoes_ge_observado': n_ge, 'B': B,
                     'p_valor': (1 + n_ge) / (B + 1)})
        draws[f'nulo|{r.id}|{m}'] = null[m]
    np.savez(cf, rows=np.array(rows[n_rows:], dtype=object), **{f'nulo|{r.id}|{m}': null[m] for m in METS})
    print(f'acaso {r.protocolo:8} {r.algoritmo:18} AP={obs["PR AUC (AP)"]:.4f} '
          f'(nulo máx {null["PR AUC (AP)"].max():.4f}) AUC={obs["ROC AUC score"]:.3f} '
          f'(nulo máx {null["ROC AUC score"].max():.3f})  {time.time() - t0:.0f}s', flush=True)

if SHARD:
    raise SystemExit(0)

# ---------------------------------------------------------------- 2. sensitivity (paired bootstrap, as on the server)
C2 = CACHE / 'etapa2.npz'
if C2.exists():
    z = np.load(C2, allow_pickle=True)
    rows += list(z['rows'])
    draws.update({k: z[k] for k in z.files if k != 'rows'})
    print('cache etapa 2', flush=True)
n2, k2 = len(rows), set(draws)
for r in (tests[tests.fase == 'fase3'] if not C2.exists() else tests.iloc[:0]).itertuples():
    te_main, te_var = split(r.protocolo, 'principal'), split(r.protocolo, r.variante)
    pos = np.searchsorted(te_main, te_var)
    y = y_all[te_var]
    models = {'principal_restrito': Sorted(y, score(r.origem)[pos]), 'variante': Sorted(y, score(r.id))}
    d = bootstrap(models, len(y), B, SEED)
    cached = json.loads((RES / 'bootstrap' / f'par__{r.id}__B{B}.json').read_text(encoding='utf-8'))
    for m in METS:
        delta = d['variante'][m] - d['principal_restrito'][m]
        lo, hi = ci(delta)
        assert np.allclose([lo, hi], cached[f'diferenca|{m}'], atol=1e-12), f'IC difere do servidor: {r.id} {m}'
        obs = {k: s.metrics(np.ones(len(y)))[m] for k, s in models.items()}
        n_le = int((delta <= 0).sum())
        rows.append({'teste': 'sensibilidade', 'protocolo': r.protocolo, 'algoritmo': r.algoritmo, 'id': r.id,
                     'metrica': m, 'observado': obs['variante'] - obs['principal_restrito'],
                     'principal_restrito': obs['principal_restrito'], 'variante': obs['variante'],
                     'IC95_inf': lo, 'IC95_sup': hi, 'reamostras_delta_le_0': n_le, 'B': B,
                     'p_valor': min(1.0, 2 * (1 + n_le) / (B + 1))})
        draws[f'delta|{r.protocolo}|{m}'] = delta
    print(f'sensibilidade {r.protocolo}: IC reproduz o do servidor  {time.time() - t0:.0f}s', flush=True)

# best temporal model on the full test set: replicate the CI of Table 5 (check) and keep the draws
best = ic[ic.protocolo == 'temporal'].sort_values('PR AUC (AP)', ascending=False).iloc[0]
te = split('temporal', 'principal')
d = {'modelo': {m: draws[f'boot|{best.id}|{m}'] for m in METS}} if C2.exists() else bootstrap({'modelo': Sorted(y_all[te], score(best.id))}, len(te), B, SEED)
cached = json.loads((RES / 'bootstrap' / f'ic__{best.id}__B{B}.json').read_text(encoding='utf-8'))
for m in METS:
    assert np.allclose(ci(d['modelo'][m]), cached[f'modelo|{m}'], atol=1e-12)
    draws[f'boot|{best.id}|{m}'] = d['modelo'][m]
print('IC do melhor modelo temporal reproduz o do servidor', flush=True)
if not C2.exists():
    np.savez(C2, rows=np.array(rows[n2:], dtype=object), **{k: draws[k] for k in set(draws) - k2})

# ---------------------------------------------------------------- 3. feature level x chance
fr = pd.read_csv(RES / 'nivel_feature_por_release.csv')
summ = pd.read_csv(RES / 'nivel_feature_resumo.csv')
cfg = summ[(summ.id != 'BASELINE') & summ.medida.str.startswith('taxa')].sort_values('spearman_medio', ascending=False).iloc[0]
fb = fr[fr.id == cfg.id]


def rho_by_release(df, pcol, rcol='taxa_real'):
    out = {}
    for rel, g in df.dropna(subset=[pcol, rcol]).groupby('release'):
        if g[pcol].nunique() > 1 and g[rcol].nunique() > 1:
            out[rel] = g[pcol].rank().corr(g[rcol].rank())
    return out


rng = np.random.default_rng(SEED)
for name, pcol in (('modelo', 'score_medio'), ('persistencia', 'persist_taxa'), ('media_historica', 'hist_taxa')):
    obs = rho_by_release(fb, pcol)
    mean_obs = float(np.mean(list(obs.values())))
    ref = cfg.spearman_medio if name == 'modelo' else summ[summ.medida == f'taxa ({name})'].spearman_medio.iloc[0]
    assert abs(mean_obs - ref) < 1e-9, f'Spearman médio difere do nivel_feature_resumo: {name} {mean_obs} {ref}'
    groups = [g.dropna(subset=[pcol, 'taxa_real']) for _, g in fb.groupby('release')]
    groups = [g for g in groups if g[pcol].nunique() > 1 and g.taxa_real.nunique() > 1]
    ranks_real = [g.taxa_real.rank().to_numpy() for g in groups]
    ranks_pred = [g[pcol].rank().to_numpy() for g in groups]
    null = np.empty(B_FEAT)
    for b in range(B_FEAT):
        null[b] = np.mean([np.corrcoef(rng.permutation(p), r)[0, 1] for p, r in zip(ranks_pred, ranks_real)])
    n_ge = int((null >= mean_obs).sum())
    rows.append({'teste': 'acaso_feature', 'protocolo': 'temporal', 'algoritmo': name, 'id': cfg.id if name == 'modelo'
                 else '', 'metrica': 'Spearman médio', 'observado': mean_obs, 'referencia_acaso': 0.0,
                 'nulo_media': null.mean(), 'nulo_p2.5': np.quantile(null, .025), 'nulo_p97.5': np.quantile(null, .975),
                 'nulo_max': null.max(), 'permutacoes_ge_observado': n_ge, 'B': B_FEAT,
                 'p_valor': (1 + n_ge) / (B_FEAT + 1), 'releases': len(groups)})
    draws[f'nulo_feature|{name}'] = null
    print(f'feature {name:16} Spearman médio {mean_obs:.3f} (nulo máx {null.max():.3f}) p={(1 + n_ge) / (B_FEAT + 1):.4f}',
          flush=True)

pd.DataFrame(rows).to_csv(RES / 'testes_hipoteses.csv', index=False)
np.savez_compressed(RES / 'testes_hipoteses_draws.npz', **draws)
print('gravado', (RES / 'testes_hipoteses.csv').relative_to(ROOT), f'({time.time() - t0:.0f}s)')
