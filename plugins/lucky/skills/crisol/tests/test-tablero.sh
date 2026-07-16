#!/usr/bin/env bash
# test-tablero — la bandeja del operador (ADR 0019 §3): semántica de secciones.
set -uo pipefail

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$TESTS_DIR/../../../../.." && pwd)"
PROYECTAR="${PROYECTAR_OVERRIDE:-$REPO_ROOT/scripts/proyectar.py}"
PYBIN="$(command -v python || command -v python3 || echo python)"
"$PYBIN" -c "import yaml" 2>/dev/null || { echo "XX falta PyYAML"; exit 1; }

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
SB="$TMP/sb"
TOY="$SB/plugins/lucky/skills/toy"
mkdir -p "$TOY/ramas" "$SB/docs/refactor/_crisol/runs" "$SB/docs/decisions"

PASS=0; FAIL=0
ok(){ if [ "$2" -eq "$3" ] 2>/dev/null; then PASS=$((PASS+1)); echo "  ✅ $1"
      else FAIL=$((FAIL+1)); echo "  ❌ $1 (esperado $2, obtuvo $3)"; fi; }
has(){ grep -qF "$2" "$SB/docs/TABLERO.md"; echo $?; }

fila_run(){ cat > "$SB/docs/refactor/_crisol/runs/$1.md" <<EOF
---
id: $1
schema: corrida/1
tipo: corrida
estado: $2
creado: 2026-01-01
branch: main
titulo: "corrida $1"
tier: "fast-path"
target: "docker-local"
runState: wip
veredictos: []
---
- Alcance: fixture
EOF
}
printf -- '---\nname: toy\n---\n# Toy\n\n<!-- RAMAS:BEGIN (generado por scripts/proyectar.py — propuesta = cuarentena, no rutea; ADR 0018) -->\n<!-- RAMAS:END -->\n' > "$TOY/SKILL.md"
cat > "$TOY/ramas/001-cuarentena.md" <<'EOF'
---
id: 001-cuarentena
schema: rama/1
tipo: rama
estado: LIVE
canal: propuesta
creado: 2026-01-01
skill: toy
gatillo: "gatillo de prueba"
refs: []
---
x
EOF
cat > "$TOY/ramas/002-en-duda.md" <<'EOF'
---
id: 002-en-duda
schema: rama/1
tipo: rama
estado: EN_DUDA
canal: estable
creado: 2026-01-01
skill: toy
gatillo: "gatillo dudoso"
refs: []
---
x
EOF
cat > "$SB/docs/decisions/0099-pendiente.md" <<'EOF'
---
id: adr:0099
schema: decision/1
tipo: decision
estado: PROPUESTA
creado: 2026-01-01
refs: []
---
# 0099 — decisión de prueba
EOF
fila_run "2026-01-01-abierta" "ACTIVE"
fila_run "2026-01-02-cerrada" "CLOSED"

echo "— TABLERO (ADR 0019) —"
ok "T1 proyectar exit 0" 0 "$("$PYBIN" "$PROYECTAR" --repo "$SB" >/dev/null 2>&1; echo $?)"
ok "T2 marcador GENERADO en línea 1" 0 "$(head -1 "$SB/docs/TABLERO.md" | grep -qF "GENERADO por scripts/proyectar.py"; echo $?)"
ok "T3 corrida ACTIVE listada" 0 "$(has x "corrida:2026-01-01-abierta")"
ok "T4 corrida CLOSED NO listada" 1 "$(has x "corrida:2026-01-02-cerrada")"
ok "T5 decisión PROPUESTA en la bandeja" 0 "$(has x "decision:adr:0099")"
ok "T6 rama propuesta en CUARENTENA" 0 "$(has x "rama:toy/001-cuarentena")"
ok "T7 rama EN_DUDA en frescura" 0 "$(has x "rama:toy/002-en-duda")"
ok "T8 cuarentena NO rutea al tronco (cross-check)" 1 "$(grep -qF "001-cuarentena.md" "$TOY/SKILL.md"; echo $?)"
ok "T9 idempotencia (--check sin drift)" 0 "$("$PYBIN" "$PROYECTAR" --repo "$SB" --check >/dev/null 2>&1; echo $?)"

echo; echo "TABLERO: $PASS pass, $FAIL fail"
[ "$FAIL" -eq 0 ]
