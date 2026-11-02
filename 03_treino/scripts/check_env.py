"""Environment check before training: library versions, system resources and a mini training of every
algorithm x resampling on synthetic imbalanced data (same code path as the jobs). Also checks that the fast weighted
metrics used by the bootstrap match sklearn with sample_weight.
Output: saida/logs/check_env.json. Exit code 1 if anything fails.
"""
import os
import platform
import shutil
import sys
import time
import traceback

import numpy as np
import psutil
from sklearn.metrics import average_precision_score, roc_auc_score

from common import ROOT, SAIDA, Log, load_config, versions, write_json
from metrics import Sorted
from models import fit_predict

(SAIDA / 'logs').mkdir(parents=True, exist_ok=True)
log = Log(SAIDA / 'logs' / 'check_env.log')
cfg = load_config()
report = {'inicio': time.strftime('%Y-%m-%d %H:%M:%S'), 'versoes': versions(), 'erros': []}
log('versões:', report['versoes'])
for k, v in report['versoes'].items():
    if str(v).startswith('ERRO'):
        report['erros'].append(f'import {k}: {v}')
vm = psutil.virtual_memory()
report['sistema'] = {
    'plataforma': platform.platform(), 'glibc': platform.libc_ver(), 'python': sys.executable,
    'nucleos_logicos': psutil.cpu_count(logical=True), 'nucleos_fisicos': psutil.cpu_count(logical=False),
    'ram_total_gb': round(vm.total / 1e9, 1), 'ram_livre_gb': round(vm.available / 1e9, 1),
    'disco_livre_gb': round(shutil.disk_usage(ROOT).free / 1e9, 1),
    'carga_1_5_15min': os.getloadavg() if hasattr(os, 'getloadavg') else None}
log('sistema:', report['sistema'])

# ---- mini training (same functions as job.py) ----
rng = np.random.default_rng(0)
n, d = 4000, 12
X = rng.normal(size=(n, d)).astype(np.float32)
y = (X[:, 0] + 0.5 * X[:, 1] + rng.normal(scale=1.0, size=n) > 2.6).astype(np.int64)
log(f'mini-treino: {n} linhas, {int(y.sum())} positivos')
algs = sorted({a for f in ('fase1', 'fase2') for a in cfg['fases'][f]['algoritmos']})
report['mini_treino'] = {}
for alg in algs:
    for rs in cfg['reamostragem']:
        t0 = time.time()
        try:
            pred, score, _, info = fit_predict(alg, rs, X[:3000], y[:3000], X[3000:], 42, 2, lambda *a: None)
            auc = roc_auc_score(y[3000:], score)
            report['mini_treino'][f'{alg}/{rs}'] = {'auc': round(auc, 3), 'segundos': round(time.time() - t0, 2)}
            if not np.isfinite(score).all() or auc < 0.6:
                report['erros'].append(f'mini-treino {alg}/{rs}: AUC {auc:.3f} ou scores não finitos')
        except Exception as e:  # noqa: BLE001 - everything is reported
            report['erros'].append(f'mini-treino {alg}/{rs}: {e!r}')
            log(traceback.format_exc())
log('mini-treino:', report['mini_treino'])

# ---- weighted metrics (bootstrap) == sklearn with sample_weight ----
s = np.round(rng.random(5000), 2).astype(np.float32)           # rounded: many ties
yy = (rng.random(5000) < 0.1 + 0.3 * s).astype(np.int64)
w = np.bincount(rng.integers(0, 5000, 5000), minlength=5000).astype(float)
m = Sorted(yy, s, (s > 0.5).astype(np.int8)).metrics(w)
ref_auc = roc_auc_score(yy, s, sample_weight=w)
ref_ap = average_precision_score(yy, s, sample_weight=w)
report['bootstrap_metricas'] = {'auc': [m['ROC AUC score'], ref_auc], 'ap': [m['PR AUC (AP)'], ref_ap]}
if abs(m['ROC AUC score'] - ref_auc) > 1e-9 or abs(m['PR AUC (AP)'] - ref_ap) > 1e-9:
    report['erros'].append(f'métricas ponderadas divergem do sklearn: {report["bootstrap_metricas"]}')
log('métricas ponderadas vs sklearn:', report['bootstrap_metricas'])

report['fim'] = time.strftime('%Y-%m-%d %H:%M:%S')
write_json(SAIDA / 'logs' / 'check_env.json', report)
if report['erros']:
    log('FALHAS:\n' + '\n'.join(report['erros']))
    sys.exit(1)
log('ambiente OK')
