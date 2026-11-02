"""PR and ROC curves of the sensitivity analysis (fase 3): main model restricted to the variant's test rows ("antes")
versus the model trained without PTP, Scout and Mylyn ("depois"), one panel per protocol.

Reads predições/predicoes/*.npz and predições/prep (labels, features, test indices). The variant's test rows are the
main test indices without the three features, the same rule as prepare_data.py. Areas are checked against
resultados_e_logs/saida/resultados/sensibilidade.csv.
Writes PNG/SVG/PDF with title to graficos_apresentacao/resultados/ and PDF without title to
TCC___Kevin___UDESC/Textuais/imagens/curvas/.
Usage: python graficos_sensibilidade.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PRED = ROOT / 'predições'
RES = ROOT / 'resultados_e_logs' / 'saida' / 'resultados'
OUT = ROOT / 'graficos_apresentacao' / 'resultados'
OUT_TCC = ROOT / 'TCC___Kevin___UDESC' / 'Textuais' / 'imagens' / 'curvas'
OUT_TCC.mkdir(parents=True, exist_ok=True)

EXCL = ['PTP', 'Scout', 'Mylyn']
CONF = {'temporal': ('fase1', 'model2', 'ROS', 'LightGBM'), 'random': ('fase1', 'model2', 'ROS', 'XGBoost')}
PROTO_PT = {'temporal': 'Protocolo temporal', 'random': 'Protocolo aleatório'}
ALG_PT = {'LightGBM': 'LightGBM', 'XGBoost': 'XGBoost'}
C_ANTES, C_DEPOIS, C_ACASO = '#E69F00', '#0072B2', '#616161'

plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 12,
    'axes.titlesize': 13, 'axes.titleweight': 'bold', 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.alpha': 0.3, 'grid.linestyle': '--', 'axes.formatter.use_locale': False,
    'savefig.bbox': 'tight', 'savefig.dpi': 300,
})


def br(x, nd=2):
    """Number with decimal comma, rounded half up (same as the thesis tables)."""
    from decimal import ROUND_HALF_UP, Decimal
    v = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    return f'{v:.{nd}f}'.replace('.', ',')


def comma_axis(ax, axis='y', nd=2):
    f = mtick.FuncFormatter(lambda v, _: br(v, nd))
    (ax.yaxis if axis == 'y' else ax.xaxis).set_major_formatter(f)


def curves(y, s):
    """Points of the ROC and PR curves at every distinct score, plus ROC-AUC and AP (same as graficos_curvas.py)."""
    o = np.argsort(-s, kind='mergesort')
    s, y = s[o], y[o].astype(np.int64)
    last = np.r_[np.flatnonzero(np.diff(s)), len(s) - 1]
    tp = np.cumsum(y)[last]
    fp = (last + 1) - tp
    P, N = tp[-1], fp[-1]
    tpr, fpr = np.r_[0, tp / P], np.r_[0, fp / N]
    prec, rec = tp / (tp + fp), tp / P
    return fpr, tpr, rec, prec, np.trapezoid(tpr, fpr), np.sum(np.diff(np.r_[0, rec]) * prec)


def thin(x, y, n=4000):
    if len(x) <= n:
        return x, y
    keep = np.unique(np.r_[np.searchsorted(x, np.linspace(x[0], x[-1], n)).clip(0, len(x) - 1), 0, len(x) - 1])
    return x[keep], y[keep]


y_all = np.load(PRED / 'prep' / 'y.npy')
feat = np.load(PRED / 'prep' / 'feature.npy')
names = json.loads((PRED / 'prep' / 'meta.json').read_text(encoding='utf-8'))['features']
keep_feat = ~np.isin(feat, [names.index(f) for f in EXCL])
ref = pd.read_csv(RES / 'sensibilidade.csv')

data = {}
for proto, (fase, conj, rs, alg) in CONF.items():
    te = np.load(PRED / 'prep' / 'splits' / f'{proto}__principal__test.npy')
    mask = keep_feat[te]                                    # main test rows that remain in the variant
    y = y_all[te][mask]
    s_main = np.load(PRED / 'predicoes' / f'{fase}__{proto}__principal__{conj}__{rs}__{alg}__teste.npz')['score']
    s_var = np.load(PRED / 'predicoes' / f'fase3__{proto}__sem_PTP_Scout_Mylyn__{conj}__{rs}__{alg}__teste.npz')['score']
    assert len(s_var) == mask.sum(), 'variant test rows differ from the main test rows without the three features'
    antes = curves(y, s_main[mask].astype(np.float64))
    depois = curves(y, s_var.astype(np.float64))
    r = ref[ref.protocolo == proto].set_index('metrica')
    print(f'{proto:8} AP antes={antes[5]:.4f} (csv {r.loc["PR AUC (AP)", "principal_restrito"]:.4f}) '
          f'depois={depois[5]:.4f} (csv {r.loc["PR AUC (AP)", "variante"]:.4f}) | '
          f'AUC antes={antes[4]:.4f} (csv {r.loc["ROC AUC score", "principal_restrito"]:.4f}) '
          f'depois={depois[4]:.4f} (csv {r.loc["ROC AUC score", "variante"]:.4f})')
    data[proto] = (alg, y.mean(), antes, depois)


def draw(kind, tcc):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.6))
    fs = 13 if tcc else 9.5
    for ax, (proto, (alg, base, antes, depois)) in zip(axes, data.items()):
        for lab, c, cur in (('Antes: modelo principal', C_ANTES, antes),
                            ('Depois: sem PTP, Scout e Mylyn', C_DEPOIS, depois)):
            fpr, tpr, rec, prec, auc, ap = cur
            if kind == 'roc':
                ax.plot(*thin(fpr, tpr), color=c, lw=1.8, label=f'{lab}: {br(auc, 3)}')
            else:
                ax.plot(*thin(rec, prec), color=c, lw=1.8, label=f'{lab}: {br(ap, 4)}')
        if kind == 'roc':
            ax.plot([0, 1], [0, 1], color=C_ACASO, ls='--', lw=1.4, label='Acaso: 0,500')
            ax.set(xlim=(0, 1), ylim=(0, 1.005), xlabel='Taxa de falsos positivos',
                   ylabel='Taxa de verdadeiros positivos (recall)')
            ax.set_aspect('equal')
            comma_axis(ax, 'x', 1), comma_axis(ax, 'y', 1)
            loc, ttl = 'lower right', 'ROC-AUC'
        else:
            top = max(c[3][c[2] >= 0.01].max() for c in (antes, depois))
            ymax = min(1, top * 1.1)
            ax.axhline(base, color=C_ACASO, ls='--', lw=1.4, label=f'Acaso (taxa de positivos): {br(base, 4)}')
            ax.set(xlim=(0, 1), ylim=(0, ymax), xlabel='Recall (métodos alterados encontrados)',
                   ylabel='Precisão (alertas corretos)')
            if ymax < 0.5:
                ax.yaxis.set_major_locator(mtick.MultipleLocator(0.025))
            comma_axis(ax, 'x', 1), comma_axis(ax, 'y', 3 if ymax < 0.5 else 1)
            loc, ttl = 'upper right', 'PR-AUC'
        ax.set_title(f'{PROTO_PT[proto]} ({ALG_PT[alg]}, model2, ROS)', fontsize=12)
        ax.legend(title=ttl, loc=loc, fontsize=fs - 1, title_fontsize=fs - 1)
    name = f'c_sens_{kind}'
    if tcc:
        fig.savefig(OUT_TCC / f'{name}.pdf')
        print('ok tcc', name)
    else:
        fig.suptitle(('Curvas ROC' if kind == 'roc' else 'Curvas precisão–recall')
                     + ' – análise de sensibilidade (mesmas linhas de teste)', fontweight='bold')
        for ext in ('png', 'svg', 'pdf'):
            fig.savefig(OUT / f'{name}.{ext}')
        print('ok', name)
    plt.close(fig)


for kind in ('pr', 'roc'):
    for tcc in (False, True):
        draw(kind, tcc)
