// Native PowerPoint version of f1_mapa_roc_feature_x_algoritmo, in the colors of the presentation template.
// Input: graficos_apresentacao/por_feature/empates_roc.csv (written by graficos_por_feature.py).
// Usage: node mapa_roc_slide_pptx.js <empates_roc.csv> <saida.pptx>   (needs pptxgenjs)
const fs = require('fs');
const pptxgen = require('pptxgenjs');
const [CSV, OUT] = process.argv.slice(2);

const ALGS = ['LightGBM', 'MLP', 'LogisticRegression', 'XGBoost', 'LinearSVC', 'RandomForest', 'DT'];
const SHORT = { LightGBM: 'LightGBM', MLP: 'MLP', LogisticRegression: 'Regr. log.', XGBoost: 'XGBoost',
                LinearSVC: 'SVM linear', RandomForest: 'RF', DT: 'DT' };
const INK = '262626', MUTED = '7F7F7F', MARK = '1F2937';
const LO = 0.45, HI = 0.95;
const RAMP = [[0.0, 'F4FBFA'], [0.5, '69CCB9'], [1.0, '1E6B6B']];   // template teal, light -> dark

const rows = fs.readFileSync(CSV, 'utf8').trim().split(/\r?\n/).slice(1).map(l => {
  const [feature, algoritmo, roc, melhor, empata] = l.split(',');
  return { feature, algoritmo, roc: +roc, melhor: melhor === 'True', empata: empata === 'True' };
});
const get = (f, a) => rows.find(r => r.feature === f && r.algoritmo === a);
const features = [...new Set(rows.map(r => r.feature))]
  .sort((a, b) => get(b, 'LightGBM').roc - get(a, 'LightGBM').roc);

function color(v) {
  const t = Math.min(1, Math.max(0, (v - LO) / (HI - LO)));
  const k = t <= RAMP[1][0] ? 0 : 1;
  const [t0, c0] = RAMP[k], [t1, c1] = RAMP[k + 1];
  const u = (t - t0) / (t1 - t0);
  const ch = i => Math.round(parseInt(c0.substr(i, 2), 16) * (1 - u) + parseInt(c1.substr(i, 2), 16) * u);
  return [0, 2, 4].map(i => ch(i).toString(16).padStart(2, '0')).join('').toUpperCase();
}
const darkText = v => (v - LO) / (HI - LO) < 0.74;

// border of each cell edge: the stronger mark of the two cells sharing it wins (best > tie > white grid)
const GRID = { type: 'solid', pt: 1, color: 'FFFFFF' };
const BEST = { type: 'solid', pt: 3, color: MARK };
const TIE = { type: 'dash', pt: 1.5, color: MARK };
const level = r => (r ? (r.melhor ? 2 : r.empata ? 1 : 0) : 0);
const style = l => [GRID, TIE, BEST][l];
const edge = (a, b) => ({ ...style(Math.max(level(a), level(b))) });

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.title = 'ROC-AUC por feature e algoritmo';
const slide = pres.addSlide();
slide.addText('Qual algoritmo acerta melhor os métodos de cada feature?', {
  x: 3.7, y: 0.3, w: 9.2, h: 0.55, fontSize: 26, bold: true, color: INK, margin: 0, isTextBox: true,
  objectName: 'Título' });
slide.addText('ROC-AUC dentro de cada feature, protocolo temporal (0,5 = acaso)', {
  x: 3.7, y: 0.85, w: 9.2, h: 0.32, fontSize: 14, color: MUTED, margin: 0, isTextBox: true,
  objectName: 'Subtítulo' });

const base = { fontSize: 12, valign: 'middle', align: 'center', margin: [0, 0.04, 0, 0.04] };
const NONE = { type: 'none' };
// cells outside the grid repeat the mark of the neighbouring data cell on the shared edge, so it is not overridden
const outer = r => (level(r) ? style(level(r)) : NONE);
const table = [[{ text: '', options: { ...base, border: [NONE, NONE, NONE, NONE] } },
  ...ALGS.map(a => ({ text: SHORT[a], options: { ...base, bold: true, color: INK,
                                                  border: [NONE, NONE, outer(get(features[0], a)), NONE] } }))]];
