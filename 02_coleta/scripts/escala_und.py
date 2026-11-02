"""Scaling test: N simultaneous Understand runs (batch mode) on different EGit snapshots; reports wall time,
throughput and peak RAM / CPU of the machine. Used to size UND workers (RECURSOS.md)."""
import sys, time, tempfile, threading, psutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import und_lib
snaps = sorted((Path(__file__).resolve().parents[1] / 'EGit' / 'work' / 'snapshots').iterdir())
tmp = Path(tempfile.mkdtemp(prefix='und_scale_'))
for n in map(int, sys.argv[1:]):
    sel = snaps[-n:]; peak = [0, 0]; stop = [False]
    def mon():
        while not stop[0]:
            peak[0] = max(peak[0], psutil.virtual_memory().used); peak[1] = max(peak[1], psutil.cpu_percent(0.5))
    th = threading.Thread(target=mon); th.start(); t = time.time()
    with ThreadPoolExecutor(n) as ex:
        list(ex.map(lambda s: und_lib.run(s, tmp / f'{n}_{s.name}.und', tmp / f'{n}_{s.name}.csv'), sel))
    stop[0] = True; th.join(); dt = time.time() - t
    print(f'{n} simultaneos: {dt:.0f}s total | {dt / n:.1f}s por snapshot | RAM usada pico {peak[0]/2**30:.1f}GB | CPU pico {peak[1]:.0f}%', flush=True)
