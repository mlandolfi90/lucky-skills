#!/usr/bin/env bash
# bitacora-stale — reporta entradas de Bitácora VENCIDAS (validated_on más viejo
# que el umbral, o ausente → nace STALE). Convierte el reloj de validez en señal.
#
# Filosofía (calcada de brujula/crisol-pulso): READ-ONLY (reporta, no borra ni
# edita) y FAIL-SOFT (exit 0 SIEMPRE — es un reporter del heartbeat, NO un gate;
# jamás traba al humano). El que degrada visiblemente la entrada es la brújula al
# surfacearla con bandera; este script solo la nombra.
#
# La verificación del commit-ancla de validated_on es fiable solo intra-repo;
# cross-repo el ancla portable es la FECHA — por eso el validador mide por fecha.
#
# Entorno: GNU date (Linux / Git-Bash en Windows). 'date -d' es GNU.
# Uso:
#   bash bitacora-stale.sh                         # entries/ junto a este script, hoy = sistema
#   bash bitacora-stale.sh --today 2026-09-30      # fecha de referencia fija (determinismo/test)
#   bash bitacora-stale.sh --umbral 30 <dir>       # umbral en días + directorio explícito
set -uo pipefail
export LC_ALL=C

UMBRAL=90
TODAY=""
DIR=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --today)         TODAY="${2:-}"; shift 2 || shift ;;
    --umbral|--days) UMBRAL="${2:-90}"; shift 2 || shift ;;
    --*)             shift ;;                 # flag desconocido → ignorar (fail-soft)
    *)               DIR="$1"; shift ;;
  esac
done

# Directorio por defecto: entries/ relativo a este script.
if [ -z "$DIR" ]; then
  SELF="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"
  DIR="$SELF/../entries"
fi
[ -d "$DIR" ] || { echo "N/D — sin directorio de entradas ($DIR)"; exit 0; }

# Epoch (segundos) de una fecha YYYY-MM-DD; vacío si no parsea.
epoch_of(){ date -d "$1" +%s 2>/dev/null; }

if [ -n "$TODAY" ]; then NOW_S="$(epoch_of "$TODAY")"; else NOW_S="$(date +%s 2>/dev/null)"; fi
if [ -z "${NOW_S:-}" ]; then echo "N/D — no se pudo resolver la fecha de hoy (¿GNU date?)"; exit 0; fi

total=0; live=0; stale=0
declare -a STALE_LINES=()

for f in "$DIR"/*.md; do
  [ -f "$f" ] || continue
  total=$((total+1))
  id="$(basename "$f" .md)"

  # Entradas jubiladas/superseded no se reportan como STALE (ya están fuera de servicio).
  estado="$(grep -iE '^\s*-\s*\*\*estado:\*\*' "$f" 2>/dev/null | head -1 || true)"
  case "$estado" in
    *RETIRED*|*SUPERSEDED*) continue ;;
  esac

  # Fecha de validated_on: primer YYYY-MM-DD en esa línea.
  vline="$(grep -iE 'validated_on' "$f" 2>/dev/null | head -1 || true)"
  vdate="$(printf '%s' "$vline" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1 || true)"

  if [ -z "$vdate" ]; then
    stale=$((stale+1))
    STALE_LINES+=("  ⚠ $id · STALE · sin validated_on (nace STALE)")
    continue
  fi

  vs="$(epoch_of "$vdate")"
  if [ -z "${vs:-}" ]; then
    stale=$((stale+1))
    STALE_LINES+=("  ⚠ $id · STALE · validated_on ilegible ($vdate)")
    continue
  fi

  age=$(( (NOW_S - vs) / 86400 ))
  if [ "$age" -gt "$UMBRAL" ]; then
    stale=$((stale+1))
    STALE_LINES+=("  ⚠ $id · STALE · validated_on $vdate (${age}d > ${UMBRAL}d)")
  else
    live=$((live+1))
  fi
done

echo "📓 BITÁCORA-STALE — $DIR (hoy=${TODAY:-sistema}, umbral=${UMBRAL}d)"
echo "  Entradas: $total · vigentes: $live · STALE: $stale"
if [ "$stale" -gt 0 ]; then
  printf '%s\n' "${STALE_LINES[@]}"
  echo "  → STALE no se borra: la brújula la surface con bandera '⚠ verificar antes de confiar'."
fi
exit 0
