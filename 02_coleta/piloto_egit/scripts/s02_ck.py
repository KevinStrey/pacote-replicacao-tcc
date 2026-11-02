"""Step 2 - CK metrics (method and class) per snapshot.

Equivalent to cpmp/1.ck/ck.sh: java -jar ck-0.7.1 <dir> true 0 false <out>
Output: data/ck/<release>_<commit>_method.csv / _class.csv
Resumable: skips snapshots that were already collected.
"""
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from config import CK_JAR, DATA, JAVA
from s01_snapshots import snapshot_dir

OUT = DATA / 'ck'


def run(r):
    release, commit = int(r['release']), r['commit']
    tag = f'{release:02d}_{commit}'
    method_csv = OUT / f'{tag}_method.csv'
    if method_csv.exists():
        return tag, 'skip'
    tmp = OUT / f'tmp_{tag}'
    tmp.mkdir(parents=True, exist_ok=True)
    src = snapshot_dir(release, commit)
    p = subprocess.run([JAVA, '-jar', str(CK_JAR), str(src), 'true', '0', 'false', str(tmp) + '/'],
                       capture_output=True, text=True, cwd=tmp)
    (OUT / f'{tag}.log').write_text(p.stdout[-5000:] + p.stderr[-5000:], encoding='utf-8')
    if p.returncode != 0 or not (tmp / 'method.csv').exists():
        return tag, f'ERROR rc={p.returncode}'
    shutil.move(tmp / 'class.csv', OUT / f'{tag}_class.csv')
    shutil.move(tmp / 'method.csv', method_csv)
    shutil.rmtree(tmp, ignore_errors=True)
    return tag, 'ok'


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    tl = pd.read_csv(DATA / 'timeline.csv')
    with ThreadPoolExecutor(4) as ex:
        for tag, st in ex.map(run, [r for _, r in tl.iterrows()]):
            print(tag, st, flush=True)
