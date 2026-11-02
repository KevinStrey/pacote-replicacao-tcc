# JDT: verificações manuais (complemento do AUDITORIA.md gerado automaticamente)

## CK 0.7.1 trava nos snapshots 45–54 (2024–2026), M24
`NullPointerException` no JDT embutido no CK (`Scope.getMethod`, ao resolver uma *switch expression*). Por
*delta debugging* (`scripts/ddmin_ck.py`, 80 execuções), o conjunto mínimo é
`compiler/codegen/CodeStream.java` + `compiler/codegen/OperandStack.java`; cada um sozinho passa. `OperandStack.java`
foi criado em 2024-05-07 (`565cabe5b1`), justamente no 1º snapshot com falha (45), e não existe antes.
Decisão do autor: excluir `OperandStack.java` **só da entrada do CK** (`features.py`, `ck_exclude`; arquivos
`data/ck/<tag>.excluded.txt`). Os métodos dele ficam fora do dataset (join interno), e as métricas do CK que dependem
de ligações entre classes não contam esse arquivo. Understand e evometrics não foram alterados.

## Spot check: 86 de 88 commits em comum com o `git log -L`
Método `Parser.consumeRule(int)`. Os 2 commits não listados (`30c7385ebc` de 2020-04-17 e `ea65681e2c` de
2021-04-27) são anteriores à mudança de caminho de `Parser.java` para o bundle `org.eclipse.jdt.core.compiler.batch`
(`c4e7594a65`, 2022-12-07; `git log --follow --diff-filter=R -- <arquivo>`). O `git log -L` sobre o caminho final não
segue renomeações. Conclusão: a contagem está correta.

## Falhas de parsing (40; 11 em snapshots)
`sealed` (ex.: `abstract static sealed class SwitchTranslator` em `compiler/ast/SwitchStatement.java`), não reconhecido
pelo JavaParser 3.25.0: limitação M23. As demais (29) são versões intermediárias dentro de commits.

## Fixtures excluídas do dataset
`JCL/` (M18) e `modules/` (2 arquivos, fixture do APT, Bug 517841; M25, aplicado no join).
