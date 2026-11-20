"""Figures of the hypothesis tests (reads the output of testes_hipoteses.py).

t_acaso_metodo   best temporal model: null distribution of PR-AUC and ROC-AUC with the labels shuffled (permutation)
                 next to the distribution of the model (bootstrap of the test rows)
t_acaso_feature  feature level: null distribution of the mean Spearman (predicted rates shuffled within each
                 release) and the observed values of the model, the persistence and the historical mean
t_sensibilidade  sensitivity: bootstrap distribution of delta = variant - main model restricted, per protocol and
                 metric, with the line of H0 (delta = 0) and the 95% interval
Writes PNG/SVG/PDF with title to graficos_apresentacao/resultados/ and PDF without title to
TCC___Kevin___UDESC/Textuais/imagens/testes/.
Usage: python graficos_testes.py
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
RES = ROOT / 'resultados_e_logs' / 'saida' / 'resultados'
OUT = ROOT / 'graficos_apresentacao' / 'resultados'
OUT_TCC = ROOT / 'TCC___Kevin___UDESC' / 'Textuais' / 'imagens' / 'testes'
OUT_TCC.mkdir(parents=True, exist_ok=True)
C_NULO, C_MOD, C_PERS, C_HIST = '#8C8C8C', '#0072B2', '#E69F00', '#009E73'
C_OBS = '#FFC20A'  # observed value over the blue histograms (yellow, visible on blue and on white)

plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 12,
    'axes.titlesize': 12, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True,
    'grid.alpha': 0.3, 'grid.linestyle': '--', 'savefig.bbox': 'tight', 'savefig.dpi': 300,
})


def br(x, nd=2):
    v = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    return f'{v:.{nd}f}'.replace('.', ',').replace('-', '−')


def comma_axis(ax, nd):
    ax.xaxis.set_major_locator(mtick.MaxNLocator(5))
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, nd)))


def mil(n):
    return f'{int(n):,}'.replace(',', '.')


def p_txt(p, B):  # B kept for the call sites; rounded values get ≈ (thesis convention)
    if p >= 1:
        return 'p = 1'
    return f'p ≈ {f"{p:.1g}".replace(".", ",")}' if p < 0.01 else f'p ≈ {br(p, 2)}'


T = pd.read_csv(RES / 'testes_hipoteses.csv')
D = np.load(RES / 'testes_hipoteses_draws.npz')


def save(fig, name, title, tcc):
    if tcc:
        fig.savefig(OUT_TCC / f'{name}.pdf')
    else:
        fig.suptitle(title, fontweight='bold', y=1.0 if name == 't_sensibilidade' else None)
        for ext in ('png', 'svg', 'pdf'):
            fig.savefig(OUT / f'{name}.{ext}')
    plt.close(fig)
    print('ok', name, 'tcc' if tcc else '')


# ------------------------------------------------------------------ method level x chance
best = T[(T.teste == 'acaso_metodo') & (T.protocolo == 'temporal')].sort_values('observado', ascending=False)
best_id = best[best.metrica == 'PR AUC (AP)'].iloc[0].id
for tcc in (False, True):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    for ax, met, nd, lab in zip(axes, ('PR AUC (AP)', 'ROC AUC score'), (4, 2), ('PR-AUC', 'ROC-AUC')):
        r = T[(T.teste == 'acaso_metodo') & (T.id == best_id) & (T.metrica == met)].iloc[0]
        null, boot = D[f'nulo|{best_id}|{met}'], D[f'boot|{best_id}|{met}']
        ax.hist(null, bins=40, color=C_NULO, alpha=.85, label=f'Sob H$_0$ (rótulos embaralhados, {mil(r.B)} vezes)')
        ax.hist(boot, bins=40, color=C_MOD, alpha=.85, label='Modelo (bootstrap das linhas de teste)')
        ax.axvline(r.referencia_acaso, color='k', ls='--', lw=1.2,
                   label=f'Valor do acaso: {br(r.referencia_acaso, 4 if nd == 4 else 1)}')
        ax.axvline(r.observado, color=C_OBS, lw=1.2, label='Valor observado')
        ax.set(xlabel=lab, ylabel='Frequência', yticks=[])
        comma_axis(ax, nd)
        ax.set_title(f'{lab}: observado {br(r.observado, 4 if nd == 4 else 3)} | {p_txt(r.p_valor, int(r.B))}')
        ax.legend(fontsize=9.5, loc='upper center', frameon=False)
        ax.set_ylim(top=ax.get_ylim()[1] * 1.45)
    save(fig, 't_acaso_metodo', 'Teste de permutação: melhor modelo do protocolo temporal × acaso', tcc)

# ------------------------------------------------------------------ feature level x chance
F = T[T.teste == 'acaso_feature'].set_index('algoritmo')
null = D['nulo_feature|modelo']
for tcc in (False, True):
    fig, ax = plt.subplots(figsize=(10, 4.4))
    ax.hist(null, bins=50, color=C_NULO, alpha=.85,
            label=f'Sob H$_0$ (taxas previstas embaralhadas, {mil(F.loc["modelo", "B"])} vezes)')
    for k, c, lab in (('modelo', C_MOD, 'Modelo'), ('persistencia', C_PERS, 'Persistência'),
                      ('media_historica', C_HIST, 'Média histórica')):
        r = F.loc[k]
        ax.axvline(r.observado, color=c, lw=2, label=f'{lab}: {br(r.observado, 3)} ({p_txt(r.p_valor, int(r.B))})')
    ax.axvline(0, color='k', ls='--', lw=1)
    ax.set(xlabel='Correlação de Spearman média nas 17 releases de teste', ylabel='Frequência', yticks=[], xlim=(-.45, .8))
    comma_axis(ax, 1)
    ax.xaxis.set_major_locator(mtick.MultipleLocator(.2))
    ax.legend(fontsize=10, loc='upper center', bbox_to_anchor=(.5, -.2), ncol=2, frameon=False)
    save(fig, 't_acaso_feature', 'Teste de permutação: ordenação das features × acaso', tcc)

# ------------------------------------------------------------------ sensitivity
S = T[T.teste == 'sensibilidade']
for tcc in (False, True):
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.2))
    for i, proto in enumerate(('temporal', 'random')):
        for j, (met, lab, nd) in enumerate((('PR AUC (AP)', 'PR-AUC', 4), ('ROC AUC score', 'ROC-AUC', 4))):
            ax = axes[i, j]
            r = S[(S.protocolo == proto) & (S.metrica == met)].iloc[0]
            d = D[f'delta|{proto}|{met}']
            ax.axvspan(r.IC95_inf, r.IC95_sup, color=C_MOD, alpha=.12, label='IC 95%')
            ax.hist(d, bins=40, color=C_MOD, alpha=.85, label='Δ nas 1.000 reamostras')
            ax.axvline(0, color='k', ls='--', lw=1.2, label='H$_0$: Δ = 0')
            ax.axvline(r.observado, color=C_OBS, lw=2.4, label='Δ observado')
            lo = min(0, d.min()) - .1 * (d.max() - min(0, d.min()))
            ax.set_xlim(lo, d.max() + .1 * (d.max() - lo))
            comma_axis(ax, nd)
            ax.set(xlabel=f'Δ {lab} (variante − principal restrito)', ylabel='Frequência', yticks=[])
            ax.set_title(f'{"Temporal" if proto == "temporal" else "Aleatório"}, {lab}: Δ = {br(r.observado, 4 if lab == "PR-AUC" else 3)} | '
                         f'{p_txt(r.p_valor, int(r.B))}')
    fig.tight_layout(rect=(0, .05, 1, 1 if tcc else .95))
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc='lower center', ncol=4, frameon=False, fontsize=11)
    save(fig, 't_sensibilidade', 'Análise de sensibilidade: diferença pareada (bootstrap) e hipótese nula', tcc)
