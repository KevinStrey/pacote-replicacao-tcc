# Plano de treinamento

Base: datasets da coleta em `5-Coleta_features/<feature>/data/<feature>-all-releases.parquet` (19 features,
18.059.107 linhas, 87.687 positivos = 0,49%). Decisões da coleta: `5-Coleta_features/INVENTARIO.md` (M1–M28).

## 1. Servidor de treino
`vdi-cvi-peg-001` (UDESC/CEAVI): Ubuntu 18.04.6, glibc 2.27, 48 núcleos, 251 GB de RAM (~223 GB livres), sem GPU,
usuário sem sudo, Python moderno indisponível no sistema.

## 2. Ambiente
- **micromamba** instalado no home (binário único, sem sudo), com `environment.yml` de versões fixas, vindas do
  conda-forge e compatíveis com glibc 2.27: Python, numpy, pandas, pyarrow, scikit-learn, imbalanced-learn
  (+ XGBoost/LightGBM se aprovados).
- `check_env.py`: versões, importação das bibliotecas, mini-treino, núcleos/RAM/disco; registro em arquivo.
- A verificar no servidor: acesso à internet, espaço livre no home, `tmux`/`screen`, permanência dos processos após o
  logout da VDI.

## 3. Dados
- Só os 19 parquets finais + `timeline.csv`/`calendario.csv` (não os 57 GB da coleta).
- Manifesto SHA-256 gerado aqui e conferido no servidor (`verify_data.py`).

## 4. Scripts (pasta `6-Treino/`)
| Arquivo | Função |
|---|---|
| `executar_tudo.sh` | Script único: sistema → micromamba → ambiente → `check_env` → `verify_data` → `prepare_data` → teste rápido → fases 1–3 → resultados e `saida/resultados_e_logs.zip` |
| `iniciar.sh`, `status.sh`, `parar.sh` | Inicia em segundo plano (sobrevive ao logout), mostra o andamento, interrompe de forma ordenada |
| `environment.yml`, `conda-linux-64.lock` | Versões fixas; lock explícito resolvido para linux-64 com glibc 2.27 (123 pacotes, XGBoost/LightGBM em build CPU) |
| `config/experimentos.yaml` | Grade (conjuntos, reamostragens, protocolos, fases), recursos, bootstrap, teste rápido |
| `scripts/prepare_data.py` | Une os 19 parquets em ordem determinística, valida o esquema, float64 (como o piloto) + `fillna(0)`, grava `X.npy` (lido em memory-map pelos jobs) e os índices de treino/teste dos protocolos e da variante; amostra estratificada para o teste rápido |
| `scripts/models.py`, `scripts/metrics.py` | Algoritmos, reamostragem e `fit_predict` do piloto (com as correções aprovadas); métricas do piloto, por feature e versões ponderadas para o bootstrap |
| `scripts/train.py`, `scripts/job.py` | Agendador (núcleos/RAM, checkpoint, novas tentativas, timeout, vigia de memória) e execução de um job em subprocesso; cada parte da CV é um job |
| `scripts/collect_results.py` | Tabelas, por feature, importâncias, IC 95% por bootstrap, comparação da sensibilidade (pareada, mesma população de teste) e `RELATORIO.md` |
| `scripts/check_env.py`, `scripts/verify_data.py`, `scripts/empacotar_saida.py` | Teste do ambiente, SHA-256 dos dados, zip da saída |
| `ferramentas_locais/montar_pacote.py` | (local) monta `pacote/treino_tcc.zip` com dados, manifesto e binário do micromamba |
| `ferramentas_locais/equivalencia_piloto.py` | (local) mesmo código aplicado ao dataset do piloto; compara com `4-Coleta_egit/results` |

## 5. Robustez
- Checkpoint por job (`results/jobs/<id>.json`, escrita atômica); reinício pula o que já terminou.
- `try/except` por job, `errors/<id>.log`, novas tentativas configuráveis; uma falha não derruba as demais.
- Limite de jobs simultâneos, `OMP/MKL/OPENBLAS_NUM_THREADS` controlados, orçamento de RAM e tempo máximo por job.
- Sementes fixas em divisão, CV, reamostragem e modelo; cada resultado guarda configuração, versões das bibliotecas e
  hash dos dados.
- Log de progresso + arquivo de status; execução com `nohup python train.py ... > logs/train.log 2>&1 &` (ou `tmux`).
- Validação antes do treino completo: teste rápido com amostra de 1% e equivalência com o piloto (dataset antigo do
  EGit contra `4-Coleta_egit/results`).

