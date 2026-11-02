"""Understand (und) runner shared by s03 and the validation scripts.

Same sequence and the same 53 metrics/settings as the pilot (4-Coleta_egit/scripts/s03_understand.py, which
reproduces cpmp/2.understand/understand.py): create -> add . -> analyze -> settings -> metrics.
mode='pilot': one und process per command (10 processes per snapshot, as in the pilot).
mode='batch': the same commands, in the same order, in ONE und process (und process <file>), which avoids
reloading the database 10 times. Equivalence verified on BIRT/EGit snapshots (RECURSOS.md).
"""
import shutil
import subprocess
from pathlib import Path

UND = r'C:\Program Files\SciTools\bin\pc-win64\und.exe'
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


def commands(db, out_csv):
    db, out_csv = str(db), str(out_csv)
    return [['create', '-db', db, '-languages', 'java'],
            ['-db', db, 'add', '.'],
            ['analyze', '-db', db],
            ['settings', '-MetricMetrics', *METRICS, db],
            ['settings', '-MetricFileNameDisplayMode', 'RelativePath', db],
            ['settings', '-MetricDeclaredInFileDisplayMode', 'RelativePath', db],
            ['settings', '-MetricShowDeclaredInFile', 'on', db],
            ['settings', '-MetricShowFunctionParameterTypes', 'on', db],
            ['settings', '-MetricOutputFile', out_csv, db],
            ['metrics', db]]


def _summary(txt):
    """Log kept on disk: head, every line that looks like a problem, tail (the full log is ~1 MB per snapshot)."""
    import re
    probs = [l for l in txt.splitlines()
             if re.search(r'(?i)error|fail|licen|unable|cannot|denied|abort|out of memory', l) and 'src.zip' not in l]
    return txt[:2000] + '\n...\n[problem lines]\n' + '\n'.join(probs[:200]) + '\n...\n' + txt[-3000:]


def run(src, db, out_csv, mode='batch', retries=2):
    """Runs Understand on the snapshot directory src; returns the log text.
    The CSV is written to <out_csv>.tmp and renamed only when und finished, so an interrupted run never leaves a
    partial CSV that a resumed collection would take as done. Transient failures (seen once with 8+ simultaneous
    und processes) are retried."""
    db, out_csv = Path(db), Path(out_csv)
    tmp_csv = out_csv.with_name(out_csv.name + '.tmp')
    logs = []
    for attempt in range(1 + retries):
        if db.exists():
            shutil.rmtree(db)
        tmp_csv.unlink(missing_ok=True)
        rc = 0
        if mode == 'pilot':
            for args in commands(db, tmp_csv):
                p = subprocess.run([UND, *args], capture_output=True, text=True, cwd=src)
                rc = rc or p.returncode
                logs.append(' '.join(args[:3]) + '\n' + _summary(p.stdout + p.stderr))
        else:
            # und process <file>: one command per line, run in order in a single und process
            cmd_file = db.with_suffix('.cmds.txt')
            lines = [' '.join(f'"{a}"' if (' ' in a or '\\' in a or ':' in a) else a for a in args)
                     for args in commands(db, tmp_csv)]
            cmd_file.write_text('\n'.join(lines) + '\n', encoding='utf-8')
            p = subprocess.run([UND, 'process', str(cmd_file)], capture_output=True, text=True, cwd=src)
            rc = p.returncode
            logs.append(f'[attempt {attempt + 1}] rc={rc}\n' + _summary(p.stdout + p.stderr))
            cmd_file.unlink(missing_ok=True)
        shutil.rmtree(db, ignore_errors=True)
        if rc == 0 and tmp_csv.exists() and tmp_csv.stat().st_size > 0:
            tmp_csv.replace(out_csv)
            break
    return '\n'.join(logs)
