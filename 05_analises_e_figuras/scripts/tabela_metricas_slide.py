"""Compact table of the metric categories, for the slides (the full version is Table 3 of the thesis).

Output: graficos_apresentacao/metricas/tabela_categorias_metricas.png|svg
Usage: python tabela_metricas_slide.py
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'graficos_apresentacao' / 'metricas'
OUT.mkdir(parents=True, exist_ok=True)

INK, MUTED, GRID = '#1F2937', '#6B7280', '#E5E7EB'
plt.rcParams.update({'font.family': 'sans-serif',
                     'font.sans-serif': ['Segoe UI', 'Inter', 'Helvetica', 'Arial', 'DejaVu Sans']})

# (block title, subtitle, color, tint, rows: (subcategory, count, examples))
BLOCKS = [
    ('CK', 'Estruturais · 29 métricas', '#2E86AB', '#EAF4F9', [
        ('Acoplamento', 5, 'cbo, fanin, fanout'),
        ('Complexidade', 5, 'wmc, loopQty, maxNestedBlocksQty'),
        ('Tamanho', 1, 'loc'),
        ('Elementos do corpo', 10, 'variablesQty, parametersQty, returnsQty'),
        ('Chamadas a métodos', 3, 'methodsInvokedQty, methodsInvokedLocalQty'),
        ('Estruturas aninhadas', 3, 'lambdasQty, innerClassesQty, anonymousClassesQty'),
        ('Declaração e documentação', 2, 'modifiers, hasJavaDoc'),
    ]),
    ('Understand', 'Estruturais · 53 métricas (23 usadas)', '#7E57C2', '#F3EEFA', [
        ('Complexidade', 10, 'Cyclomatic, Essential, MaxNesting'),
        ('Tamanho', 9, 'CountLineCode, CountStmt, CountSemicolon'),
        ('Comentários', 2, 'CountLineComment, RatioCommentToCode'),
        ('Fluxo de dados', 2, 'CountInput, CountOutput'),
        ('Nível de classe (vazias para métodos)', 30, 'AvgCyclomatic, CountDeclMethod, MaxEssential'),
    ]),
    ('Evolutivas', 'Histórico de mudanças · 16 métricas', '#E4572E', '#FDEEE9', [
        ('Tempo', 3, 'BOM, FCH, LCH'),
        ('Ocorrência e frequência', 3, 'CHO, FRCH, WFR'),
        ('Volume de mudança', 4, 'TACH, CSB, LCA'),
        ('Densidade de mudança', 4, 'CHD, CSBS, ACDF'),
        ('Ponderadas pela recência', 2, 'WCH, WCD'),
    ]),
]

ROW, GAP, HEAD = 0.52, 0.32, 0.62
n_rows = sum(len(b[4]) for b in BLOCKS)
H = HEAD + n_rows * ROW + GAP * (len(BLOCKS) - 1)
W = 13.0
X_BAND, X_SUB, X_QTD, X_EX = 0.0, 3.35, 7.55, 8.05

fig = plt.figure(figsize=(W, H * 0.62 + 1.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(-0.1, W)
ax.set_ylim(-0.95, H + 1.15)
ax.invert_yaxis()
ax.axis('off')

ax.text(0, -0.55, 'Métricas coletadas no nível de método', fontsize=22, fontweight='bold', color=INK, va='center')
ax.text(0, 0.05, '98 métricas em 3 grupos  ·  todas calculadas para cada método em cada release', fontsize=13,
        color=MUTED, va='center')
y = 0.62
for x, txt, ha in ((X_SUB, 'Subcategoria', 'left'), (X_QTD, 'Qtd.', 'right'), (X_EX, 'Exemplos', 'left')):
    ax.text(x, y + 0.2, txt, fontsize=12, color=MUTED, fontweight='bold', ha=ha, va='center')
y += HEAD - 0.1
for title, sub, color, tint, rows in BLOCKS:
    h = len(rows) * ROW
    ax.add_patch(FancyBboxPatch((X_SUB - 0.15, y + 0.03), W - X_SUB + 0.05, h - 0.06,
                                boxstyle='round,pad=0,rounding_size=0.12', fc=tint, ec='none'))
    ax.add_patch(FancyBboxPatch((X_BAND, y + 0.03), 3.15, h - 0.06, boxstyle='round,pad=0,rounding_size=0.12',
                                fc=color, ec='none'))
    ax.text(X_BAND + 0.22, y + h / 2 - 0.17, title, fontsize=17, fontweight='bold', color='white', va='center')
    ax.text(X_BAND + 0.22, y + h / 2 + 0.25, sub, fontsize=10.5, color='white', va='center', wrap=True)
    for k, (name, qtd, ex) in enumerate(rows):
        yc = y + (k + 0.5) * ROW
        faded = name.startswith('Nível de classe')
        c = MUTED if faded else INK
        if k:
            ax.plot([X_SUB, W - 0.2], [y + k * ROW] * 2, color='white', lw=1.6)
        ax.text(X_SUB, yc, name, fontsize=12.5, color=c, va='center', style='italic' if faded else 'normal')
        ax.text(X_QTD, yc, str(qtd), fontsize=12.5, color=c, va='center', ha='right', fontweight='bold')
        ax.text(X_EX, yc, ex, fontsize=11.5, color=MUTED if faded else '#374151', va='center', family='monospace')
    y += h + GAP

ax.text(0, y + 0.15, 'Alvo (o que se quer prever): o método terá alguma mudança na AST até a próxima release? '
        '— obtido com o ChangeDistiller', fontsize=11.5, color=MUTED, va='center')

for ext in ('png', 'svg'):
    fig.savefig(OUT / f'tabela_categorias_metricas.{ext}', dpi=300, facecolor='white', bbox_inches='tight',
                pad_inches=0.25)
print('ok tabela_categorias_metricas')
