# Relatório do treino (teste_rapido)

Gerado em 2026-10-15 21:08:28 por `scripts/collect_results.py`. Plano: `PLANO_TREINO.md`.

- Dados: 180596 linhas, 880 positivos; corte temporal T = 36 (amostra 0.01)
- Configurações avaliadas no teste: 158; partes de CV: 144; jobs com erro registrado: 0

## Situação das fases

- fase1: total 288, concluídos antes 0, concluídos agora 288, pendentes 0, falhas 0 (atualizado 2026-10-15 20:55:52)
- fase2: total 12, concluídos antes 0, concluídos agora 12, pendentes 0, falhas 0 (atualizado 2026-10-15 21:07:52)
- fase3: total 2, concluídos antes 0, concluídos agora 2, pendentes 0, falhas 0 (atualizado 2026-10-15 21:08:00)

## Protocolo random: 15 melhores por PR-AUC (teste)

| conjunto | reamostragem | algoritmo | PR AUC (AP) | ROC AUC score | MCC | F1(class1) | precision | Sensitivity | segundos | cv_ap_media | cv_auc_media |
|---|---|---|---|---|---|---|---|---|---|---|---|
| model2 | NONE | LightGBM | 0.1878 | 0.8066 | 0.1120 | 0.0670 | 0.0363 | 0.4318 | 2.1000 | 0.1374 | 0.8009 |
| model2 | ROS | LightGBM | 0.1827 | 0.8102 | 0.1133 | 0.0674 | 0.0365 | 0.4394 | 2.6000 | 0.1267 | 0.7846 |
| model2 | SMOTE | LightGBM | 0.1821 | 0.8096 | 0.2872 | 0.2442 | 0.5250 | 0.1591 | 4.0000 | 0.1607 | 0.8084 |
| model2 | ADA | LightGBM | 0.1687 | 0.8142 | 0.2736 | 0.2386 | 0.4773 | 0.1591 | 4.0000 | 0.1541 | 0.8104 |
| model2 | SMOTE | XGBoost | 0.1611 | 0.7906 | 0.2895 | 0.2236 | 0.6207 | 0.1364 | 3.6000 | 0.1472 | 0.7867 |
| model2 | ROS | XGBoost | 0.1548 | 0.7124 | 0.1051 | 0.0931 | 0.0594 | 0.2159 | 2.5000 | 0.1340 | 0.7042 |
| model2 | ADA | XGBoost | 0.1541 | 0.7915 | 0.2776 | 0.2202 | 0.5714 | 0.1364 | 3.7000 | 0.1379 | 0.7802 |
| model3 | NONE | LightGBM | 0.1536 | 0.6251 | 0.0666 | 0.0415 | 0.0223 | 0.3030 | 1.3000 | 0.1087 | 0.5765 |
| model3 | ROS | LightGBM | 0.1491 | 0.6375 | 0.0734 | 0.0450 | 0.0241 | 0.3258 | 1.7000 | 0.1030 | 0.5540 |
| model2 | NONE | XGBoost | 0.1461 | 0.7228 | 0.1153 | 0.1023 | 0.0657 | 0.2311 | 1.7000 | 0.1192 | 0.7060 |
| model2 | SMOTE | RandomForest | 0.1406 | 0.8131 | 0.2725 | 0.2222 | 0.5362 | 0.1402 | 10.6000 | 0.1233 | 0.7939 |
| model2 | ADA | RandomForest | 0.1389 | 0.8151 | 0.2612 | 0.2149 | 0.5070 | 0.1364 | 10.2000 | 0.1153 | 0.7836 |
| model3 | NONE | XGBoost | 0.1322 | 0.5406 | 0.0563 | 0.0384 | 0.0209 | 0.2424 | 1.2000 | 0.0887 | 0.4847 |
| model3 | SMOTE | LightGBM | 0.1321 | 0.5754 | 0.0615 | 0.0436 | 0.0240 | 0.2348 | 1.8000 | 0.1021 | 0.5661 |
| model3 | ROS | XGBoost | 0.1311 | 0.5537 | 0.0525 | 0.0363 | 0.0197 | 0.2311 | 1.4000 | 0.0865 | 0.4832 |

## Protocolo temporal: 15 melhores por PR-AUC (teste)

