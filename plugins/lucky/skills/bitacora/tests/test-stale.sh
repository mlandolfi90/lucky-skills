#!/usr/bin/env bash
# test-stale — fixture de bitacora-stale.sh. Determinista vía --today (no depende
# del reloj). REGLA 0: el Verificador lo corre ÉL MISMO en el TARGET.
# Verde ⟺ exit 0 + "N/N PASS". Cualquier assert roja → exit 1.
set -uo pipefail
export LC_ALL=C

HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$HERE/../scripts/bitacora-stale.sh"
TODAY="2026-09-30"          # referencia fija; umbral default = 90 días

pass=0; fail=0
OUT=""
has(){    if printf '%s' "$OUT" | grep -qF "$1"; then pass=$((pass+1)); else fail=$((fail+1)); echo "  FAIL: falta   → '$1'"; fi; }
hasnt(){  if printf '%s' "$OUT" | grep -qF "$1"; then fail=$((fail+1)); echo "  FAIL: sobra   → '$1'"; else pass=$((pass+1)); fi; }
eq(){     if [ "$1" = "$2" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "  FAIL: $3 (esperado '$2', fue '$1')"; fi; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# ── fixtures (hoy=2026-09-30, umbral=90d) ───────────────────────────────────────
# vigente: 29 días
printf '## [FRESH-001]\n- **validated_on:** `main` · 2026-09-01 · `<sha>`\n- **estado:** LIVE\n'   > "$TMP/FRESH-001.md"
# borde EXACTO 90 días (2026-07-02 → 90d) → vigente (no > 90)
printf '## [BOUND90-001]\n- **validated_on:** `main` · 2026-07-02 · `<sha>`\n- **estado:** LIVE\n'  > "$TMP/BOUND90-001.md"
# borde 91 días (2026-07-01) → STALE
printf '## [BOUND91-001]\n- **validated_on:** `main` · 2026-07-01 · `<sha>`\n- **estado:** LIVE\n'  > "$TMP/BOUND91-001.md"
# vieja: 272 días → STALE
printf '## [OLD-001]\n- **validated_on:** `main` · 2026-01-01 · `<sha>`\n- **estado:** LIVE\n'       > "$TMP/OLD-001.md"
# sin validated_on → nace STALE
printf '## [NODATE-001]\n- **estado:** LIVE\n- (esta entrada no declara validated_on)\n'            > "$TMP/NODATE-001.md"
# jubilada y vieja → NO se reporta (skip)
printf '## [RETIRED-001]\n- **validated_on:** `main` · 2026-01-01 · `<sha>`\n- **estado:** RETIRED\n' > "$TMP/RETIRED-001.md"

# ── correr ──────────────────────────────────────────────────────────────────────
OUT="$(bash "$SCRIPT" --today "$TODAY" "$TMP" 2>&1)"; rc=$?
echo "$OUT"
echo "────────"

# ── asserts ─────────────────────────────────────────────────────────────────────
eq "$rc" "0" "exit fail-soft (siempre 0)"
has   "OLD-001 · STALE"
has   "BOUND91-001 · STALE"
has   "NODATE-001 · STALE · sin validated_on"
hasnt "FRESH-001"            # vigente → no aparece en STALE
hasnt "BOUND90-001"          # borde exacto 90d → vigente
hasnt "RETIRED-001"          # jubilada → no se reporta
has   "Entradas: 6 · vigentes: 2 · STALE: 3"   # total 6, retired skip, 2 live, 3 stale

n=$((pass+fail))
echo "test-stale: $pass/$n PASS"
[ "$fail" -eq 0 ] || { echo "test-stale: ROJO ($fail fallas)"; exit 1; }
exit 0
