"""Runs CK on a full snapshot minus the given relative files; reports success and method rows."""
import shutil, subprocess, sys, tempfile
from pathlib import Path
from config import CK_JAR, JAVA, Paths
P = Paths(sys.argv[1]); src = next(P.snapshots.glob(f'{int(sys.argv[2]):02d}_*')); excl = {Path(x) for x in sys.argv[3:]}
tmp = Path(tempfile.mkdtemp(prefix='ckx_', dir=P.work)); d = tmp / 'src'
for p in src.rglob('*.java'):
    rel = p.relative_to(src)
    if p.is_file() and rel not in excl:
        (d / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, d / rel)
out = tmp / 'out'; out.mkdir()
r = subprocess.run([JAVA, '-Xmx3g', '-jar', str(CK_JAR), str(d), 'true', '0', 'false', str(out) + '/'], capture_output=True, text=True, cwd=out)
ok = r.returncode == 0 and (out / 'method.csv').exists()
print('excluidos:', [str(x) for x in excl], '->', 'OK' if ok else 'FALHA', '| linhas method.csv:', sum(1 for _ in open(out / 'method.csv', encoding='utf-8', errors='replace')) - 1 if ok else '-')
shutil.rmtree(tmp, ignore_errors=True)
