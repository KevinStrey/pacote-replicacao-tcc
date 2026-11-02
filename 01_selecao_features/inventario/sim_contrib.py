"""What each feature actually contributed to each simrel release (read-only on simrel.build).

For every release JSON of the mapping, reads the feature's contribution file(s) (.b3aggrcon / .aggrcon)
at the simrel commit of that release and records: contribution enabled, repository locations
(+enabled), contributed features with versionRange (+enabled).
Output: sim_contrib.json  {feature: [{release, simrel_date, simrel_commit, files: {...}}]}
"""
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(r'C:\Users\Kevin Strey\Desktop\TCC-LPS-Prediction')
SIMREL = ROOT / 'simrel.build'
MAP = ROOT / '3-Mapeamento_features_simrel' / 'simrel_mapper' / 'output'

# feature -> regex of contribution file names (old b3aggrcon names and current aggrcon names)
FILES = {
    'BIRT': r'^birt\.', 'CDT': r'^cdt\.', 'DataTools': r'^dtp\.', 'EGit': r'^egit\.',
    'EMF': r'^(emf-emf|emf)\.', 'EclipseLink': r'^eclipse[lL]ink\.', 'GEF': r'^gef\.',
    'GMF Runtime': r'^(gmp-gmf-runtime|gmf-runtime)\.', 'JDT': r'^ep\.', 'PDE': r'^ep\.',
    'Mylyn': r'^mylyn\.', 'PTP': r'^ptp\.', 'RAP': r'^(rap|rap-tools)\.', 'Scout': r'^scout\.',
    'Subversive': r'^subversive\.', 'WebTools': r'^webtools\.', 'Window Builder': r'^windowbuilder\.',
    'm2e': r'^m2e\.',
}
EXT = re.compile(r'\.(b3)?aggrcon$')


def git(*a):
    return subprocess.run(['git', '-C', str(SIMREL), *a], capture_output=True, text=True,
                          encoding='utf-8', errors='replace').stdout


def local(tag):
    return tag.rsplit('}', 1)[-1]


def parse(xml):
    root = ET.fromstring(xml)
    out = {'enabled': root.get('enabled', 'true'), 'label': root.get('label'), 'repos': []}
    for rep in root:
        if local(rep.tag) != 'repositories':
            continue
        r = {'location': rep.get('location'), 'enabled': rep.get('enabled', 'true'), 'features': [],
             'n_bundles': 0, 'n_products': 0}
        for ch in rep:
            t = local(ch.tag)
            if t == 'features':
                r['features'].append((ch.get('name'), ch.get('versionRange'), ch.get('enabled', 'true')))
            elif t == 'bundles':
                r['n_bundles'] += 1
            elif t == 'products':
                r['n_products'] += 1
        out['repos'].append(r)
    return out


rels = []
for f in MAP.glob('*.json'):
    d = json.loads(f.read_text(encoding='utf-8'))
    rels.append((d['date'], d['release'], d['simrel_commit']))
rels.sort()

res = {k: [] for k in FILES}
for date, rel, sc in rels:
    names = [n for n in git('ls-tree', '--name-only', sc).splitlines() if EXT.search(n)]
    for feat, pat in FILES.items():
        files = {}
        for n in names:
            if re.match(pat, n):
                try:
                    files[n] = parse(git('show', f'{sc}:{n}'))
                except ET.ParseError as e:
                    files[n] = {'error': str(e)}
        res[feat].append({'release': rel, 'simrel_date': date, 'simrel_commit': sc, 'files': files})
    print(rel, sc[:8], len(names), flush=True)

Path(sys.argv[1]).write_text(json.dumps(res, indent=1), encoding='utf-8')
