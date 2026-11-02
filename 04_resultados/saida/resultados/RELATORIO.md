# Relatório do treino (principal)

Gerado em 2026-10-21 03:46:23 por `scripts/collect_results.py`. Plano: `PLANO_TREINO.md`.

- Dados: 18059107 linhas, 87687 positivos; corte temporal T = 36
- Configurações avaliadas no teste: 158; partes de CV: 720; jobs com erro registrado: 0

## Situação das fases

- fase1: total 864, concluídos antes 0, concluídos agora 864, pendentes 0, falhas 0 (atualizado 2026-10-19 16:40:45)
- fase2: total 12, concluídos antes 0, concluídos agora 12, pendentes 0, falhas 0 (atualizado 2026-10-21 03:22:14)
- fase3: total 2, concluídos antes 0, concluídos agora 2, pendentes 0, falhas 0 (atualizado 2026-10-21 03:33:13)

## Protocolo random: 15 melhores por PR-AUC (teste)

| conjunto | reamostragem | algoritmo | PR AUC (AP) | ROC AUC score | MCC | F1(class1) | precision | Sensitivity | segundos | cv_ap_media | cv_auc_media |
|---|---|---|---|---|---|---|---|---|---|---|---|
| model2 | ROS | XGBoost | 0.2223 | 0.8813 | 0.1026 | 0.0380 | 0.0195 | 0.7711 | 216.6000 | 0.2170 | 0.8784 |
| model2 | NONE | XGBoost | 0.2193 | 0.8814 | 0.1032 | 0.0384 | 0.0197 | 0.7697 | 128.1000 | 0.2144 | 0.8783 |
| model2 | ROS | LightGBM | 0.2081 | 0.8738 | 0.0968 | 0.0348 | 0.0178 | 0.7804 | 200.9000 | 0.2006 | 0.8709 |
| model2 | SMOTE | RandomForest | 0.2035 | 0.7939 | 0.1943 | 0.1976 | 0.1793 | 0.2200 | 1519.3000 | 0.1974 | 0.7981 |
| model2 | NONE | LightGBM | 0.2018 | 0.8741 | 0.0969 | 0.0347 | 0.0178 | 0.7830 | 124.8000 | 0.1975 | 0.8709 |
| model2 | ADA | RandomForest | 0.1937 | 0.7993 | 0.1842 | 0.1869 | 0.1637 | 0.2177 | 1972.2000 | 0.1878 | 0.7964 |
| model2 | SMOTE | LightGBM | 0.1898 | 0.7923 | 0.2088 | 0.2109 | 0.1840 | 0.2470 | 248.0000 | 0.1811 | 0.7880 |
| model2 | SMOTE | XGBoost | 0.1862 | 0.7819 | 0.2322 | 0.2353 | 0.2508 | 0.2215 | 265.0000 | 0.1910 | 0.7820 |
| model3 | ROS | XGBoost | 0.1852 | 0.7454 | 0.0837 | 0.0405 | 0.0211 | 0.4940 | 94.1000 | 0.1808 | 0.7427 |
| model3 | NONE | XGBoost | 0.1825 | 0.7456 | 0.0836 | 0.0401 | 0.0209 | 0.4995 | 69.8000 | 0.1796 | 0.7430 |
| model3 | NONE | LightGBM | 0.1734 | 0.7461 | 0.0832 | 0.0401 | 0.0209 | 0.4947 | 64.6000 | 0.1698 | 0.7439 |
| model3 | ROS | LightGBM | 0.1716 | 0.7461 | 0.0831 | 0.0400 | 0.0208 | 0.4965 | 88.8000 | 0.1696 | 0.7433 |
| model3 | SMOTE | XGBoost | 0.1714 | 0.6952 | 0.0838 | 0.0471 | 0.0251 | 0.3957 | 122.5000 | 0.1668 | 0.6933 |
| model3 | SMOTE | LightGBM | 0.1624 | 0.7138 | 0.0893 | 0.0498 | 0.0265 | 0.4153 | 121.1000 | 0.1573 | 0.7098 |
| model3 | SMOTE | RandomForest | 0.1565 | 0.6128 | 0.0655 | 0.0416 | 0.0224 | 0.2908 | 583.2000 | 0.1523 | 0.6096 |

## Protocolo temporal: 15 melhores por PR-AUC (teste)

