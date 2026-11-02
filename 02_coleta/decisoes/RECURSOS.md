# Recursos, desempenho e equivalência com o piloto (coleta multi-feature)

Data: 2026-10-12. Máquina de coleta: Intel i7-11800H (8 núcleos / 16 threads), 15,8 GB de RAM, NVIDIA RTX 3050
Laptop (4 GB), SSD com 128 GB livres, Windows 11, Java 21.0.11, Understand build 1263, Python 3.14.5
(`5-Coleta_features/.venv`, versões fixadas em `requirements.txt`).

Princípio: **nenhuma otimização pode mudar o resultado.** Cada mudança em relação ao piloto (`4-Coleta_egit/scripts`)
foi validada contra as saídas do piloto (seção 3).

## 1. Medições (ferramentas do pipeline)
| Medição | Resultado | Comando/script |
|---|---|---|
| CK, maior snapshot (BIRT 2020-06, 8.050 .java) | 50,8 s, pico 1,55 GB | `scripts/medir.py` |
| Understand, mesmo snapshot, 10 processos `und` (modo do piloto) | 678,8 s, pico 3,14 GB | `BIRT/work/medir/und_test.py` |
| Understand, mesmo snapshot, 1 processo `und process` (modo batch) | 613,3 s, pico 3,16 GB | idem |
| Understand: a análise (`analyze`) leva ~2 min; o restante é o cálculo/exportação das 53 métricas (`metrics`) | — | horários dos arquivos |
| Understand em paralelo (snapshots do EGit, ~1.000 .java) | 1 inst.: 78 s/snapshot; 4 simultâneas: 23,3 s/snapshot (3,4×); 8 simultâneas: 16,2 s/snapshot (4,8×), mas RAM em 100% | `scripts/escala_und.py` |
| RAM ocupada por outros programas (VS Code ~3,2 GB, sistema etc.) | 8,8 GB em uso sem a coleta, ~6,5–7 GB disponíveis | PowerShell `Win32_OperatingSystem` |
| Extração de snapshots (s01), EGit 54 snapshots | 14 s (`read-tree` + `checkout-index` em índice temporário) contra >10 min com tar em fluxo no Python | `s01_snapshots.py` |
| s04–s07 no EGit (57 snapshots do piloto) | s04 106 s, s05 10 s, s06 30 s, s07 31 s | `EGit_validacao_piloto/*.log` |

**Gargalo:** Understand (≈ 76 ms por arquivo × snapshot numa instância) e **memória RAM** (≈ 0,40 GB por 1.000 arquivos
para o Understand e ≈ 0,19 GB para o CK). A CPU não limita: com 8 Understand em paralelo a CPU chegou a 96%, mas a RAM
esgotou antes.

**GPU:** nenhuma ferramenta da coleta usa GPU (CK/JDT, Understand, JavaParser, ChangeDistiller e git rodam só em CPU),
então a RTX 3050 não acelera esta etapa. Ela pode ser usada no treino (ex.: XGBoost/LightGBM com CUDA).
**Vários ambientes virtuais:** desnecessários. O paralelismo é feito com processos externos (JVMs, `und`) e, na parte
em Python puro (diffs de Myers da s05), com `ProcessPoolExecutor` (processos separados, sem a trava do GIL).

## 2. Paralelismo adotado
- **Fila global de CK + Understand** (`run_all.py`, fase B): todos os snapshots de todas as features selecionadas,
  **maiores primeiro** (evita cauda longa), sob um **orçamento de RAM** (padrão: RAM disponível no início − 1 GB) e
  um limite de processos. Antes de lançar cada job, verifica a RAM realmente livre (outros programas podem crescer).
  Estimativas por job: Understand 0,6 + 0,40 GB/1.000 arquivos; CK 0,5 + 0,30 GB/1.000 arquivos (com `-Xmx`
  proporcional).
