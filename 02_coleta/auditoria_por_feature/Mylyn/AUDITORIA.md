# Auditoria da coleta: Mylyn (`1-Repositorios/org.eclipse.mylyn`)

Gerado por `scripts/auditar_feature.py`. Decisões: `5-Coleta_features/INVENTARIO.md` (M1–M18); recursos e equivalência com o piloto: `5-Coleta_features/RECURSOS.md`.

## 1. Linha do tempo
- Snapshots: **14** (2023-06 → 2026-09; índices globais 41..54); datas do calendário na série: 14; duplicatas removidas: 0; lacunas de presença atravessadas: 0.
- História linear verificada (s00). .java de produção: 2581 → 3188.
- Commits nos intervalos: 3239; válidos: 1277; importados por merge e excluídos (M6): 1962.

## 2. Falhas de parsing do JavaParser (piloto: 0)
- Versões de arquivo únicas: 8841; **falhas: 1**; métodos (sem anônimos/locais): 75248; descartados por chave duplicada no arquivo: 9; textos distintos: 31622.

## 3. ChangeDistiller (piloto: 0 erros)
- Chamadas: 7851; **erros (CDERROR): 0**.
- CK: logs com exceção: 0 ; CSVs do Understand: 14 de 14.

## 4. Taxas de match no join (piloto: ~100%)
- Mínimo por release: evo_in_ck = 1.0000, evo_in_und = 1.0000, ck_in_evo = 0.9899, und_in_evo = 0.9776.
- Média: evo_in_ck = 1.0000, evo_in_und = 1.0000. Tabela completa: `data/join_audit.csv`.

## 5. Dataset e positivos por release
- Linhas: **296709**; positivos: **1282** (0.43%). A última release não tem rótulo.

| Release (índice) | Tag | Métodos | Positivos | % |
|---|---|---|---|---|
| 41 | 2023-06 | 17891 | 22 | 0.12 |
| 42 | 2023-09 | 17498 | 109 | 0.62 |
| 43 | 2023-12 | 24086 | 892 | 3.70 |
| 44 | 2024-03 | 24087 | 59 | 0.24 |
| 45 | 2024-06 | 24086 | 58 | 0.24 |
| 46 | 2024-09 | 24109 | 0 | 0.00 |
| 47 | 2024-12 | 24109 | 4 | 0.02 |
| 48 | 2025-03 | 24109 | 2 | 0.01 |
| 49 | 2025-06 | 23584 | 30 | 0.13 |
| 50 | 2025-09 | 23642 | 4 | 0.02 |
| 51 | 2025-12 | 23665 | 3 | 0.01 |
| 52 | 2026-03 | 23601 | 37 | 0.16 |
| 53 | 2026-06 | 22242 | 62 | 0.28 |

## 6. Spot check das métricas evolutivas contra `git log -L`
- Método: `org.eclipse.mylyn.internal.gitlab.ui.GitlabRepositorySettingsPage.createAdditionalControls(Composite)` (arquivo `mylyn.tasks/connectors/gitlab/org.eclipse.mylyn.gitlab.ui/src/org/eclipse/mylyn/internal/gitlab/ui/GitlabRepositorySettingsPage.java`, linhas 84,260 em af1cae9076)
- Comando: `git -C 1-Repositorios/org.eclipse.mylyn log --no-merges --format=%H --no-patch -L84,260:mylyn.tasks/connectors/gitlab/org.eclipse.mylyn.gitlab.ui/src/org/eclipse/mylyn/internal/gitlab/ui/GitlabRepositorySettingsPage.java 916f7f48a8..af1cae9076`
- Commits contados pela s05: 9 | listados pelo `git log -L`: 9 | em comum: 7 | contados e não listados: 2
- Resultado: **VERIFICAR** (commits contados fora do `git log -L`: d0a2f4d4f0, f3d06000be)

## 7. Quebras de identidade de métodos (M28, ameaça à validade)
- Nascimentos após o 1º snapshot: 8585; por mudança de pacote/classe: 51; em código importado (M6, heurística): 6546.
- Efeito: histórico zerado (BOM = release da quebra; FRCH/CSB… recomeçam em 0) e método sem rótulo na transição. Detalhe: `data/identidade_metodos.csv`, `data/identidade_pares.csv`, `5-Coleta_features/AMEACA_identidade.md`.

| Transição | Métodos | Nascidos / sumidos | Movidos | Importados |
|---|---|---|---|---|
| 2023-09 → 2023-12 | 24090 | 6592 / 703 | 0 | 6546 |
