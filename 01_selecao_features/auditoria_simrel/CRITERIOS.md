# Critérios de presença no simrel e de evolução das features (auditável)

Todos os comandos abaixo são somente de leitura e foram executados em 2026-10-12 sobre:
- `simrel.build`: clone de `https://github.com/eclipse-simrel/simrel.build` (HEAD `c6e54875`, 2026-10-08);
- `1-Repositorios/<repo>`: clones dos repositórios das features.

Os caminhos são relativos à raiz do projeto (`TCC-LPS-Prediction/`).

---

## 1. Definição operacional
**Feature da LPS Eclipse IDE na release *t*:** um componente cuja contribuição está **presente, referenciada e
habilitada** na configuração de agregação do Eclipse Simultaneous Release (simrel) no commit que define a release *t*.

O critério de corte da série temporal de cada feature é **somente a presença** (seção 3). As evidências de evolução
(seção 5) não definem o corte: servem para explicar por que a feature saiu e para descrever ameaças à validade.

## 2. Unidade de análise: a release do simrel
Cada release é uma **tag** do `simrel.build`. A data da release é a data de commit do commit apontado pela tag.

```bash
# lista as tags em ordem cronológica, com a data do commit
for t in $(git -C simrel.build tag); do
  echo "$(git -C simrel.build show -s --format='%ct %cs' "$t^{commit}") $t"; done | sort -n | cut -d' ' -f2-
```

Conferência com o mapeamento: o `simrel_commit` de cada JSON do mapeamento é o commit da tag homônima
(**61 de 61 releases idênticas, 0 divergências**):

```bash
for f in 3-Mapeamento_features_simrel/simrel_mapper/output/*.json; do
  r=$(basename "$f" .json)
  c=$(grep -m1 '"simrel_commit"' "$f" | sed 's/.*: "\(.*\)".*/\1/')
  [ "$c" = "$(git -C simrel.build rev-list -1 "refs/tags/$r")" ] || echo "DIVERGE $r"
done
```

## 3. Critérios de presença (aplicados a cada release *t*)
A agregação do simrel é definida por um arquivo principal (`simrel.b3aggr` até 2016, `simrel.aggr` depois), que
referencia um arquivo de contribuição por projeto (`<projeto>.b3aggrcon` / `<projeto>.aggrcon`).

| Critério | Pergunta | Comando (para a tag `$t` e o arquivo `$f`) |
|---|---|---|
| **C1** | O arquivo de contribuição existe na release? | `git -C simrel.build ls-tree --name-only "$t^{commit}" \| grep -E '^birt\.(b3)?aggrcon$'` |
| **C2** | Ele é referenciado pela agregação? | `git -C simrel.build show "$t:simrel.aggr" \| grep "href=\"$f#"` (até 2016: `simrel.b3aggr`) |
| **C3** | A contribuição está habilitada? | `git -C simrel.build show "$t:$f" \| grep -oE '<aggregator:Contribution[^>]*>'`: ausência de `enabled="false"` |
| **C4** | (Só quando a feature vem dentro da contribuição de outro projeto, como o CVS no Platform.) A feature p2 está listada e habilitada? | `git -C simrel.build show "$t:ep.aggrcon" \| grep 'name="org.eclipse.cvs.feature.group"'` |

**Presente em *t*** ⇔ C1 ∧ C2 ∧ C3 (∧ C4, quando aplicável).

Verificações adicionais feitas em todas as 61 releases do mapeamento: nenhum arquivo de contribuição presente deixou
de estar referenciado (C1 ⇒ C2 sempre), e nenhum `validationSet` do arquivo principal estava desabilitado.

O script `presenca.sh` (nesta pasta) aplica C1–C4 a todas as tags e gera um TSV por feature:

