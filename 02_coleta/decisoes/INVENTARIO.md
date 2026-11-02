# Inventário das features (Passo 1): nada foi coletado ainda

Data: 2026-10-10. Todos os acessos ao git foram somente leitura (`ls-tree`, `rev-list`, `merge-base`, `show`), sem checkout.
Scripts e saídas brutas: `inventario/` (`inv_timeline.py` → linearidade; `inv_commits.py` → raízes/nº .java por commit;
`inv_rule2.py` → regra de testes e contagem de produção; `inv_intervals.py` → históricos importados).
Tabelas completas (inclusive cada snapshot fora da linha, com branch/tag): `inventario/tabelas.md`.

## Como os snapshots fora da linha foram identificados
Commits únicos ordenados por data de commit (como no s00 do piloto); cadeia de ancestralidade mais longa
(`git merge-base --is-ancestor`, programação dinâmica). Os commits que ficam fora dessa cadeia são os "fora da linha".
No EGit, o método reproduz exatamente o piloto (57 snapshots; Mars.1 e Oxygen.2_respin fora).

## Achados
1. **O mapper não usa o conteúdo do simrel.** `simrel_mapper/main.py:85-91` pega, para cada repositório, o último commit
   de *qualquer ref* (`git log --all --date-order --until=<data do simrel> -1`). `status=SUCCESS` só significa que
   existe algum commit antes da data. Daí vêm os commits em branches de manutenção, de feature e em sub-históricos.
2. **Históricos importados por merge** (repositórios consolidados): o nº de raízes do histórico cresce em CDT, Mylyn,
   PDE, EMF, GEF, DataTools, WebTools, Scout, m2e e CVS. No intervalo do merge, `rev-list prev..cur` (s04) inclui todo
   o histórico antigo do repositório importado (ex.: CDT 2020-03: 7.900 de 8.073 commits; Mylyn 2023-03: 17.158;
   DataTools Oxygen.3: 4.333), que seria contado como mudança daquele intervalo.
3. **Mylyn**: antes de 2023-03, cada release aponta para um sub-histórico diferente. A cadeia linear pré-2023 é o
   conector GitHub (`org.eclipse.egit.github.*`, ~190 arquivos); o Mylyn consolidado (~3.300 arquivos) só começa em 2023-03.
4. **DataTools**: até KeplerSR1 os commits mapeados têm 0–188 .java; o código real (~4.900 arquivos) só entra em
   Oxygen.3 (importação de 22 raízes).
5. **Subversive → `subclipse`**: Subclipse (Tigris) e Subversive (Eclipse) são produtos diferentes; o mapeamento vem
   só do dicionário `config.py` do mapper.
6. **CVS → `org.eclipse.team.cvs`**: o mapeamento diz `eclipse.cvs`. A pasta local é um fork pessoal
   (github.com/JAndrassy), não o repositório oficial. Todos os commits mapeados existem nele. Último snapshot: 2023-12;
   em 2023-06 cai de ~1.600 para 622 .java.
   *Investigação (2026-10-11):* o fork tem o histórico completo do repositório oficial
   `eclipse-platform/eclipse.platform.team` (raízes de 2001/2007; hashes idênticos, conferido no GitHub:
   `8e348bd773cd` com pai `cc6ef5d`) até 2022-02-09. Depois disso, só há commits do JAndrassy (`1f9b1461e`,
   2023-04-06: "delete non-cvs bundles"). No simrel, o CVS (`org.eclipse.cvs.feature.group`) vinha na contribuição
   "Eclipse" (`ep.aggrcon`, update site do Platform) desde o commit inicial (2012) até `3fc26371` (2022-01-07, 2022-03 M1),
   quando foi removido. A feature CVS (`features/org.eclipse.cvs-feature/feature.xml`) tem só 4 plugins:
   `org.eclipse.cvs`, `org.eclipse.team.cvs.core`, `org.eclipse.team.cvs.ssh2` e `org.eclipse.team.cvs.ui`
   (~523 .java de produção). Até 2022 os snapshots têm ~1.460 arquivos, com ~940 de Team/Compare/net/jsch
   (Platform, não CVS). As releases 2022-03 a 2023-03 caem todas no mesmo commit; de 2023-06 em diante, nos commits do fork.
