"""Remove the review colours from LaTeX sources (\\laranja, \\azul, \\rosa, \\ciano, \\verdeescuro, \\verde,
\\color{ForestGreen|orange|red|blue|...} and \\captionsetup{font+={color=...}}), keeping the text.

 - {\\rosa texto}                 -> texto   (braces kept if the group has other declarations, e.g. \\scriptsize)
 - \\macro{\\rosa texto}           -> \\macro{texto}
 - \\begingroup\\rosa% ... \\endgroup -> ...   (the matching \\endgroup and a following {} are removed)
 - \\captionsetup{font+={color=X}}% -> (removed)
Design colours (figures, cover, code listings) are not touched: only the colours listed in COLORS.
Usage: python sem_cores.py <file or folder> [...]   (PacotesBasicos.tex, where the commands are defined, is skipped)
"""
import pathlib
import re
import sys

CMDS = ('verdeescuro', 'laranja', 'azul', 'rosa', 'ciano', 'verde')
COLORS = ('ForestGreen', 'orange', 'red', 'blue', 'rosa', 'ciano', 'verdeescuro')
MARK = re.compile(r'\\(?:%s)(?![A-Za-z])|\\color\{(?:%s)\}' % ('|'.join(CMDS), '|'.join(COLORS)))
CAPSET = re.compile(r'[ \t]*\\captionsetup\{font\+=\{color=(?:%s)\}\}%%?[ \t]*\n?' % '|'.join(COLORS))
DECL = re.compile(r'\\(?:tiny|scriptsize|footnotesize|small|normalsize|large|Large|LARGE|huge|Huge|bfseries|'
                  r'itshape|ttfamily|sffamily|rmfamily|mdseries|upshape|slshape|scshape|em|color|centering|'
                  r'raggedright|raggedleft|selectfont|fontsize|setlength|renewcommand|def|let)(?![A-Za-z])')


def match_brace(s, i):
    """Index of the '}' closing the '{' at s[i]."""
    depth = 0
    j = i
    while j < len(s):
        c = s[j]
        if c == '\\':
            j += 2
            continue
        if c == '%':
            j = s.find('\n', j)
            if j < 0:
                raise ValueError('unclosed group')
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return j
        j += 1
    raise ValueError('unclosed group')


def match_endgroup(s, i):
    depth = 1
    for m in re.finditer(r'\\(begingroup|endgroup)(?![A-Za-z])', s[i:]):
        depth += 1 if m.group(1) == 'begingroup' else -1
        if depth == 0:
            return i + m.start()
    raise ValueError('unclosed \\begingroup')


def is_bare_group(s, i):
    """True if the '{' at s[i] opens a plain group (not the argument of a command)."""
    k = i - 1
    if k < 0:
        return True
    c = s[k]
    if c in ']}*':
        return False
    if c.isalpha():
        j = k
        while j >= 0 and s[j].isalpha():
            j -= 1
        return not (j >= 0 and s[j] == '\\')
    return True


def in_comment(s, i):
    line_start = s.rfind('\n', 0, i) + 1
    k = line_start
    while k < i:
        if s[k] == '\\':
            k += 2
            continue
        if s[k] == '%':
            return True
        k += 1
    return False


def clean(s):
    s = CAPSET.sub('', s)
    pos = 0
    while True:
        m = MARK.search(s, pos)
        if not m:
            return s
        a, b = m.start(), m.end()
        if in_comment(s, a):
            pos = b
            continue
        is_word = not m.group().startswith('\\color{')
        # spaces after a control word are eaten by TeX; after \color{..} they are not
        e = b
        while e < len(s) and s[e] in ' \t':
            e += 1
        pre = s[:a].rstrip(' \t')
        if pre.endswith('\\begingroup'):
            g = len(pre) - len('\\begingroup')
            rest = s[e:]
            if rest.startswith('%'):
                nl = s.find('\n', e)
                e = nl + 1 if nl >= 0 else len(s)
            end = match_endgroup(s, e)
            tail = end + len('\\endgroup')
            if s.startswith('{}', tail):
                tail += 2
            s = s[:g] + s[e:end] + s[tail:]
            pos = g
            continue
        if a > 0 and s[a - 1] == '{':
            o = a - 1
            close = match_brace(s, o)
            inner = s[e:close]
            if is_bare_group(s, o) and not DECL.search(inner):
                s = s[:o] + inner + s[close + 1:]
                pos = o
                continue
            s = s[:a] + s[e:]
            pos = a
            continue
        keep_space = (not is_word) and e > b and a > 0 and s[a - 1] not in ' \t\n{'
        s = s[:a] + (' ' if keep_space else '') + s[e:]
        pos = a


def main(paths):
    total = 0
    for root in map(pathlib.Path, paths):
        files = [root] if root.is_file() else sorted(root.rglob('*.tex'))
        for f in files:
            if f.name == 'PacotesBasicos.tex':
                continue
            s = f.read_text(encoding='utf-8')
            n = len(MARK.findall(s)) + len(CAPSET.findall(s))
            if not n:
                continue
            t = clean(s)
            if t != s:
                f.write_text(t, encoding='utf-8', newline='')
                total += n
                print(f'{n:4d}  {f}')
    print('marcas removidas:', total)


if __name__ == '__main__':
    main(sys.argv[1:])
