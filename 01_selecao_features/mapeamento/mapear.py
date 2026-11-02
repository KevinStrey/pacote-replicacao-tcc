"""New temporal mapping simrel -> commit for every SPL feature (decisions M1–M16).

1. Calendar (M2): simrel.build tags in commit-date order, minus TAGS_EXCLUDED; global index 1..N (M4).
2. Presence (M3): criteria C1–C4 of auditoria_simrel/CRITERIOS.md at the commit of each tag.
   The series of a feature goes from its first to its last present date (internal gaps are crossed),
   starting no earlier than FEATURES[f]['start'] (M12, M15).
3. Snapshot (M1): last commit of the main line, following only the first parent, with committer date
   <= the tag date:  git rev-list -1 --first-parent --before=<date> <main line>
4. Consecutive identical snapshots are marked as duplicates and dropped (M5).
5. Audits: ancestry between consecutive snapshots (linearity), commits of the interval, commits coming
   from histories imported by merge (M6), production .java per snapshot (M9, M10, M14).
Outputs (output/): calendario.csv, presenca.csv, mapeamento.csv, intervalos.csv, mapear.log
Read-only on every repository.
"""
import csv
import re
import subprocess
import sys
from datetime import datetime

from features import FEATURES, OUT, REPOS, SIMREL, TAGS_EXCLUDED, is_production_java


def git(repo, *args, check=False):
    p = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True, encoding='utf-8',
                       errors='replace')
    if check and p.returncode:
        raise RuntimeError(f'git {args} in {repo}: {p.stderr}')
    return p.stdout.strip()


LOG = []


def log(*a):
    s = ' '.join(str(x) for x in a)
    LOG.append(s)
    print(s, flush=True)


# ---------- 1. calendar ----------
tags = []
for t in git(SIMREL, 'tag').split():
    c = git(SIMREL, 'rev-list', '-1', f'refs/tags/{t}')
    iso = git(SIMREL, 'show', '-s', '--format=%cI', c)
    tags.append((datetime.fromisoformat(iso), t, c, iso))
