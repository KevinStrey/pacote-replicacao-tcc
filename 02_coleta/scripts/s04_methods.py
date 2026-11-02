"""Step 4 - Method inventory (batch JMethodsExtractor equivalent) and commit changes per interval.

1. For each snapshot: production .java files and their blobs (M9/M10/M14 rule of the feature).
2. For each interval (release r_prev, release r]: non-merge commits, EXCLUDING commits of histories imported by
   merge (M6: a commit counts only if it descends from a root of the previous snapshot's history), and, for each
   commit, the production .java files modified relative to its (only) parent, with rename detection (-M).
   Pilot: 2 git calls per commit (rev-list --parents + diff-tree). Here: one `git log --raw -M --no-merges` per
   interval (same diff: for a non-merge commit, --raw shows the diff against its single parent).
3. Writes every unique blob to work/blobs and extracts its methods once with MethodsBatch.java (same extraction as
   cpmp's JMethodsExtractor, JavaParser JAVA_17), RESOURCES['JVM_WORKERS'] JVMs in parallel.
4. Streams the JSON output into the method store (methods_lib.build_store: sqlite texts + compact index).
Outputs: data/methods/snapshot_files.csv, commit_changes.csv, interval_commits.csv, blob_methods.jsonl,
         method_texts.sqlite, blob_index.pkl, methods_stats.json
"""
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from config import JAVA, JAVA_DIR, JME_JAR, RESOURCES, parse_args
from methods_lib import build_store

P = parse_args(__doc__)
OUT = P.data / 'methods'
BLOBS = P.work / 'blobs'
NULL_SHA = '0' * 40


def git(*args):
    return subprocess.run(['git', '-C', str(P.repo), *args], capture_output=True, text=True, check=True,
                          encoding='utf-8', errors='replace').stdout


def snapshot_files(tl):
    rows = []
    for _, r in tl.iterrows():
        for line in git('ls-tree', '-r', r['commit']).splitlines():
            meta, path = line.split('\t', 1)
            _, typ, sha = meta.split()
            if typ == 'blob' and P.is_production_java(path):
                rows.append((r['release'], r['commit'], path, sha))
    return pd.DataFrame(rows, columns=['release', 'commit', 'path', 'blob'])


def valid_commits(prev, cur):
    """Non-merge commits of prev..cur that descend from a root of prev's history (M6), and the imported ones."""
    allc = git('rev-list', '--no-merges', f'{prev}..{cur}').split()
    desc = set()
    for root in git('rev-list', '--max-parents=0', prev).split():
        desc |= set(git('rev-list', '--no-merges', '--ancestry-path', f'{root}..{cur}').split())
    return [c for c in allc if c in desc], [c for c in allc if c not in desc]


def commit_changes(tl):
    rows, audit = [], []
    rel, commits = list(tl['release']), list(tl['commit'])
    for i in range(1, len(commits)):
        valid, imported = valid_commits(commits[i - 1], commits[i])
        valid_set = set(valid)
        audit.append({'release': rel[i], 'prev_release': rel[i - 1], 'commits': len(valid) + len(imported),
                      'valid': len(valid), 'imported_excluded': len(imported)})
        # chronological (topological) order, as in the pilot
        out = git('log', '--reverse', '--topo-order', '--no-merges', '-M', '--raw', '--no-abbrev',
                  '--format=%x00%H %P', f'{commits[i - 1]}..{commits[i]}')
        for block in out.split('\x00')[1:]:
            lines = block.strip('\n').split('\n')
            c, *parents = lines[0].split()
            if c not in valid_set or not parents:
                continue
            for line in lines[1:]:
                if not line.startswith(':'):
                    continue
                meta, *paths = line.split('\t')
                _, _, old_blob, new_blob, status = meta.split()
                status = status[0]
                old_path = paths[0]
                new_path = paths[1] if len(paths) > 1 else paths[0]
                if status == 'A':
                    old_path = None
                if status == 'D':
                    new_path = None
                if not ((old_path and P.is_production_java(old_path)) or (new_path and P.is_production_java(new_path))):
                    continue
                rows.append((rel[i], c, parents[0], status, old_path, new_path,
                             None if old_blob == NULL_SHA else old_blob, None if new_blob == NULL_SHA else new_blob))
    cc = pd.DataFrame(rows, columns=['release', 'commit', 'parent', 'status', 'old_path', 'new_path', 'old_blob',
                                     'new_blob'])
    return cc, pd.DataFrame(audit)


def dump_blobs(shas):
    BLOBS.mkdir(parents=True, exist_ok=True)
    todo = [s for s in shas if not (BLOBS / f'{s}.java').exists()]
    for k in range(0, len(todo), 5000):           # chunks keep the cat-file output in memory bounded
        chunk = todo[k:k + 5000]
        p = subprocess.run(['git', '-C', str(P.repo), 'cat-file', '--batch'], input='\n'.join(chunk).encode() + b'\n',
                           capture_output=True, check=True)
        data, pos = p.stdout, 0
        for s in chunk:
            nl = data.index(b'\n', pos)
            size = int(data[pos:nl].split()[2])
            (BLOBS / f'{s}.java').write_bytes(data[nl + 1: nl + 1 + size])
            pos = nl + 1 + size + 1


def extract(shas):
    n_jobs = max(1, min(RESOURCES['JVM_WORKERS'], len(shas) // 200 + 1))
    chunks = [shas[i::n_jobs] for i in range(n_jobs)]
    cp = f'{JME_JAR};{JAVA_DIR}'

    def run(i):
        man = OUT / f'manifest_{i}.tsv'
        man.write_text('\n'.join(f'{s}\t{BLOBS / (s + ".java")}' for s in chunks[i]), encoding='utf-8')
        out = OUT / f'blob_methods_{i}.jsonl'
        subprocess.run([JAVA, f'-Xmx{RESOURCES["JVM_XMX"]}', '-cp', cp, 'MethodsBatch', str(man), str(out)],
                       check=True)
        man.unlink()
        return out

    with ThreadPoolExecutor(n_jobs) as ex:
        parts = list(ex.map(run, range(n_jobs)))
    with open(OUT / 'blob_methods.jsonl', 'w', encoding='utf-8') as f:
        for part in parts:
            with open(part, encoding='utf-8') as g:
                for line in g:
                    f.write(line)
            part.unlink()


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    tl = pd.read_csv(P.data / 'timeline.csv')
    sf = snapshot_files(tl)
    sf.to_csv(OUT / 'snapshot_files.csv', index=False)
    print('snapshot files:', len(sf), 'unique blobs:', sf['blob'].nunique(), flush=True)
    cc, audit = commit_changes(tl)
    cc.to_csv(OUT / 'commit_changes.csv', index=False)
    audit.to_csv(OUT / 'interval_commits.csv', index=False)
    print('file changes:', len(cc), '| commits with production changes:', cc['commit'].nunique(),
          '| imported commits excluded:', int(audit['imported_excluded'].sum()) if len(audit) else 0, flush=True)
    shas = sorted(set(sf['blob']) | set(cc['old_blob'].dropna()) | set(cc['new_blob'].dropna()))
    print('unique blobs total:', len(shas), flush=True)
    dump_blobs(shas)
    extract(shas)
    stats = build_store(OUT / 'blob_methods.jsonl', OUT / 'method_texts.sqlite', OUT / 'blob_index.pkl')
    (OUT / 'methods_stats.json').write_text(json.dumps(stats, indent=1), encoding='utf-8')
    print('parse ok:', stats['parse_ok'], ' failures:', stats['parse_fail'], '| store:', dict(stats))
