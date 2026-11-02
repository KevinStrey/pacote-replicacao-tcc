# Resumo da análise dos resultados (fase 1)

Taxa de positivos no teste (referência do acaso para PR-AUC): {'random': np.float64(0.00486), 'temporal': np.float64(0.00276)}

## temporal: PR AUC (AP), máximo sobre reamostragens

| algoritmo | model1 | model2 | model3 |
|---|---|---|---|
| DT | 0.0038 | 0.0035 | 0.0035 |
| RandomForest | 0.0048 | 0.0083 | 0.0028 |
| LogisticRegression | 0.0083 | 0.0099 | 0.0134 |
| LinearSVC | 0.0090 | 0.0107 | 0.0101 |
| MLP | 0.0112 | 0.0153 | 0.0120 |
| XGBoost | 0.0110 | 0.0130 | 0.0056 |
| LightGBM | 0.0102 | 0.0175 | 0.0166 |

## temporal: ROC AUC score, máximo sobre reamostragens

| algoritmo | model1 | model2 | model3 |
|---|---|---|---|
| DT | 0.5025 | 0.5215 | 0.4506 |
| RandomForest | 0.6267 | 0.6653 | 0.4763 |
| LogisticRegression | 0.7446 | 0.7514 | 0.6390 |
| LinearSVC | 0.7484 | 0.7623 | 0.6457 |
| MLP | 0.7845 | 0.7897 | 0.7014 |
| XGBoost | 0.7862 | 0.7698 | 0.5655 |
| LightGBM | 0.7915 | 0.8010 | 0.6963 |

## temporal: MCC, máximo sobre reamostragens

| algoritmo | model1 | model2 | model3 |
|---|---|---|---|
| DT | 0.0139 | 0.0200 | 0.0068 |
| RandomForest | 0.0091 | 0.0074 | 0.0039 |
| LogisticRegression | 0.0436 | 0.0446 | 0.0291 |
| LinearSVC | 0.0438 | 0.0478 | 0.0397 |
| MLP | 0.0511 | 0.0487 | 0.0383 |
| XGBoost | 0.0507 | 0.0460 | 0.0159 |
| LightGBM | 0.0513 | 0.0521 | 0.0313 |

## temporal: PR-AUC média por reamostragem (sobre os 3 conjuntos)

| algoritmo | NONE | ROS | SMOTE | ADA |
|---|---|---|---|---|
| DT | 0.0032 | 0.0032 | 0.0034 | 0.0035 |
| RandomForest | 0.0041 | 0.0038 | 0.0053 | 0.0051 |
| LogisticRegression | 0.0097 | 0.0096 | 0.0095 | 0.0105 |
| LinearSVC | 0.0097 | 0.0097 | 0.0094 | 0.0099 |
| MLP | 0.0114 | 0.0124 | 0.0112 | 0.0090 |
| XGBoost | 0.0095 | 0.0098 | 0.0070 | 0.0066 |
| LightGBM | 0.0144 | 0.0148 | 0.0090 | 0.0083 |

temporal: lift da melhor PR-AUC sobre o acaso = 6.4x

## random: PR AUC (AP), máximo sobre reamostragens

| algoritmo | model1 | model2 | model3 |
|---|---|---|---|
| DT | 0.0646 | 0.0948 | 0.0863 |
| RandomForest | 0.1009 | 0.2035 | 0.1565 |
| LogisticRegression | 0.0258 | 0.0392 | 0.0324 |
| LinearSVC | 0.0262 | 0.0444 | 0.0443 |
| MLP | nan | nan | nan |
| XGBoost | 0.1151 | 0.2223 | 0.1852 |
| LightGBM | 0.1018 | 0.2081 | 0.1734 |

## random: ROC AUC score, máximo sobre reamostragens

| algoritmo | model1 | model2 | model3 |
|---|---|---|---|
| DT | 0.6161 | 0.6223 | 0.5766 |
| RandomForest | 0.7761 | 0.8352 | 0.6128 |
| LogisticRegression | 0.8037 | 0.8144 | 0.6614 |
| LinearSVC | 0.8063 | 0.8204 | 0.6681 |
| MLP | nan | nan | nan |
| XGBoost | 0.8546 | 0.8814 | 0.7456 |
| LightGBM | 0.8480 | 0.8741 | 0.7461 |

