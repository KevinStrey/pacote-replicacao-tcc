# Auditoria da coleta: EMF (`1-Repositorios/org.eclipse.emf`)

Gerado por `scripts/auditar_feature.py`. Decisões: `5-Coleta_features/INVENTARIO.md` (M1–M18); recursos e equivalência com o piloto: `5-Coleta_features/RECURSOS.md`.

## 1. Linha do tempo
- Snapshots: **54** (JunoSR0 → 2026-09; índices globais 1..54); datas do calendário na série: 54; duplicatas removidas: 0; lacunas de presença atravessadas: 0.
- História linear verificada (s00). .java de produção: 1540 → 1918.
- Commits nos intervalos: 2695; válidos: 1347; importados por merge e excluídos (M6): 1348.

## 2. Falhas de parsing do JavaParser (piloto: 0)
- Versões de arquivo únicas: 8417; **falhas: 1**; métodos (sem anônimos/locais): 335637; descartados por chave duplicada no arquivo: 50; textos distintos: 75306.

## 3. ChangeDistiller (piloto: 0 erros)
- Chamadas: 19392; **erros (CDERROR): 0**.
- CK: logs com exceção: 0 ; CSVs do Understand: 54 de 54.

## 4. Taxas de match no join (piloto: ~100%)
- Mínimo por release: evo_in_ck = 0.9773, evo_in_und = 1.0000, ck_in_evo = 0.6429, und_in_evo = 0.9943.
- Média: evo_in_ck = 0.9809, evo_in_und = 1.0000. Tabela completa: `data/join_audit.csv`.

## 5. Dataset e positivos por release
- Linhas: **960732**; positivos: **15453** (1.61%). A última release não tem rótulo.

| Release (índice) | Tag | Métodos | Positivos | % |
|---|---|---|---|---|
| 1 | JunoSR0 | 14666 | 1574 | 10.73 |
| 2 | JunoSR1 | 14534 | 2132 | 14.67 |
| 3 | JunoSR2 | 14760 | 2028 | 13.74 |
| 4 | KeplerPostRC4 | 15693 | 12 | 0.08 |
| 5 | KeplerSR0 | 15694 | 1644 | 10.48 |
| 6 | KeplerSR1 | 15530 | 1985 | 12.78 |
| 7 | LunaSR0 | 15970 | 515 | 3.22 |
| 8 | LunaRC4 | 16072 | 1911 | 11.89 |
| 9 | LunaSR2 | 16086 | 33 | 0.21 |
| 10 | S201504150911 | 16105 | 34 | 0.21 |
| 11 | Mars.1 | 16106 | 19 | 0.12 |
| 12 | Neon | 16096 | 2196 | 13.64 |
| 13 | Neon.1 | 16116 | 0 | 0.00 |
| 14 | Neon.2 | 16116 | 32 | 0.20 |
| 15 | Neon.3 | 16192 | 13 | 0.08 |
| 16 | Oxygen | 16227 | 110 | 0.68 |
| 17 | Oxygen.1 | 16289 | 91 | 0.56 |
| 18 | Oxygen.1a | 16769 | 27 | 0.16 |
| 19 | Oxygen.2 | 16774 | 123 | 0.73 |
| 20 | Oxygen.3 | 17075 | 28 | 0.16 |
| 21 | Photon.0 | 17079 | 140 | 0.82 |
| 22 | 2018-09 | 17065 | 31 | 0.18 |
| 23 | 2018-12 | 17088 | 13 | 0.08 |
| 24 | 2019-03 | 17096 | 43 | 0.25 |
| 25 | 2019-06 | 17106 | 77 | 0.45 |
| 26 | 2019-09 | 17852 | 6 | 0.03 |
| 27 | 2019-12 | 17852 | 16 | 0.09 |
| 28 | 2020-03 | 17852 | 8 | 0.04 |
| 29 | 2020-06 | 15613 | 352 | 2.25 |
| 30 | 2020-09 | 17907 | 9 | 0.05 |
| 31 | 2020-12 | 17908 | 6 | 0.03 |
| 32 | 2021-03 | 17908 | 10 | 0.06 |
| 33 | 2021-06 | 17908 | 5 | 0.03 |
| 34 | 2021-09 | 17908 | 3 | 0.02 |
| 35 | 2021-12 | 17909 | 12 | 0.07 |
| 36 | 2022-03 | 17910 | 2 | 0.01 |
| 37 | 2022-06 | 17910 | 27 | 0.15 |
| 38 | 2022-09 | 17925 | 5 | 0.03 |
| 39 | 2022-12 | 17924 | 38 | 0.21 |
| 40 | 2023-03 | 21991 | 1 | 0.00 |
| 41 | 2023-06 | 21991 | 8 | 0.04 |
| 42 | 2023-09 | 21990 | 9 | 0.04 |
| 43 | 2023-12 | 21991 | 6 | 0.03 |
| 44 | 2024-03 | 21994 | 40 | 0.18 |
| 45 | 2024-06 | 21994 | 10 | 0.05 |
| 46 | 2024-09 | 21994 | 33 | 0.15 |
| 47 | 2024-12 | 21995 | 5 | 0.02 |
| 48 | 2025-03 | 21995 | 9 | 0.04 |
| 49 | 2025-06 | 22023 | 4 | 0.02 |
| 50 | 2025-09 | 22046 | 7 | 0.03 |
| 51 | 2025-12 | 22046 | 5 | 0.02 |
| 52 | 2026-03 | 22046 | 3 | 0.01 |
| 53 | 2026-06 | 22046 | 3 | 0.01 |

## 6. Spot check das métricas evolutivas contra `git log -L`
- Método: `org.eclipse.emf.codegen.ecore.genmodel.impl.GenModelPackageImpl.initializePackageContents()` (arquivo `plugins/org.eclipse.emf.codegen.ecore/src/org/eclipse/emf/codegen/ecore/genmodel/impl/GenModelPackageImpl.java`, linhas 2946,3369 em 5504314ab7)
- Comando: `git -C 1-Repositorios/org.eclipse.emf log --no-merges --format=%H --no-patch -L2946,3369:plugins/org.eclipse.emf.codegen.ecore/src/org/eclipse/emf/codegen/ecore/genmodel/impl/GenModelPackageImpl.java b419d880e1..5504314ab7`
- Commits contados pela s05: 58 | listados pelo `git log -L`: 59 | em comum: 58 | contados e não listados: 0
- Resultado: **OK** (todos os commits contados estão no `git log -L`; os demais do git são mudanças em linhas vizinhas ou só de comentário/formatação)

## 7. Quebras de identidade de métodos (M28, ameaça à validade)
- Nascimentos após o 1º snapshot: 10791; por mudança de pacote/classe: 2252; em código importado (M6, heurística): 4025.
- Efeito: histórico zerado (BOM = release da quebra; FRCH/CSB… recomeçam em 0) e método sem rótulo na transição. Detalhe: `data/identidade_metodos.csv`, `data/identidade_pares.csv`, `5-Coleta_features/AMEACA_identidade.md`.

| Transição | Métodos | Nascidos / sumidos | Movidos | Importados |
|---|---|---|---|---|
| 2020-06 → 2020-09 | 18307 | 2294 / 2239 | 2226 | 0 |
| 2022-12 → 2023-03 | 22396 | 4068 / 1 | 0 | 4025 |
