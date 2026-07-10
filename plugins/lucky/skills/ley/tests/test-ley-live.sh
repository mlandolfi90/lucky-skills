#!/usr/bin/env bash
# Suite de ley-live.sh — determinista; casos 1-6 sin red (la rama de red se
# corta antes vía LEY_LIVE_CLON); el caso 7 PUEDE tocar ls-remote (con o sin
# red debe dar exit 0 — eso es lo que prueba). PASS/FAIL con exit real.
set -u

HOOK="$(cd "$(dirname "$0")/.." && pwd)/hooks/ley-live.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
PASS=0; FAIL=0

check() { # $1 nombre · $2 exit esperado · $3 exit real
  if [ "$2" = "$3" ]; then PASS=$((PASS+1)); echo "  ok $1";
  else FAIL=$((FAIL+1)); echo "  XX $1 (esperado exit=$2, real=$3)"; fi
}

# 1) sintaxis válida
bash -n "$HOOK"; check "sintaxis bash -n" 0 $?

# 2) off-switch: LEY_LIVE=off → exit 0 inmediato
LEY_LIVE=off bash "$HOOK"; check "off-switch exit 0" 0 $?

# 3) sin clon (ruta inexistente) → fail-open exit 0
LEY_LIVE_CLON="$TMP/no-existe" bash "$HOOK"; check "sin clon → fail-open" 0 $?

# 4) directorio sin .git → fail-open exit 0
mkdir -p "$TMP/plano"
LEY_LIVE_CLON="$TMP/plano" bash "$HOOK"; check "dir sin .git → fail-open" 0 $?

# 5) el hook JAMÁS escribe fuera del clon: correrlo con clon inválido no crea nada en $TMP
ANTES=$(ls -A "$TMP" | wc -l)
LEY_LIVE_CLON="$TMP/no-existe" bash "$HOOK" >/dev/null 2>&1
DESPUES=$(ls -A "$TMP" | wc -l)
[ "$ANTES" = "$DESPUES" ]; check "no crea artefactos colaterales" 0 $?

# 6) silencioso: con off-switch no emite NADA a stdout
OUT="$(LEY_LIVE=off bash "$HOOK")"
[ -z "$OUT" ]; check "stdout vacío (silencioso)" 0 $?

# 7) fail-open ante clon git VACÍO (sin remoto ni tags): exit 0 sin colgarse
#    (la rama ls-remote usa la URL fija; acá el describe/ff fallan → exit 0)
git init -q "$TMP/vacio" 2>/dev/null
GIT_TERMINAL_PROMPT=0 LEY_LIVE_CLON="$TMP/vacio" timeout 30 bash "$HOOK" >/dev/null 2>&1
RC=$?; [ "$RC" = "0" ] && R=0 || R=1
check "clon git vacío → fail-open sin colgar" 0 $R

echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" = "0" ]
