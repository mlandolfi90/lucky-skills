#!/usr/bin/env bash
# test-atomicidad-scan — el escaneo CITA las unidades > T sobre el diff staged,
# reusa la política de código del enforcer (fuente única), respeta el umbral
# configurable, y NUNCA emite veredicto (solo citaciones). exit 0 siempre.
set -uo pipefail

SCAN="$(cd "$(dirname "$0")/.." && pwd)/scripts/atomicidad-scan.sh"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
R="$TMP/repo"; mkdir -p "$R/docs/refactor/_crisol"
( cd "$R" && { git init -q -b main 2>/dev/null || { git init -q && git checkout -qb main; }; }
  git -C "$R" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init )

PASS=0; FAIL=0
ok(){ if eval "$2"; then PASS=$((PASS+1)); echo "  ✅ $1"; else FAIL=$((FAIL+1)); echo "  ❌ $1"; fi; }

mkfile(){ ( cd "$R" && { i=1; while [ $i -le "$2" ]; do echo "x=$i"; i=$((i+1)); done > "$1"; git add "$1"; } ); }

echo "== atomicidad-scan =="

# 1. archivo grande (.py, 450 >= 400) -> CITACION
mkfile big.py 450
OUT="$( cd "$R" && bash "$SCAN" )"
ok "cita big.py (450>=400)"            'printf "%s" "$OUT" | grep -q "CITACION · big.py"'
ok "reporta el umbral T=400"           'printf "%s" "$OUT" | grep -q "T=400"'
ok "NO emite veredicto (solo cita)"    '! printf "%s" "$OUT" | grep -qiE "PASS|FAIL|REJECT|APPROVE"'

# 2. archivo chico (.py, 100 < 400) -> sin citación
( cd "$R" && git reset -q . ); mkfile small.py 100
OUT="$( cd "$R" && bash "$SCAN" )"
ok "NO cita small.py (100<400)"        '! printf "%s" "$OUT" | grep -q "CITACION · small.py"'

# 3. no-código (.json grande) -> nunca se cita (política del enforcer)
( cd "$R" && git reset -q . ; { i=1; while [ $i -le 900 ]; do echo "\"k$i\": $i,"; i=$((i+1)); done > big.json; } && git add big.json )
OUT="$( cd "$R" && bash "$SCAN" )"
ok "NO cita big.json (no es código)"   '! printf "%s" "$OUT" | grep -q "CITACION · big.json"'

# 4. umbral configurable por conf: conf=50 -> small.py (100>=50) se cita
( cd "$R" && git reset -q . ) ; printf '50\n' > "$R/docs/refactor/_crisol/atomicidad.conf"; mkfile small.py 100
OUT="$( cd "$R" && bash "$SCAN" )"
ok "conf=50 cita small.py (100>=50)"   'printf "%s" "$OUT" | grep -q "CITACION · small.py"'
rm -f "$R/docs/refactor/_crisol/atomicidad.conf"

# 5. env gana sobre conf/default: T=9999 -> big.py no se cita
( cd "$R" && git reset -q . ); mkfile big.py 450
OUT="$( cd "$R" && CRISOL_ATOMICIDAD_T=9999 bash "$SCAN" )"
ok "env T=9999 no cita big.py"         '! printf "%s" "$OUT" | grep -q "CITACION · big.py"'

# 6. exit 0 siempre (es reporter, no gate)
( cd "$R" && bash "$SCAN" >/dev/null 2>&1 ); ok "exit 0 (reporter)" '[ $? -eq 0 ]'

echo; echo "PASS=$PASS FAIL=$FAIL"; [ "$FAIL" -eq 0 ]
