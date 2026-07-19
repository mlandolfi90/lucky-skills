#!/usr/bin/env bash
# test-superficie-index — GUARDIÁN de la superficie del INDEX.md REAL de bitácora.
#
# El dolor: hooks/bitacora-push.sh y scripts/bitacora-lint.sh parsean el INDEX
# POSICIONALMENTE con `awk -F'|'` ($8=estado, $2/$4/$5, $6/$7/$8). El hook viaja
# a TODA la flota por autoUpdate (ADR 0006). HOY ningún test lee el INDEX.md REAL:
# test-lint.sh y test-push.sh usan fixtures con header propio inline. Si alguien
# cambia una columna del archivo real, la suite queda verde y el awk de la flota
# se rompe EN SILENCIO. Este test congela la superficie del archivo real.
set -uo pipefail
export LC_ALL=C

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
INDEX="$HERE/../INDEX.md"
PUSH_SRC="$HERE/../hooks/bitacora-push.sh"

PASS=0; FAIL=0
check(){ if [ "$2" = "$3" ]; then PASS=$((PASS+1)); echo "  ✅ $1"; else FAIL=$((FAIL+1)); echo "  ❌ $1 (esperado '$2', obtuvo '$3')"; fi; }

# ── contrato congelado: header literal de 7 columnas ─────────────────────────
EXPECTED_HEADER='| SÍNTOMA OBSERVABLE (lo que ves) | TIPO | ACCIÓN (1 línea) | ENTRADA | validated_on | usos | estado |'

# primera línea que empieza con "| SÍNTOMA" (byte-literal; el ^ ancla, el | es literal en BRE)
header_of(){ grep -m1 '^| SÍNTOMA' "$1"; }

# aridad: cuenta filas de DATOS con NF!=9 bajo awk -F'|' (7 celdas + 2 bordes).
# Ignora: header, separador |---|, y filas con pipe ESCAPADO '\|' dentro de una
# celda — mismo trato que bitacora-lint.sh (case *'\|'*), que las maneja aparte.
bad_arity_count(){
  awk -F'|' '
    /^\|/ {
      if ($0 ~ /\\\|/) next                      # pipe escapado en celda: lo maneja el lint aparte
      if ($2 ~ /S[ÍI]NTOMA/) next                # header (mismo regex que push/lint)
      if ($0 ~ /^\|[-|[:space:]]*$/) next         # separador |---|---|...
      if (NF != 9) n++
    }
    END { print n+0 }
  ' "$1"
}

echo "test-superficie-index — INDEX real: $INDEX"

# ══ A0 — RED_GREEN: el detector se prueba a sí mismo (patrón test-pin-scan.sh) ══
# Sobre una COPIA del INDEX real mutada, los detectores de A1 y A2 DEBEN disparar.
SANDBOX="$(mktemp -d)"; trap 'rm -rf "$SANDBOX"' EXIT
cp "$INDEX" "$SANDBOX/INDEX.md"

# (a) mutar el header: renombrar la 7ª columna 'estado' -> 'status'
sed 's/| estado |/| status |/' "$INDEX" > "$SANDBOX/INDEX.md"
MUT_HEADER="$(header_of "$SANDBOX/INDEX.md")"
check "A0.a rojo: header mutado ('estado'->'status') es detectado" \
  "distinto" "$([ "$MUT_HEADER" != "$EXPECTED_HEADER" ] && echo distinto || echo igual)"

# (b) mutar la aridad: sumar una columna a una fila de datos (NF pasa a 10)
cp "$INDEX" "$SANDBOX/INDEX.md"
printf '| a | b | c | d | e | f | g | h |\n' >> "$SANDBOX/INDEX.md"
check "A0.b rojo: fila con columna de más (NF!=9) es detectada" \
  "detectada" "$([ "$(bad_arity_count "$SANDBOX/INDEX.md")" -ge 1 ] && echo detectada || echo perdida)"

# ══ A1 — header literal congelado (verde contra el archivo REAL) ══════════════
ACTUAL_HEADER="$(header_of "$INDEX")"
if [ "$ACTUAL_HEADER" = "$EXPECTED_HEADER" ]; then
  PASS=$((PASS+1)); echo "  ✅ A1 header literal de 7 columnas congelado"
else
  FAIL=$((FAIL+1))
  echo "  ❌ A1 el header del INDEX real cambió"
  echo "     esperado: $EXPECTED_HEADER"
  echo "     obtuvo:   $ACTUAL_HEADER"
  echo "     POR QUÉ DUELE: el awk -F'|' posicional de bitacora-push.sh (\$8=estado)"
  echo "     viaja a la flota por autoUpdate — si esta columna cambia, actualizá"
  echo "     TAMBIÉN el hook y el lint, y recién DESPUÉS este literal."
fi

# ══ A2 — aridad de TODAS las filas de datos del INDEX real ════════════════════
check "A2 toda fila de datos tiene NF==9 (7 celdas + 2 bordes)" "0" "$(bad_arity_count "$INDEX")"

# ══ A3 — coherencia con el consumidor: $8 sigue siendo estado==LIVE en el hook ═
# Si el hook migrara de columna, este assert avisa que el contrato cambió de lugar.
A3_FIELD="$(grep -cE 'estado[[:space:]]*=[[:space:]]*\$8' "$PUSH_SRC" || true)"
A3_LIVE="$(grep -cF '!= "LIVE"' "$PUSH_SRC" || true)"
if [ "${A3_FIELD:-0}" -ge 1 ] && [ "${A3_LIVE:-0}" -ge 1 ]; then
  PASS=$((PASS+1)); echo "  ✅ A3 bitacora-push.sh sigue leyendo \$8 como estado y filtrando LIVE"
else
  FAIL=$((FAIL+1))
  echo "  ❌ A3 el contrato \$8=estado / LIVE cambió de lugar en bitacora-push.sh"
  echo "     (estado=\$8: $A3_FIELD match, != \"LIVE\": $A3_LIVE match)"
  echo "     RECONCILIÁ: el hook ya no compara la 7ª columna (\$8) contra LIVE."
  echo "     Actualizá este assert Y el header esperado A1 juntos, o el guardián miente."
fi

echo
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
