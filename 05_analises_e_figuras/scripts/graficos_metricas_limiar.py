"""Charts of the threshold-dependent metrics (accuracy, precision, recall, F1, MCC) for the presentation.
Not in the thesis.

Inputs:  resultados_e_logs/saida/resultados/resultados_teste.csv  (metrics at the default threshold of 0.5)
         predições/predicoes + predições/prep                     (scores, only for the metric-vs-threshold chart)
Outputs: graficos_apresentacao/metricas_limiar/ (PNG 300 dpi + SVG) and tabela_metricas_limiar.csv
Usage:   python graficos_metricas_limiar.py
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / 'resultados_e_logs' / 'saida' / 'resultados'
PRED = ROOT / 'predições' / 'predicoes'
PREP = ROOT / 'predições' / 'prep'
OUT = ROOT / 'graficos_apresentacao' / 'metricas_limiar'
OUT.mkdir(parents=True, exist_ok=True)

# ---------------- modern style (same as graficos_predicoes.py) ----------------
INK, MUTED, GRID = '#1F2937', '#6B7280', '#E5E7EB'
plt.rcParams.update({
    'font.family': 'sans-serif', 'font.sans-serif': ['Segoe UI', 'Inter', 'Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 12, 'text.color': INK, 'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED,
    'axes.edgecolor': GRID, 'axes.linewidth': 1.0, 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.8, 'axes.axisbelow': True,
    'axes.titlesize': 14, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left', 'axes.titlepad': 10,
    'legend.frameon': False, 'legend.fontsize': 10, 'figure.facecolor': 'white', 'savefig.facecolor': 'white',
    'savefig.bbox': 'tight', 'savefig.dpi': 300, 'lines.linewidth': 2.4, 'lines.solid_capstyle': 'round',
})
ALG = {
    'LightGBM': ('LightGBM', '#E4572E'), 'XGBoost': ('XGBoost', '#F3A712'), 'MLP': ('MLP', '#7E57C2'),
    'LogisticRegression': ('Regressão logística', '#2E86AB'), 'LinearSVC': ('SVM linear', '#17BEBB'),
    'RandomForest': ('Random Forest', '#3BB273'), 'DT': ('Árvore de decisão', '#9CA3AF')}
METRICS = [('Accuracy', 'Acurácia'), ('precision', 'Precisão'), ('Sensitivity', 'Revocação'),
           ('F1(class1)', 'F1 (classe "muda")'), ('MCC', 'MCC')]


def br(v, nd=2):
    return f'{v:.{nd}f}'.replace('.', ',')


def pct(v, nd=0):
    return br(100 * v, nd) + '%'


def save(fig, name, title, subtitle, note=None):
    fig.canvas.draw()
    top = max(ax.get_tightbbox().transformed(fig.transFigure.inverted()).y1 for ax in fig.axes if ax.get_visible())
    left = min(ax.get_position().x0 for ax in fig.axes if ax.get_visible())
    x0 = min(0.0, left - 0.06)
    fig.text(x0, top + 0.012, subtitle, fontsize=12, color=MUTED, ha='left', va='bottom')
    fig.text(x0, top + 0.06, title, fontsize=18, fontweight='bold', ha='left', va='bottom')
    if note:
        fig.text(x0, -0.03, note, fontsize=9.5, color=MUTED, ha='left', va='top')
    for ext in ('png', 'svg'):
        fig.savefig(OUT / f'{name}.{ext}')
    plt.close(fig)
    print('ok', name)


# ---------------- data: best configuration (highest PR-AUC) of each algorithm, as in the thesis ----------------
t = pd.read_csv(RES / 'resultados_teste.csv')
t = t[t.variante == 'principal']
best = (t.sort_values('PR AUC (AP)', ascending=False).groupby(['protocolo', 'algoritmo']).head(1)
        .sort_values(['protocolo', 'PR AUC (AP)'], ascending=[False, False]))
cols = ['protocolo', 'algoritmo', 'conjunto', 'reamostragem', 'Accuracy', 'precision', 'Sensitivity', 'Specificity',
        'F1(class1)', 'F1-Score(macro)', 'MCC', 'ROC AUC score', 'PR AUC (AP)', 'tn', 'fp', 'fn', 'tp']
best[cols].to_csv(OUT / 'tabela_metricas_limiar.csv', index=False, sep=';', decimal=',')
tmp = best[best.protocolo == 'temporal'].reset_index(drop=True)
prev_t = tmp.positivos.iloc[0] / tmp.linhas.iloc[0]
NOTE = ('Melhor configuração de cada algoritmo (a da tabela de resultados do TCC), protocolo temporal, '
        'limiar padrão de 0,5.')

# ---- m1: the five threshold metrics side by side (one scale per metric) ----
fig, axs = plt.subplots(1, 5, figsize=(17, 5.6), sharey=True)
yy = np.arange(len(tmp))[::-1]
for ax, (col, name) in zip(axs, METRICS):
    vals = tmp[col].to_numpy()
    ax.barh(yy, vals, color=[ALG[a][1] for a in tmp.algoritmo], height=0.62)
    lim = max(vals.max() * 1.35, 0.02)
    for y, v in zip(yy, vals):
        ax.text(v + lim * 0.02, y, br(v, 3), va='center', fontsize=10, color=INK)
    ax.set_xlim(0, lim)
    ax.set_title(name)
    ax.grid(axis='y', visible=False)
    ax.xaxis.set_major_locator(mtick.MaxNLocator(3))
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 2)))
axs[0].set_yticks(yy, [ALG[a][0] for a in tmp.algoritmo])
axs[0].tick_params(axis='y', length=0, labelsize=11.5, colors=INK)
save(fig, 'm1_metricas_no_limiar_padrao', 'Métricas no limiar padrão (0,5), protocolo temporal',
     'Cada painel tem a sua escala; algoritmos na ordem da PR-AUC', NOTE)

# ---- m2: the accuracy paradox ----
always_no = 1 - prev_t
names = [ALG[a][0] for a in tmp.algoritmo] + ['Sempre "não muda"']
colors = [ALG[a][1] for a in tmp.algoritmo] + [MUTED]
acc = list(tmp.Accuracy) + [always_no]
rec = list(tmp.Sensitivity) + [0.0]
yy2 = np.arange(len(names))[::-1]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
for ax, vals, title in ((a1, acc, 'Acurácia'), (a2, rec, 'Revocação (mudanças encontradas)')):
    bars = ax.barh(yy2, vals, color=colors, height=0.62)
    bars[-1].set_hatch('///'); bars[-1].set_edgecolor('white')
    for y, v in zip(yy2, vals):
        ax.text(v + 0.015, y, pct(v, 1), va='center', fontsize=10.5, color=INK)
    ax.set_xlim(0, 1.15)
    ax.set_title(title)
    ax.grid(axis='y', visible=False)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1, decimals=0))
a1.set_yticks(yy2, names)
a1.tick_params(axis='y', length=0, labelsize=11.5, colors=INK)
save(fig, 'm2_paradoxo_da_acuracia', 'A acurácia engana quando a mudança é rara',
     f'Um "modelo" que diz sempre "não muda" tem {pct(always_no, 1)} de acurácia e não encontra nenhuma mudança',
     NOTE + f' Só {pct(prev_t, 2)} dos métodos do teste mudam.')

# ---- m3: how each metric moves with the threshold (LightGBM, temporal) ----
te = np.load(PREP / 'splits' / 'temporal__principal__test.npy')
y = np.load(PREP / 'y.npy')[te]
lg = tmp[tmp.algoritmo == 'LightGBM'].iloc[0]
s = np.load(PRED / f'{lg.id}.npz')['score'].astype(np.float64)
thr = np.linspace(0.01, 0.99, 99)
edges = np.r_[thr, np.inf]
pos_hist = np.histogram(s[y == 1], bins=np.r_[-np.inf, edges])[0]
neg_hist = np.histogram(s[y == 0], bins=np.r_[-np.inf, edges])[0]
P, N = (y == 1).sum(), (y == 0).sum()
tp = (P - np.cumsum(pos_hist)[:-1]).astype(np.float64)          # scores >= threshold
fp = (N - np.cumsum(neg_hist)[:-1]).astype(np.float64)
fn, tn = P - tp, N - fp
prec = np.where(tp + fp > 0, tp / np.maximum(tp + fp, 1), np.nan)
recall = tp / P
f1 = np.where(prec + recall > 0, 2 * prec * recall / (prec + recall), 0)
accu = (tp + tn) / (P + N)
mcc = (tp * tn - fp * fn) / np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
flagged = (tp + fp) / (P + N)
k50 = int(np.argmin(np.abs(thr - 0.5)))
print(f'conferencia no limiar 0,5: MCC {mcc[k50]:.4f} (servidor {lg.MCC:.4f}), revocacao {recall[k50]:.4f} '
      f'(servidor {lg.Sensitivity:.4f}), precisao {prec[k50]:.4f} (servidor {lg.precision:.4f})')
fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 6))
for vals, name, color in ((recall, 'Revocação', '#E4572E'), (accu, 'Acurácia', '#2E86AB'),
                          (flagged, 'Métodos apontados (fração)', '#9CA3AF')):
    a1.plot(thr, vals, color=color, label=name)
for vals, name, color in ((prec, 'Precisão', '#7E57C2'), (f1, 'F1 (classe "muda")', '#3BB273'),
                          (mcc, 'MCC', '#F3A712')):
    a2.plot(thr, vals, color=color, label=name)
a2.axhline(prev_t, ls=(0, (4, 4)), color=MUTED, lw=1.3)
a2.text(0.02, prev_t * 1.15, f'precisão do acaso ({pct(prev_t, 2)})', color=MUTED, fontsize=10)
for ax in (a1, a2):
    ax.axvline(0.5, color=INK, lw=1.2, ls=(0, (2, 3)))
    ax.set_xlabel('Limiar de decisão (probabilidade mínima para apontar "vai mudar")')
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 1)))
    ax.legend(loc='upper right' if ax is a2 else 'center right')
a1.text(0.51, 0.03, 'limiar padrão', fontsize=10, color=INK)
a1.set_ylim(0, 1.02)
a1.yaxis.set_major_formatter(mtick.PercentFormatter(1, decimals=0))
a1.set_title('Escala de 0 a 100%')
a2.set_yscale('log')
a2.set_ylim(prev_t / 3, 0.5)
a2.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 3) if v < 0.01 else br(v, 2)))
a2.set_title('Escala logarítmica (valores pequenos)')
save(fig, 'm3_metricas_por_limiar_lightgbm', 'Cada limiar dá um resultado diferente',
     'LightGBM (model2, ROS), protocolo temporal: o mesmo modelo, avaliado com limiares de 0,01 a 0,99',
     'A ROC-AUC e a PR-AUC resumem todos esses limiares de uma vez; por isso foram as métricas principais.')

# ---- m4: temporal x random for F1 and MCC ----
both = best.pivot(index='algoritmo', columns='protocolo', values=['F1(class1)', 'MCC']).dropna()
order = best[best.protocolo == 'random'].sort_values('MCC').algoritmo
order = [a for a in order if a in both.index]
fig, axs = plt.subplots(1, 2, figsize=(14, 5.4), sharey=True)
for ax, (col, name) in zip(axs, (('F1(class1)', 'F1 (classe "muda")'), ('MCC', 'MCC'))):
    for k, a in enumerate(order):
        vt, vr = both.loc[a, (col, 'temporal')], both.loc[a, (col, 'random')]
        ax.plot([vt, vr], [k, k], color=GRID, lw=5, solid_capstyle='round', zorder=1)
        ax.scatter([vt], [k], s=90, color=ALG[a][1], ec='white', lw=1.5, zorder=3, marker='o')
        ax.scatter([vr], [k], s=90, color='white', ec=ALG[a][1], lw=2, zorder=3, marker='o')
    ax.set_title(name)
    ax.grid(axis='y', visible=False)
    ax.xaxis.set_major_locator(mtick.MultipleLocator(0.05))
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 2)))
axs[0].set_yticks(range(len(order)), [ALG[a][0] for a in order])
axs[0].tick_params(axis='y', length=0, labelsize=11.5, colors=INK)
axs[1].scatter([], [], s=90, color=MUTED, label='Temporal (ponto cheio)')
axs[1].scatter([], [], s=90, color='white', ec=MUTED, lw=2, label='Aleatório (ponto vazio)')
axs[1].legend(loc='lower right')
save(fig, 'm4_temporal_x_aleatorio_f1_mcc', 'O protocolo aleatório também infla o F1 e o MCC',
     'Melhor configuração de cada algoritmo em cada protocolo, limiar padrão de 0,5',
     'MLP só foi treinado no protocolo temporal e não aparece aqui.')

# ---- m5: MCC of every algorithm x metric set (best resampling), temporal ----
tt = t[t.protocolo == 'temporal']
grid = tt.groupby(['algoritmo', 'conjunto']).MCC.max().unstack()[['model1', 'model2', 'model3']]
grid = grid.loc[[a for a in tmp.algoritmo]]
fig, ax = plt.subplots(figsize=(9.5, 6.2))
im = ax.imshow(grid.values, cmap='Blues', vmin=0, vmax=grid.values.max() * 1.05, aspect='auto')
for (i, j), v in np.ndenumerate(grid.values):
    ax.text(j, i, br(v, 3), ha='center', va='center', fontsize=12,
            color='white' if v > grid.values.max() * 0.6 else INK)
ax.set_xticks(range(3), ['Estruturais\n(model1)', 'Estruturais + evolutivas\n(model2)', 'Evolutivas\n(model3)'])
ax.set_yticks(range(len(grid)), [ALG[a][0] for a in grid.index])
ax.xaxis.tick_top()
ax.tick_params(length=0, labelsize=11.5, colors=INK)
ax.grid(False)
for sp in ax.spines.values():
    sp.set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03, format=mtick.FuncFormatter(lambda v, _: br(v, 2)))
cb.outline.set_visible(False)
cb.set_label('MCC (0 = acaso, 1 = perfeito)', color=MUTED)
save(fig, 'm5_mcc_algoritmo_x_metricas', 'MCC por algoritmo e conjunto de métricas',
     'Protocolo temporal, melhor reamostragem de cada combinação, limiar padrão de 0,5')
print('tabela:', OUT / 'tabela_metricas_limiar.csv')
