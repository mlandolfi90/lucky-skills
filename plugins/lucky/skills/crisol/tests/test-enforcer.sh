#!/usr/bin/env bash
# test-enforcer — ¿Quién verifica al Verificador?
# Fixture: repos de juguete + casos binarios contra crisol-enforcer.sh (bash) Y
# contra crisol_gate.py (global) — fuente única de verdad de la regla para que
# los dos guardianes JAMÁS deriven (condición del Steward, c5).
#
# Cubre: cambio A (exigir TARGET en repos adoptados) + cambio B (piso TARGET
# global para repos NO adoptados, per repo+session_id) + invariantes FAIL-OPEN.
#
# El gate bajo prueba se elige con CRISOL_GATE_OVERRIDE (para testear la copia
# versionada del repo ANTES de desplegarla a ~/.claude/hooks). Por defecto usa
# el desplegado.
set -uo pipefail

HOOK="$(cd "$(dirname "$0")/.." && pwd)/hooks/crisol-enforcer.sh"
GATE="${CRISOL_GATE_OVERRIDE:-$HOME/.claude/hooks/crisol_gate.py}"
PYBIN="$(command -v python || command -v python3 || echo python)"

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
ADOPTED="$TMP/adopted"; PLAIN="$TMP/plain"; CACHE="$TMP/cache"
mkdir -p "$ADOPTED" "$PLAIN" "$CACHE"
for R in "$ADOPTED" "$PLAIN"; do
  ( cd "$R" && { git init -q -b main 2>/dev/null || { git init -q && git checkout -qb main; }; }
    git -C "$R" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init )
done
mkdir -p "$ADOPTED/docs/refactor/_crisol"

wpath(){ cygpath -m "$1" 2>/dev/null || ( cd "$1" 2>/dev/null && pwd -W ) 2>/dev/null || echo "$1"; }
WADOPTED="$(wpath "$ADOPTED")"; WPLAIN="$(wpath "$PLAIN")"
export CRISOL_TARGET_CACHE_DIR="$(wpath "$CACHE")"

PASS=0; FAIL=0
check(){ if [ "$2" -eq "$3" ] 2>/dev/null; then PASS=$((PASS+1)); echo "  ✅ $1"
         else FAIL=$((FAIL+1)); echo "  ❌ $1 (esperado exit $2, obtuvo $3)"; fi; }
have_gate(){ [ -f "$GATE" ] && command -v "${PYBIN%% *}" >/dev/null 2>&1; }

ledger(){ printf '%b' "$1" > "$ADOPTED/docs/refactor/_crisol/RUN-LEDGER.md"; }

# bash enforcer (corre con PWD = repo)
run_hook(){ ( cd "$1" && printf '{"tool_input":{"file_path":"%s"}}' "$2" | bash "$HOOK" >/dev/null 2>&1; echo $? ); }
hook_check(){ if have_gate || true; then check "enforcer.sh: $1" "$3" "$(run_hook "$2" "$4")"; fi; }

# gate.py (no depende de PWD: cwd va en el JSON)
run_gate(){ # file_path cwd_win sid("" none) tool(Edit)
  have_gate || { echo skip; return; }
  local fp="$1" cwd="$2" sid="$3" tool="${4:-Edit}" json
  if [ -n "$sid" ]; then
    json="$(printf '{"tool_name":"%s","tool_input":{"file_path":"%s"},"cwd":"%s","session_id":"%s"}' "$tool" "$fp" "$cwd" "$sid")"
  else
    json="$(printf '{"tool_name":"%s","tool_input":{"file_path":"%s"},"cwd":"%s"}' "$tool" "$fp" "$cwd")"
  fi
  printf '%s' "$json" | "$PYBIN" "$GATE" >/dev/null 2>&1; echo $?
}
run_gate_commit(){ # cwd_win sid
  have_gate || { echo skip; return; }
  printf '{"tool_name":"Bash","tool_input":{"command":"git commit -m x"},"cwd":"%s","session_id":"%s"}' "$1" "$2" \
    | "$PYBIN" "$GATE" >/dev/null 2>&1; echo $?
}
gate_check(){ r="$1"; if [ "$r" = "skip" ]; then echo "  ⤼ gate.py ausente — '$2' omitido"; else check "gate.py: $2" "$3" "$r"; fi; }

echo "== Grupo 0: opt-in (repo NO adoptado, sin session_id) =="
hook_check "no adoptado permite código"        "$PLAIN" 0 src/app.c
gate_check "$(run_gate src/app.c "$WPLAIN" "")" "no adoptado sin sid permite" 0