7. **EclipseLink 2021-06** (`e9ddf971`) não existe no clone (nenhum ref). O mapper rodou em outro clone
   (`Desktop\Feature-models\1-Repositorios`).
8. **Sem feature no mapeamento**: `gef` (GEF 4/5, repositório novo; a feature GEF aponta para `gef-classic`) e
   `simrel.build` (é a fonte das datas, não é feature; tem 50 `.aggrcon`, a maioria de projetos sem repositório clonado).
   Nenhuma feature ficou sem repositório.
9. **PTP** termina em 2021-09 (projeto arquivado).

## Regra de testes proposta (genérica, reproduz exatamente o filtro do piloto no EGit)
Um arquivo é teste se: (a) estiver em `src/test/` ou `src/it/` (Maven); ou (b) algum diretório **antes da raiz de
pacotes** (`src*`, `org`, `com`, …) tiver nome em {test, tests, testsuites, unittest, src-test, src_test, testsrc,
test-src, testdata} ou um bundle cujos tokens (separados por ponto) incluam {test, tests, junit, testing, testapps,
testhelper, testsuite, testsuites}. Exceções mantidas como produção (ferramentas de execução de testes distribuídas
aos usuários): `org.eclipse.pde.junit.runtime`, `org.eclipse.pde.unittest.junit`, `org.eclipse.rap.junit(.runtime)`.
Diretórios de pacote como `org/eclipse/ui/testing` (RAP) e `org/eclipse/wb/core/controls/test` (WindowBuilder)
continuam como produção.

## Decisões pendentes (do autor)
Ver a mensagem do Passo 1 / a seção de decisões a ser registrada aqui após a resposta.

## Decisões do autor para o novo mapeamento (2026-10-12)
Base: `Analise_Timeline_Projetos.md` (análise do mapeamento e estratégias) e `auditoria_simrel/CRITERIOS.md`.

| # | Decisão | Escolha |
|---|---|---|
| M1 | Estratégia | **E3**: snapshot = último commit da **linha principal (first-parent)** antes da data; simrel usado como filtro de presença e escopo |
| M2 | Calendário | Tags do simrel filtradas: sem triplicatas (`z20140805-2300`, `z20140806`), respins (`Neon.1a`, `Neon.3_respin`, `Oxygen.1a_respin`, `Oxygen.2_respin`), `OxygenPreRienaRemoval_9-8-2016`, `PhotonM7`, `PhotonRC4`. Inclui as tags novas 2026-06 e 2026-09. **54 datas** (JunoSR0 2012-08-03 → 2026-09) |
| M3 | Presença | Critérios C1–C4 (`auditoria_simrel/CRITERIOS.md`). A série vai da 1ª à última release presente; **lacunas internas são atravessadas** (coleta contínua), registradas como ameaça |
| M4 | Índice de release | **Global do calendário** (1..54, igual para todas as features); afeta BOM/FCH/LCH/WFR (desvio do piloto) |
| M5 | Snapshots idênticos consecutivos | Removidos (mantém o primeiro), como no piloto |
| M6 | Históricos importados por merge | Commits que não descendem da linha principal anterior **não contam** no intervalo do merge |
| M7 | Escopo multi-repositório | Só os repositórios já clonados (WebTools = webtools.javaee; JDT = JDT Core; sem RAP Tools, m2e-wtp, LaunchBar, cdt-lsp) |
| M8 | GEF | Só `gef-classic` (presença pela feature `org.eclipse.gef.sdk`) |
| M9 | Testes | Regra genérica aprovada, com exceções de produção (pde.junit.runtime, pde.unittest.junit, rap.junit(.runtime), CDT testsrunner) |
| M10 | Exemplos/releng | Excluídos (diretórios/bundles example(s)/sample(s)/demo/tutorial/releng antes da raiz de pacotes) |
| M11 | Subversive | Repositório real clonado em `1-Repositorios/subversive` (`gitlab.eclipse.org/eclipse/subversive/subversive`), verificado: as 7 features contribuídas existem e, nas 20 releases presentes, a versão da linha principal cai no `versionRange` do simrel. **`subclipse` apagado** com autorização do autor |
| M12 | Mylyn | Série a partir de **2023-06** (repositório consolidado) |
| M13 | EclipseLink | Mantido só no período de presença (JunoSR0 → LunaSR0) |
| M14 | CVS | Escopo = plugins da feature (`org.eclipse.cvs`, `team.cvs.core`, `team.cvs.ssh2`, `team.cvs.ui`, + `team.cvs.ssh` até 2014); até 2021-12 |
| M15 | DataTools | Série a partir de **Oxygen.3** (1º snapshot com o código da feature na linha principal) |
| M16 | EGit | Recoletado em `5-Coleta_features` com a nova estratégia (sem tocar em `4-Coleta_egit`) |


