"""Inventory step E: refined generic test rule; production .java per linear snapshot; check vs EGit pilot regex."""
import json, re, subprocess, sys
from pathlib import Path

REPOS = Path(r'C:\Users\Kevin Strey\Desktop\TCC-LPS-Prediction\1-Repositorios')
inv = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))

TEST_TOKENS = {'test', 'tests', 'junit', 'testing', 'testapps', 'testhelper', 'testsuite', 'testsuites'}
TEST_DIRS = {'test', 'tests', 'testsuites', 'unittest', 'src-test', 'src_test', 'testsrc', 'test-src', 'testdata'}
PKG_ROOTS = {'org', 'com', 'net', 'java', 'javax', 'jakarta', 'uk', 'junit', 'src', 'Eclipse UI'}
# production bundles that contain a test token (tools for running tests, shipped to users)
KEEP = re.compile(r'^(org\.eclipse\.pde\.junit\.runtime|org\.eclipse\.pde\.unittest\.junit|org\.eclipse\.rap\.junit(\.runtime)?)$')
MAVEN_TEST = re.compile(r'(^|/)src/(test|it)/')
EGIT = re.compile(r'^[^/]+\.(test|tests|junit)/')


def is_test(path):
    if MAVEN_TEST.search(path):
        return True
    for c in path.split('/')[:-1]:
        if c in PKG_ROOTS or c.startswith('src'):
            return c in TEST_DIRS
        if KEEP.match(c):
            continue
        if c.lower() in TEST_DIRS or TEST_TOKENS & set(c.lower().split('.')):
            return True
    return False


res = {}
for feat, r in inv.items():
    repo = REPOS / r['folder']
    counts = []
    for rel, c in r['chain']:
        fs = [p for p in subprocess.run(['git', '-C', str(repo), 'ls-tree', '-r', '--name-only', c], capture_output=True,
              text=True, encoding='utf-8', errors='replace').stdout.splitlines() if p.endswith('.java')]
        prod = [p for p in fs if not is_test(p)]
        if feat == 'EGit':
            assert len(prod) == sum(1 for p in fs if not EGIT.match(p)), (rel, len(prod))
        counts.append((rel, len(fs), len(prod)))
    res[feat] = counts
    print(feat, 'first', counts[0], 'last', counts[-1], 'sum_prod', sum(x[2] for x in counts), flush=True)
Path(sys.argv[2]).write_text(json.dumps(res), encoding='utf-8')
