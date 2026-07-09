#!/usr/bin/env bash
# bitacora-observar — hook SessionEnd: barre el transcript de la sesión buscando
# SEÑALES DÉBILES (near-miss, hiyari-hatto) y las acumula en un log LOCAL.
#
# Absorbido de ECC continuous-learning-v2 (observación por hooks) y adaptado a la
# doctrina lucky (ADR 0010):
#   - Detección 100% DETERMINISTA (grep de marcadores conocidos), sin LLM.
#   - El log es EVIDENCIA CRUDA, NO catálogo: nada entra al INDEX ni a SENALES.md
#     por esta vía. La promoción sigue siendo acto humano (regla "sin evidencia
#     real, NO entra" — el log ES la evidencia que el humano revisa).
#   - Zero-leak por construcción: se registran SOLO etiquetas de señal + conteos
#     (jamás contenido del transcript, jamás rutas completas ni secretos).
#   - Log LOCAL por máquina (fuera del repo), con rotación dura.
#   - FAIL-OPEN total: cualquier error → exit 0 silencioso. Corre en toda la flota.
#
# Controles (env, 12-factor):
#   BITACORA_OBSERVAR=off        → apagado
#   BITACORA_OBSERVAR_DIR=<dir>  → override del directorio del log (tests)
#
# Uso operador:
#   bash bitacora-observar.sh --resumen   → agrega el log: qué señal, cuántas veces
#     (visto ≥ 2 → candidata a investigar; ver SENALES.md de la bitácora)
set -uo pipefail
export LC_ALL=C

# ── señales deterministas: ETIQUETA<TAB>regex (marcadores que emiten los propios
#    guardianes/suites de lucky — ampliar acá es ampliar la observación) ─────────
SIGNALS='GATE-BLOQUEO	\[CRISOL\] BLOQUEADO
COBERTURA-BLOQUEO	\[CRISOL - COBERTURA\] BLOQUEADO
ENFORCER-BLOQUEO	CRISOL BLOQUEADO:
SUITE-ROJA	PASS=[0-9]+ FAIL=[1-9]
INTEGRIDAD	INTEGRIDAD FALLA|MISMATCH sha256
LEY-DIFERIDA	DIFERIDO \(publicado
FALSO-VERDE	FALSO-VERDE'

# ── destino del log (LOCAL, fuera del repo; override para tests) ───────────────
log_dir(){
  if [ -n "${BITACORA_OBSERVAR_DIR:-}" ]; then printf '%s' "$BITACORA_OBSERVAR_DIR"; return; fi
  if [ -n "${LOCALAPPDATA:-}" ]; then
    printf '%s/lucky/bitacora' "$(cygpath -u "$LOCALAPPDATA" 2>/dev/null || printf '%s' "$LOCALAPPDATA")"
  else
    printf '%s/lucky/bitacora' "${XDG_DATA_HOME:-$HOME/.local/share}"
  fi
}
LOG="$(log_dir)/observaciones.log"

# Introspección para el fixture de paridad con bitacora-push.sh (que copia
# log_dir para el timbre de juicio); sale sin leer stdin. Patrón ADR 0008.
if [ "${1:-}" = "--print-log-dir" ]; then
  printf '%s\n' "$(log_dir)"
  exit 0
fi

# ── modo resumen (lo corre el humano; agrega el log acumulado) ─────────────────
if [ "${1:-}" = "--resumen" ]; then
  if [ ! -s "$LOG" ]; then echo "bitacora-observar: log vacío ($LOG) — nada observado aún."; exit 0; fi
  echo "SEÑAL · veces-vista · sesiones (log: $LOG)"
  awk -F' · ' '
    { sub(/^x/,"",$4); n[$3]+=$4; s[$3]++ }
    END { for (k in n) printf "  %s · x%d · %d sesion(es)\n", k, n[k], s[k] }
  ' "$LOG" 2>/dev/null | sort -t'x' -k2 -rn
  echo "(visto ≥ 2 → investigar en la próxima corrida que lo roce; ver SENALES.md)"
  exit 0
fi

# ── off-switch ──────────────────────────────────────────────────────────────────
case "$(printf '%s' "${BITACORA_OBSERVAR:-}" | tr '[:upper:]' '[:lower:]')" in
  off|0|false) exit 0 ;;
esac

# ── hook SessionEnd: extraer transcript_path + cwd del JSON (estilo enforcer) ───
INPUT="$(cat 2>/dev/null || true)"
TRANSCRIPT="$(printf '%s' "$INPUT" | grep -oE '"transcript_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*"transcript_path"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/' || true)"
CWD="$(printf '%s' "$INPUT" | grep -oE '"cwd"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*"cwd"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/' || true)"
[ -n "$TRANSCRIPT" ] || exit 0
# El JSON escapa '\' como '\\' (rutas Windows): des-escapar para poder abrir el archivo.
TRANSCRIPT="$(printf '%s' "$TRANSCRIPT" | sed 's/\\\\/\//g; s/\\\//\//g')"
[ -f "$TRANSCRIPT" ] || exit 0

# repo = basename del cwd (jamás la ruta completa: zero-leak)
REPO="desconocido"
if [ -n "$CWD" ]; then REPO="$(basename "$(printf '%s' "$CWD" | sed 's/\\\\/\//g')" 2>/dev/null || echo desconocido)"; fi
FECHA="$(date '+%Y-%m-%d %H:%M' 2>/dev/null || echo 's/f')"

# ── barrer señales y acumular (solo etiqueta + conteo; nunca contenido) ─────────
OUT=""
while IFS="$(printf '\t')" read -r ETI RE; do
  [ -n "$ETI" ] || continue
  N="$(grep -cE "$RE" "$TRANSCRIPT" 2>/dev/null || true)"
  case "$N" in ''|*[!0-9]*) N=0 ;; esac
  if [ "$N" -gt 0 ]; then
    OUT="${OUT}${FECHA} · ${REPO} · ${ETI} · x${N}
"
  fi
done <<EOF
$SIGNALS
EOF
[ -n "$OUT" ] || exit 0

mkdir -p "$(log_dir)" 2>/dev/null || exit 0
printf '%s' "$OUT" >> "$LOG" 2>/dev/null || exit 0

# ── rotación dura: conservar las últimas 400 líneas ─────────────────────────────
LINES="$(wc -l < "$LOG" 2>/dev/null | tr -d ' ' || echo 0)"
case "$LINES" in *[!0-9]*|'') LINES=0 ;; esac
if [ "$LINES" -gt 400 ]; then
  TMP="$LOG.tmp.$$"
  tail -400 "$LOG" > "$TMP" 2>/dev/null && mv -f "$TMP" "$LOG" 2>/dev/null || rm -f "$TMP" 2>/dev/null
fi
exit 0
