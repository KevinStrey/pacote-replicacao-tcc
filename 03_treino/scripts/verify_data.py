"""Checks the data files against dados/MANIFESTO.sha256 (generated where the package was built).
Exit code 1 if a file is missing or its hash differs. Log: saida/logs/verify_data.log.
"""
import sys

from common import DADOS, SAIDA, Log, sha256

(SAIDA / 'logs').mkdir(parents=True, exist_ok=True)
log = Log(SAIDA / 'logs' / 'verify_data.log')
mf = DADOS / 'MANIFESTO.sha256'
if not mf.exists():
    log('ERRO: manifesto ausente', mf)
    sys.exit(1)
bad = 0
entries = [l.split(None, 1) for l in mf.read_text(encoding='utf-8').splitlines() if l.strip()]
for h, name in entries:
    p = DADOS / name.strip().lstrip('*')
    if not p.exists():
        log('AUSENTE', p.name)
        bad += 1
        continue
    got = sha256(p)
    ok = got == h
    bad += not ok
    log('ok      ' if ok else 'DIFERENTE', p.name, '' if ok else f'(esperado {h}, obtido {got})')
log(f'{len(entries)} arquivos conferidos, {bad} com problema')
sys.exit(1 if bad else 0)
