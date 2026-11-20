"""LaTeX tables of the Kruskal-Wallis analyses (reads resultados/kruskal/*.csv from testes_kruskal.py).

Writes to TCC___Kevin___UDESC/Elementos/Tabelas/ (without review colours: sem_cores.clean):
 tab-04-res-kw.tex             every Kruskal-Wallis test (H, p)
 tab-04-res-a12-acaso.tex           QP1: each algorithm x random classifier
 tab-04-res-a12-melhor.tex          QP2: each algorithm x best algorithm of the protocol
 tab-04-res-a12-fatores.tex         QP2: algorithm, metric set and resampling (84 temporal configurations)
 tab-04-res-nivel-feature.tex       QP3: predictors x persistence and x random order
 tab-04-res-a12-melhor-feature.tex  QP4: best configuration of each algorithm x best one, feature level
 tab-04-res-a12-fatores-feature.tex QP4: algorithm, metric set and resampling at the feature level
 tab-04-res-feature-interacao.tex   QP4: mean Spearman of each algorithm x metric set
 tab-04-res-sens-teste.tex          identity breaks: main model x variant, per release
(Research questions as numbered in the thesis after the 2026-11-11 revision.)
Usage: python tabelas_kruskal.py
"""
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
import re

import numpy as np
import sem_cores
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / 'resultados_e_logs' / 'saida' / 'resultados'
KW = RES / 'kruskal'
TAB = ROOT / 'TCC___Kevin___UDESC' / 'Elementos' / 'Tabelas'

kw = pd.read_csv(KW / 'kw.csv')
pares = pd.read_csv(KW / 'pares.csv')
pares['magnitude'] = pares.magnitude.replace('desprezível', 'insignificante')  # term used in the TCC
grupos = pd.read_csv(KW / 'grupos.csv')
tests = pd.read_csv(RES / 'resultados_teste.csv')
ND = {'pr_auc': 4, 'roc_auc': 3, 'spearman': 3}
MET = {'pr_auc': 'PR-AUC', 'roc_auc': 'ROC-AUC', 'spearman': 'Spearman'}


def br(x, nd):
    v = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    s = f'{abs(v):.{nd}f}'.replace('.', ',')
    return ('$-$' if v < 0 else '') + s


def pval(p):
    return '$<$ 0,001' if p < 0.001 else br(p, 3)


def ms(analise, metrica, grupo):
    g = grupos[(grupos.analise == analise) & (grupos.metrica == metrica) & (grupos.grupo == grupo)].iloc[0]
    return f'{br(g.media, ND[metrica])} $\\pm$ {br(g.dp, ND[metrica])}', int(g.n)


def md(analise, metrica, grupo):
    """Median per release (method-level tables, advisor review 2026-11-19); the tests are rank-based."""
    g = grupos[(grupos.analise == analise) & (grupos.metrica == metrica) & (grupos.grupo == grupo)].iloc[0]
    return br(g.mediana, ND[metrica]), int(g.n)


def pair(analise, metrica, x, y):
    """A12 of x over y (probability that x is larger), magnitude and Bonferroni p, whatever the stored order."""
    d = pares[(pares.analise == analise) & (pares.metrica == metrica)]
    r = d[(d.a == x) & (d.b == y)]
    if len(r):
        r = r.iloc[0]
        return r.A12, r.magnitude, r.p_bonferroni
    r = d[(d.a == y) & (d.b == x)].iloc[0]
    return 1 - r.A12, r.magnitude, r.p_bonferroni


def classe(a):
    d = round(abs(a - 0.5), 9)
    return 'insignificante' if d < 0.06 else 'pequeno' if d < 0.14 else 'médio' if d < 0.21 else 'grande'


def a12txt(a, mag):
    """Two decimals, or three when rounding to two would move the value to another class of the threshold table."""
    return br(a, 2) if classe(round(a, 2)) == mag else br(a, 3)


def cells(analise, metrica, x, y):
    a, mag, p = pair(analise, metrica, x, y)
    if p >= 0.05:      # no significant difference: the effect size is not reported (advisor review, 2026-11-19)
        return f'{{\\rosa ---}} & {{\\rosa ---}} & {pval(p)}'
    return f'{a12txt(a, mag)} & {mag} & {pval(p)}'


