
## Análise do mapeamento: demais features (repositórios clonados × `simrel.build`)

### Método
Scripts e saídas em `5-Coleta_features/inventario/` (somente leitura no git):
- `sim_contrib.py` → `sim_contrib.json`: para cada uma das 61 releases do mapeamento, lê no **commit do simrel daquela
  release** o arquivo de contribuição da feature (`*.b3aggrcon` até 2016, `*.aggrcon` depois) e extrai: contribuição
  ativa ou não, update sites (`repositories location`) e features contribuídas com `versionRange`.
- `sim_vs_map.py` → `sim_vs_map.csv`: timestamp do build distribuído (qualificador da versão ou ID do build no update
  site) × data do commit escolhido pelo mapper.
- `sim_tags.py` → `sim_tags.csv`: resolve o **commit distribuído** pelas tags do repositório (1º pelo timestamp do build,
  ex. `v7.0.0.202409031743-r`, `I20260226-0420`, `v201706142203`; 2º pela versão, ex. `R2_33_0`, `CDT_10_1_0`,
  `3.20.0-R`) e classifica a relação com o commit do mapper: **igual**, **mapper à frente** (o distribuído é ancestral
  do mapeado), **mapper atrás**, **divergente** (branches diferentes) ou **sem tag**.
- `sim_report.py` → tabelas de períodos abaixo.

Confiança da resolução por tag: exata quando achada pelo timestamp. Aproximada quando achada pela versão, porque a tag
de release costuma ficar 1–2 commits depois do build RC contribuído (ex.: RAP, "mapper atrás 1" = commit de release).

### Problemas transversais (com evidência)

**P1. O mapper pega o último commit de qualquer ref, não o código distribuído.**
`git log --all --date-order --until=<data do commit do simrel> -1` (`simrel_mapper/main.py:85-91`).
Das 709 releases ativas em que o commit distribuído foi resolvido, o mapper coincide em **17,5%**, está **à frente**
(código de desenvolvimento posterior ao build distribuído) em **47,5%**, **diverge** (outro branch) em **29,2%** e
está atrás em 5,8%. Padrões:
- *Pós-build*: o simrel agrega o build RC/R semanas antes da data da tag do simrel; o mapper inclui o que entrou depois
  no `master` (desenvolvimento da versão seguinte). Ex.: JDT 2026-03 distribuiu `I20260226-0420` (base do R-4.39);
  o mapper pegou `c9cb9ed5` (2026-03-09), 15 commits depois, e o campo `version` do mapeamento diz `I20260309-1800`.
- *Releases de manutenção*: SR1/SR2 e `.1/.2/.3` saem de branches de manutenção (`R4_x_maintenance`, `cdt_10_1`,
  `stable-4.0`…), mas o mapper pega o commit mais recente entre todos os refs, geralmente no `master`. Ex.: JDT
  Oxygen.1 distribuiu `M20170906-1700` (branch 4.7.x); o mapper pegou o `master` (4.8), **399 commits** divergentes.
- *Branches arbitrários*: qualquer branch com commit recente vence (Scout `features/...`, m2e `bugfix/...`,
  JDT `manoj_544073_yield`, EclipseLink `2.6_WAS`).

**P2. O conjunto de releases vem das 63 tags do `simrel.build`, que não são todas releases.**
- Triplicata: `LunaSR0`, `z20140805-2300` e `z20140806` usam o **mesmo commit do simrel** (`492e3bf4`).
- Nomes que não correspondem ao conteúdo: `LunaRC4` = Luna SR1 (set/2014); `S201504150911` = build intermediário do
  Mars (abr/2015); `OxygenPreRienaRemoval_9-8-2016` = ponto de desenvolvimento entre Neon e Oxygen; `PhotonM7` =
  milestone; `KeplerPostRC4` = pós-RC4 do Kepler.