| conjunto | reamostragem | algoritmo | PR AUC (AP) | ROC AUC score | MCC | F1(class1) | precision | Sensitivity | segundos |
|---|---|---|---|---|---|---|---|---|---|
| model2 | ROS | LightGBM | 0.0175 | 0.8007 | 0.0521 | 0.0150 | 0.0076 | 0.6671 | 220.4000 |
| model2 | NONE | LightGBM | 0.0172 | 0.8010 | 0.0521 | 0.0150 | 0.0076 | 0.6657 | 117.2000 |
| model3 | ROS | LightGBM | 0.0166 | 0.6963 | 0.0313 | 0.0107 | 0.0054 | 0.5479 | 102.1000 |
| model3 | NONE | LightGBM | 0.0159 | 0.6865 | 0.0294 | 0.0102 | 0.0052 | 0.5434 | 74.3000 |
| model2 | ROS | MLP | 0.0153 | 0.7897 | 0.0487 | 0.0133 | 0.0067 | 0.7134 | 15169.9000 |
| model2 | SMOTE | MLP | 0.0135 | 0.7100 | 0.0358 | 0.0119 | 0.0060 | 0.5457 | 35673.6000 |
| model3 | ADA | LogisticRegression | 0.0134 | 0.6390 | 0.0291 | 0.0103 | 0.0052 | 0.5336 | 2498.7000 |
| model2 | ROS | XGBoost | 0.0130 | 0.7698 | 0.0460 | 0.0147 | 0.0074 | 0.5658 | 215.5000 |
| model2 | NONE | MLP | 0.0129 | 0.7676 | 0.0365 | 0.0160 | 0.1633 | 0.0084 | 3805.1000 |
| model2 | NONE | XGBoost | 0.0129 | 0.7656 | 0.0460 | 0.0156 | 0.0079 | 0.5133 | 140.5000 |
| model2 | SMOTE | LightGBM | 0.0128 | 0.6782 | 0.0426 | 0.0446 | 0.0360 | 0.0587 | 258.9000 |
| model2 | ADA | LightGBM | 0.0122 | 0.6798 | 0.0377 | 0.0401 | 0.0332 | 0.0507 | 1031.0000 |
| model3 | NONE | MLP | 0.0120 | 0.6348 | 0.0383 | 0.0156 | 0.1854 | 0.0081 | 1622.3000 |
| model3 | SMOTE | LogisticRegression | 0.0116 | 0.6180 | 0.0283 | 0.0133 | 0.0068 | 0.2938 | 123.5000 |
| model3 | NONE | LogisticRegression | 0.0116 | 0.6175 | 0.0286 | 0.0135 | 0.0069 | 0.2890 | 67.2000 |

## Melhor configuração por protocolo e algoritmo (IC 95% por bootstrap)

| protocolo | algoritmo | conjunto | reamostragem | PR AUC (AP) | PR AUC (AP) IC95 inf | PR AUC (AP) IC95 sup | ROC AUC score | MCC |
|---|---|---|---|---|---|---|---|---|
| random | XGBoost | model2 | ROS | 0.2223 | 0.2171 | 0.2274 | 0.8813 | 0.1026 |
| random | LightGBM | model2 | ROS | 0.2081 | 0.2031 | 0.2132 | 0.8738 | 0.0968 |
| random | RandomForest | model2 | SMOTE | 0.2035 | 0.1985 | 0.2086 | 0.7939 | 0.1943 |
| random | DT | model2 | NONE | 0.0948 | 0.0911 | 0.0983 | 0.6155 | 0.1068 |
| random | LinearSVC | model2 | SMOTE | 0.0444 | 0.0429 | 0.0460 | 0.8199 | 0.0864 |
| random | LogisticRegression | model2 | SMOTE | 0.0392 | 0.0379 | 0.0405 | 0.8143 | 0.0825 |
| temporal | LightGBM | model2 | ROS | 0.0175 | 0.0165 | 0.0189 | 0.8007 | 0.0521 |
| temporal | MLP | model2 | ROS | 0.0153 | 0.0141 | 0.0166 | 0.7897 | 0.0487 |
| temporal | LogisticRegression | model3 | ADA | 0.0134 | 0.0123 | 0.0147 | 0.6390 | 0.0291 |
| temporal | XGBoost | model2 | ROS | 0.0130 | 0.0122 | 0.0141 | 0.7698 | 0.0460 |
| temporal | LinearSVC | model2 | ROS | 0.0107 | 0.0103 | 0.0113 | 0.7622 | 0.0478 |
| temporal | RandomForest | model2 | SMOTE | 0.0083 | 0.0080 | 0.0086 | 0.6413 | 0.0074 |
| temporal | DT | model1 | NONE | 0.0038 | 0.0036 | 0.0039 | 0.4951 | 0.0136 |

## Análise de sensibilidade (sem PTP, Scout e Mylyn)

| protocolo | configuracao | metrica | principal_teste_completo | principal_restrito | variante | diferenca_variante_menos_restrito_IC95 | diferenca_inclui_zero |
|---|---|---|---|---|---|---|---|
| random | model2 ROS XGBoost | PR AUC (AP) | 0.2223 | 0.2495 | 0.2516 | 0.0007–0.0036 | False |
| random | model2 ROS XGBoost | ROC AUC score | 0.8813 | 0.8893 | 0.8911 | 0.0010–0.0027 | False |
| random | model2 ROS XGBoost | MCC | 0.1026 | 0.1024 | 0.1052 | 0.0022–0.0035 | False |
| temporal | model2 ROS LightGBM | PR AUC (AP) | 0.0175 | 0.0199 | 0.0241 | 0.0031–0.0054 | False |
| temporal | model2 ROS LightGBM | ROC AUC score | 0.8007 | 0.8115 | 0.8229 | 0.0103–0.0124 | False |
| temporal | model2 ROS LightGBM | MCC | 0.0521 | 0.0547 | 0.0594 | 0.0040–0.0053 | False |