| conjunto | reamostragem | algoritmo | PR AUC (AP) | ROC AUC score | MCC | F1(class1) | precision | Sensitivity | segundos |
|---|---|---|---|---|---|---|---|---|---|
| model2 | NONE | LogisticRegression | 0.0202 | 0.7323 | 0.0438 | 0.0144 | 0.0073 | 0.5436 | 3.8000 |
| model2 | ROS | LogisticRegression | 0.0183 | 0.7383 | 0.0439 | 0.0145 | 0.0073 | 0.5436 | 8.5000 |
| model2 | NONE | LinearSVC | 0.0173 | 0.7400 | 0.0419 | 0.0140 | 0.0071 | 0.5302 | 13.3000 |
| model2 | ROS | LinearSVC | 0.0167 | 0.7396 | 0.0409 | 0.0139 | 0.0071 | 0.5168 | 19.4000 |
| model2 | SMOTE | LogisticRegression | 0.0160 | 0.7298 | 0.0412 | 0.0140 | 0.0071 | 0.5168 | 8.2000 |
| model3 | ROS | LogisticRegression | 0.0143 | 0.6165 | 0.0263 | 0.0104 | 0.0053 | 0.4497 | 1.6000 |
| model2 | ADA | LinearSVC | 0.0141 | 0.7239 | 0.0424 | 0.0134 | 0.0068 | 0.5839 | 12.9000 |
| model2 | SMOTE | LinearSVC | 0.0140 | 0.7253 | 0.0437 | 0.0145 | 0.0073 | 0.5369 | 10.4000 |
| model1 | ADA | MLP | 0.0137 | 0.5340 | 0.0116 | 0.0090 | 0.0046 | 0.1678 | 713.5000 |
| model2 | ADA | LogisticRegression | 0.0137 | 0.7266 | 0.0411 | 0.0128 | 0.0065 | 0.5973 | 6.0000 |
| model3 | NONE | LogisticRegression | 0.0132 | 0.6057 | 0.0242 | 0.0099 | 0.0050 | 0.4497 | 0.9000 |
| model3 | ADA | LogisticRegression | 0.0124 | 0.6008 | 0.0228 | 0.0094 | 0.0047 | 0.4698 | 1.7000 |
| model3 | NONE | LinearSVC | 0.0122 | 0.6109 | 0.0274 | 0.0107 | 0.0054 | 0.4497 | 0.9000 |
| model1 | NONE | LogisticRegression | 0.0117 | 0.7287 | 0.0441 | 0.0145 | 0.0074 | 0.5436 | 2.1000 |
| model3 | ROS | LinearSVC | 0.0116 | 0.6115 | 0.0271 | 0.0107 | 0.0054 | 0.4430 | 2.9000 |

## Melhor configuração por protocolo e algoritmo (IC 95% por bootstrap)

| protocolo | algoritmo | conjunto | reamostragem | PR AUC (AP) | PR AUC (AP) IC95 inf | PR AUC (AP) IC95 sup | ROC AUC score | MCC |
|---|---|---|---|---|---|---|---|---|
| random | LightGBM | model2 | NONE | 0.1878 | 0.1298 | 0.2355 | 0.8066 | 0.1120 |
| random | XGBoost | model2 | SMOTE | 0.1611 | 0.1222 | 0.2166 | 0.7906 | 0.2895 |
| random | RandomForest | model2 | SMOTE | 0.1406 | 0.0948 | 0.1984 | 0.8131 | 0.2725 |
| random | LogisticRegression | model2 | NONE | 0.0495 | 0.0365 | 0.0653 | 0.8158 | 0.0856 |
| random | LinearSVC | model2 | ROS | 0.0450 | 0.0336 | 0.0586 | 0.8174 | 0.0922 |
| random | DT | model3 | ROS | 0.0382 | 0.0228 | 0.0592 | 0.4872 | 0.0423 |
| temporal | LogisticRegression | model2 | NONE | 0.0202 | 0.0107 | 0.0414 | 0.7323 | 0.0438 |
| temporal | LinearSVC | model2 | NONE | 0.0173 | 0.0099 | 0.0348 | 0.7400 | 0.0419 |
| temporal | MLP | model1 | ADA | 0.0137 | 0.0037 | 0.0351 | 0.5340 | 0.0116 |
| temporal | LightGBM | model2 | SMOTE | 0.0111 | 0.0081 | 0.0183 | 0.7000 | -0.0006 |
| temporal | XGBoost | model2 | ADA | 0.0100 | 0.0065 | 0.0299 | 0.6768 | 0.0406 |
| temporal | RandomForest | model2 | SMOTE | 0.0091 | 0.0072 | 0.0130 | 0.7278 | -0.0006 |
| temporal | DT | model3 | NONE | 0.0037 | 0.0024 | 0.0054 | 0.4783 | 0.0100 |

