"""Regression test: outputs of the new s04-s07, run on EGit with the pilot's timeline (EGit_validacao_piloto),
against the pilot's outputs (4-Coleta_egit/data). Compares every common column, row by row."""
import numpy as np, pandas as pd
from pathlib import Path
B = Path(__file__).resolve().parents[1]; PIL = B.parent / '4-Coleta_egit' / 'data'; NEW = B / 'EGit_validacao_piloto' / 'data'

def compare(name, old, new, keys):
    old, new = old.sort_values(keys).reset_index(drop=True), new.sort_values(keys).reset_index(drop=True)
    print(f'== {name}: pilot {old.shape} | new {new.shape}')
    if len(old) != len(new) or not (old[keys].values == new[keys].values).all():
        print('   ROW KEYS DIFFER'); return False
    ok = True
    for c in [c for c in old.columns if c in new.columns and c not in keys]:
        a, b = old[c], new[c]
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            eq = np.isclose(a.astype(float), b.astype(float), rtol=1e-12, atol=1e-12, equal_nan=True)
        else:
            eq = (a.astype(str).values == b.astype(str).values)
        if not eq.all():
            ok = False; print(f'   column {c}: {int((~eq).sum())} differences')
    only = sorted(set(old.columns) ^ set(new.columns))
    print('   columns only in one side:', only)
    print('   IDENTICAL' if ok else '   DIFFERENT'); return ok

evo_o = pd.read_csv(PIL / 'evometrics.csv'); evo_n = pd.read_parquet(NEW / 'evometrics.parquet')
compare('evometrics', evo_o, evo_n.drop(columns=['feature', 'repository']), ['release', 'method_name'])
cd_o = pd.read_csv(PIL / 'change_distiller.csv', low_memory=False); cd_n = pd.read_parquet(NEW / 'change_distiller.parquet')
for d in (cd_o, cd_n):
    for c in ['CLASS_CURRENTCOMMIT', 'CLASS_PREVIOUSCOMMIT']: d[c] = d[c].fillna('').astype(str).replace('nan', '')
compare('change_distiller', cd_o, cd_n.drop(columns=['PROJECT_NAME']).assign(PROJECT_NAME=cd_o.sort_values(['CURRENT_COMMIT','method_name'])['PROJECT_NAME'].values[0]) if False else cd_n.drop(columns=['PROJECT_NAME']), ['CURRENT_COMMIT', 'method_name'])
fo = pd.read_csv(PIL / 'egit-all-releases.csv', low_memory=False); fn = pd.read_parquet(NEW / 'EGit-all-releases.parquet')
compare('dataset final', fo.drop(columns=['project']), fn.drop(columns=['project', 'feature', 'repository', 'method_uid']), ['release', 'method_name'])
ja = pd.read_csv(PIL / 'join_audit.csv'); jn = pd.read_csv(NEW / 'join_audit.csv')
compare('join_audit', ja, jn.drop(columns=['tag']), ['release'])
