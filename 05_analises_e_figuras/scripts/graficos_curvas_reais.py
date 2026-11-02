"""Real ROC and precision-recall curves of the best configuration of each algorithm (presentation; NOT in the thesis).

Input: curvas_roc_pr.csv, produced on the server by scripts/curvas_roc_pr.py
       (default location: resultados_e_logs/saida/resultados/curvas_roc_pr.csv).
Output: graficos_apresentacao/curvas_reais/ (PNG 300 dpi + SVG), in a clean style and in the hand-drawn style.
Usage: python graficos_curvas_reais.py [--entrada caminho.csv] [--saida pasta]
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--entrada', default=str(ROOT / 'resultados_e_logs' / 'saida' / 'resultados' / 'curvas_roc_pr.csv'))
ap.add_argument('--saida', default=str(ROOT / 'graficos_apresentacao' / 'curvas_reais'))
args = ap.parse_args()
OUT = Path(args.saida)
OUT.mkdir(parents=True, exist_ok=True)
cv = pd.read_csv(args.entrada)

ALG = {'LightGBM': ('LightGBM', '#C62828'), 'XGBoost': ('XGBoost', '#EF6C00'), 'MLP': ('MLP', '#6A1B9A'),
       'LogisticRegression': ('Regr. logística', '#1565C0'), 'LinearSVC': ('SVM linear', '#00838F'),
       'RandomForest': ('Random Forest', '#2E7D32'), 'DT': ('Árvore de decisão', '#757575')}
PROTO = {'temporal': 'temporal (prever releases futuras)', 'random': 'aleatório (dados misturados)'}


def br(v, nd=2):
    return f'{v:.{nd}f}'.replace('.', ',')


def draw(style):
    for proto in [p for p in ('temporal', 'random') if p in set(cv.protocolo)]:
        g = cv[cv.protocolo == proto]
        prev = g.taxa_positivos.iloc[0]
        order = (g[g.curva == 'pr'].groupby('algoritmo').area.first().sort_values(ascending=False).index)
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 6.5))
        for alg in order:
            nome, cor = ALG.get(alg, (alg, None))
            for ax, curva in ((a1, 'roc'), (a2, 'pr')):
                c = g[(g.algoritmo == alg) & (g.curva == curva)]
                rot = 'AUC' if curva == 'roc' else 'PR-AUC'
                nd = 3 if curva == 'roc' else 4
                conf = f'{c.conjunto.iloc[0]}, {c.reamostragem.iloc[0]}'
                ax.plot(c.x, c.y, color=cor, lw=2, label=f'{nome} ({conf}) – {rot} = {br(c.area.iloc[0], nd)}')
        a1.plot([0, 1], [0, 1], '--', color='black', lw=1.2, label='Classificador aleatório (AUC = 0,5)')
        a1.set_xlabel('Taxa de falsos positivos')
        a1.set_ylabel('Taxa de verdadeiros positivos')
        a1.set_title('Curva ROC')
        a2.axhline(prev, ls='--', color='black', lw=1.2,
                   label=f'Classificador aleatório (taxa de positivos = {br(100 * prev, 2)}%)')
        a2.set_yscale('log')
        a2.set_ylim(prev / 3, 1.05)
        a2.set_xlabel('Revocação (dos métodos que mudam, quantos foram encontrados)')
        a2.set_ylabel('Precisão (dos alertas, quantos estavam certos) – escala log')
        a2.set_title('Curva precisão-revocação')
        a2.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 3) if v < 0.01 else br(v, 2)))
        for ax in (a1, a2):
            ax.legend(fontsize=8.5, loc='upper right' if ax is a2 else 'lower right')
            ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 1)))
        a1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: br(v, 1)))
        fig.suptitle(f'Melhor configuração de cada algoritmo – protocolo {PROTO[proto]}', fontsize=15)
        fig.tight_layout()
        nome_arq = f'curvas_{proto}' + ('_desenhado' if style == 'xkcd' else '')
        for ext in ('png', 'svg'):
            fig.savefig(OUT / f'{nome_arq}.{ext}', dpi=300, bbox_inches='tight')
        plt.close(fig)
        print('ok', nome_arq)


plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 12,
                     'axes.grid': True, 'grid.alpha': 0.3, 'grid.linestyle': '--', 'axes.spines.top': False,
                     'axes.spines.right': False})
draw('limpo')
with plt.xkcd(scale=0.6, length=150, randomness=2):
    plt.rcParams['font.family'] = ['Comic Sans MS', 'DejaVu Sans']
    draw('xkcd')
