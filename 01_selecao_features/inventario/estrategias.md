
## Estratégias para o novo mapeamento e impacto na coleta e no ML

### Como o mapeamento entra no pipeline (o que ele define)
Cada snapshot mapeado define, para cada feature:
1. **Métricas estruturais** (CK, Understand): calculadas no snapshot *r*.
2. **Métricas evolutivas** (TACH, CHO, FRCH, WCH…): calculadas sobre os commits do intervalo (snapshot *r−1*, snapshot *r*].
   Dependem de **história linear** (o intervalo é `rev-list prev..cur`) e são proporcionais à **duração do intervalo**.
3. **Rótulo** (`will_change`): ChangeDistiller entre *r* e *r+1*, com `TOTAL_CHANGES > mediana` (a mediana foi 0 em todas
   as releases do piloto, então na prática o rótulo é "o método muda no próximo intervalo"). A taxa de positivos também
   é proporcional à duração e à atividade do intervalo.
4. **Unidade temporal comum** entre as features: necessária para a validação temporal do modelo agregado (treinar até a
   data T e testar depois de T, para todas as features).

Portanto, o mapeamento determina diretamente: (a) a validade das métricas evolutivas (linearidade); (b) a homogeneidade
dos intervalos (escala das métricas evolutivas e da taxa de positivos); (c) o significado do rótulo; (d) o escopo de
código (que métodos entram); e (e) o alinhamento temporal entre features.

Pré-requisito verificado: todo repositório tem uma linha principal identificável (`origin/HEAD`: `master`/`main`).
A exceção é o **Scout**, que não tem `master`: o desenvolvimento ocorre na branch `releases/<próxima versão>`. Mesmo assim,
o first-parent de `releases/27.1` é contínuo de 2010 a 2026 (13.994 commits).

---

### E1. Proximidade temporal na linha principal (correção da estratégia original)
**Regra:** para cada data do simrel, o último commit **da linha principal, seguindo só o primeiro pai**, anterior à data
(`git rev-list -1 --first-parent --before=<data> <linha principal>`), em vez de `git log --all`.

- **O que corrige:** P1 (branches arbitrários, manutenção, `features/…`), a não linearidade (todos os snapshots
  ficam na mesma cadeia por construção, sem exclusões) e a queda em sub-históricos (P7: o first-parent não entra no
  histórico importado antes do merge).
- **O que não corrige:** o snapshot continua sendo o "estado do desenvolvimento na data", não o código distribuído
  (em releases de manutenção, é o desenvolvimento da versão seguinte); P3–P6 dependem de decisões à parte.
- **Coleta:** contínua, sem lacunas; todos os snapshots são utilizáveis. Duplicatas só onde não houve commit no
  período (projetos parados). Os intervalos são `prev..cur` na mesma cadeia: as métricas evolutivas ficam bem definidas.
  Estende-se trivialmente a features com vários repositórios (a data é a chave comum).
- **ML:** o rótulo passa a significar "o método muda no próximo trimestre de desenvolvimento", uma definição coerente
  e comparável entre features. Usa o mesmo calendário para todas as features, então a validação temporal agregada é
  direta. O risco é a heterogeneidade dos intervalos antes de 2018 (de 4 dias, Oxygen.1→1a, a 7 meses), que muda a
  escala das métricas evolutivas e a taxa de positivos entre releases (ver E1b).
- **Custo:** baixo, automático e reprodutível.

### E1b. Variante: calendário regularizado
Igual à E1, mas com **datas de corte regulares** (ex.: trimestrais, de 2012-09 a 2026-03) ou com as datas do simrel
**filtradas**: remover triplicatas (`z2014…`), respins (`Neon.1a`, `*_respin`), pontos que não são releases
(`OxygenPreRienaRemoval`, `PhotonM7`, `KeplerPostRC4`) e manter as releases reais do trem.
- **ML:** intervalos quase homogêneos (~3 meses). Isso reduz o deslocamento de distribuição nas métricas evolutivas e no
  rótulo entre releases, e evita intervalos minúsculos com rótulo quase todo 0 (ex.: 4 dias).
- **Coleta:** um pouco menos de snapshots (~50–55 em vez de 61), também contínuos.
- **Perda:** com datas trimestrais fixas, a correspondência nominal com as releases do simrel deixa de ser exata.
  Com o filtro de datas, ela se mantém.

### E2. Build efetivamente distribuído (fidelidade ao simrel)
**Regra:** para cada release, o commit da tag do build contribuído (resolvido como em `sim_tags.csv`).
- **Corrige:** P1 por definição; o snapshot é o produto que a LPS distribuiu.
- **Coleta:**
  - **Não linear:** releases de manutenção vêm de branches. O intervalo "SR2 (branch 4.7.x) → próxima major (master)"
    mistura histórias (backports contados duas vezes, commits do branch que não estão no master). Isso afeta TACH,
    FRCH, CHO etc. e exigiria redefinir as métricas evolutivas.
  - **Builds repetidos** (BIRT 4.7.0 em 19 releases, GEF Legacy 2016–2022, PTP, Mylyn): intervalos de mudança zero,
    que precisam ser deduplicados. A série vira **irregular**, com intervalos de dias a anos e menos snapshots
    (ex.: BIRT 12, PTP 17).
  - **267 releases sem tag resolvida automaticamente:** exigem regras por projeto e trabalho manual (Scout,
    WindowBuilder, DataTools, PTP, GMF).