```bash
export SIMREL=simrel.build
bash 5-Coleta_features/auditoria_simrel/presenca.sh '^birt\.(b3)?aggrcon$'          > birt.tsv
bash 5-Coleta_features/auditoria_simrel/presenca.sh '^eclipse[lL]ink\.(b3)?aggrcon$' > eclipselink.tsv
bash 5-Coleta_features/auditoria_simrel/presenca.sh '^subversive\.(b3)?aggrcon$'    > subversive.tsv
bash 5-Coleta_features/auditoria_simrel/presenca.sh '^ptp\.(b3)?aggrcon$'           > ptp.tsv
bash 5-Coleta_features/auditoria_simrel/presenca.sh '^mylyn\.(b3)?aggrcon$'         > mylyn.tsv
bash 5-Coleta_features/auditoria_simrel/presenca.sh '^rap\.(b3)?aggrcon$'           > rap_runtime.tsv
bash 5-Coleta_features/auditoria_simrel/presenca.sh '^ep\.(b3)?aggrcon$' org.eclipse.cvs.feature.group > cvs.tsv
```

### Resultado (transições de estado; TSVs completos nesta pasta)
`[C1,C2,C3,C4]` como impresso pelo script:

| Feature | Presente em | Ausente a partir de | Estado na transição | Lacunas internas |
|---|---|---|---|---|
| BIRT | JunoSR0 (2012-08-03) | **2020-12** (2020-12-09) | `[nao,-,-,-]`: arquivo removido | OxygenPreRienaRemoval_9-8-2016 `[sim,sim,nao]` |
| EclipseLink | JunoSR0 | **LunaRC4** (2014-09-17) | `[nao,-,-,-]` | — |
| Subversive | JunoSR0 | **PhotonM7** (2018-05-17) | `[sim,sim,nao]`: desabilitado; arquivo removido depois | OxygenPreRienaRemoval_9-8-2016 |
| PTP | JunoSR0 | **2026-03** (2026-03-11) | `[nao,-,-,-]` | — |
| Mylyn | JunoSR0 | — | — | **2022-06 → 2023-03** `[sim,sim,nao]` (desabilitado); volta em 2023-06 |
| RAP Runtime (`rap.aggrcon`) | JunoSR0 | **2025-09** (2025-09-05) | `[nao,-,-,-]` (o `rap-tools.aggrcon` continua) | — |
| CVS (dentro do `ep.aggrcon`) | JunoSR0 | **2022-03** (2022-03-15) | `[sim,sim,sim,nao]`: feature retirada da contribuição do Platform | — |

Observação: a tag `OxygenPreRienaRemoval_9-8-2016` registra um estado intermediário do simrel em que várias
contribuições estavam desabilitadas ao mesmo tempo. Ela não é uma release distribuída (ver análise do mapeamento, P2).

## 4. Evento de saída (commit que retira a feature) e motivo registrado

```bash
git -C simrel.build log --all --diff-filter=D --format='%h %cs %an | %s' -- 'birt.*aggrcon'
git -C simrel.build log --all --diff-filter=D --format='%h %cs %an | %s' -- 'eclipse?ink.*aggrcon'
git -C simrel.build log --all --diff-filter=D --format='%h %cs %an | %s' -- 'subversive.*aggrcon'
git -C simrel.build log --all --diff-filter=D --format='%h %cs %an | %s' -- 'ptp.*aggrcon'
git -C simrel.build log --all --diff-filter=D --format='%h %cs %an | %s' -- 'rap.aggrcon'
git -C simrel.build log --all --format='%h %cs %an | %s' -S'org.eclipse.cvs.feature.group' -- ep.aggrcon ep.b3aggrcon
git -C simrel.build log --all --format='%h %cs %an | %s' -G'Contribution.*enabled="false"' -- mylyn.aggrcon
git -C simrel.build log --all --format='%h %cs %an | %s' -G'Contribution.*enabled="false"' -- subversive.aggrcon subversive.b3aggrcon
git -C simrel.build show -s --format='%h %cs %an%n%B' <commit>      # mensagem completa
```