def table(name, caption, label, colspec, header, body, size='\\footnotesize', sep='4pt'):
    caption, header, body = (re.sub(r'(?<![\w\\_/.=-])([Rr]eleases?)(?![\w_/.-])', r'\\textit{\1}', x)
                             for x in (caption, header, body))   # 'release' always in italics in the TCC
    tex = ('% Gerado por 6-Treino/ferramentas_locais/tabelas_kruskal.py (não editar à mão)\n'
           '\\begin{table}[htbp]\n    \\laranja\n    \\captionsetup{font+={color=orange}}%\n    \\centering\n'
           f'    {size}\n    \\setlength{{\\tabcolsep}}{{{sep}}}%\n'
           f'    \\caption{{{caption}}}\n    \\label{{{label}}}\n'
           f'    \\begin{{tabular}}{{{colspec}}}\n        \\toprule\n' + header + '        \\midrule\n' + body +
           '        \\bottomrule\n    \\end{tabular}\n    \\fonte{Elaborado pelo autor (2026)}\n\\end{table}%\n')
    (TAB / name).write_text(sem_cores.clean(tex), encoding='utf-8')   # review colours removed (2026-11-20)
    print('ok', name)


# ---------------------------------------------------------------- every Kruskal-Wallis test
DESC = [('metodo_acaso__temporal', 'QP1', 'Algoritmos e classificador aleatório, protocolo temporal'),
        ('metodo_acaso__random', 'QP1', 'Algoritmos e classificador aleatório, protocolo aleatório'),
        ('fator_algoritmo__temporal', 'QP2', 'Algoritmos (84 configurações)'),
        ('fator_conjunto__temporal', 'QP2', 'Conjuntos de métricas (84 configurações)'),
        ('fator_reamostragem__temporal', 'QP2', 'Estratégias de balanceamento (84 configurações)'),
        ('feature_ordem', 'QP3', 'Modelos, previsões ingênuas e ordenação aleatória'),
        ('fator_algoritmo__feature', 'QP4', 'Algoritmos, nível de \\textit{feature} (84 configurações)'),
        ('fator_conjunto__feature', 'QP4', 'Conjuntos de métricas, nível de \\textit{feature} (84 configurações)'),
        ('fator_reamostragem__feature', 'QP4', 'Estratégias de balanceamento, nível de \\textit{feature} (84 configurações)'),
        ('identidade__temporal', 'QP5', 'Com e sem PTP, Scout e Mylyn, protocolo temporal'),
        ('identidade__random', 'QP5', 'Com e sem PTP, Scout e Mylyn, protocolo aleatório')]
body = ''
for an, qp, desc in DESC:
    rows = kw[kw.analise == an]
    for i, r in enumerate(rows.itertuples()):
        first = (f'{qp} & \\multirow{{{len(rows)}}}{{=}}{{{desc}}}' if len(rows) > 1 else f'{qp} & {desc}') if i == 0 else ' &'
        body += (f'        {first} & {MET[r.metrica]} & {br(r.H, 2)} & {pval(r.p)} & '
                 f'{"Rejeita" if r.rejeita else "Não rejeita"} \\\\\n')
    body += '        \\midrule\n' if an != DESC[-1][0] else ''
table('tab-04-res-kw.tex', 'Resultados dos testes de Kruskal-Wallis', 'tab:res-kw',   # k and N: tab-04-res-kw-kn
      'lp{6.6cm}lrrl',
      '        Pergunta & Grupos comparados & Indicador & $H$ & $p$ & $H_0$ \\\\\n', body)

# ---------------------------------------------------------------- QP1: algorithms x random classifier
body = ''
for proto, nome in (('temporal', 'Temporal'), ('random', 'Aleatório')):
    an = f'metodo_acaso__{proto}'
    order = grupos[(grupos.analise == an) & (grupos.metrica == 'pr_auc') & (grupos.grupo != 'Aleatório')] \
        .sort_values('mediana', ascending=False).grupo.tolist()
    for i, alg in enumerate(order):
        body += (f'        {nome if i == 0 else ""} & {alg} & {md(an, "pr_auc", alg)[0]} & {cells(an, "pr_auc", alg, "Aleatório")} & '
                 f'{md(an, "roc_auc", alg)[0]} & {cells(an, "roc_auc", alg, "Aleatório")} \\\\\n')
    body += (f'         & Aleatório & {md(an, "pr_auc", "Aleatório")[0]} & --- & --- & --- & '
             f'{md(an, "roc_auc", "Aleatório")[0]} & --- & --- & --- \\\\\n')
    body += '        \\midrule\n' if proto == 'temporal' else ''
