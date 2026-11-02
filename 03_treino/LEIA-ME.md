# Treino no servidor: instruções

Pacote: `treino_tcc.zip` (dados + scripts + ambiente com versões travadas). Plano e decisões: `PLANO_TREINO.md`.

## 1. Antes de começar (no servidor)
```bash
df -h ~              # é preciso ter pelo menos 50 GB livres (recomendado: 70 GB)
which unzip tmux     # só informativo
```

## 2. Descompactar
```bash
cd ~                                   # ou outra pasta com espaço
unzip treino_tcc.zip                   # sem unzip: python2 -m zipfile -e treino_tcc.zip .
cd treino_tcc
chmod +x *.sh ferramentas/micromamba   # por garantia
```

## 3. Iniciar (um único comando)
```bash
bash iniciar.sh
```
Roda em segundo plano e **continua após o logout**. Ele faz, nesta ordem:
1. registra o sistema (`saida/logs/sistema.txt`) e confere o espaço em disco;
2. instala o ambiente Python em `treino_tcc/ambiente` (micromamba, sem sudo, versões travadas em
   `conda-linux-64.lock`; precisa de internet, ~2 GB);
3. testa o ambiente (mini-treino de todos os algoritmos);
4. confere a integridade dos dados (SHA-256);
5. prepara a matriz de treino (~14 GB em `trabalho/`);
6. **teste rápido** com amostra de 1% e a grade inteira; se algo falhar, **para aqui** e gera o zip de logs;
7. fase 1 (sem MLP) → fase 2 (MLP, temporal) → fase 3 (sensibilidade). Depois de cada fase, atualiza
   `saida/resultados_e_logs.zip`.

## 4. Acompanhar e interromper
```bash
bash status.sh                              # etapa atual, progresso, jobs rodando, erros, RAM
tail -f saida/logs/executar_tudo.log        # log completo (Ctrl+C só sai do tail)
bash parar.sh                               # parada ordenada; o que terminou fica salvo
bash iniciar.sh                             # retoma do ponto em que parou
```
Opções: `--so-teste` (para após o teste rápido), `--ate fase1` (para após a fase 1) e `--pular-teste`,
por exemplo `bash iniciar.sh --so-teste`.

## 5. O que me entregar
**`saida/resultados_e_logs.zip`** (gerado ao final e após cada fase, inclusive se houver erro). Contém:
- `saida/logs/`: log geral, sistema, ambiente, verificação dos dados, preparação, treino por fase e log de cada job;
- `saida/erros/`: um arquivo por job que falhou (motivo, código de saída e fim do log) e erros do script geral;
- `saida/resultados/`: tabelas (`resultados_teste.csv`, `por_feature.csv`, `bootstrap_ic.csv`,
  `sensibilidade.csv`, `nivel_feature_*.csv`...), `RELATORIO.md` e o resultado de cada job (`jobs/*.json`);
- `saida/teste_rapido/`: o mesmo para o teste com amostra.

Se o zip de resultados não existir (falha antes da instalação do Python), entregue a pasta `saida/` compactada com
`tar czf saida.tar.gz saida`.

## 6. Problemas comuns
- **Sem internet / falha na instalação do ambiente:** o erro fica em `saida/logs/executar_tudo.log`; rode
  `bash iniciar.sh` de novo (a instalação é refeita até 3 vezes).
- **Servidor reiniciado ou processo morto:** `bash iniciar.sh` retoma; jobs concluídos não são refeitos.
- **Outro usuário usando a máquina:** reduza `threads` ou aumente `reserva_nucleos`/`reserva_ram_gb` em
  `config/experimentos.yaml` antes de retomar.
