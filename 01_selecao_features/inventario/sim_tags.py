"""Resolve the commit actually shipped in each simrel release through the repository tags, and compare
it with the commit chosen by the mapper.

Tag resolution (in this order):
 1. tags whose name contains a build timestamp of the contribution (YYYYMMDDHHMM or YYYYMMDD-HHMM),
    taken from feature qualifiers and repository locations (except aggregated train repos);
 2. tags whose name encodes the contributed version X.Y[.Z] (from the location path or the feature
    versions), with an optional prefix (R, V, v, CDT_, R_, ...) and no RC/M/beta suffix.
Relation mapper x shipped: same | mapper ahead (shipped is an ancestor; n commits) |
mapper behind | divergent (different branches) | no tag.
Output: sim_tags.csv
"""
import csv
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(r'C:\Users\Kevin Strey\Desktop\TCC-LPS-Prediction')
REPOS = ROOT / '1-Repositorios'
MAP = ROOT / '3-Mapeamento_features_simrel' / 'simrel_mapper' / 'output'
HERE = Path(__file__).resolve().parent
ALIAS = {'eclipse.cvs': 'org.eclipse.team.cvs'}
TRAIN = re.compile(r'/releases/(juno|kepler|luna|mars|neon|oxygen|photon|20\d\d-\d\d)/', re.I)
TS12 = re.compile(r'(?<!\d)(20\d{6})(\d{4})(?:\d{2})?(?!\d)')
TS84 = re.compile(r'(?<!\d)(20\d{6})-(\d{4})(?!\d)')
VER = re.compile(r'(?<![\d.])(\d+)\.(\d+)(?:\.(\d+))?(?![\d])')
BAD = re.compile(r'(rc|m\d|beta|alpha|snapshot|nightly|milestone)', re.I)


def git(repo, *a):
    return subprocess.run(['git', '-C', str(repo), *a], capture_output=True, text=True,
                          encoding='utf-8', errors='replace').stdout.strip()


_tags = {}


def tags(repo):
    if repo not in _tags:
        out = {}
        for line in git(repo, 'for-each-ref', 'refs/tags', '--format=%(refname:short)\t%(objectname)\t%(*objectname)').splitlines():
            n, o, p = (line.split('\t') + ['', ''])[:3]
            out[n] = p or o
        _tags[repo] = out
    return _tags[repo]


def ts_keys(s):
    keys = set()
    for m in TS12.finditer(s):
        keys |= {m.group(1) + m.group(2), f'{m.group(1)}-{m.group(2)}'}
    for m in TS84.finditer(s):
        keys |= {m.group(1) + m.group(2), f'{m.group(1)}-{m.group(2)}'}
    return keys


def ver_regex(x, y, z):
    zpart = rf'[._]{z}' if z and z != '0' else (r'([._]0)?' if z == '0' or not z else '')
    return re.compile(rf'^[A-Za-z_]*[-_]?v?{x}[._]{y}{zpart}([._-]?(R|r|Release.*|SR\d*|final))?$')


contrib = json.loads((HERE / 'sim_contrib.json').read_text(encoding='utf-8'))
mapping = {}
for f in MAP.glob('*.json'):
    d = json.loads(f.read_text(encoding='utf-8'))
    for k, m in d['mappings'].items():
        mapping[(k, d['release'])] = m

rows = []
for feat, rels in contrib.items():
    for r in rels:
        m = mapping[(feat, r['release'])]
        repo = REPOS / ALIAS.get(m['repository'], m['repository'])
        T = tags(repo)
        keys, vers = set(), []
        enabled = False
        for x in r['files'].values():
            if x.get('enabled') != 'true':
                continue
            enabled = True
            for rep in x['repos']:
                if rep['enabled'] != 'true':
                    continue
                loc = rep['location'] or ''
                if not TRAIN.search(loc):
                    keys |= ts_keys(loc)
                    vers += VER.findall(loc.split('eclipse.org')[-1])
                for _, vr, en in rep['features']:
                    if en == 'true' and vr:
                        keys |= ts_keys(vr)
                        vers += VER.findall(vr.split(',')[0])
        tag, how = None, ''
        if enabled:
            hits = sorted(n for n in T if any(k in n for k in keys))
            if hits:
                tag, how = hits[0], 'timestamp'
            else:
                seen = []
                for v in sorted(set(vers), key=lambda v: (-len([p for p in v if p]), vers.index(v))):
                    if v in seen:
                        continue
                    seen.append(v)
                    rx = ver_regex(*v)
                    hits = sorted(n for n in T if rx.match(n) and not BAD.search(n))
                    if hits:
                        tag, how = hits[0], 'versão ' + '.'.join(p for p in v if p)
                        break
        c = m['commit']
        rel_s, ahead, behind = '', '', ''
        sc = T.get(tag) if tag else None
        if sc and git(repo, 'cat-file', '-t', c) == 'commit':
            if sc == c:
                rel_s = 'igual'
            else:
                b, a = git(repo, 'rev-list', '--left-right', '--count', f'{sc}...{c}').split()
                ahead, behind = int(a), int(b)
                rel_s = ('mapper à frente' if behind == 0 else
                         'mapper atrás' if ahead == 0 else 'divergente')
        elif enabled:
            rel_s = 'sem tag'
        else:
            rel_s = 'fora do simrel' if not r['files'] else 'contrib. desativada'
        rows.append({'feature': feat, 'release': r['release'], 'simrel_date': r['simrel_date'][:10],
                     'tag_distribuida': tag or '', 'resolvida_por': how,
                     'commit_distribuido': (sc or '')[:9],
                     'data_distribuido': git(repo, 'show', '-s', '--format=%cs', sc) if sc else '',
                     'commit_mapper': c[:9], 'data_mapper': git(repo, 'show', '-s', '--format=%cs', c),
                     'relacao': rel_s, 'mapper_commits_a_mais': ahead, 'mapper_commits_a_menos': behind})
    print(feat, flush=True)

with open(HERE / 'sim_tags.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
