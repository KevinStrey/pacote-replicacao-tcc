"""Inventory step D: evaluate a candidate generic test rule on the first/last linear snapshot of every feature."""
import json, re, subprocess, sys
from collections import Counter
from pathlib import Path

REPOS = Path(r'C:\Users\Kevin Strey\Desktop\TCC-LPS-Prediction\1-Repositorios')
inv = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
TESTISH = re.compile(r'(test|junit)', re.I)
# candidate rule: a directory named like a test dir, or a bundle whose dot-tokens contain a test token
DIRNAMES = {'test', 'tests', 'testsuites', 'junit', 'src-test', 'src_test', 'unittest', 'test-src', 'testsrc'}
TOKENS = {'test', 'tests', 'junit', 'junit4', 'junit5', 'testhelper', 'testapps', 'testing', 'testsuite', 'testsuites',
          'testfixture', 'testenvironment', 'testutils', 'testplugin', 'testplugins'}

def is_test_dir(c):
    lc = c.lower()
    return lc in DIRNAMES or bool(TOKENS & set(lc.split('.')))

def classify(p):
    for c in p.split('/')[:-1]:
        if is_test_dir(c):
            return 'rule', c
    for c in p.split('/')[:-1]:
        if TESTISH.search(c):
            return 'testish_not_rule', c
    return 'prod', None

for feat, r in inv.items():
    repo = REPOS / r['folder']
    print(f'\n######## {feat}')
    for lab, (rel, c) in (('FIRST', r['first']), ('LAST', r['last'])):
        fs = [p for p in subprocess.run(['git', '-C', str(repo), 'ls-tree', '-r', '--name-only', c], capture_output=True,
              text=True, encoding='utf-8', errors='replace').stdout.splitlines() if p.endswith('.java')]
        cnt, comps, miss = Counter(), Counter(), Counter()
        for p in fs:
            k, comp = classify(p)
            cnt[k] += 1
            if k == 'rule':
                comps[comp] += 1
            elif k == 'testish_not_rule':
                miss[comp] += 1
        print(f'  {lab} {rel}: java={len(fs)} excluded_by_rule={cnt["rule"]} production={len(fs) - cnt["rule"]} testish_not_excluded={cnt["testish_not_rule"]}')
        print('     rule dirs:', ', '.join(f'{k}:{v}' for k, v in comps.most_common(14)))
        if miss:
            print('     NOT excluded (testish):', ', '.join(f'{k}:{v}' for k, v in miss.most_common(12)))
