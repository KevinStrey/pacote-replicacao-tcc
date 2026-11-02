"""Step 2 - CK metrics (method and class) per snapshot.

Same call as the pilot / cpmp/1.ck/ck.sh: java -jar ck-0.7.1 <dir> true 0 false <out>/
Differences: explicit heap (-Xmx, RESOURCES['CK_XMX']), RESOURCES['CK_WORKERS'] snapshots in parallel and, when the
feature declares `ck_exclude` (M24), CK gets a hard-linked copy of the snapshot without those files (the excluded
paths are written to data/ck/<tag>.excluded.txt).
Output: data/ck/<release>_<commit>_method.csv / _class.csv (+ .log). Resumable (skips finished snapshots).
"""
import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from config import CK_JAR, JAVA, RESOURCES, parse_args


def ck_input(P, snap, tag):
    """Directory given to CK: the snapshot, or a hard-linked copy without the `ck_exclude` files of the feature."""
    pats = [re.compile(p) for p in P.cfg.get('ck_exclude', [])]
    if not pats:
        return snap
    files = [f for f in snap.rglob('*.java') if f.is_file()]
    rel = {f: f.relative_to(snap).as_posix() for f in files}
    excl = [f for f in files if any(p.match(rel[f]) for p in pats)]
    if not excl:
        return snap
    d = P.work / 'ck_input' / tag
    shutil.rmtree(d, ignore_errors=True)
    for f in files:
        if f in excl:
            continue
        t = d / rel[f]
        t.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(f, t)
        except OSError:
            shutil.copy2(f, t)
    (P.data / 'ck').mkdir(parents=True, exist_ok=True)
    (P.data / 'ck' / f'{tag}.excluded.txt').write_text('\n'.join(rel[f] for f in excl), encoding='utf-8')
    return d


def run(P, r):
    out = P.data / 'ck'
    release, commit = int(r['release']), r['commit']
    tag = f'{release:02d}_{commit}'
    method_csv = out / f'{tag}_method.csv'
    if method_csv.exists():
        return tag, 'skip'
    tmp = P.work / 'ck_tmp' / tag
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    src = ck_input(P, P.snapshot_dir(release, commit), tag)
    p = subprocess.run([JAVA, f'-Xmx{RESOURCES["CK_XMX"]}', '-jar', str(CK_JAR), str(src), 'true', '0', 'false',
                        str(tmp) + '/'], capture_output=True, text=True, cwd=tmp)
    (out / f'{tag}.log').write_text(p.stdout[-5000:] + p.stderr[-5000:], encoding='utf-8')
    if p.returncode != 0 or not (tmp / 'method.csv').exists():
        return tag, f'ERROR rc={p.returncode}'
    shutil.move(tmp / 'class.csv', out / f'{tag}_class.csv')
    shutil.move(tmp / 'method.csv', method_csv)
    shutil.rmtree(tmp, ignore_errors=True)
    if src != P.snapshot_dir(release, commit):
        shutil.rmtree(src, ignore_errors=True)
    return tag, 'ok'


if __name__ == '__main__':
    P = parse_args(__doc__)
    (P.data / 'ck').mkdir(parents=True, exist_ok=True)
    tl = pd.read_csv(P.data / 'timeline.csv')
    with ThreadPoolExecutor(RESOURCES['CK_WORKERS']) as ex:
        res = list(ex.map(lambda r: run(P, r), [r for _, r in tl.iterrows()]))
    for tag, st in res:
        print(tag, st, flush=True)
    bad = [t for t, s in res if s.startswith('ERROR')]
    if bad:
        raise SystemExit(f'CK failed: {bad}')
