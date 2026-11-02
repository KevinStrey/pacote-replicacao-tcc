#!/usr/bin/env bash
# Interrompe a execução de forma ordenada (jobs concluídos ficam salvos; os em andamento serão refeitos).
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR" || exit 1
if [ -f saida/.lock/pid ] && kill -0 "$(cat saida/.lock/pid)" 2>/dev/null; then
  kill -TERM "$(cat saida/.lock/pid)"
  echo "Sinal de parada enviado ao PID $(cat saida/.lock/pid). Acompanhe com: bash status.sh"
else
  echo "Nenhuma execução ativa."
fi
