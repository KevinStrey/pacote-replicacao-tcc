"""Rebuilds resultados_teste.csv and por_feature.csv from the job JSONs (resultados/jobs/*.json), with the same logic as
scripts/collect_results.py (load_rows + CV aggregation + sort), without recomputing anything.

Needed because both CSVs were opened and saved in Excel after the training (';' separator and numbers converted, e.g.
0,000095 -> 9,53E+10 in por_feature.csv). The current files are kept as *_excel.csv. The rebuilt tables are checked
against the job JSONs and against the copy taken before Excel (6-Treino/resultados_e_logs, phase 1 only).
Usage: python regerar_csv_resultados.py
"""
import json
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / 'resultados_e_logs' / 'saida' / 'resultados'
OLD = ROOT / '6-Treino' / 'resultados_e_logs' / 'saida' / 'resultados'
KEYS = ['fase', 'protocolo', 'variante', 'conjunto', 'reamostragem', 'algoritmo']

tests, cvs, feats = [], [], []
for p in sorted((RES / 'jobs').glob('*.json')):
    r = json.loads(p.read_text(encoding='utf-8'))
    base = {k: r[k] for k in ['id'] + KEYS + ['parte']}
    extra = {k: r.get(k) for k in ('segundos', 'segundos_treino', 'pico_ram_gb', 'linhas_treino', 'positivos_treino',
                                   'linhas_treino_reamostrado', 'iteracoes', 'convergiu', 'origem')}
    row = {**base, **r['metricas'], **extra}
    if r['parte'] == 'teste':
        tests.append(row)
        feats += [{**base, **f} for f in r.get('por_feature', [])]
    else:
        cvs.append(row)
tests, cvs, feats = pd.DataFrame(tests), pd.DataFrame(cvs), pd.DataFrame(feats)
agg = cvs.groupby(KEYS).agg(cv_partes=('id', 'size'), cv_ap_media=('PR AUC (AP)', 'mean'),
                            cv_ap_dp=('PR AUC (AP)', 'std'), cv_auc_media=('ROC AUC score', 'mean'),
                            cv_auc_dp=('ROC AUC score', 'std'), cv_mcc_media=('MCC', 'mean'),
                            cv_mcc_dp=('MCC', 'std'), cv_segundos=('segundos', 'sum')).reset_index()
tests = tests.merge(agg, on=KEYS, how='left')
tests = tests.sort_values(['protocolo', 'variante', 'PR AUC (AP)'], ascending=[True, True, False])

# checks against the pre-Excel copy (phase 1): same values where both exist
for name, new in (('resultados_teste.csv', tests), ('por_feature.csv', feats)):
    old = pd.read_csv(OLD / name)
    key = ['id', 'feature'] if name == 'por_feature.csv' else ['id']
    m = old.merge(new, on=key, suffixes=('_old', ''))
    cols = [c for c in old.columns if c not in key and c in new.columns and pd.api.types.is_numeric_dtype(old[c])
            and pd.api.types.is_numeric_dtype(new[c])]
    diff = max((m[f'{c}_old'] - m[c]).abs().max() for c in cols)
    print(f'{name}: {len(new)} linhas (cópia pré-Excel: {len(old)}, em comum: {len(m)}), maior diferença: {diff:.1e}')
    assert len(m) == len(old) and diff < 1e-9

for name, df in (('resultados_teste.csv', tests), ('por_feature.csv', feats)):
    cur = RES / name
    bak = RES / name.replace('.csv', '_excel.csv')
    if cur.exists() and not bak.exists():
        shutil.copy2(cur, bak)
    df.to_csv(cur, index=False)
    print('gravado', cur.relative_to(ROOT), '| original do Excel em', bak.name)
