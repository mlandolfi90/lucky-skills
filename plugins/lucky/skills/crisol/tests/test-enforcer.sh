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

# matriz: escribe en el RUN-LEDGER de juguete una entrada ACTIVE válida (TARGET real)
# + un bloque VEREDICTOS parametrizable. $1 = runState (wip|closing|""=sin bloque),
# $2 = cuerpo de las líneas [V] (con \n entre líneas; ""=sin líneas [V]).
# El cuerpo se inserta tal cual; cada caso D arma sus líneas `- [V] <ID> · <V> · <q> · <e>`.
matriz(){
  local rs="$1" body="$2" header lines=""
  header='### main — 2026-06-21\n- STATUS: ACTIVE\n- Tier: completo\n- Fecha: 2026-06-21\n- TARGET: docker-local\n'
  if [ -n "$rs" ]; then
    lines='<!-- VEREDICTOS:BEGIN -->\n- runState: '"$rs"'\n'
    [ -n "$body" ] && lines="$lines$body"'\n'
    lines="$lines"'<!-- VEREDICTOS:END -->\n'
  fi
  printf '%b' "$header$lines" > "$ADOPTED/docs/refactor/_crisol/RUN-LEDGER.md"
}

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

# check de igualdad de STRINGS (para la paridad de listas, no exit codes)
check_eq(){ if [ "$2" = "$3" ]; then PASS=$((PASS+1)); echo "  ✅ $1"
            else FAIL=$((FAIL+1)); echo "  ❌ $1 (gate=[$2] enforcer=[$3])"; fi; }

