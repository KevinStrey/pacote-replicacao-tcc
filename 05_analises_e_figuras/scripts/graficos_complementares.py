"""Complementary material for the replication package: every configuration, per release, with summaries and plots.

The thesis shows only the best configuration of each algorithm (and the factor groups). This script writes, for ALL
configurations, the per-release values used by the tests, their median/mean/SD, and one box plot per algorithm, so a
reader can check every comparison and tie (e.g. the four linear-SVM configurations with metric set model3 have the
same median Spearman). It also copies the thesis tables (.tex) and figures (.pdf) and the statistical-test outputs.

Output: 8-Material_complementar/ (copied by 7-Pacote_replicacao/montar_pacote.py to
05_analises_e_figuras/material_complementar/).
Usage: python graficos_complementares.py
"""
import shutil
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / 'resultados_e_logs' / 'saida' / 'resultados'
KW = RES / 'kruskal'
TCC = ROOT / 'TCC___Kevin___UDESC'
OUT = ROOT / '8-Material_complementar'
ALG = {'LightGBM': 'LightGBM', 'MLP': 'MLP', 'LogisticRegression': 'Regr. log.', 'XGBoost': 'XGBoost',
       'LinearSVC': 'SVM linear', 'RandomForest': 'RF', 'DT': 'DT'}
CONJ = ['model1', 'model2', 'model3']
REAM = ['NONE', 'ROS', 'SMOTE', 'ADA']
COR = {'model1': '#0072B2', 'model2': '#009E73', 'model3': '#E69F00'}
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.alpha': 0.3,
                     'grid.linestyle': '--', 'savefig.bbox': 'tight', 'savefig.dpi': 200})


def br(x, nd):
    v = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    return f'{v:.{nd}f}'.replace('.', ',')


def resumo(df, chave, col):
    g = df.groupby(chave)[col]
    r = g.agg(n='size', mediana='median', media='mean', dp='std', minimo='min', maximo='max').reset_index()
    return r.sort_values(['mediana', 'media'], ascending=False)


def box_por_algoritmo(df, col, titulo, nome, ylabel, ref=None):
    """One panel per algorithm, one box per configuration (metric set x resampling), one point per release."""
    algs = [a for a in ALG if a in set(df.algoritmo)]
    fig, axes = plt.subplots(len(algs), 1, figsize=(10, 2.3 * len(algs)), sharex=False)
    for ax, alg in zip(np.atleast_1d(axes), algs):
        d = df[df.algoritmo == alg]
        labels, data, cores = [], [], []
        for c in CONJ:
            for r in REAM:
                v = d[(d.conjunto == c) & (d.reamostragem == r)][col].to_numpy()
                if len(v):
                    labels.append(f'{c}\n{r}')
                    data.append(v)
                    cores.append(COR[c])
        bp = ax.boxplot(data, widths=0.6, patch_artist=True, showfliers=False, medianprops=dict(color='black', lw=1.4))
        rng = np.random.default_rng(0)
        for i, (patch, v, c) in enumerate(zip(bp['boxes'], data, cores), 1):
            patch.set(facecolor=c, alpha=0.35, edgecolor=c)
            ax.scatter(i + rng.uniform(-0.15, 0.15, len(v)), v, s=8, color=c, alpha=0.8, zorder=3, linewidths=0)
            ax.text(i, ax.get_ylim()[1] if False else np.max(v), br(np.median(v), 3), ha='center', va='bottom',
                    fontsize=7)
        ax.set_xticks(range(1, len(labels) + 1), labels, fontsize=7)
        ax.set_title(ALG[alg], fontsize=10, loc='left')
        ax.set_ylabel(ylabel, fontsize=8)
        if ref is not None:
            ax.axhline(ref, color='black', ls=':', lw=1)
    fig.suptitle(titulo, fontsize=11)
    fig.tight_layout()
    fig.savefig(nome.with_suffix('.png'))
    fig.savefig(nome.with_suffix('.pdf'))
    plt.close(fig)


shutil.rmtree(OUT, ignore_errors=True)
for d in ('01_tabelas_e_figuras_do_tcc/tabelas', '01_tabelas_e_figuras_do_tcc/figuras', '02_testes_estatisticos',
          '03_configuracoes_nivel_metodo', '04_configuracoes_nivel_feature'):
    (OUT / d).mkdir(parents=True)

# ---------------------------------------------------------------- 01 thesis tables and figures
for p in sorted((TCC / 'Elementos' / 'Tabelas').glob('tab-*.tex')):
    shutil.copy2(p, OUT / '01_tabelas_e_figuras_do_tcc' / 'tabelas' / p.name)
for p in sorted((TCC / 'Elementos' / 'Diagramas').glob('fig-0[34]-*.tex')):
    shutil.copy2(p, OUT / '01_tabelas_e_figuras_do_tcc' / 'figuras' / p.name)
for sub in ('curvas', 'testes'):
    for p in sorted((TCC / 'Textuais' / 'imagens' / sub).glob('*.pdf')):
        shutil.copy2(p, OUT / '01_tabelas_e_figuras_do_tcc' / 'figuras' / p.name)