- Releases reais sem tag, portanto ausentes: Kepler SR2 (fev/2014), Mars (jun/2015), Mars.2 (fev/2016).
- Tags novas `2026-06` e `2026-09` existem no `simrel.build` clonado, mas não estão no mapeamento.
- Respins (`Neon.1a`, `Neon.3_respin`, `Oxygen.1a`, `Mars.1`) apontam para o repositório agregado do trem
  (`releases/neon/2016...`), ou seja, redistribuem o conteúdo da release anterior.

**P3. Features fora do simrel (ou com contribuição desativada) recebem commits mesmo assim.**
`status=SUCCESS` em 100% porque o mapper não consulta o simrel.
- **EclipseLink**: no simrel só até LunaSR0; removido em 2014-08-20 (`a9ad600f`, Bug 442174). **52 de 61** releases
  mapeadas sem contribuição.
- **BIRT**: removido em 2020-11-25 (`3e248d33`, Bug 569180); **22 releases** (2020-12 → 2026-03) sem contribuição. De
  2019-12 a 2020-09, só a feature de gráficos.
- **Subversive**: desativado de PhotonM7 a 2018-09 e removido em 2018-11-30 (`1374e999`); **35 releases** sem contribuição.
- **PTP**: removido em 2026-02 (`3b1d0f16`). De 2023-12 em diante, só 1 feature.
- **Mylyn**: contribuição **desativada** de 2022-06 a 2023-03 (4 releases). **RAP Runtime**: removido em 2025-08; de
  2025-09 em diante só o RAP Tools (outro repositório).
- Desativações pontuais em `OxygenPreRienaRemoval_9-8-2016` (BIRT, DTP, GMF, Scout, Subversive, WebTools) e em
  Neon (WindowBuilder).

**P4. O mesmo build é redistribuído por várias releases, mas o mapper atribui commits diferentes.**
O código distribuído não muda, mas o mapeamento cria "evolução" com commits de desenvolvimento não distribuídos:
- BIRT 4.7.0 (`v201706142203`) de **Oxygen a 2020-09 (19 releases)**: o mapper usa 16 commits diferentes, até 375
  commits à frente.
- GEF Legacy `4.0.0_gef-master_1952` (2016) de Neon a 2022-06; PTP build `9.4/2021-09` de 2021-09 a 2025-12;
  Mylyn 3.24.2 (2018-09 → 2020-03) e 3.25.2 (2020-09 → 2022-03); DTP 1.13/1.14.x; WindowBuilder 1.9.x.

**P5. O escopo do repositório ≠ o escopo da contribuição.**
- **WebTools**: `webtools.aggrcon` é o WTP inteiro (~30 features: common, sourceediting, servertools, jsdt, dali…).
  O repositório local é só o `webtools.javaee`.
- **JDT / PDE**: vêm do `ep.aggrcon` (Eclipse SDK inteiro, 19 features hoje). O JDT local é só o `eclipse.jdt.core`
  (JDT UI/Debug ficam em outros repositórios). O PDE local é o `eclipse.pde`.
- **GEF**: a contribuição traz GEF Legacy/Classic (`gef-classic`), **GEF4/GEF5 (`gef`, clonado mas sem feature)** e o
  runtime e(fx)clipse. Do GEF Classic, 40% dos .java são exemplos.
- **RAP**: `rap.aggrcon` (runtime, repositório local) + `rap-tools.aggrcon` (outro repositório).
- **Mylyn**: até 2023, vários repositórios (commons, tasks, context, docs, reviews, builds, versions; o GitHub
  connector vinha da EGit). O repositório atual consolidou esses históricos em 2023.
- **m2e**: inclui **m2e-wtp** a partir de 2022-09 (outro repositório). **CDT**: inclui o **LaunchBar** (repositório
  separado até a consolidação) e o **cdt-lsp** (2024+, outro repositório). **EGit**: inclui o egit-github connector.

