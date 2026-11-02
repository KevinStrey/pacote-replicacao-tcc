# Scout: verificações manuais (complemento do AUDITORIA.md gerado automaticamente)

## Spot check: 76 de 81 commits em comum com o `git log -L`
Método `org.eclipse.scout.rt.client.ui.basic.table.AbstractTable.initConfig()`. Os 5 commits não listados
(`0b1840e9de`, `fa2ea89aa8`, `dcfd1ed59e` de 2014; `48f2022d11`, `2685a03979` de 2016) alteram o arquivo
`AbstractTable.java` nas regiões do método (hunks `@@ -800`, `@@ -873` etc., verificados com `git show <commit>`).
- O arquivo foi **renomeado** em 2015-02-20 (`01cec757f8`, R100: `src/…` → `src/main/java/…`;
  `git log --follow --diff-filter=R -- <arquivo>`). O `git log -L` sobre o caminho final não acompanha o histórico
  anterior à renomeação (commits de 2014).
- Os 2 commits de 2016 estão num ramo lateral mesclado, que o `-L` também não segue (mesmo caso do Mylyn).
Conclusão: a contagem da s05 está correta.

## Falhas de parsing
~290 das ~300 são templates de arquétipo Maven (Velocity, `#set …`) em
`scout-*-app/src/main/resources/archetype-resources/…`: não são código de produto (M22) e não entram no dataset.
Os 2–3 arquivos com `_` como identificador foram resolvidos com a 2ª tentativa em JAVA_8 (M21; s04–s07 refeitas em
2026-10-14).