tags.sort()
calendar = [(t, c, iso) for _, t, c, iso in tags if t not in TAGS_EXCLUDED]
log(f'simrel tags: {len(tags)} | excluded: {len(TAGS_EXCLUDED)} | calendar: {len(calendar)}')
OUT.mkdir(exist_ok=True)
with open(OUT / 'calendario.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['idx', 'tag', 'simrel_commit', 'data'])
    for i, (t, c, iso) in enumerate(calendar, 1):
        w.writerow([i, t, c, iso])


# ---------- 2. presence ----------
_tree, _blob = {}, {}


def tree(commit):
    if commit not in _tree:
        _tree[commit] = git(SIMREL, 'ls-tree', '--name-only', commit).splitlines()
    return _tree[commit]


def show(commit, path):
    k = (commit, path)
    if k not in _blob:
        _blob[k] = git(SIMREL, 'show', f'{commit}:{path}')
    return _blob[k]


ROOT_TAG = re.compile(r'<aggregator:Contribution\b[^>]*>', re.S)


def presence(cfg, commit):
    files = [n for n in tree(commit) if re.match(cfg['file'], n)]
    if not files:
        return dict(c1='nao', c2='-', c3='-', c4='-', arquivo='')
    fn = files[0]
    main = next(n for n in tree(commit) if n in ('simrel.aggr', 'simrel.b3aggr'))
    c2 = 'sim' if f'href="{fn}#' in show(commit, main) else 'nao'
    xml = show(commit, fn)
    root = ROOT_TAG.search(xml)
    c3 = 'nao' if root and 'enabled="false"' in root.group(0) else 'sim'
    c4 = '-'
    if cfg.get('p2'):
        m = re.search(rf'<features[^>]*name="{re.escape(cfg["p2"])}"[^>]*>', xml)
        c4 = 'nao' if not m else ('desabilitada' if 'enabled="false"' in m.group(0) else 'sim')
    return dict(c1='sim', c2=c2, c3=c3, c4=c4, arquivo=fn)


# ---------- 3–5. snapshots and audits ----------
def main_line(repo, ref, follow_parent2=()):
    """Main line as [(commit, committer_ts)], newest first: the first-parent chain from ref, except at the merges
    listed in follow_parent2 (inverted merges), where the chain continues through the 2nd parent."""
    chain, tip = [], ref
    while tip:
        seg = [l.split() for l in git(repo, 'rev-list', '--first-parent', '--format=%H %ct', tip).splitlines()
               if not l.startswith('commit ')]
        tip = None
        for h, ts in seg:
            chain.append((h, int(ts)))
            if h in follow_parent2:
                tip = f'{h}^2'
                break
    return chain


def snapshot_at(chain, iso):
    """First commit of the main line (walk order) with committer date <= iso; same semantics as
    git rev-list -1 --first-parent --before=<iso>."""
    limit = datetime.fromisoformat(iso).timestamp()
    return next((h for h, ts in chain if ts <= limit), '')


def roots(repo, c):
    return git(repo, 'rev-list', '--max-parents=0', c).split()


def interval_commits(repo, prev, cur):
    """Non-merge commits in prev..cur, and those that do not descend from the previous history (imported)."""
    allc = set(git(repo, 'rev-list', '--no-merges', f'{prev}..{cur}').split())
    if not allc:
        return 0, 0
    desc = set()
    for r in roots(repo, prev):
        desc |= set(git(repo, 'rev-list', '--no-merges', '--ancestry-path', f'{r}..{cur}').split())
    return len(allc), len(allc - desc)


only = sys.argv[1:]
pres_rows, map_rows, int_rows = [], [], []
for feat, cfg in FEATURES.items():
    if only and feat not in only:
        continue
    repo = REPOS / cfg['repo']
    ref = cfg.get('ref') or git(repo, 'symbolic-ref', '--short', 'refs/remotes/origin/HEAD', check=True)
    log(f'\n=== {feat} ({cfg["repo"]}, linha principal {ref})')
    pres = []
    for i, (t, c, iso) in enumerate(calendar, 1):
        p = presence(cfg, c)
        ok = p['c1'] == p['c2'] == p['c3'] == 'sim' and p['c4'] in ('-', 'sim')
        pres.append(ok)
        pres_rows.append(dict(feature=feat, idx=i, tag=t, data=iso[:10], presente='sim' if ok else 'nao', **p))
    present_idx = [i for i, ok in enumerate(pres) if ok]
    if not present_idx:
        log('  never present')
        continue
    first, last = present_idx[0], present_idx[-1]
    start_tag = cfg.get('start')
    if start_tag:
        first = max(first, next(i for i, (t, _, _) in enumerate(calendar) if t == start_tag))
    gaps = [calendar[i][0] for i in range(first, last + 1) if not pres[i]]
    log(f'  present: {calendar[present_idx[0]][0]} -> {calendar[last][0]} | series: {calendar[first][0]} -> '
        f'{calendar[last][0]} | internal gaps crossed: {gaps or "none"}')
    chain = main_line(repo, ref, cfg.get('follow_parent2', ()))
    log(f'  main line: {len(chain)} commits, ends at {chain[-1][0][:10]} '
        f'({git(repo, "show", "-s", "--format=%cs %s", chain[-1][0])[:70]})')
    prev_kept = None
    for i in range(first, last + 1):
        t, c, iso = calendar[i]
        snap = snapshot_at(chain, iso)
        files = git(repo, 'ls-tree', '-r', '--name-only', snap).splitlines() if snap else []
        prod = sum(is_production_java(p, feat) for p in files)
        status = 'snapshot'
        if not snap:
            status = 'sem commit'
        elif prev_kept and snap == prev_kept[1]:
            status = f'duplicata de {prev_kept[0]}'
        row = dict(feature=feat, repository=cfg['repo'], idx=i + 1, tag=t, data_simrel=iso[:10],
                   presente='sim' if pres[i] else 'nao (lacuna)', commit=snap,
                   data_commit=git(repo, 'show', '-s', '--format=%cs', snap) if snap else '',
                   java_producao=prod, status=status)
        map_rows.append(row)
        if status == 'snapshot':
            if prev_kept:
                lin = subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', prev_kept[1],
                                      snap]).returncode == 0
                n, imp = interval_commits(repo, prev_kept[1], snap)
                int_rows.append(dict(feature=feat, de=prev_kept[0], ate=t, idx_de=prev_kept[2], idx_ate=i + 1,
                                     linear='sim' if lin else 'NAO', commits=n, importados=imp,
                                     commits_validos=n - imp))
                if not lin:
                    log(f'  !! NOT LINEAR {prev_kept[0]} -> {t}')
            prev_kept = (t, snap, i + 1)
    kept = [r for r in map_rows if r['feature'] == feat and r['status'] == 'snapshot']
    ints = [r for r in int_rows if r['feature'] == feat]
    log(f'  snapshots: {len(kept)} (duplicates removed: '
        f'{sum(1 for r in map_rows if r["feature"] == feat and r["status"].startswith("duplicata"))}) | '
        f'prod .java {kept[0]["java_producao"]} -> {kept[-1]["java_producao"]} | '
        f'interval commits {sum(r["commits"] for r in ints)} (imported excluded: {sum(r["importados"] for r in ints)})')


def dump(name, rows):
    """Writes output/<name>; when only some features were run, replaces just their rows in the existing file."""
    path = OUT / name
    if only and path.exists():
        old = [r for r in csv.DictReader(open(path, encoding='utf-8')) if r['feature'] not in only]
        order = list(FEATURES)
        rows = sorted(old + rows, key=lambda r: order.index(r['feature']))
    if rows:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)


dump('presenca.csv', pres_rows)
dump('mapeamento.csv', map_rows)
dump('intervalos.csv', int_rows)
with open(OUT / 'mapear.log', 'a' if only else 'w', encoding='utf-8') as f:
    f.write(('\n\n# rerun: ' + ', '.join(only) + '\n' if only else '') + '\n'.join(LOG))
