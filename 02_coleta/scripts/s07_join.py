"""Step 7 - Join CK + Understand + evometrics + ChangeDistiller (same logic as the pilot's s07_join.py).

As in the pilot: inner join on method_name per release; will_change = TOTAL_CHANGES > median(TOTAL_CHANGES of the
release) computed per feature and release; keys duplicated inside one source are discarded; constructors and
anonymous/local-class methods excluded; the last snapshot has no label.
Added: columns `feature`, `repository` and `method_uid` = "<repository>::<method_name>" (unique across features,
the same method_name can exist in different repositories). The CK column `line` is kept in the dataset as in the
pilot, but must stay out of the model features (decision D6).
Outputs: data/<slug>-all-releases.parquet and data/join_audit.csv (match rates per release).
"""
import re

import numpy as np
import pandas as pd

from config import parse_args, slug
from features import FEATURES, is_template
from methods_lib import norm_type

P = parse_args(__doc__)


def split_top(s):
    """Split on top-level commas (ignores commas inside <...>)."""
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch == '<':
            depth += 1
        elif ch == '>':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur)
            cur = ''
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


def ck_key(cls, method):
    if '$Anonymous' in cls:
        return None
    name, _, rest = method.partition('/')
    m = re.match(r'\d+(\[(.*)\])?$', rest)
    params = split_top(m.group(2)) if m and m.group(2) else []
    return f'{cls.replace("$", ".")}.{name}({",".join(norm_type(p) for p in params)})'


def und_key(name):
    if '(Anon_' in name:
        return None
    m = re.match(r'^(.*?)\((.*)\)$', name)
    if not m:
        return None
    params = split_top(m.group(2)) if m.group(2) else []
    return f'{m.group(1)}({",".join(norm_type(p) for p in params)})'


def dedup(df, key, audit, src):
    dup = df[key].duplicated(keep=False)
    audit[f'{src}_dup_discarded'] = int(dup.sum())
    return df[~dup]


def load_ck(rel, commit):
    df = pd.read_csv(P.data / 'ck' / f'{rel:02d}_{commit}_method.csv', index_col=False)
    df = df[df['constructor'] == False]  # noqa: E712
    df['method_name'] = [ck_key(c, m) for c, m in zip(df['class'], df['method'])]
    return df[df['method_name'].notna()]


def load_und(rel, commit):
    df = pd.read_csv(P.data / 'understand' / f'{rel:02d}_{commit}.csv', dtype=str, keep_default_na=False)
    df = df[df['Kind'].str.contains('Method') & ~df['Kind'].str.contains('Implicit') & (df['File'] != '')]
    df = df.copy()
    df['method_name'] = [und_key(n) for n in df['Name']]
    df = df[df['method_name'].notna()]
    for c in df.columns.difference(['Kind', 'Name', 'File', 'method_name']):
        df[c] = pd.to_numeric(df[c].str.replace(',', '.'), errors='coerce')   # Understand writes decimal commas
    return df


if __name__ == '__main__':
    tl = pd.read_csv(P.data / 'timeline.csv')
    evo = pd.read_parquet(P.data / 'evometrics.parquet')
    cd = pd.read_parquet(P.data / 'change_distiller.parquet')
    out, audits = [], []
    for _, r in tl.iterrows():
        rel, commit = int(r['release']), r['commit']
        a = {'release': rel, 'tag': r['tag']}
        ck = dedup(load_ck(rel, commit), 'method_name', a, 'ck')
        und = dedup(load_und(rel, commit), 'method_name', a, 'und')
        ev = evo[evo['release'] == rel]
        tpl = ev['file'].map(is_template)                 # M22: code-generation templates are not product code
        a['template_methods_excluded'] = int(tpl.sum())
        ev = ev[~tpl]
        dex = FEATURES[P.feature].get('dataset_exclude')  # M25: feature-specific test fixtures (JDT modules/)
        if dex:
            fx = ev['file'].str.contains(dex, regex=True)
            a['fixture_methods_excluded'] = int(fx.sum())
            ev = ev[~fx]
        c = cd[cd['CURRENT_COMMIT'] == commit]
        a.update(ck=len(ck), und=len(und), evo=len(ev), cd=len(c))
        a['ck_in_evo'] = ck['method_name'].isin(ev['method_name']).mean()
        a['und_in_evo'] = und['method_name'].isin(ev['method_name']).mean()
        a['evo_in_ck'] = ev['method_name'].isin(ck['method_name']).mean()
        a['evo_in_und'] = ev['method_name'].isin(und['method_name']).mean()
        j = ck.merge(und, on='method_name', how='inner', suffixes=('', '_und'))
        a['ck_und'] = len(j)
        j = j.merge(ev.drop(columns=['file']), on='method_name', how='inner')
        a['ck_und_evo'] = len(j)
        if len(c):
            j = j.merge(c.drop(columns=['PROJECT_NAME']), on='method_name', how='inner')
            j['will_change'] = np.where(j['TOTAL_CHANGES'] > j['TOTAL_CHANGES'].median(), 1, 0)
            a['final'] = len(j)
            a['median_total_changes'] = j['TOTAL_CHANGES'].median()
            a['positives'] = int(j['will_change'].sum())
            out.append(j)
        else:
            a['final'] = 0          # last snapshot: no next snapshot -> no label
        audits.append(a)
        print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in a.items()}, flush=True)

    df = pd.concat(out, ignore_index=True)
    df['hasJavaDoc'] = df['hasJavaDoc'].astype(int)
    df.insert(0, 'method_uid', df['repository'] + '::' + df['method_name'])
    df.to_parquet(P.data / f'{slug(P.feature)}-all-releases.parquet', index=False)
    pd.DataFrame(audits).to_csv(P.data / 'join_audit.csv', index=False)
    print('final dataset:', df.shape, '| positives:', int(df['will_change'].sum()),
          f'({100 * df["will_change"].mean():.2f}%)')