hdr = ('         & & \\multicolumn{4}{c|}{PR-AUC} & \\multicolumn{4}{c}{ROC-AUC} \\\\\n'
       '        \\cmidrule(lr){3-6}\\cmidrule(lr){7-10}\n'
       '        Protocolo & Algoritmo & {\\rosa Mediana} & $\\hat{A}_{12}$ & Efeito & $p$ & {\\rosa Mediana} & $\\hat{A}_{12}$ & Efeito & $p$ \\\\\n')
table('tab-04-res-a12-acaso.tex',
      'Melhor configuração de cada algoritmo comparada com o classificador aleatório', 'tab:res-a12-acaso',
      'llcclc|cclc', hdr, body, size='\\scriptsize', sep='3pt')   # vertical rule between PR-AUC and ROC-AUC

# ---------------------------------------------------------------- QP2: algorithms x best of the protocol
body = ''
for proto, nome in (('temporal', 'Temporal'), ('random', 'Aleatório')):
    an = f'metodo_acaso__{proto}'
    g = grupos[(grupos.analise == an) & (grupos.grupo != 'Aleatório')]
    order = g[g.metrica == 'pr_auc'].sort_values('mediana', ascending=False).grupo.tolist()
    best = {m: g[g.metrica == m].sort_values('mediana', ascending=False).grupo.iloc[0] for m in ('pr_auc', 'roc_auc')}
    nomes = {'LogisticRegression': 'Regr. log.', 'LinearSVC': 'SVM linear', 'RandomForest': 'RF'}
    conf = {nomes.get(r.algoritmo, r.algoritmo): (r.conjunto, r.reamostragem)
            for r in pd.read_csv(KW / f'melhores__{proto}.csv').itertuples()}
    for i, alg in enumerate(order):
        c = [cells(an, m, best[m], alg) if alg != best[m] else '\\multicolumn{3}{c}{(referência)}'
             for m in ('pr_auc', 'roc_auc')]
        cj, rs = conf[alg]   # the configuration that represents the algorithm (metric set and resampling)
        body += f'        {nome if i == 0 else ""} & {alg} & {{\\rosa {cj}}} & {{\\rosa {rs}}} & {c[0]} & {c[1]} \\\\\n'
    body += '        \\midrule\n' if proto == 'temporal' else ''
hdr = ('         & & & & \\multicolumn{3}{c}{PR-AUC} & \\multicolumn{3}{c}{ROC-AUC} \\\\\n'
       '        \\cmidrule(lr){5-7}\\cmidrule(lr){8-10}\n'
       '        Protocolo & Algoritmo & {\\rosa Métricas} & {\\rosa Reamostr.} & $\\hat{A}_{12}$ & Efeito & $p$ & $\\hat{A}_{12}$ & Efeito & $p$ \\\\\n')
table('tab-04-res-a12-melhor.tex',
      'Configuração de maior mediana em cada protocolo comparada com as demais', 'tab:res-a12-melhor',
      'llllclcclc', hdr, body, size='\\scriptsize', sep='3pt')

# ---------------------------------------------------------------- QP2: factors
NOMES = {'model1': 'Estruturais (model1)', 'model2': 'Estruturais e evolutivas (model2)', 'model3': 'Evolutivas (model3)',
         'NONE': 'Sem reamostragem (NONE)', 'ROS': 'Sobreamostragem aleatória (ROS)', 'SMOTE': 'SMOTE', 'ADA': 'ADASYN (ADA)'}
