"""Overview charts of the per-feature analyses, temporal protocol (presentation; NOT in the thesis).

Two different questions are shown:
  A. Method level, split by feature: each global model scores every test method; the metrics are computed inside the
     methods of each feature (Table 6 of the thesis, now for every algorithm).
  B. Feature level (the core of the work): the method scores are averaged per feature x release, the features are
     ranked and the ranking is compared with the real change rate (Spearman), against the persistence baseline.

Inputs:  resultados_e_logs/saida/resultados/ (por_feature.csv, resultados_teste.csv, nivel_feature_*.csv)
         predições/predicoes + predições/prep (only for the bootstrap ties of chart f1)
Outputs: graficos_apresentacao/por_feature/ (PNG 300 dpi + SVG), visao_geral.png (all charts side by side) and
         empates_roc.csv.
Usage: python graficos_por_feature.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import rankdata  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PRED = ROOT / 'predições' / 'predicoes'
PREP = ROOT / 'predições' / 'prep'
RES = ROOT / 'resultados_e_logs' / 'saida' / 'resultados'
OUT = ROOT / 'graficos_apresentacao' / 'por_feature'
OUT.mkdir(parents=True, exist_ok=True)

# ---------------- modern style (same as graficos_predicoes.py) ----------------
INK, MUTED, GRID = '#1F2937', '#6B7280', '#E5E7EB'
plt.rcParams.update({
    'font.family': 'sans-serif', 'font.sans-serif': ['Segoe UI', 'Inter', 'Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 12, 'text.color': INK, 'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED,
    'axes.edgecolor': GRID, 'axes.linewidth': 1.0, 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.8, 'axes.axisbelow': True,
    'axes.titlesize': 14, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left', 'axes.titlepad': 12,
    'legend.frameon': False, 'legend.fontsize': 10, 'figure.facecolor': 'white', 'savefig.facecolor': 'white',
    'savefig.bbox': 'tight', 'savefig.dpi': 300, 'lines.linewidth': 2.4, 'lines.solid_capstyle': 'round',
})
ALG = {
    'LightGBM': ('LightGBM', '#E4572E'), 'XGBoost': ('XGBoost', '#F3A712'), 'MLP': ('MLP', '#7E57C2'),
    'LogisticRegression': ('Regressão logística', '#2E86AB'), 'LinearSVC': ('SVM linear', '#17BEBB'),
    'RandomForest': ('Random Forest', '#3BB273'), 'DT': ('Árvore de decisão', '#9CA3AF')}
SHORT = {'LightGBM': 'LightGBM', 'XGBoost': 'XGBoost', 'MLP': 'MLP', 'LogisticRegression': 'Regr. log.',
         'LinearSVC': 'SVM linear', 'RandomForest': 'RF', 'DT': 'DT'}
SEQ = 'Blues'
N_BOOT = 100


def br(v, nd=2):
    return f'{v:.{nd}f}'.replace('.', ',')


def pct(v, nd=0):
    return br(100 * v, nd) + '%'


def suptitle(fig, title, subtitle):
    fig._titulos = (title, subtitle)


def save(fig, name, note=None):
    if getattr(fig, '_titulos', None):
        fig.canvas.draw()
        top = max(ax.get_tightbbox().transformed(fig.transFigure.inverted()).y1 for ax in fig.axes
                  if ax.get_visible() and ax.get_label() != '<colorbar>')
        left = min(ax.get_position().x0 for ax in fig.axes if ax.get_visible())
        x0 = min(0.0, left - 0.06)
        fig.text(x0, top + 0.012, fig._titulos[1], fontsize=12, color=MUTED, ha='left', va='bottom')
        fig.text(x0, top + 0.055, fig._titulos[0], fontsize=18, fontweight='bold', ha='left', va='bottom')
    if note:
        fig.text(0.0, -0.02, note, fontsize=9.5, color=MUTED, ha='left', va='top', transform=fig.transFigure)
    for ext in ('png', 'svg'):
        fig.savefig(OUT / f'{name}.{ext}')
    plt.close(fig)
    print('ok', name)


# ---------------- data ----------------
t = pd.read_csv(RES / 'resultados_teste.csv')
t = t[(t.variante == 'principal') & (t.protocolo == 'temporal')]
best_cfg = t.sort_values('PR AUC (AP)', ascending=False).groupby('algoritmo').head(1).set_index('algoritmo')
ALGS = list(best_cfg.sort_values('PR AUC (AP)', ascending=False).index)      # thesis order (Table 4)
pf = pd.read_csv(RES / 'por_feature.csv')
pf = pf[(pf.protocolo == 'temporal') & (pf.variante == 'principal') & (pf.positivos > 0)]
pf['acaso'] = pf.positivos / pf.linhas
pf['lift'] = pf['PR AUC (AP)'] / pf.acaso
th = pf[pf.id.isin(best_cfg.id)].copy()
roc = th.pivot(index='feature', columns='algoritmo', values='ROC AUC score')[ALGS]
lift = th.pivot(index='feature', columns='algoritmo', values='lift')[ALGS]
info = th.drop_duplicates('feature').set_index('feature')[['linhas', 'positivos', 'acaso']]
order = roc['LightGBM'].sort_values(ascending=False).index
roc, lift, info = roc.loc[order], lift.loc[order], info.loc[order]

# ---- paired bootstrap over the methods of each feature: which algorithms tie with the best ROC-AUC ----
y_all = np.load(PREP / 'y.npy')
feat_all = np.load(PREP / 'feature.npy')
names = json.loads((PREP / 'meta.json').read_text(encoding='utf-8'))['features']
te = np.load(PREP / 'splits' / 'temporal__principal__test.npy')
yt, ft = y_all[te], feat_all[te]
scores = {a: np.load(PRED / f'{best_cfg.loc[a, "id"]}.npz')['score'].astype(np.float64) for a in ALGS}


def auc(y, s):
    r = rankdata(s)
    n1 = y.sum()
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y) - n1))


ties = []
rng = np.random.default_rng(42)
for fe in order:
    m = ft == names.index(fe)
    y = yt[m]
    pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
    best = roc.loc[fe].idxmax()
    diffs = {a: [] for a in ALGS}
    for _ in range(N_BOOT):                     # stratified resample keeps the positives count fixed
        idx = np.r_[rng.choice(pos, len(pos)), rng.choice(neg, len(neg))]
        yb = y[idx]
        vals = {a: auc(yb, scores[a][m][idx]) for a in ALGS}
        for a in ALGS:
            diffs[a].append(vals[best] - vals[a])
    for a in ALGS:
        d = np.array(diffs[a])
        ties.append({'feature': fe, 'algoritmo': a, 'roc': roc.loc[fe, a], 'melhor': a == best,
                     'empata_com_melhor': a == best or np.quantile(d, 0.025) <= 0})
    print('bootstrap', fe)
ties = pd.DataFrame(ties)
ties.to_csv(OUT / 'empates_roc.csv', index=False)
tie = ties.pivot(index='feature', columns='algoritmo', values='empata_com_melhor').loc[order, ALGS]
FEAT_NOTE = (f'Configuração de cada algoritmo = a da Tabela 5 do TCC. DataTools tem só {int(info.loc["DataTools", "positivos"])} '
             'métodos alterados no teste: seus valores são pouco confiáveis.')

# ================= A. method level, split by feature =================
# ---- f1: heatmap ROC-AUC feature x algorithm, best and ties marked ----
fig, ax = plt.subplots(figsize=(11, 8.2))
im = ax.imshow(roc.values, cmap=SEQ, vmin=0.45, vmax=0.95, aspect='auto')
for i, fe in enumerate(order):
    for j, a in enumerate(ALGS):
        v = roc.loc[fe, a]
        dark = v > 0.78
        best = a == roc.loc[fe].idxmax()
        ax.text(j, i, br(v, 3), ha='center', va='center', fontsize=10.5, fontweight='bold' if best else 'normal',
                color='white' if dark else INK)
        if tie.loc[fe, a]:
            ax.add_patch(plt.Rectangle((j - 0.46, i - 0.42), 0.92, 0.84, fill=False,
                                       ec=INK, lw=2.2 if best else 1.0, ls='-' if best else (0, (3, 2))))
ax.set_xticks(range(len(ALGS)), [SHORT[a] for a in ALGS])
ax.set_yticks(range(len(order)), [f'{fe}' for fe in order])
ax.xaxis.tick_top()
ax.tick_params(length=0, labelsize=11.5, colors=INK)
ax.grid(False)
for s in ax.spines.values():
    s.set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02, format=mtick.FuncFormatter(lambda v, _: br(v, 1)))
cb.outline.set_visible(False)
cb.set_label('ROC-AUC (0,5 = acaso)', color=MUTED)
suptitle(fig, 'Qual algoritmo acerta melhor os métodos de cada feature?',
         'ROC-AUC dentro de cada feature, protocolo temporal. Moldura cheia = melhor; tracejada = empate estatístico com o melhor')
save(fig, 'f1_mapa_roc_feature_x_algoritmo',
     'Empate: o intervalo de 95% (bootstrap pareado, 100 reamostragens) da diferença para o melhor inclui zero. '
     + FEAT_NOTE)

# ---- f2: dot plot, one row per feature ----
fig, ax = plt.subplots(figsize=(11, 8))
yy = np.arange(len(order))[::-1]
for i, fe in zip(yy, order):
    ax.plot([roc.loc[fe].min(), roc.loc[fe].max()], [i, i], color=GRID, lw=6, solid_capstyle='round', zorder=1)
for a in ALGS[::-1]:
    big = a == 'LightGBM'
    ax.scatter(roc[a], yy, s=110 if big else 55, color=ALG[a][1], ec='white', lw=1.5, zorder=4 if big else 3,
               label=ALG[a][0])
ax.axvline(0.5, ls=(0, (4, 4)), color=MUTED, lw=1.3)
ax.text(0.505, yy[0] + 0.6, 'acaso', color=MUTED, fontsize=10, va='bottom')
ax.set_yticks(yy, order)
ax.tick_params(axis='y', length=0, labelsize=11.5, colors=INK)
ax.set_xlabel('ROC-AUC dentro da feature')
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 1)))
ax.grid(axis='y', visible=False)
h, lab = ax.get_legend_handles_labels()
ax.legend(h[::-1], lab[::-1], loc='lower left', ncols=1, bbox_to_anchor=(1.0, 0.0))
suptitle(fig, 'Desempenho de cada algoritmo em cada feature',
         'Protocolo temporal; a faixa cinza mostra a distância entre o pior e o melhor algoritmo da feature')
save(fig, 'f2_pontos_roc_por_feature', FEAT_NOTE)

# ---- f3: wins and ties per algorithm ----
win = ties[ties.melhor].groupby('algoritmo').size().reindex(ALGS, fill_value=0)
tied = ties[ties.empata_com_melhor & ~ties.melhor].groupby('algoritmo').size().reindex(ALGS, fill_value=0)
o = (win + tied).sort_values(ascending=True).index
fig, ax = plt.subplots(figsize=(10.5, 5.5))
ax.barh([ALG[a][0] for a in o], win[o], color=[ALG[a][1] for a in o], height=0.62, label='Melhor da feature')
ax.barh([ALG[a][0] for a in o], tied[o], left=win[o], color=[ALG[a][1] for a in o], alpha=0.35, height=0.62,
        label='Empate estatístico com o melhor')
for k, a in enumerate(o):
    ax.text(win[a] + tied[a] + 0.15, k, f'{win[a]} melhor + {tied[a]} empate{"" if tied[a] == 1 else "s"}',
            va='center', fontsize=10.5, color=INK)
ax.set_xlim(0, len(order) + 3)
ax.set_xlabel(f'Número de features (de {len(order)})')
ax.xaxis.set_major_locator(mtick.MultipleLocator(2))
ax.grid(axis='y', visible=False)
ax.tick_params(axis='y', length=0, labelsize=11.5, colors=INK)
ax.legend([plt.Rectangle((0, 0), 1, 1, color=MUTED), plt.Rectangle((0, 0), 1, 1, color=MUTED, alpha=0.35)],
          ['Melhor da feature', 'Empate estatístico com o melhor'], loc='lower right')
suptitle(fig, 'Em quantas features cada algoritmo fica entre os melhores?',
         'ROC-AUC por feature, protocolo temporal: barra cheia = melhor; barra clara = estatisticamente empatado com o melhor')
save(fig, 'f3_vitorias_por_algoritmo', FEAT_NOTE)

# ---- f4: change rate of the feature x ROC-AUC (LightGBM) ----
lg = th[th.algoritmo == 'LightGBM'].set_index('feature').loc[order]
fig, ax = plt.subplots(figsize=(11, 6.5))
sz = 60 + 900 * lg.linhas / lg.linhas.max()
ax.scatter(lg.acaso, lg['ROC AUC score'], s=sz, color=ALG['LightGBM'][1], alpha=0.75, ec='white', lw=1.5, zorder=3)
OFF = {'DataTools': (8, -4), 'EMF': (10, 6), 'WebTools': (10, 4), 'CDT': (-14, -14), 'RAP': (10, -12),
       'GMF Runtime': (10, -6), 'Mylyn': (10, -10), 'GEF': (-10, 0), 'JDT': (-14, 0)}
for fe, r in lg.iterrows():
    dx, dy = OFF.get(fe, (10, 0))
    ax.annotate(fe, (r.acaso, r['ROC AUC score']), xytext=(dx, dy), textcoords='offset points', fontsize=10.5,
                ha='right' if dx < 0 else 'left', va='center', color=INK)
ax.set_xscale('log')
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(100 * v, 3 if v < 0.001 else 2 if v < 0.01 else 1)
                                                 .rstrip('0').rstrip(',') + '%'))
ax.axhline(0.5, ls=(0, (4, 4)), color=MUTED, lw=1.3)
ax.set_ylim(0.45, 1.0)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 1)))
ax.set_xlabel('Taxa de mudança da feature no teste (escala log): % dos métodos que mudaram')
ax.set_ylabel('ROC-AUC do LightGBM na feature')
suptitle(fig, 'O modelo funciona em features muito e pouco ativas',
         'Cada bolha é uma feature (tamanho = nº de métodos no teste); LightGBM model2 ROS, protocolo temporal')
save(fig, 'f4_taxa_de_mudanca_x_roc')

# ---- f5: lift heatmap (PR-AUC / chance) ----
fig, ax = plt.subplots(figsize=(11, 8.2))
L = np.log10(lift.values)
im = ax.imshow(L, cmap=SEQ, vmin=0, vmax=np.log10(max(150, np.nanmax(lift.values))), aspect='auto')
for i, fe in enumerate(order):
    for j, a in enumerate(ALGS):
        v = lift.loc[fe, a]
        ax.text(j, i, f'{br(v, 1)}×' if v < 100 else f'{v:.0f}×', ha='center', va='center', fontsize=10.5,
                color='white' if np.log10(v) > 1.3 else INK,
                fontweight='bold' if a == lift.loc[fe].idxmax() else 'normal')
ax.set_xticks(range(len(ALGS)), [SHORT[a] for a in ALGS])
ax.set_yticks(range(len(order)), [f'{fe}  ({pct(info.loc[fe, "acaso"], 3 if info.loc[fe, "acaso"] < 1e-4 else 2)})' for fe in order])
ax.xaxis.tick_top()
ax.tick_params(length=0, labelsize=11.5, colors=INK)
ax.grid(False)
for s in ax.spines.values():
    s.set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02,
                  format=mtick.FuncFormatter(lambda v, _: f'{10 ** v:.0f}×'))
cb.outline.set_visible(False)
cb.set_label('PR-AUC ÷ taxa de mudança (escala log)', color=MUTED)
suptitle(fig, 'Quantas vezes melhor que o acaso, em cada feature?',
         'PR-AUC dividida pela taxa de mudança da feature (entre parênteses); em negrito, o maior da linha')
save(fig, 'f5_ganho_sobre_acaso_feature_x_algoritmo', FEAT_NOTE)

# ================= B. feature level (ranking of the features) =================
res = pd.read_csv(RES / 'nivel_feature_resumo.csv')
base = res[res.id == 'BASELINE'].set_index('medida')
per = res[(res.medida == 'taxa (score_medio)') & (res.id != 'BASELINE')].merge(
    pd.read_csv(RES / 'resultados_teste.csv')[['id', 'PR AUC (AP)']], on='id')
P = base.loc['taxa (persistencia)']

# ---- f6: method-level quality x feature-level quality (all 84 temporal configurations) ----
fig, ax = plt.subplots(figsize=(11, 6.8))
ax.axhspan(P.spearman_IC95_inf, P.spearman_IC95_sup, color=MUTED, alpha=0.10, lw=0)
ax.axhline(P.spearman_medio, color=MUTED, lw=1.6, ls=(0, (4, 4)))
ax.text(0.0186, P.spearman_medio + 0.012, f'Persistência (repetir a release anterior): ρ = {br(P.spearman_medio)}',
        ha='right', va='bottom', color=MUTED, fontsize=10.5)
for a in ALGS:
    g = per[per.algoritmo == a]
    ax.scatter(g['PR AUC (AP)'], g.spearman_medio, s=55, color=ALG[a][1], ec='white', lw=1.2, label=ALG[a][0],
               zorder=3)
for idv, txt, dx, dy in ((per.loc[per.spearman_medio.idxmax(), 'id'], 'melhor no ranking de features', -10, 14),
                         (per.loc[per['PR AUC (AP)'].idxmax(), 'id'], 'melhor no nível de método', -10, -16)):
    r = per[per.id == idv].iloc[0]
    ax.scatter([r['PR AUC (AP)']], [r.spearman_medio], s=170, facecolor='none', ec=INK, lw=1.6, zorder=4)
    ax.annotate(f'{txt}\n{ALG[r.algoritmo][0]} {r.conjunto} {r.reamostragem}: ρ = {br(r.spearman_medio)}',
                (r['PR AUC (AP)'], r.spearman_medio), xytext=(dx, dy), textcoords='offset points', ha='right',
                va='bottom' if dy > 0 else 'top', fontsize=10, color=INK)
ax.set_xlabel('PR-AUC no nível de método (todas as features juntas)')
ax.set_ylabel('Spearman médio do ranking de features')
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 3)))
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 1)))
ax.set_xlim(0, 0.019)
ax.xaxis.set_major_locator(mtick.MultipleLocator(0.003))
ax.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
suptitle(fig, 'Acertar métodos não garante acertar o ranking de features',
         'Cada ponto é uma das 84 configurações do protocolo temporal; faixa cinza = IC 95% da persistência')
save(fig, 'f6_nivel_metodo_x_nivel_feature',
     'Nenhuma configuração supera a persistência. Os modelos que melhor ordenam métodos (boosting) são os que pior '
     'ordenam features; uma explicação provável é que suas probabilidades, ao serem promediadas por feature, '
     'refletem mais o tamanho e o perfil dos métodos do que a atividade recente.')

# ---- f7: rank of each feature per test release: real x model x persistence ----
det = pd.read_csv(RES / 'nivel_feature_por_release.csv')
best_id = per.loc[per.spearman_medio.idxmax(), 'id']
b = det[det.id == best_id].copy()
b['rk_real'] = b.groupby('release').taxa_real.rank(ascending=False, method='min')
b['rk_mod'] = b.groupby('release').score_medio.rank(ascending=False, method='min')
b['rk_per'] = b.groupby('release').persist_taxa.rank(ascending=False, method='min')
forder = b.groupby('feature').rk_real.mean().sort_values().index
rels = sorted(b.release.unique())
br_ = per[per.id == best_id].iloc[0]
fig, axs = plt.subplots(1, 3, figsize=(16, 7.2), sharey=True)
for ax, col, ttl in zip(axs, ('rk_real', 'rk_mod', 'rk_per'),
                        ('Real', f'Modelo ({ALG[br_.algoritmo][0]} {br_.conjunto} {br_.reamostragem})',
                         'Persistência')):
    M = b.pivot(index='feature', columns='release', values=col).reindex(index=forder, columns=rels)
    im = ax.imshow(M.values, cmap=SEQ + '_r', vmin=1, vmax=14, aspect='auto')
    for (i, j), v in np.ndenumerate(M.values):
        if not np.isnan(v):
            ax.text(j, i, f'{v:.0f}', ha='center', va='center', fontsize=7.5, color='white' if v <= 5 else INK)
    ax.set_title(ttl)
    ax.set_xticks(range(len(rels)), rels, fontsize=8.5)
    ax.set_xlabel('Release de teste')
    ax.grid(False)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
axs[0].set_yticks(range(len(forder)), forder)
axs[0].tick_params(axis='y', labelsize=11, colors=INK)
suptitle(fig, 'Posição de cada feature no ranking de propensão à mudança, release a release',
         '1 = feature com maior taxa de mudança na release; células vazias = feature fora da LPS ou sem dado anterior')
save(fig, 'f7_ranking_por_release_real_modelo_persistencia',
     f'Modelo: ρ médio = {br(br_.spearman_medio)}; persistência: ρ médio = {br(P.spearman_medio)} '
     '(Spearman entre a ordem prevista e a real, em cada release, médio nas 17 releases de teste).')

# ---- f8: Spearman of the best configuration of each algorithm vs the baselines ----
bestper = per.sort_values('spearman_medio', ascending=False).groupby('algoritmo').head(1)
rows = [(ALG[r.algoritmo][0], r.spearman_medio, r.spearman_IC95_inf, r.spearman_IC95_sup, ALG[r.algoritmo][1])
        for r in bestper.itertuples()]
rows += [('Persistência', P.spearman_medio, P.spearman_IC95_inf, P.spearman_IC95_sup, INK)]
H = base.loc['taxa (media_historica)']
rows += [('Média histórica', H.spearman_medio, H.spearman_IC95_inf, H.spearman_IC95_sup, MUTED)]
rows.sort(key=lambda r: r[1])
fig, ax = plt.subplots(figsize=(10.5, 6))
for k, (n, m, lo, hi, c) in enumerate(rows):
    ax.plot([lo, hi], [k, k], color=c, lw=3, alpha=0.45, solid_capstyle='round')
    ax.scatter([m], [k], s=110, color=c, ec='white', lw=1.5, zorder=3, marker='D' if c in (INK, MUTED) else 'o')
    ax.text(hi + 0.02, k, br(m), va='center', fontsize=10.5, color=INK)
ax.set_yticks(range(len(rows)), [r[0] for r in rows])
ax.tick_params(axis='y', length=0, labelsize=11.5, colors=INK)
ax.axvline(0, color=MUTED, lw=1)
ax.set_xlim(-0.1, 1.0)
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 1)))
ax.set_xlabel('Spearman médio entre o ranking previsto e o real (com IC 95%)')
ax.grid(axis='y', visible=False)
suptitle(fig, 'Prever quais features vão mudar mais: modelos × referências simples',
         'Melhor configuração de cada algoritmo no ranking de features (losangos = referências sem aprendizado)')
save(fig, 'f8_spearman_nivel_feature')

# ---------------- overview sheet ----------------
files = sorted(p for p in OUT.glob('f*.png'))
fig, axs = plt.subplots(int(np.ceil(len(files) / 2)), 2, figsize=(16, 5.2 * np.ceil(len(files) / 2)))
for ax in axs.flat:
    ax.axis('off')
for ax, p in zip(axs.flat, files):
    ax.imshow(mpimg.imread(p))
    ax.set_title(p.stem, fontsize=13, loc='left')
fig.tight_layout()
fig.savefig(OUT / 'visao_geral.png', dpi=110)
plt.close(fig)
print('ok visao_geral')
