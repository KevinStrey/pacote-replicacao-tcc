"""PR and ROC curves of the best configuration of each algorithm (Tabela res-melhores), one chart per protocol and curve.

Reads the per-row test scores downloaded from the server (predições/predicoes/*.npz) and the labels and test indices
of predições/prep. Curves are computed with numpy (same definitions as sklearn: thresholds at every distinct score,
AP = sum (R_n - R_{n-1}) P_n, ROC-AUC by the trapezoidal rule); the areas are checked against resultados_teste.csv.
Writes PNG (300 dpi), SVG and PDF to graficos_apresentacao/resultados/ (slides, with title) and PDF without title to
TCC___Kevin___UDESC/Textuais/imagens/curvas/ (thesis; the figure caption is the title).
Usage: python graficos_curvas.py
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PRED = ROOT / 'predições'
RES = ROOT / 'resultados_e_logs' / 'saida' / 'resultados'
OUT = ROOT / 'graficos_apresentacao' / 'resultados'
OUT_TCC = ROOT / 'TCC___Kevin___UDESC' / 'Textuais' / 'imagens' / 'curvas'
OUT_TCC.mkdir(parents=True, exist_ok=True)

# best configuration of each algorithm (same rows and order as the thesis table)
BEST = {
    'temporal': [('fase1', 'model2', 'ROS', 'LightGBM'), ('fase2', 'model2', 'ROS', 'MLP'),
                 ('fase1', 'model3', 'ADA', 'LogisticRegression'), ('fase1', 'model2', 'ROS', 'XGBoost'),
                 ('fase1', 'model2', 'ROS', 'LinearSVC'), ('fase1', 'model2', 'SMOTE', 'RandomForest'),
                 ('fase1', 'model1', 'NONE', 'DT')],
    'random': [('fase1', 'model2', 'ROS', 'XGBoost'), ('fase1', 'model2', 'ROS', 'LightGBM'),
               ('fase1', 'model2', 'SMOTE', 'RandomForest'), ('fase1', 'model2', 'NONE', 'DT'),
               ('fase1', 'model2', 'SMOTE', 'LinearSVC'), ('fase1', 'model2', 'SMOTE', 'LogisticRegression')],
}
# one fixed color per algorithm in all four charts (Okabe-Ito, colorblind safe)
COLOR = {'LightGBM': '#E69F00', 'XGBoost': '#0072B2', 'MLP': '#CC79A7', 'LogisticRegression': '#009E73',
         'LinearSVC': '#56B4E9', 'RandomForest': '#D55E00', 'DT': '#000000'}
PROTO_PT = {'temporal': 'Protocolo temporal', 'random': 'Protocolo aleatório'}

# same style and helpers as graficos_resultados.py
plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 12,
    'axes.titlesize': 13, 'axes.titleweight': 'bold', 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.alpha': 0.3, 'grid.linestyle': '--', 'axes.formatter.use_locale': False,
    'savefig.bbox': 'tight', 'savefig.dpi': 300,
})
ALG_PT = {'LightGBM': 'LightGBM', 'XGBoost': 'XGBoost', 'MLP': 'MLP', 'LogisticRegression': 'Regr. logística',
          'LinearSVC': 'SVM linear', 'RandomForest': 'Random Forest', 'DT': 'Árvore de decisão'}


def br(x, nd=2):
    """Number with decimal comma, rounded half up (same as the thesis tables)."""
    from decimal import ROUND_HALF_UP, Decimal
    v = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    return f'{v:.{nd}f}'.replace('.', ',')


def comma_axis(ax, axis='y', nd=2):
    f = mtick.FuncFormatter(lambda v, _: br(v, nd))
    (ax.yaxis if axis == 'y' else ax.xaxis).set_major_formatter(f)

y_all = np.load(PRED / 'prep' / 'y.npy')
ref = pd.read_csv(RES / 'resultados_teste.csv')


def curves(y, s):
    """Points of the ROC and PR curves at every distinct score, plus ROC-AUC and AP."""
    o = np.argsort(-s, kind='mergesort')
    s, y = s[o], y[o].astype(np.int64)
    last = np.r_[np.flatnonzero(np.diff(s)), len(s) - 1]       # last row of each distinct score
    tp = np.cumsum(y)[last]
    fp = (last + 1) - tp
    P, N = tp[-1], fp[-1]
    tpr, fpr = np.r_[0, tp / P], np.r_[0, fp / N]
    prec, rec = tp / (tp + fp), tp / P
    auc = np.trapezoid(tpr, fpr)
    ap = np.sum(np.diff(np.r_[0, rec]) * prec)
    return fpr, tpr, rec, prec, auc, ap


def thin(x, y, n=4000):
    """Keep at most ~n points (evenly spaced along x) so the SVG/PDF stay small."""
    if len(x) <= n:
        return x, y
    keep = np.unique(np.r_[np.searchsorted(x, np.linspace(x[0], x[-1], n)).clip(0, len(x) - 1), 0, len(x) - 1])
    return x[keep], y[keep]


def save(fig, name):
    for ext in ('png', 'svg', 'pdf'):
        fig.savefig(OUT / f'{name}.{ext}')
    plt.close(fig)
    print('ok', name)


def draw(proto, res, base, tcc):
    """tcc=False: slides (title, PNG/SVG/PDF in OUT). tcc=True: thesis (no title, larger legend, PDF in OUT_TCC)."""
    fs = 10 if tcc else 8.5

    def finish(fig, ax, title, name):
        if not tcc:
            ax.set_title(title)
        if tcc:
            fig.savefig(OUT_TCC / f'{name}.pdf')
            plt.close(fig)
            print('ok tcc', name)
        else:
            save(fig, name)

    # ---- ROC ----
    fig, ax = plt.subplots(figsize=(6.4, 6))
    for alg, conj, rs, fpr, tpr, rec, prec, auc, ap in res:
        ax.plot(*thin(fpr, tpr), color=COLOR[alg], lw=1.6,
                label=f'{ALG_PT[alg]} ({conj}, {rs}): {br(auc, 3)}')
    ax.plot([0, 1], [0, 1], color='#616161', ls='--', lw=1.4, label='Acaso: 0,500')
    ax.set(xlim=(0, 1), ylim=(0, 1.005), xlabel='Taxa de falsos positivos',
           ylabel='Taxa de verdadeiros positivos (recall)')
    ax.set_aspect('equal')
    comma_axis(ax, 'x', 1), comma_axis(ax, 'y', 1)
    ax.legend(title='Algoritmo (métricas, reamostr.): ROC-AUC', loc='lower right', fontsize=fs - (0.9 if proto == 'temporal' else 0.5),
              title_fontsize=fs - (0.9 if proto == 'temporal' else 0.5))                          # smaller: the box must not touch the chance diagonal
    finish(fig, ax, f'Curva ROC – {PROTO_PT[proto].lower()}', f'c_roc_{proto}')

    # ---- PR ----
    fig, ax = plt.subplots(figsize=(6.4, 6))
    top = 0
    for alg, conj, rs, fpr, tpr, rec, prec, auc, ap in res:
        r_, p_ = thin(rec, prec)
        ax.plot(r_, p_, color=COLOR[alg], lw=1.6, label=f'{ALG_PT[alg]} ({conj}, {rs}): {br(ap, 4)}')
        top = max(top, prec[rec >= 0.01].max())               # ignore the first few alerts (precision ~1 by chance)
    ax.axhline(base, color='#616161', ls='--', lw=1.4, label=f'Acaso (taxa de positivos): {br(base, 4)}')
    ymax = min(1, top * 1.1)
    ax.text(0.99, base + ymax * 0.012, f'acaso = {br(base, 4)}', ha='right', va='bottom', fontsize=fs + 0.5,
            color='#616161')
    ax.set(xlim=(0, 1), ylim=(0, ymax), xlabel='Recall (métodos alterados encontrados)',
           ylabel='Precisão (alertas corretos)')
    if ymax < 0.5:                                              # temporal: round ticks every 0.025
        ax.yaxis.set_major_locator(mtick.MultipleLocator(0.025))
    comma_axis(ax, 'x', 1), comma_axis(ax, 'y', 3 if ymax < 0.5 else 1)
    ax.legend(title='Algoritmo (métricas, reamostr.): PR-AUC', loc='upper right', fontsize=fs, title_fontsize=fs)
    finish(fig, ax, f'Curva precisão–recall – {PROTO_PT[proto].lower()}', f'c_pr_{proto}')


for proto, rows in BEST.items():
    te = np.load(PRED / 'prep' / 'splits' / f'{proto}__principal__test.npy')
    y = y_all[te]
    base = y.mean()
    res = []
    for fase, conj, rs, alg in rows:
        s = np.load(PRED / 'predicoes' / f'{fase}__{proto}__principal__{conj}__{rs}__{alg}__teste.npz')['score']
        fpr, tpr, rec, prec, auc, ap = curves(y, s.astype(np.float64))
        r = ref[(ref.protocolo == proto) & (ref.variante == 'principal') & (ref.conjunto == conj)
                & (ref.reamostragem == rs) & (ref.algoritmo == alg)]
        print(f'{proto:8} {alg:18} AP={ap:.4f} (servidor {r["PR AUC (AP)"].iloc[0]:.4f})  '
              f'AUC={auc:.4f} (servidor {r["ROC AUC score"].iloc[0]:.4f})')
        res.append((alg, conj, rs, fpr, tpr, rec, prec, auc, ap))

    for tcc in (False, True):
        draw(proto, res, base, tcc)