# one table per factor (algorithm, metric set, resampling), each placed with its own text and box plot
for fator, tit, cap in (('algoritmo', 'Algoritmo', 'Algoritmos'),
                        ('conjunto', 'Conjunto de métricas', 'Conjuntos de métricas'),
                        ('reamostragem', 'Balanceamento', 'Estratégias de balanceamento')):
    an = f'fator_{fator}__temporal'
    g = grupos[grupos.analise == an]
    order = g[g.metrica == 'pr_auc'].sort_values('mediana', ascending=False).grupo.tolist()
    best = {m: g[g.metrica == m].sort_values('mediana', ascending=False).grupo.iloc[0] for m in ('pr_auc', 'roc_auc')}
    body = ''
    for alg in order:
        c = [cells(an, m, best[m], alg) if alg != best[m] else '\\multicolumn{3}{c}{(referência)}'
             for m in ('pr_auc', 'roc_auc')]
        body += (f'        {NOMES.get(alg, alg)} & {md(an, "pr_auc", alg)[0]} & {c[0]} & '
                 f'{md(an, "roc_auc", alg)[0]} & {c[1]} \\\\\n')
    hdr = ('         & \\multicolumn{4}{c|}{PR-AUC} & \\multicolumn{4}{c}{ROC-AUC} \\\\\n'
           '        \\cmidrule(lr){2-5}\\cmidrule(lr){6-9}\n'
           f'        {tit} & {{\\rosa Mediana}} & $\\hat{{A}}_{{12}}$ & Efeito & $p$ & {{\\rosa Mediana}} & $\\hat{{A}}_{{12}}$ & '
           'Efeito & $p$ \\\\\n')
    n = md(an, 'pr_auc', order[0])[1]
    table(f'tab-04-res-a12-fatores-{fator}.tex',
          f'{cap} no protocolo temporal ({n} valores por grupo): cada grupo comparado com o de maior mediana',
          f'tab:res-a12-fatores-{fator}', 'lcclc|cclc', hdr, body, size='\\scriptsize', sep='3pt')

# ---------------------------------------------------------------- QP3: order of the features
# Feature level standardised on the MEDIAN per release (advisor review, 2026-11-19): Spearman columns show the median,
# the reference of each comparison is the group of highest median, and the Top 3 shows the median with the mean in
# parentheses (tie-breaker).
summ = pd.read_csv(RES / 'nivel_feature_resumo.csv')
topf = pd.read_csv(KW / 'melhores__feature.csv')          # best configuration per algorithm, by median (testes_kruskal)
frl = pd.read_csv(RES / 'nivel_feature_por_release.csv')
ALG = {'LightGBM': 'LightGBM', 'MLP': 'MLP', 'LogisticRegression': 'Regr. log.', 'XGBoost': 'XGBoost',
       'LinearSVC': 'SVM linear', 'RandomForest': 'RF', 'DT': 'DT'}
an = 'feature_ordem'


def top3_release(df, pcol, rcol='taxa_real'):
    """Hits in the top 3 (0 to 3) in each test release."""
    out = []
    for _, g in df.dropna(subset=[pcol, rcol]).groupby('release'):
        a = set(g.sort_values(pcol, ascending=False).feature.head(3))
        b = set(g.sort_values(rcol, ascending=False).feature.head(3))
        out.append(len(a & b))
    return out


def top3txt(v, mean_check):
    assert abs(np.mean(v) - mean_check) < 1e-9
    return f'{br(np.median(v), 0)} ({br(np.mean(v), 2)})'


fb = frl[frl.id == topf.iloc[0].id]
# two tables (advisor review, 2026-11-19): first every predictor against the random order, then against persistence
naive = (('Persistência', 'persist_taxa', 'taxa (persistencia)'), ('Média histórica', 'hist_taxa', 'taxa (media_historica)'))
t3 = {nome: top3txt(top3_release(fb, col), summ[summ.medida == med].acerto_top3_medio.iloc[0] * 3) for nome, col, med in naive}
for r in topf.itertuples():
    t3[ALG[r.algoritmo]] = top3txt(top3_release(frl[frl.id == r.id], 'score_medio'),
                                   summ[(summ.id == r.id) & (summ.medida == 'taxa (score_medio)')].acerto_top3_medio.iloc[0] * 3)
