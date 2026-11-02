# Equivalência com o piloto (EGit, protocolo temporal)

Gerado por `ferramentas_locais/equivalencia_piloto.py`: código de treino do pacote (`scripts/models.py`, `scripts/metrics.py`) aplicado ao dataset do piloto (`4-Coleta_egit/data/egit-all-releases.csv`), comparado com `4-Coleta_egit/results/egit-results-trad_temporal.csv`.

- Linhas: 342707; corte T = 42; treino 240793; teste 101914.
- O pacote usa float64 em todas as etapas, como o piloto (float32 alterava cortes das árvores e vizinhos do SMOTE/ADASYN).
- Diferenças restantes (ADASYN; LR do model1/model2): build das bibliotecas numéricas. O mesmo código no venv do piloto (pip, numpy 2.5.3) reproduz o piloto exatamente (ex.: model3/ADA/DT AUC 0,368442); no ambiente conda-forge do pacote o ADASYN gera 474.343 amostras em vez de 474.395 (determinístico em cada ambiente).

| Conjunto | Reamostragem | Algoritmo | AUC pacote / piloto | AP pacote / piloto | MCC pacote / piloto | tp, fp pacote / piloto | Dif. máx. |
|---|---|---|---|---|---|---|---|
| model1 | NONE | DT | 0.5065 / 0.5065 | 0.0021 / 0.0021 | 0.0069 / 0.0069 | 6, 2706 / 6, 2706 | 6.1e-17 |
| model1 | NONE | RandomForest | 0.6317 / 0.6317 | 0.0041 / 0.0041 | 0.0173 / 0.0173 | 11, 2621 / 11, 2621 | 1.8e-17 |
| model1 | NONE | LogisticRegression | 0.7662 / 0.7665 | 0.0075 / 0.0075 | 0.0300 / 0.0300 | 59, 22019 / 59, 22022 | 3.4e-04 |
| model1 | ROS | DT | 0.5010 / 0.5010 | 0.0019 / 0.0019 | 0.0050 / 0.0050 | 5, 2684 / 5, 2684 | 9.5e-17 |
| model1 | ROS | RandomForest | 0.6075 / 0.6075 | 0.0040 / 0.0040 | 0.0015 / 0.0015 | 3, 2438 / 3, 2438 | 8.3e-17 |
| model1 | ROS | LogisticRegression | 0.7653 / 0.7661 | 0.0076 / 0.0075 | 0.0309 / 0.0317 | 60, 21910 / 61, 21868 | 8.3e-04 |
| model1 | SMOTE | DT | 0.5159 / 0.5159 | 0.0015 / 0.0015 | 0.0130 / 0.0130 | 3, 424 / 3, 424 | 6.9e-17 |
| model1 | SMOTE | RandomForest | 0.6143 / 0.6144 | 0.0062 / 0.0063 | 0.0269 / 0.0269 | 5, 318 / 5, 318 | 1.1e-04 |
| model1 | SMOTE | LogisticRegression | 0.7594 / 0.7579 | 0.0074 / 0.0072 | 0.0301 / 0.0286 | 60, 22584 / 58, 22527 | 1.5e-03 |
| model1 | ADA | DT | 0.5158 / 0.5052 | 0.0017 / 0.0019 | 0.0178 / 0.0207 | 4, 428 / 4, 331 | 1.1e-02 |
| model1 | ADA | RandomForest | 0.6259 / 0.6096 | 0.0064 / 0.0062 | 0.0237 / 0.0252 | 4, 260 / 4, 233 | 1.6e-02 |
| model1 | ADA | LogisticRegression | 0.7564 / 0.7542 | 0.0073 / 0.0072 | 0.0281 / 0.0280 | 59, 23664 / 59, 23729 | 2.2e-03 |
| model2 | NONE | DT | 0.5047 / 0.5047 | 0.0010 / 0.0010 | 0.0038 / 0.0038 | 2, 934 / 2, 934 | 5.2e-17 |
| model2 | NONE | RandomForest | 0.6532 / 0.6532 | 0.0028 / 0.0028 | 0.0045 / 0.0045 | 1, 279 / 1, 279 | 5.6e-17 |
| model2 | NONE | LogisticRegression | 0.7491 / 0.7486 | 0.0066 / 0.0066 | 0.0338 / 0.0337 | 51, 14821 / 51, 14895 | 4.2e-04 |
| model2 | ROS | DT | 0.5097 / 0.5097 | 0.0012 / 0.0012 | 0.0067 / 0.0067 | 3, 1010 / 3, 1010 | 4.6e-17 |
| model2 | ROS | RandomForest | 0.6592 / 0.6592 | 0.0030 / 0.0030 | 0.0123 / 0.0123 | 2, 221 / 2, 221 | 6.1e-17 |
| model2 | ROS | LogisticRegression | 0.7497 / 0.7478 | 0.0066 / 0.0066 | 0.0339 / 0.0342 | 51, 14782 / 51, 14610 | 1.9e-03 |
| model2 | SMOTE | DT | 0.5363 / 0.5363 | 0.0014 / 0.0014 | 0.0185 / 0.0185 | 9, 1712 / 9, 1712 | 6.9e-17 |
| model2 | SMOTE | RandomForest | 0.6760 / 0.6760 | 0.0068 / 0.0068 | 0.0405 / 0.0405 | 4, 94 / 4, 94 | 5.2e-07 |
| model2 | SMOTE | LogisticRegression | 0.7334 / 0.7325 | 0.0065 / 0.0064 | 0.0320 / 0.0314 | 50, 15349 / 49, 15199 | 9.1e-04 |
| model2 | ADA | DT | 0.5614 / 0.5616 | 0.0016 / 0.0015 | 0.0196 / 0.0195 | 11, 2218 / 11, 2236 | 2.5e-04 |
| model2 | ADA | RandomForest | 0.6858 / 0.6856 | 0.0087 / 0.0074 | 0.0439 / 0.0403 | 4, 80 / 4, 95 | 3.6e-03 |
| model2 | ADA | LogisticRegression | 0.7342 / 0.7351 | 0.0065 / 0.0065 | 0.0308 / 0.0308 | 51, 16664 / 51, 16637 | 8.9e-04 |
| model3 | NONE | DT | 0.3963 / 0.3963 | 0.0010 / 0.0010 | 0.0009 / 0.0009 | 6, 5757 / 6, 5757 | 8.0e-17 |
| model3 | NONE | RandomForest | 0.4178 / 0.4178 | 0.0008 / 0.0008 | -0.0013 / -0.0013 | 4, 5278 / 4, 5278 | 1.6e-07 |
| model3 | NONE | LogisticRegression | 0.6041 / 0.6041 | 0.0037 / 0.0037 | 0.0260 / 0.0260 | 38, 12372 / 38, 12372 | 2.3e-06 |
| model3 | ROS | DT | 0.3876 / 0.3876 | 0.0009 / 0.0009 | -0.0003 / -0.0003 | 5, 5598 / 5, 5598 | 2.7e-17 |
| model3 | ROS | RandomForest | 0.4096 / 0.4096 | 0.0007 / 0.0007 | -0.0013 / -0.0013 | 4, 5236 / 4, 5236 | 9.9e-17 |
| model3 | ROS | LogisticRegression | 0.6043 / 0.6043 | 0.0037 / 0.0037 | 0.0259 / 0.0259 | 38, 12395 / 38, 12395 | 2.4e-06 |
| model3 | SMOTE | DT | 0.3699 / 0.3699 | 0.0008 / 0.0008 | -0.0006 / -0.0006 | 5, 5819 / 5, 5819 | 6.2e-17 |
| model3 | SMOTE | RandomForest | 0.4338 / 0.4338 | 0.0008 / 0.0008 | -0.0006 / -0.0006 | 4, 4719 / 4, 4719 | 1.1e-16 |
| model3 | SMOTE | LogisticRegression | 0.5977 / 0.5977 | 0.0040 / 0.0040 | 0.0246 / 0.0246 | 36, 12068 / 36, 12068 | 2.1e-06 |
| model3 | ADA | DT | 0.3984 / 0.3684 | 0.0010 / 0.0008 | 0.0046 / -0.0001 | 9, 5999 / 5, 5416 | 3.0e-02 |
| model3 | ADA | RandomForest | 0.4444 / 0.4346 | 0.0008 / 0.0008 | -0.0007 / -0.0007 | 4, 4789 / 4, 4788 | 9.7e-03 |
| model3 | ADA | LogisticRegression | 0.5944 / 0.5940 | 0.0037 / 0.0038 | 0.0244 / 0.0245 | 38, 13304 / 38, 13246 | 4.1e-04 |
