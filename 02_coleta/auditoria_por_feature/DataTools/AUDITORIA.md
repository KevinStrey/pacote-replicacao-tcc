# Auditoria da coleta: DataTools (`1-Repositorios/datatools`)

Gerado por `scripts/auditar_feature.py`. Decisões: `5-Coleta_features/INVENTARIO.md` (M1–M18); recursos e equivalência com o piloto: `5-Coleta_features/RECURSOS.md`.

## 1. Linha do tempo
- Snapshots: **24** (Oxygen.3 → 2026-06; índices globais 20..53); datas do calendário na série: 35; duplicatas removidas: 11; lacunas de presença atravessadas: 0.
- História linear verificada (s00). .java de produção: 4600 → 4639.
- Commits nos intervalos: 98; válidos: 98; importados por merge e excluídos (M6): 0.

## 2. Falhas de parsing do JavaParser (piloto: 0)
- Versões de arquivo únicas: 9099; **falhas: 0**; métodos (sem anônimos/locais): 108904; descartados por chave duplicada no arquivo: 0; textos distintos: 46607.

## 3. ChangeDistiller (piloto: 0 erros)
- Chamadas: 420; **erros (CDERROR): 0**.
- CK: logs com exceção: 0 ; CSVs do Understand: 24 de 24.

## 4. Taxas de match no join (piloto: ~100%)
- Mínimo por release: evo_in_ck = 0.9999, evo_in_und = 1.0000, ck_in_evo = 0.9948, und_in_evo = 0.9974.
- Média: evo_in_ck = 0.9999, evo_in_und = 1.0000. Tabela completa: `data/join_audit.csv`.

## 5. Dataset e positivos por release
- Linhas: **1184083**; positivos: **408** (0.03%). A última release não tem rótulo.

| Release (índice) | Tag | Métodos | Positivos | % |
|---|---|---|---|---|
| 20 | Oxygen.3 | 51321 | 27 | 0.05 |
| 21 | Photon.0 | 51321 | 1 | 0.00 |
| 22 | 2018-09 | 51322 | 0 | 0.00 |
| 23 | 2018-12 | 51322 | 8 | 0.02 |
| 24 | 2019-03 | 51322 | 3 | 0.01 |
| 25 | 2019-06 | 51322 | 0 | 0.00 |
| 27 | 2019-12 | 51322 | 0 | 0.00 |
| 28 | 2020-03 | 51322 | 1 | 0.00 |
| 30 | 2020-09 | 51322 | 0 | 0.00 |
| 31 | 2020-12 | 51322 | 0 | 0.00 |
| 32 | 2021-03 | 51322 | 0 | 0.00 |
| 33 | 2021-06 | 51322 | 1 | 0.00 |
| 34 | 2021-09 | 51322 | 0 | 0.00 |
| 36 | 2022-03 | 51322 | 361 | 0.70 |
| 41 | 2023-06 | 51322 | 0 | 0.00 |
| 42 | 2023-09 | 51322 | 1 | 0.00 |
| 43 | 2023-12 | 51843 | 2 | 0.00 |
| 44 | 2024-03 | 51843 | 0 | 0.00 |
| 46 | 2024-09 | 51843 | 2 | 0.00 |
| 47 | 2024-12 | 51851 | 1 | 0.00 |
| 48 | 2025-03 | 51851 | 0 | 0.00 |
| 49 | 2025-06 | 51851 | 0 | 0.00 |
| 51 | 2025-12 | 51851 | 0 | 0.00 |

## 6. Spot check das métricas evolutivas contra `git log -L`
- Método: `org.eclipse.datatools.enablement.mysql.catalog.loaders.MySqlTableColumnLoader.createResultSet()` (arquivo `plugins/enablement/org.eclipse.datatools.enablement.mysql/src/org/eclipse/datatools/enablement/mysql/catalog/loaders/MySqlTableColumnLoader.java`, linhas 37,43 em 46532a2d4c)
- Comando: `git -C 1-Repositorios/datatools log --no-merges --format=%H --no-patch -L37,43:plugins/enablement/org.eclipse.datatools.enablement.mysql/src/org/eclipse/datatools/enablement/mysql/catalog/loaders/MySqlTableColumnLoader.java 3b5fb7fbcc..46532a2d4c`
- Commits contados pela s05: 2 | listados pelo `git log -L`: 3 | em comum: 2 | contados e não listados: 0
- Resultado: **OK** (todos os commits contados estão no `git log -L`; os demais do git são mudanças em linhas vizinhas ou só de comentário/formatação)

## 7. Quebras de identidade de métodos (M28, ameaça à validade)
- Nascimentos após o 1º snapshot: 530; por mudança de pacote/classe: 0; em código importado (M6, heurística): 0.
- Efeito: histórico zerado (BOM = release da quebra; FRCH/CSB… recomeçam em 0) e método sem rótulo na transição. Detalhe: `data/identidade_metodos.csv`, `data/identidade_pares.csv`, `5-Coleta_features/AMEACA_identidade.md`.

- Nenhuma transição acima do limite (≥ 100 ou ≥ 1% dos métodos).
