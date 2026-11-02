"""Shared paths, configuration and I/O helpers of the training package (PLANO_TREINO.md).

Layout of the package root (TCC_RAIZ, default = parent of scripts/):
  dados/                 19 parquets, calendario.csv, MANIFESTO.sha256 (read only)
  config/experimentos.yaml
  trabalho/              prepared matrices and predictions (large; not sent back)
  saida/                 logs, errors and results (zipped into saida/resultados_e_logs.zip)
Two runs share the code: 'principal' (full data) and 'teste_rapido' (stratified 1% sample).
"""
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(os.environ.get('TCC_RAIZ', Path(__file__).resolve().parent.parent))
DADOS = Path(os.environ.get('TCC_DADOS', ROOT / 'dados'))
CONFIG = ROOT / 'config' / 'experimentos.yaml'
TRABALHO = ROOT / 'trabalho'
SAIDA = ROOT / 'saida'


def load_config():
    with open(CONFIG, encoding='utf-8') as fh:
        cfg = yaml.safe_load(fh)
    cfg['colunas'] = cfg['estruturais'] + cfg['evolutivas']
    return cfg


class Run:
    """Directories of one run ('principal' or 'teste_rapido')."""

    def __init__(self, name):
        if name not in ('principal', 'teste_rapido'):
            raise SystemExit(f'execução desconhecida: {name}')
        self.name = name
        self.sample = name == 'teste_rapido'
        self.prep = TRABALHO / ('prep_amostra' if self.sample else 'prep')
        self.preds = TRABALHO / ('predicoes_teste_rapido' if self.sample else 'predicoes')
        out = SAIDA / 'teste_rapido' if self.sample else SAIDA
        self.out = out
        self.logs = out / 'logs'
        self.job_logs = out / 'logs' / 'jobs'
        self.errors = out / 'erros'
        self.results = out / 'resultados'
        self.jobs = out / 'resultados' / 'jobs'
        self.status = out / 'status'
        for p in (self.prep, self.preds, self.logs, self.job_logs, self.errors, self.results, self.jobs, self.status):
            p.mkdir(parents=True, exist_ok=True)


def write_json(path, obj):
    """Atomic write (tmp + rename): a crash never leaves a truncated result."""
    path = Path(path)
    tmp = path.with_suffix(path.suffix + f'.tmp{os.getpid()}')
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1, default=_json_default)
    os.replace(tmp, path)


def _json_default(o):
    import numpy as np
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return None if np.isnan(o) else float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(type(o))


def read_json(path):
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def sha256(path, block=1 << 24):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        while chunk := fh.read(block):
            h.update(chunk)
    return h.hexdigest()


def versions():
    import importlib
    out = {'python': sys.version.split()[0], 'platform': platform.platform()}
    for mod in ('numpy', 'pandas', 'pyarrow', 'scipy', 'sklearn', 'imblearn', 'xgboost', 'lightgbm', 'joblib'):
        try:
            out[mod] = importlib.import_module(mod).__version__
        except Exception as e:  # noqa: BLE001 - reported, not fatal here
            out[mod] = f'ERRO: {e}'
    return out


class Log:
    """Prints with a timestamp to stdout (captured by executar_tudo.sh) and to a log file."""

    def __init__(self, path):
        self.fh = open(path, 'a', encoding='utf-8', buffering=1)

    def __call__(self, *msg):
        line = time.strftime('%Y-%m-%d %H:%M:%S ') + ' '.join(str(m) for m in msg)
        print(line, flush=True)
        self.fh.write(line + '\n')
