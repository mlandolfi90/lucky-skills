#!/usr/bin/env bash
# test-enforcer — ¿Quién verifica al Verificador?
# Fixture: repo de juguete + casos binarios contra crisol-enforcer.sh (bash) Y
# contra crisol_gate.py (global, si existe) — fuente única de verdad de la
# regla para que los dos guardianes JAMÁS deriven (condición del Steward, c5).
set -uo pipefail

HOOK="$(cd "$(dirname "$0")/.." && pwd)/hooks/crisol-enforcer.sh"
GATE="$HOME/.claude/hooks/crisol_gate.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
git init -q -b main 2>/dev/null || { git init -q && git checkout -qb main; }
git -c user.email=t@t -c user.name=t commit -q --allow-empty -m init

PASS=0; FAIL=0
check(){ # desc, expected, actual
  if [ "$2" -eq "$3" ]; then PASS=$((PASS+1)); echo "  ✅ $1"
  else FAIL=$((FAIL+1)); echo "  ❌ $1 (esperado exit $2, obtuvo $3)"; fi
}
run_hook(){ printf '{"tool_input":{"file_path":"%s"}}' "$1" | bash "$HOOK" >/dev/null 2>&1; echo $?; }
run_hook_me(){ printf '{"tool_name":"MultiEdit","tool_input":{"file_path":"%s","edits":[{"old_string":"a","new_string":"b"}]}}' "$1" | bash "$HOOK" >/dev/null 2>&1; echo $?; }
run_gate(){
  if [ -f "$GATE" ] && command -v python >/dev/null 2>&1; then
    # En Git Bash $PWD es POSIX (/tmp/...) — el Python de Windows necesita C:/...
    WPWD="$(cygpath -m "$PWD" 2>/dev/null || pwd -W 2>/dev/null || echo "$PWD")"
    printf '{"tool_name":"Edit","tool_input":{"file_path":"%s"},"cwd":"%s"}' "$1" "$WPWD" | python "$GATE" >/dev/null 2>&1; echo $?
  else echo skip; fi
}
gate_check(){ r="$(run_gate "$2")"; if [ "$r" = "skip" ]; then echo "  ⤼ gate.py ausente — '$1' omitido"; else check "gate.py: $1" "$3" "$r"; fi }

# 0. OPT-IN: repo SIN docs/refactor/_crisol → ambos guardianes inertes
check "opt-in: repo no adoptado permite src/app.c" 0 "$(run_hook src/app.c)"
gate_check "opt-in: no adoptado permite"            src/app.c 0
# 1. Adoptado (dir existe) pero sin ledger → bloquea
mkdir -p docs/refactor/_crisol
check "adoptado sin ledger bloquea"                 2 "$(run_hook src/app.c)"
# 2. Markdown/docs exentos siempre
check "docs/x.md exento"                            0 "$(run_hook docs/x.md)"
check "README.md exento"                            0 "$(run_hook README.md)"
# 3. Entrada trucha de 1 línea (sin Tier/Fecha) → bloquea (anti ticket-propio)
printf '### main — 2026-06-11\n- STATUS: ACTIVE\n' > docs/refactor/_crisol/RUN-LEDGER.md
check "ACTIVE sin campos mínimos bloquea"           2 "$(run_hook src/app.c)"
gate_check "trucha bloquea"                         src/app.c 2
# 4. Entrada mínima completa → permite
printf '### main — 2026-06-11\n- STATUS: ACTIVE\n- Tier: fast-path\n- Fecha: 2026-06-11\n' > docs/refactor/_crisol/RUN-LEDGER.md
check "ACTIVE con campos mínimos permite"           0 "$(run_hook src/app.c)"
gate_check "mínima permite"                         src/app.c 0
# 5. CLOSED → vuelve a bloquear
printf '### main — 2026-06-11\n- STATUS: CLOSED\n- Tier: fast-path\n- Fecha: 2026-06-11\n' > docs/refactor/_crisol/RUN-LEDGER.md
check "CLOSED bloquea"                              2 "$(run_hook src/app.c)"
gate_check "CLOSED bloquea"                         src/app.c 2
# 6. ACTIVE de OTRO branch → bloquea en main
printf '### otra-rama — 2026-06-11\n- STATUS: ACTIVE\n- Tier: fast-path\n- Fecha: 2026-06-11\n' > docs/refactor/_crisol/RUN-LEDGER.md
check "ACTIVE de otro branch bloquea"               2 "$(run_hook src/app.c)"
# 7. Payload MultiEdit: extrae file_path (con CLOSED debe bloquear = lo parseó)
printf '### main — 2026-06-11\n- STATUS: CLOSED\n- Tier: fast-path\n- Fecha: 2026-06-11\n' > docs/refactor/_crisol/RUN-LEDGER.md
check "MultiEdit con CLOSED bloquea (parseo ok)"    2 "$(run_hook_me src/app.c)"

echo
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
