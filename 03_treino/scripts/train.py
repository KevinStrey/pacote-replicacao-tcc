"""Builds the jobs of a phase and runs them in parallel subprocesses, with checkpoint, retries and timeouts.

- Checkpoint: a job is done when resultados/jobs/<id>.json exists (written atomically by job.py); a restart skips it.
- Each job runs in its own process (job.py) with OMP/BLAS threads limited; its output goes to logs/jobs/<id>.log and,
  on failure, to erros/<id>.log (with exit code and reason). One failure never stops the others.
- Scheduling: jobs start while the sum of their threads fits the cores and the sum of their estimated RAM fits the
  budget (config: recursos). A memory watchdog kills the most recent job when free RAM falls below half of the reserve
  and sends it back to the queue to run alone ('solo'); this does not count as an attempt.
- Retries: 'tentativas' per job (timeouts are not retried); the retry of a job killed by the system (sinal 9, typical
  of the OOM killer) runs alone.
- Status: status/<fase>.json (updated every 30 s) and logs/train_<fase>.log.
- Phase 3 picks the best configuration(s) of each protocol among the 'principal' results of phases 1 and 2.
Exit code: 0 = every job done; 3 = some job failed (see erros/); 2 = configuration/data error.
Usage: python train.py --execucao principal --fase fase1
"""
import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import psutil

from common import Log, Run, load_config, read_json, write_json

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--execucao', default='principal', choices=['principal', 'teste_rapido'])
ap.add_argument('--fase', required=True, choices=['fase1', 'fase2', 'fase3'])
args = ap.parse_args()
cfg = load_config()
run = Run(args.execucao)
log = Log(run.logs / f'train_{args.fase}.log')
R = cfg['recursos']
meta_p = run.prep / 'meta.json'
if not meta_p.exists():
    log('ERRO: dados não preparados', meta_p)
    sys.exit(2)
meta = read_json(meta_p)
SEED = cfg['semente']
CV = cfg['protocolos']['random']['cv_partes']
CV_RUN = cfg['teste_rapido']['cv_partes_executadas'] if run.sample else CV
CORES = max(1, (psutil.cpu_count(logical=True) or 1) - R['reserva_nucleos'])
RESERVE = R['reserva_ram_gb'] if not run.sample else min(R['reserva_ram_gb'], 2)
BUDGET = max(1.0, psutil.virtual_memory().available / 1e9 - RESERVE)
TIMEOUT = R['timeout_horas'] * 3600


def ncols(conj):
    return sum(len(cfg[g]) for g in cfg['conjuntos'][conj])


def job(fase, proto, var, conj, rs, alg, parte):
    jid = f'{fase}__{proto}__{var}__{conj}__{rs}__{alg}__{parte}'
    n_tr = meta['splits'][f'{proto}__{var}']['treino']
    if parte != 'teste':
        n_tr = n_tr * (CV - 1) // CV
    mem = n_tr * ncols(conj) * 4 / 1e9 * R['mem_multiplicador'][rs] + R['mem_extra_gb'][alg]
    if run.sample:
        mem = mem / 10
    mem += R['mem_base_gb']
    return {'id': jid, 'execucao': run.name, 'fase': fase, 'protocolo': proto, 'variante': var, 'conjunto': conj,
            'reamostragem': rs, 'algoritmo': alg, 'parte': parte, 'cv_partes': CV, 'semente': SEED,
            'threads': min(R['threads'][alg], CORES), 'mem_gb': round(mem, 1)}


