"""Step 0 - EGit timeline derived from the simrel mapping.

Reads every release in the simrel mapping, takes the EGit commit, removes
duplicates (same commit in several releases keeps the earliest release),
removes the releases excluded by decision, checks that the result is a
linear history (each snapshot is an ancestor of the next) and writes
data/timeline.csv.
"""
import json
import subprocess

import pandas as pd

from config import DATA, EXCLUDED_RELEASES, FEATURE_KEY, MAPPING_DIR, REPO


def git(*args):
    return subprocess.run(['git', '-C', str(REPO), *args], capture_output=True, text=True)


rows = []
for f in sorted(MAPPING_DIR.glob('*.json')):
    d = json.loads(f.read_text(encoding='utf-8'))
    m = d['mappings'].get(FEATURE_KEY)
    if not m or m.get('status') != 'SUCCESS' or not m.get('commit'):
        print('without mapping:', d['release'])
        continue
    rows.append({'simrel_release': d['release'], 'simrel_date': d['date'],
                 'version': m.get('version'), 'commit': m['commit']})

df = pd.DataFrame(rows)
df['commit_ts'] = [int(git('show', '-s', '--format=%ct', c).stdout.strip()) for c in df['commit']]
df['commit_date'] = pd.to_datetime(df['commit_ts'], unit='s', utc=True)
df = df.sort_values(['commit_ts', 'simrel_date']).reset_index(drop=True)

log = [f'mapped releases: {len(df)}']
grouped = df.groupby('commit', sort=False).agg(
    simrel_release=('simrel_release', 'first'),
    all_releases=('simrel_release', lambda s: ';'.join(s)),
    simrel_date=('simrel_date', 'first'),
    version=('version', 'first'),
    commit_ts=('commit_ts', 'first'),
    commit_date=('commit_date', 'first'),
).reset_index()
log.append(f'unique commits: {len(grouped)}')
for _, r in grouped[grouped['all_releases'].str.contains(';')].iterrows():
    log.append(f'  duplicate commit {r["commit"][:8]}: {r["all_releases"]} -> kept {r["simrel_release"]}')

excl = grouped['simrel_release'].isin(EXCLUDED_RELEASES)
for _, r in grouped[excl].iterrows():
    log.append(f'  EXCLUDED {r["simrel_release"]} ({r["commit"][:8]}): {EXCLUDED_RELEASES[r["simrel_release"]]}')
tl = grouped[~excl].sort_values('commit_ts').reset_index(drop=True)
tl.insert(0, 'release', range(1, len(tl) + 1))

# Linearity check
prev = None
n_between = []
for c in tl['commit']:
    if prev is None:
        n_between.append(0)
    else:
        ok = git('merge-base', '--is-ancestor', prev, c).returncode == 0
        assert ok, f'{prev} is not an ancestor of {c}'
        n_between.append(int(git('rev-list', '--count', f'{prev}..{c}').stdout))
    prev = c
tl['commits_since_previous'] = n_between
log.append(f'final timeline: {len(tl)} snapshots, linear history verified')

DATA.mkdir(exist_ok=True)
tl.to_csv(DATA / 'timeline.csv', index=False)
(DATA / 'timeline.log').write_text('\n'.join(log), encoding='utf-8')
print('\n'.join(log))
print(tl[['release', 'simrel_release', 'commit', 'commit_date', 'commits_since_previous']].to_string())
