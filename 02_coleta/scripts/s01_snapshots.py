"""Step 1 - Export each snapshot (production .java only, M9/M10/M14).

Pilot: `git archive` + Python tarfile. Here, natively and faster: the commit tree is read into a TEMPORARY index
file (GIT_INDEX_FILE) and only the production files are written with `git checkout-index --prefix=<dir>/ --stdin`.
Neither the checkout nor the real index of the repository is touched (read-only use of the repository).
Snapshots run in parallel (I/O bound). The content is identical to the pilot's export (verified on EGit,
RECURSOS.md). Output: work/snapshots/<release>_<commit8>/, data/snapshots_stats.csv
"""
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from config import parse_args

P = parse_args(__doc__)


def export(r):
    out = P.snapshot_dir(r['release'], r['commit'])
    files = subprocess.run(['git', '-C', str(P.repo), 'ls-tree', '-r', '--name-only', r['commit']],
                           capture_output=True, text=True, encoding='utf-8', errors='replace',
                           check=True).stdout.splitlines()
    prod = [f for f in files if P.is_production_java(f)]
    n_java = sum(f.endswith('.java') for f in files)
    if not (out.exists() and sum(1 for f in out.rglob('*.java') if f.is_file()) == len(prod)):
        out.mkdir(parents=True, exist_ok=True)
        fd, idx = tempfile.mkstemp(prefix='tcc_idx_', dir=P.work)
        os.close(fd)
        os.remove(idx)
        env = dict(os.environ, GIT_INDEX_FILE=idx)
        try:
            subprocess.run(['git', '-C', str(P.repo), 'read-tree', r['commit']], env=env, check=True)
            subprocess.run(['git', '-C', str(P.repo), 'checkout-index', '--force', f'--prefix={out.as_posix()}/',
                            '--stdin'], env=env, input='\n'.join(prod).encode('utf-8'), check=True)
        finally:
            if os.path.exists(idx):
                os.remove(idx)
        got = sum(1 for f in out.rglob('*.java') if f.is_file())
        assert got == len(prod), f'{out.name}: extracted {got} of {len(prod)}'
    return {'release': r['release'], 'commit': r['commit'], 'java_total': n_java, 'java_production': len(prod)}


if __name__ == '__main__':
    tl = pd.read_csv(P.data / 'timeline.csv')
    with ThreadPoolExecutor(6) as ex:
        stats = list(ex.map(export, [r for _, r in tl.iterrows()]))
    for s in stats:
        print(s['release'], s['commit'][:8], s['java_total'], s['java_production'])
    pd.DataFrame(stats).to_csv(P.data / 'snapshots_stats.csv', index=False)
