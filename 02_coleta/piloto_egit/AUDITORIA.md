# Auditoria — Execução piloto do pipeline cpmp no EGit

Data: 2026-10-10. Escopo: feature **EGit** da LPS Eclipse (repositório `1-Repositorios/egit`).
Todos os scripts estão em `scripts/` (numerados na ordem de execução); a pasta `cpmp/` original não foi modificada.

## 1. Decisões tomadas pelo autor

| # | Decisão | Escolha |
|---|---------|---------|
| D1 | Linha do tempo | 57 snapshots lineares (duplicatas removidas; Mars.1 e Oxygen.2_respin excluídos) |
| D2 | Evometrics / ChangeDistiller | Reimplementação corrigida (mesmas definições e extratores, bugs corrigidos, chamadas em lote) |
| D3 | Escopo de código | Apenas produção (exclui bundles `*.test`, `*.tests`, `*.junit`) |
| D4 | Validação | Ambos: protocolo original (aleatório 70/30, com correções) e temporal |
| D5 | Rótulo | Manter o `will_change` original apesar da baixa taxa de positivos: o modelo final agregará os métodos das 19 features LPS; o foco do TCC é a qualidade metodológica, não o desempenho |
| D6 | Feature `line` | Removida das features estruturais (linha inicial do método no arquivo: sem significado de métrica e funciona como identificador do método). Resultados preliminares com `line` foram movidos para `results/descartados_com_line/` |
| D7 | hist_ml (janelas) | Não executar no piloto |

## 2. Linha do tempo (s00_timeline.py → `data/timeline.csv`)

- 61 releases simrel mapeadas → 59 commits únicos (LunaSR0, z20140805-2300 e z20140806 apontam para `df446a83`; mantido LunaSR0).
- Excluídos (D1): **Mars.1** (`4cc706a2`, branch `stable-4.0`, não ancestral do snapshot seguinte) e **Oxygen.2_respin** (`03cda165`, tag v4.9.2 de manutenção, não descendente de Oxygen.2 `eb33e504`).
- Resultado: 57 snapshots (2012-07-31 → 2026-03-08), **história linear verificada** (`git merge-base --is-ancestor` entre todos os consecutivos). Intervalos de 3 a 570 commits.
- Observação: as versões (`version`) do mapeamento são a tag *seguinte* ao commit (ex.: JunoSR0 → v2.1.0), mas o commit é o que define o snapshot.

## 3. Coleta

| Etapa | Ferramenta | Saída | Observações |
|---|---|---|---|
| s01 | `git archive` | `work/snapshots/` | Não altera o checkout do repositório original. 642 → 987 arquivos de produção |
| s02 | CK 0.7.1 (jar do cpmp) | `data/ck/` | Mesmos argumentos do `ck.sh` (`true 0 false`) |
| s03 | Understand (und.exe, build 1263) | `data/understand/` | Mesmas 53 métricas e configurações do `understand.py`. CSV sai com vírgula decimal (locale pt-BR) — convertido no join |
| s04 | JMethodsExtractor em lote (`java/MethodsBatch.java`) | `data/methods/` | 9.557 versões de arquivo únicas, **0 falhas de parsing** |
| s05 | Evometrics (Python) | `data/evometrics.csv` | 351.826 linhas método×release |
| s06 | ChangeDistiller (jar do cpmp via `java/CDBatch.java`) | `data/change_distiller.csv` | 6.904 chamadas, 0 erros |
| s07 | Join | `data/egit-all-releases.csv` | **342.707 linhas, 4.073 positivos (1,19%)** |

### 3.1 Bugs encontrados no código original e correções (D2)