echo "== Grupo A: repos adoptados — exigir TARGET =="
ledger '### main — 2026-06-20\n- STATUS: ACTIVE\n- Tier: completo\n- Fecha: 2026-06-20\n- TARGET: paas:miproyecto/api@dev\n'
hook_check "ACTIVE+Tier+Fecha+TARGET permite"  "$ADOPTED" 0 src/app.c
gate_check "$(run_gate src/app.c "$WADOPTED" "")" "ACTIVE+TARGET permite" 0

ledger '### main — 2026-06-20\n- STATUS: ACTIVE\n- Tier: completo\n- Fecha: 2026-06-20\n'
hook_check "ACTIVE sin TARGET bloquea"         "$ADOPTED" 2 src/app.c
gate_check "$(run_gate src/app.c "$WADOPTED" "")" "ACTIVE sin TARGET bloquea" 2

ledger '### main — 2026-06-20\n- STATUS: ACTIVE\n- Tier: completo\n- Fecha: 2026-06-20\n- TARGET:\n'
hook_check "TARGET vacío bloquea"              "$ADOPTED" 2 src/app.c
gate_check "$(run_gate src/app.c "$WADOPTED" "")" "TARGET vacío bloquea" 2

ledger '### main — 2026-06-20\n- STATUS: ACTIVE\n- Tier: completo\n- Fecha: 2026-06-20\n- TARGET: <...>\n'
hook_check "TARGET placeholder bloquea"        "$ADOPTED" 2 src/app.c
gate_check "$(run_gate src/app.c "$WADOPTED" "")" "TARGET placeholder bloquea" 2

# PARIDAD: placeholders en MAYÚSCULA deben tratarse IGUAL en ambos guardianes
# (regresión cazada por el Verificador: enforcer.sh era case-sensitive y permitía 'TBD').
ledger '### main — 2026-06-20\n- STATUS: ACTIVE\n- Tier: completo\n- Fecha: 2026-06-20\n- TARGET: TBD\n'
hook_check "TARGET 'TBD' (mayúsc) bloquea — paridad" "$ADOPTED" 2 src/app.c
gate_check "$(run_gate src/app.c "$WADOPTED" "")"    "TARGET 'TBD' (mayúsc) bloquea — paridad" 2

ledger '### main — 2026-06-20\n- STATUS: ACTIVE\n- Tier: completo\n- Fecha: 2026-06-20\n- TARGET: Pendiente\n'
hook_check "TARGET 'Pendiente' (mayúsc) bloquea — paridad" "$ADOPTED" 2 src/app.c
gate_check "$(run_gate src/app.c "$WADOPTED" "")"         "TARGET 'Pendiente' (mayúsc) bloquea — paridad" 2

ledger '### main — 2026-06-20\n- STATUS: ACTIVE\n- Tier: fast-path\n- Fecha: 2026-06-20\n- TARGET: docker-local\n'
gate_check "$(run_gate src/app.c "$WADOPTED" "")" "TARGET docker-local permite" 0

ledger '### main — 2026-06-20\n- STATUS: ACTIVE\n- Tier: fast-path\n- Fecha: 2026-06-20\n- TARGET: algo-raro-pero-presente\n'
gate_check "$(run_gate src/app.c "$WADOPTED" "")" "TARGET no-esquema pero presente permite (presencia, no esquema)" 0

ledger '### main — 2026-06-20\n- STATUS: ACTIVE\n'
hook_check "ACTIVE sin campos mínimos bloquea" "$ADOPTED" 2 src/app.c
gate_check "$(run_gate src/app.c "$WADOPTED" "")" "ACTIVE sin Tier/Fecha/TARGET bloquea" 2

ledger '### main — 2026-06-20\n- STATUS: CLOSED\n- Tier: fast-path\n- Fecha: 2026-06-20\n- TARGET: pc-local\n'
hook_check "CLOSED bloquea"                    "$ADOPTED" 2 src/app.c
gate_check "$(run_gate src/app.c "$WADOPTED" "")" "CLOSED bloquea" 2

ledger '### otra-rama — 2026-06-20\n- STATUS: ACTIVE\n- Tier: fast-path\n- Fecha: 2026-06-20\n- TARGET: pc-local\n'
gate_check "$(run_gate src/app.c "$WADOPTED" "")" "ACTIVE de otro branch bloquea" 2

ledger '## RUN 2026-06-20\nSTATUS: ACTIVE\nBranch: main\n'
gate_check "$(run_gate src/app.c "$WADOPTED" "")" "legado ## RUN ACTIVE sin TARGET permite (retro-compat)" 0