**P6. Repositório errado.** "Subversive" → `subclipse`. O simrel distribuía o Subversive
(`download.eclipse.org/technology/subversive`), projeto Eclipse diferente do Subclipse (Tigris/GitHub). Nenhum commit
do mapeamento corresponde a código distribuído no simrel.

**P7. Históricos importados e sub-históricos** (já descritos no INVENTARIO.md): CDT, Mylyn, PDE, EMF, GEF, DataTools,
WebTools, Scout, m2e. Com `--all`, o mapper às vezes cai em sub-históricos sem código (DataTools até 2017,
Mylyn/PDE/m2e em datas isoladas).

### Resumo por feature

| Feature | Rel. ativas no simrel | Builds distintos distribuídos* | Commits distintos do mapper | igual | à frente | divergente | atrás | sem tag | fora/desativ. | Mediana de commits a mais | Principais problemas |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BIRT | 38 | 12 | 33 | 0 | 29 | 8 | 1 | 0 | 23 | 166 | P3 (sai em 2020-12), P4 (4.7.0 por 19 releases), P1 |
| CDT | 61 | 44 | 59 | 9 | 23 | 17 | 2 | 10 | 0 | 50 | P1 (branches `cdt_X_Y`), P5 (LaunchBar, cdt-lsp), P7 |
| DataTools | 60 | 23 | 33 | 3 | 1 | 13 | 0 | 43 | 1 | 5124 | P7 (até Oxygen.3 commits sem código), P4, tags sem padrão |
| EGit | 61 | 46 | 59 | 2 | 50 | 7 | 0 | 2 | 0 | 9 | P1 leve (pós-build, poucos commits); Mars.1/Oxygen.2_respin em branch de manutenção |
| EMF | 61 | 45 | 56 | 19 | 32 | 5 | 1 | 4 | 0 | 11 | P1 leve; XSD no mesmo repositório |
| EclipseLink | 9 | 5 | 7 | 0 | 2 | 4 | 3 | 0 | 52 | 213 | **P3 (só até 2014)**, P1 (branches 2.x) |
| GEF | 61 | 25 | 32 | 9 | 41 | 0 | 2 | 9 | 0 | 30 | P4 (Legacy 2016–2022), **P5 (`gef` sem feature)**, exemplos |
| GMF Runtime | 60 | 24 | 46 | 10 | 22 | 4 | 3 | 21 | 1 | 6 | P1 leve, P4 (notation fixo) |
| JDT | 61 | 56 | 59 | 0 | 38 | 20 | 0 | 3 | 0 | 28 | **P1 (manutenção → master)**, P5 (só JDT Core) |
| PDE | 61 | 56 | 59 | 0 | 36 | 22 | 0 | 3 | 0 | 12 | **P1 (manutenção → master)**, P7 |
| Mylyn | 57 | 29 | 55 | 6 | 6 | 44 | 1 | 0 | 4 | 3,5 (pós-2023) | **P5/P7 (multi-repo até 2023)**, P3 (desativado), P4 |
| PTP | 60 | 17 | 27 | 0 | 22 | 13 | 1 | 24 | 1 | 28 | P4 (mesmo build 2021–2025), P3 (sai em 2026-03) |
| RAP | 61 | 46 | 55 | 17 | 4 | 12 | 25 | 3 | 0 | 2,5 | Mapeamento quase correto (≈ RC); P3 (runtime sai em 2025-09) |
| Scout | 60 | 47 | 58 | 0 | 0 | 13 | 0 | 47 | 1 | — | P1 (branches `releases/X` e `features/...`); tags por build sem padrão de versão |
| Subversive | 26 | 10 | 18 | 0 | 0 | 0 | 0 | 26 | 35 | — | **P6 (repositório errado)**, P3 |
| WebTools | 60 | 43 | 42 | 32 | 4 | 19 | 2 | 3 | 1 | 4 | **P5 (só javaee de todo o WTP)**, P7 |
| Window Builder | 59 | 33 | 46 | 7 | 2 | 0 | 0 | 50 | 2 | 12,5 | P4 (1.2.0/1.9.x), tags só a partir de 1.10 |
| m2e | 60 | 48 | 56 | 10 | 25 | 6 | 0 | 19 | 1 | 3 | P1 leve, P5 (m2e-wtp 2022+) |

