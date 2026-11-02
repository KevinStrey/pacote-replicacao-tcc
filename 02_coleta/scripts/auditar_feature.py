"""Per-feature audit -> <feature>/AUDITORIA.md (same checks recorded in the pilot's AUDITORIA.md).

1. Timeline: snapshots, period, presence gaps crossed, commits per interval (valid / imported excluded, M6).
2. JavaParser parse failures (pilot: 0).
3. ChangeDistiller errors (pilot: 0).
4. Join match rates (join_audit.csv; pilot ~100%).
5. Positives per release.
6. Spot check of the evolutionary metrics against `git log -L`: for the method (unique name in its file) with the
   most changing commits, the commits counted by s05 must be contained in the commits that `git log -L` reports
   for its line range (git's heuristic over-approximates: it also lists changes to neighbouring lines).
Usage: python auditar_feature.py --feature CVS
"""
import json
import sys
import re
import subprocess

import pandas as pd

from config import MAPPING_CSV, parse_args, slug

P = parse_args(__doc__)
D = P.data
tl = pd.read_csv(D / 'timeline.csv')
m = pd.read_csv(MAPPING_CSV)
mf = m[m.feature == P.feature]
stats = json.loads((D / 'methods' / 'methods_stats.json').read_text(encoding='utf-8'))
ic = pd.read_csv(D / 'methods' / 'interval_commits.csv')
ja = pd.read_csv(D / 'join_audit.csv')
s06_log = (D / 's06_change_distiller.log').read_text(encoding='utf-8') if (D / 's06_change_distiller.log').exists() else ''
cd_err = re.search(r'CDERROR: (\d+)', s06_log)
cd_calls = re.search(r'ChangeDistiller calls: (\d+)', s06_log)
final = pd.read_parquet(D / f'{slug(P.feature)}-all-releases.parquet', columns=['release', 'will_change'])
ck_err = sorted(p.name for p in (D / 'ck').glob('*.log') if 'Exception' in p.read_text(encoding='utf-8', errors='replace'))
und_n = len(list((D / 'understand').glob('*.csv')))

# ---- spot check ----
ch = pd.read_parquet(D / 'method_changes.parquet')
evo = pd.read_parquet(D / 'evometrics.parquet', columns=['release', 'method_name', 'file'])
spot = ['(sem mudanças no período)']
if len(ch):
    last_seen = evo.drop_duplicates('method_name', keep='last').set_index('method_name')
    last_file = last_seen['file']
    names = evo.drop_duplicates(['file', 'method_name'])
    names = names.assign(simple=names.method_name.str.extract(r'\.([^.(]+)\(')[0])
    unique = names.groupby(['file', 'simple']).method_name.transform('nunique') == 1
    ok = set(names[unique].method_name)
    counts = ch[ch.method_name.isin(ok)].groupby('method_name').commit.nunique().sort_values(ascending=False)
    if len(counts):
        key = counts.index[0]
        path = last_file[key]
        simple = re.search(r'\.([^.(]+)\(', key).group(1)
        # last snapshot in which the method still exists (it may have been removed/renamed later)
        first = tl.commit.iloc[0]
        last = tl.loc[tl.release == int(last_seen.loc[key, 'release']), 'commit'].iloc[0]
        ours = set(ch[ch.method_name == key].commit)
        # explicit line range of the DECLARATION in the last snapshot (a `-L:<name>:` regex can match a call site):
        # the declaration line contains `<name>(` preceded by a type/modifier and is not a statement (no `;`
        # before the brace); the end is found by brace balance (braces inside strings/comments ignored roughly)
        src_txt = subprocess.run(['git', '-C', str(P.repo), 'show', f'{last}:{path}'], capture_output=True,
                                 text=True, encoding='utf-8', errors='replace').stdout.splitlines()
        # declaration = [annotations] (type/modifier tokens followed by whitespace)+ name( ; a call such as
        # `name(...)`, `this.name(`, `x = name(` or `return name(` has no type token right before the name
        decl = re.compile(rf'^\s*(?:@[\w.]+(?:\([^)]*\))?\s+)*(?:[\w$<>\[\],.?]+\s+)+{re.escape(simple)}\s*\(')
        start = next((i for i, l in enumerate(src_txt) if decl.search(l)
                      and not re.match(r'\s*(return|new|else|throw|case)\b', l)), None)
        end, depth, opened = None, 0, False
        if start is not None:
            for i in range(start, len(src_txt)):
                code = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//.*', '', src_txt[i])
                depth += code.count('{') - code.count('}')
                opened = opened or '{' in code
                if opened and depth <= 0:
                    end = i
                    break
        # the method text (JavaParser toString, as in the pilot) includes annotations and Javadoc: extend the range
        # upwards over the annotation lines and the Javadoc block right above the declaration
        if start is not None:
            k = start - 1
            while k >= 0 and src_txt[k].strip().startswith('@'):
                k -= 1
            if k >= 0 and src_txt[k].strip().endswith('*/'):
                while k >= 0 and not src_txt[k].strip().startswith('/**'):
                    k -= 1
                k -= 1
            start = k + 1
        rng = f'{start + 1},{end + 1}' if start is not None and end is not None else ''
        out = subprocess.run(['git', '-C', str(P.repo), 'log', '--no-merges', '--format=%H', '--no-patch',
                              f'-L{rng}:{path}', f'{first}..{last}'], capture_output=True, text=True,
                             encoding='utf-8', errors='replace') if rng else None
        theirs = set(out.stdout.split()) if out else set()
        spot = [f'Método: `{key}` (arquivo `{path}`, linhas {rng or "não localizadas"} em {last[:10]})',
                f'Comando: `git -C 1-Repositorios/{P.repository} log --no-merges --format=%H --no-patch '
                f'-L{rng}:{path} {first[:10]}..{last[:10]}`'
                + (f' (stderr: {out.stderr.strip()[:200]})' if out is not None and out.returncode else ''),
                f'Commits contados pela s05: {len(ours)} | listados pelo `git log -L`: {len(theirs)} | '
                f'em comum: {len(ours & theirs)} | contados e não listados: {len(ours - theirs)}',
                'Resultado: ' + ('**OK** (todos os commits contados estão no `git log -L`; os demais do git são '
                                  'mudanças em linhas vizinhas ou só de comentário/formatação)'
                                  if ours <= theirs else '**VERIFICAR** (commits contados fora do `git log -L`: '
                                  + ', '.join(c[:10] for c in sorted(ours - theirs)[:10]) + ')')]

