# Gráficos para a apresentação

Gráficos para os slides, sem uso no texto do TCC. Cada um está em **PNG** (300 dpi, para slides) e **SVG** (vetorial,
não perde qualidade ao ampliar). Para gerar de novo, rode os scripts de `6-Treino/ferramentas_locais/`.

## resultados/ — uma versão gráfica de cada tabela do TCC (`graficos_resultados.py`)

| Arquivo | Tabela/figura do TCC | O que mostra |
|---|---|---|
| `t1_dataset_por_feature` | Tabela 1 | Tamanho do dataset e taxa de mudança de cada feature |
| `t4_melhores_por_algoritmo` | Tabela 5 | PR-AUC com IC 95% (temporal e aleatório) e ROC-AUC de cada algoritmo |
| `t4b_temporal_vs_aleatorio` | Tabela 5 | Melhor PR-AUC nos dois protocolos: o aleatório resulta em PR-AUC ≈ 13× maior |
| `c_pr_temporal`, `c_pr_random` | Tabela 5, Figuras 14 e 16 | Curvas precisão–recall da melhor configuração de cada algoritmo, com a linha do acaso (`graficos_curvas.py`; também em PDF) |
| `c_roc_temporal`, `c_roc_random` | Tabela 5, Figuras 15 e 17 | Curvas ROC da melhor configuração de cada algoritmo, com a diagonal do acaso (`graficos_curvas.py`; também em PDF) |
| `c_sens_pr`, `c_sens_roc` | Figuras 20 e 21 | Curvas PR e ROC da análise de sensibilidade: modelo principal × sem PTP, Scout e Mylyn, nas mesmas linhas de teste (`graficos_sensibilidade.py`; também em PDF) |
| `t5_grade_temporal` | Tabela 6 | Mapas de calor algoritmo × conjunto de métricas (PR-AUC e ROC-AUC) |
| `t5b_balanceamento_temporal` | Seção 4.3 | Efeito de NONE, ROS, SMOTE e ADASYN em cada algoritmo |
| `t6_desempenho_por_feature` | Tabela 7 | ROC-AUC e ganho sobre o acaso por feature |
| `t7_nivel_feature_spearman` | Tabela 8 | Spearman com IC: modelos × persistência × média histórica |
| `t8_ranking_real_previsto` | Tabela 9 | Ordem real × prevista das features (verde = exata) |
| `t9_sensibilidade` | Tabela 10 | PR-AUC com e sem PTP, Scout e Mylyn |
| `fig7_taxa_por_release` | Figura 13 | Taxa de métodos alterados por release, com o corte treino/teste |
| `fig8_spearman_por_release` | Figura 19 | Spearman por release: modelo × persistência |

## evolucao/ — evolução das features da LPS ao longo das releases (`graficos_evolucao.py`)

| Arquivo | O que mostra |
|---|---|
| `e01_numero_de_metodos` | Número de métodos de cada feature |
| `e02_loc_total` | Tamanho do código (soma do LOC dos métodos, em milhares) |
| `e03_loc_medio_por_metodo` | Média de linhas de código por método |
| `e04_complexidade_media` | Complexidade ciclomática média por método |
| `e05_acoplamento_medio` | Acoplamento médio (CBO) por método |
| `e06_csb_medio` | Média de CSB por método (mesmo estilo do gráfico do piloto) |
| `e07_linhas_alteradas` | Linhas alteradas entre uma release e a seguinte (escala log) |
| `e08_metodos_alterados` | Métodos alterados até a release seguinte (o rótulo do modelo) |
| `e09_taxa_de_mudanca` | % dos métodos alterados até a release seguinte |
| `e10_alteracoes_acumuladas` | Métodos alterados acumulados ao longo do tempo |
| `e11_metodos_novos` | Métodos novos por release (escala log) |
| `e12_mapa_calor_taxa_mudanca` | Mapa de calor feature × release da taxa de mudança, com o corte temporal |
| `e13_presenca_das_features` | Período em que cada feature fez parte da LPS e snapshots coletados |
| `e14_tamanho_da_lps_empilhado` | Tamanho total da LPS: métodos por feature em área empilhada |
| `dados_evolucao.csv` | Valores agregados usados nos gráficos e01–e14 |

Observação: o conjunto de dados contém as releases com rótulo; a última release de cada feature não aparece nos
gráficos de linha.

## didaticos/ — conceitos explicados com dados ilustrativos (`graficos_didaticos.py`)

Curvas calculadas com pontuações **sintéticas**, só para explicar os conceitos (não são resultados do TCC).

| Arquivo | O que mostra |
|---|---|
| `d1_curva_roc` | Curva ROC: modelo bom, razoável e fraco, classificador aleatório e perfeito |
| `d2_curva_precisao_revocacao` | Curva precisão-revocação com mudanças raras (0,5%), como no TCC |
| `d3_roc_vs_pr_classes_raras` | O mesmo modelo com 50% ou 0,5% de positivos: a ROC quase não muda, a PR despenca |
| `d4_validacao_temporal_vs_aleatoria` | Diferença entre a validação temporal e a aleatória |

## curvas_reais/ — curvas ROC e precisão-revocação dos modelos do TCC (`graficos_curvas_reais.py`)

Dependem do arquivo `curvas_roc_pr.csv`, gerado no servidor (as previsões de cada método ficaram lá):