features.forEach((f, i) => {
  const line = [{ text: f, options: { ...base, align: 'right', color: INK, margin: [0, 0.1, 0, 0],
                                      border: [NONE, outer(get(f, ALGS[0])), NONE, NONE] } }];
  ALGS.forEach((a, j) => {
    const r = get(f, a);
    const up = i > 0 ? get(features[i - 1], a) : null, down = i < features.length - 1 ? get(features[i + 1], a) : null;
    const left = j > 0 ? get(f, ALGS[j - 1]) : null, right = j < ALGS.length - 1 ? get(f, ALGS[j + 1]) : null;
    line.push({ text: r.roc.toFixed(3).replace('.', ','), options: { ...base,
      fill: { color: color(r.roc) }, color: darkText(r.roc) ? INK : 'FFFFFF', bold: r.melhor,
      border: [edge(r, up), edge(r, right), edge(r, down), edge(r, left)] } });
  });
  table.push(line);
});
slide.addTable(table, { x: 0.6, y: 1.3, w: 11.4, colW: [2.0, ...ALGS.map(() => 9.4 / ALGS.length)], rowH: 0.3,
                        objectName: 'Mapa ROC-AUC' });

// legend: colour scale + border meaning
const LX = 12.15, LY = 1.6;
slide.addText('ROC-AUC', { x: LX, y: LY - 0.32, w: 1.0, h: 0.28, fontSize: 11, bold: true, color: MUTED, margin: 0,
                           isTextBox: true });
[0.9, 0.8, 0.7, 0.6, 0.5].forEach((v, k) => {
  slide.addShape(pres.shapes.RECTANGLE, { x: LX, y: LY + k * 0.36, w: 0.32, h: 0.32, fill: { color: color(v) },
                                          line: { color: 'FFFFFF', width: 0.5 } });
  slide.addText(v.toFixed(1).replace('.', ','), { x: LX + 0.4, y: LY + k * 0.36, w: 0.5, h: 0.32, fontSize: 11,
                                                  color: MUTED, margin: 0, valign: 'middle', isTextBox: true });
});
slide.addShape(pres.shapes.RECTANGLE, { x: LX, y: LY + 2.05, w: 0.32, h: 0.24, fill: { color: 'FFFFFF' },
                                        line: { color: MARK, width: 2.25 } });
slide.addText('melhor', { x: LX + 0.4, y: LY + 2.03, w: 0.8, h: 0.28, fontSize: 11, color: MUTED, margin: 0,
                          valign: 'middle', isTextBox: true });
slide.addShape(pres.shapes.RECTANGLE, { x: LX, y: LY + 2.45, w: 0.32, h: 0.24, fill: { color: 'FFFFFF' },
                                        line: { color: MARK, width: 1.25, dashType: 'dash' } });
slide.addText('empate', { x: LX + 0.4, y: LY + 2.43, w: 0.8, h: 0.28, fontSize: 11, color: MUTED, margin: 0,
                          valign: 'middle', isTextBox: true });

slide.addNotes('Cada algoritmo usa a configuração da Tabela 5 do TCC. Moldura cheia: melhor ROC-AUC da feature. '
  + 'Tracejada: empate estatístico com o melhor (o IC 95% da diferença, por bootstrap pareado com 100 reamostragens, '
  + 'inclui zero). DataTools tem só 6 métodos alterados no teste, então seus valores são pouco confiáveis. '
  + 'LightGBM é o melhor ou empata com o melhor em 13 das 14 features; a exceção é o RAP.');
pres.writeFile({ fileName: OUT }).then(f => console.log('ok', f));
