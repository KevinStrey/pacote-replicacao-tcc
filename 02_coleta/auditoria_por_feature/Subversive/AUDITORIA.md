# Auditoria da coleta: Subversive (`1-Repositorios/subversive`)

Gerado por `scripts/auditar_feature.py`. Decisões: `5-Coleta_features/INVENTARIO.md` (M1–M18); recursos e equivalência com o piloto: `5-Coleta_features/RECURSOS.md`.

## 1. Linha do tempo
- Snapshots: **16** (JunoSR0 → Oxygen; índices globais 1..16); datas do calendário na série: 20; duplicatas removidas: 4; lacunas de presença atravessadas: 0.
- História linear verificada (s00). .java de produção: 1127 → 1165.
- Commits nos intervalos: 425; válidos: 425; importados por merge e excluídos (M6): 0.

## 2. Falhas de parsing do JavaParser (piloto: 0)
- Versões de arquivo únicas: 2083; **falhas: 0**; métodos (sem anônimos/locais): 23467; descartados por chave duplicada no arquivo: 0; textos distintos: 8055.

## 3. ChangeDistiller (piloto: 0 erros)
- Chamadas: 913; **erros (CDERROR): 0**.
- CK: logs com exceção: 0 ; CSVs do Understand: 16 de 16.

## 4. Taxas de match no join (piloto: ~100%)
- Mínimo por release: evo_in_ck = 1.0000, evo_in_und = 1.0000, ck_in_evo = 0.9978, und_in_evo = 1.0000.
- Média: evo_in_ck = 1.0000, evo_in_und = 1.0000. Tabela completa: `data/join_audit.csv`.

## 5. Dataset e positivos por release
- Linhas: **106964**; positivos: **777** (0.73%). A última release não tem rótulo.

| Release (índice) | Tag | Métodos | Positivos | % |
|---|---|---|---|---|
| 1 | JunoSR0 | 7002 | 4 | 0.06 |
| 2 | JunoSR1 | 6980 | 94 | 1.35 |
| 3 | JunoSR2 | 7043 | 53 | 0.75 |
| 4 | KeplerPostRC4 | 7070 | 1 | 0.01 |
| 5 | KeplerSR0 | 7070 | 12 | 0.17 |
| 6 | KeplerSR1 | 6999 | 227 | 3.24 |
| 7 | LunaSR0 | 7150 | 39 | 0.55 |
| 8 | LunaRC4 | 7148 | 24 | 0.34 |
| 9 | LunaSR2 | 7074 | 78 | 1.10 |
| 10 | S201504150911 | 7178 | 48 | 0.67 |
| 11 | Mars.1 | 7141 | 97 | 1.36 |
| 12 | Neon | 7252 | 17 | 0.23 |
| 13 | Neon.1 | 7256 | 32 | 0.44 |
| 14 | Neon.2 | 7298 | 9 | 0.12 |
| 15 | Neon.3 | 7303 | 42 | 0.58 |

## 6. Spot check das métricas evolutivas contra `git log -L`
- Método: `org.eclipse.team.svn.ui.operation.CompareResourcesInternalOperation.fetchStatuses18(ISVNConnector,ArrayList,ArrayList,IProgressMonitor)` (arquivo `org.eclipse.team.svn.ui/src/org/eclipse/team/svn/ui/operation/CompareResourcesInternalOperation.java`, linhas 223,293 em fbd40e2521)
- Comando: `git -C 1-Repositorios/subversive log --no-merges --format=%H --no-patch -L223,293:org.eclipse.team.svn.ui/src/org/eclipse/team/svn/ui/operation/CompareResourcesInternalOperation.java 9466e2902f..fbd40e2521`
- Commits contados pela s05: 11 | listados pelo `git log -L`: 12 | em comum: 11 | contados e não listados: 0
- Resultado: **OK** (todos os commits contados estão no `git log -L`; os demais do git são mudanças em linhas vizinhas ou só de comentário/formatação)

## 7. Quebras de identidade de métodos (M28, ameaça à validade)
- Nascimentos após o 1º snapshot: 579; por mudança de pacote/classe: 5; em código importado (M6, heurística): 0.
- Efeito: histórico zerado (BOM = release da quebra; FRCH/CSB… recomeçam em 0) e método sem rótulo na transição. Detalhe: `data/identidade_metodos.csv`, `data/identidade_pares.csv`, `5-Coleta_features/AMEACA_identidade.md`.

- Nenhuma transição acima do limite (≥ 100 ou ≥ 1% dos métodos).
