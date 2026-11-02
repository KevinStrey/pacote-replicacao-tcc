"""Builds the package for the server (run on the collection machine): 6-Treino/pacote/treino_tcc/ and treino_tcc.zip.

Contents: scripts, config, shell scripts, environment files, plan, instructions, the micromamba binary for linux-64,
and dados/ with the 19 final parquets, calendario.csv and MANIFESTO.sha256 (checked on the server by verify_data.py).
Text files are written with LF line endings; shell scripts and micromamba get the executable bit inside the zip.
Usage: python montar_pacote.py [--sem-zip]
"""
import argparse
import hashlib
import shutil
import sys
import zipfile
from pathlib import Path

TREINO = Path(__file__).resolve().parent.parent
ROOT = TREINO.parent
COLETA = ROOT / '5-Coleta_features'
OUT = TREINO / 'pacote'
STAGE = OUT / 'treino_tcc'
FEATURES = ['BIRT', 'CDT', 'CVS', 'DataTools', 'EGit', 'EMF', 'EclipseLink', 'GEF', 'GMF_Runtime', 'JDT', 'Mylyn',
            'PDE', 'PTP', 'RAP', 'Scout', 'Subversive', 'WebTools', 'Window_Builder', 'm2e']
TEXT = ['executar_tudo.sh', 'iniciar.sh', 'status.sh', 'parar.sh', 'environment.yml', 'conda-linux-64.lock',
        'PLANO_TREINO.md', 'LEIA-ME.md', 'config/experimentos.yaml'] + \
       [f'scripts/{p.name}' for p in sorted((TREINO / 'scripts').glob('*.py'))]
EXEC = {'executar_tudo.sh', 'iniciar.sh', 'status.sh', 'parar.sh', 'ferramentas/micromamba'}


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        while chunk := fh.read(1 << 24):
            h.update(chunk)
    return h.hexdigest()


ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--sem-zip', action='store_true')
args = ap.parse_args()
sys.stdout.reconfigure(encoding='utf-8')
(STAGE / 'dados').mkdir(parents=True, exist_ok=True)
for rel in TEXT:
    dst = STAGE / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    txt = (TREINO / rel).read_text(encoding='utf-8').replace('\r\n', '\n')
    dst.write_text(txt, encoding='utf-8', newline='\n')
(STAGE / 'ferramentas').mkdir(exist_ok=True)
shutil.copy2(TREINO / 'ferramentas' / 'micromamba', STAGE / 'ferramentas' / 'micromamba')
manifest = []
for f in FEATURES:
    src = COLETA / f / 'data' / f'{f}-all-releases.parquet'
    dst = STAGE / 'dados' / src.name
    if not dst.exists() or dst.stat().st_size != src.stat().st_size or dst.stat().st_mtime < src.stat().st_mtime:
        shutil.copy2(src, dst)
    manifest.append((sha256(dst), dst.name))
    print('dados:', dst.name, f'{dst.stat().st_size / 1e6:.0f} MB', flush=True)
shutil.copy2(COLETA / 'mapeamento' / 'output' / 'calendario.csv', STAGE / 'dados' / 'calendario.csv')
manifest.append((sha256(STAGE / 'dados' / 'calendario.csv'), 'calendario.csv'))
(STAGE / 'dados' / 'MANIFESTO.sha256').write_text(''.join(f'{h}  {n}\n' for h, n in manifest), encoding='utf-8',
                                                  newline='\n')
print('manifesto:', len(manifest), 'arquivos')
if args.sem_zip:
    sys.exit(0)
zpath = OUT / 'treino_tcc.zip'
tmp = OUT / 'treino_tcc.zip.tmp'
with zipfile.ZipFile(tmp, 'w', allowZip64=True) as z:
    for p in sorted(STAGE.rglob('*')):
        if not p.is_file():
            continue
        rel = p.relative_to(STAGE).as_posix()
        if rel.startswith(('saida/', 'trabalho/', 'ambiente/', '.mamba/')):
            continue
        info = zipfile.ZipInfo.from_file(p, f'treino_tcc/{rel}')
        info.create_system = 3                                     # unix, so the mode below is honoured by unzip
        info.external_attr = ((0o755 if rel in EXEC else 0o644) | 0o100000) << 16
        info.compress_type = zipfile.ZIP_STORED if p.suffix == '.parquet' or rel in EXEC else zipfile.ZIP_DEFLATED
        with open(p, 'rb') as src, z.open(info, 'w', force_zip64=True) as dst:
            shutil.copyfileobj(src, dst, 1 << 24)
tmp.replace(zpath)
print(f'{zpath}: {zpath.stat().st_size / 1e9:.2f} GB; SHA-256 {sha256(zpath)}')
