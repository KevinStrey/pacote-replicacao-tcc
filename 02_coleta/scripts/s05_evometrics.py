"""Step 5 - Evolutionary metrics per method and release (same definitions as the pilot,
4-Coleta_egit/scripts/s05_evometrics.py; metrics from Elish & Al-Khiaty, 2013).

Differences from the pilot (decisions M4, M6; equivalence of the computation verified on EGit, RECURSOS.md):
 - `release` is the GLOBAL calendar index (M4). Formulas are unchanged: WCH/WCD weights 2^(j-r) and
   WFR = sum (j-1)*CHO_j use that index; BOM/FCH/LCH are global indexes. The first snapshot of the feature has
   no history (every metric 0 except BOM), as the pilot's "release 1".
 - interval commits exclude histories imported by merge (done in s04, M6).
 - equivalent commits (same patch-id: cherry-pick, rebase, "squashed merge") are counted once, at their earliest
   occurrence (M26, dup_lib.py; data/commit_duplicates.csv). The pilot counted the copies again.
 - Myers diffs (the expensive part) run in RESOURCES['PY_WORKERS'] processes; texts are read from the sqlite
   store by hash. Each distinct (old text, new text) pair is diffed once.
Per method m present in snapshot r (definitions as in the pilot): BOM, TACH, CHO, FRCH, FCH, LCH, CHD, WCH,
WCD, WFR, CSB, CSBS, ATAF, LCA, LCD, ACDF. Outputs: data/evometrics.parquet, data/method_changes.parquet (audit trail of every method change)
"""
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from config import RESOURCES, parse_args
from dup_lib import duplicates
from methods_lib import TextStore, load_index, snapshot_methods

_store = None


def _init(db):
    global _store
    import methods_lib
    _store = methods_lib.TextStore(db)


def _diff_size(pair):
    """Lines inserted + removed between two method texts (Myers diff, as in the pilot)."""
    import myers
    a, b = _store.get(pair[0]), _store.get(pair[1])
    return pair, sum(1 for op, _ in myers.diff(a.splitlines(), b.splitlines()) if op in ('i', 'r'))


if __name__ == '__main__':
    P = parse_args(__doc__)
    M = P.data / 'methods'
    tl = pd.read_csv(P.data / 'timeline.csv')
    sf = pd.read_csv(M / 'snapshot_files.csv')
    cc = pd.read_csv(M / 'commit_changes.csv')
    index = load_index(M / 'blob_index.pkl')

    # --- M26: equivalent commits (cherry-pick/rebase copies) are counted once ---
    dups = duplicates(P.repo, cc)
    dups.to_csv(P.data / 'commit_duplicates.csv', index=False)
    ignored = set(dups.loc[dups['duplicate_of'] != '', 'commit'])
    print(f'equivalent commits ignored (M26): {len(ignored)} of {len(dups)} commits with modified files', flush=True)

    # --- change events per commit: (release, commit, key, old_hash, new_hash) ---
    mod = cc[cc['old_blob'].notna() & cc['new_blob'].notna() & ~cc['commit'].isin(ignored)]
    changes = []                       # (release, commit, key, pair)
    for row in mod.itertuples(index=False):
        old, new = index[row.old_blob], index[row.new_blob]
        for k, (h, _) in new.items():
            prev = old.get(k)
            if prev is None or prev[0] == h:
                continue
            changes.append((row.release, row.commit, k, (prev[0], h)))
    pairs = sorted({c[3] for c in changes})
    print(f'changed method versions: {len(changes)} | distinct text pairs to diff: {len(pairs)}', flush=True)
    sizes = {}
    if pairs:
        with ProcessPoolExecutor(RESOURCES['PY_WORKERS'], initializer=_init,
                                 initargs=(str(M / 'method_texts.sqlite'),)) as ex:
            for pair, n in ex.map(_diff_size, pairs, chunksize=256):
                sizes[pair] = n

    events = defaultdict(lambda: [0, 0])     # (release, key) -> [tach, n_commits]
    per_commit = defaultdict(int)            # (release, commit, key) -> lines changed in that commit
    for rel, commit, k, pair in changes:
        per_commit[(rel, commit, k)] += sizes[pair]
    for (rel, commit, k), t in per_commit.items():
        e = events[(rel, k)]
        e[0] += t
        e[1] += 1
    print('change events (release, method):', len(events), flush=True)
    # audit trail (not used by the metrics): every (release, commit, method) change with its size
    pd.DataFrame([(rel, commit, k, t) for (rel, commit, k), t in per_commit.items()],
                 columns=['release', 'commit', 'method_name', 'lines_changed']).to_parquet(
        P.data / 'method_changes.parquet', index=False)

    # --- metrics per snapshot (same loop as the pilot; rel = global index) ---
    st = defaultdict(lambda: {'bom': None, 'loc_birth': 0, 'frch': 0, 'fch': 0, 'lch': 0, 'csb': 0,
                              'sum_chd': 0.0, 'wfr': 0, 'lca': 0, 'lcd': 0.0, 'hist': []})
    sf_by_rel = {rel: list(zip(g['path'], g['blob'])) for rel, g in sf.groupby('release')}
    rows, prev_commit, first_rel = [], '', int(tl['release'].iloc[0])
    for _, r in tl.iterrows():
        rel, commit = int(r['release']), r['commit']
        present = snapshot_methods(sf_by_rel.get(rel, []), index)
        for k, (h, loc, path) in present.items():
            s = st[k]
            if s['bom'] is None:
                s['bom'] = rel
                s['loc_birth'] = loc
            tach, ncom = events.get((rel, k), (0, 0)) if rel > first_rel else (0, 0)
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
                'feature': P.feature, 'repository': P.repository, 'project': P.repository, 'commit': commit,
                'commitprevious': prev_commit, 'release': rel, 'file': path, 'method_name': k, 'LOC_method': loc,
                'BOM': s['bom'], 'TACH': tach, 'FCH': s['fch'], 'LCH': s['lch'], 'CHO': cho, 'FRCH': frch,
                'CHD': chd, 'WCH': wch, 'WCD': wcd, 'WFR': s['wfr'],
                'ATAF': s['csb'] / frch if frch else 0.0, 'LCA': s['lca'], 'LCD': s['lcd'], 'CSB': s['csb'],
                'CSBS': s['csb'] / s['loc_birth'] if s['loc_birth'] else 0.0,
                'ACDF': s['sum_chd'] / frch if frch else 0.0,
            })
        prev_commit = commit
        print(rel, commit[:8], 'methods:', len(present), flush=True)

    df = pd.DataFrame(rows)
    df.to_parquet(P.data / 'evometrics.parquet', index=False)
    print('rows:', len(df))