# Paridad de la política de código: extrae CODE_EXTS/CODE_FILENAMES de AMBOS guardianes
# y normaliza (sin punto inicial, sin vacíos, ordenado) para comparar como texto.
norm_list(){ tr ' ' '\n' | sed 's/^\.//' | grep -v '^$' | LC_ALL=C sort | tr '\n' ' '; }
gate_policy(){  # 2 líneas: exts / filenames. Importa el módulo (NO corre main: __name__!='__main__').
  "$PYBIN" - "$GATE" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("crisol_gate_probe", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(" ".join(sorted(m._CODE_EXTS)))
print(" ".join(sorted(m._CODE_FILENAMES)))
PY
}
enf_policy(){ bash "$HOOK" --print-code-policy; }  # 2 líneas: exts / filenames

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

echo "== Grupo D: gate de cobertura (matriz de veredictos en el commit de cierre) =="
# Código staged en el repo adoptado para TODOS los casos D (commit con .py).
( cd "$ADOPTED" && git reset -q . >/dev/null 2>&1; echo 'x=1' > a.py && git add a.py )

# D1: closing + todas PASS -> cierra (exit 0)
matriz closing '- [V] REGLA0 · PASS · gate · tests/test-enforcer.sh:N/N\n- [V] OPEN_CLOSED · PASS · open_closed-verifier · gate.py:1 (AGREGAR)'
gate_check "$(run_gate_commit "$WADOPTED" "")" "D1 closing + todas PASS cierra" 0

# D2: closing + bloque VEREDICTOS ausente/vacío -> bloquea (agujero central + cond 4iii)
matriz closing ''
gate_check "$(run_gate_commit "$WADOPTED" "")" "D2 closing + matriz vacía bloquea" 2

# D3: closing + una línea PENDIENTE -> bloquea
matriz closing '- [V] REGLA0 · PASS · gate · ok\n- [V] TARGET · PENDIENTE · gate · -'
gate_check "$(run_gate_commit "$WADOPTED" "")" "D3 closing + PENDIENTE bloquea" 2

# D4: closing + una FAIL -> bloquea
matriz closing '- [V] REGLA0 · PASS · gate · ok\n- [V] OPEN_CLOSED · FAIL · open_closed-verifier · viola OCP'
gate_check "$(run_gate_commit "$WADOPTED" "")" "D4 closing + FAIL bloquea" 2

# D5: closing + fail/Fail (variante de mayúsculas) -> bloquea (borde de paridad, v1.11.0)
matriz closing '- [V] REGLA0 · fail · gate · x\n- [V] TARGET · Fail · gate · y'
gate_check "$(run_gate_commit "$WADOPTED" "")" "D5 closing + fail/Fail (mayúsc) bloquea" 2

# D6: closing + PASS/pass/N/A mezclados, todas green -> cierra (case-insensitive)
matriz closing '- [V] REGLA0 · PASS · gate · a\n- [V] TARGET · pass · gate · b\n- [V] CONFORMIDAD · N/A · conformidad-verifier · no aplica'
gate_check "$(run_gate_commit "$WADOPTED" "")" "D6 closing + PASS/pass/N/A todas green cierra" 0

# D7: wip + matriz incompleta (PENDIENTE) + código staged -> pasa (WIP-commit no se rompe)
matriz wip '- [V] REGLA0 · PASS · gate · a\n- [V] TARGET · PENDIENTE · gate · -'
gate_check "$(run_gate_commit "$WADOPTED" "")" "D7 wip + matriz incompleta permite" 0

# D8: closing + mezcla con un N/A (no aplicable) y resto PASS -> cierra
matriz closing '- [V] REGLA0 · PASS · gate · a\n- [V] MIGRATION · N/A · gate · sin DDL\n- [V] ZERO_LEAK · PASS · zero_leak-verifier · 0/0/0'
gate_check "$(run_gate_commit "$WADOPTED" "")" "D8 closing + N/A + PASS cierra" 0

# D9: commit solo-docs (.md) con matriz incompleta -> pasa (no hay código staged; FO existente)
matriz closing '- [V] REGLA0 · PENDIENTE · gate · -'
( cd "$ADOPTED" && git reset -q . >/dev/null 2>&1; echo '# d' > c.md && git add c.md )
gate_check "$(run_gate_commit "$WADOPTED" "")" "D9 solo-docs + matriz incompleta permite (sin código staged)" 0
( cd "$ADOPTED" && git reset -q . >/dev/null 2>&1; echo 'x=1' > a.py && git add a.py )

# D10: repo NO adoptado, código staged -> pasa (FO-15, regresión del piso B)
( cd "$PLAIN" && echo 'y=1' > z.py && git add z.py )
gate_check "$(run_gate_commit "$WPLAIN" "sess-D10")" "D10 no-adoptado + código staged permite (FO-15)" 0
( cd "$PLAIN" && git reset -q . >/dev/null 2>&1 )

# D11: closing + matriz completa+verde PERO ledger sin TARGET -> bloquea (cambio A muerde ANTES)
printf '%b' '### main — 2026-06-21\n- STATUS: ACTIVE\n- Tier: completo\n- Fecha: 2026-06-21\n<!-- VEREDICTOS:BEGIN -->\n- runState: closing\n- [V] REGLA0 · PASS · gate · ok\n<!-- VEREDICTOS:END -->\n' > "$ADOPTED/docs/refactor/_crisol/RUN-LEDGER.md"
gate_check "$(run_gate_commit "$WADOPTED" "")" "D11 closing+verde pero SIN TARGET bloquea (A muerde antes)" 2

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

echo "== Grupo E: paridad de listas de código (gate <-> enforcer, condición Steward c5) =="
if have_gate; then
  GP="$(gate_policy)"; EP="$(enf_policy)"
  G_EXTS="$(printf '%s\n' "$GP" | sed -n 1p | norm_list)"
  G_FN="$( printf '%s\n' "$GP" | sed -n 2p | norm_list)"
  E_EXTS="$(printf '%s\n' "$EP" | sed -n 1p | norm_list)"
  E_FN="$( printf '%s\n' "$EP" | sed -n 2p | norm_list)"
  check_eq "paridad _CODE_EXTS idénticas gate==enforcer"      "$G_EXTS" "$E_EXTS"
  check_eq "paridad _CODE_FILENAMES idénticas gate==enforcer" "$G_FN"   "$E_FN"
else
  echo "  ⤼ gate.py ausente — paridad de listas omitida"
fi

echo "== Grupo F: branch match EXACTO (== , no substring) =="
# F1: branch 'main' + entrada '### main-hotfix' ACTIVE -> BLOQUEA. Era false-PASS del
# enforcer (awk 'entry ~ b' = substring); el gate ya matcheaba exacto.
ledger '### main-hotfix — 2026-06-20\n- STATUS: ACTIVE\n- Tier: completo\n- Fecha: 2026-06-20\n- TARGET: docker-local\n'
hook_check "F1 main + '### main-hotfix' ACTIVE BLOQUEA (mata el false-PASS)" "$ADOPTED" 2 src/app.c
gate_check "$(run_gate src/app.c "$WADOPTED" "")" "F1 main + '### main-hotfix' ACTIVE bloquea" 2

# F2: branch 'main' + entrada '### main' ACTIVE -> permite.
ledger '### main — 2026-06-20\n- STATUS: ACTIVE\n- Tier: completo\n- Fecha: 2026-06-20\n- TARGET: docker-local\n'
hook_check "F2 main + '### main' ACTIVE permite" "$ADOPTED" 0 src/app.c
gate_check "$(run_gate src/app.c "$WADOPTED" "")" "F2 main + '### main' ACTIVE permite" 0

# F2b: 'INACTIVE' ya no cuenta como 'ACTIVE' (STATUS exacto, no substring /ACTIVE/).
ledger '### main — 2026-06-20\n- STATUS: INACTIVE\n- Tier: completo\n- Fecha: 2026-06-20\n- TARGET: docker-local\n'
hook_check "F2b STATUS 'INACTIVE' NO cuenta como ACTIVE (bloquea)" "$ADOPTED" 2 src/app.c
gate_check "$(run_gate src/app.c "$WADOPTED" "")" "F2b STATUS 'INACTIVE' bloquea (match exacto)" 2

echo "== Grupo G: allow-list de código unificada (no-código pasa; código bloquea) =="
# Ledger SIN entrada ACTIVE válida para 'main' (CLOSED): sólo el código debe bloquear.
ledger '### main — 2026-06-20\n- STATUS: CLOSED\n- Tier: completo\n- Fecha: 2026-06-20\n- TARGET: docker-local\n'
# G3: no-código sin ACTIVE -> AMBOS permiten (config/dotfile/binario exento por allow-list).
hook_check "G3a .json sin ACTIVE permite (no es código)"      "$ADOPTED" 0 config.json
gate_check "$(run_gate config.json "$WADOPTED" "")" "G3a .json sin ACTIVE permite" 0
hook_check "G3b .gitignore sin ACTIVE permite (no es código)" "$ADOPTED" 0 .gitignore
gate_check "$(run_gate .gitignore "$WADOPTED" "")" "G3b .gitignore sin ACTIVE permite" 0
hook_check "G3c LICENSE sin ACTIVE permite (no es código)"    "$ADOPTED" 0 LICENSE
gate_check "$(run_gate LICENSE "$WADOPTED" "")" "G3c LICENSE sin ACTIVE permite" 0
hook_check "G3d .png sin ACTIVE permite (no es código)"       "$ADOPTED" 0 assets/logo.png
gate_check "$(run_gate assets/logo.png "$WADOPTED" "")" "G3d .png sin ACTIVE permite" 0
# G4: código (.py) sin ACTIVE -> AMBOS bloquean.
hook_check "G4 .py sin ACTIVE BLOQUEA (es código)"            "$ADOPTED" 2 x.py
gate_check "$(run_gate x.py "$WADOPTED" "")" "G4 .py sin ACTIVE bloquea" 2

echo "== Grupo H: robustez stdin utf-8 del gate (cambio b) =="
# JSON con ruta no-ASCII (acentos): el gate reconfigura stdin utf-8/replace y no rompe
# el decode; .md exento -> permite (en Windows un stdin crudo no-ASCII lo dejaba inerte).
if have_gate; then
  printf '{"tool_name":"Edit","tool_input":{"file_path":"docs/diseño-café.md"},"cwd":"%s","session_id":"s"}' "$WADOPTED" \
    | "$PYBIN" "$GATE" >/dev/null 2>&1
  gate_check "$?" "stdin no-ASCII (.md exento) permite sin romper decode" 0
else
  echo "  ⤼ gate.py ausente — robustez stdin omitida"
fi

echo "== Grupo I: aviso ATOMICIDAD (citación NO bloqueante, paridad gate<->enforcer) =="
# Captura SOLO la línea de aviso (stderr) de cada guardián. Cambio 3 (v1.28.0).
enf_stderr(){ ( cd "$1" && printf '{"tool_input":{"file_path":"%s"}}' "$2" | bash "$HOOK" 2>&1 1>/dev/null | grep -F '[CRISOL-ATOMICIDAD]' || true ); }
gate_stderr(){ have_gate || { echo ""; return; }  # $1=file_path $2=cwd
  printf '{"tool_name":"Edit","tool_input":{"file_path":"%s"},"cwd":"%s","session_id":"s"}' "$1" "$2" \
    | "$PYBIN" "$GATE" 2>&1 1>/dev/null | grep -F '[CRISOL-ATOMICIDAD]' || true; }
has_adv(){ if [ -n "$2" ]; then PASS=$((PASS+1)); echo "  ✅ $1"; else FAIL=$((FAIL+1)); echo "  ❌ $1 (sin aviso)"; fi; }
no_adv(){  if [ -z "$2" ]; then PASS=$((PASS+1)); echo "  ✅ $1"; else FAIL=$((FAIL+1)); echo "  ❌ $1 (aviso inesperado: $2)"; fi; }

ledger '### main — 2026-06-20\n- STATUS: ACTIVE\n- Tier: completo\n- Fecha: 2026-06-20\n- TARGET: docker-local\n'
( cd "$ADOPTED" && { i=1; while [ $i -le 450 ]; do echo "x=$i"; i=$((i+1)); done > big.py; }
                  { i=1; while [ $i -le 100 ]; do echo "y=$i"; i=$((i+1)); done > small.py; } )
rm -f "$ADOPTED/docs/refactor/_crisol/atomicidad.conf"

# I1: big.py (450 >= 400 default) -> AMBOS avisan, línea byte-idéntica
EI="$(enf_stderr "$ADOPTED" big.py)"
has_adv "I1 enforcer avisa en big.py (450>=400)" "$EI"
case "$EI" in *"450 lineas (umbral 400)"*) PASS=$((PASS+1)); echo "  ✅ I1 aviso cita N=450 y T=400";;
              *) FAIL=$((FAIL+1)); echo "  ❌ I1 aviso no cita 450/400: [$EI]";; esac
