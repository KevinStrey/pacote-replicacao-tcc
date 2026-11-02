# CDT: verificações manuais (complemento do AUDITORIA.md gerado automaticamente)

## Linha principal (M17)
Merge com pais invertidos `7c8bb9f0` (2022-01-11, "Merge o.e.remote into CDT"): a linha principal segue o 2º pai. A
cadeia termina na raiz do CDT (`db3c6a4470`, 2002). 8.228 commits do `org.eclipse.remote` e de outros históricos
importados foram excluídos dos intervalos (M6).

## Spot check: 32 de 33 commits em comum com o `git log -L`
Método `org.eclipse.cdt.cmake.core.internal.CMakeBuildConfiguration.build(...)`. Ele foi removido ou renomeado antes do
último snapshot. A auditoria passou a usar o último snapshot em que o método existe (correção em
`auditar_feature.py`, 2026-10-14). O commit não listado, `12904409a3` (2016-04-25, "Bug 492304 - Fix NLS warnings"),
acrescenta comentários `//$NON-NLS` no método (o texto inclui comentários, definição do piloto) e é anterior à
renomeação do arquivo (`af1b6fa238`, 2020-10-13), que o `git log -L` não segue. Conclusão: a contagem está correta.

## Falhas de parsing
4 versões em snapshots usam `_` como nome de parâmetro e de `catch` (Java ≤ 8). A s04 do CDT tinha rodado antes da
2ª tentativa em JAVA_8 (M21); s04–s07 foram refeitas em 2026-10-14 (`logs/rerun_CDT_M21.log`).
