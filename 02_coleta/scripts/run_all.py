"""Orchestrator of the collection of several features on one machine (decisions M1–M18; sizing in RECURSOS.md).

Phase A (per feature, fast):    s00 timeline, s01 snapshots.
Phase B (global queue):         every CK and Understand snapshot job of every selected feature, scheduled under a
                                RAM budget (estimated peak per job, measured on BIRT: und ~0.40 GB/1000 files,
                                CK ~0.19 GB/1000 files) and a CPU cap; largest jobs first (no long tail).
Phase C (per feature, in parallel with B): s04 methods, s05 evometrics, s06 ChangeDistiller (they do not depend
                                on CK/Understand), one feature at a time, with a fixed RAM reservation.
Phase D (per feature):          s07 join, as soon as the feature's B and C jobs are done.
Each step is resumable (finished outputs are skipped), so the orchestrator can be restarted after a failure.
Logs: 5-Coleta_features/logs/run_all_<timestamp>.log and <feature>/data/*.log
Usage: python run_all.py [--features EGit CVS ...] [--budget-gb 12] [--max-procs 12]
"""
import argparse
import datetime as dt
import heapq
import subprocess
import sys
import threading
import time
from pathlib import Path

import pandas as pd
import psutil

import und_lib
from config import BASE, CK_JAR, FEATURES, JAVA, MAPPING_CSV, RESOURCES, Paths

PY = sys.executable
SCRIPTS = Path(__file__).resolve().parent
LOGS = BASE / 'logs'
LOGS.mkdir(exist_ok=True)
LOG = LOGS / f'run_all_{dt.datetime.now():%Y%m%d_%H%M%S}.log'
_lock = threading.Lock()


def log(*a):
    s = f'{dt.datetime.now():%H:%M:%S} ' + ' '.join(str(x) for x in a)
    with _lock:
        print(s, flush=True)
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(s + '\n')


def step(feature, script):
    t = time.time()
    p = subprocess.run([PY, str(SCRIPTS / f'{script}.py'), '--feature', feature], capture_output=True, text=True,
                       cwd=SCRIPTS)
    out = Paths(feature).data / f'{script}.log'
    out.write_text(p.stdout + '\n' + p.stderr, encoding='utf-8')
    log(f'[{feature}] {script} rc={p.returncode} {time.time() - t:.0f}s')
    if p.returncode:
        raise RuntimeError(f'{feature} {script} failed, see {out}')


class Budget:
    """RAM (GB) + process-count semaphore."""

    def __init__(self, gb, procs):
        self.gb, self.total_gb, self.procs, self.running, self.cv = gb, gb, procs, 0, threading.Condition()

    def acquire(self, gb):
        with self.cv:
            # waits until the job fits in the budget AND the machine really has that RAM available (other programs
            # may grow); a job larger than the whole budget runs alone. "Alone" is tested with a counter of running
            # jobs (a float equality gb == total_gb deadlocked the first run after many fractional add/subtract).
            while True:
                alone = self.running == 0
                free = psutil.virtual_memory().available / 2**30
                if alone or (self.gb >= gb - 1e-9 and self.procs >= 1 and free >= gb + 1.0):
                    break
                self.cv.wait(timeout=5)
            self.gb -= gb
            self.procs -= 1
            self.running += 1

    def release(self, gb):
        with self.cv:
            self.gb += gb
            self.procs += 1
            self.running -= 1
            self.cv.notify_all()


def ck_job(P, r, n):
    tag = f'{int(r.release):02d}_{r.commit}'
    out = P.data / 'ck' / f'{tag}_method.csv'
    if out.exists():
        return
    import shutil
    tmp = P.work / 'ck_tmp' / tag
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    (P.data / 'ck').mkdir(exist_ok=True)
    xmx = f'{max(1, int(n / 1000 * 0.3) + 1)}g'
    from s02_ck import ck_input                     # M24: files removed from CK's input only
    src = ck_input(P, P.snapshot_dir(r.release, r.commit), tag)
    p = subprocess.run([JAVA, f'-Xmx{xmx}', '-jar', str(CK_JAR), str(src), 'true',
                        '0', 'false', str(tmp) + '/'], capture_output=True, text=True, cwd=tmp)
    if src != P.snapshot_dir(r.release, r.commit):
        shutil.rmtree(src, ignore_errors=True)
    (P.data / 'ck' / f'{tag}.log').write_text(p.stdout[-5000:] + p.stderr[-5000:], encoding='utf-8')
    if p.returncode or not (tmp / 'method.csv').exists():
        raise RuntimeError(f'CK failed {P.feature} {tag}')
    shutil.move(tmp / 'class.csv', P.data / 'ck' / f'{tag}_class.csv')
    shutil.move(tmp / 'method.csv', out)
    shutil.rmtree(tmp, ignore_errors=True)