## Análise de sensibilidade (sem PTP, Scout e Mylyn)

| protocolo | configuracao | metrica | principal_teste_completo | principal_restrito | variante | diferenca_variante_menos_restrito_IC95 | diferenca_inclui_zero |
|---|---|---|---|---|---|---|---|
| random | model2 NONE LightGBM | PR AUC (AP) | 0.1878 | 0.2135 | 0.2057 | -0.0233–0.0116 | True |
| random | model2 NONE LightGBM | ROC AUC score | 0.8066 | 0.8106 | 0.8207 | -0.0088–0.0286 | True |
| random | model2 NONE LightGBM | MCC | 0.1120 | 0.1057 | 0.1203 | -0.0006–0.0284 | True |
| temporal | model2 NONE LogisticRegression | PR AUC (AP) | 0.0202 | 0.0222 | 0.0250 | 0.0005–0.0089 | False |
| temporal | model2 NONE LogisticRegression | ROC AUC score | 0.7323 | 0.7407 | 0.7512 | 0.0029–0.0193 | False |
| temporal | model2 NONE LogisticRegression | MCC | 0.0438 | 0.0461 | 0.0458 | -0.0058–0.0043 | True |

## Nível de feature: propensão a mudança (protocolo temporal)

Ordem das features por release de teste: previsto (agregação do modelo de métodos) x real. Detalhes em `nivel_feature_*.csv` e `scripts/nivel_feature.py`.

### Previsões ingênuas (sem aprendizado)

| medida | releases | spearman_medio | spearman_IC95_inf | spearman_IC95_sup | acerto_top3_medio |
|---|---|---|---|---|---|
| taxa (persistencia) | 17 | 0.3549 | 0.1406 | 0.5499 | 0.4706 |
| taxa (media_historica) | 17 | -0.0805 | -0.1817 | 0.0407 | 0.1569 |
| volume (persistencia) | 17 | 0.3450 | 0.1309 | 0.5408 | 0.4510 |
| volume (media_historica) | 17 | -0.0416 | -0.1111 | 0.0723 | 0.2549 |

### 10 melhores configurações (taxa prevista = probabilidade média)

| conjunto | reamostragem | algoritmo | releases | spearman_medio | spearman_IC95_inf | spearman_IC95_sup | acerto_top3_medio | dif_vs_persistencia | dif_IC95_inf | dif_IC95_sup |
|---|---|---|---|---|---|---|---|---|---|---|
| model2 | SMOTE | RandomForest | 17 | 0.2669 | 0.1041 | 0.3703 | 0.3333 | -0.0880 | -0.2898 | 0.1124 |
| model3 | ROS | LinearSVC | 17 | 0.2658 | 0.0736 | 0.4153 | 0.4118 | -0.0891 | -0.3529 | 0.1582 |
| model3 | NONE | LinearSVC | 17 | 0.2645 | 0.0952 | 0.4070 | 0.4118 | -0.0904 | -0.3318 | 0.1393 |
| model3 | ADA | LinearSVC | 17 | 0.2570 | 0.0579 | 0.4140 | 0.4118 | -0.0979 | -0.3683 | 0.1494 |
| model2 | ADA | RandomForest | 17 | 0.2529 | 0.1042 | 0.3636 | 0.3333 | -0.1020 | -0.2930 | 0.0692 |
| model3 | SMOTE | LinearSVC | 17 | 0.2518 | 0.0592 | 0.4013 | 0.4118 | -0.1031 | -0.3749 | 0.1420 |
| model3 | ROS | LogisticRegression | 17 | 0.2478 | 0.0996 | 0.3919 | 0.3922 | -0.1071 | -0.3505 | 0.1397 |
| model3 | ADA | LogisticRegression | 17 | 0.2448 | 0.0753 | 0.3817 | 0.4118 | -0.1101 | -0.3525 | 0.1250 |
| model3 | SMOTE | LogisticRegression | 17 | 0.2413 | 0.0912 | 0.3718 | 0.4118 | -0.1135 | -0.3424 | 0.1116 |
| model3 | NONE | LogisticRegression | 17 | 0.2314 | 0.0912 | 0.3645 | 0.3922 | -0.1235 | -0.3420 | 0.1162 |

