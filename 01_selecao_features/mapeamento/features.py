"""Per-feature configuration for the new temporal mapping (decisions M1–M16, 5-Coleta_features/INVENTARIO.md)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]            # TCC-LPS-Prediction
REPOS = ROOT / '1-Repositorios'
SIMREL = ROOT / 'simrel.build'
OUT = Path(__file__).resolve().parent / 'output'

# M2: simrel tags removed from the calendar (the other tags, in commit-date order, form the calendar)
TAGS_EXCLUDED = {
    'z20140805-2300': 'same simrel commit as LunaSR0 (492e3bf4)',
    'z20140806': 'same simrel commit as LunaSR0 (492e3bf4)',
    'Neon.1a': 'respin', 'Neon.3_respin': 'respin', 'Oxygen.1a_respin': 'respin', 'Oxygen.2_respin': 'respin',
    'OxygenPreRienaRemoval_9-8-2016': 'development point between Neon and Oxygen, not a release',
    'PhotonM7': 'milestone', 'PhotonRC4': 'release candidate 4 days before Photon.0',
}

# file: regex of the contribution file (C1-C3); p2: feature that must be listed and enabled (C4), when needed;
# ref: main line of the repository; start: first calendar tag of the series (M12, M15); scope: path filter (M14)
FEATURES = {
    # sample bundles shipped to users (Samples view, sample database ODA driver) are product code (author decision)
    'BIRT':           dict(repo='birt',                 file=r'^birt\.(b3)?aggrcon$',
                           keep_examples=r'^org\.eclipse\.birt\..*(samplesview|samples\.(ide|rcp)|sampledb|samplereports)'),
    # merge with inverted parents: 1st parent = imported org.eclipse.remote, 2nd parent = CDT (main line)
    'CDT':            dict(repo='cdt',                  file=r'^cdt\.(b3)?aggrcon$',
                           follow_parent2=['7c8bb9f00ef0d5e3ff493bc0c944519a3e476da2']),
    'CVS':            dict(repo='org.eclipse.team.cvs', file=r'^ep\.(b3)?aggrcon$', p2='org.eclipse.cvs.feature.group',
                           scope=r'^bundles/org\.eclipse\.(cvs|team\.cvs\.[^/]+)/'),
    'DataTools':      dict(repo='datatools',            file=r'^dtp\.(b3)?aggrcon$', start='Oxygen.3'),
    'EGit':           dict(repo='egit',                 file=r'^egit\.(b3)?aggrcon$'),
    'EMF':            dict(repo='org.eclipse.emf',      file=r'^(emf-emf|emf)\.(b3)?aggrcon$'),
    'EclipseLink':    dict(repo='eclipselink',          file=r'^eclipse[lL]ink\.(b3)?aggrcon$'),
    'GEF':            dict(repo='gef-classic',          file=r'^gef\.(b3)?aggrcon$', p2='org.eclipse.gef.sdk.feature.group'),
    'GMF Runtime':    dict(repo='gmf-runtime',          file=r'^(gmp-gmf-runtime|gmf-runtime)\.(b3)?aggrcon$'),
    # JCL/ = minimal JDK class libraries used only as test input (converterJclMin*)
    # modules/ = APT test fixture (Bug 517841), excluded at dataset level (M25)
    # ck_exclude: CK 0.7.1 crashes (NPE in its embedded JDT, switch expression) when OperandStack.java (created
    # 2024-05-07) is analysed together with CodeStream.java; the file is removed only from CK's input (M24)
    'JDT':            dict(repo='eclipse.jdt.core',     file=r'^ep\.(b3)?aggrcon$', p2='org.eclipse.jdt.feature.group',
                           exclude=r'^JCL/', dataset_exclude=r'^modules/',
                           ck_exclude=[r'^org\.eclipse\.jdt\.core\.compiler\.batch/src/org/eclipse/jdt/internal/'
                                       r'compiler/codegen/OperandStack\.java$']),
    'PDE':            dict(repo='eclipse.pde',          file=r'^ep\.(b3)?aggrcon$', p2='org.eclipse.pde.feature.group'),
    'Mylyn':          dict(repo='org.eclipse.mylyn',    file=r'^mylyn\.(b3)?aggrcon$', start='2023-06'),
    'PTP':            dict(repo='ptp',                  file=r'^ptp\.(b3)?aggrcon$'),
    'RAP':            dict(repo='org.eclipse.rap',      file=r'^rap\.(b3)?aggrcon$'),
    'Scout':          dict(repo='scout.rt',             file=r'^scout\.(b3)?aggrcon$', ref='origin/releases/27.1'),
    'Subversive':     dict(repo='subversive',           file=r'^subversive\.(b3)?aggrcon$'),
    'WebTools':       dict(repo='webtools.javaee',      file=r'^webtools\.(b3)?aggrcon$'),
    'Window Builder': dict(repo='windowbuilder',        file=r'^windowbuilder\.(b3)?aggrcon$'),
    'm2e':            dict(repo='m2e-core',             file=r'^m2e\.(b3)?aggrcon$'),
}

# --- production code (M9, M10); reproduces the pilot filter exactly on EGit ---
TEST_TOKENS = {'test', 'tests', 'junit', 'testing', 'testapps', 'testhelper', 'testsuite', 'testsuites'}
TEST_DIRS = {'test', 'tests', 'testsuites', 'unittest', 'src-test', 'src_test', 'testsrc', 'test-src', 'testdata'}
PKG_ROOTS = {'org', 'com', 'net', 'java', 'javax', 'jakarta', 'uk', 'junit', 'src', 'Eclipse UI'}
KEEP = re.compile(r'^(org\.eclipse\.pde\.junit\.runtime|org\.eclipse\.pde\.unittest\.junit|org\.eclipse\.rap\.junit(\.runtime)?)$')
MAVEN_TEST = re.compile(r'(^|/)src/(test|it)/')
EXAMPLE = re.compile(r'(example|sample|demo|tutorial|releng)', re.I)


def classify(path, feature=None):
    """'test', 'example' or 'prod' for a .java path (only directories before the package root are inspected)."""
    keep_ex = FEATURES.get(feature, {}).get('keep_examples')
    if MAVEN_TEST.search(path):
        return 'test'
    kept = False                                   # inside a sample bundle kept as product (keep_examples)
    for c in path.split('/')[:-1]:
        if c in PKG_ROOTS or c.startswith('src'):
            return 'test' if c in TEST_DIRS else 'prod'
        if KEEP.match(c):
            continue
        low = c.lower()
        if low in TEST_DIRS or TEST_TOKENS & set(low.split('.')):
            return 'test'
        if keep_ex and re.match(keep_ex, c):
            kept = True
        elif EXAMPLE.search(c) and not kept:
            return 'example'
    return 'prod'


_TEMPLATE_DIR = re.compile(r'^(templates?([_-][\w.]+)?|archetype-resources)$')


def is_template(path):
    """M22: code-generation templates (wizard templates_*, Maven archetype-resources, .java under
    src/main/resources) are not product code. Only directories BEFORE the package root are inspected, so Java
    packages named `templates` (real code) are not affected. Applied at dataset level (s07)."""
    path = path.replace('\\', '/')
    if '/src/main/resources/' in path or path.startswith('src/main/resources/'):
        return True
    for c in path.split('/')[:-1]:
        if c in PKG_ROOTS or c.startswith('src'):
            return False
        if _TEMPLATE_DIR.match(c):
            return True
    return False


def is_production_java(path, feature=None):
    if not path.endswith('.java') or classify(path, feature) != 'prod':
        return False
    cfg = FEATURES.get(feature, {})
    if cfg.get('exclude') and re.match(cfg['exclude'], path):
        return False
    return not cfg.get('scope') or re.match(cfg['scope'], path) is not None
