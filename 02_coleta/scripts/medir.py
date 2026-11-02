"""Runs a command and reports wall time and peak RAM (sum of the RSS of the process tree, sampled every 0.25 s).
Used to size the parallelism of the collection (RECURSOS.md).
Usage: python medir.py <label> -- <command ...>"""
import subprocess
import sys
import time

import psutil

label = sys.argv[1]
cmd = sys.argv[sys.argv.index('--') + 1:]
t0 = time.time()
p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
pp = psutil.Process(p.pid)
peak = 0
while p.poll() is None:
    try:
        rss = pp.memory_info().rss + sum(c.memory_info().rss for c in pp.children(recursive=True))
        peak = max(peak, rss)
    except psutil.Error:
        pass
    time.sleep(0.25)
print(f'{label}: rc={p.returncode} tempo={time.time() - t0:.1f}s pico_RAM={peak / 2**30:.2f}GB', flush=True)
