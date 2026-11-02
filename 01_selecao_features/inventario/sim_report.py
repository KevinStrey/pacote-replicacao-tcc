"""Markdown tables per feature: periods of consecutive releases with the same shipped build, and how the
mapper's commits relate to it (from sim_vs_map.csv and sim_tags.csv). Output: sim_report.md"""
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
a = pd.read_csv(HERE / 'sim_vs_map.csv', dtype=str).fillna('')
b = pd.read_csv(HERE / 'sim_tags.csv', dtype=str).fillna('')
d = a.merge(b, on=['feature', 'release'], suffixes=('', '_t'))


def short(loc):
    loc = loc.split(' | ')[0].replace('https://', '').replace('http://', '')
    loc = loc.replace('download.eclipse.org/', '').rstrip('/')
    return loc[-55:]


out = []
for feat, g in d.groupby('feature', sort=False):
    g = g.reset_index(drop=True)
    key = []
    for _, r in g.iterrows():
        if r.no_simrel == 'NAO':
            key.append('fora do simrel')
        elif r.contrib_ativa == 'NAO':
            key.append('contribuição desativada')
        else:
            key.append(r.tag_distribuida or r.build_ts or short(r.location))
    g['key'] = key
    runs, start = [], 0
    for i in range(1, len(g) + 1):
        if i == len(g) or g.key[i] != g.key[start]:
            runs.append(g.iloc[start:i])
            start = i
    out.append(f'\n#### {feat}: períodos por build distribuído\n')
    out.append('| Releases | n | Distribuído (update site) | Build | Tag/commit distribuído | Commits distintos do mapper | Relação mapper × distribuído | Commits a mais no mapper (mediana/máx) |')
    out.append('|---|---|---|---|---|---|---|---|')
    for x in runs:
        f, l = x.release.iloc[0], x.release.iloc[-1]
        rng = f if f == l else f'{f} → {l}'
        r0 = x.iloc[0]
        rel = x.relacao.value_counts()
        rel_s = ', '.join(f'{k} ({v})' for k, v in rel.items())
        am = pd.to_numeric(x.mapper_commits_a_mais, errors='coerce').dropna()
        am_s = f'{am.median():.0f} / {am.max():.0f}' if len(am) else ''
        dist = (f'`{r0.tag_distribuida}` ({r0.data_distribuido})' if r0.tag_distribuida else '')
        out.append(f'| {rng} | {len(x)} | {short(r0.location) if r0.contrib_ativa == "sim" else r0.key} | '
                   f'{r0.build_ts} | {dist} | {x.commit_mapper.nunique()} | {rel_s} | {am_s} |')
(HERE / 'sim_report.md').write_text('\n'.join(out), encoding='utf-8')
print(len(out))