## random: MCC, máximo sobre reamostragens

| algoritmo | model1 | model2 | model3 |
|---|---|---|---|
| DT | 0.1290 | 0.1993 | 0.0637 |
| RandomForest | 0.1313 | 0.1943 | 0.0655 |
| LogisticRegression | 0.0773 | 0.0834 | 0.0622 |
| LinearSVC | 0.0793 | 0.0870 | 0.0731 |
| MLP | nan | nan | nan |
| XGBoost | 0.1368 | 0.2322 | 0.0838 |
| LightGBM | 0.1195 | 0.2088 | 0.0893 |

## random: PR-AUC média por reamostragem (sobre os 3 conjuntos)

| algoritmo | NONE | ROS | SMOTE | ADA |
|---|---|---|---|---|
| DT | 0.0786 | 0.0789 | 0.0717 | 0.0685 |
| RandomForest | 0.0997 | 0.0977 | 0.1536 | 0.1455 |
| LogisticRegression | 0.0319 | 0.0316 | 0.0319 | 0.0277 |
| LinearSVC | 0.0369 | 0.0375 | 0.0383 | 0.0352 |
| MLP | nan | nan | nan | nan |
| XGBoost | 0.1668 | 0.1742 | 0.1525 | 0.1023 |
| LightGBM | 0.1574 | 0.1605 | 0.1455 | 0.0916 |

random: lift da melhor PR-AUC sobre o acaso = 45.8x

Aleatório: correlação entre PR-AUC média da CV e PR-AUC no teste = 0.999; maior |CV - teste| = 0.0095; DP médio entre partes = 0.0045

Tempo de CPU-job somado (fase 1): 410 h; job mais longo: 21.1 h; pico de RAM máximo: 91 GB
Mediana de minutos por job de teste, por algoritmo: {'DT': 19.8, 'RandomForest': 17.0, 'LogisticRegression': 11.9, 'LinearSVC': 68.2, 'MLP': 199.1, 'XGBoost': 3.3, 'LightGBM': 3.5}

Melhor temporal: fase1__temporal__principal__model2__ROS__LightGBM__teste PR-AUC=0.0175 ROC=0.8007 MCC=0.0521

## Por feature (melhor temporal)

| feature | linhas | positivos | taxa | PR AUC (AP) | lift | ROC AUC score | MCC |
|---|---|---|---|---|---|---|---|
| WebTools | 417999 | 265 | 0.0006 | 0.0151 | 23.8566 | 0.9231 | 0.0575 |
| EMF | 361901 | 213 | 0.0006 | 0.0708 | 120.3585 | 0.8738 | 0.0337 |
| CDT | 1163788 | 496 | 0.0004 | 0.0054 | 12.5814 | 0.8623 | 0.0283 |
| m2e | 129942 | 443 | 0.0034 | 0.0201 | 5.8969 | 0.8311 | 0.0644 |
| DataTools | 465577 | 6 | 0.0000 | 0.0003 | 22.9854 | 0.8190 | 0.0073 |
| Scout | 465183 | 1044 | 0.0022 | 0.0130 | 5.7982 | 0.7991 | 0.0461 |
| JDT | 457900 | 4975 | 0.0109 | 0.0545 | 5.0166 | 0.7950 | 0.0952 |
| EGit | 123805 | 177 | 0.0014 | 0.0075 | 5.2725 | 0.7755 | 0.0318 |
| GMF Runtime | 170180 | 77 | 0.0005 | 0.0011 | 2.5199 | 0.7571 | 0.0164 |
| GEF | 126527 | 1432 | 0.0113 | 0.0255 | 2.2532 | 0.7459 | 0.0728 |
| PDE | 441519 | 1335 | 0.0030 | 0.0076 | 2.5293 | 0.7401 | 0.0403 |
| Window Builder | 334452 | 2769 | 0.0083 | 0.0195 | 2.3559 | 0.7099 | 0.0546 |
| RAP | 356490 | 142 | 0.0004 | 0.0229 | 57.5787 | 0.6771 | 0.0106 |
| Mylyn | 296709 | 1282 | 0.0043 | 0.0089 | 2.0676 | 0.6748 | 0.0312 |

