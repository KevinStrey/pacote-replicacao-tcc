#!/usr/bin/env bash
# Inicia executar_tudo.sh em segundo plano, desligado do terminal (continua após o logout). Aceita as mesmas opções.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR" || exit 1
mkdir -p saida/logs
if [ -f saida/.lock/pid ] && kill -0 "$(cat saida/.lock/pid)" 2>/dev/null; then
  echo "Já existe uma execução ativa (PID $(cat saida/.lock/pid)). Acompanhe com: bash status.sh"
  exit 1
fi
setsid nohup bash executar_tudo.sh "$@" >> saida/logs/console.log 2>&1 < /dev/null &
sleep 3
echo "Treino iniciado em segundo plano."
echo "  acompanhar:  bash status.sh      (ou: tail -f saida/logs/executar_tudo.log)"
echo "  parar:       bash parar.sh       (o progresso fica salvo; bash iniciar.sh retoma)"
echo "Pode encerrar a sessão; o processo continua. Ao final, entregue saida/resultados_e_logs.zip."
