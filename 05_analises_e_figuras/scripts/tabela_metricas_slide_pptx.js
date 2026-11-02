// Native PowerPoint table of the metric categories, in the colors of the presentation template (36º SiC / UDESC).
const pptxgen = require('pptxgenjs');
const OUT = process.argv[2];

const INK = '262626', MUTED = '7F7F7F';
const BLOCKS = [
  { title: 'CK', sub: 'Estruturais · 29', fill: '339999', tint: 'E3F1F1', head: 'FFFFFF', rows: [
    ['Acoplamento', 5, 'cbo, fanin, fanout'],
    ['Complexidade', 5, 'wmc, loopQty, maxNestedBlocksQty'],
    ['Tamanho', 1, 'loc'],
    ['Elementos do corpo', 10, 'variablesQty, parametersQty, returnsQty'],
    ['Chamadas a métodos', 3, 'methodsInvokedQty, methodsInvokedLocalQty'],
    ['Estruturas aninhadas', 3, 'lambdasQty, innerClassesQty, anonymousClassesQty'],
    ['Declaração e documentação', 2, 'modifiers, hasJavaDoc'],
  ] },
  { title: 'Understand', sub: 'Estruturais · 53 (23 usadas)', fill: '69CCB9', tint: 'E9F7F4', head: '17403A', rows: [
    ['Complexidade', 10, 'Cyclomatic, Essential, MaxNesting'],
    ['Tamanho', 9, 'CountLineCode, CountStmt, CountSemicolon'],
    ['Comentários', 2, 'CountLineComment, RatioCommentToCode'],
    ['Fluxo de dados', 2, 'CountInput, CountOutput'],
    ['Nível de classe (vazias para métodos)', 30, 'AvgCyclomatic, CountDeclMethod, MaxEssential'],
  ] },
  { title: 'Evolutivas', sub: 'Histórico de mudanças · 16', fill: 'D16722', tint: 'FBEADF', head: 'FFFFFF', rows: [
    ['Tempo', 3, 'BOM, FCH, LCH'],
    ['Ocorrência e frequência', 3, 'CHO, FRCH, WFR'],
    ['Volume de mudança', 4, 'TACH, CSB, LCA'],
    ['Densidade de mudança', 4, 'CHD, CSBS, ACDF'],
    ['Ponderadas pela recência', 2, 'WCH, WCD'],
  ] },
];

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';            // 13.333 x 7.5 in, same 16:9 proportion as the template
pres.title = 'Métricas coletadas no nível de método';
const slide = pres.addSlide();

slide.addText('Métricas coletadas no nível de método', {
  x: 3.7, y: 0.3, w: 9.0, h: 0.6, fontSize: 28, bold: true, color: INK, margin: 0, isTextBox: true,
  objectName: 'Título',
});
slide.addText('98 métricas em 3 grupos, calculadas para cada método em cada release', {
  x: 3.7, y: 0.85, w: 9.0, h: 0.35, fontSize: 14, color: MUTED, margin: 0, isTextBox: true,
  objectName: 'Subtítulo',
});

const SEP = { type: 'solid', pt: 1.5, color: 'FFFFFF' };
const NONE = { type: 'none' };
const cellBase = { fontSize: 12, valign: 'middle', margin: [0, 0.08, 0, 0.08] };
const rows = [[
  { text: 'Grupo', options: { ...cellBase, bold: true, color: MUTED, border: [NONE, NONE, { type: 'solid', pt: 1, color: 'BFBFBF' }, NONE] } },
  { text: 'Subcategoria', options: { ...cellBase, bold: true, color: MUTED, border: [NONE, NONE, { type: 'solid', pt: 1, color: 'BFBFBF' }, NONE] } },
  { text: 'Qtd.', options: { ...cellBase, bold: true, color: MUTED, align: 'right', border: [NONE, NONE, { type: 'solid', pt: 1, color: 'BFBFBF' }, NONE] } },
  { text: 'Exemplos', options: { ...cellBase, bold: true, color: MUTED, border: [NONE, NONE, { type: 'solid', pt: 1, color: 'BFBFBF' }, NONE] } },
]];
for (const b of BLOCKS) {
  b.rows.forEach(([name, qtd, ex], k) => {
    const faded = name.startsWith('Nível de classe');
    const c = faded ? MUTED : INK;
    const GROUP_GAP = { type: 'solid', pt: 6, color: 'FFFFFF' };
    const last = k === b.rows.length - 1;
    const bottom = last ? GROUP_GAP : SEP;                                      // [top, right, bottom, left]
    const row = [];
    if (k === 0) {
      row.push({
        text: [
          { text: b.title, options: { fontSize: 18, bold: true, color: b.head, breakLine: true } },
          { text: b.sub, options: { fontSize: 11, color: b.head } },
        ],
        options: { ...cellBase, rowspan: b.rows.length, fill: { color: b.fill }, margin: [0, 0.14, 0, 0.14],
                   border: [NONE, { type: 'solid', pt: 4, color: 'FFFFFF' }, GROUP_GAP, NONE] },
      });
    }
    const opt = { ...cellBase, fill: { color: b.tint }, border: [NONE, NONE, bottom, NONE] };
    row.push({ text: name, options: { ...opt, color: c, italic: faded,
                                      border: [NONE, NONE, bottom, { type: 'solid', pt: 4, color: 'FFFFFF' }] } });
    row.push({ text: String(qtd), options: { ...opt, color: c, bold: true, align: 'right' } });
    row.push({ text: ex, options: { ...opt, color: faded ? MUTED : '595959', italic: faded } });
    rows.push(row);
  });
}
slide.addTable(rows, {
  x: 0.6, y: 1.35, w: 12.1, colW: [2.6, 3.5, 0.8, 5.2], rowH: 0.265, objectName: 'Tabela de métricas',
});
slide.addNotes('Alvo (o que se quer prever): o método terá alguma mudança na AST até a próxima release? '
  + 'Obtido com o ChangeDistiller. As 30 métricas de nível de classe do Understand ficam vazias para métodos e '
  + 'não influenciam os modelos. Versão completa: Tabela 3 do TCC.');

pres.writeFile({ fileName: OUT }).then(f => console.log('ok', f));
