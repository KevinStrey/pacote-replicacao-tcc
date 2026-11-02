"""M26: equivalent commits (the same change applied twice, by cherry-pick, rebase or "squashed merge").

Two counted commits are equivalent when `git patch-id --stable` of their diff, restricted to the production .java
files the feature counts (whole-commit diff for very large commits), is identical. For the evolutionary metrics each
change is counted once: the earliest commit (committer date) of each patch-id is kept and the copies are ignored.
The pilot counted the copies again (decision of the author, 2026-10-14; see INVENTARIO.md, M26).
"""
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pandas as pd


def _patch_id(repo, commit, parent, paths):
    spec = ['--', *paths] if sum(len(p) for p in paths) < 20000 else []
    diff = subprocess.run(['git', '-C', str(repo), 'diff', '-M', parent, commit, *spec], capture_output=True).stdout
    out = subprocess.run(['git', '-C', str(repo), 'patch-id', '--stable'], input=diff,
                         capture_output=True).stdout.decode().split()
    ts = subprocess.run(['git', '-C', str(repo), 'show', '-s', '--format=%ct', commit], capture_output=True,
                        text=True).stdout.strip()
    return commit, (out[0] if out else ''), int(ts or 0)


def duplicates(repo, cc, workers=8):
    """cc: commit_changes.csv (modified-file rows). Returns a DataFrame commit, release, patch_id, ts, duplicate_of."""
    mod = cc[cc['old_blob'].notna() & cc['new_blob'].notna()]
    jobs = []
    for c, g in mod.groupby('commit'):
        paths = sorted(set(g['old_path'].dropna()) | set(g['new_path'].dropna()))
        jobs.append((c, g['parent'].iloc[0], paths, int(g['release'].iloc[0])))
    with ThreadPoolExecutor(workers) as ex:
        res = list(ex.map(lambda j: _patch_id(repo, j[0], j[1], j[2]), jobs))
    rel = {j[0]: j[3] for j in jobs}
    d = pd.DataFrame(res, columns=['commit', 'patch_id', 'ts'])
    d['release'] = d['commit'].map(rel)
    d = d.sort_values(['ts', 'commit']).reset_index(drop=True)
    first, dup_of = {}, []
    for r in d.itertuples():
        if r.patch_id and r.patch_id in first:
            dup_of.append(first[r.patch_id])
        else:
            dup_of.append('')
            if r.patch_id:
                first[r.patch_id] = r.commit
    d['duplicate_of'] = dup_of
    return d