## Resultado do novo mapeamento (2026-10-12)
Scripts: `mapeamento/features.py` (configuração por feature), `mapeamento/mapear.py` (calendário, presença, snapshots,
auditorias), `mapeamento/auditar_escopo.py` (escopo de código). Saídas em `mapeamento/output/`: `calendario.csv` (54 datas,
índice global), `presenca.csv` (C1–C4 por feature × data), `mapeamento.csv` (commit por feature × data, status),
`intervalos.csv` (linearidade, commits, importados), `escopo.csv` / `escopo_excluidos.txt`, `resumo.csv`, `mapear.log`.

Verificações: **todas as séries lineares** (0 intervalos não lineares); regressão do EGit = 54/54 commits idênticos entre
`git rev-list -1 --first-parent --before` e a implementação final; 1º snapshot do EGit = 642 .java de produção (igual ao piloto).

| Feature        | Repositorio          | Serie              |   Datas |   Snapshots |   Duplicatas |   Lacunas | Prod        |   Commits |   Importados |   ArqxSnap |   Estim_h |
|:---------------|:---------------------|:-------------------|--------:|------------:|-------------:|----------:|:------------|----------:|-------------:|-----------:|----------:|
| BIRT           | birt                 | JunoSR0 → 2020-09  |      30 |          27 |            3 |         0 | 7917 → 8010 |      2919 |            0 |     215570 |       9.7 |
| CDT            | cdt                  | JunoSR0 → 2026-09  |      54 |          54 |            0 |         0 | 7259 → 7896 |      7188 |         8228 |     424566 |      19   |
| CVS            | org.eclipse.team.cvs | JunoSR0 → 2021-12  |      35 |          34 |            1 |         0 | 536 → 523   |       693 |           58 |      17886 |       0.8 |
| DataTools      | datatools            | Oxygen.3 → 2026-09 |      35 |          24 |           11 |         0 | 4600 → 4639 |        98 |            0 |     110726 |       5   |
| EGit           | egit                 | JunoSR0 → 2026-09  |      54 |          54 |            0 |         0 | 642 → 995   |      4154 |            0 |      46939 |       2.1 |
| EMF            | org.eclipse.emf      | JunoSR0 → 2026-09  |      54 |          54 |            0 |         0 | 1540 → 1918 |      1347 |         1348 |      91247 |       4.1 |
| EclipseLink    | eclipselink          | JunoSR0 → LunaSR0  |       7 |           7 |            0 |         0 | 5467 → 5790 |      1511 |            0 |      39020 |       1.7 |
| GEF            | gef-classic          | JunoSR0 → 2026-09  |      54 |          33 |           21 |         0 | 693 → 780   |      1140 |          154 |      23499 |       1.1 |
| GMF Runtime    | gmf-runtime          | JunoSR0 → 2026-09  |      54 |          47 |            7 |         0 | 1572 → 1587 |       444 |            0 |      74500 |       3.3 |
| JDT            | eclipse.jdt.core     | JunoSR0 → 2026-09  |      54 |          54 |            0 |         0 | 1458 → 1844 |      8550 |            0 |      94704 |       4.2 |
| PDE            | eclipse.pde          | JunoSR0 → 2026-09  |      54 |          54 |            0 |         0 | 2381 → 3238 |      4593 |         5143 |     144052 |       6.5 |
| Mylyn          | org.eclipse.mylyn    | 2023-06 → 2026-09  |      14 |          14 |            0 |         0 | 2581 → 3188 |      1277 |         1962 |      45326 |       2   |
| PTP            | ptp                  | JunoSR0 → 2025-12  |      51 |          26 |           25 |         0 | 3155 → 2043 |      1476 |            0 |      60031 |       2.7 |
| RAP            | org.eclipse.rap      | JunoSR0 → 2025-06  |      49 |          48 |            1 |         0 | 2956 → 3609 |      3152 |            0 |     155144 |       6.9 |
| Scout          | scout.rt             | JunoSR0 → 2026-09  |      54 |          54 |            0 |         0 | 2279 → 3161 |     13562 |         3479 |     141060 |       6.3 |
| Subversive     | subversive           | JunoSR0 → Oxygen.3 |      20 |          16 |            4 |         0 | 1127 → 1165 |       425 |            0 |      18371 |       0.8 |
| WebTools       | webtools.javaee      | JunoSR0 → 2026-09  |      54 |          41 |           13 |         0 | 3044 → 3345 |       344 |         2096 |     131937 |       5.9 |
| Window Builder | windowbuilder        | JunoSR0 → 2026-09  |      54 |          48 |            6 |         1 | 3703 → 3052 |      1503 |            0 |     166308 |       7.4 |
| m2e            | m2e-core             | JunoSR0 → 2026-09  |      54 |          54 |            0 |         0 | 625 → 840   |      2202 |          120 |      40722 |       1.8 |

