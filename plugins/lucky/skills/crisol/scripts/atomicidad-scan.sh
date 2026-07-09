#!/usr/bin/env bash
# atomicidad-scan — CITACIÓN mecánica al design-verifier (NO es un veredicto).
#
# Lista los archivos de código que el diff staged deja por encima del umbral T
# de líneas. El VEREDICTO (larga-legítima —tabla de lookup, switch exhaustivo,
# generado— vs responsabilidad-múltiple) lo da el JUEZ (design-verifier, LLM);
# este script solo GARANTIZA QUE MIRE. Las líneas convocan al juicio, no sentencian.
#
# Fuente única de "qué es código": reusa `crisol-enforcer.sh --print-code-policy`
# (cero drift de listas — la lección de F1). Umbral T con la misma precedencia que
# los guardianes: env CRISOL_ATOMICIDAD_T → docs/refactor/_crisol/atomicidad.conf → 400.
# Ajustable por chat (el operador pide "subí el umbral a N" → se escribe en el .conf).
#
# Salida a stdout; exit 0 SIEMPRE (es un reporter, no un gate).
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ENFORCER="$HERE/../hooks/crisol-enforcer.sh"

# Umbral: fuente ÚNICA = el enforcer (--print-threshold; parseo canónico env→conf→400).
# Cero copia del parseo acá. Si el enforcer no está, cae a 400 (pero sin policy no se
# cita nada igual).
_t() {
  local t=""
  [ -f "$ENFORCER" ] && t="$(bash "$ENFORCER" --print-threshold 2>/dev/null | head -1 | tr -d '[:space:]' || true)"
  case "$t" in ''|*[!0-9]*) t=400 ;; esac
  printf '%s' "$t"
}

# Política de código: fuente ÚNICA = el enforcer (--print-code-policy). SIN lista
# hardcodeada acá (evita la 4ta copia — hallazgo del design-verifier). Si el enforcer
# no está, la policy queda vacía y el scan NO cita nada (fail-closed-a-vacío: el
# design-verifier igual dictamina ATOMICIDAD a mano).
CODE_EXTS=""; CODE_FILENAMES=""
if [ -f "$ENFORCER" ]; then
  _pol="$(bash "$ENFORCER" --print-code-policy 2>/dev/null || true)"
  CODE_EXTS="$(printf '%s' "$_pol" | sed -n 1p)"
  CODE_FILENAMES="$(printf '%s' "$_pol" | sed -n 2p)"
fi

is_code() {
  local base lbase ext
  base="${1##*/}"; lbase="$(printf '%s' "$base" | tr '[:upper:]' '[:lower:]')"
  case " $CODE_FILENAMES " in *" $lbase "*) return 0 ;; esac
  case "$lbase" in
    ?*.*) ext="${lbase##*.}"; case " $CODE_EXTS " in *" $ext "*) return 0 ;; esac ;;
  esac
  return 1
}

T="$(_t)"
files="$(git diff --cached --name-only 2>/dev/null || true)"
[ -n "$files" ] || files="$(git diff --name-only 2>/dev/null || true)"

hits=0
printf '# atomicidad-scan · umbral T=%s líneas (citación al juez, NO veredicto)\n' "$T"
while IFS= read -r f; do
  [ -n "$f" ] || continue
  case "$f" in *.md|*.mdx|*.markdown|*.txt|*.rst|docs/*|*/docs/*) continue ;; esac
  is_code "$f" || continue
  [ -f "$f" ] || continue
  n="$(wc -l < "$f" 2>/dev/null | tr -d ' ')"
  printf '%s' "$n" | grep -qE '^[0-9]+$' 2>/dev/null || continue
  if [ "$n" -ge "$T" ]; then
    old="$(git show "HEAD:$f" 2>/dev/null | wc -l | tr -d ' ')"
    printf '%s' "$old" | grep -qE '^[0-9]+$' 2>/dev/null || old=0
    printf 'CITACION · %s · %s líneas (Δ %+d vs HEAD) · el juez decide: ¿UNA responsabilidad o varias?\n' "$f" "$n" "$((n-old))"
    hits=$((hits+1))
  fi
done <<< "$files"
[ "$hits" -eq 0 ] && printf '(cero unidades sobre el umbral; el design-verifier igual dictamina ATOMICIDAD sobre el diff)\n'
exit 0