1. **`evometrics.py` — gerador esgotado**: `commits_between_releases = Repository(...).traverse_commits()` é um gerador consumido no primeiro método do primeiro arquivo de cada release. Todos os demais métodos recebiam TACH/FRCH/CHO… = 0. *Correção*: commits do intervalo listados explicitamente (`git rev-list --no-merges prev..cur`).
2. **`evometrics.py` — atribuição da mudança**: qualquer método alterado em um arquivo incrementava FCH/LCH/FRCH do método corrente do laço (todos os métodos do arquivo). *Correção*: a mudança é atribuída somente ao método cujo texto mudou.
3. **`evometrics.py` — variáveis não reinicializadas**: `frch`, `ataf`, `added_lines`/`deleted_lines` herdavam valores do método anterior no laço. *Correção*: estado por método.
4. **`evometrics.py` — comparação com o commit anterior na lista** (não o pai): em histórias com merges, compara commits não relacionados. *Correção*: diff contra o primeiro pai, merges excluídos, detecção de renomeação (`-M`).
5. **JMethodsExtractor no Windows**: o caminho de saída `results/<hash>/` + caminho absoluto gera caminho inválido (`results\hash\C:\...`). *Correção*: extração em lote, sem arquivos intermediários.
6. **Viabilidade**: o original lança 1 JVM por arquivo (JMethodsExtractor) e 1 JVM por método (ChangeDistiller) e faz checkout por arquivo × commit — estimativa de dias para o EGit. *Correção*: 1 JVM por lote; mesmo resultado (o `CDBatch` chama exatamente `DistillerReader.main` do jar original).
7. **ChangeDistiller em Java 21**: Guice/cglib exige `--add-opens java.base/java.lang=ALL-UNNAMED`.
8. **JavaParser**: nível de linguagem fixado em JAVA_17 (o EGit recente usa sintaxe Java 17; o default do JavaParser 3.25 falharia).

### 3.2 Definições de métricas evolutivas adotadas (s05)

Unidade de mudança: o texto do método (`MethodDeclaration.toString()` do JavaParser, como no JMethodsExtractor) difere entre o pai e o commit. Tamanho = linhas inseridas + removidas (diff de Myers, mesma biblioteca do original). O release *r* cobre os commits em (c<sub>r−1</sub>, c<sub>r</sub>].

BOM (release de nascimento), TACH, CHO, FRCH (nº acumulado de commits que alteraram), FCH/LCH, CHD = TACH/LOC, WCH = Σ TACH<sub>j</sub>·2<sup>j−r</sup>, WCD = Σ CHD<sub>j</sub>·2<sup>j−r</sup>, WFR = Σ (j−1)·CHO<sub>j</sub>, CSB = Σ TACH, CSBS = CSB/LOC no nascimento, ATAF = CSB/FRCH, LCA/LCD = TACH/CHD da última mudança, ACDF = Σ CHD/FRCH. Release 1: tudo 0 exceto BOM = 1 (**censura à esquerda**: métodos do primeiro snapshot recebem BOM=1 mesmo sendo mais antigos).

Pontos de atenção:
- ATAF foi definido como CSB/FRCH (no original era `tach/frch` só quando havia mudança, com valor residual nos demais casos).
- O texto inclui Javadoc e anotações (como no original): mudanças só de comentário contam em TACH. O ChangeDistiller (rótulo) é baseado em AST e as ignora em grande parte — ex.: o commit `52328d63f` "Add missing @Override annotations" alterou o texto de 1.195 métodos no intervalo 9→10, mas só 329 tiveram TOTAL_CHANGES > 0.

### 3.3 Verificação manual (spot check)

`org.eclipse.egit.core.Activator.start(BundleContext)`: no intervalo 3 os 3 commits contados coincidem exatamente com `git log -L`. Na história completa, os 27 commits contados estão todos entre os 35 do `git log -L`; os 8 restantes são falsos positivos da heurística de faixa de linhas do git (alterações em métodos vizinhos).

### 3.4 Identificação de métodos e join (s07, `data/join_audit.csv`)

Chave: `pacote.Externa.Interna.metodo(TipoSimples,...)` — tipos reduzidos ao nome simples, sem genéricos/anotações, varargs → `[]`. Necessário porque o CK qualifica tipos incorretamente (sem classpath, atribui o pacote corrente) e o Understand usa nomes simples com genéricos.