Total: 743 snapshots, 2,041,608 arquivo×snapshot de produção; estimativa nesta máquina (2 instâncias
do Understand, CPU compartilhada) ≈ 91 h.

### Correções técnicas encontradas na auditoria do mapeamento (a confirmar pelo autor)
- **M17 – CDT, merge com pais invertidos:** `7c8bb9f0` (2022-01-11, "Bug 577097: Merge o.e.remote into CDT") tem como 1º pai
  o repositório importado `org.eclipse.remote` (238 .java) e como 2º pai o CDT (9.364 .java). Seguindo só o 1º pai, a série
  pré-2022 era o `org.eclipse.remote` (76–221 arquivos). Correção: nesse merge a linha principal segue o 2º pai; a cadeia passa
  a terminar na raiz do CDT (`db3c6a4470`, 2002, "First commit of CDT code from QNX"). Nos outros 18 repositórios a cadeia
  first-parent já termina na raiz original do projeto (verificado) e nenhum outro merge invertido foi encontrado no CDT.
- **M18 – JDT, `JCL/`:** 668 arquivos `JCL/converterJclMin*/` (bibliotecas mínimas do JDK usadas como entrada dos testes)
  entram em 2020-12; classificados como teste (exclusão `^JCL/`).
- Saltos restantes verificados e mantidos (reais): Mylyn 2023-09→2023-12 (+824 arquivos, segunda consolidação de repositórios;
  código importado "nasce" em 2023-12, M6); PTP LunaRC4→LunaSR2 (−683, remoção de Remote Tools/RSE, Bug 459266/459268).

### Ponto de atenção no escopo
BIRT: além dos exemplos, a regra exclui bundles `*samples*`/`*sampledb*` (samplesview, samples.ide/rcp, ODA sampledb: ~40
arquivos), que são distribuídos ao usuário (visão de exemplos e banco de exemplo). Lista completa por feature:
`mapeamento/output/escopo_excluidos.txt`.

## Decisões confirmadas pelo autor (2026-10-12, após a auditoria do mapeamento)
| # | Decisão | Escolha |
|---|---|---|
| M17 | CDT, merge com pais invertidos (`7c8bb9f0`) | **Confirmada**: nesse merge a linha principal segue o 2º pai (`features.py`, `follow_parent2`) |
| M18 | JDT, `JCL/` | **Confirmada**: classificada como teste (`exclude=^JCL/`) |
| M19 | BIRT, bundles de samples distribuídos ao usuário (samplesview, samples.ide/rcp, sampledb, samplereports) | **Mantidos como produção** (`keep_examples`); continuam excluídos `chart.examples*`, `tutorial`, `releng` |
| M20 | Máquina de coleta | Coleta local (sem nuvem), com paralelismo dimensionado por medição: ver `RECURSOS.md` |