def und_job(P, r, n):
    tag = f'{int(r.release):02d}_{r.commit}'
    out = P.data / 'understand' / f'{tag}.csv'
    if out.exists():
        return
    (P.data / 'understand').mkdir(exist_ok=True)
    (P.work / 'und_dbs').mkdir(exist_ok=True)
    log_txt = und_lib.run(P.snapshot_dir(r.release, r.commit), P.work / 'und_dbs' / f'{tag}.und', out, 'batch')
    (P.data / 'understand' / f'{tag}.log').write_text(log_txt, encoding='utf-8')
    if not out.exists():
        raise RuntimeError(f'Understand failed {P.feature} {tag}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--features', nargs='*', default=None)
    ap.add_argument('--budget-gb', type=float,           # RAM available at start minus a safety margin
                    default=max(2.0, psutil.virtual_memory().available / 2**30 - 1.0))
    ap.add_argument('--max-procs', type=int, default=12)
    a = ap.parse_args()
    m = pd.read_csv(MAPPING_CSV)
    snaps = m[m.status == 'snapshot']
    order = (snaps.groupby('feature').java_producao.sum().sort_values().index.tolist())   # smallest first
    feats = [f for f in order if a.features is None or f in a.features]
    log(f'features: {feats} | RAM budget {a.budget_gb:.1f} GB | max procs {a.max_procs} | log {LOG}')

    # Phase A (a failing feature is logged and skipped; the others continue)
    for f in list(feats):
        P = Paths(f)
        if not (P.data / 'snapshots_stats.csv').exists():
            try:
                step(f, 's00_timeline')
                step(f, 's01_snapshots')
            except Exception as e:      # noqa: BLE001
                log('ERROR (feature skipped)', e)
                feats.remove(f)

    # Phase C thread (s04-s06, one feature at a time; reserves RAM in the budget)
    budget = Budget(a.budget_gb, a.max_procs)
    c_done, failed_c, errors = {}, set(), []

    def phase_c():
        for f in feats:
            P = Paths(f)
            try:
                for s, out in (('s04_methods', 'methods/blob_index.pkl'), ('s05_evometrics', 'method_changes.parquet'),
                               ('s06_change_distiller', 'change_distiller.parquet')):
                    if not (P.data / out).exists():
                        budget.acquire(3.0)
                        try:
                            step(f, s)
                        finally:
                            budget.release(3.0)
                c_done[f] = True
            except Exception as e:      # noqa: BLE001
                failed_c.add(f)
                errors.append(str(e))
                log('ERROR', e)

    tc = threading.Thread(target=phase_c)
    tc.start()

    # Phase B: global queue; smallest features first (each feature finishes and is audited as early as possible),
    # inside a feature the largest snapshots first (no long tail)
    jobs = []
    for rank, f in enumerate(feats):
        P = Paths(f)
        tl = pd.read_csv(P.data / 'timeline.csv')
        for r in tl.itertuples():
            n = int(r.java_producao)
            heapq.heappush(jobs, (rank, -n * 2.1, 'und', f, r, n, 0.6 + 0.40 * n / 1000))
            heapq.heappush(jobs, (rank, -n, 'ck', f, r, n, 0.5 + 0.30 * n / 1000))
    pending = {f: sum(1 for j in jobs if j[3] == f) for f in feats}
    log(f'phase B: {len(jobs)} CK/Understand jobs')
    threads = []
    finished = set()

    def finisher():
        """Phase D as soon as a feature is ready: s07 join + automatic audit (AUDITORIA.md)."""
        while len(finished) < len(feats):
            for f in feats:
                if f not in finished and pending[f] == 0 and (c_done.get(f) or f in failed_c):
                    finished.add(f)
                    if f in failed_c:
                        continue
                    try:
                        step(f, 's07_join')
                        step(f, 'auditar_feature')
                        log(f'[{f}] FEATURE DONE - see {Paths(f).base / "AUDITORIA.md"}')
                    except Exception as e:  # noqa: BLE001
                        errors.append(str(e))
                        log('ERROR', e)
            time.sleep(10)

    tf = threading.Thread(target=finisher)
    tf.start()

    def worker(kind, f, r, n, gb):
        try:
            (und_job if kind == 'und' else ck_job)(Paths(f), r, n)
        except Exception as e:          # noqa: BLE001
            errors.append(str(e))
            log('ERROR', e)
        finally:
            budget.release(gb)
            with _lock:
                pending[f] -= 1

    t0, done = time.time(), 0
    while jobs:
        _, _, kind, f, r, n, gb = heapq.heappop(jobs)
        gb = min(gb, a.budget_gb)
        budget.acquire(gb)
        th = threading.Thread(target=worker, args=(kind, f, r, n, gb))
        th.start()
        threads.append(th)
        done += 1
        if done % 25 == 0:
            log(f'phase B: {done} started, {len(jobs)} queued, {time.time() - t0:.0f}s')
    for th in threads:
        th.join()
    tc.join()
    tf.join()
    log('done' if not errors else f'finished with {len(errors)} errors: {errors[:5]}')


if __name__ == '__main__':
    main()