for n in ('distribuicao_dataset.pdf', 'e13_presenca_das_features.pdf'):
    shutil.copy2(TCC / 'Textuais' / 'imagens' / n, OUT / '01_tabelas_e_figuras_do_tcc' / 'figuras' / n)

# ---------------------------------------------------------------- 02 statistical tests (every pair, not only vs reference)
for p in sorted(KW.glob('*.csv')):
    shutil.copy2(p, OUT / '02_testes_estatisticos' / p.name)

# ---------------------------------------------------------------- 03 method level: every configuration per release
m = pd.read_csv(RES / 'metricas_por_release.csv', keep_default_na=False, na_values=[''])
m = m[(m.feature == 'TODAS') & (m.variante == 'principal') & (m.algoritmo.isin(ALG))]
m = m[m.restrito.isna() | (m.restrito == '')] if 'restrito' in m else m
m = m[['protocolo', 'algoritmo', 'conjunto', 'reamostragem', 'release', 'linhas', 'positivos', 'pr_auc', 'roc_auc']]
d3 = OUT / '03_configuracoes_nivel_metodo'
m.sort_values(['protocolo', 'algoritmo', 'conjunto', 'reamostragem', 'release']).to_csv(
    d3 / 'valores_por_release.csv', index=False)
for proto, nome in (('temporal', 'temporal'), ('random', 'aleatorio')):
    mp = m[m.protocolo == proto]
    for met, lab in (('pr_auc', 'PR-AUC'), ('roc_auc', 'ROC-AUC')):
        resumo(mp, ['algoritmo', 'conjunto', 'reamostragem'], met).round(4).to_csv(
            d3 / f'resumo_{nome}_{met}.csv', index=False)
        box_por_algoritmo(mp, met, f'{lab} por release de cada configuração, protocolo {nome}',
                          d3 / f'box_{nome}_{met}', lab, 0.5 if met == 'roc_auc' else None)

# ---------------------------------------------------------------- 04 feature level: every configuration per release
fr = pd.read_csv(RES / 'nivel_feature_por_release.csv')
summ = pd.read_csv(RES / 'nivel_feature_resumo.csv')
cfg = summ[(summ.id != 'BASELINE') & (summ.medida == 'taxa (score_medio)')]
rows = []
for c in cfg.itertuples():
    d = fr[fr.id == c.id].dropna(subset=['score_medio', 'taxa_real'])
    for rel, g in d.groupby('release'):
        if g.score_medio.nunique() > 1 and g.taxa_real.nunique() > 1:
            a = set(g.sort_values('score_medio', ascending=False).feature.head(3))
            b = set(g.sort_values('taxa_real', ascending=False).feature.head(3))
            rows.append(dict(algoritmo=c.algoritmo, conjunto=c.conjunto, reamostragem=c.reamostragem, release=rel,
                             features=len(g), spearman=g.score_medio.rank().corr(g.taxa_real.rank()), top3=len(a & b)))
sp = pd.DataFrame(rows)
d4 = OUT / '04_configuracoes_nivel_feature'
sp.sort_values(['algoritmo', 'conjunto', 'reamostragem', 'release']).to_csv(d4 / 'valores_por_release.csv', index=False)
r = resumo(sp, ['algoritmo', 'conjunto', 'reamostragem'], 'spearman')
t3 = sp.groupby(['algoritmo', 'conjunto', 'reamostragem']).top3.agg(top3_mediana='median', top3_media='mean').reset_index()
r.merge(t3, on=['algoritmo', 'conjunto', 'reamostragem']).round(4).to_csv(d4 / 'resumo_spearman.csv', index=False)
box_por_algoritmo(sp, 'spearman', 'Correlação de Spearman por release de cada configuração (nível de feature)',
                  d4 / 'box_spearman', 'Spearman', 0)
# the tie discussed in the thesis: the four linear-SVM configurations with model3
svm = sp[(sp.algoritmo == 'LinearSVC') & (sp.conjunto == 'model3')]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw=dict(width_ratios=[2.2, 1]))
for rs, mk in zip(REAM, 'osD^'):
    v = svm[svm.reamostragem == rs].sort_values('release')
    a1.plot(v.release, v.spearman, marker=mk, ms=4, lw=1, label=f'{rs} (mediana {br(v.spearman.median(), 3)}; '
                                                              f'média {br(v.spearman.mean(), 3)})')
a1.set(xlabel='Release de teste', ylabel='Spearman', title='SVM linear com model3: Spearman em cada release')
a1.legend(fontsize=7, loc='lower right')
a2.boxplot([svm[svm.reamostragem == rs].spearman for rs in REAM], showfliers=False,
           medianprops=dict(color='black', lw=1.4))
a2.set_xticks(range(1, 5), REAM)
a2.set(title='Distribuição (mesma mediana)')
fig.tight_layout()
fig.savefig(d4 / 'svm_model3_balanceamento.png')
fig.savefig(d4 / 'svm_model3_balanceamento.pdf')
plt.close(fig)
print('ok', OUT)