## Execução da coleta
- Scripts: `5-Coleta_features/scripts/` (`s00`–`s07` com `--feature`, `run_all.py` orquestrador, `auditar_feature.py`).
- Equivalência com o piloto validada antes da coleta (EGit com a timeline do piloto; ver `RECURSOS.md`, seção 3).
- Teste de ponta a ponta: CVS (10 min; 0 falhas de parsing, 0 erros do ChangeDistiller, spot check OK) — `CVS/AUDITORIA.md`.
- Coleta completa iniciada em 2026-10-12 17:38 (`logs/run_all_20261012_173845.log`, orçamento de RAM 5,0 GB); cada feature gera `<feature>/AUDITORIA.md` ao terminar.

**M21 (2026-10-13), falhas de parsing por sintaxe legada:** MethodsBatch tenta JAVA_8 **somente** se o JAVA_17 falhar (identificadores `_`); equivalência com o piloto preservada (RECURSOS.md, seção 5)

**M22 (2026-10-14), templates de geração de código:** diretórios `templates_*`/`template*`, `archetype-resources` e `.java`
sob `src/main/resources/` (antes da raiz de pacotes) não são código de produto (modelos que os assistentes copiam para
o projeto do usuário). Excluídos **no dataset final** (`s07_join.py`, `features.is_template`; coluna
`template_methods_excluded` no `join_audit.csv`). CK/Understand/evometrics não foram refeitos: os templates não são
referenciados pelo código do produto. Afeta PDE (`org.eclipse.pde.ui.templates/templates_*`) e DataTools
(`…oda.template.ui/templates_oda_*`); no Scout, os templates de arquétipo já não entravam (não são parseáveis).

**M23 (2026-10-14), sintaxe não suportada pelo JavaParser 3.25.0 (limitação documentada):** `sealed`/`permits`
(Window Builder, 8 arquivos de 2024–2026) e o escape `"\s"` (Mylyn, 1 arquivo). Os métodos desses arquivos ficam fora
do dataset nas releases afetadas. Usar outro parser só nesses arquivos poderia gerar mudanças falsas (texto do método
formatado por versões diferentes do JavaParser entre releases).

**M21 (aplicação):** a 2ª tentativa em JAVA_8 foi criada depois de as s04–s06 de várias features terem rodado. Ela
afeta só arquivos com `_` como identificador: EclipseLink (refeito em 2026-10-13), Scout e WebTools (refeitos em
2026-10-14). Nas demais features não há falha desse tipo.

**M24 (2026-10-14), CK no JDT:** `OperandStack.java` excluído só da entrada do CK nos snapshots em que existe (2024+),
porque o CK 0.7.1 trava com ele e com `CodeStream.java` juntos (ver `JDT/AUDITORIA_manual.md`).

**M25 (2026-10-14), JDT `modules/`:** fixture de teste do APT, excluída no dataset final (`dataset_exclude`).

**M23 (complemento):** a limitação de sintaxe inclui também `sealed` no JDT (11 versões em snapshots, 2024+) e o
parâmetro de lambda `_` (Java 22) no Scout (2 versões).

**M22 (correção, 2026-10-14):** os templates estavam no evometrics (PDE 10.380 e DataTools 3.168 linhas), mas
**não chegavam ao dataset final**: o join interno já os descartava (CK/Understand não geram chaves compatíveis
para esses arquivos). O tamanho dos datasets de PDE (1.215.106) e DataTools (1.184.083) é o mesmo antes e depois da
regra. A regra fica como salvaguarda explícita.

**M26 (2026-10-14), commits equivalentes contados uma vez:** a mesma mudança aplicada duas vezes (cherry-pick, rebase,
"merge" achatado), identificada por `git patch-id --stable` do diff restrito aos arquivos de produção, era contada em
dobro nas métricas evolutivas (comportamento do piloto). Medição antes da correção (`scripts/medir_duplicatas.py`):
BIRT 32,8% dos commits que mudaram métodos (29,3% das mudanças método×commit); PTP 7,1%; JDT 3,2%; Mylyn 3,5%;
PDE 0,6% (3,0% das mudanças); EGit 0,9% (0,3%); demais ≤ 0,1%. Decisão do autor: na s05, manter só a 1ª ocorrência
(data de commit) de cada patch-id (`dup_lib.py`; lista em `<feature>/data/commit_duplicates.csv`). O rótulo
(ChangeDistiller entre snapshots) não é afetado. Desvio em relação ao piloto: no EGit, 20 commits deixam de ser contados
em dobro (0,3% das mudanças).

