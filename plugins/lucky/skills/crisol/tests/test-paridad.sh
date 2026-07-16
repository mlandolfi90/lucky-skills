#!/usr/bin/env bash
# test-paridad — el candado de la Fase 1 de la migración árbol/registros (ADR 0016).
#
# El RUN-LEDGER.md pasó de fuente-de-verdad a PROYECCIÓN generada por
# scripts/proyectar.py desde las filas (runs/*.md). Los guardianes NO cambiaron:
# siguen parseando el mismo archivo, mismo formato, mismo path. Esta suite
# prueba que el gate emite el MISMO veredicto sobre:
#   - un ledger legacy escrito a mano  vs  la proyección regenerada desde filas
# y que la proyección respeta los invariantes del sistema de registros:
#   - idempotencia byte-a-byte (M6), puntero _ACTIVE, invariante ≤1 ACTIVE.
#
# El gate bajo prueba se elige con CRISOL_GATE_OVERRIDE (default: el desplegado
# en ~/.claude/hooks). proyectar.py se elige con PROYECTAR_OVERRIDE (default:
# scripts/proyectar.py del repo que contiene esta suite).
set -uo pipefail

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$TESTS_DIR/../../../../.." && pwd)"
GATE="${CRISOL_GATE_OVERRIDE:-$HOME/.claude/hooks/crisol_gate.py}"
PROYECTAR="${PROYECTAR_OVERRIDE:-$REPO_ROOT/scripts/proyectar.py}"
PYBIN="$(command -v python || command -v python3 || echo python)"

[ -f "$GATE" ] || { echo "SKIP: no hay gate en $GATE"; exit 0; }
[ -f "$PROYECTAR" ] || { echo "XX no existe $PROYECTAR"; exit 1; }
"$PYBIN" -c "import yaml" 2>/dev/null || { echo "XX falta PyYAML (lo exige proyectar.py)"; exit 1; }

export CRISOL_GATE_PROFILE=estricto

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
SB="$TMP/sandbox"
mkdir -p "$SB/docs/refactor/_crisol/runs"
( cd "$SB" && { git init -q -b main 2>/dev/null || { git init -q && git checkout -qb main; }; }
  git -C "$SB" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init )

wpath(){ cygpath -m "$1" 2>/dev/null || ( cd "$1" 2>/dev/null && pwd -W ) 2>/dev/null || echo "$1"; }
WSB="$(wpath "$SB")"
LEDGER="$SB/docs/refactor/_crisol/RUN-LEDGER.md"
RUNS="$SB/docs/refactor/_crisol/runs"

PASS=0; FAIL=0
check(){ if [ "$2" -eq "$3" ] 2>/dev/null; then PASS=$((PASS+1)); echo "  ✅ $1"
         else FAIL=$((FAIL+1)); echo "  ❌ $1 (esperado $2, obtuvo $3)"; fi; }

run_gate_edit(){ # exit del gate para Edit de código en la sandbox
  printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/src/foo.py"},"cwd":"%s","session_id":"paridad"}' "$WSB" "$WSB" \
    | "$PYBIN" "$GATE" >/dev/null 2>&1; echo $?
}
run_gate_commit(){ # exit del gate para `git commit` en la sandbox
  printf '{"tool_name":"Bash","tool_input":{"command":"git commit -m x"},"cwd":"%s","session_id":"paridad"}' "$WSB" \
    | "$PYBIN" "$GATE" >/dev/null 2>&1; echo $?
}
proyectar(){ "$PYBIN" "$PROYECTAR" --repo "$SB" >/dev/null 2>&1; echo $?; }

fila(){ # $1=id $2=estado $3=runState $4=veredictos-yaml-inline
  cat > "$RUNS/$1.md" <<EOF
---
id: $1
schema: corrida/1
tipo: corrida
estado: $2
creado: 2026-01-01
branch: main
titulo: "fixture de paridad"
tier: "fast-path"
target: "docker-local"
runState: $3
veredictos: $4
---
- Alcance: fixture de la suite de paridad
EOF
}

echo "— PARIDAD gate legacy ↔ proyección —"

