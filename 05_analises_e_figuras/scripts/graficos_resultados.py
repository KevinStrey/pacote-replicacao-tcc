"""Presentation charts of the TCC result tables (NOT used in the thesis).

Reads resultados_e_logs/saida/resultados/*.csv and the final parquets; writes PNG (300 dpi) and SVG files to
graficos_apresentacao/resultados/. One chart per thesis table (and the two thesis figures, for the slides).
Usage: python graficos_resultados.py
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / 'resultados_e_logs' / 'saida' / 'resultados'
OUT = ROOT / 'graficos_apresentacao' / 'resultados'
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 12,
    'axes.titlesize': 14, 'axes.titleweight': 'bold', 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.alpha': 0.3, 'grid.linestyle': '--', 'axes.formatter.use_locale': False,
    'savefig.bbox': 'tight', 'savefig.dpi': 300,
})
ALG_PT = {'LightGBM': 'LightGBM', 'XGBoost': 'XGBoost', 'MLP': 'MLP', 'LogisticRegression': 'Regr. logística',
          'LinearSVC': 'SVM linear', 'RandomForest': 'Random Forest', 'DT': 'Árvore de decisão'}
C_TEMP, C_RAND, C_PERS, C_MOD, C_GRAY = '#C62828', '#1565C0', '#1565C0', '#C62828', '#9E9E9E'


def br(x, nd=2):
    """Number with decimal comma, rounded half up (same as the thesis tables)."""
    from decimal import ROUND_HALF_UP, Decimal
    v = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    return f'{v:.{nd}f}'.replace('.', ',')


def comma_axis(ax, axis='y', nd=2):
    f = mtick.FuncFormatter(lambda v, _: br(v, nd))
    (ax.yaxis if axis == 'y' else ax.xaxis).set_major_formatter(f)


def save(fig, name):
    for ext in ('png', 'svg'):
        fig.savefig(OUT / f'{name}.{ext}')
    plt.close(fig)
    print('ok', name)


def read_res(name):
    """Results CSV written with ',' by the server or re-saved with ';' (e.g. by Excel)."""
    p = RES / name
    with open(p, encoding='utf-8') as f:
        sep = ';' if ';' in f.readline() else ','
    return pd.read_csv(p, sep=sep)


t = read_res('resultados_teste.csv')
t = t[t.variante == 'principal']
base = {p: g.positivos.iloc[0] / g.linhas.iloc[0] for p, g in t.groupby('protocolo')}

# ---- Tabela 1: conjunto de dados por feature ----
rows = []
for p in sorted((ROOT / '5-Coleta_features').glob('*/data/*-all-releases.parquet')):
    if 'validacao' in str(p):
        continue
    d = pq.read_table(p, columns=['feature', 'will_change']).to_pandas()
    rows.append({'feature': d.feature.iloc[0], 'linhas': len(d), 'positivos': int(d.will_change.sum())})
ds = pd.DataFrame(rows).sort_values('linhas')
ds['taxa'] = 100 * ds.positivos / ds.linhas
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 7), sharey=True)
a1.barh(ds.feature, ds.linhas / 1e6, color='#546E7A')
a1.set_xlabel('Linhas (milhões de pares método × release)')
a1.set_title('Tamanho do conjunto de dados')
comma_axis(a1, 'x', 1)
for y, v in enumerate(ds.linhas / 1e6):
    a1.text(v, y, ' ' + br(v, 2), va='center', fontsize=9)
a2.barh(ds.feature, ds.taxa, color=C_TEMP)
a2.axvline(100 * ds.positivos.sum() / ds.linhas.sum(), color='black', ls=':', lw=1.2)
a2.text(100 * ds.positivos.sum() / ds.linhas.sum(), len(ds) - 0.4, ' média 0,49%', fontsize=9)
a2.set_xlabel('Métodos alterados no intervalo seguinte (%)')
a2.set_title('Taxa de mudança')
comma_axis(a2, 'x', 1)
for y, v in enumerate(ds.taxa):
    a2.text(v, y, ' ' + br(v, 2), va='center', fontsize=9)
fig.suptitle('Tabela 1 – 19 features, 18.059.107 linhas, 87.687 métodos alterados', fontweight='bold')
save(fig, 't1_dataset_por_feature')

# ---- Tabela 5: melhor configuração por algoritmo (PR-AUC e ROC-AUC com IC) ----
b = pd.read_csv(RES / 'bootstrap_ic.csv')
b = b[b.variante == 'principal'] if 'variante' in b else b
fig, axes = plt.subplots(1, 3, figsize=(16, 6), gridspec_kw={'width_ratios': [1, 1, 1]})
for ax, proto, cor in ((axes[0], 'temporal', C_TEMP), (axes[1], 'random', C_RAND)):
    g = b[b.protocolo == proto].sort_values('PR AUC (AP)')
    lab = [f'{ALG_PT[a]}\n({c}, {r})' for a, c, r in zip(g.algoritmo, g.conjunto, g.reamostragem)]
    err = [g['PR AUC (AP)'] - g['PR AUC (AP) IC95 inf'], g['PR AUC (AP) IC95 sup'] - g['PR AUC (AP)']]
    ax.barh(lab, g['PR AUC (AP)'], xerr=err, color=cor, alpha=0.85, capsize=3)
    ax.axvline(base[proto], color='black', ls=':', lw=1.2)
    ax.text(base[proto], len(g) - 0.45, ' acaso', fontsize=9, va='bottom')
    ax.set_title(f'PR-AUC – protocolo {"temporal" if proto == "temporal" else "aleatório"}')
    comma_axis(ax, 'x', 3 if proto == 'temporal' else 2)
    for y, v in enumerate(g['PR AUC (AP)']):
        ax.text(v, y + 0.25, br(v, 4), fontsize=8)
    ax.tick_params(axis='y', labelsize=9)
# ROC-AUC dos dois protocolos lado a lado
algs = [a for a in ALG_PT if a in set(b.algoritmo)]
y = np.arange(len(algs))
for k, (proto, cor) in enumerate((('temporal', C_TEMP), ('random', C_RAND))):
    g = b[b.protocolo == proto].set_index('algoritmo').reindex(algs)
    axes[2].barh(y + (k - 0.5) * 0.38, g['ROC AUC score'], height=0.38, color=cor, alpha=0.85,
                 label='temporal' if proto == 'temporal' else 'aleatório')
axes[2].set_yticks(y, [ALG_PT[a] for a in algs], fontsize=9)
axes[2].axvline(0.5, color='black', ls=':', lw=1.2)
axes[2].set_xlim(0.4, 0.95)
axes[2].set_title('ROC-AUC (0,5 = acaso)')
axes[2].legend(loc='lower right', fontsize=9)
comma_axis(axes[2], 'x', 2)
fig.suptitle('Tabela 5 – Melhor configuração de cada algoritmo no nível de método', fontweight='bold')
fig.tight_layout()
save(fig, 't4_melhores_por_algoritmo')

# Comparação direta temporal x aleatório (melhor PR-AUC e razão sobre o acaso)
fig, ax = plt.subplots(figsize=(8, 5))
vals = [b[b.protocolo == 'temporal']['PR AUC (AP)'].max(), b[b.protocolo == 'random']['PR AUC (AP)'].max()]
bars = ax.bar(['Temporal\n(prever releases futuras)', 'Aleatório\n(dados misturados)'], vals,
              color=[C_TEMP, C_RAND], width=0.55)
for bb, v, p in zip(bars, vals, ('temporal', 'random')):
    ax.text(bb.get_x() + bb.get_width() / 2, v, f'{br(v, 4)}\n({br(v / base[p], 1)}× o acaso)', ha='center',
            va='bottom', fontsize=11)
ax.set_ylabel('Melhor PR-AUC')
ax.set_ylim(0, 0.27)
comma_axis(ax, 'y', 2)
ax.set_title('O protocolo aleatório resulta em PR-AUC ≈ 13 vezes maior que o temporal')
save(fig, 't4b_temporal_vs_aleatorio')

# ---- Tabela 6: grade do protocolo temporal (mapas de calor) ----
tt = t[t.protocolo == 'temporal']
algs5 = ['DT', 'RandomForest', 'LogisticRegression', 'LinearSVC', 'MLP', 'XGBoost', 'LightGBM']
fig, axes = plt.subplots(1, 2, figsize=(13, 6))
for ax, met, nd, cmap in ((axes[0], 'PR AUC (AP)', 4, 'Reds'), (axes[1], 'ROC AUC score', 3, 'Blues')):
    pv = tt.pivot_table(index='algoritmo', columns='conjunto', values=met, aggfunc='max').reindex(algs5)
    im = ax.imshow(pv.values, cmap=cmap, aspect='auto')
    ax.set_xticks(range(3), ['model1\nestruturais', 'model2\nestrut. + evol.', 'model3\nevolutivas'])
    ax.set_yticks(range(len(algs5)), [ALG_PT[a] for a in algs5])
    ax.grid(False)
    for i in range(pv.shape[0]):
        for j in range(pv.shape[1]):
            v = pv.values[i, j]
            ax.text(j, i, br(v, nd), ha='center', va='center', fontsize=11,
                    color='white' if v > np.nanpercentile(pv.values, 70) else 'black')
    ax.set_title('PR-AUC' if met.startswith('PR') else 'ROC-AUC')
fig.suptitle('Tabela 6 – Protocolo temporal: melhor resultado por algoritmo e conjunto de métricas',
             fontweight='bold')
fig.tight_layout()
save(fig, 't5_grade_temporal')

# Efeito do balanceamento (PR-AUC média por reamostragem, temporal)
pv = tt.pivot_table(index='algoritmo', columns='reamostragem', values='PR AUC (AP)', aggfunc='mean').reindex(algs5)
pv = pv[['NONE', 'ROS', 'SMOTE', 'ADA']]
fig, ax = plt.subplots(figsize=(12, 5.5))
x = np.arange(len(algs5))
cores = ['#78909C', '#43A047', '#FB8C00', '#8E24AA']
for k, rs in enumerate(pv.columns):
    ax.bar(x + (k - 1.5) * 0.2, pv[rs], width=0.2, color=cores[k],
           label={'NONE': 'Sem reamostragem', 'ROS': 'ROS', 'SMOTE': 'SMOTE', 'ADA': 'ADASYN'}[rs])
ax.set_xticks(x, [ALG_PT[a] for a in algs5])
ax.set_ylabel('PR-AUC média (3 conjuntos de métricas)')
comma_axis(ax, 'y', 3)
ax.legend(ncol=4, loc='upper left')
ax.set_title('Efeito do balanceamento no protocolo temporal')
save(fig, 't5b_balanceamento_temporal')

# ---- Tabela 7: desempenho por feature do melhor modelo temporal ----
pf = read_res('por_feature.csv')
best = t[t.protocolo == 'temporal'].sort_values('PR AUC (AP)', ascending=False).iloc[0].id
f6 = pf[pf.id == best].copy()
f6['taxa'] = f6.positivos / f6.linhas
f6['lift'] = f6['PR AUC (AP)'] / f6.taxa
f6 = f6.sort_values('ROC AUC score')
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 6.5), sharey=True)
a1.barh(f6.feature, f6['ROC AUC score'], color=C_TEMP, alpha=0.85)
a1.axvline(0.5, color='black', ls=':', lw=1.2)
a1.set_xlim(0.45, 0.97)
a1.set_title('ROC-AUC')
comma_axis(a1, 'x', 2)
for y_, v in enumerate(f6['ROC AUC score']):
    a1.text(v, y_, ' ' + br(v, 3), va='center', fontsize=9)
a2.barh(f6.feature, f6.lift, color='#6A1B9A', alpha=0.85)
a2.set_xscale('log')
a2.set_title('PR-AUC em relação ao acaso (escala log)')
a2.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f'{br(v, 0)}×'))
for y_, v in enumerate(f6.lift):
    a2.text(v, y_, ' ' + br(v, 1) + '×', va='center', fontsize=9)
fig.suptitle('Tabela 7 – Desempenho por feature do melhor modelo temporal (LightGBM, model2, ROS)',
             fontweight='bold')
fig.tight_layout()
save(fig, 't6_desempenho_por_feature')

# ---- Tabela 8: nível de feature – Spearman com IC (gráfico de floresta) ----
fs = pd.read_csv(RES / 'nivel_feature_resumo.csv')
m = fs[(fs.id != 'BASELINE') & (fs.medida == 'taxa (score_medio)')]
bpa = m.sort_values('spearman_medio', ascending=False).groupby('algoritmo').head(1)
bl = fs[fs.id == 'BASELINE'].set_index('medida')
rows = [('Persistência', bl.loc['taxa (persistencia)'], C_PERS), ('Média histórica', bl.loc['taxa (media_historica)'], C_GRAY)]
rows += [(f'{ALG_PT[r.algoritmo]} ({r.conjunto}, {r.reamostragem})', r, C_MOD) for _, r in bpa.iterrows()]
fig, ax = plt.subplots(figsize=(10, 6.5))
for i, (lab, r, cor) in enumerate(rows[::-1]):
    ax.errorbar(r.spearman_medio, i, xerr=[[r.spearman_medio - r.spearman_IC95_inf], [r.spearman_IC95_sup - r.spearman_medio]],
                fmt='o', color=cor, capsize=4, ms=8)
    ax.text(r.spearman_IC95_sup + 0.02, i, br(r.spearman_medio, 3), va='center', fontsize=10)
ax.set_yticks(range(len(rows)), [r[0] for r in rows[::-1]])
ax.axvline(bl.loc['taxa (persistencia)'].spearman_medio, color=C_PERS, ls='--', lw=1)
ax.axvline(0, color='black', lw=0.8)
ax.set_xlim(-0.1, 0.95)
ax.set_xlabel('Correlação de Spearman média entre a ordem prevista e a real (IC 95%)')
comma_axis(ax, 'x', 1)
ax.set_title('Tabela 8 – Ordenação das features: nenhum modelo supera a persistência')
save(fig, 't7_nivel_feature_spearman')

# Figura 19 do TCC (Spearman por release) em versão para slide
sr = pd.read_csv(ROOT / 'TCC___Kevin___UDESC' / 'Textuais' / 'dados' / 'spearman_por_release.dat', sep=' ')
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(sr.release, sr.modelo, '-o', color=C_MOD, label='SVM linear (model3, ROS)', lw=2)
ax.plot(sr.release, sr.persistencia, '--s', color=C_PERS, label='Persistência', lw=2)
ax.plot(sr.release, sr.melhor_metodo, ':^', color=C_GRAY, label='LightGBM (model2, ROS)', lw=1.5)
ax.set_ylim(0, 1)
ax.set_xlabel('Release de teste (índice global)')
ax.set_ylabel('Spearman')
comma_axis(ax, 'y', 1)
ax.legend(loc='lower right')
ax.set_title('Spearman por release: o modelo é mais estável, a persistência é melhor em média')
save(fig, 'fig8_spearman_por_release')

# ---- Tabela 9: ranking real x previsto (gráfico de inclinação) ----
rk = pd.read_csv(RES / 'nivel_feature_ranking.csv')
fig, ax = plt.subplots(figsize=(8, 8))
for _, r in rk.iterrows():
    desloc = abs(r.posicao_real - r.posicao_prevista)
    cor = '#2E7D32' if desloc == 0 else ('#F9A825' if desloc <= 2 else C_TEMP)
    ax.plot([0, 1], [r.posicao_real, r.posicao_prevista], '-o', color=cor, lw=2.2 if desloc > 2 else 1.6)
    ax.text(-0.04, r.posicao_real, f'{r.feature} ({int(r.posicao_real)})', ha='right', va='center', fontsize=11)
    ax.text(1.04, r.posicao_prevista, f'({int(r.posicao_prevista)}) {r.feature}', ha='left', va='center', fontsize=11)
ax.set_xlim(-0.6, 1.6)
ax.set_ylim(14.7, 0.3)
ax.set_xticks([0, 1], ['Posição real', 'Posição prevista'], fontsize=13, fontweight='bold')
ax.set_yticks([])
ax.grid(False)
for s in ('left', 'bottom'):
    ax.spines[s].set_visible(False)
ax.set_title('Tabela 9 – Features mais propensas a mudar: real × previsto\n'
             '(verde: posição exata; amarelo: até 2 posições; vermelho: mais de 2)')
save(fig, 't8_ranking_real_previsto')

# ---- Tabela 10: análise de sensibilidade ----
s9 = pd.read_csv(RES / 'sensibilidade.csv')
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for ax, proto in zip(axes, ('temporal', 'random')):
    g = s9[(s9.protocolo == proto) & (s9.metrica == 'PR AUC (AP)')].iloc[0]
    vals = [g.principal_teste_completo, g.principal_restrito, g.variante]
    bars = ax.bar(['Principal\n(teste completo)', 'Principal\n(mesmas linhas)', 'Sem PTP, Scout\ne Mylyn'], vals,
                  color=['#90A4AE', '#546E7A', C_TEMP if proto == 'temporal' else C_RAND], width=0.6)
    for bb, v in zip(bars, vals):
        ax.text(bb.get_x() + bb.get_width() / 2, v, br(v, 4), ha='center', va='bottom', fontsize=11)
    ax.set_ylabel('PR-AUC')
    comma_axis(ax, 'y', 3 if proto == 'temporal' else 2)
    ax.set_title(f'{"Temporal – LightGBM" if proto == "temporal" else "Aleatório – XGBoost"} (model2, ROS)')
fig.suptitle('Tabela 10 – Sensibilidade: sem as features com quebras de identidade, o desempenho sobe pouco',
             fontweight='bold')
fig.tight_layout()
save(fig, 't9_sensibilidade')

# Figura 13 do TCC (taxa de positivos por release) em versão para slide
pr = pd.read_csv(ROOT / 'TCC___Kevin___UDESC' / 'Textuais' / 'dados' / 'positivos_por_release.dat', sep=' ')
fig, ax = plt.subplots(figsize=(12, 4.5))
ax.plot(pr.release, pr.taxa, '-o', color=C_TEMP, ms=3)
ax.axvline(36.5, color='black', ls='--', lw=1)
ax.text(36, ax.get_ylim()[1] * 0.92, 'treino ', ha='right')
ax.text(37, ax.get_ylim()[1] * 0.92, ' teste')
ax.set_xlabel('Release (índice global)')
ax.set_ylabel('Métodos alterados (%)')
comma_axis(ax, 'y', 1)
ax.set_title('Taxa de métodos alterados por release (todas as features)')
save(fig, 'fig7_taxa_por_release')
