"""Zips saida/ (logs, errors, results, status) into saida/resultados_e_logs.zip, without the zip itself and the lock.
Predictions (trabalho/) are not included. Usage: python empacotar_saida.py
"""
import os
import zipfile

from common import SAIDA

dest = SAIDA / 'resultados_e_logs.zip'
tmp = SAIDA / 'resultados_e_logs.zip.tmp'
n = 0
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as z:
    for p in sorted(SAIDA.rglob('*')):
        if p.is_file() and p not in (dest, tmp) and '.lock' not in p.parts and '/specs/' not in p.as_posix():
            z.write(p, p.relative_to(SAIDA.parent))
            n += 1
os.replace(tmp, dest)
print(f'{dest}: {n} arquivos, {dest.stat().st_size / 1e6:.1f} MB')
