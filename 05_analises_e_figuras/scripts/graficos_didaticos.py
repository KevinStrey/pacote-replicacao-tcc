"""Didactic charts (hand-drawn "xkcd" style) explaining ROC and precision-recall curves, for the presentation.

The curves are computed (sklearn) from SYNTHETIC scores with increasing separation between the classes; they illustrate
the concepts and are not results of the TCC. Outputs: graficos_apresentacao/didaticos/*.png|svg
Usage: python graficos_didaticos.py
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score, roc_curve  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'graficos_apresentacao' / 'didaticos'
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(42)


def scores(sep, n_pos, n_neg):
    """Positives ~ N(sep, 1), negatives ~ N(0, 1)."""
    y = np.r_[np.ones(n_pos), np.zeros(n_neg)]
    s = np.r_[rng.normal(sep, 1, n_pos), rng.normal(0, 1, n_neg)]
    return y, s


def br(v, nd=2):
    return f'{v:.{nd}f}'.replace('.', ',')


def save(fig, name):
    import matplotlib.ticker as mtick
    for ax in fig.axes:          # decimal comma on the numeric axes
        for axis in (ax.xaxis, ax.yaxis):
            if isinstance(axis.get_major_formatter(), mtick.FuncFormatter):
                continue                # keeps formatters set explicitly (e.g. integer release numbers)
            if axis.get_ticklabels() and any(t.get_text() for t in axis.get_ticklabels()):
                axis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 1)))
    for ext in ('png', 'svg'):
        fig.savefig(OUT / f'{name}.{ext}', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('ok', name)


MODELS = [(1.8, '#1f77b4', 'Modelo bom'), (0.9, '#ff7f0e', 'Modelo razoável'), (0.4, '#2ca02c', 'Modelo fraco')]

with plt.xkcd(scale=0.8, length=120, randomness=2):
    plt.rcParams['font.family'] = ['Comic Sans MS', 'DejaVu Sans']

    # ---- 1. ROC curve (balanced classes) ----
    fig, ax = plt.subplots(figsize=(7.5, 6))
    for sep, cor, nome in MODELS:
        y, s = scores(sep, 2000, 2000)
        fpr, tpr, _ = roc_curve(y, s)
        ax.plot(fpr, tpr, color=cor, lw=2, label=f'{nome} (AUC = {br(roc_auc_score(y, s))})')
    ax.plot([0, 1], [0, 1], '--', color='red', lw=2)
    ax.text(0.55, 0.43, 'Classificador aleatório', color='red', rotation=37, fontsize=12)
    ax.plot(0, 1, 'o', color='blue', ms=8)
    ax.annotate('Classificador perfeito', xy=(0.02, 1.0), xytext=(0.18, 0.97), color='blue', fontsize=12,
                arrowprops=dict(arrowstyle='->', color='blue', lw=1.5))
    ax.annotate('', xy=(0.62, 0.98), xytext=(0.78, 0.82), arrowprops=dict(arrowstyle='->', lw=2))
    ax.annotate('', xy=(0.94, 0.66), xytext=(0.78, 0.82), arrowprops=dict(arrowstyle='->', lw=2))
    ax.text(0.62, 0.86, 'Melhor', rotation=45, fontsize=12)
    ax.text(0.86, 0.78, 'Pior', rotation=-40, fontsize=12)
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(-0.03, 1.06)
    ax.set_xlabel('Taxa de falsos positivos')
    ax.set_ylabel('Taxa de verdadeiros positivos')
    ax.set_title('Curva ROC')
    ax.legend(loc='lower right', fontsize=10)
    save(fig, 'd1_curva_roc')

    # ---- 2. Precision-recall curve with RARE positives (as in the TCC: 0.5%) ----
    fig, ax = plt.subplots(figsize=(7.5, 6))
    prev = 0.005
    for sep, cor, nome in MODELS:
        y, s = scores(sep + 1.0, 400, int(400 / prev))
        p, r, _ = precision_recall_curve(y, s)
        ax.plot(r, p, color=cor, lw=2, label=f'{nome} (PR-AUC = {br(average_precision_score(y, s), 3)})')
    ax.axhline(prev, ls='--', color='red', lw=2,
               label=f'Classificador aleatório = taxa de positivos ({br(100 * prev, 1)}%)')
    ax.plot(1, 1, 'o', color='blue', ms=8)
    ax.annotate('Classificador perfeito', xy=(0.98, 1.0), xytext=(0.45, 0.93), color='blue', fontsize=12,
                arrowprops=dict(arrowstyle='->', color='blue', lw=1.5))
    ax.set_xlim(-0.03, 1.05)
    ax.set_ylim(-0.03, 1.06)
    ax.set_xlabel('Revocação (dos métodos que mudam, quantos encontrei?)')
    ax.set_ylabel('Precisão (dos alertas, quantos estavam certos?)')
    ax.set_title('Curva precisão-revocação com mudanças raras')
    ax.legend(loc='upper right', fontsize=10, bbox_to_anchor=(1.0, 0.85))
    save(fig, 'd2_curva_precisao_revocacao')

    # ---- 3. Same model, balanced vs rare positives: ROC barely moves, PR collapses ----
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.5))
    for prev_, cor, nome in ((0.5, '#1f77b4', '50% de positivos'), (0.005, '#d62728', '0,5% de positivos')):
        n_pos = 2000 if prev_ == 0.5 else 400
        y, s = scores(1.5, n_pos, int(n_pos * (1 - prev_) / prev_))
        fpr, tpr, _ = roc_curve(y, s)
        p, r, _ = precision_recall_curve(y, s)
        a1.plot(fpr, tpr, color=cor, lw=2, label=f'{nome} (AUC = {br(roc_auc_score(y, s))})')
        a2.plot(r, p, color=cor, lw=2, label=f'{nome} (PR-AUC = {br(average_precision_score(y, s))})')
    a1.plot([0, 1], [0, 1], '--', color='gray')
    a1.set_title('ROC: quase não muda')
    a1.set_xlabel('Taxa de falsos positivos')
    a1.set_ylabel('Taxa de verdadeiros positivos')
    a1.legend(loc='lower right', fontsize=10)
    a2.set_title('Precisão-revocação: despenca')
    a2.set_xlabel('Revocação')
    a2.set_ylabel('Precisão')
    a2.legend(loc='upper right', fontsize=10)
    fig.suptitle('O mesmo modelo, com mudanças comuns ou raras', fontsize=15)
    save(fig, 'd3_roc_vs_pr_classes_raras')

    # ---- 4. Temporal x random validation (concept) ----
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 5.5))
    rel = np.arange(1, 55)
    a1.bar(rel, 1, color=np.where(rel <= 36, '#1f77b4', '#d62728'), width=0.9)
    a1.set_title('Validação temporal: treina no passado, testa no futuro')
    a2.bar(rel, 0.7, color='#1f77b4', width=0.9)
    a2.bar(rel, 0.3, bottom=0.7, color='#d62728', width=0.9)
    a2.set_title('Validação aleatória: 70% dos métodos de cada release no treino e 30% no teste')
    for ax in (a1, a2):
        ax.set_yticks([])
        ax.set_xlim(0, 55)
    a2.set_xlabel('Releases (2012 a 2026)')
    a1.text(18.5, 0.4, 'TREINO', color='white', fontsize=16, ha='center', path_effects=[])
    a1.text(45.5, 0.4, 'TESTE', color='white', fontsize=16, ha='center', path_effects=[])
    for ax in (a1, a2):
        ax.xaxis.set_major_locator(matplotlib.ticker.FixedLocator([1, 10, 20, 30, 36, 40, 50, 54]))
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:.0f}'))
    fig.text(0.5, -0.03, 'Azul: treino   Vermelho: teste   (cada barra é uma release; o corte temporal é a release 36)',
             ha='center', fontsize=12)
    fig.tight_layout()
    save(fig, 'd4_validacao_temporal_vs_aleatoria')
