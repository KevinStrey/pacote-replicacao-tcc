"""Step 7 - Join CK + Understand + evometrics + ChangeDistiller (cpmp/6.join_metrics).

As in the original: inner join on method_name, per release;
will_change = TOTAL_CHANGES > median(TOTAL_CHANGES of the release).
Differences: a single method_name normalization for every source (methods_lib),
discarding of keys duplicated within one source (overloads that become
indistinguishable after normalization), and constructors / anonymous-class
methods excluded (the original extractor only considered MethodDeclaration).
Outputs: data/egit-all-releases.csv and data/join_audit.csv (match rates).
"""
import re

import numpy as np
import pandas as pd

from config import DATA
from methods_lib import norm_type

CK_METRICS = ['line', 'cbo', 'cboModified', 'fanin', 'fanout', 'wmc',
              'rfc', 'loc', 'returnsQty', 'variablesQty', 'parametersQty', 'methodsInvokedQty',
              'methodsInvokedLocalQty', 'methodsInvokedIndirectLocalQty', 'loopQty', 'comparisonsQty',
              'tryCatchQty', 'parenthesizedExpsQty', 'stringLiteralsQty', 'numbersQty', 'assignmentsQty',
              'mathOperationsQty', 'maxNestedBlocksQty', 'anonymousClassesQty', 'innerClassesQty', 'lambdasQty',
              'uniqueWordsQty', 'modifiers', 'logStatementsQty', 'hasJavaDoc']


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
    df = pd.read_csv(DATA / 'ck' / f'{rel:02d}_{commit}_method.csv', index_col=False)
    df = df[df['constructor'] == False]  # noqa: E712
    df['method_name'] = [ck_key(c, m) for c, m in zip(df['class'], df['method'])]
    return df[df['method_name'].notna()]


def load_und(rel, commit):
    df = pd.read_csv(DATA / 'understand' / f'{rel:02d}_{commit}.csv', dtype=str, keep_default_na=False)
    df = df[df['Kind'].str.contains('Method') & ~df['Kind'].str.contains('Implicit') & (df['File'] != '')]
    df = df.copy()
    df['method_name'] = [und_key(n) for n in df['Name']]
    df = df[df['method_name'].notna()]
    for c in df.columns.difference(['Kind', 'Name', 'File', 'method_name']):
        df[c] = pd.to_numeric(df[c].str.replace(',', '.'), errors='coerce')
    return df


if __name__ == '__main__':
    tl = pd.read_csv(DATA / 'timeline.csv')
    evo = pd.read_csv(DATA / 'evometrics.csv')
    cd = pd.read_csv(DATA / 'change_distiller.csv', low_memory=False)
    out, audits = [], []
    for _, r in tl.iterrows():
        rel, commit = int(r['release']), r['commit']
        a = {'release': rel}
        ck = dedup(load_ck(rel, commit), 'method_name', a, 'ck')
        und = dedup(load_und(rel, commit), 'method_name', a, 'und')
        ev = evo[evo['commit'] == commit]
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
            a['final'] = 0  # last release: no next release -> no label
        audits.append(a)
        print(a, flush=True)

    df = pd.concat(out, ignore_index=True)
    df['hasJavaDoc'] = df['hasJavaDoc'].astype(int)
    df.to_csv(DATA / 'egit-all-releases.csv', index=False)
    pd.DataFrame(audits).to_csv(DATA / 'join_audit.csv', index=False)
    print('final dataset:', df.shape, '| positives:', int(df['will_change'].sum()),
          f'({100 * df["will_change"].mean():.2f}%)')
