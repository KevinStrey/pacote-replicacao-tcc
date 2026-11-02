"""Compare, per feature and simrel release, the build actually contributed to the simrel
(sim_contrib.json) with the commit chosen by the mapper (git log --all --until=<simrel date> -1).

Shipped build timestamp T: newest timestamp found in the enabled contribution, taken first from the
feature versionRanges (qualifiers), then from the repository locations (build ids), ignoring the
locations of aggregated train repos (releases/<train>/<ts>, used for respins), whose timestamp is
the train's and not the project's.
Output: sim_vs_map.csv
"""
import csv
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r'C:\Users\Kevin Strey\Desktop\TCC-LPS-Prediction')
REPOS = ROOT / '1-Repositorios'
MAP = ROOT / '3-Mapeamento_features_simrel' / 'simrel_mapper' / 'output'
HERE = Path(__file__).resolve().parent
ALIAS = {'eclipse.cvs': 'org.eclipse.team.cvs'}

TS12 = re.compile(r'(?<!\d)(20\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(?:\d{2})?(?!\d)')   # YYYYMMDDHHMM[SS]
TS8_4 = re.compile(r'(?<!\d)(20\d{2})(\d{2})(\d{2})-(\d{2})(\d{2})(?!\d)')            # YYYYMMDD-HHMM
TS8 = re.compile(r'(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)')                             # YYYYMMDD
TRAIN = re.compile(r'/releases/(juno|kepler|luna|mars|neon|oxygen|photon|20\d\d-\d\d)/', re.I)
VERLOC = re.compile(r'(?<![\d.])(\d+\.\d+(?:\.\d+)?)(?![\d])')


def stamps(s):
    out = []
    for rx in (TS12, TS8_4):
        for m in rx.finditer(s):
            y, mo, d, h, mi = map(int, m.groups()[:5])
            try:
                out.append(datetime(y, mo, d, h, mi, tzinfo=timezone.utc))
            except ValueError:
                pass
    if not out:
        for m in TS8.finditer(s):
            y, mo, d = map(int, m.groups())
            try:
                out.append(datetime(y, mo, d, tzinfo=timezone.utc))
            except ValueError:
                pass
    return out


def git(repo, *a):
    return subprocess.run(['git', '-C', str(repo), *a], capture_output=True, text=True,
                          encoding='utf-8', errors='replace').stdout.strip()


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
        c = m['commit']
        cdate = git(repo, 'show', '-s', '--format=%cI', c) or None
        present = bool(r['files'])
        enabled = present and any(x.get('enabled') == 'true' for x in r['files'].values())
        feat_ts, loc_ts, locs, vers = [], [], [], []
        for x in r['files'].values():
            if x.get('enabled') != 'true':
                continue
            for rep in x['repos']:
                if rep['enabled'] != 'true':
                    continue
                loc = rep['location'] or ''
                locs.append(loc)
                if not TRAIN.search(loc):
                    loc_ts += stamps(loc)
                    vers += VERLOC.findall(loc.split('download.eclipse.org')[-1])
                for _, vr, en in rep['features']:
                    if en == 'true' and vr:
                        feat_ts += stamps(vr)
        respin_only = bool(locs) and all(TRAIN.search(l) for l in locs)
        ts = max(feat_ts) if feat_ts else (max(loc_ts) if loc_ts else None)
        src = 'qualificador' if feat_ts else ('build id' if loc_ts else '')
        gap = None
        if ts and cdate:
            gap = (datetime.fromisoformat(cdate) - ts).total_seconds() / 86400
        rows.append({
            'feature': feat, 'release': r['release'], 'simrel_date': r['simrel_date'][:10],
            'no_simrel': 'sim' if present else 'NAO', 'contrib_ativa': 'sim' if enabled else 'NAO',
            'so_respin': 'sim' if respin_only else '',
            'build_ts': ts.strftime('%Y-%m-%d %H:%M') if ts else '', 'fonte_ts': src,
            'versao_loc': ' '.join(dict.fromkeys(vers))[:40],
            'commit_mapper': (c or '')[:9], 'data_commit_mapper': (cdate or 'AUSENTE')[:16],
            'gap_dias': f'{gap:.1f}' if gap is not None else '',
            'location': ' | '.join(locs)[:300],
        })

with open(HERE / 'sim_vs_map.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(len(rows), 'rows')