## 6. Protocolos, algoritmos e fases (decididos em 2026-10-15)
- **Protocolos:** temporal (corte comum no calendário global onde as linhas acumuladas chegam a 70%, como no piloto)
  e aleatório 70/30 estratificado + validação cruzada de 10 partes no treino (comparabilidade com o cpmp).
- **Algoritmos:** os do cpmp (RandomForest, DecisionTree, LogisticRegression, MLP) + **XGBoost**, **LightGBM** e
  **SVM linear** (`LinearSVC`). Hiperparâmetros do cpmp/piloto; para os novos, padrões da biblioteca com
  balanceamento de classes equivalente (desvio documentado). SVM com kernel é inviável (~12 milhões de linhas).
- **Conjuntos de features:** model1 (estruturais), model2 (estruturais + evolutivas), model3 (evolutivas); `line` fora (D6).
- **Reamostragem:** NONE, ROS, SMOTE, ADASYN (só no treino, dentro de cada parte da CV).
- **Métricas:** globais e **por feature** no conjunto de teste (mesmo modelo global).
- **Fases:**
  1. **Resultados iniciais, sem MLP:** temporal + aleatório/CV; RF, DT, LR, XGBoost, LightGBM, SVM linear.
  2. **MLP só no protocolo temporal.**
  3. **Análise de sensibilidade** (seção 7).
- Analisados e **não incluídos**: LSTM (exigiria reorganizar os dados em sequências e PyTorch ≤ 2.5 por causa da
  glibc 2.27) e GNN (exigiria uma nova coleta de grafos de dependência/chamadas, não extraídos).

## 6.2 Propensão a mudança no nível de feature (decidida em 2026-10-15; foco do trabalho)
Não há modelo próprio por feature (~700 exemplos feature × release seriam poucos): as previsões do **modelo de
métodos** são agregadas por feature × release, **só no protocolo temporal** (o aleatório mistura passado e futuro).
- **Medida principal: taxa de mudança** da feature = métodos que mudam no intervalo seguinte ÷ métodos da feature
  (mudança no código existente; métodos novos não entram). **Volume** (número de métodos que mudam) como
  complementar, pois favorece features grandes.
- **Previsto:** probabilidade média dos métodos da feature (principal); proporção prevista como positiva; proporção
  dos métodos da feature entre os 5% de maior risco da LPS na release; volume previsto.
- **Avaliação por release de teste** (releases 37–53, as 17 com rótulo; **14 features**: BIRT, CVS,
  EclipseLink, PTP e Subversive só existem antes do corte T = 36): correlação de **Spearman** entre a ordem prevista
  e a real e **acerto no top 3**; média com IC 95% por *bootstrap* sobre as releases.
- **Comparação com previsões ingênuas** (sem aprendizado, informação disponível no momento da previsão):
  **persistência** (taxa da feature no intervalo anterior) e **média histórica** (média nas releases de treino);
  diferença pareada modelo − persistência com IC 95%. Se o modelo não superar a persistência, isso é um resultado.
- **Limitações:** probabilidades de modelos com reamostragem/pesos são infladas (por isso a ordem é a medida
  principal); o Mylyn começa na release 41 e não tem média histórica nem aparece no treino.
- Implementação: cada job temporal grava `por_feature_release` (métodos, mudanças reais, probabilidade média,
  mudanças previstas, topo 1/5/10%); `scripts/nivel_feature.py` gera `nivel_feature_resumo.csv`,
  `nivel_feature_por_release.csv`, `nivel_feature_ranking.csv` e uma seção do `RELATORIO.md`.

## 6.1 Execução no servidor
Um `.zip` (dados + scripts + ambiente com versões travadas) colocado no Google Drive e baixado manualmente. Um
**script único** (`executar_tudo.sh`) instala o ambiente (micromamba, com internet), confere sistema e dados
(SHA-256), roda o teste rápido e as fases 1→2→3 com retomada automática, grava **todos os logs e erros em
`saida/`** e, ao final, gera `saida/resultados_e_logs.zip` para análise.

## 7. Análise de sensibilidade (decidida em 2026-10-15)
**Uma única variante: treino e teste sem PTP, Scout e Mylyn**, com a melhor configuração do cenário principal,
comparada por PR-AUC, MCC e ROC-AUC com intervalos de confiança por *bootstrap*. Se os intervalos se sobrepuserem, as
conclusões não dependem do fenômeno.

**Motivo:** quebras de identidade de métodos (M28; renomeação de pacote/classe e código importado) zeram o histórico
evolutivo dos métodos afetados. No dataset global atingem 4,68% das linhas e 3,63% dos positivos, concentrados nestas
três features:

