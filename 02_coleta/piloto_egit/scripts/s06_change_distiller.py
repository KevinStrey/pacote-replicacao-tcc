"""Step 6 - ChangeDistiller between consecutive releases (r -> r+1), per method.

Same semantics as cpmp/5.cd/methods_change_distiller.py:
 - only methods present in both snapshots (same key);
 - each method is wrapped in 'public class Fake_function_qwerty { ... }';
 - original jar call: (method_r, method_r+1, csv, project, commit_r, commit_r+1, ...),
   so CURRENT_COMMIT = commit_r and the row describes the change that happens
   AFTER release r (label for release r).
Difference: methods with identical text in r and r+1 get TOTAL_CHANGES = 0 without
calling ChangeDistiller (that is the result the tool returns for identical input);
the calls go in batch (CDBatch.java) instead of one JVM per method.
Output: data/change_distiller.csv
"""
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from config import CD_JAR, DATA, JAVA, PROJECT, WORK
from methods_lib import load_blob_methods

M = DATA / 'methods'
CDW = WORK / 'cd'
JAVA_DIR = __import__('pathlib').Path(__file__).resolve().parent / 'java'
CLASS_SIG = 'public class Fake_function_qwerty {'

COLS = ["PROJECT_NAME", "CURRENT_COMMIT", "PREVIOUS_COMMIT", "CLASS_CURRENTCOMMIT", "CLASS_PREVIOUSCOMMIT",
        "CLASS_CURRENTNAME", "CLASS_PREVIOUSNAME",
        "STATEMENT_DELETE", "STATEMENT_INSERT", "STATEMENT_ORDERING_CHANGE",
        "STATEMENT_PARENT_CHANGE", "STATEMENT_UPDATE", "TOTAL_STATEMENTLEVELCHANGES",
        "PARENT_CLASS_CHANGE", "PARENT_CLASS_DELETE", "PARENT_CLASS_INSERT", "CLASS_RENAMING",
        "TOTAL_CLASSDECLARATIONCHANGES",
        "RETURN_TYPE_CHANGE", "RETURN_TYPE_DELETE", "RETURN_TYPE_INSERT", "METHOD_RENAMING",
        "PARAMETER_DELETE", "PARAMETER_INSERT", "PARAMETER_ORDERING_CHANGE", "PARAMETER_RENAMING",
        "PARAMETER_TYPE_CHANGE", "TOTAL_METHODDECLARATIONSCHANGES",
        "ATTRIBUTE_RENAMING", "ATTRIBUTE_TYPE_CHANGE", "TOTAL_ATTRIBUTEDECLARATIONCHANGES",
        "ADDING_ATTRIBUTE_MODIFIABILITY", "REMOVING_ATTRIBUTE_MODIFIABILITY",
        "REMOVING_CLASS_DERIVABILITY", "REMOVING_METHOD_OVERRIDABILITY",
        "ADDING_CLASS_DERIVABILITY", "ADDING_CLASS_DERIVABILITY_2", "ADDING_METHOD_OVERRIDABILITY",
        "TOTAL_DECLARATIONPARTCHANGES", "TOTAL_CHANGES"]
NUM_COLS = COLS[7:]


def wrap(text):
    return text if text.startswith(CLASS_SIG) else CLASS_SIG + '\n' + text + '\n}'


def snapshot_methods(sf, blobs, rel):
    present = {}
    for _, f in sf[sf['release'] == rel].iterrows():
        for k, text in blobs[f['blob']].items():
            present[k] = None if k in present else text
    return {k: v for k, v in present.items() if v is not None}


if __name__ == '__main__':
    tl = pd.read_csv(DATA / 'timeline.csv')
    sf = pd.read_csv(M / 'snapshot_files.csv')
    blobs, _ = load_blob_methods()
    if CDW.exists():
        shutil.rmtree(CDW)
    CDW.mkdir(parents=True)

    zero_rows, jobs = [], []
    snaps = {int(r): snapshot_methods(sf, blobs, int(r)) for r in tl['release']}
    for i in range(len(tl) - 1):
        r, c_r, c_n = int(tl['release'][i]), tl['commit'][i], tl['commit'][i + 1]
        a, b = snaps[r], snaps[r + 1]
        common = sorted(set(a) & set(b))
        d = CDW / f'{r:02d}'
        d.mkdir()
        n_changed = 0
        for j, k in enumerate(common):
            if a[k] == b[k]:
                zero_rows.append([PROJECT, c_r, c_n, '', '', k, k] + [0] * len(NUM_COLS))
                continue
            fa, fb = d / f'{j}_A.java', d / f'{j}_B.java'
            fa.write_text(wrap(a[k]), encoding='utf-8')
            fb.write_text(wrap(b[k]), encoding='utf-8')
            jobs.append([str(fa), str(fb), PROJECT, c_r, c_n, k, k])
            n_changed += 1
        print(f'{r}->{r + 1}: common={len(common)} changed={n_changed}', flush=True)

    n_jobs = 4
    cp = f'{CD_JAR};{JAVA_DIR}'

    def run(i):
        csv = CDW / f'cd_{i}.csv'
        man = CDW / f'manifest_{i}.tsv'
        man.write_text('\n'.join('\t'.join([j[0], j[1], str(csv), *j[2:]]) for j in jobs[i::n_jobs]),
                       encoding='utf-8')
        p = subprocess.run([JAVA, '--add-opens', 'java.base/java.lang=ALL-UNNAMED', '-cp', cp, 'CDBatch', str(man)],
                           capture_output=True, text=True)
        (CDW / f'cd_{i}.log').write_text(p.stdout[-20000:] + '\n' + p.stderr[-20000:], encoding='utf-8')
        return csv

    with ThreadPoolExecutor(n_jobs) as ex:
        parts = [pd.read_csv(p, header=None, skiprows=1, dtype=str) for p in ex.map(run, range(n_jobs))
                 if p.exists()]
    cd = pd.concat(parts, ignore_index=True)
    cd.columns = COLS
    cd = pd.concat([cd, pd.DataFrame(zero_rows, columns=COLS)], ignore_index=True)
    cd[NUM_COLS] = cd[NUM_COLS].astype(int)
    cd['method_name'] = cd['CLASS_CURRENTNAME']
    print('ChangeDistiller calls:', len(jobs), '| returned rows:', len(parts and pd.concat(parts)),
          '| zero rows (identical text):', len(zero_rows))
    cd.to_csv(DATA / 'change_distiller.csv', index=False)
