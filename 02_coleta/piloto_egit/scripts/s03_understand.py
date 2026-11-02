"""Step 3 - Understand (SciTools) metrics per snapshot.

Same sequence and the same 55 metrics as cpmp/2.understand/understand.py:
create -> add -> analyze -> settings (metrics, RelativePath, ShowDeclaredInFile,
ShowFunctionParameterTypes) -> metrics.
Output: data/understand/<release>_<commit>.csv
"""
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from config import DATA, UND, WORK
from s01_snapshots import snapshot_dir

OUT = DATA / 'understand'
DBS = WORK / 'und_dbs'

METRICS = ['AvgCyclomatic', 'AvgCyclomaticModified', 'AvgCyclomaticStrict',
           'AvgEssential', 'AvgLine', 'AvgLineBlank', 'AvgLineCode', 'AvgLineComment', 'CountClassBase',
           'CountClassCoupled', 'CountClassDerived', 'CountDeclClass', 'CountDeclClassMethod',
           'CountDeclClassVariable', 'CountDeclFile', 'CountDeclFunction', 'CountDeclInstanceMethod',
           'CountDeclInstanceVariable', 'CountDeclMethod', 'CountDeclMethodAll', 'CountDeclMethodDefault',
           'CountDeclMethodPrivate', 'CountDeclMethodProtected', 'CountDeclMethodPublic', 'CountInput',
           'CountLine', 'CountLineBlank', 'CountLineCode', 'CountLineCodeDecl', 'CountLineCodeExe',
           'CountLineComment', 'CountOutput', 'CountPath', 'CountSemicolon', 'CountStmt', 'CountStmtDecl',
           'CountStmtExe', 'Cyclomatic', 'CyclomaticModified', 'CyclomaticStrict', 'Essential',
           'MaxCyclomatic', 'MaxCyclomaticModified', 'MaxCyclomaticStrict', 'MaxEssential',
           'MaxInheritanceTree', 'MaxNesting', 'PercentLackOfCohesion', 'RatioCommentToCode', 'SumCyclomatic',
           'SumCyclomaticModified', 'SumCyclomaticStrict', 'SumEssential']


def und(*args, cwd=None):
    return subprocess.run([UND, *args], capture_output=True, text=True, cwd=cwd)


def run(r):
    release, commit = int(r['release']), r['commit']
    tag = f'{release:02d}_{commit}'
    out_csv = OUT / f'{tag}.csv'
    if out_csv.exists():
        return tag, 'skip'
    db = DBS / f'{tag}.und'
    if db.exists():
        shutil.rmtree(db)
    src = snapshot_dir(release, commit)
    logs = []
    for args in (['create', '-db', str(db), '-languages', 'java'],
                 ['-db', str(db), 'add', '.'],
                 ['analyze', '-db', str(db)],
                 ['settings', '-MetricMetrics', *METRICS, str(db)],
                 ['settings', '-MetricFileNameDisplayMode', 'RelativePath', str(db)],
                 ['settings', '-MetricDeclaredInFileDisplayMode', 'RelativePath', str(db)],
                 ['settings', '-MetricShowDeclaredInFile', 'on', str(db)],
                 ['settings', '-MetricShowFunctionParameterTypes', 'on', str(db)],
                 ['settings', '-MetricOutputFile', str(out_csv), str(db)],
                 ['metrics', str(db)]):
        p = und(*args, cwd=src)
        logs.append(' '.join(args[:3]) + '\n' + p.stdout[-3000:] + p.stderr[-3000:])
    (OUT / f'{tag}.log').write_text('\n'.join(logs), encoding='utf-8')
    shutil.rmtree(db, ignore_errors=True)
    return tag, 'ok' if out_csv.exists() else 'ERROR'


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    DBS.mkdir(parents=True, exist_ok=True)
    tl = pd.read_csv(DATA / 'timeline.csv')
    with ThreadPoolExecutor(4) as ex:
        for tag, st in ex.map(run, [r for _, r in tl.iterrows()]):
            print(tag, st, flush=True)