echo "== Grupo A: exentos en repo adoptado =="
gate_check "$(run_gate docs/x.md "$WADOPTED" "")" "docs/*.md exento" 0
gate_check "$(run_gate README.md "$WADOPTED" "")" "README.md exento" 0

echo "== Grupo A: git commit en adoptado =="
ledger '### main — 2026-06-20\n- STATUS: ACTIVE\n- Tier: completo\n- Fecha: 2026-06-20\n- TARGET: pc-local\n'
( cd "$ADOPTED" && echo 'x=1' > a.py && git add a.py )
gate_check "$(run_gate_commit "$WADOPTED" "")" "commit staged .py + ACTIVE con TARGET permite" 0
ledger '### main — 2026-06-20\n- STATUS: ACTIVE\n- Tier: completo\n- Fecha: 2026-06-20\n'
gate_check "$(run_gate_commit "$WADOPTED" "")" "commit staged .py + ACTIVE sin TARGET bloquea" 2
( cd "$ADOPTED" && git reset -q a.py && echo '# doc' > b.md && git add b.md )
gate_check "$(run_gate_commit "$WADOPTED" "")" "commit staged solo .md permite" 0

echo "== Grupo B: piso TARGET (repo NO adoptado) =="
SIDA="sess-AAAA"; SIDB="sess-BBBB"
rm -rf "$CACHE"/*  2>/dev/null || true
gate_check "$(run_gate foo.js "$WPLAIN" "$SIDA")" "1ra edición sin marcador bloquea (msg B)" 2
gate_check "$(run_gate foo.js "$WPLAIN" "$SIDA")" "2da edición misma sesión permite (marcador escrito)" 0
gate_check "$(run_gate bar.py "$WPLAIN" "$SIDA")" "otro archivo misma sesión permite (marcador por repo+sesión)" 0
gate_check "$(run_gate foo.js "$WPLAIN" "$SIDB")" "marcador de OTRA sesión re-pregunta (bloquea)" 2
rm -rf "$CACHE"/*  2>/dev/null || true
gate_check "$(run_gate docs/x.md "$WPLAIN" "$SIDA")" "docs/.md en no-adoptado nunca pisa (exento)" 0
gate_check "$(run_gate_commit "$WPLAIN" "$SIDA")"    "git commit en no-adoptado pasa libre (FO-15)" 0

echo "== Grupo B: CLI --register-target desbloquea =="
rm -rf "$CACHE"/*  2>/dev/null || true
"$PYBIN" "$GATE" --register-target "paas:foo/bar@dev" --session "$SIDA" --repo "$WPLAIN" >/dev/null 2>&1
gate_check "$(run_gate foo.js "$WPLAIN" "$SIDA")" "tras --register-target, edición permite sin bloquear" 0

echo "== Grupo C: FAIL-OPEN =="
rm -rf "$CACHE"/*  2>/dev/null || true
gate_check "$(run_gate foo.js "$WPLAIN" "")" "no-adoptado SIN session_id permite (FO-11)" 0
# cache no escribible: apuntar el cache a un subdir de un ARCHIVO -> mkdir falla
touch "$TMP/notadir"
( export CRISOL_TARGET_CACHE_DIR="$(wpath "$TMP/notadir")/sub"
  r1="$(run_gate foo.js "$WPLAIN" "sess-CCCC")"; r2="$(run_gate foo.js "$WPLAIN" "sess-CCCC")"
  if [ "$r1" = "0" ] && [ "$r2" = "0" ]; then echo "  ✅ gate.py: cache no escribible permite (FO-14, repetible)";
  else echo "  ❌ gate.py: cache no escribible (esperaba 0/0, obtuvo $r1/$r2)"; fi )
gate_check "$(run_gate loose.py "$(wpath "$TMP")" "sess-DDDD")" "archivo fuera de repo git permite (FO-5)" 0
printf '{"tool_name":"Read","tool_input":{"file_path":"x.py"},"cwd":"%s","session_id":"s"}' "$WPLAIN" | "$PYBIN" "$GATE" >/dev/null 2>&1
gate_check "$?" "tool Read (no Edit/Write/Bash) permite (FO-1)" 0
printf '{"tool_name":"Bash","tool_input":{"command":"npm test"},"cwd":"%s","session_id":"s"}' "$WPLAIN" | "$PYBIN" "$GATE" >/dev/null 2>&1
gate_check "$?" "Bash que no es git commit permite (FO-3)" 0
printf 'no-json-roto' | "$PYBIN" "$GATE" >/dev/null 2>&1
gate_check "$?" "stdin roto permite (FO-4)" 0

echo
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
