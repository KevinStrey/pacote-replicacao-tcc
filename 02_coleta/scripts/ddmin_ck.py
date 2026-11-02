"""Delta debugging (ddmin, Zeller & Hildebrandt 2002) of a CK 0.7.1 crash: finds a minimal set of source files of
one directory of a snapshot that still makes CK crash. Same CK arguments as s02 (true 0 false).
Usage: python ddmin_ck.py --feature JDT --release 53 --subdir org.eclipse.jdt.core.compiler.batch"""
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from config import CK_JAR, JAVA, Paths

ap = argparse.ArgumentParser()
ap.add_argument('--feature', required=True)
ap.add_argument('--release', type=int, required=True)
ap.add_argument('--subdir', default='')
a = ap.parse_args()
P = Paths(a.feature)
src = next(P.snapshots.glob(f'{a.release:02d}_*')) / a.subdir
files = sorted(p.relative_to(src) for p in src.rglob('*.java') if p.is_file())
tmp = Path(tempfile.mkdtemp(prefix='ckdd_', dir=P.work))
runs = [0]


def crashes(subset):
    runs[0] += 1
    d = tmp / 'src'
    shutil.rmtree(d, ignore_errors=True)
    for rel in subset:
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, d / rel)
    out = tmp / 'out'
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir()
    p = subprocess.run([JAVA, '-Xmx3g', '-jar', str(CK_JAR), str(d), 'true', '0', 'false', str(out) + '/'],
                       capture_output=True, text=True, cwd=out)
    return p.returncode != 0 or not (out / 'method.csv').exists()


assert crashes(files), 'the directory alone does not crash'
cur, n = files, 2
while len(cur) >= 2:
    size = len(cur) // n
    chunks = [cur[i * size:(i + 1) * size] if i < n - 1 else cur[i * size:] for i in range(n)]
    reduced = False
    for c in chunks:                                   # try a single chunk
        if crashes(c):
            cur, n, reduced = c, 2, True
            break
    if not reduced:
        for i in range(n):                             # try the complement of each chunk
            comp = [f for j, c in enumerate(chunks) if j != i for f in c]
            if crashes(comp):
                cur, n, reduced = comp, max(n - 1, 2), True
                break
    if not reduced:
        if n >= len(cur):
            break
        n = min(len(cur), 2 * n)
    print(f'runs={runs[0]} current set={len(cur)} files', flush=True)
print('MINIMAL CRASHING SET:')
for f in cur:
    print('  ', f)
shutil.rmtree(tmp, ignore_errors=True)
