#!/usr/bin/env bash
# test-lint — fixture de bitacora-lint.sh. Determinista (no depende del reloj).
# REGLA 0: el Verificador lo corre ÉL MISMO en el TARGET.
# Verde ⟺ exit 0 + "N/N PASS". Cualquier assert roja → exit 1.
set -uo pipefail
export LC_ALL=C

HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$HERE/../scripts/bitacora-lint.sh"

pass=0; fail=0
OUT=""
has(){   if printf '%s' "$OUT" | grep -qF "$1"; then pass=$((pass+1)); else fail=$((fail+1)); echo "  FAIL: falta   → '$1'"; fi; }
hasnt(){ if printf '%s' "$OUT" | grep -qF "$1"; then fail=$((fail+1)); echo "  FAIL: sobra   → '$1'"; else pass=$((pass+1)); fi; }
eq(){    if [ "$1" = "$2" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "  FAIL: $3 (esperado '$2', fue '$1')"; fi; }

# Entrada VÁLIDA completa: mkentry <dir> <ID> <fecha> <usos> <estado>
mkentry(){
  cat > "$1/entries/$2.md" <<EOF
## [$2] síntoma de prueba de $2
- **TIPO:** GAP
- **SÍNTOMA (lo observable, NO la causa):** algo observable
- **CAUSA-RAÍZ (1 línea):** porque sí
- **ACCIÓN (pasos, máx 7):**
  1. paso único
- **ANTI-ACCIÓN (el camino muerto — evita re-derivar):** no hagas eso
- **PREVENCIÓN:** una regla
- **validated_on:** \`main\` · $3 · \`<sha>\`
- **stale_si:** >90 días
- **origen:** test   ·   **usos:** $4
- **REFS:** —   ·   **NEXT:** —
- **estado:** $5
EOF
}
# Fila de INDEX: mkrow <dir> <ID> <fecha> <usos> <estado>
mkrow(){ printf '| síntoma de %s | GAP | acción | [%s](entries/%s.md) | %s | %s | %s |\n' "$2" "$2" "$2" "$3" "$4" "$5" >> "$1/INDEX.md"; }
mkhdr(){ mkdir -p "$1/entries"; printf '# INDEX de prueba\n\n| SÍNTOMA | TIPO | ACCIÓN | ENTRADA | validated_on | usos | estado |\n|---|---|---|---|---|---|---|\n' > "$1/INDEX.md"; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# ── F1: catálogo COHERENTE → exit 0, 0 incoherencias ────────────────────────────
A="$TMP/a"; mkhdr "$A"
mkentry "$A" GAP-001   2026-07-01 3 LIVE
mkentry "$A" DRIFT-001 2026-07-01 2 CANDIDATE
mkrow   "$A" GAP-001   2026-07-01 3 LIVE
mkrow   "$A" DRIFT-001 2026-07-01 2 CANDIDATE
OUT="$(bash "$SCRIPT" "$A" 2>&1)"; rc=$?
echo "$OUT"; echo "────────"
eq "$rc" "0" "F1 exit coherente"
has  "incoherencias: 0"
has  "el INDEX dice la verdad"

# ── F2: la BATERÍA de mentiras → exit 1, cada una detectada ─────────────────────
B="$TMP/b"; mkhdr "$B"
mkentry "$B" GAP-001   2026-07-01 3 LIVE            # coherente (control)
mkentry "$B" HUER-001  2026-07-01 1 LIVE            # sin fila → huérfana
mkentry "$B" USOS-001  2026-07-01 5 LIVE            # usos desespejado (INDEX dice 2)
mkentry "$B" EST-001   2026-07-01 1 CANDIDATE       # estado desespejado (INDEX dice LIVE)
mkentry "$B" FECH-001  2026-07-01 1 LIVE            # fecha desespejada (INDEX dice 2026-01-01)
mkentry "$B" ILEG-001  2026-07-01 1 APROBADA        # estado ilegal
mkentry "$B" TIT-001   2026-07-01 1 LIVE            # título ≠ ID (lo rompemos abajo)
sed -i '1s/.*/## [OTRO-999] título que miente/' "$B/entries/TIT-001.md"
mkentry "$B" CAMPO-001 2026-07-01 1 LIVE            # sin ANTI-ACCIÓN (lo borramos abajo)
sed -i '/ANTI-ACCIÓN/d' "$B/entries/CAMPO-001.md"
mkentry "$B" GORDA-001 2026-07-01 1 LIVE            # >35 líneas
for i in $(seq 1 30); do echo "  relleno $i" >> "$B/entries/GORDA-001.md"; done
mkrow "$B" GAP-001   2026-07-01 3 LIVE
mkrow "$B" USOS-001  2026-07-01 2 LIVE
mkrow "$B" EST-001   2026-07-01 1 LIVE
mkrow "$B" FECH-001  2026-01-01 1 LIVE
mkrow "$B" ILEG-001  2026-07-01 1 APROBADA
mkrow "$B" TIT-001   2026-07-01 1 LIVE
mkrow "$B" CAMPO-001 2026-07-01 1 LIVE
mkrow "$B" GORDA-001 2026-07-01 1 LIVE
mkrow "$B" FANT-001  2026-07-01 1 LIVE              # fila sin archivo → fantasma
mkrow "$B" GAP-001   2026-07-01 3 LIVE              # 2da fila del mismo ID → duplicada
OUT="$(bash "$SCRIPT" "$B" 2>&1)"; rc=$?
echo "$OUT"; echo "────────"
eq "$rc" "1" "F2 exit fail-closed"
has  "HUER-001 · HUÉRFANA"
has  "USOS-001 · USOS desespejado: entrada='5' vs INDEX='2'"
has  "EST-001 · ESTADO desespejado: entrada='CANDIDATE' vs INDEX='LIVE'"
has  "FECH-001 · FECHA desespejada: entrada='2026-07-01' vs INDEX='2026-01-01'"
has  "ILEG-001 · ESTADO ilegal"
has  "OTRO-999" # el título miente → se reporta contra el ID del archivo
has  "TIT-001 · TÍTULO"
has  "CAMPO-001 · CAMPO faltante: ANTI-ACCIÓN"
has  "GORDA-001 · TAMAÑO"
has  "FANT-001 · FANTASMA"
has  "GAP-001 · DUPLICADA: 2 filas"
hasnt "GAP-001 · HUÉRFANA"   # el control coherente no genera falsos positivos de bijección

# ── F3: ORDEN roto (usos asc) → detectado ────────────────────────────────────────
C="$TMP/c"; mkhdr "$C"
mkentry "$C" UNO-001 2026-07-01 1 LIVE
mkentry "$C" DOS-001 2026-07-01 4 LIVE
mkrow   "$C" UNO-001 2026-07-01 1 LIVE
mkrow   "$C" DOS-001 2026-07-01 4 LIVE              # 4 abajo de 1 → orden roto
OUT="$(bash "$SCRIPT" "$C" 2>&1)"; rc=$?
echo "$OUT"; echo "────────"
eq "$rc" "1" "F3 exit orden"
has  "DOS-001 · ORDEN: usos=4 arriba de usos=1"

# ── F4: ausencia total → fail-soft; catálogo a MEDIAS → fail-closed ─────────────
OUT="$(bash "$SCRIPT" "$TMP/inexistente" 2>&1)"; rc=$?
eq "$rc" "0" "F4a ausencia total exit 0"
has "N/D — sin bitácora"
D="$TMP/d"; mkdir -p "$D/entries"; mkentry "$D" SOLO-001 2026-07-01 1 LIVE   # entries sin INDEX
OUT="$(bash "$SCRIPT" "$D" 2>&1)"; rc=$?
eq "$rc" "1" "F4b catálogo a medias exit 1"
has "falta INDEX.md pero entries/ existe"

# ── F5: DOGFOOD — la bitácora REAL del repo debe pasar el lint ───────────────────
OUT="$(bash "$SCRIPT" "$HERE/.." 2>&1)"; rc=$?
echo "$OUT"; echo "────────"
eq "$rc" "0" "F5 la bitácora real es coherente"
has "el INDEX dice la verdad"

echo "────────"
echo "RESULTADO: $pass PASS · $fail FAIL"
[ "$fail" -eq 0 ] || exit 1
exit 0
