"""Runs ONE job (subprocess started by train.py): fit on the training indices, evaluate, save the result atomically.

A job is a (fase, protocolo, variante, conjunto, reamostragem, algoritmo, parte) tuple; parte = 'teste' (train on the
whole training set, evaluate on the test set, save per-row predictions and per-feature metrics) or 'cvKK' (fold KK of
the stratified CV on the training set of the random protocol).
Usage: python job.py <spec.json>
"""
import os
import socket
import sys
import time
import traceback

import numpy as np
from sklearn.model_selection import StratifiedKFold

from common import Run, load_config, read_json, versions, write_json
from metrics import feature_release, per_feature, scores
from models import fit_predict, importances


def log(*m):
    print(time.strftime('%H:%M:%S'), *m, flush=True)


def peak_rss_gb():
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6   # KB on Linux
    except ImportError:
        import psutil
        return getattr(psutil.Process().memory_info(), 'peak_wset', 0) / 1e9


def main(spec_path):
    spec = read_json(spec_path)
    cfg = load_config()
    run = Run(spec['execucao'])
    t0 = time.time()
    meta = read_json(run.prep / 'meta.json')
    log('job', spec['id'], '| pid', os.getpid(), '| threads', spec['threads'])
    use = [c for grp in cfg['conjuntos'][spec['conjunto']] for c in cfg[grp]]
    cidx = np.array([meta['colunas'].index(c) for c in use])
    X = np.load(run.prep / 'X.npy', mmap_mode='r')
    y = np.load(run.prep / 'y.npy')
    feat = np.load(run.prep / 'feature.npy')
    release = np.load(run.prep / 'release.npy')
    base = run.prep / 'splits' / f'{spec["protocolo"]}__{spec["variante"]}'
    tr = np.load(f'{base}__train.npy')
    te = np.load(f'{base}__test.npy')
    if spec['parte'] != 'teste':
        k = int(spec['parte'][2:])
        skf = StratifiedKFold(n_splits=spec['cv_partes'], shuffle=True, random_state=spec['semente'])
        for i, (f_tr, f_va) in enumerate(skf.split(np.zeros(len(tr)), y[tr]), start=1):
            if i == k:
                tr, te = tr[f_tr], tr[f_va]
                break
    log(f'treino={len(tr)} (pos={int(y[tr].sum())}) avaliação={len(te)} (pos={int(y[te].sum())}) '
        f'colunas={len(cidx)}')
    Xtr = np.asarray(X[np.ix_(tr, cidx)], dtype=np.float64)     # float64, as in the pilot
    Xte = np.asarray(X[np.ix_(te, cidx)], dtype=np.float64)
    ytr, yte = y[tr].astype(np.int64), y[te].astype(np.int64)
    t1 = time.time()
    pred, score, model, info = fit_predict(spec['algoritmo'], spec['reamostragem'], Xtr, ytr, Xte,
                                           spec['semente'], spec['threads'], log)
    del Xtr
    fit_s = time.time() - t1
    s = scores(yte, pred, score)
    log(f'AP={s["PR AUC (AP)"]:.4f} AUC={s["ROC AUC score"]:.4f} MCC={s["MCC"]:.4f} F1(1)={s["F1(class1)"]:.4f} '
        f'({fit_s:.0f} s de treino)')
    res = {**{k: v for k, v in spec.items() if k != 'threads_env'}, 'metricas': s, **info,
           'segundos_treino': round(fit_s, 1), 'linhas_treino': int(len(tr)), 'positivos_treino': int(ytr.sum())}
    if spec['parte'] == 'teste':
        res['por_feature'] = per_feature(yte, pred, score, feat[te], meta['features'])
        res['importancias'] = importances(model, use)
        res['por_feature_release'] = feature_release(yte, pred, score, feat[te], release[te], meta['features'])
        tmp = run.preds / f'{spec["id"]}.tmp.npz'
        np.savez(tmp, score=score, pred=pred)
        os.replace(tmp, run.preds / f'{spec["id"]}.npz')
    res.update({'segundos': round(time.time() - t0, 1), 'pico_ram_gb': round(peak_rss_gb(), 2),
                'host': socket.gethostname(), 'versoes': versions(), 'sha256_manifesto': meta.get('sha256_manifesto')})
    write_json(run.jobs / f'{spec["id"]}.json', res)
    log('ok', spec['id'], f'{res["segundos"]} s, pico de RAM {res["pico_ram_gb"]} GB')


if __name__ == '__main__':
    try:
        main(sys.argv[1])
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush()
        sys.exit(1)
