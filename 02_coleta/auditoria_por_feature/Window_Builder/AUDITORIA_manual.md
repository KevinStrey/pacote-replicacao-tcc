# Window Builder: verificações manuais

## Falhas de parsing (16 versões, 8 arquivos em snapshots)
Arquivos de 2024–2026 com `sealed`/`permits` (ex.: `org.eclipse.wb.swt.widgets.baseline/…/IBaseline.java`:
`public sealed interface IBaseline permits Baseline`) e o diretório `src_java24`. O JavaParser 3.25.0 do
JMethodsExtractor original não reconhece essa sintaxe em nenhum nível (testado: JAVA_17, JAVA_17_PREVIEW, JAVA_8).
Limitação documentada (M23): os métodos desses arquivos ficam fora do dataset nas releases afetadas.
