"""M28 - Identity breaks of methods across consecutive snapshots (documentation only; no dataset is changed).

The method key is <package>.<Class>[.<Inner>].<name>(<simple param types>), independent of the file path. Moving a file
without changing its package keeps the key (history preserved). Changing the package or the class name, or importing
code from another repository (M6), creates keys that "are born" in the middle of the series: BOM = that release and
FRCH/CSB/... restart at 0 (history reset, not inflation), and the method has no label in that transition.

For each transition r_prev -> r of each feature:
  born / dead       keys present only in r / only in r_prev
  born_moved        born keys whose suffix <Class>.<name>(params) equals the suffix of a key that died in the same
                    transition (package/class rename or move)
  born_imported     the other born keys located in files that did not exist in r_prev, in an interval that has
                    commits of imported histories (M6) - heuristic, see AMEACA_identidade.md
Outputs: <feature>/data/identidade_metodos.csv, <feature>/data/identidade_pares.csv,
         5-Coleta_features/AMEACA_identidade.md (transitions with >= 100 artificial births or >= 1% of the methods)
Usage: python medir_identidade.py"""
from collections import Counter

import pandas as pd

from config import BASE, FEATURES, Paths

MIN_N, MIN_PCT = 100, 1.0


def suffix(k):
    head, params = k.split('(', 1)
    return '.'.join(head.rsplit('.', 2)[-2:]) + '(' + params


def owner(k):
    return k.split('(')[0].rsplit('.', 1)[0]


def package_of(k):
    """Package/class prefix before <Class>.<name>."""
    return k.split('(')[0].rsplit('.', 2)[0]


lines = []
for f in FEATURES:
    P = Paths(f)
    e = pd.read_parquet(P.data / 'evometrics.parquet', columns=['release', 'method_name', 'file'])
    sf = pd.read_csv(P.data / 'methods' / 'snapshot_files.csv', usecols=['release', 'path'])
    ic = pd.read_csv(P.data / 'methods' / 'interval_commits.csv')
    tl = pd.read_csv(P.data / 'timeline.csv').set_index('release')
    imp = dict(zip(ic.release, ic.imported_excluded))
    rels = sorted(e.release.unique())
    keys = {r: g.set_index('method_name')['file'].to_dict() for r, g in e.groupby('release')}
    paths = {r: set(g) for r, g in sf.groupby('release').path}
    rows, pairs = [], []
    for a, b in zip(rels, rels[1:]):
        born, dead = set(keys[b]) - set(keys[a]), set(keys[a]) - set(keys[b])
        dead_by_suf = {}
        for k in dead:
            dead_by_suf.setdefault(suffix(k), []).append(k)
        moved = set()
        for k in born:
            cand = dead_by_suf.get(suffix(k), [])
            if cand:
                moved.add(k)
                pairs.append(dict(release=b, tag=tl.loc[b, 'tag'], old_key=cand[0], new_key=k,
                                  old_prefix=package_of(cand[0]), new_prefix=package_of(k),
                                  old_file=keys[a][cand[0]], new_file=keys[b][k], ambiguous=len(cand) > 1))
        imported = {k for k in born - moved if imp.get(b, 0) > 0 and keys[b][k] not in paths.get(a, set())}
        rows.append(dict(release=b, tag=tl.loc[b, 'tag'], prev_release=a, prev_tag=tl.loc[a, 'tag'],
                         commit=tl.loc[b, 'commit'], prev_commit=tl.loc[a, 'commit'], methods=len(keys[b]),
                         born=len(born), dead=len(dead), born_moved=len(moved), born_imported=len(imported),
                         imported_commits=int(imp.get(b, 0))))
    d = pd.DataFrame(rows)
    d.to_csv(P.data / 'identidade_metodos.csv', index=False)
    pr = pd.DataFrame(pairs, columns=['release', 'tag', 'old_key', 'new_key', 'old_prefix', 'new_prefix', 'old_file',
                                      'new_file', 'ambiguous'])
    pr.to_csv(P.data / 'identidade_pares.csv', index=False)
    art = d.born_moved + d.born_imported
    sel = d[(art >= MIN_N) | (100 * art / d.methods >= MIN_PCT)]
    for r in sel.itertuples():
        top = Counter(zip(pr[pr.release == r.release].old_prefix, pr[pr.release == r.release].new_prefix))
        top_s = '<br>'.join(f'{n}× `{o}` → `{w}`' for (o, w), n in top.most_common(3)) or '—'
        cmd = (f'`git -C 1-Repositorios/{P.repository} diff -M --name-status {r.prev_commit[:10]} '
               f'{r.commit[:10]} | grep ^R`')
        lines.append(f'| {f} | {r.prev_tag} → {r.tag} ({r.prev_release}→{r.release}) | {r.methods} | {r.born} / {r.dead} '
                     f'| {r.born_moved} | {r.born_imported} | {100 * (r.born_moved + r.born_imported) / r.methods:.1f}% '
                     f'| {top_s} | {cmd} |')
    print(f'{f}: transições={len(d)} | nascidos={d.born.sum()} | movidos={d.born_moved.sum()} | '
          f'importados={d.born_imported.sum()} | transições na tabela={len(sel)}', flush=True)

