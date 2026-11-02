# Auditoria da coleta: m2e (`1-Repositorios/m2e-core`)

Gerado por `scripts/auditar_feature.py`. Decisões: `5-Coleta_features/INVENTARIO.md` (M1–M18); recursos e equivalência com o piloto: `5-Coleta_features/RECURSOS.md`.

## 1. Linha do tempo
- Snapshots: **54** (JunoSR0 → 2026-09; índices globais 1..54); datas do calendário na série: 54; duplicatas removidas: 0; lacunas de presença atravessadas: 0.
- História linear verificada (s00). .java de produção: 625 → 840.
- Commits nos intervalos: 2322; válidos: 2202; importados por merge e excluídos (M6): 120.

## 2. Falhas de parsing do JavaParser (piloto: 0)
- Versões de arquivo únicas: 6982; **falhas: 1**; métodos (sem anônimos/locais): 95037; descartados por chave duplicada no arquivo: 95; textos distintos: 17030.

## 3. ChangeDistiller (piloto: 0 erros)
- Chamadas: 7029; **erros (CDERROR): 0**.
- CK: logs com exceção: 0 ; CSVs do Understand: 54 de 54.

## 4. Taxas de match no join (piloto: ~100%)
- Mínimo por release: evo_in_ck = 0.9977, evo_in_und = 1.0000, ck_in_evo = 0.9927, und_in_evo = 0.9258.
- Média: evo_in_ck = 0.9993, evo_in_und = 1.0000. Tabela completa: `data/join_audit.csv`.

## 5. Dataset e positivos por release
- Linhas: **384483**; positivos: **1696** (0.44%). A última release não tem rótulo.

| Release (índice) | Tag | Métodos | Positivos | % |
|---|---|---|---|---|
| 1 | JunoSR0 | 6356 | 27 | 0.42 |
| 2 | JunoSR1 | 6380 | 79 | 1.24 |
| 3 | JunoSR2 | 6654 | 38 | 0.57 |
| 4 | KeplerPostRC4 | 6683 | 65 | 0.97 |
| 5 | KeplerSR0 | 6711 | 16 | 0.24 |
| 6 | KeplerSR1 | 6436 | 168 | 2.61 |
| 7 | LunaSR0 | 6874 | 35 | 0.51 |
| 8 | LunaRC4 | 6901 | 62 | 0.90 |
| 9 | LunaSR2 | 6973 | 24 | 0.34 |
| 10 | S201504150911 | 6953 | 29 | 0.42 |
| 11 | Mars.1 | 6904 | 66 | 0.96 |
| 12 | Neon | 7121 | 8 | 0.11 |
| 13 | Neon.1 | 7130 | 3 | 0.04 |
| 14 | Neon.2 | 7134 | 3 | 0.04 |
| 15 | Neon.3 | 7134 | 2 | 0.03 |
| 16 | Oxygen | 7126 | 6 | 0.08 |
| 17 | Oxygen.1 | 7149 | 1 | 0.01 |
| 18 | Oxygen.1a | 7158 | 0 | 0.00 |
| 19 | Oxygen.2 | 7146 | 16 | 0.22 |
| 20 | Oxygen.3 | 7182 | 83 | 1.16 |
| 21 | Photon.0 | 7259 | 11 | 0.15 |
| 22 | 2018-09 | 7259 | 1 | 0.01 |
| 23 | 2018-12 | 7267 | 7 | 0.10 |
| 24 | 2019-03 | 7265 | 26 | 0.36 |
| 25 | 2019-06 | 7277 | 10 | 0.14 |
| 26 | 2019-09 | 7279 | 26 | 0.36 |
| 27 | 2019-12 | 7264 | 31 | 0.43 |
| 28 | 2020-03 | 7083 | 20 | 0.28 |
| 29 | 2020-06 | 7315 | 2 | 0.03 |
| 30 | 2020-09 | 7312 | 28 | 0.38 |
| 31 | 2020-12 | 7342 | 6 | 0.08 |
| 32 | 2021-03 | 7420 | 77 | 1.04 |
| 33 | 2021-06 | 7408 | 69 | 0.93 |
| 34 | 2021-09 | 7477 | 14 | 0.19 |
| 35 | 2021-12 | 7117 | 71 | 1.00 |
| 36 | 2022-03 | 7092 | 123 | 1.73 |
| 37 | 2022-06 | 7324 | 117 | 1.60 |
| 38 | 2022-09 | 7350 | 103 | 1.40 |
| 39 | 2022-12 | 7464 | 44 | 0.59 |
| 40 | 2023-03 | 7594 | 23 | 0.30 |
| 41 | 2023-06 | 7627 | 20 | 0.26 |
| 42 | 2023-09 | 7671 | 43 | 0.56 |
| 43 | 2023-12 | 7653 | 48 | 0.63 |
| 44 | 2024-03 | 7706 | 2 | 0.03 |
| 45 | 2024-06 | 7708 | 1 | 0.01 |
| 46 | 2024-09 | 7719 | 2 | 0.03 |
| 47 | 2024-12 | 7718 | 9 | 0.12 |
| 48 | 2025-03 | 7741 | 0 | 0.00 |
| 49 | 2025-06 | 7744 | 3 | 0.04 |
| 50 | 2025-09 | 7625 | 9 | 0.12 |
| 51 | 2025-12 | 7760 | 4 | 0.05 |
| 52 | 2026-03 | 7759 | 8 | 0.10 |
| 53 | 2026-06 | 7779 | 7 | 0.09 |

## 6. Spot check das métricas evolutivas contra `git log -L`
- Método: `org.eclipse.m2e.core.internal.MavenPluginActivator.start(BundleContext)` (arquivo `org.eclipse.m2e.core/src/org/eclipse/m2e/core/internal/MavenPluginActivator.java`, linhas 88,108 em 19318e846c)
- Comando: `git -C 1-Repositorios/m2e-core log --no-merges --format=%H --no-patch -L88,108:org.eclipse.m2e.core/src/org/eclipse/m2e/core/internal/MavenPluginActivator.java 42829301c0..19318e846c`
- Commits contados pela s05: 23 | listados pelo `git log -L`: 24 | em comum: 23 | contados e não listados: 0
- Resultado: **OK** (todos os commits contados estão no `git log -L`; os demais do git são mudanças em linhas vizinhas ou só de comentário/formatação)

## 7. Quebras de identidade de métodos (M28, ameaça à validade)
- Nascimentos após o 1º snapshot: 3840; por mudança de pacote/classe: 835; em código importado (M6, heurística): 370.
- Efeito: histórico zerado (BOM = release da quebra; FRCH/CSB… recomeçam em 0) e método sem rótulo na transição. Detalhe: `data/identidade_metodos.csv`, `data/identidade_pares.csv`, `5-Coleta_features/AMEACA_identidade.md`.

| Transição | Métodos | Nascidos / sumidos | Movidos | Importados |
|---|---|---|---|---|
| KeplerSR1 → LunaSR0 | 6912 | 476 / 308 | 117 | 0 |
| 2020-03 → 2020-06 | 7315 | 232 / 220 | 195 | 0 |
| 2021-12 → 2022-03 | 7566 | 449 / 371 | 0 | 370 |
| 2022-03 → 2022-06 | 7488 | 396 / 474 | 277 | 0 |
| 2025-09 → 2025-12 | 7779 | 136 / 122 | 111 | 0 |
