"""Shared configuration of the multi-feature collection (generalization of 4-Coleta_egit/scripts/config.py).

Every script takes --feature <name> (as in the mapping, ex.: "GMF Runtime"). Outputs per feature:
  5-Coleta_features/<slug>/data/   final and intermediate results (kept)
  5-Coleta_features/<slug>/work/   snapshots, blobs, temporary files (can be deleted after the feature)
Decisions M1–M18: 5-Coleta_features/INVENTARIO.md. Resources: see RESOURCES below and RECURSOS.md.
"""
import argparse
import os
import sys
from pathlib import Path

import psutil

SCRIPTS = Path(__file__).resolve().parent
BASE = SCRIPTS.parent                                  # 5-Coleta_features
ROOT = BASE.parent                                     # TCC-LPS-Prediction
REPOS = ROOT / '1-Repositorios'
CPMP = ROOT / 'cpmp'
MAPPING_CSV = BASE / 'mapeamento' / 'output' / 'mapeamento.csv'
CALENDAR_CSV = BASE / 'mapeamento' / 'output' / 'calendario.csv'

sys.path.insert(0, str(BASE / 'mapeamento'))
from features import FEATURES, is_production_java  # noqa: E402

JAVA = 'java'
UND = r'C:\Program Files\SciTools\bin\pc-win64\und.exe'
CK_JAR = CPMP / '1.ck' / 'ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar'
JME_JAR = CPMP / '4.evometrics' / 'JMethodsExtractor-0.0.1-SNAPSHOT-jar-with-dependencies.jar'
CD_JAR = CPMP / '5.cd' / 'ChangeDistillerReader-methods-0.0.1-SNAPSHOT-jar-with-dependencies.jar'
JAVA_DIR = SCRIPTS / 'java'

# ---- resources (8 physical / 16 logical cores, 15.8 GB RAM on the collection machine) ----
# Values can be overridden by environment variables (TCC_UND_WORKERS etc.). Sizing rationale: RECURSOS.md.
_CPUS = psutil.cpu_count(logical=True) or 4
RESOURCES = {
    'UND_WORKERS': int(os.environ.get('TCC_UND_WORKERS', 4)),      # parallel und processes
    'CK_WORKERS': int(os.environ.get('TCC_CK_WORKERS', 3)),        # parallel CK JVMs
    'CK_XMX': os.environ.get('TCC_CK_XMX', '3g'),
    'JVM_WORKERS': int(os.environ.get('TCC_JVM_WORKERS', max(2, _CPUS // 2))),   # MethodsBatch / CDBatch JVMs
    'JVM_XMX': os.environ.get('TCC_JVM_XMX', '1g'),
    'PY_WORKERS': int(os.environ.get('TCC_PY_WORKERS', max(2, _CPUS - 2))),      # Python processes (s05)
    'MEM_RESERVE_GB': float(os.environ.get('TCC_MEM_RESERVE_GB', 2.5)),         # RAM kept free for the OS
}


def slug(feature):
    return feature.replace(' ', '_')


class Paths:
    def __init__(self, feature):
        if feature not in FEATURES:
            raise SystemExit(f'unknown feature {feature!r}; options: {", ".join(FEATURES)}')
        self.feature = feature
        self.cfg = FEATURES[feature]
        self.repo = REPOS / self.cfg['repo']
        self.repository = self.cfg['repo']
        # TCC_RUN_SUFFIX: isolated runs (ex.: regression against the pilot), never mixed with the real outputs
        self.base = BASE / (slug(feature) + os.environ.get('TCC_RUN_SUFFIX', ''))
        self.data = self.base / 'data'
        self.work = self.base / 'work'
        self.snapshots = self.work / 'snapshots'
        for p in (self.data, self.work):
            p.mkdir(parents=True, exist_ok=True)

    def is_production_java(self, path):
        return is_production_java(path.replace('\\', '/'), self.feature)

    def snapshot_dir(self, idx, commit):
        return self.snapshots / f'{int(idx):02d}_{commit[:8]}'


def parse_args(description=''):
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument('--feature', required=True)
    return Paths(ap.parse_args().feature)