doc = f"""# Ameaça à validade: quebras de identidade de métodos (M28)

Gerado por `scripts/medir_identidade.py`. Nenhum dataset foi alterado; este documento só registra onde ocorreu o efeito.

## Mecanismo
A chave do método é `<pacote>.<Classe>[.<Interna>].<nome>(<tipos simples dos parâmetros>)`, **independente do caminho
do arquivo** (diferente do cpmp, cuja chave inclui o caminho). Mover um arquivo de diretório mantendo o pacote preserva
o histórico. Duas situações, porém, criam chaves que "nascem" no meio da série:
1. **Renomeação/movimentação de pacote ou classe** (`born_moved`): o método reaparece com a mesma classe e assinatura em
   outro pacote/classe externa; o par chave antiga → chave nova está em `<feature>/data/identidade_pares.csv`
   (`ambiguous=True` quando havia mais de um candidato com o mesmo sufixo).
2. **Código importado de outro repositório** (`born_imported`, heurística): nascimentos em arquivos que não existiam no
   snapshot anterior, num intervalo com commits de históricos importados (M6).

## Efeito nas métricas
**O histórico é zerado, não inflado.** O commit que renomeia/move não conta mudança (a s05 só conta quando a mesma
chave existe antes e depois); os commits importados são excluídos (M6). O método aparece como novo (BOM = release da
quebra; FRCH, CSB, WCH, ATAF, LCH etc. recomeçam em 0) e, na transição da quebra, não tem rótulo (o ChangeDistiller
compara chaves iguais em r e r+1), ficando fora do dataset nessa release. Em gráficos agregados, isso aparece como pico
de BOM e queda de CSB.

## Transições afetadas (≥ {MIN_N} nascimentos artificiais ou ≥ {MIN_PCT:.0f}% dos métodos da release)
| Feature | Transição (índice global) | Métodos na release | Nascidos / sumidos | Movidos (pacote/classe) | Importados (M6) | Artificiais / release | Principais renomeações | Verificação |
|---|---|---|---|---|---|---|---|---|
""" + '\n'.join(lines) + """

## Observações
- DataTools: a consolidação dos repositórios (2018-01-16, ex.: `503b5d22`) é anterior ao 1º snapshot da série
  (Oxygen.3, M15); não gera nascimentos artificiais no meio da série.
- "Nascidos" também inclui métodos realmente novos e métodos com assinatura alterada (não distinguíveis de novos).
- Tabelas por transição: `<feature>/data/identidade_metodos.csv`; pares: `<feature>/data/identidade_pares.csv`.
"""
(BASE / 'AMEACA_identidade.md').write_text(doc, encoding='utf-8')
print('AMEACA_identidade.md:', len(lines), 'transições')