### Features: ordem real x prevista (melhor configuração: `fase1__temporal__principal__model2__SMOTE__RandomForest__teste`)

| feature | posicao_real | posicao_prevista | taxa_real_media | score_medio | mudancas_reais | mudancas_previstas | releases |
|---|---|---|---|---|---|---|---|
| JDT | 1 | 4 | 0.01205 | 0.02089 | 53 | 1 | 17 |
| GEF | 2 | 1 | 0.01183 | 0.02449 | 15 | 0 | 17 |
| Window Builder | 3 | 7 | 0.00939 | 0.01585 | 31 | 0 | 17 |
| Mylyn | 4 | 5 | 0.00439 | 0.01810 | 13 | 1 | 13 |
| PDE | 5 | 2 | 0.00263 | 0.02385 | 11 | 1 | 17 |
| EGit | 6 | 3 | 0.00223 | 0.02155 | 3 | 0 | 17 |
| Scout | 7 | 8 | 0.00100 | 0.01392 | 5 | 1 | 17 |
| EMF | 8 | 10 | 0.00097 | 0.01242 | 3 | 0 | 17 |
| CDT | 9 | 9 | 0.00068 | 0.01260 | 8 | 2 | 17 |
| WebTools | 10 | 13 | 0.00068 | 0.00701 | 3 | 0 | 12 |
| m2e | 11 | 6 | 0.00066 | 0.01604 | 1 | 0 | 17 |
| GMF Runtime | 12 | 12 | 0.00061 | 0.00890 | 1 | 0 | 16 |
| RAP | 13 | 11 | 0.00056 | 0.00986 | 2 | 0 | 12 |
| DataTools | 14 | 14 | 0.00000 | 0.00664 | 0 | 1 | 9 |

## Tempos na amostra (s por job)

Na matriz completa o tempo cresce pelo menos 1/fração (×100); para RF, SMOTE e ADASYN, mais que isso.

| algoritmo | reamostragem | mean | max |
|---|---|---|---|
| DT | ADA | 9.3 | 17.3 |
| DT | NONE | 1.9 | 3.1 |
| DT | ROS | 4.9 | 9.3 |
| DT | SMOTE | 9.8 | 19.4 |
| LightGBM | ADA | 2.4 | 4.0 |
| LightGBM | NONE | 1.3 | 2.1 |
| LightGBM | ROS | 1.9 | 2.8 |
| LightGBM | SMOTE | 2.4 | 4.0 |
| LinearSVC | ADA | 8.2 | 17.7 |
| LinearSVC | NONE | 5.2 | 13.3 |
| LinearSVC | ROS | 13.0 | 30.4 |
| LinearSVC | SMOTE | 7.5 | 13.4 |
| LogisticRegression | ADA | 4.3 | 9.2 |
| LogisticRegression | NONE | 2.1 | 3.8 |
| LogisticRegression | ROS | 3.9 | 8.5 |
| LogisticRegression | SMOTE | 4.5 | 10.2 |
| MLP | ADA | 542.5 | 713.5 |
| MLP | NONE | 14.8 | 22.9 |
| MLP | ROS | 556.5 | 670.8 |
| MLP | SMOTE | 578.6 | 663.8 |
| RandomForest | ADA | 7.4 | 10.6 |
| RandomForest | NONE | 1.8 | 2.7 |
| RandomForest | ROS | 4.7 | 6.6 |
| RandomForest | SMOTE | 7.6 | 10.7 |
| XGBoost | ADA | 2.3 | 3.9 |
| XGBoost | NONE | 1.1 | 1.9 |
| XGBoost | ROS | 1.7 | 2.6 |
| XGBoost | SMOTE | 2.3 | 3.6 |