pos = final.groupby('release').will_change.agg(['size', 'sum', 'mean']).reset_index()
pos = pos.merge(tl[['release', 'tag']], on='release')
lines = [f'# Auditoria da coleta: {P.feature} (`1-Repositorios/{P.repository}`)', '',
         'Gerado por `scripts/auditar_feature.py`. Decisões: `5-Coleta_features/INVENTARIO.md` (M1–M18); '
         'recursos e equivalência com o piloto: `5-Coleta_features/RECURSOS.md`.', '',
         '## 1. Linha do tempo',
         f'- Snapshots: **{len(tl)}** ({tl.tag.iloc[0]} → {tl.tag.iloc[-1]}; índices globais '
         f'{tl.release.min()}..{tl.release.max()}); datas do calendário na série: {len(mf)}; duplicatas removidas: '
         f'{int(mf.status.str.startswith("duplicata").sum())}; lacunas de presença atravessadas: '
         f'{int((mf.presente != "sim").sum())}.',
         f'- História linear verificada (s00). .java de produção: {tl.java_producao.iloc[0]} → {tl.java_producao.iloc[-1]}.',
         f'- Commits nos intervalos: {int(ic.commits.sum())}; válidos: {int(ic.valid.sum())}; importados por merge e '
         f'excluídos (M6): {int(ic.imported_excluded.sum())}.', '',
         '## 2. Falhas de parsing do JavaParser (piloto: 0)',
         f'- Versões de arquivo únicas: {stats["blobs"]}; **falhas: {stats.get("parse_fail", 0)}**; métodos (sem anônimos/'
         f'locais): {stats["methods"]}; descartados por chave duplicada no arquivo: {stats.get("duplicate_key", 0)}; '
         f'textos distintos: {stats["distinct_texts"]}.', '',
         '## 3. ChangeDistiller (piloto: 0 erros)',
         f'- Chamadas: {cd_calls.group(1) if cd_calls else "?"}; **erros (CDERROR): {cd_err.group(1) if cd_err else "?"}**.',
         f'- CK: logs com exceção: {len(ck_err)} {ck_err[:5] if ck_err else ""}; CSVs do Understand: {und_n} de {len(tl)}.',
         '', '## 4. Taxas de match no join (piloto: ~100%)',
         f'- Mínimo por release: evo_in_ck = {ja.evo_in_ck.min():.4f}, evo_in_und = {ja.evo_in_und.min():.4f}, '
         f'ck_in_evo = {ja.ck_in_evo.min():.4f}, und_in_evo = {ja.und_in_evo.min():.4f}.',
         f'- Média: evo_in_ck = {ja.evo_in_ck.mean():.4f}, evo_in_und = {ja.evo_in_und.mean():.4f}. '
         'Tabela completa: `data/join_audit.csv`.', '',
         '## 5. Dataset e positivos por release',
         f'- Linhas: **{len(final)}**; positivos: **{int(final.will_change.sum())}** '
         f'({100 * final.will_change.mean():.2f}%). A última release não tem rótulo.', '',
         '| Release (índice) | Tag | Métodos | Positivos | % |', '|---|---|---|---|---|']
lines += [f'| {r.release} | {r.tag} | {r["size"]} | {int(r["sum"])} | {100 * r["mean"]:.2f} |' for _, r in pos.iterrows()]
lines += ['', '## 6. Spot check das métricas evolutivas contra `git log -L`', *[f'- {s}' for s in spot], '']

# ---- 7. identity breaks (M28; produced by medir_identidade.py) ----
idm_p = D / 'identidade_metodos.csv'
if idm_p.exists():
    idm = pd.read_csv(idm_p)
    art = idm.born_moved + idm.born_imported
    sel = idm[(art >= 100) | (100 * art / idm.methods >= 1.0)]
    lines += ['## 7. Quebras de identidade de métodos (M28, ameaça à validade)',
              f'- Nascimentos após o 1º snapshot: {int(idm.born.sum())}; por mudança de pacote/classe: '
              f'{int(idm.born_moved.sum())}; em código importado (M6, heurística): {int(idm.born_imported.sum())}.',
              '- Efeito: histórico zerado (BOM = release da quebra; FRCH/CSB… recomeçam em 0) e método sem rótulo na '
              'transição. Detalhe: `data/identidade_metodos.csv`, `data/identidade_pares.csv`, '
              '`5-Coleta_features/AMEACA_identidade.md`.', '']
    if len(sel):
        lines += ['| Transição | Métodos | Nascidos / sumidos | Movidos | Importados |', '|---|---|---|---|---|']
        lines += [f'| {r.prev_tag} → {r.tag} | {r.methods} | {r.born} / {r.dead} | {r.born_moved} | {r.born_imported} |'
                  for r in sel.itertuples()]
    else:
        lines += ['- Nenhuma transição acima do limite (≥ 100 ou ≥ 1% dos métodos).']
    lines += ['']
(P.base / 'AUDITORIA.md').write_text('\n'.join(lines), encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')
print('\n'.join(lines))
