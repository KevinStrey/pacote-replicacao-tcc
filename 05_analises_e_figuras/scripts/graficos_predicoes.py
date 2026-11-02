"""Charts computed from the per-method predictions downloaded from the server (presentation; NOT in the thesis).

Inputs:  predições/predicoes/<job id>.npz   (score and hard prediction of every test row)
         predições/prep/                     (labels, feature of each row and test indices; validated against the
                                              server metrics, see predições/prep/LEIA-ME.txt)
         resultados_e_logs/saida/resultados/  (which configuration is the best of each algorithm in the thesis)
For each protocol x algorithm the thesis configuration (best PR-AUC) is used when its predictions are available;
otherwise the best configuration available is used and marked with * in the legends.
Outputs: graficos_apresentacao/predicoes/ (PNG 300 dpi + SVG) and selecao.csv (which configuration each curve uses).
Usage: python graficos_predicoes.py
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import (average_precision_score, confusion_matrix, precision_recall_curve,  # noqa: E402
                             roc_auc_score, roc_curve)

ROOT = Path(__file__).resolve().parents[2]
PRED = ROOT / 'predições' / 'predicoes'
PREP = ROOT / 'predições' / 'prep'
RES = ROOT / 'resultados_e_logs' / 'saida' / 'resultados'
OUT = ROOT / 'graficos_apresentacao' / 'predicoes'
OUT.mkdir(parents=True, exist_ok=True)

# ---------------- modern style ----------------
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
ALG = {  # name, color (colour-blind-friendly palette)
    'LightGBM': ('LightGBM', '#E4572E'), 'XGBoost': ('XGBoost', '#F3A712'), 'MLP': ('MLP', '#7E57C2'),
    'LogisticRegression': ('Regressão logística', '#2E86AB'), 'LinearSVC': ('SVM linear', '#17BEBB'),
    'RandomForest': ('Random Forest', '#3BB273'), 'DT': ('Árvore de decisão', '#9CA3AF')}
PROTO = {'temporal': 'Protocolo temporal', 'random': 'Protocolo aleatório'}


def br(v, nd=2):
    return f'{v:.{nd}f}'.replace('.', ',')


def pct(v, nd=0):
    return br(100 * v, nd) + '%'


def suptitle(fig, title, subtitle):
    fig._titulos = (title, subtitle)      # drawn in save(), just above the axes


def save(fig, name, note=None):
    if getattr(fig, '_titulos', None):
        fig.canvas.draw()
        top = max(ax.get_tightbbox().transformed(fig.transFigure.inverted()).y1 for ax in fig.axes
                  if ax.get_visible())
        left = min(ax.get_position().x0 for ax in fig.axes if ax.get_visible())
        x0 = min(0.0, left - 0.06)
        fig.text(x0, top + 0.012, fig._titulos[1], fontsize=12, color=MUTED, ha='left', va='bottom')
        fig.text(x0, top + 0.055, fig._titulos[0], fontsize=18, fontweight='bold', ha='left', va='bottom')
    if note:
        fig.text(0.0, -0.04, note, fontsize=9.5, color=MUTED, ha='left', va='top', transform=fig.transFigure)
    for ext in ('png', 'svg'):
        fig.savefig(OUT / f'{name}.{ext}')
    plt.close(fig)
    print('ok', name)


# ---------------- data ----------------
y_all = np.load(PREP / 'y.npy')
feat_all = np.load(PREP / 'feature.npy')
import json  # noqa: E402
FEATS = json.loads((PREP / 'meta.json').read_text(encoding='utf-8'))['features']
TEST = {p: np.load(PREP / 'splits' / f'{p}__principal__test.npy') for p in ('temporal', 'random')}
t = pd.read_csv(RES / 'resultados_teste.csv')
t = t[t.variante == 'principal']
have = {p.stem for p in PRED.glob('*.npz')}
sel = []
for (proto, alg), g in t.groupby(['protocolo', 'algoritmo']):
    g = g.sort_values('PR AUC (AP)', ascending=False)
    thesis = g.iloc[0]
    av = g[g.id.isin(have)]
    if not len(av):
        continue
    use = av.iloc[0]
    sel.append({'protocolo': proto, 'algoritmo': alg, 'id': use.id, 'conjunto': use.conjunto,
                'reamostragem': use.reamostragem, 'config_do_tcc': use.id == thesis.id, 'id_tcc': thesis.id})
sel = pd.DataFrame(sel)
sel.to_csv(OUT / 'selecao.csv', index=False)
_cache = {}


def load(jid):
    if jid not in _cache:
        z = np.load(PRED / f'{jid}.npz')
        _cache[jid] = (z['score'].astype(np.float64), z['pred'])
    return _cache[jid]


def label(r, area_name, area, nd):
    star = '' if r.config_do_tcc else '*'
    return f'{ALG[r.algoritmo][0]}{star}  ·  {area_name} {br(area, nd)}'


NOTE_STAR = ('* Configuração diferente da melhor do TCC (as previsões dela não estavam no download); '
             'é a melhor entre as disponíveis.')

# ---------------- 1-2. ROC and PR curves per protocol ----------------
for proto in ('temporal', 'random'):
    s = sel[sel.protocolo == proto].copy()
    y = y_all[TEST[proto]]
    prev = y.mean()
    s['ap'] = [average_precision_score(y, load(i)[0]) for i in s.id]
    s = s.sort_values('ap', ascending=False)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 6.2))
    for r in s.itertuples():
        sc = load(r.id)[0]
        fpr, tpr, _ = roc_curve(y, sc)
        p, rc, _ = precision_recall_curve(y, sc)
        cor = ALG[r.algoritmo][1]
        a1.plot(fpr, tpr, color=cor, label=label(r, 'AUC', roc_auc_score(y, sc), 3))
        a2.plot(rc, p, color=cor, label=label(r, 'PR-AUC', r.ap, 4), lw=2)
    a1.plot([0, 1], [0, 1], ls=(0, (4, 4)), color=MUTED, lw=1.5, label='Acaso  ·  AUC 0,500')
    a1.set(xlim=(0, 1), ylim=(0, 1.01), xlabel='Taxa de falsos positivos', ylabel='Taxa de verdadeiros positivos')
    a1.set_title('Curva ROC')
    a2.axhline(prev, ls=(0, (4, 4)), color=MUTED, lw=1.5, label=f'Acaso  ·  {pct(prev, 2)} de positivos')
    a2.set_yscale('log')
    a2.set(xlim=(0, 1), ylim=(prev / 2.5, 1.02), xlabel='Revocação (mudanças encontradas)',
           ylabel='Precisão (alertas corretos), escala log')
    a2.set_title('Curva precisão-revocação')
    a2.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: pct(v, 1 if v < 0.01 else 0)))
    for ax in (a1, a2):
        ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 1)))
    a1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 1)))
    a1.legend(loc='lower right')
    a2.legend(loc='upper right')
    sub = ('Treino nas releases 1–36, teste nas 37–53' if proto == 'temporal'
           else '70% dos métodos de cada release no treino, 30% no teste')
    suptitle(fig, f'{PROTO[proto]}: melhor configuração de cada algoritmo', sub)
    fig.tight_layout()
    save(fig, f'p1_roc_pr_{"temporal" if proto == "temporal" else "aleatorio"}',
         NOTE_STAR if not s.config_do_tcc.all() else None)

# ---------------- 3. same algorithm, temporal x random ----------------
fig, axes = plt.subplots(1, 2, figsize=(15, 6.2))
for ax, alg in zip(axes, ('LightGBM', 'XGBoost')):
    for proto, ls in (('random', (0, (6, 3))), ('temporal', '-')):
        r = sel[(sel.protocolo == proto) & (sel.algoritmo == alg)].iloc[0]
        y = y_all[TEST[proto]]
        sc = load(r.id)[0]
        p, rc, _ = precision_recall_curve(y, sc)
        star = '' if r.config_do_tcc else '*'
        ax.plot(rc, p, ls=ls, color=ALG[alg][1] if proto == 'temporal' else INK, lw=2,
                label=f'{"Temporal" if proto == "temporal" else "Aleatório"}{star}  ·  PR-AUC '
                      f'{br(average_precision_score(y, sc), 3)}')
    ax.set_yscale('log')
    ax.set(xlim=(0, 1), ylim=(1e-3, 1.02), xlabel='Revocação (mudanças encontradas)',
           ylabel='Precisão, escala log')
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: pct(v, 1 if v < 0.01 else 0)))
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 1)))
    ax.set_title(ALG[alg][0])
    ax.legend(loc='upper right')
suptitle(fig, 'O mesmo algoritmo, dois protocolos de validação',
         'Misturar passado e futuro (aleatório) faz o modelo parecer muito melhor do que é ao prever releases futuras')
fig.tight_layout()
save(fig, 'p2_temporal_vs_aleatorio', NOTE_STAR if not sel[sel.algoritmo.isin(['LightGBM', 'XGBoost'])]
     .config_do_tcc.all() else None)

# ---------------- 4. cumulative gains (temporal) ----------------
proto = 'temporal'
y = y_all[TEST[proto]]
s = sel[sel.protocolo == proto]
fig, ax = plt.subplots(figsize=(11, 6.5))
grid = np.linspace(0, 1, 501)
best_line = None
for r in s.assign(ap=s.id.map(t.set_index('id')['PR AUC (AP)'])).sort_values('ap', ascending=False).itertuples():
    sc = load(r.id)[0]
    order = np.argsort(-sc, kind='mergesort')
    cum = np.cumsum(y[order]) / y.sum()
    frac = np.arange(1, len(y) + 1) / len(y)
    g_ = np.interp(grid, frac, cum)
    ax.plot(grid, g_, color=ALG[r.algoritmo][1], lw=2.2,
            label=f'{ALG[r.algoritmo][0]}{"" if r.config_do_tcc else "*"}')
    if r.algoritmo == 'LightGBM':
        best_line = (frac, cum)
ax.plot([0, 1], [0, 1], ls=(0, (4, 4)), color=MUTED, lw=1.5, label='Acaso (ordem aleatória)')
if best_line is not None:
    for k in (0.05, 0.10, 0.20):
        v = np.interp(k, *best_line)
        ax.scatter([k], [v], color=ALG['LightGBM'][1], zorder=5, s=40)
        ax.annotate(f'{pct(k)} dos métodos → {pct(v)} das mudanças', (k, v), xytext=(0.30 + k, v - 0.06),
                    fontsize=11, color=INK, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.35', fc='white', ec=GRID),
                    arrowprops=dict(arrowstyle='-', color=MUTED, lw=1))
ax.set(xlim=(0, 1), ylim=(0, 1.01), xlabel='Fração dos métodos inspecionados (do maior para o menor risco)',
       ylabel='Fração das mudanças encontradas')
ax.xaxis.set_major_formatter(mtick.PercentFormatter(1, decimals=0))
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1, decimals=0))
ax.legend(loc='lower right')
suptitle(fig, 'Quanto das mudanças se encontra revisando só os métodos de maior risco?',
         'Protocolo temporal: métodos das releases 37–53 ordenados pela probabilidade prevista (curva de ganho)')
save(fig, 'p3_curva_de_ganho_temporal', NOTE_STAR if not s.config_do_tcc.all() else None)

# ---------------- 5. precision in the top k% (temporal, LightGBM) ----------------
r = s[s.algoritmo == 'LightGBM'].iloc[0]
sc = load(r.id)[0]
order = np.argsort(-sc, kind='mergesort')
ks = [0.001, 0.005, 0.01, 0.05, 0.10, 0.20]
prec_k = [y[order[:max(1, int(k * len(y)))]].mean() for k in ks]
fig, ax = plt.subplots(figsize=(11, 5.5))
bars = ax.bar([f'Top {br(100 * k, 1).rstrip("0").rstrip(",")}%' for k in ks], prec_k, color=ALG['LightGBM'][1],
              width=0.62)
ax.axhline(y.mean(), ls=(0, (4, 4)), color=MUTED, lw=1.5)
ax.set_xlim(-0.6, len(ks) + 0.45)
ax.text(len(ks) - 0.35, y.mean(), f'acaso\n{pct(y.mean(), 2)}', va='bottom', ha='left', color=MUTED, fontsize=10.5)
for b, v in zip(bars, prec_k):
    ax.text(b.get_x() + b.get_width() / 2, v, f'{pct(v, 1)}\n({br(v / y.mean(), 1)}× o acaso)', ha='center',
            va='bottom', fontsize=10.5)
ax.set_ylim(0, max(prec_k) * 1.3)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1, decimals=0))
ax.set_ylabel('Precisão: métodos do grupo que de fato mudaram')
ax.grid(axis='x', visible=False)
suptitle(fig, 'Precisão entre os métodos de maior risco (LightGBM, protocolo temporal)',
         'Quanto menor o grupo inspecionado, maior a proporção de métodos que realmente mudam')
save(fig, 'p4_precisao_no_topo_temporal')

# ---------------- 6. score distribution (temporal, LightGBM) ----------------
fig, ax = plt.subplots(figsize=(11, 5.5))
bins = np.linspace(0, 1, 61)
for mask, nome, cor in ((y == 0, 'Métodos que não mudaram', '#9CA3AF'), (y == 1, 'Métodos que mudaram', '#E4572E')):
    h, _ = np.histogram(sc[mask], bins=bins)
    ax.fill_between(bins[:-1], h / mask.sum(), step='post', alpha=0.35, color=cor)
    ax.step(bins[:-1], h / mask.sum(), where='post', color=cor, lw=2,
            label=f'{nome} ({mask.sum():,} métodos)'.replace(',', '.'))
ax.axvline(0.5, color=INK, lw=1.2, ls=(0, (2, 3)))
ax.text(0.49, ax.get_ylim()[1] * 0.97, 'limiar padrão (0,5)', fontsize=10.5, color=INK, ha='right', va='top')
ax.set(xlim=(0, 1), xlabel='Probabilidade de mudança prevista pelo modelo', ylabel='Proporção dos métodos do grupo')
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 1)))
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1, decimals=0))
ax.legend(loc='upper right')
suptitle(fig, 'Como o modelo separa os métodos que mudam dos que não mudam',
         'LightGBM (model2, ROS), protocolo temporal: distribuição da probabilidade prevista em cada grupo')
save(fig, 'p5_distribuicao_das_probabilidades')

# ---------------- 7. confusion matrix (temporal, LightGBM, threshold 0.5) ----------------
pred = load(r.id)[1]
cm = confusion_matrix(y, pred, labels=[0, 1])
fig, ax = plt.subplots(figsize=(7.5, 6.2))
cores = np.array([['#ECFDF5', '#FEF2F2'], ['#FEF2F2', '#ECFDF5']])
for i in range(2):
    for j in range(2):
        ax.add_patch(plt.Rectangle((j, 1 - i), 1, 1, color=cores[i, j], ec='white', lw=4))
        tot = cm[i].sum()
        ax.text(j + 0.5, 1 - i + 0.58, br(cm[i, j], 0).replace(',', '.') if False else f'{cm[i, j]:,}'.replace(',', '.'),
                ha='center', va='center', fontsize=22, fontweight='bold')
        ax.text(j + 0.5, 1 - i + 0.33, f'{pct(cm[i, j] / tot, 1)} da linha', ha='center', va='center', fontsize=11,
                color=MUTED)
ax.set(xlim=(0, 2), ylim=(0, 2))
ax.set_xticks([0.5, 1.5], ['Previsto: não muda', 'Previsto: muda'])
ax.set_yticks([1.5, 0.5], ['Real: não mudou', 'Real: mudou'])
ax.tick_params(length=0, labelsize=12, colors=INK)
ax.grid(False)
for sp in ax.spines.values():
    sp.set_visible(False)
tp, fp = cm[1, 1], cm[0, 1]
suptitle(fig, 'Matriz de confusão (LightGBM, protocolo temporal)',
         f'Limiar padrão de 0,5: {pct(cm[1, 1] / cm[1].sum())} das mudanças encontradas, '
         f'{br(fp / tp, 0)} alertas falsos por acerto')
save(fig, 'p6_matriz_de_confusao_temporal')

# ---------------- 8. ROC per feature (temporal, LightGBM) ----------------
fe = feat_all[TEST[proto]]
codes = [c for c in np.unique(fe) if y[fe == c].sum() > 0]
aucs = {c: roc_auc_score(y[fe == c], sc[fe == c]) for c in codes}
codes = sorted(codes, key=lambda c: -aucs[c])
n = len(codes)
cols = 5
rows_ = int(np.ceil(n / cols))
fig, axes = plt.subplots(rows_, cols, figsize=(16, 3.3 * rows_), sharex=True, sharey=True)
for ax, c in zip(axes.flat, codes):
    m = fe == c
    fpr, tpr, _ = roc_curve(y[m], sc[m])
    ax.fill_between(fpr, tpr, alpha=0.15, color=ALG['LightGBM'][1])
    ax.plot(fpr, tpr, color=ALG['LightGBM'][1], lw=2)
    ax.plot([0, 1], [0, 1], ls=(0, (3, 3)), color=MUTED, lw=1)
    ax.set_title(f'{FEATS[c]}', fontsize=12)
    ax.text(0.97, 0.06, f'AUC {br(aucs[c], 3)}', ha='right', fontsize=11, fontweight='bold',
            transform=ax.transAxes)
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 1)))
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 1)))
for ax in list(axes.flat)[n:]:
    ax.set_visible(False)
fig.supxlabel('Taxa de falsos positivos', color=INK)
fig.supylabel('Taxa de verdadeiros positivos', color=INK)
fig.tight_layout()
suptitle(fig, 'Curva ROC por feature da LPS (mesmo modelo global)',
         'LightGBM (model2, ROS), protocolo temporal; features ordenadas pela AUC')
save(fig, 'p7_roc_por_feature_temporal')
print(sel.to_string())