| Feature | Linhas afetadas (% da feature) | Positivos afetados (% da feature) | Positivos da feature (% do global) |
|---|---|---|---|
| PTP | 39,6% | 32,3% (469 de 1.451) | 1,7% |
| Scout | 18,6% | 13,1% (1.683 de 12.852) | 14,7% |
| Mylyn | 24,3% | 10,4% (133 de 1.282) | 1,5% |

**Por que o EMF não entrou** (embora tenha 11,5% das linhas afetadas):
1. Os métodos afetados no EMF são sobretudo código gerado (parser ANTLR do Xcore movido de `xcore.ui` para
   `xcore.ide` em 2020-09) e o XSD importado em 2023-03, que quase nunca mudam: só **14 dos 15.453 positivos do EMF
   (0,09%)** vêm desses métodos. O efeito no rótulo é desprezível.
2. O EMF é a feature com **mais positivos do dataset (17,6% do total)**. Retirá-lo confundiria a variante: uma
   diferença de desempenho poderia vir da perda de 1/6 dos exemplos positivos, não da remoção da ameaça.

Não entram como variantes (decisão do autor): sem BIRT/JDT (M27), ponto de corte temporal, deixar uma feature de fora a
cada rodada e múltiplas sementes. M27 fica documentada como ameaça à validade.

## 8. Estimativa de tempo no servidor (±50%)
| Cenário | Tempo |
|---|---|
| Temporal, grade completa sem MLP / com MLP | ~1–2 h / ~10–15 h |
| Aleatório com CV de 10 partes, sem MLP / com MLP | ~6–10 h / ~3–4 dias |
| Variante de sensibilidade (melhor configuração) | minutos |

## 9. Validação local (2026-10-15, antes do envio)
- **Ambiente:** lock `conda-linux-64.lock` (glibc 2.27) e ambiente local equivalente em Windows com as mesmas versões
  (scikit-learn 1.9.1, imbalanced-learn 0.14.2, XGBoost 3.4.2, LightGBM 4.7.0, numpy 2.5.4, pandas 3.0.6).
- **Preparação da matriz completa** (18.059.107 linhas, 98 colunas): 2 min; corte temporal **T = 36**; temporal
  12.747.135 treino (73.031 pos.) / 5.311.972 teste (14.656 pos.); aleatório 12.641.374 / 5.417.733.
- **Colunas constantes do Understand:** 30 métricas (Avg*, CountDecl*, CountClass*, Max* exceto MaxNesting,
  PercentLackOfCohesion) são nulas em **todas** as linhas: o Understand só as calcula para classes/arquivos/pacotes, não
  para métodos. O mesmo ocorre no piloto (0 valores não nulos em 342.707 linhas) e no cpmp; com `fillna(0)` viram
  constantes sem efeito nos modelos. Mantidas para fidelidade ao cpmp; registradas em `meta.json` (`nan_por_coluna`).
  `RatioCommentToCode` (vírgula decimal no CSV do Understand) foi convertido corretamente na coleta (`s07_join.py`).
- **Teste rápido com amostra de 1%** pelo próprio `executar_tudo.sh`: fase 1 (288 jobs), fase 2 (12), fase 3 (2),
  coleta e zip sem falhas; retomada verificada (rodar de novo pula os 288 jobs concluídos); o vigia de memória
  encerrou e recolocou na fila 3 jobs (a máquina local tinha ~3 GB livres) e eles terminaram sozinhos.
  Repetido do zero com a versão final (float64): todas as etapas com código 0 e nenhum erro registrado.
- **Equivalência com o piloto** (`validacao/EQUIVALENCIA_PILOTO.md`): o código do pacote no dataset do piloto, protocolo
  temporal, reproduz exatamente (diferença ~1e-16) DT e RF com NONE/ROS/SMOTE e a LR do model3. A primeira versão,
  com matriz em float32, divergia (até 0,03 de AUC): por isso **tudo é feito em float64**, como no piloto. As
  diferenças restantes (ADASYN, LR do model1/model2, até 0,03) vêm do build das bibliotecas numéricas: o mesmo código
  no venv do piloto (pip, numpy 2.5.3) reproduz o piloto exatamente, e o ambiente conda-forge gera outro número de
  amostras no ADASYN (474.343 contra 474.395) de forma determinística. O ambiente do servidor é fixado pelo lock.
- **Tempos na amostra (s/job):** MLP com reamostragem ~350 s, LinearSVC com ROS até 64 s, demais < 35 s. Na matriz
  completa, ×100 ou mais: o MLP com reamostragem deve passar de 10 h por job (timeout configurado: 72 h).

## 10. Decisões pendentes
- Nenhuma (todas fechadas em 2026-10-15). O servidor tem acesso à internet.
