# PDE: verificações manuais (complemento do AUDITORIA.md gerado automaticamente)

## Spot check: 23 de 24 commits em comum com o `git log -L`
Método `org.eclipse.pde.launching.JUnitLaunchConfigurationDelegate.collectExecutionArguments(…)`. O commit não
listado, `25a41843de` (2015-08-08, "Bug 474221 - Remove Non-Javadoc statemens"), remove blocos
`/* (non-Javadoc) … */` presos aos métodos (`git show 25a41843de -- <arquivo>`). O texto do método inclui comentários
e Javadoc (mesma definição do piloto), então a mudança é contada. O `git log -L` não a vê porque o bloco não existe no
commit final. Conclusão: a contagem está correta.

## Falhas de parsing (34)
São todas templates do assistente de plug-ins (`ui/org.eclipse.pde.ui.templates/templates_*/…`, com variáveis
`%…%`/`$…$`), que não são código de produto. Os templates que são parseáveis (~10 mil linhas no evometrics) são
excluídos do dataset final pela regra M22.
