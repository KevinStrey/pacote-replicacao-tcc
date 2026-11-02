"""Step 0 - Feature timeline taken from the new mapping (5-Coleta_features/mapeamento/output/mapeamento.csv).

Keeps only rows with status 'snapshot' (duplicates already removed, M5). The release number is the GLOBAL
calendar index (M4: 1..54, identical for every feature), so it is not consecutive inside a feature.
Re-checks that consecutive snapshots are linear (each one an ancestor of the next).
Output: data/timeline.csv  (release, tag, data_simrel, commit, commit_date, presente, java_producao,
                            prev_commit, commits_since_previous)
"""
import subprocess

import pandas as pd

from config import MAPPING_CSV, parse_args

P = parse_args(__doc__)
m = pd.read_csv(MAPPING_CSV, dtype=str)
tl = m[(m.feature == P.feature) & (m.status == 'snapshot')].copy()
tl['release'] = tl['idx'].astype(int)
tl = tl.sort_values('release').reset_index(drop=True)


def git(*a):
    return subprocess.run(['git', '-C', str(P.repo), *a], capture_output=True, text=True)


prev, n_between = None, []
for c in tl['commit']:
    if prev is not None:
        assert git('merge-base', '--is-ancestor', prev, c).returncode == 0, f'not linear: {prev} -> {c}'
        n_between.append(int(git('rev-list', '--count', f'{prev}..{c}').stdout))
    else:
        n_between.append(0)
    prev = c
tl['prev_commit'] = [''] + list(tl['commit'][:-1])
tl['commits_since_previous'] = n_between
tl = tl.rename(columns={'data_commit': 'commit_date'})
cols = ['release', 'tag', 'data_simrel', 'commit', 'commit_date', 'presente', 'java_producao', 'prev_commit',
        'commits_since_previous']
tl[cols].to_csv(P.data / 'timeline.csv', index=False)
print(f'{P.feature}: {len(tl)} snapshots, releases (global index) {tl.release.min()}..{tl.release.max()}, '
      f'linear history verified')
