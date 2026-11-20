"""Figure of the thesis: presence of the features in the SPL and collected snapshots (vector PDF).

Same chart as e13_presenca_das_features in graficos_evolucao.py (same data, colours and axes), cropped the same way as
the version previously used in the thesis: no title and no footnote. Only depends on the mapping files, not on the
parquet dataset.
Output: TCC___Kevin___UDESC/Textuais/imagens/e13_presenca_das_features.pdf
Usage: python figura_presenca_tcc.py
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / '5-Coleta_features' / 'mapeamento' / 'output'
OUT = ROOT / 'TCC___Kevin___UDESC' / 'Textuais' / 'imagens' / 'e13_presenca_das_features.pdf'

plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 12,
    'axes.grid': True, 'grid.alpha': 0.3, 'grid.linestyle': '--',
    'savefig.bbox': 'tight', 'pdf.fonttype': 42,
})

cal = pd.read_csv(MAP / 'calendario.csv')
TAGS = dict(zip(cal.idx, cal.tag))
mp = pd.read_csv(MAP / 'mapeamento.csv')
FEATS = sorted(mp.feature.unique(), key=str.lower)          # same 19 features and order as graficos_evolucao.py
cmap = plt.get_cmap('tab20')
COLOR = {f: cmap(i % 20) for i, f in enumerate(FEATS)}
XT = list(range(1, 55))

fig, ax = plt.subplots(figsize=(18, 7))
for y, f in enumerate(FEATS[::-1]):
    g = mp[mp.feature == f]
    serie = g[g.status != 'fora']
    lo, hi = int(serie.idx.min()), int(serie.idx.max())
    ax.barh(y, hi - lo + 1, left=lo - 0.5, color=COLOR[f], alpha=0.35, height=0.6)
    snaps = g[g.status == 'snapshot'].idx
    ax.plot(snaps, [y] * len(snaps), '|', color=COLOR[f], ms=12, mew=2)
    ax.text(hi + 0.8, y, str(len(snaps)), va='center', fontsize=9)
ax.set_yticks(range(len(FEATS)), FEATS[::-1])
ax.set_xticks(XT, [TAGS[i] for i in XT], rotation=45, ha='right', fontsize=10)
ax.set_xlim(0.5, 56)
fig.savefig(OUT)
print('ok', OUT, 'snapshots:', int((mp.status == 'snapshot').sum()))
