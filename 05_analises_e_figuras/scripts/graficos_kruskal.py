"""Box plots of the Kruskal-Wallis analyses (reads resultados/kruskal/valores.csv from testes_kruskal.py).

box_metodo_acaso_*    QP1: best configuration of each algorithm and the random classifier, one figure per protocol
box_fatores_*         QP2: the 84 temporal configurations grouped by algorithm, metric set and resampling (one figure each)
box_feature_ordem     QP3: Spearman per test release of each predictor
box_fatores_feature   QP4: Spearman of the 84 temporal configurations grouped by algorithm, metric set and resampling
box_identidade_*      QP5: main model (restricted) x variant, one figure per protocol
Each box summarises the values of the test releases (one value per release); the points are the releases.
Writes PDF (no title) to TCC___Kevin___UDESC/Textuais/imagens/testes/ and PNG to graficos_apresentacao/resultados/.
Usage: python graficos_kruskal.py
"""
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
KW = ROOT / 'resultados_e_logs' / 'saida' / 'resultados' / 'kruskal'
OUT = ROOT / 'graficos_apresentacao' / 'resultados'
OUT_TCC = ROOT / 'TCC___Kevin___UDESC' / 'Textuais' / 'imagens' / 'testes'
OUT.mkdir(parents=True, exist_ok=True)
OUT_TCC.mkdir(parents=True, exist_ok=True)
C_MOD, C_ALE, C_ING, C_B = '#0072B2', '#8C8C8C', '#E69F00', '#009E73'
MET = {'pr_auc': 'PR-AUC', 'roc_auc': 'ROC-AUC', 'spearman': 'Correlação de Spearman'}

plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 11,
    'mathtext.fontset': 'custom', 'mathtext.it': 'Times New Roman:italic', 'mathtext.rm': 'Times New Roman',
    'axes.titlesize': 11, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True,
    'grid.alpha': 0.3, 'grid.linestyle': '--', 'savefig.bbox': 'tight', 'savefig.dpi': 300, 'pdf.fonttype': 42,
})

V = pd.read_csv(KW / 'valores.csv')


def br(x, nd=2):
    v = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    return f'{v:.{nd}f}'.replace('.', ',').replace('-', '−')


def comma(ax, nd, axis='x'):
    a = ax.xaxis if axis == 'x' else ax.yaxis
    a.set_major_locator(mtick.MaxNLocator(6))
    a.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, nd)))


def box(ax, groups, colors, nd, xlabel, ref=None, dark=False):
    """Horizontal box plot, first group on top; one point per release."""
    names = list(groups)[::-1]
    data = [np.asarray(groups[n]) for n in names]
    bp = ax.boxplot(data, orientation='horizontal', widths=0.6, patch_artist=True, showfliers=False,
                    medianprops=dict(color='black', lw=1.4, zorder=4))
    rng = np.random.default_rng(0)
    for i, (patch, n, d) in enumerate(zip(bp['boxes'], names, data), 1):
        c = colors.get(n, C_MOD)
        patch.set(facecolor=c, alpha=0.35, edgecolor=c)
        many = len(d) > 100 and not dark        # large groups: lighter points, so that the box stays visible
        ax.scatter(d, i + rng.uniform(-0.18, 0.18, len(d)), s=3 if many else 7, color=c,
                   alpha=0.18 if many else 0.75, zorder=1 if many else 3, linewidths=0)
    ax.set_yticks(range(1, len(names) + 1), names)
    ax.set_xlabel(xlabel)
    ax.grid(axis='y', visible=False)
    if ref is not None:
        ax.axvline(ref, color='black', ls=':', lw=1)
    comma(ax, nd)


def groups_of(analise, metrica, order=None):
    d = V[(V.analise == analise) & (V.metrica == metrica)]
    g = {k: v.valor.to_numpy() for k, v in d.groupby('grupo', sort=False)}
    keys = order or sorted(g, key=lambda k: -np.median(g[k]))
    return {k: g[k] for k in keys if k in g}


def last(g, name):
    """Moves one group (the random reference) to the end."""
    return {**{k: v for k, v in g.items() if k != name}, **({name: g[name]} if name in g else {})}


def save(fig, name):
    fig.savefig(OUT_TCC / f'{name}.pdf')
    fig.savefig(OUT / f'{name}.png')
    plt.close(fig)
    print('ok', name)


# ---------------------------------------------------------------- QP1
for proto in ('temporal', 'random'):          # one figure per protocol, PR-AUC above and ROC-AUC below
    fig, axes = plt.subplots(2, 1, figsize=(9, 8.4))
    for ax, (met, nd, ref) in zip(axes, (('pr_auc', 3, None), ('roc_auc', 2, 0.5))):
        g = last(groups_of(f'metodo_acaso__{proto}', met), 'Aleatório')
        box(ax, g, {'Aleatório': C_ALE}, nd, MET[met], ref)
    fig.tight_layout()
    save(fig, f'box_metodo_acaso_{proto}')

# ---------------------------------------------------------------- QP2
for fator, h in (('algoritmo', 8.4), ('conjunto', 5.6), ('reamostragem', 6.4)):  # one figure per factor
    fig, axes = plt.subplots(2, 1, figsize=(9, h))
    for ax, (met, nd, ref) in zip(axes, (('pr_auc', 3, None), ('roc_auc', 2, 0.5))):
        box(ax, groups_of(f'fator_{fator}__temporal', met), {}, nd, MET[met], ref,
            dark=True)   # Figures 23-25: points as dark as in the QP1 figures
    fig.tight_layout()
    save(fig, f'box_fatores_{fator}')

# ---------------------------------------------------------------- QP3
fig, ax = plt.subplots(figsize=(8.5, 4.6))
g = last(groups_of('feature_ordem', 'spearman'), 'Aleatório')
box(ax, g, {'Aleatório': C_ALE, 'Persistência': C_ING, 'Média histórica': C_ING}, 1,
    'Correlação de Spearman em cada $\\mathit{release}$ de teste', 0)
save(fig, 'box_feature_ordem')

# ---------------------------------------------------------------- QP4: factors at the feature level
fig, axes = plt.subplots(3, 1, figsize=(9, 11), gridspec_kw=dict(height_ratios=[7, 3.4, 4.2]))  # stacked
for ax, (fator, tit) in zip(axes, (('algoritmo', 'Algoritmo'), ('conjunto', 'Conjunto de métricas'),
                                   ('reamostragem', 'Balanceamento'))):
    box(ax, groups_of(f'fator_{fator}__feature', 'spearman'), {}, 1, MET['spearman'], 0, dark=True)
    ax.set_title(tit)
fig.tight_layout()
save(fig, 'box_fatores_feature')

# ---------------------------------------------------------------- identity breaks
for proto in ('temporal', 'random'):          # one figure per protocol, PR-AUC above and ROC-AUC below
    fig, axes = plt.subplots(2, 1, figsize=(9, 4.6))
    for ax, (met, nd) in zip(axes, (('pr_auc', 3), ('roc_auc', 2))):
        box(ax, groups_of(f'identidade__{proto}', met, ['Principal (restrito)', 'Sem PTP, Scout e Mylyn']),
            {'Principal (restrito)': C_MOD, 'Sem PTP, Scout e Mylyn': C_ING}, nd, MET[met])
    fig.tight_layout()
    save(fig, f'box_identidade_{proto}')