def build_jobs():
    F = cfg['fases']
    jobs = []
    if args.fase in ('fase1', 'fase2'):
        f = F[args.fase]
        for proto in f['protocolos']:                      # temporal first: fastest initial results
            for conj in cfg['conjuntos']:
                for rs in cfg['reamostragem']:
                    for alg in f['algoritmos']:
                        jobs.append(job(args.fase, proto, 'principal', conj, rs, alg, 'teste'))
        for proto in f['protocolos']:                      # CV folds after every test job of the phase
            if proto == 'random':
                for conj in cfg['conjuntos']:
                    for rs in cfg['reamostragem']:
                        for alg in f['algoritmos']:
                            jobs += [job(args.fase, proto, 'principal', conj, rs, alg, f'cv{k:02d}')
                                     for k in range(1, CV_RUN + 1)]
        return jobs
    f = F['fase3']
    done = [read_json(p) for p in run.jobs.glob('fase[12]__*__principal__*__teste.json')]
    sel = []
    for proto in f['protocolos']:
        cand = [r for r in done if r['protocolo'] == proto and r['metricas'].get(f['metrica_selecao']) is not None]
        cand.sort(key=lambda r: r['metricas'][f['metrica_selecao']], reverse=True)
        if not cand:
            log(f'AVISO: sem resultados do protocolo {proto} para a fase 3')
        for r in cand[:f['top_k']]:
            sel.append({'protocolo': proto, 'origem': r['id'], 'metrica': r['metricas'][f['metrica_selecao']]})
            j = job('fase3', proto, f['variante'], r['conjunto'], r['reamostragem'], r['algoritmo'], 'teste')
            j['origem'] = r['id']
            jobs.append(j)
    write_json(run.results / 'fase3_selecao.json', sel)
    for s in sel:
        log(f'fase 3: {s["protocolo"]} <- {s["origem"]} ({f["metrica_selecao"]} = {s["metrica"]:.4f})')
    return jobs


jobs = build_jobs()
specs_dir = run.status / 'specs'
specs_dir.mkdir(exist_ok=True)
todo = [j for j in jobs if not (run.jobs / f'{j["id"]}.json').exists()]
log(f'{args.execucao} {args.fase}: {len(jobs)} jobs, {len(jobs) - len(todo)} já concluídos, {len(todo)} a executar | '
    f'núcleos={CORES} orçamento RAM={BUDGET:.0f} GB reserva={RESERVE} GB timeout={R["timeout_horas"]} h')
for j in todo:
    j.update({'tentativas': 0, 'solo': j['mem_gb'] > BUDGET})
    write_json(specs_dir / f'{j["id"]}.json', j)

pending = list(todo)
running = {}      # id -> dict(job, proc, start, logfh)
failed = {}
finished = []
stop = False


def on_signal(signum, _frame):
    global stop
    stop = True
    log(f'sinal {signum} recebido: encerrando jobs em execução (os concluídos ficam salvos)')


signal.signal(signal.SIGTERM, on_signal)
signal.signal(signal.SIGINT, on_signal)
if hasattr(signal, 'SIGHUP'):
    signal.signal(signal.SIGHUP, signal.SIG_IGN)    # logout of the session must not stop the run


def kill(proc):
    try:
        if os.name == 'posix':
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
    except (ProcessLookupError, PermissionError, OSError):
        pass


def start(j):
    env = dict(os.environ)
    t = str(j['threads'])
    env.update({'OMP_NUM_THREADS': t, 'OPENBLAS_NUM_THREADS': t, 'MKL_NUM_THREADS': t, 'NUMEXPR_NUM_THREADS': t,
                'VECLIB_MAXIMUM_THREADS': t, 'PYTHONHASHSEED': '0', 'PYTHONNOUSERSITE': '1',
                'PYTHONIOENCODING': 'utf-8'})
    fh = open(run.job_logs / f'{j["id"]}.log', 'a', encoding='utf-8')
    fh.write(f'\n===== tentativa {j["tentativas"] + 1} {time.strftime("%Y-%m-%d %H:%M:%S")} =====\n')
    fh.flush()
    proc = subprocess.Popen([sys.executable, '-u', str(HERE / 'job.py'), str(specs_dir / f'{j["id"]}.json')],
                            stdout=fh, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env, cwd=str(HERE),
                            start_new_session=(os.name == 'posix'))
    running[j['id']] = {'job': j, 'proc': proc, 'start': time.time(), 'fh': fh}
    log(f'início {j["id"]} (threads={j["threads"]}, RAM estimada={j["mem_gb"]} GB{", sozinho" if j["solo"] else ""})')


def record_error(j, reason, rc):
    src = run.job_logs / f'{j["id"]}.log'
    with open(run.errors / f'{j["id"]}.log', 'a', encoding='utf-8') as out:
        out.write(f'##### ERRO {time.strftime("%Y-%m-%d %H:%M:%S")} tentativa {j["tentativas"]} | motivo: {reason} | '
                  f'código de saída: {rc} =====\n')
        if src.exists():
            out.write(''.join(src.read_text(encoding='utf-8', errors='replace').splitlines(True)[-200:]))
        out.write('\n')


