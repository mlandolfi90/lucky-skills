#!/usr/bin/env bash
# bitacora-push — hook SessionStart: inyecta el TOP-N de patrones LIVE del INDEX
# de la Bitácora como contexto al arrancar la sesión (modelo PUSH).
#
# Absorbido de ECC continuous-learning-v2 (inyección de instincts en SessionStart,
# cap + presupuesto) y adaptado a la doctrina lucky (ADR 0010):
#   - Inyecta SOLO el top-N por `usos` (jamás el INDEX entero — regla del propio
#     INDEX: "NO volcar este archivo entero al contexto").
#   - Solo entradas LIVE (evidencia confirmada); CANDIDATE/STALE jamás se inyectan.
#   - Presupuesto DURO de caracteres con recorte marcado.
#   - Solo en arranque real (source=startup); resume/clear/compact no re-inyectan.
#   - FAIL-OPEN total: cualquier error → additionalContext vacío, exit 0. Este
#     hook corre en TODA la flota (autoUpdate): jamás puede romper una sesión.
#
# Controles (env, 12-factor):
#   BITACORA_PUSH=off         → apagado (no inyecta nada)
#   BITACORA_PUSH_MAX=6       → máximo de filas inyectadas (default 6)
#   BITACORA_PUSH_MAX_CHARS=2000 → presupuesto duro de caracteres (default 2000)
#
# Contrato SessionStart:
#   stdin  = JSON del harness (incluye "source": startup|resume|clear|compact)
#   stdout = {"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"..."}}
#   exit 0 SIEMPRE.
set -uo pipefail
export LC_ALL=C.UTF-8 2>/dev/null || export LC_ALL=C

emit(){ # $1 = additionalContext YA escapado como string JSON (con comillas)
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":%s}}\n' "$1"
  exit 0
}
vacio(){ emit '""'; }

# ── off-switch ────────────────────────────────────────────────────────────────
case "$(printf '%s' "${BITACORA_PUSH:-}" | tr '[:upper:]' '[:lower:]')" in
  off|0|false) vacio ;;
esac

# ── solo en arranque real (startup); si no hay source, se asume startup ───────
INPUT="$(cat 2>/dev/null || true)"
SOURCE="$(printf '%s' "$INPUT" | grep -oE '"source"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*"([^"]*)"$/\1/' || true)"
if [ -n "$SOURCE" ] && [ "$SOURCE" != "startup" ]; then vacio; fi

# ── ubicar el INDEX (el hook vive en <skill>/hooks/) ──────────────────────────
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" 2>/dev/null && pwd -P)" || vacio
INDEX="$HERE/../INDEX.md"
[ -f "$INDEX" ] || vacio

# ── parámetros con default y saneo (solo dígitos; inválido → default) ─────────
MAXN="${BITACORA_PUSH_MAX:-6}"
case "$MAXN" in ''|*[!0-9]*) MAXN=6 ;; esac
MAXC="${BITACORA_PUSH_MAX_CHARS:-2000}"
case "$MAXC" in ''|*[!0-9]*) MAXC=2000 ;; esac
[ "$MAXN" -gt 0 ] || vacio

# ── extraer top-N LIVE del INDEX (ya viene ordenado por usos) ─────────────────
# Filas: | SÍNTOMA | TIPO | ACCIÓN | ENTRADA | validated_on | usos | estado |
LINES="$(awk -F'|' -v maxn="$MAXN" '
  /^\|/ {
    # saltar encabezado y separador
    if ($2 ~ /S[ÍI]NTOMA/ || $2 ~ /^[[:space:]]*-+[[:space:]]*$/) next
    estado=$8; gsub(/^[[:space:]]+|[[:space:]]+$/,"",estado)
    if (estado != "LIVE") next
    sintoma=$2; accion=$4; entrada=$5
    gsub(/^[[:space:]]+|[[:space:]]+$/,"",sintoma)
    gsub(/^[[:space:]]+|[[:space:]]+$/,"",accion)
    id=entrada; sub(/^[^\[]*\[/,"",id); sub(/\].*$/,"",id)
    if (sintoma=="" || accion=="") next
    n++
    if (n>maxn) exit
    printf "- %s -> %s (%s)\n", sintoma, accion, id
  }
' "$INDEX" 2>/dev/null || true)"
[ -n "$LINES" ] || vacio

BLOCK="[BITACORA · push] Patrones LIVE confirmados (síntoma -> acción; detalle: /bitacora):
$LINES
(Regla: si un síntoma matchea, abrí SOLO esa entrada. No volcar el INDEX entero.)"

# ── presupuesto duro de caracteres ────────────────────────────────────────────
BLOCK="$(printf '%s' "$BLOCK" | awk -v maxc="$MAXC" '
  { buf = buf $0 "\n" }
  END {
    if (length(buf) > maxc) buf = substr(buf, 1, maxc) "\n…(recortado por presupuesto BITACORA_PUSH_MAX_CHARS)"
    printf "%s", buf
  }
' || true)"
[ -n "$BLOCK" ] || vacio

# ── escapar como string JSON (puro awk: sin dependencia de python) ────────────
JSON="$(printf '%s' "$BLOCK" | awk '
  BEGIN { out = "" }
  {
    line = $0
    gsub(/\\/, "\\\\", line)
    gsub(/"/, "\\\"", line)
    gsub(/\t/, "\\t", line)
    gsub(/\r/, "", line)
    out = out (NR>1 ? "\\n" : "") line
  }
  END { printf "\"%s\"", out }
' || true)"
case "$JSON" in \"*\") emit "$JSON" ;; *) vacio ;; esac