\* Aproximado: respins com repositório agregado contam como build próprio.
"sem tag" = o build distribuído não foi resolvido automaticamente para um commit; isso não indica erro do mapper.

### Observações por feature
- **BIRT**: 12 builds distintos em 38 releases ativas; o último build novo é o 4.7.0 (jun/2017). O mapper avança até
  375 commits além dele. Tags `vYYYYMMDDHHMM` e `BIRT_X_Y_Z_Release_*` permitem resolver todos os builds.
- **CDT**: builds versionados (`cdt-X.Y.Z-rcN`), tags `CDT_X_Y_Z`. Várias releases distribuídas a partir de branches
  `cdt_X_Y`. 10 sem tag nas releases antigas (Neon–Oxygen), em que o update site só tem nome de milestone.
- **DataTools**: até Oxygen.3, o repositório local não tem o código (commits de sub-históricos de releng). Os
  update sites de 2018+ são `-SNAPSHOT` (1.14.10x), sem tag correspondente.
- **EGit**: o caso mais próximo do correto. Todas as releases têm tag `vX.Y.Z.<timestamp>-r`; o mapper fica em geral
  2–9 commits depois da tag (mediana 9).
- **EMF**: `release/2.NN` e tags `R2_NN_0`; 19 iguais e 32 à frente (mediana 11).
- **EclipseLink**: 9 releases ativas (Juno → LunaSR0), com builds 2.4.0, 2.4.1, 2.5.0, 2.5.1 e 2.6.0-M2.
- **GEF**: o GEF Classic distribuído ficou fixo (`4.0.0_gef-master_1952`, 2016) até 2022-06. A partir de 2022-09,
  `classic/releases/3.14+`. O GEF4/5 (repositório `gef`) estava na mesma contribuição de 2015 a 2025-09.
- **GMF Runtime**: builds `R<timestamp>` resolvem bem; 21 sem tag (formato de tag diferente em parte do histórico).
- **JDT / PDE**: IDs de build do Platform → tags `I…`/`M…`/`R4_x` exatas. Nas releases de manutenção até 2018, o
  mapper sempre diverge (master); de 2019 em diante, fica 2–147 commits à frente do I-build.
- **Mylyn**: pré-2023, nenhum commit mapeado está na linha das tags `R_3_x` distribuídas (44 divergentes, até 8.810
  commits). Pós-2023 (repositório consolidado), igual ou 1–6 commits à frente.
- **PTP**: builds `RC`/`milestones` sem timestamp; o mesmo build 9.4/2021-09 entre 2021-09 e 2025-12.
- **RAP**: o mapper fica no próprio commit do RC2 (1 commit antes da tag `X.Y.0-R`); é a feature com mapeamento
  mais próximo do correto. O RAP Tools está fora do repositório local.
- **Scout**: o simrel distribui builds numerados (`releases/14.0/29`); o repositório usa tags por build (`24.2.24`,
  `11.0.63`). A correspondência exige mapear o número do build no update site para a tag.
- **WebTools**: o javaee muda pouco; o mapper coincide com a tag em 32 releases. O problema é o escopo (P5).
- **Window Builder**: 1.2.0 até Photon (mesmo número de versão em builds diferentes), 1.9.x; tags só a partir de `V1.10.0`.
- **m2e**: `milestones/1.x/<timestamp>` e `releases/2.x`; tags `milestones/…` e `X.Y.Z` resolvem a maioria.

### Tabelas de períodos por feature
Cada linha agrupa releases consecutivas com o mesmo build distribuído. Dados completos, release por release:
`5-Coleta_features/inventario/sim_tags.csv` e `sim_vs_map.csv`.
