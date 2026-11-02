"""Method identification shared by evometrics, ChangeDistiller and the join (same key as the pilot).

Method key: <package>.<Outer>.<Inner>.<name>(<SimpleType1>,<SimpleType2>)
 - parameter types reduced to their simple name, without generics or annotations; varargs normalized to [];
 - methods of anonymous/local classes are discarded; keys duplicated inside one file are discarded (as in the pilot).

Memory-efficient storage (difference from the pilot, same content): the pilot loaded every method text of every
blob into one dict (162 MB of JSON for EGit; several GB for CDT/BIRT). Here:
 - data/methods/method_texts.sqlite : text of each DISTINCT method text, keyed by a 16-byte BLAKE2b hash;
 - data/methods/blob_index.pkl      : blob -> {key: (hash, loc)}  (loc = number of lines of the text, the
                                      pilot's LOC_method), built while streaming blob_methods.jsonl.
Two method versions are "equal" iff their hashes are equal (same criterion as the pilot's text comparison).
"""
import hashlib
import json
import pickle
import re
import sqlite3
from collections import Counter

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


def text_hash(text):
    return hashlib.blake2b(text.encode('utf-8'), digest_size=16).digest()


def nloc(text):
    return len(text.splitlines())


def build_store(jsonl_path, db_path, index_path):
    """Streams blob_methods.jsonl -> sqlite texts + pickled index. Returns discard/parse statistics."""
    stats = Counter()
    con = sqlite3.connect(db_path)
    con.execute('PRAGMA journal_mode=OFF')
    con.execute('PRAGMA synchronous=OFF')
    con.execute('CREATE TABLE IF NOT EXISTS t (h BLOB PRIMARY KEY, text TEXT) WITHOUT ROWID')
    index, batch = {}, []
    with open(jsonl_path, encoding='utf-8') as f:
        for line in f:
            d = json.loads(line)
            stats['blobs'] += 1
            stats['parse_ok' if d['ok'] else 'parse_fail'] += 1
            ms, dup = {}, set()
            for m in d['methods']:
                if m['owner'] is None:
                    stats['anonymous_or_local'] += 1
                    continue
                k = method_key(m['pkg'], m['owner'], m['name'], m['params'])
                if k in ms:
                    dup.add(k)
                h = text_hash(m['text'])
                ms[k] = (h, nloc(m['text']))
                batch.append((h, m['text']))
            for k in dup:
                del ms[k]
                stats['duplicate_key'] += 1
            stats['methods'] += len(ms)
            index[d['id']] = ms
            if len(batch) > 20000:
                con.executemany('INSERT OR IGNORE INTO t VALUES (?, ?)', batch)
                batch = []
    con.executemany('INSERT OR IGNORE INTO t VALUES (?, ?)', batch)
    con.commit()
    stats['distinct_texts'] = con.execute('SELECT COUNT(*) FROM t').fetchone()[0]
    con.close()
    with open(index_path, 'wb') as f:
        pickle.dump(index, f, protocol=pickle.HIGHEST_PROTOCOL)
    return stats


def load_index(index_path):
    with open(index_path, 'rb') as f:
        return pickle.load(f)


class TextStore:
    """Read-only access to method texts by hash."""

    def __init__(self, db_path):
        self.con = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)

    def get(self, h):
        return self.con.execute('SELECT text FROM t WHERE h = ?', (h,)).fetchone()[0]


def snapshot_methods(sf_release_rows, index):
    """{key: (hash, loc, path)} for one snapshot; keys present in two files are dropped (pilot rule)."""
    present = {}
    for path, blob in sf_release_rows:
        for k, (h, loc) in index[blob].items():
            present[k] = None if k in present else (h, loc, path)
    return {k: v for k, v in present.items() if v is not None}
