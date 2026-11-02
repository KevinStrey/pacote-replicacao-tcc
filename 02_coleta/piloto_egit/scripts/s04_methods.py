"""Step 4 - Method inventory (batch JMethodsExtractor equivalent).

1. For each snapshot: list of production .java files and their blobs.
2. For each interval (release r-1, release r]: non-merge commits and, for each
   commit, the production .java files modified relative to the first parent
   (with rename detection), with old/new blobs.
3. Writes every unique blob to work/blobs and extracts its methods once
   (MethodsBatch.java, same extraction logic as cpmp's JMethodsExtractor).

Outputs:
  data/methods/snapshot_files.csv   release, path, blob
  data/methods/commit_changes.csv   release, commit, parent, status, old_path, new_path, old_blob, new_blob
  data/methods/blob_methods.jsonl   methods per blob (raw)
"""
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from config import DATA, JAVA, JME_JAR, REPO, WORK, is_production_java

OUT = DATA / 'methods'
BLOBS = WORK / 'blobs'
JAVA_DIR = __import__('pathlib').Path(__file__).resolve().parent / 'java'
NULL_SHA = '0' * 40


def git(*args):
    return subprocess.run(['git', '-C', str(REPO), *args], capture_output=True, text=True,
                          check=True, encoding='utf-8').stdout


def snapshot_files(tl):
    rows = []
    for _, r in tl.iterrows():
        for line in git('ls-tree', '-r', r['commit']).splitlines():
            meta, path = line.split('\t', 1)
            _, typ, sha = meta.split()
            if typ == 'blob' and is_production_java(path):
                rows.append((r['release'], r['commit'], path, sha))
    return pd.DataFrame(rows, columns=['release', 'commit', 'path', 'blob'])


def commit_changes(tl):
    rows = []
    commits = list(tl['commit'])
    for i in range(1, len(commits)):
        rel = int(tl['release'].iloc[i])
        # chronological order (topological), first-parent diff, merges excluded
        revs = git('rev-list', '--reverse', '--topo-order', '--no-merges',
                   f'{commits[i - 1]}..{commits[i]}').split()
        for c in revs:
            parents = git('rev-list', '--parents', '-n', '1', c).split()[1:]
            if not parents:
                continue
            out = git('diff-tree', '-r', '-M', '--no-commit-id', '--raw', parents[0], c)
            for line in out.splitlines():
                meta, *paths = line.split('\t')
                _, _, old_blob, new_blob, status = meta.split()
                status = status[0]
                old_path = paths[0]
                new_path = paths[1] if len(paths) > 1 else paths[0]
                if status == 'A':
                    old_path = None
                if status == 'D':
                    new_path = None
                if not ((old_path and is_production_java(old_path)) or (new_path and is_production_java(new_path))):
                    continue
                rows.append((rel, c, parents[0], status, old_path, new_path,
                             None if old_blob == NULL_SHA else old_blob,
                             None if new_blob == NULL_SHA else new_blob))
    return pd.DataFrame(rows, columns=['release', 'commit', 'parent', 'status', 'old_path', 'new_path',
                                       'old_blob', 'new_blob'])


def dump_blobs(shas):
    BLOBS.mkdir(parents=True, exist_ok=True)
    todo = [s for s in shas if not (BLOBS / f'{s}.java').exists()]
    if not todo:
        return
    p = subprocess.run(['git', '-C', str(REPO), 'cat-file', '--batch'], input='\n'.join(todo).encode() + b'\n',
                       capture_output=True, check=True)
    data, pos = p.stdout, 0
    for s in todo:
        nl = data.index(b'\n', pos)
        header = data[pos:nl].split()
        size = int(header[2])
        (BLOBS / f'{s}.java').write_bytes(data[nl + 1: nl + 1 + size])
        pos = nl + 1 + size + 1


def extract(shas, n_jobs=4):
    chunks = [shas[i::n_jobs] for i in range(n_jobs)]
    cp = f'{JME_JAR};{JAVA_DIR}'

    def run(i):
        man = OUT / f'manifest_{i}.tsv'
        man.write_text('\n'.join(f'{s}\t{BLOBS / (s + ".java")}' for s in chunks[i]), encoding='utf-8')
        out = OUT / f'blob_methods_{i}.jsonl'
        subprocess.run([JAVA, '-Xmx2g', '-cp', cp, 'MethodsBatch', str(man), str(out)], check=True)
        return out

    with ThreadPoolExecutor(n_jobs) as ex:
        parts = list(ex.map(run, range(n_jobs)))
    with open(OUT / 'blob_methods.jsonl', 'w', encoding='utf-8') as f:
        for part in parts:
            f.write(part.read_text(encoding='utf-8'))
            part.unlink()
            (OUT / f'manifest_{parts.index(part)}.tsv').unlink()


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    tl = pd.read_csv(DATA / 'timeline.csv')
    sf = snapshot_files(tl)
    sf.to_csv(OUT / 'snapshot_files.csv', index=False)
    print('snapshot files:', len(sf), 'unique blobs:', sf['blob'].nunique())
    cc = commit_changes(tl)
    cc.to_csv(OUT / 'commit_changes.csv', index=False)
    print('file changes in commits:', len(cc), 'commits:', cc['commit'].nunique())
    print(cc['status'].value_counts().to_string())
    shas = sorted(set(sf['blob']) | set(cc['old_blob'].dropna()) | set(cc['new_blob'].dropna()))
    print('unique blobs total:', len(shas))
    dump_blobs(shas)
    extract(shas)
    n_ok = n_fail = 0
    with open(OUT / 'blob_methods.jsonl', encoding='utf-8') as f:
        for line in f:
            d = json.loads(line)
            n_ok += d['ok']
            n_fail += not d['ok']
    print(f'parse ok: {n_ok}  failures: {n_fail}')