conf = {ALG[r.algoritmo]: f'{r.conjunto}, {r.reamostragem}' for r in topf.itertuples()}
modelos = [ALG[a] for a in topf.algoritmo]
# --- (a) against the random order
body = ''
for nome in modelos:
    body += f'        {nome} & {conf[nome]} & {md(an, "spearman", nome)[0]} & {t3[nome]} & {cells(an, "spearman", nome, "Aleatório")} \\\\\n'
body += '        \\midrule\n'
for nome in ('Persistência', 'Média histórica'):
    body += f'        {nome} & --- & {md(an, "spearman", nome)[0]} & {t3[nome]} & {cells(an, "spearman", nome, "Aleatório")} \\\\\n'
body += f'        Ordenação aleatória & --- & {md(an, "spearman", "Aleatório")[0]} & --- & \\multicolumn{{3}}{{c}}{{(referência)}} \\\\\n'
hdr = ('         & & & & \\multicolumn{3}{c}{Comparação com a ordenação aleatória} \\\\\n'
       '        \\cmidrule(lr){5-7}\n'
       '        Preditor & Configuração & Spearman & Top 3 & $\\hat{A}_{12}$ & Efeito & $p$ \\\\\n')
table('tab-04-res-nivel-feature.tex',
      'Ordenação das \\textit{features} por taxa de mudança: modelos e previsões ingênuas comparados com o acaso',
      'tab:res-nivel-feature', 'llcccl c'.replace(' ', ''), hdr, body)
# --- (b) against persistence
body = '        Persistência & --- & ' + md(an, "spearman", "Persistência")[0] + ' & \\multicolumn{3}{c}{(referência)} \\\\\n        \\midrule\n'
for nome in modelos:
    body += f'        {nome} & {conf[nome]} & {md(an, "spearman", nome)[0]} & {cells(an, "spearman", nome, "Persistência")} \\\\\n'
body += '        \\midrule\n'
body += f'        Média histórica & --- & {md(an, "spearman", "Média histórica")[0]} & {cells(an, "spearman", "Média histórica", "Persistência")} \\\\\n'
body += f'        Ordenação aleatória & --- & {md(an, "spearman", "Aleatório")[0]} & {cells(an, "spearman", "Aleatório", "Persistência")} \\\\\n'
hdr = ('         & & & \\multicolumn{3}{c}{Comparação com a persistência} \\\\\n'
       '        \\cmidrule(lr){4-6}\n'
       '        Preditor & Configuração & Spearman & $\\hat{A}_{12}$ & Efeito & $p$ \\\\\n')
table('tab-04-res-nivel-feature-persistencia.tex',
      'Ordenação das \\textit{features} por taxa de mudança: modelos e previsões ingênuas comparados com a persistência',
      'tab:res-nivel-feature-persistencia', 'llcclc', hdr, body)

# ---------------------------------------------------------------- QP4: best configuration of each algorithm, feature level
body = ''
algs = [ALG[a] for a in topf.algoritmo]                  # already in decreasing order of median Spearman
ref = algs[0]
for r in topf.itertuples():
    nome = ALG[r.algoritmo]
    c = '\\multicolumn{3}{c}{(referência)}' if nome == ref else cells(an, 'spearman', ref, nome)
    body += f'        {nome} & {r.conjunto}, {r.reamostragem} & {md(an, "spearman", nome)[0]} & {c} \\\\\n'
hdr = ('        Algoritmo & Configuração & {\\rosa Spearman (mediana)} & $\\hat{A}_{12}$ & Efeito & $p$ \\\\\n')
table('tab-04-res-a12-melhor-feature.tex',
      'Melhor configuração de cada algoritmo na ordenação das \\textit{features} comparada com a de maior {\\rosa mediana}',
      'tab:res-a12-melhor-feature', 'llcclc', hdr, body)

# ---------------------------------------------------------------- QP4: factors at the feature level
body = ''
for fator, tit in (('algoritmo', 'Algoritmo'), ('conjunto', 'Conjunto de métricas'), ('reamostragem', 'Balanceamento')):
    an4 = f'fator_{fator}__feature'
    g = grupos[grupos.analise == an4]
    order = g.sort_values('mediana', ascending=False).grupo.tolist()
    body += f'        \\multicolumn{{6}}{{l}}{{\\textit{{{tit}}} ({md(an4, "spearman", order[0])[1]} valores por grupo)}} \\\\\n'
    for x in order:
        c = '\\multicolumn{3}{c}{(referência)}' if x == order[0] else cells(an4, 'spearman', order[0], x)
        dp = grupos[(grupos.analise == an4) & (grupos.grupo == x)].dp.iloc[0]   # dispersion cited in the text
        body += f'        \\quad {NOMES.get(x, x)} & {md(an4, "spearman", x)[0]} & {{\\rosa {br(dp, 3)}}} & {c} \\\\\n'
    body += '        \\midrule\n' if fator != 'reamostragem' else ''
