"""Step 1 - Export each timeline snapshot (production .java only) via git archive.

Does not change the checkout of the original repository. Each snapshot goes to
work/snapshots/<release>_<commit8>/ and is the input for CK and Understand.
"""
import io
import subprocess
import tarfile

import pandas as pd

from config import DATA, REPO, SNAPSHOTS, is_production_java


def snapshot_dir(release, commit):
    return SNAPSHOTS / f'{int(release):02d}_{commit[:8]}'


if __name__ == '__main__':
    tl = pd.read_csv(DATA / 'timeline.csv')
    stats = []
    for _, r in tl.iterrows():
        out = snapshot_dir(r['release'], r['commit'])
        files = subprocess.run(['git', '-C', str(REPO), 'ls-tree', '-r', '--name-only', r['commit']],
                               capture_output=True, text=True, check=True).stdout.splitlines()
        prod = [f for f in files if is_production_java(f)]
        n_java = sum(f.endswith('.java') for f in files)
        if not (out.exists() and sum(1 for _ in out.rglob('*.java')) == len(prod)):
            out.mkdir(parents=True, exist_ok=True)
            tar = subprocess.run(['git', '-C', str(REPO), 'archive', '--format=tar', r['commit']],
                                 capture_output=True, check=True).stdout
            with tarfile.open(fileobj=io.BytesIO(tar)) as t:
                members = [m for m in t.getmembers() if m.isfile() and is_production_java(m.name)]
                t.extractall(out, members=members, filter='data')
        stats.append({'release': r['release'], 'commit': r['commit'], 'java_total': n_java,
                      'java_production': len(prod)})
        print(r['release'], r['commit'][:8], n_java, len(prod))
    pd.DataFrame(stats).to_csv(DATA / 'snapshots_stats.csv', index=False)
