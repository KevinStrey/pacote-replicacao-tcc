"""Extracts the ROC and precision-recall curve points of the best configuration of each protocol x algorithm
(the rows of resultados/bootstrap_ic.csv) into a small CSV, so the curves can be plotted without copying the
per-method predictions (several GB) from the server.

Reads trabalho/predicoes/<id>.npz, trabalho/prep/y.npy and the test split of each protocol.
Output: saida/resultados/curvas_roc_pr.csv (a few MB). Each curve is down-sampled to at most 2000 points, keeping
both ends.
Usage (in the treino_tcc folder on the server):  ambiente/bin/python scripts/curvas_roc_pr.py
"""
import argparse

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score, roc_curve

from common import Run

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--execucao', default='principal', choices=['principal', 'teste_rapido'])
ap.add_argument('--pontos', type=int, default=2000)
args = ap.parse_args()
run = Run(args.execucao)
y_all = np.load(run.prep / 'y.npy')
sel = pd.read_csv(run.results / 'bootstrap_ic.csv')


def thin(x, y, n):
    if len(x) <= n:
        return x, y
    idx = np.unique(np.r_[0, np.linspace(0, len(x) - 1, n).astype(int), len(x) - 1])
    return x[idx], y[idx]


rows = []
for r in sel.itertuples():
    pred_file = run.preds / f'{r.id}.npz'
    if not pred_file.exists():
        print('sem predições:', r.id)
        continue
    te = np.load(run.prep / 'splits' / f'{r.protocolo}__principal__test.npy')
    y = y_all[te]
    s = np.load(pred_file)['score'].astype(np.float64)
    fpr, tpr, _ = roc_curve(y, s)
    prec, rec, _ = precision_recall_curve(y, s)
    base = {'id': r.id, 'protocolo': r.protocolo, 'algoritmo': r.algoritmo, 'conjunto': r.conjunto,
            'reamostragem': r.reamostragem, 'taxa_positivos': float(y.mean())}
    for curva, x, yy, area in (('roc', fpr, tpr, roc_auc_score(y, s)),
                               ('pr', rec[::-1], prec[::-1], average_precision_score(y, s))):
        x, yy = thin(x, yy, args.pontos)
        rows += [{**base, 'curva': curva, 'area': area, 'x': a, 'y': b} for a, b in zip(x, yy)]
    print('ok', r.id)
out = run.results / 'curvas_roc_pr.csv'
pd.DataFrame(rows).to_csv(out, index=False, float_format='%.6g')
print('gerado', out)
