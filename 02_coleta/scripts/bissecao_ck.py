"""Finds the source files that make CK 0.7.1 crash on a snapshot (bisection over the file list).
Each candidate subset is copied (keeping relative paths) to a temporary directory and CK is run with the same
arguments as s02 (true 0 false). Prints the minimal crashing files found.
Usage: python bissecao_ck.py --feature JDT --release 53"""
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from config import CK_JAR, JAVA, Paths

ap = argparse.ArgumentParser()
ap.add_argument('--feature', required=True)
ap.add_argument('--release', type=int, required=True)
a = ap.parse_args()
P = Paths(a.feature)
src = next(P.snapshots.glob(f'{a.release:02d}_*'))
files = sorted(p.relative_to(src) for p in src.rglob('*.java') if p.is_file())
tmp_root = Path(tempfile.mkdtemp(prefix='ckbis_', dir=P.work))


def crashes(subset):
    d = tmp_root / 'src'
    shutil.rmtree(d, ignore_errors=True)
    for rel in subset:
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, d / rel)
    out = tmp_root / 'out'
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir()
    p = subprocess.run([JAVA, '-Xmx3g', '-jar', str(CK_JAR), str(d), 'true', '0', 'false', str(out) + '/'],
                       capture_output=True, text=True, cwd=out)
    return p.returncode != 0 or not (out / 'method.csv').exists()


print(f'{src.name}: {len(files)} files; full snapshot crashes: {crashes(files)}', flush=True)
culprits, pending = [], [files]
while pending:
    chunk = pending.pop()
    if not crashes(chunk):
        continue
    if len(chunk) == 1:
        culprits.append(chunk[0])
        print('CRASH FILE:', chunk[0], flush=True)
        continue
    half = len(chunk) // 2
    a_, b_ = chunk[:half], chunk[half:]
    ca, cb = crashes(a_), crashes(b_)
    if ca:
        pending.append(a_)
    if cb:
        pending.append(b_)
    if not ca and not cb:   # crash needs files from both halves: report the chunk
        print(f'crash depends on a combination inside a chunk of {len(chunk)} files: {[str(x) for x in chunk[:10]]}')
remaining = [f for f in files if f not in culprits]
print('without the culprit files the snapshot crashes:', crashes(remaining))
shutil.rmtree(tmp_root, ignore_errors=True)