Saídas obtidas:

| Feature | Commit | Data | Autor | Mensagem |
|---|---|---|---|---|
| BIRT | `3e248d33` | 2020-11-25 | Jonah Graham | Bug 569180: Remove BIRT from SimRel |
| EclipseLink | `a9ad600f` / `c1335055` | 2014-08-20 | David Williams | Bug 442174 - remove eclipselink b3aggrcon file from Luna (and Mars) |
| Subversive (desabilitação) | `86cba8ab` | 2018-01-30 | Frederic Gurr | Disable Subversive contribution (and EMF Diffmerge until it's fixed) |
| Subversive (remoção) | `1374e999` | 2018-11-30 | Wayne Beaton | eGerrit, Sapphire and Subversive have dropped out of the simrel. |
| PTP | `3b1d0f16` | 2026-02-06 | Ed Merks | Remove ptp.aggrcon and reconcile simrel.aggran. |
| RAP Runtime | `d4525d15` | 2025-08-20 | Markus Knauer | Remove RAP Runtime validation set from SimRel contribution (#987): "RAP Tools remain in SimRel" |
| CVS | `3fc26371` | 2022-01-07 | Kit Lo | Eclipse and Equinox contribution for SimRel 2022-03 M1 (remove `org.eclipse.cvs.feature.group`) |
| Mylyn (desabilitação) | `35d10c5a` | 2022-03-29 | Jonah Graham | Bug 569078: Disable Mylyn from SimRel |
| Mylyn (reabilitação) | `20266fef` | 2023-05-04 | Alexander Fedorov | Mylyn 3.26.0 RC2 to SimRel 2023-06 M2 |

As datas dos commits de remoção são anteriores às releases em que a feature aparece ausente na seção 3, o que é
consistente: uma remoção em nov/2020 vale a partir da release seguinte (2020-12).

## 5. Evidências de evolução (descritivas; não definem o corte)

### 5a. Evolução do que foi distribuído: o build contribuído muda entre releases?
O build distribuído é identificado pelo update site (`location`) e pelas versões fixadas (`versionRange`) na
contribuição. Mesmo identificador em releases consecutivas = nenhum código novo distribuído.

```bash
for t in Oxygen 2018-09 2019-06 2019-12 2020-09; do
  git -C simrel.build show "$t:birt.aggrcon" | grep -oE 'versionRange="[^"]+"' | sort -u; done
# saída em todas: versionRange="4.7.0.v201706142203"   (o mesmo build do BIRT de jun/2017 até a remoção)

for t in 2021-09 2023-12 2025-12; do
  git -C simrel.build show "$t:ptp.aggrcon" | grep -oE 'location="[^"]+"'; done
# saída em todas: location="https://download.eclipse.org/tools/ptp/builds/9.4/2021-09"
```

Tabela completa, release a release e para todas as features: `5-Coleta_features/inventario/sim_contrib.json`
(gerado por `inventario/sim_contrib.py`) e `inventario/sim_vs_map.csv` (colunas `location`, `build_ts`).

### 5b. Evolução do código no repositório (linha principal)
```bash
git -C 1-Repositorios/<repo> log -1 --format='%h %cs' origin/HEAD                     # último commit
git -C 1-Repositorios/<repo> rev-list --count --no-merges --since=<data> origin/HEAD   # commits após a saída
```

| Repositório | Último commit | Commits (sem merge) após a saída do simrel |
|---|---|---|
| birt | `d0e6e0929c` 2026-10-10 | 752 desde 2020-11-25 |
| eclipselink | `64f96f8d5f` 2026-10-09 | 1.965 desde 2014-08-20 |
| ptp | `47cda24d7` 2021-08-31 | 0 desde 2021-09-30 |
| org.eclipse.rap | `b0830aae7` 2026-10-07 | (o runtime continua no repositório do projeto) |
| org.eclipse.team.cvs (fork) | `265ca4883` 2026-07-30 | só commits do fork depois de 2022-02 (ver seção CVS de `Analise_Timeline_Projetos.md`) |

Interpretação: **presença no simrel e evolução do código são independentes.** Projetos saíram do simrel e continuaram
evoluindo fora dele (BIRT, EclipseLink, RAP Runtime), e projetos ficaram no simrel sem evoluir (PTP: último commit em
2021-08; mesmo build redistribuído até 2025-12; BIRT: mesmo build de 2017 a 2020). Por isso o corte usa a presença
(definição da LPS), e a ausência de evolução é tratada à parte (deduplicação de snapshots idênticos, ameaças à validade).

## 5c. Auditoria manual no PowerShell (Windows), testada
Todos os comandos rodam **dentro do `simrel.build`** (não no repositório da feature). No PowerShell: usar
`"${t}:arquivo"` (e não `"$t:arquivo"`, que vira referência de variável) e `Select-String` no lugar de `grep`.

```powershell
Set-Location "C:\Users\Kevin Strey\Desktop\TCC-LPS-Prediction\simrel.build"

# Evento de saída
git log --all --diff-filter=D --format='%h %cs %an | %s' -- 'birt.*aggrcon'
git show -s --format='%h %cs %an%n%B' 3e248d33

# C1: o arquivo existe antes da saída e não existe depois
git ls-tree --name-only 2020-09 | Select-String '^birt\.'      # -> birt.aggrcon
git ls-tree --name-only 2020-12 | Select-String '^birt\.'      # -> (vazio)

# C2: referenciado pela agregação (até 2016: simrel.b3aggr e birt.b3aggrcon)
git show 2020-09:simrel.aggr | Select-String 'birt.aggrcon'    # -> <contributions href="birt.aggrcon#/"/>

# C3: habilitado (tag raiz sem enabled="false")
foreach ($t in '2022-03','2022-06','2023-06') {
  $l = git show "${t}:mylyn.aggrcon" | Select-String 'aggregator:Contribution '; "$t -> $l" }
# -> 2022-06 contém enabled="false"; 2022-03 e 2023-06 não

# C4 (CVS dentro da contribuição do Platform)
foreach ($t in '2021-12','2022-03') {
  $n = (git show "${t}:ep.aggrcon" | Select-String 'org.eclipse.cvs.feature.group').Count; "$t -> $n" }
# -> 2021-12: 1, 2022-03: 0

# Build distribuído repetido (evidência de não evolução)
git show 2019-06:birt.aggrcon | Select-String 'versionRange'   # -> 4.7.0.v201706142203

# Data de uma release (data do commit da tag)
git log -1 --format='%h %cs' 2020-12
```

## 6. Limitações
1. **Configuração ≠ artefato publicado:** os critérios verificam a configuração da agregação, não o repositório p2
   publicado em `download.eclipse.org`. Uma contribuição habilitada pode, em tese, ter falhado no build agregado.
2. **Tags como releases:** algumas tags do simrel não correspondem a releases distribuídas
   (`OxygenPreRienaRemoval_9-8-2016`, `PhotonM7`, `KeplerPostRC4`, `z20140805-2300`, `z20140806`), e algumas releases
   reais não têm tag (Kepler SR2, Mars, Mars.2).
3. **Branches do simrel:** releases de manutenção são tagueadas em branches de manutenção do simrel. Uma mudança no
   `main` só vale para as releases seguintes desse stream (ex.: a desabilitação do Subversive em 2018-01 não afeta a
   Oxygen.3, de 2018-03, que é do branch de manutenção do Oxygen).
4. **Motivos da saída:** as mensagens de commit registram o evento, mas nem sempre o motivo. Os bugs citados
   (569180, 442174, 569078) podem ser consultados no Bugzilla da Eclipse para a justificativa completa.