- 100% dos métodos do evometrics foram encontrados no CK e no Understand em todas as releases.
- **Excluídos**: construtores (o extrator original só considera `MethodDeclaration`), métodos de classes anônimas/locais (sem nome estável entre ferramentas; ~25% das ocorrências de métodos — comum em código de UI Eclipse com listeners), blocos inicializadores, chaves duplicadas após normalização (≤57 por release no Understand).
- Última release (57) não tem rótulo (não há release seguinte).

### 3.5 Rótulo

Como no original: `will_change = TOTAL_CHANGES > mediana(TOTAL_CHANGES do release)`, sendo TOTAL_CHANGES do ChangeDistiller entre o release r e r+1 (rótulo **futuro**, sem vazamento por construção).
**A mediana é 0 em todas as releases**, logo o rótulo equivale a "o método mudará (AST) no próximo intervalo". Taxa de positivos: 0,03%–9,2% por release; a partir da release 42 (≈2022), 2 a 11 positivos por release (EGit em modo de manutenção).

## 4. Treinamento (s08, s09)

Correções metodológicas em relação a `trad_ml.py` (D4): scaler ajustado só no treino (o original reajustava no teste); reamostragem só no treino e dentro de cada fold; modelo final treinado no treino completo (o original avaliava o modelo do último fold); ROC AUC por probabilidade (o original usava rótulos); split estratificado; métricas adicionais PR-AUC e MCC; LogisticRegression `max_iter=1000`.

### 4.1 Achados de validade (importante)

1. **Vazamento por identidade no protocolo aleatório**: 99,9% das linhas de teste pertencem a métodos presentes no treino (em outras releases) e 93,1% têm o par idêntico (método, `line`). Métodos estáveis repetem quase as mesmas features em todas as releases → o modelo pode memorizar o método. Resultados do protocolo aleatório são **otimistas** e não representam predição para releases futuras.
2. **Feature `line`** (linha inicial do método no arquivo, do CK) foi a mais importante no MDI (0,21) na execução preliminar, sem significado causal: funciona como identificador do método. Estava na lista original de métricas estruturais do cpmp; removida (D6).
3. **Temporal**: corte em T=42 (70% das linhas) deixa apenas **95 positivos em 101.914 linhas de teste** (0,09%) → métricas com alta variância.

### 4.2 Resultados finais (sem `line`; 48 configurações por protocolo, sem erros)

Melhor ROC AUC por conjunto de features × algoritmo (máximo sobre as reamostragens):

| Conjunto | Protocolo | DT | LR | MLP | RF |
|---|---|---|---|---|---|
| model1 (estrutural) | temporal | 0,516 | 0,766 | 0,777 | 0,632 |
| model2 (estrutural + evolutivo) | temporal | 0,562 | 0,749 | 0,764 | 0,686 |
| model3 (evolutivo) | temporal | 0,396 | 0,604 | 0,615 | 0,435 |
| model1 (estrutural) | aleatório | 0,542 | 0,777 | 0,798 | 0,767 |
| model2 (estrutural + evolutivo) | aleatório | 0,557 | 0,796 | **0,831** | 0,822 |
| model3 (evolutivo) | aleatório | 0,543 | 0,698 | 0,714 | 0,631 |

Interpretação:
- No protocolo aleatório, as métricas evolutivas acrescentam informação (model2 > model1). No temporal, o ganho desaparece e as evolutivas isoladas ficam próximas ao acaso. Ou seja, o histórico de mudanças do passado não se transfere para releases futuros, o que é consistente com a mudança de regime do EGit (modo de manutenção a partir de ~2022) e com o vazamento por identidade do protocolo aleatório (4.1).
- Desempenho prático baixo em todos os casos: o melhor PR-AUC é 0,011 no temporal (prevalência no teste de 0,09%) e 0,105 no aleatório; F1 da classe positiva ≤ 0,14; MCC ≤ 0,14.
- No ranking MDI sem `line`, o topo é WCH (0,20) e WCD (0,17), duas métricas evolutivas. A importância é calculada sobre todos os releases juntos, o que não garante generalização temporal.

(Resultados numéricos: `results/egit-results-trad_temporal.csv` e `results/egit-results-trad_random.csv`; importância: `results/mdi_egit.csv`, `results/information_gain_egit.csv`.)