- **ML:** o rótulo significa "o método muda na próxima versão distribuída", semanticamente mais próximo de
  "release" (como em Elish & Al-Khiaty). Porém a duração dos intervalos varia muito, o que distorce as métricas
  evolutivas e a taxa de positivos. Também não há calendário comum entre features, o que dificulta a validação temporal
  agregada. Há mais exemplos com rótulo 0 em períodos de build repetido.
- **Custo:** alto, com trechos manuais.

### E2b. Variante: só releases "feature" da linha principal
Só os builds X.Y.0 (ou equivalentes) que estão na linha principal; descarta SRs e manutenção.
- **Coleta:** linear (as tags X.Y.0 em geral são ancestrais umas das outras no master); poucos snapshots
  (de anual a trimestral, conforme o projeto); intervalos longos e desiguais entre projetos.
- **ML:** rótulo por versão principal; menos amostras temporais; intervalos longos → taxa de positivos maior (bom para
  o desbalanceamento). Mas a heterogeneidade entre projetos é grande (CDT trimestral vs. BIRT/WindowBuilder com
  anos sem versão nova).

### E3. Híbrido recomendado: E1/E1b + simrel como filtro de presença e de escopo
**Regra:** snapshots pela E1 (ou E1b) na linha principal. O simrel é usado para decidir:
- **Presença:** só entram as releases em que a feature está **ativa** no simrel (contribuição presente e habilitada).
  BIRT até 2020-09, EclipseLink até 2014, Subversive até Oxygen.3, PTP até 2025-12, CVS até 2021-12; Mylyn com lacuna
  2022-06 → 2023-03. **Decisão sua:** lacunas internas (Mylyn, desativações pontuais) podem ser tratadas como
  "continuar coletando" (preserva a continuidade) ou "cortar a série" (fidelidade estrita).
- **Escopo:** os repositórios e diretórios que compõem a contribuição. Exemplos: WTP além do `javaee`? JDT só Core?
  Incluir o `gef` (GEF4/5) no GEF? Incluir os exemplos?
- **Validação:** registrar, por release, a distância entre o snapshot E1 e o build distribuído (já calculada em
  `sim_tags.csv`) como ameaça à validade, e opcionalmente rodar a E2 em 1–2 features como análise de sensibilidade.
- **Coleta:** continuidade da E1 dentro do período de presença; menos snapshots onde a feature saiu do simrel.
- **ML:** mantém as vantagens da E1 (linearidade, calendário comum, rótulo coerente) e restringe os dados ao período
  em que o código pertence à LPS. Isso evita treinar com métodos de código que não estava na LPS (ex.: BIRT 2021–2026).

---

### Impacto comparado

| Critério | E1 | E1b | E2 | E2b | E3 (E1/E1b + filtros) |
|---|---|---|---|---|---|
| Continuidade (sem lacunas) | sim | sim | não (dedup., branches) | parcial (poucos pontos) | sim, no período de presença |
| Linearidade (métricas evolutivas válidas) | sim | sim | não | sim (em geral) | sim |
| Intervalos homogêneos | parcial (irregular antes de 2018) | sim | não | não | conforme E1/E1b |
| Rótulo = "próxima versão distribuída" | não (próximo trimestre) | não | sim | sim (major) | não (documentado como ameaça) |
| Calendário comum entre features (validação temporal) | sim | sim | não | não | sim |
| Código pertence à LPS na data | não garantido | não garantido | sim | sim | sim (pelo filtro) |
| Suporte a features multi-repo | fácil | fácil | difícil | difícil | fácil |
| Custo / reprodutibilidade | baixo / alta | baixo / alta | alto / média | médio / alta | baixo–médio / alta |

### Pontos que valem para qualquer estratégia
- **Históricos importados** (P7): decidir o tratamento dos commits importados no intervalo do merge (recomendado:
  excluí-los dos intervalos; o código importado "nasce" naquela release).
- **Subversive:** o repositório correto não está clonado; o `subclipse` não representa a feature. Excluir a feature
  ou buscar o repositório do Subversive.
- **EclipseLink:** com o filtro de presença, só 9 releases (2012–2014). Avaliar se compensa mantê-la.
- **EGit (piloto):** para manter a consistência, o EGit deve ser recoletado com a estratégia escolhida (com E1, os
  problemas de Mars.1 e Oxygen.2_respin desaparecem por construção).
- **Censura à esquerda** (BOM=1 no primeiro snapshot) e o rótulo da última release não mudam com a estratégia.
