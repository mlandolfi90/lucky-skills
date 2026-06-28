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
has(){   if printf '%s' "$OUT" | grep -qF "$1"; then pass=$((pass+1)); else fail=$((fail+1)); echo "  FAIL: falta   → '$1'"; fi; }
hasnt(){ if printf '%s' "$OUT" | grep -qF "$1"; then fail=$((fail+1)); echo "  FAIL: sobra   → '$1'"; else pass=$((pass+1)); fi; }
eq(){    if [ "$1" = "$2" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "  FAIL: $3 (esperado '$2', fue '$1')"; fi; }

mkentry(){ printf '## [%s]\n- **validated_on:** `%s` · %s · `<sha>`\n- **estado:** %s\n' "$1" "$2" "$3" "$4"; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# ── fixtures principales (hoy=2026-09-30, umbral=90d) ───────────────────────────
mkentry FRESH-001    main 2026-09-01 LIVE      > "$TMP/FRESH-001.md"      # 29d → vigente
mkentry BOUND90-001  main 2026-07-02 LIVE      > "$TMP/BOUND90-001.md"    # 90d exacto → vigente
mkentry BOUND91-001  main 2026-07-01 LIVE      > "$TMP/BOUND91-001.md"    # 91d → STALE
mkentry OLD-001      main 2026-01-01 LIVE      > "$TMP/OLD-001.md"        # 272d → STALE
printf '## [NODATE-001]\n- **estado:** LIVE\n- (sin validated_on)\n'      > "$TMP/NODATE-001.md"   # sin fecha → STALE
mkentry RETIRED-001  main 2026-01-01 RETIRED   > "$TMP/RETIRED-001.md"    # jubilada → skip
mkentry ILEGIBLE-001 main 2026-13-45 LIVE      > "$TMP/ILEGIBLE-001.md"   # fecha inválida → STALE (ilegible)

OUT="$(bash "$SCRIPT" --today "$TODAY" "$TMP" 2>&1)"; rc=$?
echo "$OUT"; echo "────────"

eq "$rc" "0" "exit fail-soft (siempre 0)"
has   "OLD-001 · STALE"
has   "BOUND91-001 · STALE"
has   "NODATE-001 · STALE · sin validated_on"
has   "ILEGIBLE-001 · STALE · validated_on ilegible"   # F6: rama fecha-ilegible
hasnt "FRESH-001"
hasnt "BOUND90-001"
hasnt "RETIRED-001"
has   "Entradas: 7 · vigentes: 2 · STALE: 4"

# ── F2: un branch CON fecha no debe confundir la fecha de validación ────────────
mkentry DATEDBRANCH-001 release-2026-01-01 2026-09-29 LIVE > "$TMP/DATEDBRANCH-001.md"
OUT="$(bash "$SCRIPT" --today "$TODAY" "$TMP" 2>&1)"
hasnt "DATEDBRANCH-001"      # 2026-09-29 es vigente; NO debe tomar 2026-01-01 del branch
rm -f "$TMP/DATEDBRANCH-001.md"

# ── F13: estado en minúscula se respeta (retired → skip) ────────────────────────
LC="$(mktemp -d)"
mkentry LCRET main 2020-01-01 retired > "$LC/LCRET.md"
OUT="$(bash "$SCRIPT" --today "$TODAY" "$LC" 2>&1)"
hasnt "LCRET"               # retired (minúscula) → no se reporta
has   "Entradas: 1 · vigentes: 0 · STALE: 0"
rm -rf "$LC"

# ── F5: directorio inexistente → fail-soft, exit 0 ──────────────────────────────
OUT="$(bash "$SCRIPT" --today "$TODAY" "$TMP/no-existe-xyz" 2>&1)"; rc=$?
eq "$rc" "0" "dir inexistente fail-soft"
has   "N/D — sin directorio"

# ── F0: --umbral no-numérico no rompe (sin 'integer expression') ni traga el dir ─
DZ="$(mktemp -d)"
mkentry Z main 2026-01-01 LIVE > "$DZ/Z.md"   # 272d
OUT="$(bash "$SCRIPT" --today "$TODAY" --umbral xyz "$DZ" 2>&1)"; rc=$?
eq "$rc" "0" "umbral no-numérico fail-soft"
hasnt "integer expression"
has   "umbral=90d"           # cayó al default, no tomó 'xyz'
has   "Z · STALE"            # y escaneó el dir correcto
rm -rf "$DZ"

# ── F1: DST — el MISMO par de fechas da el MISMO veredicto bajo TZ distintos ─────
DST="$(mktemp -d)"
mkentry DSTBORDER main 2026-01-30 LIVE > "$DST/DSTBORDER.md"   # 91d calendario a 2026-05-01, cruza spring-forward
V_UTC="$(TZ=UTC               bash "$SCRIPT" --today 2026-05-01 "$DST" 2>&1 | grep -E 'Entradas:' | head -1)"
V_NY="$( TZ=America/New_York  bash "$SCRIPT" --today 2026-05-01 "$DST" 2>&1 | grep -E 'Entradas:' | head -1)"
eq "$V_UTC" "$V_NY" "veredicto estable entre TZ (anti-DST)"
case "$V_UTC" in *"STALE: 1"*) pass=$((pass+1));; *) fail=$((fail+1)); echo "  FAIL: DST esperaba STALE:1, fue '$V_UTC'";; esac
rm -rf "$DST"

n=$((pass+fail))
echo "test-stale: $pass/$n PASS"
[ "$fail" -eq 0 ] || { echo "test-stale: ROJO ($fail fallas)"; exit 1; }
exit 0