## Nível de feature: propensão a mudança (protocolo temporal)

Ordem das features por release de teste: previsto (agregação do modelo de métodos) x real. Detalhes em `nivel_feature_*.csv` e `scripts/nivel_feature.py`.

### Previsões ingênuas (sem aprendizado)

| medida | releases | spearman_medio | spearman_IC95_inf | spearman_IC95_sup | acerto_top3_medio |
|---|---|---|---|---|---|
| taxa (persistencia) | 17 | 0.6837 | 0.5523 | 0.7922 | 0.6667 |
| taxa (media_historica) | 17 | 0.0767 | -0.0409 | 0.1995 | 0.0980 |
| volume (persistencia) | 17 | 0.6538 | 0.5515 | 0.7456 | 0.5098 |
| volume (media_historica) | 17 | 0.1921 | 0.0968 | 0.2917 | 0.1569 |

### 10 melhores configurações (taxa prevista = probabilidade média)

| conjunto | reamostragem | algoritmo | releases | spearman_medio | spearman_IC95_inf | spearman_IC95_sup | acerto_top3_medio | dif_vs_persistencia | dif_IC95_inf | dif_IC95_sup |
|---|---|---|---|---|---|---|---|---|---|---|
| model3 | ROS | LinearSVC | 17 | 0.6346 | 0.5808 | 0.6862 | 0.5882 | -0.0491 | -0.1318 | 0.0451 |
| model3 | SMOTE | LinearSVC | 17 | 0.6326 | 0.5785 | 0.6881 | 0.5882 | -0.0511 | -0.1355 | 0.0475 |
| model3 | NONE | LinearSVC | 17 | 0.6306 | 0.5781 | 0.6820 | 0.5882 | -0.0531 | -0.1366 | 0.0441 |
| model3 | ADA | LinearSVC | 17 | 0.6285 | 0.5761 | 0.6826 | 0.5882 | -0.0552 | -0.1395 | 0.0413 |
| model3 | ADA | LogisticRegression | 17 | 0.6245 | 0.5552 | 0.6845 | 0.5294 | -0.0593 | -0.1410 | 0.0295 |
| model3 | NONE | LogisticRegression | 17 | 0.6035 | 0.5144 | 0.6788 | 0.5098 | -0.0802 | -0.1652 | 0.0095 |
| model3 | SMOTE | LogisticRegression | 17 | 0.5989 | 0.5127 | 0.6757 | 0.5098 | -0.0848 | -0.1754 | 0.0085 |
| model3 | ROS | LogisticRegression | 17 | 0.5966 | 0.5119 | 0.6726 | 0.5098 | -0.0871 | -0.1774 | 0.0055 |
| model2 | SMOTE | RandomForest | 17 | 0.5900 | 0.5077 | 0.6783 | 0.3333 | -0.0937 | -0.1949 | 0.0334 |
| model3 | ROS | MLP | 17 | 0.5867 | 0.5010 | 0.6654 | 0.5294 | -0.0970 | -0.1838 | -0.0028 |

### Features: ordem real x prevista (melhor configuração: `fase1__temporal__principal__model3__ROS__LinearSVC__teste`)

| feature | posicao_real | posicao_prevista | taxa_real_media | score_medio | mudancas_reais | mudancas_previstas | releases |
|---|---|---|---|---|---|---|---|
| GEF | 1 | 1 | 0.01154 | 0.08236 | 1432 | 80885 | 17 |
| JDT | 2 | 3 | 0.01097 | -0.02439 | 4975 | 187609 | 17 |
| Window Builder | 3 | 6 | 0.00829 | -0.09339 | 2769 | 77232 | 17 |
| Mylyn | 4 | 8 | 0.00427 | -0.10320 | 1282 | 70331 | 13 |
| m2e | 5 | 4 | 0.00348 | -0.05483 | 443 | 41851 | 17 |
| PDE | 6 | 2 | 0.00308 | -0.02191 | 1335 | 144795 | 17 |
| Scout | 7 | 7 | 0.00224 | -0.09583 | 1044 | 98705 | 17 |
| EGit | 8 | 5 | 0.00143 | -0.06911 | 177 | 32684 | 17 |
| WebTools | 9 | 9 | 0.00063 | -0.12809 | 265 | 62952 | 12 |
| EMF | 10 | 11 | 0.00061 | -0.13358 | 213 | 37126 | 17 |
| GMF Runtime | 11 | 13 | 0.00045 | -0.17982 | 77 | 3186 | 16 |
| CDT | 12 | 10 | 0.00043 | -0.13014 | 496 | 165843 | 17 |
| RAP | 13 | 12 | 0.00040 | -0.16404 | 142 | 17578 | 12 |
| DataTools | 14 | 14 | 0.00001 | -0.18171 | 6 | 3692 | 9 |
