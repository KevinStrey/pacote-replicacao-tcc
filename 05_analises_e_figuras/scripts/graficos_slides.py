"""Charts drawn for the slide template of the 36th SIC (teal/orange palette). Not in the thesis.

Output: graficos_apresentacao/slides/taxa_por_release.png|svg
Usage: python graficos_slides.py
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PREP = ROOT / 'predições' / 'prep'
OUT = ROOT / 'graficos_apresentacao' / 'slides'
OUT.mkdir(parents=True, exist_ok=True)
INK, MUTED, GRID = '#262626', '#6B7280', '#E5E7EB'
TEAL, ORANGE = '#339999', '#D16722'
T = 36
plt.rcParams.update({
    'font.family': 'sans-serif', 'font.sans-serif': ['Segoe UI', 'Arial', 'DejaVu Sans'], 'font.size': 14,
    'text.color': INK, 'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED, 'axes.edgecolor': GRID,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': GRID,
    'axes.axisbelow': True, 'figure.facecolor': 'white', 'savefig.facecolor': 'white'})

y = np.load(PREP / 'y.npy')
rel = np.load(PREP / 'release.npy')
r = np.arange(1, rel.max() + 1)
rate = np.bincount(rel, weights=y, minlength=r.max() + 1)[1:] / np.bincount(rel, minlength=r.max() + 1)[1:]

fig, ax = plt.subplots(figsize=(12, 4.6))
ax.axvspan(0.4, T + 0.5, color=TEAL, alpha=0.08, lw=0)
ax.axvspan(T + 0.5, r.max() + 0.6, color=ORANGE, alpha=0.08, lw=0)
ax.bar(r, rate, color=np.where(r <= T, TEAL, ORANGE), width=0.72)
ax.axvline(T + 0.5, color=INK, lw=1.2, ls=(0, (4, 3)))
tr, te = y[rel <= T].mean(), y[rel > T].mean()
ax.text(T / 2, 0.0262, f'Treino: releases 1–{T} (2012–2022)  ·  média {100 * tr:.2f}%'.replace('.', ','),
        ha='center', va='bottom', color=TEAL, fontsize=14, fontweight='bold')
ax.text((T + r.max()) / 2 + 0.5, 0.0262, f'Teste: {T + 1}–{r.max()}\nmédia {100 * te:.2f}%'.replace('.', ','),
        ha='center', va='bottom', color=ORANGE, fontsize=14, fontweight='bold')
ax.set_xlim(0.4, r.max() + 0.6)
ax.set_ylim(0, 0.0315)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f'{100 * v:.1f}%'.replace('.', ',')))
ax.set_ylabel('Métodos que mudam até\na release seguinte')
ax.set_xlabel('Release (índice no calendário global, 2012 a 2026)')
ax.grid(axis='x', visible=False)
for ext in ('png', 'svg'):
    fig.savefig(OUT / f'taxa_por_release.{ext}', dpi=300, bbox_inches='tight')
print('ok taxa_por_release', round(tr, 5), round(te, 5))
