#!/usr/bin/env bash
# test-ramas — el mecanismo de ramas con cuarentena (ADR 0018).
# Prueba proyectar_ramas(): indexado de estables, cuarentena de propuestas,
# marca EN_DUDA, idempotencia byte-a-byte, y fail-closed sin bloque.
set -uo pipefail

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$TESTS_DIR/../../../../.." && pwd)"
PROYECTAR="${PROYECTAR_OVERRIDE:-$REPO_ROOT/scripts/proyectar.py}"
PYBIN="$(command -v python || command -v python3 || echo python)"
"$PYBIN" -c "import yaml" 2>/dev/null || { echo "XX falta PyYAML"; exit 1; }

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
SB="$TMP/sandbox"
TOY="$SB/plugins/lucky/skills/toy"
mkdir -p "$TOY/ramas" "$SB/docs/refactor/_crisol/runs"

PASS=0; FAIL=0
check(){ if [ "$2" -eq "$3" ] 2>/dev/null; then PASS=$((PASS+1)); echo "  ✅ $1"
         else FAIL=$((FAIL+1)); echo "  ❌ $1 (esperado $2, obtuvo $3)"; fi; }
has(){ grep -qF "$2" "$1"; echo $?; }

tronco(){ cat > "$TOY/SKILL.md" <<'EOF'
---
name: toy
---
# Toy

<!-- RAMAS:BEGIN (generado por scripts/proyectar.py — propuesta = cuarentena, no rutea; ADR 0018) -->
<!-- RAMAS:END -->

resto del tronco
EOF
}
rama(){ # $1=nnn-slug $2=estado $3=canal
  cat > "$TOY/ramas/$1.md" <<EOF
---
id: $1
schema: rama/1
tipo: rama
estado: $2
canal: $3
creado: 2026-01-01
skill: toy
gatillo: "gatillo de $1"
refs: []
---
regla de $1
EOF
}
proyectar(){ "$PYBIN" "$PROYECTAR" --repo "$SB" >/dev/null 2>&1; echo $?; }

echo "— RAMAS (ADR 0018) —"

# R1: rama estable LIVE entra al índice
tronco; rama "001-estable" "LIVE" "estable"
check "R1a proyectar exit 0" 0 "$(proyectar)"
check "R1b la rama estable está en el bloque" 0 "$(has "$TOY/SKILL.md" "ramas/001-estable.md")"

# R2: CUARENTENA — propuesta NO rutea
rama "002-propuesta" "LIVE" "propuesta"
proyectar >/dev/null
check "R2 propuesta NO aparece en el bloque (cuarentena)" 1 "$(has "$TOY/SKILL.md" "ramas/002-propuesta.md")"

# R3: promoción propuesta→estable → aparece
rama "002-propuesta" "LIVE" "estable"
proyectar >/dev/null
check "R3 promovida a estable → aparece" 0 "$(has "$TOY/SKILL.md" "ramas/002-propuesta.md")"

# R4: SUPERSEDIDA sale del índice
rama "002-propuesta" "SUPERSEDIDA" "estable"
proyectar >/dev/null
check "R4 supersedida sale del índice" 1 "$(has "$TOY/SKILL.md" "ramas/002-propuesta.md")"

# R5: EN_DUDA rutea con marca de juicio
rama "001-estable" "EN_DUDA" "estable"
proyectar >/dev/null
check "R5 EN_DUDA lleva marca ⚠" 0 "$(has "$TOY/SKILL.md" "⚠EN_DUDA")"

# R6: idempotencia (M6) — re-proyectar es no-op
proyectar >/dev/null
check "R6 --check sin drift" 0 "$("$PYBIN" "$PROYECTAR" --repo "$SB" --check >/dev/null 2>&1; echo $?)"

# R7: fail-closed — ramas sin bloque en el tronco → error
printf -- '---\nname: toy\n---\n# Toy sin bloque\n' > "$TOY/SKILL.md"
check "R7 ramas sin bloque RAMAS → proyectar exit 1" 1 "$(proyectar)"

echo
echo "RAMAS: $PASS pass, $FAIL fail"
[ "$FAIL" -eq 0 ]