def finish(jid, reason=None):
    r = running.pop(jid)
    j, proc = r['job'], r['proc']
    r['fh'].close()
    rc = proc.poll()
    ok = reason is None and rc == 0 and (run.jobs / f'{jid}.json').exists()
    if ok:
        finished.append(jid)
        log(f'fim {jid} em {time.time() - r["start"]:.0f} s ({len(finished)}/{len(todo)})')
        return
    if reason == 'memoria':          # killed by the watchdog: back to the queue, alone, without counting an attempt
        j['solo'] = True
        record_error(j, 'encerrado pelo vigia de memória; volta para a fila para rodar sozinho', rc)
        pending.insert(0, j)
        return
    j['tentativas'] += 1
    if reason is None:
        reason = f'morto pelo sinal {-rc} (sinal 9 = provável falta de memória)' if rc is not None and rc < 0 \
            else f'erro (código {rc}; traceback no log)'
    record_error(j, reason, rc)
    retry = j['tentativas'] < R['tentativas'] and not reason.startswith('timeout') and not stop
    log(f'FALHA {jid}: {reason}' + (' -> nova tentativa' if retry else ' -> desistindo'))
    if retry:
        if rc is not None and rc < 0:
            j['solo'] = True
        pending.append(j)
    else:
        failed[jid] = reason


def fits(j, used_threads, used_mem):
    if not running:
        return True
    if j['solo'] or any(r['job']['solo'] for r in running.values()):
        return False
    return used_threads + j['threads'] <= CORES and used_mem + j['mem_gb'] <= BUDGET


def write_status():
    write_json(run.status / f'{args.fase}.json', {
        'atualizado': time.strftime('%Y-%m-%d %H:%M:%S'), 'execucao': run.name, 'fase': args.fase,
        'total': len(jobs), 'ja_concluidos_antes': len(jobs) - len(todo), 'concluidos_agora': len(finished),
        'pendentes': len(pending), 'em_execucao': [{'id': k, 'minutos': round((time.time() - v['start']) / 60, 1),
                                                     'ram_gb': _rss(v['proc'])} for k, v in running.items()],
        'falhas': failed, 'ram_livre_gb': round(psutil.virtual_memory().available / 1e9, 1)})


def _rss(proc):
    try:
        p = psutil.Process(proc.pid)
        return round(sum(c.memory_info().rss for c in [p] + p.children(recursive=True)) / 1e9, 1)
    except psutil.Error:
        return None


last_status = 0
head_wait = None
while (pending or running) and not stop:
    for jid, r in list(running.items()):
        if r['proc'].poll() is not None:
            finish(jid)
        elif time.time() - r['start'] > TIMEOUT:
            kill(r['proc'])
            r['proc'].wait()
            finish(jid, f'timeout ({R["timeout_horas"]} h)')
    avail = psutil.virtual_memory().available / 1e9
    if avail < RESERVE / 2 and len(running) > 1:
        jid = max(running, key=lambda k: running[k]['start'])
        log(f'vigia de memória: {avail:.1f} GB livres; encerrando {jid}')
        kill(running[jid]['proc'])
        running[jid]['proc'].wait()
        finish(jid, 'memoria')
    used_t = sum(r['job']['threads'] for r in running.values())
    used_m = sum(r['job']['mem_gb'] for r in running.values())
    started = True
    while started and pending and not stop:
        started = False
        for i, j in enumerate(pending):
            if i > 0 and head_wait and time.time() - head_wait > 1200:
                break                                  # the head waited 20 min: stop backfilling smaller jobs
            if fits(j, used_t, used_m) and (not running or avail - j['mem_gb'] >= RESERVE or j['solo']):
                pending.pop(i)
                start(j)
                used_t += j['threads']
                used_m += j['mem_gb']
                head_wait = None if i == 0 else head_wait
                started = True
                break
            if i == 0 and head_wait is None:
                head_wait = time.time()
    if time.time() - last_status > 30:
        write_status()
        last_status = time.time()
    time.sleep(2)

if stop:
    for jid, r in list(running.items()):
        kill(r['proc'])
        r['proc'].wait()
        r['fh'].close()
        record_error(r['job'], 'interrompido por sinal (o job será refeito na próxima execução)', None)
    running.clear()
write_status()
shutil.rmtree(specs_dir, ignore_errors=True) if not pending and not failed and not stop else None
log(f'{args.fase}: concluídos agora {len(finished)}, falhas {len(failed)}, pendentes {len(pending)}')
for k, v in failed.items():
    log(f'  falhou: {k}: {v}')
sys.exit(130 if stop else (3 if failed else 0))
