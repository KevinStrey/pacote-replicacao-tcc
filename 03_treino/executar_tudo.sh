#!/usr/bin/env bash
# Executa todas as etapas do treino (PLANO_TREINO.md, seção 6.1). Retomável: se for interrompido, rode de novo e ele
# continua do ponto em que parou (jobs concluídos ficam salvos).
#
#   bash iniciar.sh                      recomendado: roda em segundo plano e sobrevive ao logout
#   bash executar_tudo.sh [opções]       em primeiro plano
#     --pular-teste                      não roda o teste rápido (amostra de 1%)
#     --ate fase1|fase2|fase3            para depois da fase indicada (padrão: fase3)
#     --so-teste                         para depois do teste rápido
#
# Etapas: sistema -> micromamba -> ambiente -> check_env -> verify_data -> prepare_data -> teste rápido ->
#         fase1 (sem MLP) -> fase2 (MLP, temporal) -> fase3 (sensibilidade). Após cada fase: tabelas, relatório e
#         saida/resultados_e_logs.zip (o arquivo a ser entregue para análise).
set -u -o pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
SAIDA="$DIR/saida"
LOGS="$SAIDA/logs"
ETAPAS="$SAIDA/etapas"
mkdir -p "$LOGS" "$SAIDA/erros" "$ETAPAS"
exec > >(tee -a "$LOGS/executar_tudo.log") 2>&1

PULAR_TESTE=0
SO_TESTE=0
ATE=fase3
while [ $# -gt 0 ]; do
  case "$1" in
    --pular-teste) PULAR_TESTE=1 ;;
    --so-teste) SO_TESTE=1 ;;
    --ate) ATE="${2:-fase3}"; shift ;;
    *) echo "opção desconhecida: $1"; exit 2 ;;
  esac
  shift
done

