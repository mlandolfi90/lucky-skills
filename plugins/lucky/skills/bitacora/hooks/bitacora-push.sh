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
# Además del top-N, inyecta el TIMBRE DE JUICIO (⚖ JUICIO PENDIENTE): cuenta lo
# que espera decisión HUMANA — señales con visto ≥ 2 en el log local del
# observador y entradas CANDIDATE del INDEX — e instruye al agente a avisarle
# al humano. Cero juicio automático: solo conteo y aviso; si no hay nada
# pendiente, la sección no existe (cero ruido). Enmienda 2026-07-09 al ADR 0010.
#
# Controles (env, 12-factor):
#   BITACORA_PUSH=off         → apagado (no inyecta nada, timbre incluido)
#   BITACORA_PUSH_MAX=6       → máximo de filas inyectadas (default 6)
#   BITACORA_PUSH_MAX_CHARS=2000 → presupuesto duro de caracteres (default 2000)
#   BITACORA_OBSERVAR_DIR=<dir>  → override del dir del log del observador (tests)
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

# ── destino del log del observador — COPIA EXACTA de bitacora-observar.sh:log_dir
#    (editar acá => editar allá; la paridad la prueba test-push.sh vía
#    --print-log-dir en ambos hooks, mismo patrón que ADR 0008) ────────────────
log_dir(){
  if [ -n "${BITACORA_OBSERVAR_DIR:-}" ]; then printf '%s' "$BITACORA_OBSERVAR_DIR"; return; fi
  if [ -n "${LOCALAPPDATA:-}" ]; then
    printf '%s/lucky/bitacora' "$(cygpath -u "$LOCALAPPDATA" 2>/dev/null || printf '%s' "$LOCALAPPDATA")"
  else
    printf '%s/lucky/bitacora' "${XDG_DATA_HOME:-$HOME/.local/share}"
  fi
}

# Introspección para el fixture de paridad; sale sin leer stdin.
if [ "${1:-}" = "--print-log-dir" ]; then
  printf '%s\n' "$(log_dir)"
  exit 0
fi

# ── off-switch ────────────────────────────────────────────────────────────────
case "$(printf '%s' "${BITACORA_PUSH:-}" | tr '[:upper:]' '[:lower:]')" in
  off|0|false) vacio ;;
esac

# ── solo en arranque real (startup); si no hay source, se asume startup ───────
INPUT="$(cat 2>/dev/null || true)"
SOURCE="$(printf '%s' "$INPUT" | grep -oE '"source"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*"([^"]*)"$/\1/' || true)"
if [ -n "$SOURCE" ] && [ "$SOURCE" != "startup" ]; then vacio; fi

# ── ubicar el INDEX (el hook vive en <skill>/hooks/) ──────────────────────────
# Sin INDEX no hay patrones ni conteo de CANDIDATE, pero el timbre de señales
# del log local sigue vivo → no cortar acá.
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" 2>/dev/null && pwd -P)" || vacio
INDEX="$HERE/../INDEX.md"

# ── parámetros con default y saneo (solo dígitos; inválido → default) ─────────
MAXN="${BITACORA_PUSH_MAX:-6}"
case "$MAXN" in ''|*[!0-9]*) MAXN=6 ;; esac
MAXC="${BITACORA_PUSH_MAX_CHARS:-2000}"
case "$MAXC" in ''|*[!0-9]*) MAXC=2000 ;; esac
[ "$MAXN" -gt 0 ] || vacio

# ── extraer top-N LIVE del INDEX (ya viene ordenado por usos) ─────────────────
# Filas: | SÍNTOMA | TIPO | ACCIÓN | ENTRADA | validated_on | usos | estado |
LINES=""
if [ -f "$INDEX" ]; then
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
fi

# ── TIMBRE DE JUICIO (enmienda ADR 0010): contar lo que espera decisión HUMANA ─
# (a) entradas CANDIDATE en el INDEX (esperan endoso: LIVE o afuera)
CAND=0
if [ -f "$INDEX" ]; then
  CAND="$(awk -F'|' '
    /^\|/ {
      if ($2 ~ /S[ÍI]NTOMA/ || $2 ~ /^[[:space:]]*-+[[:space:]]*$/) next
      estado=$8; gsub(/^[[:space:]]+|[[:space:]]+$/,"",estado)
      if (estado == "CANDIDATE") n++
    }
    END { print n+0 }
  ' "$INDEX" 2>/dev/null || echo 0)"
fi
case "$CAND" in ''|*[!0-9]*) CAND=0 ;; esac

# (b) señales con visto ≥ 2 en el log local del observador (líneas = sesiones
#     avistadas por etiqueta — la semántica `visto: N` de SENALES.md)
SEN=0
OBSLOG="$(log_dir)/observaciones.log"
if [ -f "$OBSLOG" ]; then
  SEN="$(awk -F' · ' 'NF>=4 { c[$3]++ } END { n=0; for (k in c) if (c[k]>=2) n++; print n+0 }' "$OBSLOG" 2>/dev/null || echo 0)"