# P1: ledger legacy A MANO con ACTIVE → veredicto de referencia (allow, exit 0)
printf '### main — 2026-01-01\n- STATUS: ACTIVE\n- Tier: fast-path\n- Fecha: 2026-01-01\n- TARGET: docker-local\n' > "$LEDGER"
REF_ACTIVE="$(run_gate_edit)"
check "P1 referencia legacy: ACTIVE a mano permite código (exit 0)" 0 "$REF_ACTIVE"

# P2: MISMO contenido como FILA + proyección → MISMO veredicto que P1
fila "2026-01-01-caso" "ACTIVE" "wip" "[]"
check "P2 proyectar sale limpio" 0 "$(proyectar)"
check "P2 paridad: proyección con ACTIVE = mismo veredicto que legacy" "$REF_ACTIVE" "$(run_gate_edit)"

# P3: fila CLOSED (ninguna ACTIVE) → proyección → gate BLOQUEA (exit 2)
fila "2026-01-01-caso" "CLOSED" "wip" "[]"
proyectar >/dev/null
check "P3 sin ACTIVE en filas → gate bloquea código (exit 2)" 2 "$(run_gate_edit)"

# P4: cierre con matriz ROJA → commit de código bloqueado (cobertura, exit 2)
mkdir -p "$SB/src"; echo "x=1" > "$SB/src/foo.py"; git -C "$SB" add src/foo.py
fila "2026-01-01-caso" "ACTIVE" "closing" "[{regla: REGLA0, veredicto: FAIL, quien: gate, evidencia: fixture}]"
proyectar >/dev/null
check "P4 closing con FAIL en matriz → commit bloqueado (exit 2)" 2 "$(run_gate_commit)"

# P5: cierre con matriz VERDE → commit permitido (exit 0)
fila "2026-01-01-caso" "ACTIVE" "closing" "[{regla: REGLA0, veredicto: PASS, quien: gate, evidencia: fixture}]"
proyectar >/dev/null
check "P5 closing todo verde → commit permitido (exit 0)" 0 "$(run_gate_commit)"

# P6: idempotencia byte-a-byte (M6): proyectar 2 veces → --check sin drift
proyectar >/dev/null
check "P6 re-proyectar es no-op (--check exit 0)" 0 "$("$PYBIN" "$PROYECTAR" --repo "$SB" --check >/dev/null 2>&1; echo $?)"

# P7: puntero _ACTIVE apunta a la corrida abierta (línea 1 = id)
fila "2026-01-01-caso" "ACTIVE" "wip" "[]"
proyectar >/dev/null
GOT_ID="$(head -1 "$SB/docs/refactor/_crisol/_ACTIVE" | tr -d '\r')"
if [ "$GOT_ID" = "2026-01-01-caso" ]; then PASS=$((PASS+1)); echo "  ✅ P7 _ACTIVE apunta a la corrida abierta"
else FAIL=$((FAIL+1)); echo "  ❌ P7 _ACTIVE dice '$GOT_ID'"; fi

# P8: invariante ≤1 ACTIVE — dos filas ACTIVE → proyectar FALLA (exit 1)
fila "2026-01-02-otra" "ACTIVE" "wip" "[]"
check "P8 dos ACTIVE → proyectar aborta (exit 1)" 1 "$(proyectar)"
rm -f "$RUNS/2026-01-02-otra.md"

# P9: el archivo histórico congelado viaja verbatim dentro de la proyección
printf '# RUN-LEDGER — sandbox\n\n### main — 2020-01-01\n- STATUS: CLOSED\n- Tier: fast-path\n- Fecha: 2020-01-01\n- TARGET: docker-local\n' > "$RUNS/_archivo-hasta-2026-07.md"
proyectar >/dev/null
if grep -q "2020-01-01" "$LEDGER" && head -1 "$LEDGER" | grep -q "GENERADO por scripts/proyectar.py"; then
  PASS=$((PASS+1)); echo "  ✅ P9 archivo congelado + marcador GENERADO en la proyección"
else FAIL=$((FAIL+1)); echo "  ❌ P9 proyección sin archivo congelado o sin marcador"; fi

echo
echo "PARIDAD: $PASS pass, $FAIL fail"
[ "$FAIL" -eq 0 ]
