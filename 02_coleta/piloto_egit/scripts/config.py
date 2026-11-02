"""Shared configuration for the EGit pilot run of the cpmp pipeline."""
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]           # 4-Coleta_egit
ROOT = BASE.parent                                   # TCC-LPS-Prediction
REPO = ROOT / '1-Repositorios' / 'egit'
MAPPING_DIR = ROOT / '3-Mapeamento_features_simrel' / 'simrel_mapper' / 'output'
CPMP = ROOT / 'cpmp'

DATA = BASE / 'data'
RESULTS = BASE / 'results'
WORK = BASE / 'work'
SNAPSHOTS = WORK / 'snapshots'

PROJECT = 'egit'
FEATURE_KEY = 'EGit'   # key in the simrel mapping

JAVA = 'java'
UND = r'C:\Program Files\SciTools\bin\pc-win64\und.exe'
CK_JAR = CPMP / '1.ck' / 'ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar'
JME_JAR = CPMP / '4.evometrics' / 'JMethodsExtractor-0.0.1-SNAPSHOT-jar-with-dependencies.jar'
CD_JAR = CPMP / '5.cd' / 'ChangeDistillerReader-methods-0.0.1-SNAPSHOT-jar-with-dependencies.jar'

# Decisions made by the author (see AUDITORIA.md)
EXCLUDED_RELEASES = {
    'Mars.1': 'commit 4cc706a2 on branch stable-4.0, not an ancestor of the next snapshot',
    'Oxygen.2_respin': 'commit 03cda165 (v4.9.2, maintenance) is not a descendant of Oxygen.2 (eb33e504)',
}

# Production code only: exclude test bundles
_TEST_BUNDLE = re.compile(r'^[^/]+\.(test|tests|junit)/')


def is_production_java(path: str) -> bool:
    path = path.replace('\\', '/')
    return path.endswith('.java') and not _TEST_BUNDLE.match(path)
