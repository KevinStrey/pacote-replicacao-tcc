# BIRT: verificações manuais (complemento do AUDITORIA.md gerado automaticamente)

## Spot check: commits contados que o `git log -L` não lista
Antes da M26, o método escolhido tinha 31 commits contados e 12 em comum com o `git log -L`. A investigação mostrou:
1. **Commits equivalentes contados em dobro** (cherry-pick/rebase): 9 pares com a mesma mensagem e o mesmo tamanho (ex.:
   `d7d24b8188`, 2013, e `1dd720e09b`, 2014-07-22, "Query Pushdown is not applied if join cannot be pushdown"), além de
   "Merge master to 1666 branch" (`939de889b8`, um só pai). Corrigido pela **M26** (`data/commit_duplicates.csv`).
2. **Branches mesclados tarde** (M27): o desenvolvimento do BIRT ocorria em ramos laterais. No método
   `TextWriter.startBlockText(...)` (escolhido após a M26), os commits do branch PPTX de 2014 entram no intervalo 11
   (mesclagem em 2015), e os "Refactor…" de 2015-01 que reimplementam o mesmo trabalho entram no intervalo 9. Todos
   alteram de fato o método (`git show <commit> -- <arquivo>`). O `git log -L` não segue esses ramos laterais.
Conclusão: a contagem segue a definição do cpmp (todo commit sem merge do intervalo); o viés por mesclagem tardia
(39,7% das mudanças do BIRT) está documentado como ameaça à validade (M27).

## Falha de parsing (1)
Marcador de conflito de merge (`<<<<<<<`) commitado num commit intermediário e corrigido depois; não está em snapshots.