1. Copie `6-Treino/scripts/curvas_roc_pr.py` para a pasta `treino_tcc/scripts/` do servidor.
2. No servidor, dentro de `treino_tcc`: `ambiente/bin/python scripts/curvas_roc_pr.py`
3. Traga `saida/resultados/curvas_roc_pr.csv` para `resultados_e_logs/saida/resultados/` aqui.
4. Rode `python 6-Treino/ferramentas_locais/graficos_curvas_reais.py`.

Saídas: `curvas_temporal`, `curvas_random` (estilo limpo) e `curvas_*_desenhado` (estilo desenhado à mão).

## predicoes/ — gráficos calculados com as previsões baixadas do servidor (`graficos_predicoes.py`)

Usa `predições/predicoes/*.npz` e `predições/prep/` (respostas e índices de teste; validados contra as métricas do
servidor, diferença máxima 1e-16). Cada algoritmo usa a mesma configuração da Tabela 5 do TCC (ver `selecao.csv`);
se faltar algum arquivo de previsão, o script usa a melhor configuração disponível e a marca com *.

| Arquivo | O que mostra |
|---|---|
| `p1_roc_pr_temporal`, `p1_roc_pr_aleatorio` | Curvas ROC e precisão-revocação da melhor configuração de cada algoritmo |
| `p2_temporal_vs_aleatorio` | O mesmo algoritmo (LightGBM, XGBoost) nos dois protocolos |
| `p3_curva_de_ganho_temporal` | Quantas mudanças se encontram revisando os X% métodos de maior risco |
| `p4_precisao_no_topo_temporal` | Precisão entre os 0,1%, 1%, 5%... métodos de maior risco |
| `p5_distribuicao_das_probabilidades` | Probabilidade prevista para métodos que mudaram e que não mudaram |
| `p6_matriz_de_confusao_temporal` | Matriz de confusão no limiar padrão |
| `p7_roc_por_feature_temporal` | Curva ROC de cada feature da LPS (mesmo modelo global) |

## por_feature/ — visão geral das análises por feature, protocolo temporal (`graficos_por_feature.py`)

`visao_geral.png` mostra todos lado a lado, para escolher. A = nível de método separado por feature; B = ranking de
features (centro do TCC).

| Arquivo | Parte | O que mostra |
|---|---|---|
| `f1_mapa_roc_feature_x_algoritmo` | A | ROC-AUC de cada algoritmo em cada feature; melhor e empates estatísticos marcados |
| `f2_pontos_roc_por_feature` | A | Mesmos valores em pontos: a distância entre o pior e o melhor algoritmo de cada feature |
| `f3_vitorias_por_algoritmo` | A | Em quantas features cada algoritmo é o melhor ou empata com o melhor |
| `f4_taxa_de_mudanca_x_roc` | A | Taxa de mudança da feature × ROC-AUC do LightGBM |
| `f5_ganho_sobre_acaso_feature_x_algoritmo` | A | PR-AUC ÷ acaso de cada algoritmo em cada feature |
| `f6_nivel_metodo_x_nivel_feature` | A × B | As 84 configurações: acerto em métodos × acerto no ranking de features |
| `f7_ranking_por_release_real_modelo_persistencia` | B | Posição de cada feature em cada release: real, modelo e persistência |
| `f8_spearman_nivel_feature` | B | Spearman do ranking de features: melhor de cada algoritmo × referências simples |
| `empates_roc.csv` | A | Dados dos empates (bootstrap pareado, 100 reamostragens) |
| `mapa_roc_feature_x_algoritmo.pptx` | A | O f1 como **tabela nativa do PowerPoint**, nas cores do modelo da apresentação (`mapa_roc_slide_pptx.js`: `node mapa_roc_slide_pptx.js empates_roc.csv saida.pptx`) |

## metricas/ — tabela-resumo das métricas para o slide (`tabela_metricas_slide.py`)

| Arquivo | O que mostra |
|---|---|
| `tabela_categorias_metricas` (.png/.svg) | Categorias e subcategorias das 98 métricas, com a quantidade e até 3 exemplos (versão completa: Tabela 3 do TCC) |
| `tabela_categorias_metricas.pptx` | A mesma tabela como **tabela nativa do PowerPoint**, nas cores do modelo da apresentação (`tabela_metricas_slide_pptx.js`, Node + pptxgenjs: `node tabela_metricas_slide_pptx.js saida.pptx`) |

## metricas_limiar/ — métricas que dependem do limiar (`graficos_metricas_limiar.py`)

Acurácia, precisão, revocação, F1 e MCC no limiar padrão de 0,5 (valores de `resultados_teste.csv`, conferidos contra
as previsões). Material de apoio: mostram por que a ROC-AUC e a PR-AUC foram as métricas principais.

| Arquivo | O que mostra |
|---|---|
| `m1_metricas_no_limiar_padrao` | As 5 métricas da melhor configuração de cada algoritmo, protocolo temporal |
| `m2_paradoxo_da_acuracia` | Acurácia × revocação: "sempre não muda" tem 99,7% de acurácia e não acha nada |
| `m3_metricas_por_limiar_lightgbm` | Como cada métrica muda com o limiar (LightGBM), de 0,01 a 0,99 |
| `m4_temporal_x_aleatorio_f1_mcc` | F1 e MCC nos dois protocolos |
| `m5_mcc_algoritmo_x_metricas` | MCC por algoritmo × conjunto de métricas |
| `tabela_metricas_limiar.csv` | Todas as métricas da melhor configuração de cada algoritmo (abre direto no Excel: `;` e vírgula decimal) |
