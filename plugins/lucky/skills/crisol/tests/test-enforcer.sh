#!/usr/bin/env bash
# test-enforcer — ¿Quién verifica al Verificador?
# Fixture mínimo: repo de juguete + casos binarios contra crisol-enforcer.sh.
# REGLA 0 aplicada al guardián: cada cambio del hook corre este test.
set -uo pipefail

HOOK="$(cd "$(dirname "$0")/.." && pwd)/hooks/crisol-enforcer.sh"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
git init -q -b main 2>/dev/null || { git init -q && git checkout -qb main; }
git -c user.email=t@t -c user.name=t commit -q --allow-empty -m init

PASS=0; FAIL=0
check(){ # desc, expected_exit, actual_exit
  if [ "$2" -eq "$3" ]; then PASS=$((PASS+1)); echo "  ✅ $1"
  else FAIL=$((FAIL+1)); echo "  ❌ $1 (esperado exit $2, obtuvo $3)"; fi
}
run_hook(){ printf '{"tool_input":{"file_path":"%s"}}' "$1" | bash "$HOOK" >/dev/null 2>&1; echo $?; }

# 1. Sin ledger → bloquea código
check "sin ledger bloquea src/app.c"          2 "$(run_hook src/app.c)"
# 2. Markdown/docs exentos siempre
check "docs/x.md exento"                      0 "$(run_hook docs/x.md)"
check "README.md exento"                      0 "$(run_hook README.md)"
# 3. Entrada trucha de 1 línea (sin Tier/Fecha) → bloquea (anti write-your-own-ticket)
mkdir -p docs/refactor/_crisol
printf '### main — 2026-06-11\n- STATUS: ACTIVE\n' > docs/refactor/_crisol/RUN-LEDGER.md
check "ACTIVE sin campos mínimos bloquea"     2 "$(run_hook src/app.c)"
# 4. Entrada mínima completa → permite
printf '### main — 2026-06-11\n- STATUS: ACTIVE\n- Tier: fast-path\n- Fecha: 2026-06-11\n' > docs/refactor/_crisol/RUN-LEDGER.md
check "ACTIVE con campos mínimos permite"     0 "$(run_hook src/app.c)"
# 5. CLOSED → vuelve a bloquear
printf '### main — 2026-06-11\n- STATUS: CLOSED\n- Tier: fast-path\n- Fecha: 2026-06-11\n' > docs/refactor/_crisol/RUN-LEDGER.md
check "CLOSED bloquea"                        2 "$(run_hook src/app.c)"
# 6. ACTIVE de OTRO branch → bloquea en main
printf '### otra-rama — 2026-06-11\n- STATUS: ACTIVE\n- Tier: fast-path\n- Fecha: 2026-06-11\n' > docs/refactor/_crisol/RUN-LEDGER.md
check "ACTIVE de otro branch bloquea"         2 "$(run_hook src/app.c)"

echo
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