hdr = ('        Grupo & {\\rosa Spearman (mediana)} & {\\rosa Desvio padrão} & $\\hat{A}_{12}$ & Efeito & $p$ \\\\\n')
table('tab-04-res-a12-fatores-feature.tex',
      'Algoritmos, conjuntos de métricas e estratégias de balanceamento na ordenação das \\textit{features}: cada '
      'grupo comparado com o de maior {\\rosa mediana}', 'tab:res-a12-fatores-feature', 'lccclc', hdr, body)

# ---------------------------------------------------------------- QP4: algorithm x metric set (median per release)
rows = []
cf = summ[(summ.id != 'BASELINE') & (summ.medida == 'taxa (score_medio)')]
for r in cf.itertuples():
    d = frl[frl.id == r.id].dropna(subset=['score_medio', 'taxa_real'])
    for _, gr in d.groupby('release'):
        if gr.score_medio.nunique() > 1 and gr.taxa_real.nunique() > 1:
            rows.append((r.algoritmo, r.conjunto, gr.score_medio.rank().corr(gr.taxa_real.rank())))
sp = pd.DataFrame(rows, columns=['algoritmo', 'conjunto', 'rho'])
pv = sp.pivot_table(index='algoritmo', columns='conjunto', values='rho', aggfunc='median')
pv = pv.loc[[a for a in topf.algoritmo]]
body = ''
for alg, r in pv.iterrows():
    body += f'        {ALG[alg]} & {br(r.model1, 3)} & {br(r.model2, 3)} & {br(r.model3, 3)} \\\\\n'
hdr = '        Algoritmo & Estruturais (model1) & Estruturais e evolutivas (model2) & Evolutivas (model3) \\\\\n'
table('tab-04-res-feature-interacao.tex',
      'Correlação de Spearman {\\rosa mediana} de cada algoritmo com cada conjunto de métricas na ordenação das '
      '\\textit{features} {\\rosa (mediana dos valores por \\textit{release} das quatro estratégias de balanceamento)}',
      'tab:res-feature-interacao', 'l' + '>{\\centering\\arraybackslash}p{2.9cm}' * 3, hdr, body)

# ---------------------------------------------------------------- identity breaks
best = {'temporal': 'fase1__temporal__principal__model2__ROS__LightGBM__teste',
        'random': 'fase1__random__principal__model2__ROS__XGBoost__teste'}
sens = pd.read_csv(RES / 'sensibilidade.csv') if (RES / 'sensibilidade.csv').exists() else None
P, Vn = 'Principal (restrito)', 'Sem PTP, Scout e Mylyn'
body = ''
for proto, nome in (('temporal', 'Temporal'), ('random', 'Aleatório')):
    an = f'identidade__{proto}'
    for i, m in enumerate(('pr_auc', 'roc_auc')):
        body += (f'        {nome if i == 0 else ""} & {MET[m]} & {md(an, m, P)[0]} & {md(an, m, Vn)[0]} & '
                 f'{cells(an, m, Vn, P)} \\\\\n')
    body += '        \\midrule\n' if proto == 'temporal' else ''
hdr = ('         & & Principal & Variante & \\multicolumn{3}{c}{Variante comparada com o principal} \\\\\n'
       '        \\cmidrule(lr){5-7}\n'
       '        Protocolo & Indicador & (mesmas {\\azul amostras}) & (sem as 3) & $\\hat{A}_{12}$ & Efeito & $p$ \\\\\n')
table('tab-04-res-sens-teste.tex',
      'Impacto da quebra de identidade: {\\rosa mediana} por release e comparação entre os modelos',
      'tab:res-sens-teste', 'llccclc', hdr, body)
