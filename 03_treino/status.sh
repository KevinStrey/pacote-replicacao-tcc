#!/usr/bin/env bash
# Mostra o andamento: etapa atual, progresso das fases, erros e uso da máquina.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR" || exit 1
if [ -f saida/.lock/pid ] && kill -0 "$(cat saida/.lock/pid)" 2>/dev/null; then
  echo "EM EXECUÇÃO (PID $(cat saida/.lock/pid))"
else
  echo "PARADO (nenhuma execução ativa)"
fi
cat saida/ESTADO.txt 2>/dev/null
echo
for f in saida/teste_rapido/status/fase*.json saida/status/fase*.json; do
  [ -f "$f" ] || continue
  if [ -x ambiente/bin/python ]; then
    ambiente/bin/python - "$f" <<'EOF'
import json, sys
s = json.load(open(sys.argv[1], encoding='utf-8'))
feitos = s['ja_concluidos_antes'] + s['concluidos_agora']
print(f"{s['execucao']:13s} {s['fase']}: {feitos}/{s['total']} concluídos, {len(s['em_execucao'])} rodando, "
      f"{s['pendentes']} na fila, {len(s['falhas'])} falhas | RAM livre {s['ram_livre_gb']} GB | {s['atualizado']}")
for r in s['em_execucao']:
    print(f"    {r['id']}  {r['minutos']} min  {r['ram_gb']} GB")
EOF
  else
    echo "$f:"; head -c 600 "$f"; echo
  fi
done
echo
echo "arquivos de erro: $(ls saida/erros 2>/dev/null | wc -l) (saida/erros/)"
echo "--- últimas linhas de saida/logs/executar_tudo.log ---"
tail -n 12 saida/logs/executar_tudo.log 2>/dev/null
echo "---"
uptime
free -g | head -2
