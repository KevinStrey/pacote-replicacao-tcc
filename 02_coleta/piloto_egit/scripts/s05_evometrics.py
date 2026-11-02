"""Step 5 - Evolutionary metrics per method and release (corrected reimplementation of
cpmp/4.evometrics/evometrics.py; metrics from Elish & Al-Khiaty, 2013).

Change unit: a method m changes in commit k when its text (JavaParser toString,
as in JMethodsExtractor) differs between the first parent and k. Change size =
lines added + removed (Myers diff, the same library as the original).
Release r covers the non-merge commits in (c_{r-1}, c_r].

Per method m present in snapshot r:
  BOM   first release in which m appears in a snapshot (1 = already existed in the first)
  TACH  total lines changed in interval r
  CHO   1 if m changed in interval r
  FRCH  cumulative number of commits that changed m up to r
  FCH / LCH  first / last release in which m changed (0 = never)
  CHD   TACH_r / LOC_r (LOC = lines of the method text in snapshot r)
  WCH   sum_{j=BOM..r} TACH_j * 2^(j-r)
  WCD   sum_{j=BOM..r} CHD_j  * 2^(j-r)
  WFR   sum_{j<=r} (j-1) * CHO_j
  CSB   sum_{j<=r} TACH_j            (change size since birth)
  CSBS  CSB / LOC at birth
  ATAF  CSB / FRCH                   (0 if FRCH = 0)
  LCA / LCD  TACH / CHD of the last release with a change
  ACDF  sum_{j<=r} CHD_j / FRCH      (0 if FRCH = 0)
Release 1 (no history): every metric 0 except BOM = 1.
Output: data/evometrics.csv
"""
from collections import defaultdict

import myers
import pandas as pd

from config import DATA, PROJECT
from methods_lib import load_blob_methods

M = DATA / 'methods'


def nloc(text):
    return len(text.splitlines())


if __name__ == '__main__':
    tl = pd.read_csv(DATA / 'timeline.csv')
    sf = pd.read_csv(M / 'snapshot_files.csv')
    cc = pd.read_csv(M / 'commit_changes.csv')
    blobs, stats = load_blob_methods()
    print('blob methods:', dict(stats))

    # --- change events per commit ---
    events = defaultdict(lambda: [0, 0])     # (release, key) -> [tach, n_commits]
    mod = cc[cc['old_blob'].notna() & cc['new_blob'].notna()]
    for (rel, commit), g in mod.groupby(['release', 'commit'], sort=False):
        changed_in_commit = defaultdict(int)
        for _, row in g.iterrows():
            old, new = blobs[row['old_blob']], blobs[row['new_blob']]
            for k, text in new.items():
                prev = old.get(k)
                if prev is None or prev == text:
                    continue
                d = myers.diff(prev.splitlines(), text.splitlines())
                changed_in_commit[k] += sum(1 for op, _ in d if op in ('i', 'r'))
        for k, t in changed_in_commit.items():
            e = events[(rel, k)]
            e[0] += t
            e[1] += 1
    print('change events (release, method):', len(events))

    # --- metrics per snapshot ---
    st = defaultdict(lambda: {'bom': None, 'loc_birth': 0, 'frch': 0, 'fch': 0, 'lch': 0, 'csb': 0,
                              'sum_chd': 0.0, 'wfr': 0, 'lca': 0, 'lcd': 0.0, 'hist': []})
    rows = []
    prev_commit = ''
    n_dup_snapshot = 0
    for _, r in tl.iterrows():
        rel, commit = int(r['release']), r['commit']
        present = {}
        for _, f in sf[sf['release'] == rel].iterrows():
            for k, text in blobs[f['blob']].items():
                if k in present:            # same key in two files (duplicated class)
                    present[k] = None
                    n_dup_snapshot += 1
                else:
                    present[k] = (f['path'], text)
        for k, v in present.items():
            if v is None:
                continue
            path, text = v
            s = st[k]
            loc = nloc(text)
            if s['bom'] is None:
                s['bom'] = rel
                s['loc_birth'] = loc
            tach, ncom = events.get((rel, k), (0, 0)) if rel > 1 else (0, 0)
            cho = int(ncom > 0)
            chd = tach / loc if (tach and loc) else 0.0
            s['hist'].append((rel, tach, chd))
            s['frch'] += ncom
            s['csb'] += tach
            s['sum_chd'] += chd
            s['wfr'] += (rel - 1) * cho
            if cho:
                s['fch'] = s['fch'] or rel
                s['lch'] = rel
                s['lca'], s['lcd'] = tach, chd
            wch = sum(t * 2.0 ** (j - rel) for j, t, _ in s['hist'])
            wcd = sum(c * 2.0 ** (j - rel) for j, _, c in s['hist'])
            frch = s['frch']
            rows.append({
                'project': PROJECT, 'commit': commit, 'commitprevious': prev_commit, 'release': rel,
                'file': path, 'method_name': k, 'LOC_method': loc,
                'BOM': s['bom'], 'TACH': tach, 'FCH': s['fch'], 'LCH': s['lch'], 'CHO': cho, 'FRCH': frch,
                'CHD': chd, 'WCH': wch, 'WCD': wcd, 'WFR': s['wfr'],
                'ATAF': s['csb'] / frch if frch else 0.0, 'LCA': s['lca'], 'LCD': s['lcd'], 'CSB': s['csb'],
                'CSBS': s['csb'] / s['loc_birth'] if s['loc_birth'] else 0.0,
                'ACDF': s['sum_chd'] / frch if frch else 0.0,
            })
        prev_commit = commit
        print(rel, commit[:8], 'methods:', sum(v is not None for v in present.values()), flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(DATA / 'evometrics.csv', index=False)
    print('rows:', len(df), '| keys duplicated across files (discarded):', n_dup_snapshot)
    print(df.groupby('release')['CHO'].mean().describe())
