# Auditoria da coleta: JDT (`1-Repositorios/eclipse.jdt.core`)

Gerado por `scripts/auditar_feature.py`. Decisões: `5-Coleta_features/INVENTARIO.md` (M1–M18); recursos e equivalência com o piloto: `5-Coleta_features/RECURSOS.md`.

## 1. Linha do tempo
- Snapshots: **54** (JunoSR0 → 2026-09; índices globais 1..54); datas do calendário na série: 54; duplicatas removidas: 0; lacunas de presença atravessadas: 0.
- História linear verificada (s00). .java de produção: 1458 → 1844.
- Commits nos intervalos: 8550; válidos: 8550; importados por merge e excluídos (M6): 0.

## 2. Falhas de parsing do JavaParser (piloto: 0)
- Versões de arquivo únicas: 31583; **falhas: 40**; métodos (sem anônimos/locais): 1781785; descartados por chave duplicada no arquivo: 121; textos distintos: 70595.

## 3. ChangeDistiller (piloto: 0 erros)
- Chamadas: 26917; **erros (CDERROR): 0**.
- CK: logs com exceção: 0 ; CSVs do Understand: 54 de 54.

## 4. Taxas de match no join (piloto: ~100%)
- Mínimo por release: evo_in_ck = 0.9978, evo_in_und = 0.9789, ck_in_evo = 0.9818, und_in_evo = 0.9746.
- Média: evo_in_ck = 0.9996, evo_in_und = 0.9989. Tabela completa: `data/join_audit.csv`.

## 5. Dataset e positivos por release
- Linhas: **1336291**; positivos: **13108** (0.98%). A última release não tem rótulo.

| Release (índice) | Tag | Métodos | Positivos | % |
|---|---|---|---|---|
| 1 | JunoSR0 | 20219 | 55 | 0.27 |
| 2 | JunoSR1 | 20093 | 391 | 1.95 |
| 3 | JunoSR2 | 20455 | 413 | 2.02 |
| 4 | KeplerPostRC4 | 20890 | 26 | 0.12 |
| 5 | KeplerSR0 | 20872 | 282 | 1.35 |
| 6 | KeplerSR1 | 20888 | 751 | 3.60 |
| 7 | LunaSR0 | 21915 | 113 | 0.52 |
| 8 | LunaRC4 | 21318 | 417 | 1.96 |
| 9 | LunaSR2 | 22158 | 135 | 0.61 |
| 10 | S201504150911 | 22206 | 210 | 0.95 |
| 11 | Mars.1 | 22231 | 485 | 2.18 |
| 12 | Neon | 22509 | 87 | 0.39 |
| 13 | Neon.1 | 22503 | 158 | 0.70 |
| 14 | Neon.2 | 23992 | 200 | 0.83 |
| 15 | Neon.3 | 24097 | 165 | 0.68 |
| 16 | Oxygen | 24263 | 14 | 0.06 |
| 17 | Oxygen.1 | 24133 | 424 | 1.76 |
| 18 | Oxygen.1a | 25798 | 119 | 0.46 |
| 19 | Oxygen.2 | 25761 | 406 | 1.58 |
| 20 | Oxygen.3 | 26027 | 228 | 0.88 |
| 21 | Photon.0 | 26130 | 99 | 0.38 |
| 22 | 2018-09 | 26186 | 92 | 0.35 |
| 23 | 2018-12 | 26250 | 122 | 0.46 |
| 24 | 2019-03 | 26312 | 189 | 0.72 |
| 25 | 2019-06 | 26472 | 229 | 0.87 |
| 26 | 2019-09 | 26555 | 163 | 0.61 |
| 27 | 2019-12 | 26719 | 73 | 0.27 |
| 28 | 2020-03 | 26723 | 590 | 2.21 |
| 29 | 2020-06 | 27213 | 64 | 0.24 |
| 30 | 2020-09 | 27197 | 238 | 0.88 |
| 31 | 2020-12 | 27482 | 41 | 0.15 |
| 32 | 2021-03 | 27503 | 394 | 1.43 |
| 33 | 2021-06 | 26048 | 393 | 1.51 |
| 34 | 2021-09 | 26278 | 152 | 0.58 |
| 35 | 2021-12 | 26479 | 100 | 0.38 |
| 36 | 2022-03 | 26516 | 115 | 0.43 |
| 37 | 2022-06 | 26691 | 62 | 0.23 |
| 38 | 2022-09 | 26756 | 82 | 0.31 |
| 39 | 2022-12 | 26707 | 167 | 0.63 |
| 40 | 2023-03 | 26851 | 252 | 0.94 |
| 41 | 2023-06 | 26867 | 98 | 0.36 |
| 42 | 2023-09 | 26351 | 513 | 1.95 |
| 43 | 2023-12 | 26136 | 1450 | 5.55 |
| 44 | 2024-03 | 26957 | 549 | 2.04 |
| 45 | 2024-06 | 27069 | 162 | 0.60 |
| 46 | 2024-09 | 26780 | 268 | 1.00 |
| 47 | 2024-12 | 27142 | 168 | 0.62 |
| 48 | 2025-03 | 27029 | 621 | 2.30 |
| 49 | 2025-06 | 27155 | 204 | 0.75 |
| 50 | 2025-09 | 27257 | 120 | 0.44 |
| 51 | 2025-12 | 27338 | 93 | 0.34 |
| 52 | 2026-03 | 27386 | 47 | 0.17 |
| 53 | 2026-06 | 27428 | 119 | 0.43 |

## 6. Spot check das métricas evolutivas contra `git log -L`
- Método: `org.eclipse.jdt.internal.compiler.parser.Parser.consumeRule(int)` (arquivo `org.eclipse.jdt.core.compiler.batch/src/org/eclipse/jdt/internal/compiler/parser/Parser.java`, linhas 6454,8158 em 8c40c7d2ae)
- Comando: `git -C 1-Repositorios/eclipse.jdt.core log --no-merges --format=%H --no-patch -L6454,8158:org.eclipse.jdt.core.compiler.batch/src/org/eclipse/jdt/internal/compiler/parser/Parser.java 29b2c21843..8c40c7d2ae`
- Commits contados pela s05: 88 | listados pelo `git log -L`: 90 | em comum: 86 | contados e não listados: 2
- Resultado: **VERIFICAR** (commits contados fora do `git log -L`: 30c7385ebc, ea65681e2c)

## 7. Quebras de identidade de métodos (M28, ameaça à validade)
- Nascimentos após o 1º snapshot: 13264; por mudança de pacote/classe: 7; em código importado (M6, heurística): 0.
- Efeito: histórico zerado (BOM = release da quebra; FRCH/CSB… recomeçam em 0) e método sem rótulo na transição. Detalhe: `data/identidade_metodos.csv`, `data/identidade_pares.csv`, `5-Coleta_features/AMEACA_identidade.md`.

- Nenhuma transição acima do limite (≥ 100 ou ≥ 1% dos métodos).