## Nível de feature: previsões ingênuas

| medida | spearman_medio | spearman_IC95_inf | spearman_IC95_sup | acerto_top3_medio |
|---|---|---|---|---|
| taxa (persistencia) | 0.6837 | 0.5523 | 0.7922 | 0.6667 |
| taxa (media_historica) | 0.0767 | -0.0409 | 0.1995 | 0.0980 |
| volume (persistencia) | 0.6538 | 0.5515 | 0.7456 | 0.5098 |
| volume (media_historica) | 0.1921 | 0.0968 | 0.2917 | 0.1569 |

taxa (score_medio): 84 configurações; melhor Spearman 0.635; mediana 0.286; superam a persistência (dif > 0): 0; IC da diferença > 0: 0; IC < 0 (pior): 74

taxa (taxa_prevista): 84 configurações; melhor Spearman 0.622; mediana 0.277; superam a persistência (dif > 0): 0; IC da diferença > 0: 0; IC < 0 (pior): 80

taxa (risco_topo5): 84 configurações; melhor Spearman 0.628; mediana 0.287; superam a persistência (dif > 0): 0; IC da diferença > 0: 0; IC < 0 (pior): 80

volume (mudancas_previstas): 84 configurações; melhor Spearman 0.571; mediana 0.303; superam a persistência (dif > 0): 0; IC da diferença > 0: 0; IC < 0 (pior): 84

## Melhor por algoritmo (taxa, probabilidade média)

| algoritmo | conjunto | reamostragem | spearman_medio | spearman_IC95_inf | spearman_IC95_sup | acerto_top3_medio | dif_vs_persistencia | dif_IC95_inf | dif_IC95_sup |
|---|---|---|---|---|---|---|---|---|---|
| LinearSVC | model3 | ROS | 0.6346 | 0.5808 | 0.6862 | 0.5882 | -0.0491 | -0.1318 | 0.0451 |
| LogisticRegression | model3 | ADA | 0.6245 | 0.5552 | 0.6845 | 0.5294 | -0.0593 | -0.1410 | 0.0295 |
| RandomForest | model2 | SMOTE | 0.5900 | 0.5077 | 0.6783 | 0.3333 | -0.0937 | -0.1949 | 0.0334 |
| MLP | model3 | ROS | 0.5867 | 0.5010 | 0.6654 | 0.5294 | -0.0970 | -0.1838 | -0.0028 |
| DT | model2 | ADA | 0.5038 | 0.4156 | 0.5984 | 0.3333 | -0.1799 | -0.2793 | -0.0659 |
| XGBoost | model1 | NONE | 0.3997 | 0.3158 | 0.4887 | 0.3333 | -0.2841 | -0.3727 | -0.1860 |
| LightGBM | model3 | ROS | 0.3956 | 0.2602 | 0.5043 | 0.2745 | -0.2882 | -0.3947 | -0.1763 |

Spearman (taxa) por conjunto de métricas: {'mean': {'model1': 0.246, 'model2': 0.299, 'model3': 0.113}, 'max': {'model1': 0.438, 'model2': 0.59, 'model3': 0.635}}

Melhor modelo no nível de método (fase1__temporal__principal__model2__ROS__LightGBM__teste) no nível de feature: Spearman 0.381 [0.285, 0.475], top3 0.137

## Spearman por release (fase1__temporal__principal__model3__ROS__LinearSVC__teste x persistência x fase1__temporal__principal__model2__ROS__LightGBM__teste)

