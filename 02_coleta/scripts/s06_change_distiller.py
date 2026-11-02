"""Step 6 - ChangeDistiller between consecutive snapshots (r -> next r), per method.

Same semantics as the pilot (4-Coleta_egit/scripts/s06_change_distiller.py, which follows
cpmp/5.cd/methods_change_distiller.py): only methods present in both snapshots (same key); each method wrapped in
'public class Fake_function_qwerty { ... }'; original jar call (CDBatch -> DistillerReader.main) with
CURRENT_COMMIT = commit_r, so the row describes the change AFTER release r (label of release r); methods with
identical text get TOTAL_CHANGES = 0 without calling the tool.
Differences: texts come from the sqlite store; RESOURCES['JVM_WORKERS'] JVMs in parallel.
Output: data/change_distiller.parquet
"""
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from config import CD_JAR, JAVA, JAVA_DIR, RESOURCES, parse_args
from methods_lib import TextStore, load_index, snapshot_methods

P = parse_args(__doc__)
M = P.data / 'methods'
CDW = P.work / 'cd'
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


if __name__ == '__main__':
    tl = pd.read_csv(P.data / 'timeline.csv')
    sf = pd.read_csv(M / 'snapshot_files.csv')
    index = load_index(M / 'blob_index.pkl')
    store = TextStore(M / 'method_texts.sqlite')
    if CDW.exists():
        shutil.rmtree(CDW)
    CDW.mkdir(parents=True)
    sf_by_rel = {rel: list(zip(g['path'], g['blob'])) for rel, g in sf.groupby('release')}
    rels, commits = [int(x) for x in tl['release']], list(tl['commit'])
    zero_rows, jobs = [], []
    snaps = {r: snapshot_methods(sf_by_rel.get(r, []), index) for r in rels}
    for i in range(len(rels) - 1):
        r, rn, c_r, c_n = rels[i], rels[i + 1], commits[i], commits[i + 1]
        a, b = snaps[r], snaps[rn]
        common = sorted(set(a) & set(b))
        d = CDW / f'{r:02d}'
        d.mkdir()
        n_changed = 0
        for j, k in enumerate(common):
            if a[k][0] == b[k][0]:
                zero_rows.append([P.repository, c_r, c_n, '', '', k, k] + [0] * len(NUM_COLS))
                continue
            fa, fb = d / f'{j}_A.java', d / f'{j}_B.java'
            fa.write_text(wrap(store.get(a[k][0])), encoding='utf-8')
            fb.write_text(wrap(store.get(b[k][0])), encoding='utf-8')
            jobs.append([str(fa), str(fb), P.repository, c_r, c_n, k, k])
            n_changed += 1
        print(f'{r}->{rn}: common={len(common)} changed={n_changed}', flush=True)

    n_jobs = max(1, min(RESOURCES['JVM_WORKERS'], len(jobs) // 200 + 1))
    cp = f'{CD_JAR};{JAVA_DIR}'

    def run(i):
        csv = CDW / f'cd_{i}.csv'
        man = CDW / f'manifest_{i}.tsv'
        man.write_text('\n'.join('\t'.join([j[0], j[1], str(csv), *j[2:]]) for j in jobs[i::n_jobs]),
                       encoding='utf-8')
        p = subprocess.run([JAVA, f'-Xmx{RESOURCES["JVM_XMX"]}', '--add-opens', 'java.base/java.lang=ALL-UNNAMED',
                            '-cp', cp, 'CDBatch', str(man)], capture_output=True, text=True)
        (CDW / f'cd_{i}.log').write_text(p.stdout[-20000:] + '\n' + p.stderr[-20000:], encoding='utf-8')
        return csv

    parts = []
    if jobs:
        with ThreadPoolExecutor(n_jobs) as ex:
            parts = [pd.read_csv(p, header=None, skiprows=1, dtype=str) for p in ex.map(run, range(n_jobs))
                     if p.exists()]
    n_err = sum(open(CDW / f'cd_{i}.log', encoding='utf-8').read().count('CDERROR') for i in range(n_jobs)
                if (CDW / f'cd_{i}.log').exists())
    cd = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=COLS)
    cd.columns = COLS
    cd = pd.concat([cd, pd.DataFrame(zero_rows, columns=COLS)], ignore_index=True)
    cd[NUM_COLS] = cd[NUM_COLS].astype(int)
    cd['method_name'] = cd['CLASS_CURRENTNAME']
    print('ChangeDistiller calls:', len(jobs), '| returned rows:', sum(len(p) for p in parts),
          '| zero rows (identical text):', len(zero_rows), '| CDERROR:', n_err)
    cd.to_parquet(P.data / 'change_distiller.parquet', index=False)
