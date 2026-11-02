"""Local analysis of the server results (saida/resultados) for the TCC results chapter.

Reads 6-Treino/resultados_e_logs/saida/resultados/*.csv (+ the final parquets for the per-release positive rate) and
writes:
  6-Treino/analise/RESUMO_ANALISE.md       numbers used in the text (auditable)
  TCC___Kevin___UDESC/Textuais/dados/*.dat     data for the pgfplots figures
Usage: python analisar_resultados.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / 'resultados_e_logs' / 'saida' / 'resultados'   # final results (phases 1-3)
OUT = ROOT / '6-Treino' / 'analise'
DAT = ROOT / 'TCC___Kevin___UDESC' / 'Textuais' / 'dados'
OUT.mkdir(exist_ok=True)
DAT.mkdir(exist_ok=True)
sys.stdout.reconfigure(encoding='utf-8')
L = []


def say(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    L.append(s)


def md(df, floatfmt='.4f'):
    """Markdown table without the optional 'tabulate' dependency."""
    cols = list(df.columns)
    fmt = lambda v: format(v, floatfmt) if isinstance(v, (float, np.floating)) else str(v)  # noqa: E731
    rows = ['| ' + ' | '.join(str(c) for c in cols) + ' |', '|' + '---|' * len(cols)]
    rows += ['| ' + ' | '.join(fmt(v) for v in r) + ' |' for r in df.itertuples(index=False)]
    return '\n'.join(rows)


t = pd.read_csv(RES / 'resultados_teste.csv')
t = t[t.variante == 'principal']
EVO = ['BOM', 'TACH', 'FCH', 'LCH', 'CHO', 'FRCH', 'CHD', 'WCH', 'WCD', 'WFR', 'ATAF', 'LCA', 'LCD', 'CSB', 'CSBS', 'ACDF']
ALG = ['DT', 'RandomForest', 'LogisticRegression', 'LinearSVC', 'MLP', 'XGBoost', 'LightGBM']
base = {p: g.positivos.iloc[0] / g.linhas.iloc[0] for p, g in t.groupby('protocolo')}
say('# Resumo da análise dos resultados (fase 1)\n')
say('Taxa de positivos no teste (referência do acaso para PR-AUC):', {k: round(v, 5) for k, v in base.items()})

# ---- A. melhor PR-AUC / ROC / MCC por algoritmo x conjunto (máximo sobre as reamostragens) ----
for proto in ('temporal', 'random'):
    g = t[t.protocolo == proto]
    for met in ('PR AUC (AP)', 'ROC AUC score', 'MCC'):
        pv = g.pivot_table(index='algoritmo', columns='conjunto', values=met, aggfunc='max').reindex(ALG)
        say(f'\n## {proto}: {met}, máximo sobre reamostragens\n')
        say(md(pv.reset_index()))
    pv = g.pivot_table(index='algoritmo', columns='reamostragem', values='PR AUC (AP)', aggfunc='mean').reindex(ALG)
    say(f'\n## {proto}: PR-AUC média por reamostragem (sobre os 3 conjuntos)\n')
    say(md(pv[['NONE', 'ROS', 'SMOTE', 'ADA']].reset_index()))
    say(f'\n{proto}: lift da melhor PR-AUC sobre o acaso = {g["PR AUC (AP)"].max() / base[proto]:.1f}x')

# ---- B. CV x teste no aleatório ----
r = t[(t.protocolo == 'random') & t.cv_ap_media.notna()]
say(f'\nAleatório: correlação entre PR-AUC média da CV e PR-AUC no teste = {np.corrcoef(r.cv_ap_media, r["PR AUC (AP)"])[0, 1]:.3f};'
    f' maior |CV - teste| = {np.abs(r.cv_ap_media - r["PR AUC (AP)"]).max():.4f}; DP médio entre partes = {r.cv_ap_dp.mean():.4f}')

# ---- C. tempo computacional ----
cvp = pd.read_csv(RES / 'cv_partes.csv')
tot = (t.segundos.sum() + cvp.segundos.sum()) / 3600
say(f'\nTempo de CPU-job somado (fase 1): {tot:.0f} h; job mais longo: {max(t.segundos.max(), cvp.segundos.max()) / 3600:.1f} h; '
    f'pico de RAM máximo: {max(t.pico_ram_gb.max(), cvp.pico_ram_gb.max()):.0f} GB')
tm = t.groupby('algoritmo').segundos.median().reindex(ALG) / 60
say('Mediana de minutos por job de teste, por algoritmo:', tm.round(1).to_dict())

# ---- D. por feature (melhor temporal) ----
pf = pd.read_csv(RES / 'por_feature.csv')
best_t = t[t.protocolo == 'temporal'].sort_values('PR AUC (AP)', ascending=False).iloc[0]
say(f'\nMelhor temporal: {best_t.id} PR-AUC={best_t["PR AUC (AP)"]:.4f} ROC={best_t["ROC AUC score"]:.4f} MCC={best_t.MCC:.4f}')
b = pf[pf.id == best_t.id].copy()
b['taxa'] = b.positivos / b.linhas
b['lift'] = b['PR AUC (AP)'] / b.taxa
b = b.sort_values('ROC AUC score', ascending=False)
say('\n## Por feature (melhor temporal)\n')
say(md(b[['feature', 'linhas', 'positivos', 'taxa', 'PR AUC (AP)', 'lift', 'ROC AUC score', 'MCC']], '.4f'))
b[['feature', 'linhas', 'positivos', 'taxa', 'PR AUC (AP)', 'lift', 'ROC AUC score', 'MCC']].to_csv(OUT / 'por_feature_melhor_temporal.csv', index=False)

# ---- E. nível de feature ----
fs = pd.read_csv(RES / 'nivel_feature_resumo.csv')
fd = pd.read_csv(RES / 'nivel_feature_por_release.csv')
say('\n## Nível de feature: previsões ingênuas\n')
say(md(fs[fs.id == 'BASELINE'][['medida', 'spearman_medio', 'spearman_IC95_inf', 'spearman_IC95_sup', 'acerto_top3_medio']]))
m = fs[fs.id != 'BASELINE']
for med in m.medida.unique():
    x = m[m.medida == med]
    say(f'\n{med}: {len(x)} configurações; melhor Spearman {x.spearman_medio.max():.3f}; mediana {x.spearman_medio.median():.3f};'
        f' superam a persistência (dif > 0): {(x.dif_vs_persistencia > 0).sum()}; IC da diferença > 0: '
        f'{(x.dif_IC95_inf > 0).sum()}; IC < 0 (pior): {(x.dif_IC95_sup < 0).sum()}')
mm = m[m.medida == 'taxa (score_medio)']
bpa = mm.sort_values('spearman_medio', ascending=False).groupby('algoritmo').head(1).sort_values('spearman_medio', ascending=False)
say('\n## Melhor por algoritmo (taxa, probabilidade média)\n')
say(md(bpa[['algoritmo', 'conjunto', 'reamostragem', 'spearman_medio', 'spearman_IC95_inf', 'spearman_IC95_sup',
            'acerto_top3_medio', 'dif_vs_persistencia', 'dif_IC95_inf', 'dif_IC95_sup']]))
cj = mm.groupby('conjunto').spearman_medio.agg(['mean', 'max'])
say('\nSpearman (taxa) por conjunto de métricas:', cj.round(3).to_dict())
# melhor modelo por PR-AUC no método: como se sai no nível de feature?
bm = mm[mm.id == best_t.id].iloc[0]
say(f'\nMelhor modelo no nível de método ({best_t.id}) no nível de feature: Spearman {bm.spearman_medio:.3f} '
    f'[{bm.spearman_IC95_inf:.3f}, {bm.spearman_IC95_sup:.3f}], top3 {bm.acerto_top3_medio:.3f}')

# série por release: melhor configuração (taxa) x persistência
from scipy.stats import spearmanr
bf_id = mm.sort_values('spearman_medio', ascending=False).iloc[0].id
rows = []
for rel, g in fd[fd.id == bf_id].groupby('release'):
    g = g.dropna(subset=['taxa_real'])
    rho_m = spearmanr(g.score_medio, g.taxa_real).statistic
    gp = g.dropna(subset=['persist_taxa'])
    rho_p = spearmanr(gp.persist_taxa, gp.taxa_real).statistic
    g2 = fd[(fd.id == best_t.id) & (fd.release == rel)].dropna(subset=['taxa_real'])
    rho_b = spearmanr(g2.score_medio, g2.taxa_real).statistic
    rows.append({'release': rel, 'modelo': rho_m, 'persistencia': rho_p, 'melhor_metodo': rho_b, 'features': len(g)})
sr = pd.DataFrame(rows)
sr.to_csv(DAT / 'spearman_por_release.dat', sep=' ', index=False, float_format='%.4f', na_rep='nan')
say(f'\n## Spearman por release ({bf_id} x persistência x {best_t.id})\n')
say(md(sr))
say(f'Releases em que o modelo supera a persistência: {(sr.modelo > sr.persistencia).sum()} de {len(sr)}')

# ranking médio das features (melhor configuração no nível de feature e persistência)
rk = pd.read_csv(RES / 'nivel_feature_ranking.csv')
say('\n## Ranking (melhor configuração no nível de feature)\n')
say(md(rk[['feature', 'posicao_real', 'posicao_prevista', 'taxa_real_media', 'score_medio', 'mudancas_reais', 'releases']], '.5f'))
say(f"Spearman entre as posições médias real e prevista: {spearmanr(rk.posicao_real, rk.posicao_prevista).statistic:.3f}")
pers = fd[fd.id == bf_id].groupby('feature').agg(taxa=('taxa_real', 'mean'), pers=('persist_taxa', 'mean'))
say(f"Spearman entre taxa média real e persistência média: {spearmanr(pers.taxa, pers.pers).statistic:.3f}")

# ---- F. importância ----
imp = pd.read_csv(RES / 'importancias.csv')
for alg, conj, rs in (('LightGBM', 'model2', 'ROS'), ('RandomForest', 'model2', 'SMOTE'), ('XGBoost', 'model2', 'ROS')):
    x = imp[(imp.protocolo == 'temporal') & (imp.algoritmo == alg) & (imp.conjunto == conj) & (imp.reamostragem == rs)]
    x = x.assign(v=x.valor.abs() / x.valor.abs().sum()).sort_values('v', ascending=False)
    evo_share = x[x.coluna.isin(EVO)].v.sum()
    say(f'\n## Importância {alg} {conj} {rs} (temporal): participação das evolutivas = {100 * evo_share:.1f}%\n')
    say(md(x.head(10)[['coluna', 'v']], '.3f'))
    if alg == 'LightGBM':
        x.head(10)[['coluna', 'v']].assign(v=lambda d: 100 * d.v).to_csv(DAT / 'importancia_lgbm.dat', sep=' ', index=False,
                                                                         float_format='%.2f')

# ---- G. taxa de positivos por release (conjunto completo) ----
rows = []
for p in sorted((ROOT / '5-Coleta_features').glob('*/data/*-all-releases.parquet')):
    if 'validacao' in str(p):
        continue
    d = pq.read_table(p, columns=['release', 'will_change']).to_pandas()
    rows.append(d.groupby('release').will_change.agg(['size', 'sum']))
pr = pd.concat(rows).groupby(level=0).sum()
pr['taxa'] = 100 * pr['sum'] / pr['size']
pr = pr.reset_index().rename(columns={'size': 'linhas', 'sum': 'positivos'})
pr.to_csv(DAT / 'positivos_por_release.dat', sep=' ', index=False, float_format='%.4f')
say(f'\nTaxa de positivos por release: min {pr.taxa.min():.3f}% (r={int(pr.loc[pr.taxa.idxmin(), "release"])}), '
    f'max {pr.taxa.max():.3f}% (r={int(pr.loc[pr.taxa.idxmax(), "release"])}); média treino (r<=36) '
    f'{100 * pr[pr.release <= 36].positivos.sum() / pr[pr.release <= 36].linhas.sum():.3f}%, teste '
    f'{100 * pr[pr.release > 36].positivos.sum() / pr[pr.release > 36].linhas.sum():.3f}%')

(OUT / 'RESUMO_ANALISE.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
