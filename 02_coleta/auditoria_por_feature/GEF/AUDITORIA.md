# Auditoria da coleta: GEF (`1-Repositorios/gef-classic`)

Gerado por `scripts/auditar_feature.py`. Decisões: `5-Coleta_features/INVENTARIO.md` (M1–M18); recursos e equivalência com o piloto: `5-Coleta_features/RECURSOS.md`.

## 1. Linha do tempo
- Snapshots: **33** (JunoSR0 → 2026-09; índices globais 1..54); datas do calendário na série: 54; duplicatas removidas: 21; lacunas de presença atravessadas: 0.
- História linear verificada (s00). .java de produção: 693 → 780.
- Commits nos intervalos: 1294; válidos: 1140; importados por merge e excluídos (M6): 154.

## 2. Falhas de parsing do JavaParser (piloto: 0)
- Versões de arquivo únicas: 5591; **falhas: 0**; métodos (sem anônimos/locais): 90162; descartados por chave duplicada no arquivo: 148; textos distintos: 19125.

## 3. ChangeDistiller (piloto: 0 erros)
- Chamadas: 9911; **erros (CDERROR): 0**.
- CK: logs com exceção: 0 ; CSVs do Understand: 33 de 33.

## 4. Taxas de match no join (piloto: ~100%)
- Mínimo por release: evo_in_ck = 0.9971, evo_in_und = 1.0000, ck_in_evo = 0.9949, und_in_evo = 0.9645.
- Média: evo_in_ck = 0.9992, evo_in_und = 1.0000. Tabela completa: `data/join_audit.csv`.

## 5. Dataset e positivos por release
- Linhas: **233340**; positivos: **1468** (0.63%). A última release não tem rótulo.

| Release (índice) | Tag | Métodos | Positivos | % |
|---|---|---|---|---|
| 1 | JunoSR0 | 7116 | 0 | 0.00 |
| 2 | JunoSR1 | 7115 | 2 | 0.03 |
| 3 | JunoSR2 | 7116 | 0 | 0.00 |
| 4 | KeplerPostRC4 | 7116 | 0 | 0.00 |
| 5 | KeplerSR0 | 7116 | 0 | 0.00 |
| 6 | KeplerSR1 | 7116 | 4 | 0.06 |
| 7 | LunaSR0 | 7115 | 15 | 0.21 |
| 8 | LunaRC4 | 7123 | 6 | 0.08 |
| 9 | LunaSR2 | 7124 | 0 | 0.00 |
| 10 | S201504150911 | 7124 | 6 | 0.08 |
| 11 | Mars.1 | 7124 | 3 | 0.04 |
| 12 | Neon | 7127 | 0 | 0.00 |
| 13 | Neon.1 | 7127 | 0 | 0.00 |
| 16 | Oxygen | 7127 | 0 | 0.00 |
| 18 | Oxygen.1a | 7127 | 0 | 0.00 |
| 37 | 2022-06 | 7127 | 70 | 0.98 |
| 38 | 2022-09 | 7064 | 12 | 0.17 |
| 39 | 2022-12 | 7117 | 4 | 0.06 |
| 40 | 2023-03 | 7138 | 135 | 1.89 |
| 41 | 2023-06 | 7230 | 235 | 3.25 |
| 42 | 2023-09 | 7247 | 102 | 1.41 |
| 43 | 2023-12 | 7244 | 345 | 4.76 |
| 44 | 2024-03 | 7255 | 73 | 1.01 |
| 45 | 2024-06 | 7253 | 50 | 0.69 |
| 46 | 2024-09 | 6905 | 130 | 1.88 |
| 47 | 2024-12 | 7819 | 33 | 0.42 |
| 48 | 2025-03 | 7831 | 16 | 0.20 |
| 49 | 2025-06 | 7845 | 10 | 0.13 |
| 50 | 2025-09 | 7842 | 49 | 0.62 |
| 51 | 2025-12 | 7831 | 101 | 1.29 |
| 52 | 2026-03 | 7886 | 27 | 0.34 |
| 53 | 2026-06 | 7893 | 40 | 0.51 |

## 6. Spot check das métricas evolutivas contra `git log -L`
- Método: `org.eclipse.zest.core.widgets.Graph.DragSupport.mouseDoubleClicked(MouseEvent)` (arquivo `org.eclipse.zest.core/src/org/eclipse/zest/core/widgets/Graph.java`, linhas 946,1051 em 6cbd125303)
- Comando: `git -C 1-Repositorios/gef-classic log --no-merges --format=%H --no-patch -L946,1051:org.eclipse.zest.core/src/org/eclipse/zest/core/widgets/Graph.java 0a17cd7ad6..6cbd125303`
- Commits contados pela s05: 13 | listados pelo `git log -L`: 14 | em comum: 13 | contados e não listados: 0
- Resultado: **OK** (todos os commits contados estão no `git log -L`; os demais do git são mudanças em linhas vizinhas ou só de comentário/formatação)

## 7. Quebras de identidade de métodos (M28, ameaça à validade)
- Nascimentos após o 1º snapshot: 1656; por mudança de pacote/classe: 82; em código importado (M6, heurística): 551.
- Efeito: histórico zerado (BOM = release da quebra; FRCH/CSB… recomeçam em 0) e método sem rótulo na transição. Detalhe: `data/identidade_metodos.csv`, `data/identidade_pares.csv`, `5-Coleta_features/AMEACA_identidade.md`.

| Transição | Métodos | Nascidos / sumidos | Movidos | Importados |
|---|---|---|---|---|
| 2024-09 → 2024-12 | 7834 | 916 / 361 | 49 | 551 |