msg() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
erro() { msg "ERRO: $*"; echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$SAIDA/erros/executar_tudo.log"; }
estado() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" > "$SAIDA/ESTADO.txt"; msg "== $* =="; }

# ---- uma execução por vez ----
LOCK="$SAIDA/.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  if [ -f "$LOCK/pid" ] && kill -0 "$(cat "$LOCK/pid")" 2>/dev/null; then
    msg "já existe uma execução ativa (PID $(cat "$LOCK/pid")). Saindo."
    exit 1
  fi
  msg "trava de uma execução anterior interrompida encontrada; continuando"
fi
echo $$ > "$LOCK/pid"

export PYTHONNOUSERSITE=1 PYTHONHASHSEED=0 PYTHONUNBUFFERED=1
export MAMBA_ROOT_PREFIX="$DIR/.mamba"
PY="${TCC_PYTHON:-$DIR/ambiente/bin/python}"
MM="$DIR/ferramentas/micromamba"
MM_URL="https://github.com/mamba-org/micromamba-releases/releases/download/2.9.0-0/micromamba-linux-64"
CHILD=""

empacotar() {
  if [ -x "$PY" ] && "$PY" scripts/empacotar_saida.py; then return 0; fi
  msg "empacotamento com Python falhou; usando tar"
  tar czf "$DIR/.saida.tar.gz" -C "$DIR" --exclude='saida/.lock' --exclude='saida/*.zip' saida \
    && mv "$DIR/.saida.tar.gz" "$SAIDA/resultados_e_logs.tar.gz" && msg "gerado $SAIDA/resultados_e_logs.tar.gz"
}
finalizar() {
  local rc=$?
  trap - EXIT
  msg "finalizando (código $rc); empacotando a saída"
  empacotar
  rm -rf "$LOCK"
  estado "terminado (código $rc). Entregar: saida/resultados_e_logs.zip"
}
trap finalizar EXIT
trap 'msg "sinal recebido; interrompendo (o progresso fica salvo)"; [ -n "$CHILD" ] && kill -TERM "$CHILD" 2>/dev/null; [ -n "$CHILD" ] && wait "$CHILD" 2>/dev/null; exit 130' TERM INT
trap '' HUP

# rodar <nome> <comando...>: executa em segundo plano + wait (para os sinais serem repassados), registra tempo e código
rodar() {
  local nome="$1"; shift
  msg ">>> $nome: $*"
  local t0; t0=$(date +%s)
  "$@" &
  CHILD=$!
  wait "$CHILD"
  local rc=$?
  CHILD=""
  msg "<<< $nome: código $rc em $(( $(date +%s) - t0 )) s"
  [ "$rc" -ne 0 ] && erro "$nome terminou com código $rc (detalhes em saida/logs e saida/erros)"
  return "$rc"
}

# ---- 1. sistema ----
estado "1/9 sistema"
{
  echo "data: $(date)"; echo "host: $(hostname)"; echo "usuário: $(id)"; uname -a
  cat /etc/os-release 2>/dev/null | head -4; ldd --version 2>/dev/null | head -1
  echo "núcleos: $(nproc)"; free -g; df -h "$DIR"; ulimit -a; uptime
  command -v tmux screen curl wget unzip 2>/dev/null
} > "$LOGS/sistema.txt" 2>&1
cat "$LOGS/sistema.txt"
LIVRE_GB=$(df -Pk "$DIR" | awk 'NR==2 {print int($4/1048576)}')
msg "disco livre: ${LIVRE_GB} GB"
DISCO_MIN_GB="${TCC_DISCO_MIN_GB:-50}"
if [ "${LIVRE_GB:-0}" -lt "$DISCO_MIN_GB" ]; then
  erro "pouco espaço em disco (${LIVRE_GB} GB; mínimo ${DISCO_MIN_GB} GB: matriz ~14 GB, ambiente ~2 GB, predições ~10 GB)"
  exit 1
fi
baixar() {  # baixar <url> <destino>
  if command -v curl >/dev/null; then curl -fsSL --retry 5 --retry-delay 10 -o "$2" "$1"
  elif command -v wget >/dev/null; then wget -q --tries=5 -O "$2" "$1"
  else return 127; fi
}

if [ -z "${TCC_PYTHON:-}" ]; then
  # ---- 2. micromamba ----
  estado "2/9 micromamba"
  if [ ! -x "$MM" ] || ! "$MM" --version >/dev/null 2>&1; then
    mkdir -p "$DIR/ferramentas"
    baixar "$MM_URL" "$MM.tmp" && mv "$MM.tmp" "$MM" && chmod +x "$MM" || { erro "não foi possível obter o micromamba"; exit 1; }
  fi
  msg "micromamba $("$MM" --version)"

  # ---- 3. ambiente (versões travadas em conda-linux-64.lock) ----
  estado "3/9 ambiente"
  LOCK_HASH=$(sha256sum conda-linux-64.lock | cut -d' ' -f1)
  if [ -x "$PY" ] && [ "$(cat "$ETAPAS/ambiente.ok" 2>/dev/null)" = "$LOCK_HASH" ]; then
    msg "ambiente já instalado"
  else
    ok=0
    for tentativa in 1 2 3; do
      rm -rf "$DIR/ambiente"
      if rodar "ambiente (tentativa $tentativa)" "$MM" create -y -p "$DIR/ambiente" --file conda-linux-64.lock; then ok=1; break; fi
      sleep 60
    done
    [ "$ok" -eq 1 ] || { erro "instalação do ambiente falhou 3 vezes"; exit 1; }
    echo "$LOCK_HASH" > "$ETAPAS/ambiente.ok"
  fi
  "$MM" list -p "$DIR/ambiente" > "$LOGS/ambiente_pacotes.txt" 2>&1
else
  msg "usando TCC_PYTHON=$TCC_PYTHON (instalação do ambiente pulada)"
fi

# ---- 4. ambiente funcional ----
estado "4/9 check_env"
rodar check_env "$PY" scripts/check_env.py || exit 1

# ---- 5. integridade dos dados ----
estado "5/9 verify_data"
rodar verify_data "$PY" scripts/verify_data.py || exit 1

# ---- 6. matriz de treino ----
estado "6/9 prepare_data"
rodar prepare_data "$PY" scripts/prepare_data.py || exit 1

# ---- 7. teste rápido (amostra estratificada; mesmo código, grade inteira) ----
if [ "$PULAR_TESTE" -eq 0 ] && [ ! -f "$ETAPAS/teste_rapido.ok" ]; then
  estado "7/9 teste rápido"
  FRACAO=$(cd scripts && "$PY" -c "from common import load_config; print(load_config()['teste_rapido']['fracao'])")
  falhou=0
  rodar "teste: prepare" "$PY" scripts/prepare_data.py --amostra "$FRACAO" || exit 1
  for fase in fase1 fase2 fase3; do
    rodar "teste: $fase" "$PY" scripts/train.py --execucao teste_rapido --fase "$fase" || falhou=1
  done
  rodar "teste: resultados" "$PY" scripts/collect_results.py --execucao teste_rapido || falhou=1
  if [ "$falhou" -ne 0 ]; then
    erro "o teste rápido teve falhas; o treino completo NÃO foi iniciado. Entregue saida/resultados_e_logs.zip."
    exit 1
  fi
  touch "$ETAPAS/teste_rapido.ok"
  empacotar
fi
if [ "$SO_TESTE" -eq 1 ]; then
  msg "teste rápido concluído (--so-teste): treino completo não iniciado"
  exit 0
fi

# ---- 8-9. fases do treino completo ----
for fase in fase1 fase2 fase3; do
  estado "8/9 treino $fase"
  rodar "treino $fase" "$PY" scripts/train.py --execucao principal --fase "$fase"
  rc=$?
  [ "$rc" -eq 130 ] && exit 130
  [ "$rc" -eq 3 ] && msg "AVISO: $fase terminou com jobs que falharam (ver saida/erros); seguindo"
  estado "9/9 resultados após $fase"
  rodar "resultados $fase" "$PY" scripts/collect_results.py --execucao principal
  empacotar
  [ "$fase" = "$ATE" ] && break
done
msg "todas as etapas executadas"
