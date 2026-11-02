# Previsão da propensão a mudança de *features* em uma LPS real (Eclipse IDE): pacote de replicação

Material de apoio do Trabalho de Conclusão de Curso *Predição de mudanças em sistemas com arquitetura de Linha de Produto de Software*, de Kevin Grünfeld Strey, orientado pelo Prof. Dr. Paulo Roberto Farah (UDESC, 2026). Contém o código, as
decisões de coleta, os registros de auditoria e os resultados necessários para auditar e reproduzir o trabalho. Os
dados pesados (conjunto de dados final, dados intermediários e previsões dos modelos) estão no Zenodo:
[10.5281/zenodo.23890698](https://doi.org/10.5281/zenodo.23890698).

Todos os arquivos estão listados com seu hash em `SHA256SUMS.txt`. Para conferir a integridade:
`sha256sum -c SHA256SUMS.txt` (Linux) ou `Get-FileHash` (Windows).

## Visão geral do processo

```
simrel.build (tags)  ──►  01 seleção das features e linha do tempo  ──►  02 coleta (snapshots, CK, Understand,
                                                                           métricas evolutivas, ChangeDistiller,
                                                                           junção, auditoria)
                                                                                    │
                    06 texto  ◄──  05 análises e figuras  ◄──  04 resultados  ◄──  03 treino (servidor)
```

## Estrutura

| Pasta | O que contém | Seção do TCC |
|---|---|---|
| `01_selecao_features/` | Mapeamento das *features* do *Eclipse Simultaneous Release* em cada release (`mapeamento/output/mapeamento.csv`, regras em `mapeamento/features.py`), auditoria do *simrel* e inventário exploratório dos repositórios | 3.1 Objeto de estudo; 3.2 Linha do tempo; 3.3 Escopo |
| `02_coleta/scripts/` | *Pipeline* de coleta `s00`–`s07` (linha do tempo, *snapshots*, CK, Understand, métodos, métricas evolutivas, ChangeDistiller, junção), auditoria por *feature*, medições das ameaças e contagem das falhas do JavaParser | 3.4 Métricas; 3.5 Variável alvo |
| `02_coleta/decisoes/` | `INVENTARIO.md` (decisões M1–M28, com data e justificativa), `RECURSOS.md` (desempenho e equivalência com o piloto), `AMEACA_identidade.md` (quebras de identidade de métodos) | 3.4–3.6; Ameaças à validade |
| `02_coleta/auditoria_por_feature/<feature>/` | `AUDITORIA.md` (linha do tempo, falhas de *parsing*, ChangeDistiller, taxas de junção, positivos por release), verificação manual, `timeline.csv`, `join_audit.csv`, duplicatas de commits, identidade de métodos e *logs* de cada etapa | 3.6 Validação da coleta |
| `02_coleta/piloto_egit/` | Coleta piloto no EGit com a cadeia original do cpmp e a verificação de que o *pipeline* otimizado reproduz o piloto | 3.6 |
| `02_coleta/falhas_parsing/` | Arquivos que o JavaParser 3.25.0 não analisou, causa e métodos retirados | Apêndice A |
| `03_treino/` | Pacote executado no servidor: preparação dos dados, treino, métricas, nível de *feature*, ambiente com versões travadas (`conda-linux-64.lock`) e configuração da grade (`config/experimentos.yaml`) | 3.7–3.11 |
| `04_resultados/saida/` | Saídas do servidor: métricas de teste (`resultados_teste.csv`), validação cruzada, intervalos por *bootstrap*, desempenho por *feature*, nível de *feature*, sensibilidade, importâncias, um JSON por treinamento (`jobs/`) e *logs* | Capítulo 4 |
| `05_analises_e_figuras/` | Scripts locais que geram as figuras e as tabelas do TCC a partir de `04_resultados` e das previsões | Capítulo 4 |
| `06_texto/` | PDF do TCC (incluído após a defesa) | — |

## Dados no Zenodo

| Arquivo | Conteúdo |
|---|---|
| `dataset_final.zip` | Conjunto de dados de treino: um Parquet por *feature* (18.059.107 linhas método × release, 98 métricas e o rótulo) e `meta_treino.json` (linhas, positivos e SHA-256 de cada arquivo, versões das bibliotecas e calendário) |
| `dados_intermediarios_coleta.zip` | Por *feature*: métricas evolutivas, saída do ChangeDistiller e mudanças por método e commit |
| `predicoes_modelos.zip` | Probabilidades previstas por método para cada configuração e protocolo (`.npz`) e os índices de treino e teste (`prep/`), com os quais todas as métricas do TCC podem ser recalculadas |

## Como auditar

- **Uma decisão de coleta**: procurar o código Mx em `02_coleta/decisoes/INVENTARIO.md` e o script citado em
  `02_coleta/scripts/`.
- **Um número da coleta** (linhas, positivos, *snapshots*, falhas): `02_coleta/auditoria_por_feature/<feature>/AUDITORIA.md`.
- **Um número dos resultados**: `04_resultados/saida/resultados/` (tabelas agregadas) ou o JSON do treinamento em
  `04_resultados/saida/resultados/jobs/`; os intervalos de confiança estão em `bootstrap/`.
- **Uma figura ou tabela do capítulo 4**: o script correspondente em `05_analises_e_figuras/scripts/`.
- **Recalcular as métricas**: carregar as previsões de `predicoes_modelos.zip` e os rótulos de `prep/`.

## Como reproduzir

1. **Repositórios**: clonar os repositórios abaixo em `1-Repositorios/` (nenhum foi alterado; só a leitura do
   histórico Git é usada).
2. **Coleta**: Python com `02_coleta/scripts/requirements.txt`, Java 21, CK 0.7.1 (distribuído com o cpmp) e
   Understand (SciTools, *build* 1263, licença necessária). Executar `run_all.py` (ver `RECURSOS.md`).
3. **Treino**: seguir `03_treino/LEIA-ME.md` (ambiente instalado pelo próprio pacote, com versões travadas). Na
   execução do TCC, a grade completa levou ≈ 3,8 dias em paralelo, com pico de ≈ 91 GB de RAM.
4. **Análises**: scripts de `05_analises_e_figuras/scripts/` sobre `04_resultados` e as previsões.

Não estão incluídos: os *snapshots* extraídos (reconstruídos pela etapa `s01` a partir dos repositórios) e as saídas
brutas do CK, do Understand e do JavaParser por *snapshot* (≈ 28 GB, reconstruídas pelas etapas `s02`–`s04`).

### Repositórios analisados

| *Feature* | Repositório |
|---|---|
| (calendário) | <https://github.com/eclipse-simrel/simrel.build> |
| BIRT | <https://github.com/eclipse-birt/birt> |
| CDT | <https://github.com/eclipse-cdt/cdt> |
| CVS | <https://github.com/JAndrassy/org.eclipse.team.cvs> |
| DataTools | <https://github.com/eclipse-datatools/datatools> |
| EGit | <https://github.com/eclipse-egit/egit> |
| EMF | <https://github.com/eclipse-emf/org.eclipse.emf> |
| EclipseLink | <https://github.com/eclipse-ee4j/eclipselink> |
| GEF | <https://github.com/eclipse-gef/gef-classic> |
| GMF Runtime | <https://github.com/eclipse-gmf-runtime/gmf-runtime> |
| JDT | <https://github.com/eclipse-jdt/eclipse.jdt.core> |
| Mylyn | <https://github.com/eclipse-mylyn/org.eclipse.mylyn> |
| PDE | <https://github.com/eclipse-pde/eclipse.pde> |
| PTP | <https://github.com/eclipse-ptp/ptp> |
| RAP | <https://github.com/eclipse-rap/org.eclipse.rap> |
| Scout | <https://github.com/eclipse-scout/scout.rt> |
| Subversive | <https://gitlab.eclipse.org/eclipse/subversive/subversive> |
| WebTools | <https://github.com/eclipse-jeetools/webtools.javaee> |
| Window Builder | <https://github.com/eclipse-windowbuilder/windowbuilder> |
| m2e | <https://github.com/eclipse-m2e/m2e-core> |

## Observação sobre os resultados

Os arquivos `resultados_teste.csv` e `por_feature.csv` foram regenerados localmente a partir dos JSON de `jobs/`
(fonte primária, um por treinamento), com a mesma lógica de `03_treino/scripts/collect_results.py`, porque as cópias
originais foram abertas e salvas no Excel, que alterou o separador e alguns valores numéricos. O procedimento está em
`05_analises_e_figuras/scripts/regerar_csv_resultados.py`; os valores conferem com os JSON e com a cópia anterior ao
Excel (diferença máxima de 1e-13).

## Base e licenças

A cadeia de ferramentas parte do projeto cpmp (<https://github.com/paulorfarah/cpmp>), de Paulo Roberto Farah; as
correções feitas neste trabalho estão descritas em `02_coleta/decisoes/INVENTARIO.md` e no capítulo 3 do TCC.
Licenças: código sob MIT e dados e documentação sob CC BY 4.0.

## Como citar

STREY, Kevin Grünfeld. **Pacote de replicação: Predição de mudanças em sistemas com arquitetura de Linha de Produto de
Software**. Zenodo, 2026. Disponível em: <https://doi.org/10.5281/zenodo.23890698>.
