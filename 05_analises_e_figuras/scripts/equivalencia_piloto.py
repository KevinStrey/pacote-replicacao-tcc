"""Equivalence with the pilot: runs the training code of the package (scripts/models.py, scripts/metrics.py) on the
pilot dataset (4-Coleta_egit/data/egit-all-releases.csv), temporal protocol, and compares with the pilot results
(4-Coleta_egit/results/egit-results-trad_temporal.csv). Read only on 4-Coleta_egit.
Expected: identical metrics (float64 throughout, as in the pilot), except where the libraries are not deterministic.
Output: 6-Treino/validacao/EQUIVALENCIA_PILOTO.md (+ .csv)
Usage: python equivalencia_piloto.py [--algoritmos DT RandomForest LogisticRegression]
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

TREINO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREINO / 'scripts'))
from common import load_config  # noqa: E402
from metrics import scores  # noqa: E402
from models import fit_predict  # noqa: E402

PILOTO = TREINO.parent / '4-Coleta_egit'
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--algoritmos', nargs='+', default=['DT', 'RandomForest', 'LogisticRegression'])
ap.add_argument('--reamostragem', nargs='+', default=['NONE', 'ROS', 'SMOTE', 'ADA'])
args = ap.parse_args()
sys.stdout.reconfigure(encoding='utf-8')
cfg = load_config()
ref = pd.read_csv(PILOTO / 'results' / 'egit-results-trad_temporal.csv')
df = pd.read_csv(PILOTO / 'data' / 'egit-all-releases.csv', low_memory=False)
df[cfg['colunas']] = df[cfg['colunas']].apply(pd.to_numeric, errors='coerce').fillna(0)
y = df['will_change'].astype(int).values
counts = df.groupby('release').size().sort_index()
cum = counts.cumsum() / counts.sum()
T = int(cum[cum >= 0.7].index[0])
tr, te = np.where(df['release'] <= T)[0], np.where(df['release'] > T)[0]
print(f'piloto: {len(df)} linhas, T={T}, treino={len(tr)}, teste={len(te)}')
rows = []
for conj, grupos in cfg['conjuntos'].items():
    cols = [c for g in grupos for c in cfg[g]]
    X = df[cols].to_numpy(dtype=np.float64)
    for rs in args.reamostragem:
        for alg in args.algoritmos:
            t0 = time.time()
            pred, score, _, _ = fit_predict(alg, rs, X[tr], y[tr], X[te], 42, 8, lambda *a: None)
            s = scores(y[te], pred, score)
            r = ref[(ref['model'] == conj) & (ref['resample'] == rs) & (ref['Algoritm'] == alg)].iloc[0]
            row = {'conjunto': conj, 'reamostragem': rs, 'algoritmo': alg}
            for m in ('ROC AUC score', 'PR AUC (AP)', 'MCC', 'tp', 'fp'):
                row[f'{m} pacote'] = s[m]
                row[f'{m} piloto'] = r[m]
            row['dif max (AUC, AP, MCC)'] = max(abs(s[m] - r[m]) for m in ('ROC AUC score', 'PR AUC (AP)', 'MCC'))
            rows.append(row)
            print(f'{conj} {rs:5s} {alg:18s} dif={row["dif max (AUC, AP, MCC)"]:.2e} tp {s["tp"]}/{r["tp"]} '
                  f'fp {s["fp"]}/{r["fp"]} ({time.time() - t0:.0f} s)', flush=True)
out = pd.DataFrame(rows)
(TREINO / 'validacao').mkdir(exist_ok=True)
out.to_csv(TREINO / 'validacao' / 'equivalencia_piloto.csv', index=False)
lines = ['# Equivalência com o piloto (EGit, protocolo temporal)', '',
         'Gerado por `ferramentas_locais/equivalencia_piloto.py`: código de treino do pacote (`scripts/models.py`, '
         '`scripts/metrics.py`) aplicado ao dataset do piloto (`4-Coleta_egit/data/egit-all-releases.csv`), comparado '
         'com `4-Coleta_egit/results/egit-results-trad_temporal.csv`.', '',
         f'- Linhas: {len(df)}; corte T = {T}; treino {len(tr)}; teste {len(te)}.',
         '- O pacote usa float64 em todas as etapas, como o piloto (float32 alterava cortes das árvores e vizinhos do '
         'SMOTE/ADASYN).',
         '- Diferenças restantes (ADASYN; LR do model1/model2): build das bibliotecas numéricas. O mesmo código no venv '
         'do piloto (pip, numpy 2.5.3) reproduz o piloto exatamente (ex.: model3/ADA/DT AUC 0,368442); no ambiente '
         'conda-forge do pacote o ADASYN gera 474.343 amostras em vez de 474.395 (determinístico em cada ambiente).',
         '',
         '| Conjunto | Reamostragem | Algoritmo | AUC pacote / piloto | AP pacote / piloto | MCC pacote / piloto | '
         'tp, fp pacote / piloto | Dif. máx. |', '|---|---|---|---|---|---|---|---|']
for r in out.itertuples(index=False):
    d = r._asdict()
    v = list(d.values())
    lines.append(f'| {v[0]} | {v[1]} | {v[2]} | {v[3]:.4f} / {v[4]:.4f} | {v[5]:.4f} / {v[6]:.4f} | '
                 f'{v[7]:.4f} / {v[8]:.4f} | {v[9]}, {v[11]} / {v[10]}, {v[12]} | {v[13]:.1e} |')
(TREINO / 'validacao' / 'EQUIVALENCIA_PILOTO.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('ok')
