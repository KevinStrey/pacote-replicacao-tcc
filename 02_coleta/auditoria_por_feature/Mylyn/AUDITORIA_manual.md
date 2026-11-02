# Mylyn: verificações manuais (complemento do AUDITORIA.md gerado automaticamente)

## Spot check (seção 6 do AUDITORIA.md): 7 de 9 commits em comum com o `git log -L`
Método: `org.eclipse.mylyn.internal.gitlab.ui.GitlabRepositorySettingsPage.createAdditionalControls(Composite)`.
Os 2 commits contados pela s05 e não listados pelo `git log -L` foram verificados à mão:

```bash
git -C 1-Repositorios/org.eclipse.mylyn show d0a2f4d4f0 -- "*GitlabRepositorySettingsPage.java"
git -C 1-Repositorios/org.eclipse.mylyn show f3d06000be -- "*GitlabRepositorySettingsPage.java"
```

- `d0a2f4d4f0` (2023-07-28, "update the gitlab icons…"): adiciona ao corpo de `createAdditionalControls` a criação
  e a configuração de `showCommentIconsButton` (`new Button(aditionalContainer, SWT.CHECK)`, `setText`,
  `setSelection`, `GridData`): **mudança real no método**.
- `f3d06000be` (2023-10-03, "some UI cleanup / improvements"): renomeia `showCommentIconsButton` para
  `showActivityIconsButton` e altera textos (`"Show Avantar images"` → `"Show Avantars"`) dentro do método:
  **mudança real no método**.

Conclusão: a contagem da s05 está correta. O `git log -L` (heurística de faixa de linhas) não listou esses commits.
Ambos estão em ramos laterais mesclados na linha principal, e o `-L` não segue bem esse tipo de história.

## Falha de parsing (seção 2): 1 arquivo
`mylyn.docs/wikitext/core/org.eclipse.mylyn.wikitext/src/main/java/org/eclipse/mylyn/wikitext/parser/builder/HtmlEntities.java`
(blob `762f0c256f`, snapshots da release 46 em diante). O arquivo usa o escape `"\s"` (Java 15+, linha 47:
`line.split("\s")`), que o lexer do JavaParser 3.25.0 (versão do JMethodsExtractor original) não aceita em nenhum
nível de linguagem (testado: JAVA_17, JAVA_17_PREVIEW, JAVA_8). Efeito: os métodos desse arquivo não entram no
evometrics e, portanto, ficam fora do dataset (join interno) nessas releases. Mantido como limitação, para não trocar
a versão do parser da ferramenta original.
