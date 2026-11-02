"""Step 3 - Understand (SciTools) metrics per snapshot.

Same commands, metrics and settings as the pilot (und_lib.commands). Differences: the commands of one snapshot run
in a single und process (und_lib mode 'batch', equivalence verified, RECURSOS.md) and RESOURCES['UND_WORKERS']
snapshots run in parallel. Output: data/understand/<release>_<commit>.csv (+ .log). Resumable.
"""
import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

import und_lib
from config import RESOURCES, parse_args

P = parse_args(__doc__)
OUT = P.data / 'understand'
DBS = P.work / 'und_dbs'
MODE = os.environ.get('TCC_UND_MODE', 'batch')


def run(r):
    release, commit = int(r['release']), r['commit']
    tag = f'{release:02d}_{commit}'
    out_csv = OUT / f'{tag}.csv'
    if out_csv.exists():
        return tag, 'skip'
    log = und_lib.run(P.snapshot_dir(release, commit), DBS / f'{tag}.und', out_csv, MODE)
    (OUT / f'{tag}.log').write_text(log, encoding='utf-8')
    return tag, 'ok' if out_csv.exists() else 'ERROR'


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    DBS.mkdir(parents=True, exist_ok=True)
    tl = pd.read_csv(P.data / 'timeline.csv')
    with ThreadPoolExecutor(RESOURCES['UND_WORKERS']) as ex:
        res = list(ex.map(run, [r for _, r in tl.iterrows()]))
    for tag, st in res:
        print(tag, st, flush=True)
    bad = [t for t, s in res if s == 'ERROR']
    if bad:
        raise SystemExit(f'Understand failed: {bad}')
