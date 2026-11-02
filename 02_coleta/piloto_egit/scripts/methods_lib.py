"""Method identification shared by evometrics, ChangeDistiller and the join.

Method key: <package>.<Outer>.<Inner>.<name>(<SimpleType1>,<SimpleType2>)
 - parameter types reduced to their simple name, without generics or annotations;
   varargs normalized to [];
 - methods of anonymous/local classes are discarded (no stable name, and CK and
   Understand name them inconsistently).
"""
import json
import re
from collections import Counter

from config import DATA

_ANNOT = re.compile(r'@[\w.]+(\([^()]*\))?\s*')
_GENERIC = re.compile(r'<[^<>]*>')


def norm_type(t: str) -> str:
    t = _ANNOT.sub('', t).replace('final ', '').strip()
    while '<' in t:
        new = _GENERIC.sub('', t)
        if new == t:
            break
        t = new
    t = t.replace('...', '[]').replace(' ', '')
    i = t.find('[')
    base, dims = (t, '') if i < 0 else (t[:i], t[i:])
    return base.rsplit('.', 1)[-1] + dims


def method_key(pkg, owner, name, params):
    prefix = f'{pkg}.{owner}' if pkg else owner
    return f'{prefix}.{name}({",".join(norm_type(p) for p in params)})'


def load_blob_methods(path=None):
    """blob -> {key: text}; also returns a counter of discards."""
    path = path or DATA / 'methods' / 'blob_methods.jsonl'
    blobs, stats = {}, Counter()
    with open(path, encoding='utf-8') as f:
        for line in f:
            d = json.loads(line)
            ms, dup = {}, set()
            for m in d['methods']:
                if m['owner'] is None:
                    stats['anonymous_or_local'] += 1
                    continue
                k = method_key(m['pkg'], m['owner'], m['name'], m['params'])
                if k in ms:
                    dup.add(k)
                ms[k] = m['text']
            for k in dup:
                del ms[k]
                stats['duplicate_key'] += 1
            stats['methods'] += len(ms)
            blobs[d['id']] = ms
    return blobs, stats
