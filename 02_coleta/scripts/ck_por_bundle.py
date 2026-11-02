"""Runs CK 0.7.1 on each top-level bundle of a snapshot separately, to find which bundle makes it crash."""
import shutil, subprocess, sys, tempfile
from pathlib import Path
from config import CK_JAR, JAVA, Paths
P = Paths(sys.argv[1]); src = next(P.snapshots.glob(f'{int(sys.argv[2]):02d}_*'))
tmp = Path(tempfile.mkdtemp(prefix='ckb_', dir=P.work))
for b in sorted(d for d in src.iterdir() if d.is_dir()):
    n = sum(1 for _ in b.rglob('*.java'))
    out = tmp / b.name; out.mkdir()
    p = subprocess.run([JAVA, '-Xmx3g', '-jar', str(CK_JAR), str(b), 'true', '0', 'false', str(out) + '/'],
                       capture_output=True, text=True, cwd=out)
    ok = p.returncode == 0 and (out / 'method.csv').exists()
    print(f'{b.name}: {n} arquivos -> {"OK" if ok else "FALHA"}', flush=True)
shutil.rmtree(tmp, ignore_errors=True)