- **s04–s06 em paralelo à fase B** (não dependem de CK/Understand), uma feature por vez, reservando 3 GB do orçamento;
  dentro delas: `JVM_WORKERS` JVMs (MethodsBatch, CDBatch) e `PY_WORKERS` processos (diffs da s05).
- **s07** de cada feature quando suas fases B e C terminam.
- Tudo é **retomável**: saídas prontas são puladas, então a coleta pode ser reiniciada após falha ou desligamento.

## 3. Mudanças em relação ao piloto e validação de equivalência
| Mudança | Motivo | Validação | Resultado |
|---|---|---|---|
| s01: `read-tree`/`checkout-index` em índice temporário em vez de `git archive` + tarfile | velocidade (>40×) | mesmo commit do piloto (`5d7d8383`) exportado pelos dois métodos, `diff -rq` | **idêntico** (inclui CRLF) |
| s02: CK com `-Xmx` explícito | controle de memória | snapshot 1 do piloto, CSVs ordenados (md5) | **idêntico** (method e class) |
| s03: os 10 comandos do Understand num único `und process` | evitar recarregar o banco 10× | (a) EGit snapshot 1 vs CSV do piloto; (b) BIRT 2020-06 nos dois modos | (a) **0 diferenças**; (b) mesmas linhas, ordem diferente, exceto 1 linha `Package "org"` só com zeros no modo do piloto (entidade de pacote, não usada no join) |
| s04: `git log --raw -M --no-merges` por intervalo em vez de 2 chamadas por commit; textos dos métodos em SQLite deduplicado + índice compacto (hash BLAKE2b de 16 bytes, LOC) | memória (CDT/BIRT teriam GBs de texto na RAM) e velocidade | s04–s07 completos no EGit com a timeline do piloto (`EGit_validacao_piloto`, `scripts/validar_piloto.py`) | **idêntico** em todas as colunas de métricas e rótulo: evometrics (351.826 linhas), ChangeDistiller (342.707 linhas, 6.904 chamadas, 0 erros), dataset final (342.707 linhas, 4.073 positivos), join_audit (57 releases). Únicas diferenças: `commitprevious` da 1ª release vazio (`NaN` no piloto, `''` aqui) e o caminho do arquivo temporário nas colunas `CLASS_*COMMIT` do ChangeDistiller |
| s05: diffs de Myers em paralelo, cada par de textos distinto diffado uma vez | velocidade | idem | **idêntico** |
| s06: CDBatch em `JVM_WORKERS` JVMs | velocidade | idem | **idêntico** |
| Saídas em Parquet (evometrics, ChangeDistiller, dataset final) | tamanho em disco e leitura rápida | idem (leitura e comparação) | sem perda |

Mudanças **metodológicas** (não são otimizações, foram decididas pelo autor; ver `INVENTARIO.md`, M1–M18): índice global
de release (M4), exclusão de commits importados (M6), regras de escopo (M9, M10, M14, M18), linha principal (M1, M17).

## 4. Recomendações operacionais
- Fechar programas pesados (o VS Code ocupa ~3,2 GB) durante a coleta aumenta o orçamento de RAM e o paralelismo.
- (Opcional, requer administrador) adicionar `5-Coleta_features\*\work` às exclusões do Windows Defender: a coleta
  cria milhões de arquivos `.java` temporários, e a varredura em tempo real os torna mais lentos.
- Disco: estimativa de ~50 GB em `data/` (CSVs do CK e do Understand) + snapshots em `work/` (podem ser apagados após
  a s07 de cada feature).