if have_gate; then
  GI="$(gate_stderr big.py "$WADOPTED")"
  has_adv "I1 gate avisa en big.py (450>=400)" "$GI"
  check_eq "I1 aviso byte-idéntico gate==enforcer" "$GI" "$EI"
fi

# I2: small.py (100 < 400) -> NINGUNO avisa
no_adv "I2 enforcer NO avisa en small.py (100<400)" "$(enf_stderr "$ADOPTED" small.py)"
have_gate && no_adv "I2 gate NO avisa en small.py" "$(gate_stderr small.py "$WADOPTED")"

# I3: conf=50 -> small.py (100>=50) ahora avisa en AMBOS (config chat-ajustable)
printf '50\n' > "$ADOPTED/docs/refactor/_crisol/atomicidad.conf"
has_adv "I3 enforcer avisa en small.py con conf=50" "$(enf_stderr "$ADOPTED" small.py)"
have_gate && has_adv "I3 gate avisa en small.py con conf=50" "$(gate_stderr small.py "$WADOPTED")"
rm -f "$ADOPTED/docs/refactor/_crisol/atomicidad.conf"

# I4: env CRISOL_ATOMICIDAD_T=9999 gana sobre el default -> big.py NO avisa en AMBOS
EI4="$( export CRISOL_ATOMICIDAD_T=9999; enf_stderr "$ADOPTED" big.py )"
no_adv "I4 enforcer respeta env T=9999 (no avisa big.py)" "$EI4"
if have_gate; then GI4="$( export CRISOL_ATOMICIDAD_T=9999; gate_stderr big.py "$WADOPTED" )"
  no_adv "I4 gate respeta env T=9999 (no avisa big.py)" "$GI4"; fi

echo
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