**M27 (2026-10-14), branches mesclados tarde: mantida a definição do cpmp, documentada como ameaça à validade.**
Cada commit sem merge do intervalo conta (como no cpmp e no piloto). Quando um branch antigo é mesclado, suas mudanças
são atribuídas ao intervalo da mesclagem. Medição (`scripts/medir_mesclagem_tardia.py`, fração das mudanças
método×commit vindas de commits anteriores ao snapshot anterior): **BIRT 39,7%** (atraso mediano 308 dias),
**JDT 12,4%** (91 dias; branches `BETA_JAVA*`), RAP 2,3%, demais ≤ 0,4%. Isso infla TACH/FRCH/CHO no intervalo da
mesclagem, inclusive quando o trabalho já tinha sido reimplementado na linha principal (ex.: exportador PPTX do BIRT:
commits "Refactor…" de 2015-01 no intervalo 9 e os originais de 2014 no intervalo 11). O rótulo não é afetado.
Prevista análise de sensibilidade no treino (com e sem BIRT e JDT).

## Encerramento da coleta (2026-10-14 22:06)
As 19 features estão completas: timeline, snapshots, CK e Understand em 100% dos snapshots; s04–s07 com as decisões
M1–M27; `AUDITORIA.md` gerado por feature (+ `AUDITORIA_manual.md` onde houve verificação manual). Datasets:
`<feature>/data/<feature>-all-releases.parquet` (colunas `method_uid`, `feature`, `repository` + métricas + rótulo).

- Total: **18.059.107 linhas** (método × release), **87.687 positivos (0,49%)**.
- ChangeDistiller: 0 erros em todas as features. CK/Understand: 100% dos snapshots.
- Match no join: mínimo por release ≥ 97,7% (evo_in_ck) e ≥ 97,9% (evo_in_und) em todas as features.
- Spot check contra `git log -L`: 14 features com 100% dos commits contados confirmados; BIRT, JDT, Mylyn, PDE, Scout
  e CDT com divergências explicadas e verificadas à mão (renomeações, ramos laterais, comentários removidos,
  mesclagem tardia; ver `AUDITORIA_manual.md`).
- Limitações documentadas: M23 (sintaxe `sealed`, `"\s"`, `_` de lambda não suportados pelo JavaParser 3.25.0),
  M24 (CK sem `OperandStack.java` no JDT 2024+), M27 (mesclagem tardia: BIRT 39,7%, JDT 12,4%).
- Próximo passo (fora do escopo da coleta): treino conjunto das 19 features, com análise de sensibilidade para BIRT e
  JDT (M27) e métricas por feature.

**M28 (2026-10-15), quebras de identidade de métodos: mantidas e documentadas como ameaça à validade.** A chave
do método (pacote + classe + assinatura) não depende do caminho do arquivo. Diferente do cpmp, que inclui o caminho,
mover diretórios não quebra o histórico (ex.: Scout `src/` → `src/main/java/`). Há duas exceções, que zeram o
histórico do método no meio da série (BOM = release da quebra, FRCH/CSB… em 0, sem rótulo na transição), sem inflar
as métricas: **renomeação de pacote/classe** (ex.: PTP KeplerPostRC4, 6.539 métodos; EclipseLink JunoSR2, 4.500;
Scout Neon; EMF 2020-09) e **código importado de outro repositório** (M6; ex.: Mylyn 2023-12, EMF/XSD 2023-03).
O DataTools não é afetado (a consolidação de 2018-01 é anterior ao 1º snapshot da série, M15). Registro completo,
com 31 transições acima do limite (≥ 100 métodos ou ≥ 1% da release) e comandos de verificação:
`AMEACA_identidade.md`; por feature, `data/identidade_metodos.csv`, `data/identidade_pares.csv` e a seção 7 do
`AUDITORIA.md`. Os datasets não foram alterados, e não foi criada marcação por método (decisão do autor).