## 5. Ocorrências durante a coleta (registro)
| Data/hora | Ocorrência | Causa | Ação |
|---|---|---|---|
| 2026-10-12 17:39 | `s01` do Mylyn falhou: "extracted 2582 of 2581" | a contagem com `rglob('*.java')` incluía o **diretório** `org.eclipse.mylyn.context.sdk.java` | contagem só de arquivos; o conteúdo extraído estava correto. `run_all.py` passou a pular a feature com erro na fase A em vez de abortar tudo |
| 2026-10-12 17:51 | `auditar_feature` do CVS com rc=1 | `UnicodeEncodeError` ao imprimir `→` no console cp1252 (o `AUDITORIA.md` já tinha sido gravado) | stdout em UTF-8 |
| 2026-10-12 18:21 | Understand falhou no GEF snapshot 06 (sem CSV) | transitória: a mesma execução, repetida isoladamente, terminou com 0 erros (`Analyze Completed (Errors:0 Warnings:2546)`) | `und_lib.run`: até 2 novas tentativas; CSV gravado como `.tmp` e renomeado só no sucesso (evita CSV parcial ser tomado como pronto ao retomar); log com início, linhas de problema e fim |
| 2026-10-12 ~18:30 | Reinício do orquestrador para aplicar as correções | — | só processos da coleta encerrados (nenhum `und`/`java`/`python` restante); 1 CSV parcial removido (`GEF/data/understand/12_bcd6206f…csv`, sem `.log`) |
| 2026-10-12 18:25 | Spot check do Subversive "VERIFICAR" (11 commits contados, 1 em comum com o `git log -L`) | o `-L:<nome>:arquivo` casou com uma **chamada** do método (linha 111), não com a declaração | `auditar_feature.py` passou a localizar a declaração e o fim do método (balanço de chaves) e usar `-L<início>,<fim>:arquivo`; com isso: Subversive 11/11 e CVS 6/6 commits confirmados. As métricas não mudaram |
| 2026-10-12 18:23 | Orçamento de RAM caiu para 2,0 GB | o VS Code cresceu de 3,2 para 6,6 GB durante a coleta | decisão do autor: manter a coleta como está (mais lenta) |
| 2026-10-12 18:30–21:05 | **Coleta parada por ~2,5 h** (orquestrador vivo, nenhum `und`/`java` rodando) | deadlock no orçamento de RAM: um job maior que o orçamento inteiro só rodava se `orçamento_livre == orçamento_total`; somas e subtrações de valores fracionários deixam resíduo de ponto flutuante (reproduzido: 17 de 200 intercalações simuladas não voltam exatamente a 2,0) | regra trocada por um contador de jobs em execução (`running == 0`), teste de regressão OK; orquestrador reiniciado às ~21:10 (retomável, nada perdido) |
| 2026-10-12 21:19 | Spot check do GEF: 12 de 13 commits confirmados | o commit `92f2b8e0e` ("added missing @Override annotations") alterou só a linha de anotação **acima** da declaração; o texto do método inclui anotações e Javadoc (mesma definição do piloto, ver commit `52328d63f` no `4-Coleta_egit/AUDITORIA.md`), mas o intervalo do `git log -L` começava na declaração | intervalo do spot check estendido para cima, sobre anotações e Javadoc; CVS 6/6, Subversive 11/11, GEF 13/13. As métricas não mudaram |
| 2026-10-12 21:10 → 2026-10-13 08:50 | Coleta noturna (orçamento 2,0 GB): 10 features concluídas (CVS, Subversive, GEF, EclipseLink, m2e, Mylyn, EGit, PTP, GMF Runtime, EMF), 700 de 1.486 jobs de CK/Understand iniciados | — | interrompida às ~09:00 por decisão do autor, para rodar fora do VS Code (`scripts/run_coleta.ps1`); 1 CSV temporário (`JDT/.../36_eaf6ea06….csv.tmp`) descartado |
| 2026-10-13 | Spot check com "VERIFICAR" em GMF Runtime (0 de 4) e Mylyn (7 de 9) | GMF: o localizador aceitou a linha `drawString(s, x, y);` (chamada dentro de `drawText`) como declaração. Mylyn: os 2 commits restantes alteram de fato o método (verificados à mão, `Mylyn/AUDITORIA_manual.md`); o `git log -L` não os lista (ramos laterais mesclados) | localizador exige um token de tipo/modificador antes do nome; reauditadas as 10 features: 9 confirmam 100% dos commits; Mylyn 7/9 + 2 verificados manualmente. As métricas não mudaram |
| 2026-10-13 | 5 falhas de parsing (piloto: 0): EMF 1, EclipseLink 2, Mylyn 1, m2e 1 | 3 são versões intermediárias com erro de sintaxe real (só em commits, não em snapshots); EclipseLink `asm/util/CheckMethodAdapter.java` usa `_` como identificador (Java ≤ 8); Mylyn `HtmlEntities.java` usa o escape `"\s"`, que o JavaParser 3.25.0 não aceita | **MethodsBatch: 2ª tentativa em JAVA_8 só quando o JAVA_17 falha** (valida: o arquivo do EclipseLink passa a 61 métodos; os de erro real continuam falhando; 300 blobs do EGit idênticos ao extrator do piloto). s04–s07 do EclipseLink serão refeitas. O Mylyn `"\s"` fica como limitação (mudar a versão do parser alteraria a ferramenta original) |
| 2026-10-13 10:23 → 2026-10-14 00:39 | Execução pelo autor fora do VS Code (`run_coleta.ps1`): 16 de 19 features com dataset final | — | — |
| 2026-10-14 03:28 | **Coleta interrompida por reinício do Windows Update** (evento 1074, `TrustedInstaller.exe`, "Sistema operacional: atualização (planejada)") | — | estado preservado (retomável); 1 CSV `.tmp` do CDT descartado. Faltavam BIRT (1 Understand), CDT (16 Understand + 54 CK), JDT (10 CK). Recomendação: pausar o Windows Update durante a coleta |
| 2026-10-14 | Falhas de parsing: Scout 301, PDE 34, Window Builder 16, WebTools 3 | Scout/PDE: templates de geração de código (não são produto); `_`: features processadas antes da 2ª tentativa JAVA_8; Window Builder: `sealed`/`permits` | M22 (templates excluídos no dataset final, s07 de PDE/DataTools refeita); s04–s07 de Scout e WebTools refeitas com a 2ª tentativa; M23 (limitação). Spot checks Scout 76/81 e PDE 23/24 verificados à mão (`<feature>/AUDITORIA_manual.md`) |
| 2026-10-14 13:20 | CK falhou nos 10 snapshots 2024–2026 do JDT | NPE do JDT embutido no CK 0.7.1 (*switch expression*); par mínimo `CodeStream`+`OperandStack` achado por *delta debugging* | M24: `OperandStack.java` fora só da entrada do CK; CK refeito para os 10 snapshots; s07 e auditoria do JDT refeitas |
| 2026-10-14 13:49 | Spot check do BIRT: 12 de 31 commits no `git log -L` | **contagem em dobro**: 9 pares de commits idênticos (mesma mensagem e tamanho; cherry-pick/rebase de 2013 reaplicados em 2014), e "Merge master to 1666 branch" com um só pai | medição por `git patch-id` em todas as features (M26); s05–s07 e auditorias refeitas com deduplicação (`logs/rerun_M26_*.log`) |
| 2026-10-14 21:32 | Coleta do CDT concluída (54/54 Understand e CK) | — | s05–s07 refeitas com M26 (16 commits equivalentes ignorados) |
| 2026-10-14 21:45 | Spot check do CDT sem linhas localizadas | `auditar_feature.py` procurava a declaração no último snapshot da série, mas o método tinha sido removido antes | passa a usar o último snapshot em que o método existe; CDT 32/33 (1 commit anterior a renomeação), CVS e EGit iguais |
| 2026-10-14 21:50 | CDT com 4 falhas de `_` resolvíveis | s04 do CDT rodou antes da 2ª tentativa em JAVA_8 (M21) | s04–s07 do CDT refeitas; varredura confirmou que nenhuma outra feature ficou nessa situação (os 2 casos do Scout são `_` de lambda, Java 22, M23) |
