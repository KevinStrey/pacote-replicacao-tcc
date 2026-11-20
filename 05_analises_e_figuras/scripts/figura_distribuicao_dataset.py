"""Figure of the thesis: distribution of the dataset (class balance and observations/positives per feature).

Reads the numbers of Table 1 (Elementos/Tabelas/tab-03-met-features.tex), so the figure always matches the table.
Top: share of positive and negative observations in the whole dataset (the class imbalance).
Bottom: observations per feature (left) and rate of positive observations per feature (right), sorted by size.
Output: TCC___Kevin___UDESC/Textuais/imagens/distribuicao_dataset.pdf
Usage: python figura_distribuicao_dataset.py
"""
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TEX = ROOT / 'TCC___Kevin___UDESC'
OUT = TEX / 'Textuais' / 'imagens' / 'distribuicao_dataset.pdf'

plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 9,
    'axes.spines.top': False, 'axes.spines.right': False, 'pdf.fonttype': 42, 'savefig.bbox': 'tight',
})
C_OBS, C_POS, C_NEG = '#4A6E8A', '#B3412E', '#C9D3DC'


def num(s):
    return float(s.replace('.', '').replace(',', '.'))


def br(v, nd=0):
    s = f'{v:,.{nd}f}'
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')


rows = []
for line in (TEX / 'Elementos' / 'Tabelas' / 'tab-03-met-features.tex').read_text(encoding='utf-8').splitlines():
    cells = [c.strip() for c in line.split('&')]
    if len(cells) == 7 and re.fullmatch(r'[\d.]+', cells[4] or '') and 'Total' not in cells[0]:
        rows.append((cells[0], num(cells[4]), num(cells[5])))
rows.sort(key=lambda r: r[1])                       # largest at the top of the horizontal bars
names = [r[0] for r in rows]
obs = [r[1] for r in rows]
pos = [r[2] for r in rows]
rate = [100 * p / o for p, o in zip(pos, obs)]
tot_obs, tot_pos = sum(obs), sum(pos)
tot_rate = 100 * tot_pos / tot_obs
assert len(rows) == 19 and int(tot_obs) == 18059107 and int(tot_pos) == 87687, (len(rows), tot_obs, tot_pos)

fig = plt.figure(figsize=(6.3, 5.6))
gs = fig.add_gridspec(2, 2, height_ratios=[0.55, 5], hspace=0.32, wspace=0.08)

# --- class balance of the whole dataset
ax0 = fig.add_subplot(gs[0, :])
ax0.barh(0, 100 - tot_rate, color=C_NEG, height=0.6)
ax0.barh(0, tot_rate, left=100 - tot_rate, color=C_POS, height=0.6)
ax0.set_xlim(0, 100)
ax0.set_yticks([])
ax0.spines[['left']].set_visible(False)
ax0.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax0.tick_params(axis='x', labelsize=8)
ax0.text(50, 0, f'Não alteradas: {br(tot_obs - tot_pos)} ({br(100 - tot_rate, 2)}%)', ha='center', va='center',
         fontsize=8.5)
ax0.annotate(f'Alteradas: {br(tot_pos)} ({br(tot_rate, 2)}%)', xy=(100 - tot_rate / 2, 0.3), xytext=(99, 1.0),
             textcoords='data', fontsize=8.5, color=C_POS, ha='right',
             arrowprops=dict(arrowstyle='-', color=C_POS, lw=0.8))
ax0.set_title('Proporção das classes no conjunto completo', fontsize=9, loc='left', pad=12)

# --- observations per feature
ax1 = fig.add_subplot(gs[1, 0])
y = range(len(names))
ax1.barh(y, [o / 1e6 for o in obs], color=C_OBS, height=0.7)
ax1.set_yticks(list(y), names)
ax1.set_xlabel('Instâncias (milhões)')
ax1.set_xlim(0, max(obs) / 1e6 * 1.32)
for i, o in enumerate(obs):
    ax1.text(o / 1e6 + 0.05, i, br(o / 1e6, 2), va='center', fontsize=7.5)
ax1.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: br(v, 0)))
ax1.set_title('Instâncias por feature', fontsize=9, loc='left')

# --- rate of positives per feature
ax2 = fig.add_subplot(gs[1, 1], sharey=ax1)
ax2.barh(y, rate, color=C_POS, height=0.7)
ax2.axvline(tot_rate, color='black', lw=0.8, ls='--', zorder=0)
ax2.text(tot_rate + 0.03, len(names) - 0.4, f'proporção global: {br(tot_rate, 2)}%', fontsize=7.5, va='bottom')
ax2.tick_params(axis='y', left=False, labelleft=False)
ax2.set_xlabel('Instâncias alteradas (%)')
ax2.set_xlim(0, max(rate) * 1.3)
for i, r in enumerate(rate):
    ax2.text(r + 0.02, i, br(r, 2), va='center', fontsize=7.5,
             bbox=dict(facecolor='white', edgecolor='none', pad=0.6))
ax2.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: br(v, 1)))
ax2.set_title('Taxa de instâncias alteradas', fontsize=9, loc='left')
ax2.set_ylim(-0.6, len(names) - 0.4 + 0.9)

fig.savefig(OUT)
print('ok', OUT)