fi
case "$SEN" in ''|*[!0-9]*) SEN=0 ;; esac

# (c) PUENTE log↔SENALES (enmienda 2 ADR 0010, escalera de frecuencia de ECC
#     terminando en ENDOSO): etiquetas con ≥2 sesiones acumuladas que NO tienen
#     señal formal en SENALES.md → proponer formalizar (cosecha), jamás escribir.
PUENTE=0
SENALES_MD="$HERE/../SENALES.md"
if [ -f "$OBSLOG" ]; then
  while IFS= read -r _ETI; do
    [ -n "$_ETI" ] || continue
    if [ ! -f "$SENALES_MD" ] || ! grep -q "$_ETI" "$SENALES_MD" 2>/dev/null; then
      PUENTE=$((PUENTE+1))
    fi
  done <<PUENTE_EOF
$(awk -F' · ' 'NF>=4 { c[$3]++ } END { for (k in c) if (c[k]>=2) print k }' "$OBSLOG" 2>/dev/null || true)
PUENTE_EOF
fi
case "$PUENTE" in ''|*[!0-9]*) PUENTE=0 ;; esac

# (d) INTENSIDAD (enmienda 3 ADR 0010 — "el costo agudo ES evidencia"):
#     etiquetas con x≥umbral en UNA sola sesión → proponer cosecha de
#     INTENSIDAD (destilar a INDEX-CANDIDATE). El log prueba QUE dolió;
#     el QUÉ lo pone el postmortem/humano en la cosecha.
UMBRAL_INT="${BITACORA_INTENSIDAD_UMBRAL:-10}"
case "$UMBRAL_INT" in ''|*[!0-9]*) UMBRAL_INT=10 ;; esac
INTENSO=0
if [ -f "$OBSLOG" ] && [ "$UMBRAL_INT" -gt 0 ]; then
  INTENSO="$(awk -F' · ' -v u="$UMBRAL_INT" '
    NF>=4 { n=$4; sub(/^x/,"",n); if (n+0 >= u) c[$3]=1 }
    END { t=0; for (k in c) t++; print t+0 }
  ' "$OBSLOG" 2>/dev/null || echo 0)"
fi
case "$INTENSO" in ''|*[!0-9]*) INTENSO=0 ;; esac

BELL=""
if [ "$SEN" -gt 0 ] || [ "$CAND" -gt 0 ] || [ "$PUENTE" -gt 0 ] || [ "$INTENSO" -gt 0 ]; then
  BELL="⚖ JUICIO PENDIENTE — avisale al humano en tu primera respuesta (vos no juzgás; él decide):"
  if [ "$SEN" -gt 0 ]; then
    BELL="$BELL
- $SEN señal(es) con visto ≥ 2 en el log local del observador → que corra el hook bitacora-observar.sh --resumen y decida: investigar o refutar (SENALES.md)"
  fi
  if [ "$CAND" -gt 0 ]; then
    BELL="$BELL
- $CAND entrada(s) CANDIDATE esperando endoso humano → promover a LIVE o retirar (INDEX de la bitácora)"
  fi
  if [ "$PUENTE" -gt 0 ]; then
    BELL="$BELL
- $PUENTE etiqueta(s) del log acumulan ≥ 2 sesiones SIN señal formal en SENALES.md → pedí la cosecha (\"/bitacora cosechar\") para formalizarlas o refutarlas"
  fi
  if [ "$INTENSO" -gt 0 ]; then
    BELL="$BELL
- $INTENSO etiqueta(s) con INTENSIDAD x ≥ $UMBRAL_INT en una sola sesión (costo agudo) → si hubo aprendizaje real, pedí la cosecha de intensidad: destila a INDEX-CANDIDATE (descontando meta-ruido)"
  fi
fi

# ── armar el bloque: TIMBRE PRIMERO (sobrevive al recorte), patrones después ──
[ -n "$LINES" ] || [ -n "$BELL" ] || vacio
BLOCK="[BITACORA · push]"
if [ -n "$BELL" ]; then
  BLOCK="$BLOCK
$BELL"
fi
if [ -n "$LINES" ]; then
  BLOCK="$BLOCK
Patrones LIVE confirmados (síntoma -> acción; detalle: /bitacora):
$LINES
(Regla: si un síntoma matchea, abrí SOLO esa entrada. No volcar el INDEX entero.)"
fi

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
    # RFC 8259: U+0000–U+001F van escapados en un string JSON. Los control
    # chars que sobreviven hasta aca (ESC de ANSI pegado en un sintoma, \r,
    # etc.) se ELIMINAN: no aportan y romperian json.loads en toda la flota.
    # Hallazgo del panel adversarial (iter2, corrida timbre-de-juicio).
    gsub(/[[:cntrl:]]/, "", line)
    out = out (NR>1 ? "\\n" : "") line
  }
  END { printf "\"%s\"", out }
' || true)"
case "$JSON" in \"*\") emit "$JSON" ;; *) vacio ;; esac
