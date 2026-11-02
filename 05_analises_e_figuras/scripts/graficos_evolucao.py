"""Presentation charts of the evolution of the SPL features over the releases (NOT used in the thesis).

Aggregates the final dataset (5-Coleta_features/<feature>/data/<feature>-all-releases.parquet) per feature x release
and draws one line per feature, with the simrel release names on the x axis (style of the CSB chart of the pilot).
Outputs in graficos_apresentacao/evolucao/: PNG (300 dpi) + SVG and dados_evolucao.csv (the aggregated values).
Note: the dataset holds the labelled releases, so the last snapshot of each feature (which has no label) is not shown.
Usage: python graficos_evolucao.py
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
COLETA = ROOT / '5-Coleta_features'
OUT = ROOT / 'graficos_apresentacao' / 'evolucao'
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 12,
    'axes.titlesize': 15, 'axes.titleweight': 'bold', 'axes.grid': True, 'grid.alpha': 0.3, 'grid.linestyle': '--',
    'savefig.bbox': 'tight', 'savefig.dpi': 300,
})
COLS = ['feature', 'release', 'loc', 'Cyclomatic', 'cbo', 'CSB', 'TACH', 'CHO', 'BOM', 'will_change']

cal = pd.read_csv(COLETA / 'mapeamento' / 'output' / 'calendario.csv')
TAGS = dict(zip(cal.idx, cal.tag))
DATES = dict(zip(cal.idx, cal.data.str[:7]))

# ---------------- aggregation ----------------
rows = []
for p in sorted(COLETA.glob('*/data/*-all-releases.parquet')):
    if 'validacao' in str(p):
        continue
    d = pd.read_parquet(p, columns=COLS)
    first = d.release.min()
    for r, g in d.groupby('release'):
        rows.append({
            'feature': g.feature.iloc[0], 'release': int(r), 'tag': TAGS[int(r)], 'data': DATES[int(r)],
            'metodos': len(g),
            'loc_total': g['loc'].sum(),
            'loc_medio': g['loc'].mean(),
            'ciclomatica_media': g.Cyclomatic.mean(),
            'cbo_medio': g.cbo.mean(),
            'csb_medio': g.CSB.mean(),
            'linhas_alteradas': g.TACH.sum(),                     # lines changed in (previous snapshot, r]
            'metodos_alterados_intervalo_anterior': int(g.CHO.sum()),
            'metodos_alterados_proximo': int(g.will_change.sum()),  # label: change until the next snapshot
            'taxa_mudanca': 100 * g.will_change.mean(),
            # methods born in this release (in the first release of the series every method is "born": not shown)
            'metodos_novos': int((g.BOM == r).sum()) if r != first else np.nan,
        })
    print('ok', p.parent.parent.name, flush=True)
ev = pd.DataFrame(rows).sort_values(['feature', 'release'])
ev['alteracoes_acumuladas'] = ev.groupby('feature').metodos_alterados_proximo.cumsum()
ev.to_csv(OUT / 'dados_evolucao.csv', index=False, float_format='%.4f')

FEATS = sorted(ev.feature.unique(), key=str.lower)
cmap = plt.get_cmap('tab20')
STYLE = {f: dict(color=cmap(i % 20), ls=('-', '--', '-.', ':')[i // 10 % 4] if i >= 10 else '-')
         for i, f in enumerate(FEATS)}
XT = list(range(1, 55))


def br(v, nd=0):
    s = f'{v:,.{nd}f}'
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')


def line_chart(col, title, ylabel, name, nd=2, logy=False, scale=1.0, note=None):
    fig, ax = plt.subplots(figsize=(18, 6.5))
    for f in FEATS:
        g = ev[ev.feature == f]
        y = g[col] / scale
        if logy:
            y = y.where(y > 0)          # zero has no log: the line is interrupted instead of dropping to the axis
        ax.plot(g.release, y, lw=1.8, label=f, **STYLE[f])
    ax.set_xticks(XT, [TAGS[i] for i in XT], rotation=45, ha='right', fontsize=8.5)
    ax.set_xlim(0.5, 54.5)
    ax.set_xlabel('Release')
    ax.set_ylabel(ylabel)
    if logy:
        ax.set_yscale('log')
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, nd)))
    ax.set_title(title)
    ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1.0), fontsize=10, frameon=True)
    if note:
        fig.text(0.01, -0.07, note, fontsize=9, style='italic')
    for ext in ('png', 'svg'):
        fig.savefig(OUT / f'{name}.{ext}')
    plt.close(fig)
    print('ok', name)


NOTA = 'Uma linha por feature da LPS. A última release de cada feature (sem rótulo) não aparece no conjunto de dados.'
line_chart('metodos', 'Número de métodos por release', 'Métodos', 'e01_numero_de_metodos', 0, note=NOTA)
line_chart('loc_total', 'Tamanho do código (soma do LOC dos métodos)', 'Linhas de código (milhares)',
           'e02_loc_total', 0, scale=1000, note=NOTA)
line_chart('loc_medio', 'Média de linhas de código por método', 'LOC médio por método', 'e03_loc_medio_por_metodo',
           1, note=NOTA)
line_chart('ciclomatica_media', 'Complexidade ciclomática média por método', 'Complexidade ciclomática média',
           'e04_complexidade_media', 2, note=NOTA)
line_chart('cbo_medio', 'Acoplamento médio por método (CBO)', 'CBO médio', 'e05_acoplamento_medio', 2, note=NOTA)
line_chart('csb_medio', 'Média de CSB por método (tamanho acumulado das mudanças desde o nascimento)',
           'Média de CSB por método', 'e06_csb_medio', 1, note=NOTA)
line_chart('linhas_alteradas', 'Linhas alteradas nos métodos entre a release anterior e a atual (TACH somado)',
           'Linhas alteradas (escala log)', 'e07_linhas_alteradas', 0, logy=True,
           note=NOTA + ' Releases sem nenhuma alteração interrompem a linha (zero não existe em escala log).')
line_chart('metodos_alterados_proximo', 'Métodos alterados até a release seguinte (rótulo do modelo)',
           'Métodos alterados', 'e08_metodos_alterados', 0, note=NOTA)
line_chart('taxa_mudanca', 'Taxa de mudança: % dos métodos alterados até a release seguinte',
           'Métodos alterados (%)', 'e09_taxa_de_mudanca', 1, note=NOTA)
line_chart('alteracoes_acumuladas', 'Métodos alterados acumulados ao longo do tempo', 'Alterações acumuladas',
           'e10_alteracoes_acumuladas', 0, note=NOTA)
line_chart('metodos_novos', 'Métodos novos por release', 'Métodos novos (escala log)', 'e11_metodos_novos', 0,
           logy=True, note=NOTA + ' A primeira release de cada feature não é mostrada (todos os métodos seriam novos).')

# ---------------- heat map: change rate per feature x release ----------------
pv = ev.pivot_table(index='feature', columns='release', values='taxa_mudanca').reindex(FEATS[::-1])
pv = pv.reindex(columns=XT)
fig, ax = plt.subplots(figsize=(18, 7.5))
masked = np.ma.masked_invalid(pv.values)
im = ax.imshow(masked, aspect='auto', cmap='YlOrRd', vmin=0, vmax=np.nanpercentile(pv.values, 98))
ax.set_facecolor('#F5F5F5')
ax.set_yticks(range(len(pv.index)), pv.index)
ax.set_xticks(range(len(XT)), [TAGS[i] for i in XT], rotation=45, ha='right', fontsize=8.5)
ax.grid(False)
ax.axvline(XT.index(36) + 0.5, color='black', ls='--', lw=1.2)
ax.text(XT.index(36) + 0.3, 1.005, 'treino', ha='right', va='bottom', fontsize=11, fontweight='bold',
        transform=ax.get_xaxis_transform())
ax.text(XT.index(36) + 0.7, 1.005, 'teste', ha='left', va='bottom', fontsize=11, fontweight='bold',
        transform=ax.get_xaxis_transform())
cb = fig.colorbar(im, ax=ax, pad=0.01)
cb.set_label('Métodos alterados até a release seguinte (%)')
cb.ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 1)))
ax.set_title('Mapa de calor da taxa de mudança por feature e release', pad=22)
fig.text(0.01, -0.07, 'Cinza: feature ausente da LPS, release com o mesmo commit da anterior (sem novo snapshot) ou '
         'última release (sem rótulo). Escala limitada ao percentil 98 para os picos não esconderem o restante. '
         'Linha tracejada: corte temporal do treino (T = 36).',
         fontsize=9, style='italic')
for ext in ('png', 'svg'):
    fig.savefig(OUT / f'e12_mapa_calor_taxa_mudanca.{ext}')
plt.close(fig)
print('ok e12')

# ---------------- presence of the features in the SPL over time ----------------
mp = pd.read_csv(COLETA / 'mapeamento' / 'output' / 'mapeamento.csv')
fig, ax = plt.subplots(figsize=(18, 7))
for y, f in enumerate(FEATS[::-1]):
    g = mp[mp.feature == f]
    serie = g[g.status != 'fora']
    lo, hi = int(serie.idx.min()), int(serie.idx.max())
    ax.barh(y, hi - lo + 1, left=lo - 0.5, color=STYLE[f]['color'], alpha=0.35, height=0.6)
    snaps = g[g.status == 'snapshot'].idx
    ax.plot(snaps, [y] * len(snaps), '|', color=STYLE[f]['color'], ms=12, mew=2)
    ax.text(hi + 0.8, y, str(len(snaps)), va='center', fontsize=9)
ax.set_yticks(range(len(FEATS)), FEATS[::-1])
ax.set_xticks(XT, [TAGS[i] for i in XT], rotation=45, ha='right', fontsize=8.5)
ax.set_xlim(0.5, 56)
ax.set_title('Presença das features na LPS (Eclipse Simultaneous Release) e snapshots coletados')
fig.text(0.01, -0.07, 'Faixa: período em que a feature fez parte da LPS. Traços: snapshots distintos coletados '
         '(releases com o mesmo commit da anterior não geram novo snapshot). Número à direita: total de snapshots.',
         fontsize=9, style='italic')
for ext in ('png', 'svg'):
    fig.savefig(OUT / f'e13_presenca_das_features.{ext}')
plt.close(fig)
print('ok e13')

# ---------------- stacked area: size of the SPL over time ----------------
pa = ev.pivot_table(index='release', columns='feature', values='metodos', aggfunc='sum').reindex(XT)
# releases without a new snapshot (same commit as the previous one) and the last, unlabelled release keep the size
# of the previous snapshot, inside the presence period of the feature in the SPL
for f in FEATS:
    serie = mp[mp.feature == f].idx
    lo, hi = int(serie.min()), int(serie.max())
    col = pa[f].copy()
    col.loc[lo:hi] = col.loc[lo:hi].ffill()
    pa[f] = col
pa = pa[FEATS].fillna(0)
fig, ax = plt.subplots(figsize=(18, 7))
ax.stackplot(pa.index, *[pa[f] / 1000 for f in FEATS], labels=FEATS, colors=[STYLE[f]['color'] for f in FEATS],
             alpha=0.85)
ax.set_xticks(XT, [TAGS[i] for i in XT], rotation=45, ha='right', fontsize=8.5)
ax.set_xlim(1, 54)
ax.set_ylabel('Métodos (milhares)')
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 0)))
ax.set_title('Tamanho da LPS ao longo do tempo: métodos por feature (área empilhada)')
ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1.0), fontsize=10, reverse=True)
fig.text(0.01, -0.07, 'Releases sem novo snapshot (mesmo commit da anterior) e a última release de cada feature '
         'repetem o tamanho do snapshot anterior, dentro do período em que a feature fez parte da LPS.', fontsize=9,
         style='italic')
for ext in ('png', 'svg'):
    fig.savefig(OUT / f'e14_tamanho_da_lps_empilhado.{ext}')
plt.close(fig)
print('ok e14')