| release | modelo | persistencia | melhor_metodo | features |
|---|---|---|---|---|
| 37 | 0.4615 | 0.1399 | 0.2378 | 12 |
| 38 | 0.6573 | 0.6993 | 0.4685 | 12 |
| 39 | 0.6378 | 0.5786 | 0.3417 | 11 |
| 40 | 0.4545 | 0.0175 | 0.0769 | 12 |
| 41 | 0.5253 | 0.6099 | 0.0462 | 14 |
| 42 | 0.4593 | 0.6571 | 0.5868 | 14 |
| 43 | 0.6264 | 0.9505 | 0.5330 | 13 |
| 44 | 0.7503 | 0.7723 | 0.6293 | 14 |
| 45 | 0.6648 | 0.8846 | 0.5879 | 13 |
| 46 | 0.6044 | 0.7308 | 0.0165 | 13 |
| 47 | 0.7582 | 0.8418 | 0.3901 | 13 |
| 48 | 0.6249 | 0.6953 | 0.5127 | 14 |
| 49 | 0.7182 | 0.7801 | 0.7017 | 13 |
| 50 | 0.7273 | 0.8371 | 0.2098 | 12 |
| 51 | 0.8177 | 0.8354 | 0.3315 | 13 |
| 52 | 0.5909 | 0.8838 | 0.4000 | 11 |
| 53 | 0.7091 | 0.7091 | 0.4091 | 11 |
Releases em que o modelo supera a persistência: 3 de 17

## Ranking (melhor configuração no nível de feature)

| feature | posicao_real | posicao_prevista | taxa_real_media | score_medio | mudancas_reais | releases |
|---|---|---|---|---|---|---|
| GEF | 1 | 1 | 0.01154 | 0.08236 | 1432 | 17 |
| JDT | 2 | 3 | 0.01097 | -0.02439 | 4975 | 17 |
| Window Builder | 3 | 6 | 0.00829 | -0.09339 | 2769 | 17 |
| Mylyn | 4 | 8 | 0.00427 | -0.10320 | 1282 | 13 |
| m2e | 5 | 4 | 0.00348 | -0.05483 | 443 | 17 |
| PDE | 6 | 2 | 0.00308 | -0.02191 | 1335 | 17 |
| Scout | 7 | 7 | 0.00224 | -0.09583 | 1044 | 17 |
| EGit | 8 | 5 | 0.00143 | -0.06911 | 177 | 17 |
| WebTools | 9 | 9 | 0.00063 | -0.12809 | 265 | 12 |
| EMF | 10 | 11 | 0.00061 | -0.13358 | 213 | 17 |
| GMF Runtime | 11 | 13 | 0.00045 | -0.17982 | 77 | 16 |
| CDT | 12 | 10 | 0.00043 | -0.13014 | 496 | 17 |
| RAP | 13 | 12 | 0.00040 | -0.16404 | 142 | 12 |
| DataTools | 14 | 14 | 0.00001 | -0.18171 | 6 | 9 |
Spearman entre as posições médias real e prevista: 0.864
Spearman entre taxa média real e persistência média: 0.916

## Importância LightGBM model2 ROS (temporal): participação das evolutivas = 31.4%

| coluna | v |
|---|---|
| BOM | 0.059 |
| BOM | 0.054 |
| modifiers | 0.029 |
| modifiers | 0.029 |
| LCH | 0.024 |
| LCH | 0.024 |
| WCH | 0.024 |
| CountLineCode | 0.024 |
| loc | 0.023 |
| WCH | 0.022 |

## Importância RandomForest model2 SMOTE (temporal): participação das evolutivas = 13.9%

| coluna | v |
|---|---|
| rfc | 0.059 |
| methodsInvokedQty | 0.056 |
| CountOutput | 0.043 |
| CountLineCodeDecl | 0.035 |
| maxNestedBlocksQty | 0.034 |
| uniqueWordsQty | 0.028 |
| CountInput | 0.028 |
| CountStmtDecl | 0.027 |
| cbo | 0.025 |
| fanout | 0.025 |

## Importância XGBoost model2 ROS (temporal): participação das evolutivas = 20.4%

| coluna | v |
|---|---|
| loc | 0.239 |
| CountSemicolon | 0.093 |
| WCH | 0.086 |
| hasJavaDoc | 0.044 |
| CountOutput | 0.038 |
| rfc | 0.035 |
| anonymousClassesQty | 0.034 |
| BOM | 0.024 |
| stringLiteralsQty | 0.024 |
| lambdasQty | 0.020 |

Taxa de positivos por release: min 0.102% (r=31), max 2.492% (r=2); média treino (r<=36) 0.573%, teste 0.276%
