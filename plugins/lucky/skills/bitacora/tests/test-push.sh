#!/usr/bin/env bash
# test-push — fixture del hook SessionStart bitacora-push.sh (ADR 0010).
# Prueba: inyección top-N LIVE, cap, presupuesto, off-switch, source≠startup,
# INDEX ausente, y el invariante exit 0 SIEMPRE (fail-open de flota).
set -uo pipefail
export LC_ALL=C

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PUSH_SRC="$HERE/../hooks/bitacora-push.sh"

PASS=0; FAIL=0
check(){ if [ "$2" = "$3" ]; then PASS=$((PASS+1)); echo "  ✅ $1"; else FAIL=$((FAIL+1)); echo "  ❌ $1 (esperado '$2', obtuvo '$3')"; fi; }

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/hooks"
cp "$PUSH_SRC" "$TMP/hooks/bitacora-push.sh"
PUSH="$TMP/hooks/bitacora-push.sh"

# INDEX fixture: 3 LIVE + 1 CANDIDATE (la CANDIDATE JAMÁS se inyecta)
cat > "$TMP/INDEX.md" <<'EOF'
# Bitácora — INDEX (fixture)

| SÍNTOMA OBSERVABLE (lo que ves) | TIPO | ACCIÓN (1 línea) | ENTRADA | validated_on | usos | estado |
|---|---|---|---|---|---|---|
| El verde miente en el check obligatorio | FALSO-VERDE | Auditá el CÓDIGO, no el comentario | [DRIFT-001](entries/DRIFT-001.md) | 2026-07-02 | 3 | LIVE |
| El deploy no sale en 10 min | GAP | workflow_dispatch sobre el branch | [GAP-003](entries/GAP-003.md) | 2026-07-03 | 2 | LIVE |
| CSRF invalido tras redeploy | DRIFT | PRG 303 a /login?expired=1 | [DRIFT-002](entries/DRIFT-002.md) | 2026-06-26 | 1 | LIVE |
| Sospecha sin evidencia todavia | GAP | investigar cuando se roce | [GAP-099](entries/GAP-099.md) | 2026-07-09 | 0 | CANDIDATE |
EOF

run_push(){ # $1=json-stdin ; env ya seteado por el caller
  printf '%s' "$1" | bash "$PUSH" 2>/dev/null
}

# ── 1. startup: inyecta las LIVE, con síntoma+acción+id ───────────────────────
OUT="$(run_push '{"source":"startup"}')"
check "startup: emite hookEventName SessionStart" "yes" "$(printf '%s' "$OUT" | grep -q '"hookEventName":"SessionStart"' && echo yes || echo no)"
check "startup: contiene el top-1 (DRIFT-001)" "yes" "$(printf '%s' "$OUT" | grep -q 'DRIFT-001' && echo yes || echo no)"
check "startup: contiene sintoma->accion" "yes" "$(printf '%s' "$OUT" | grep -q 'El verde miente' && echo yes || echo no)"

# ── 2. CANDIDATE jamás se inyecta ─────────────────────────────────────────────
check "CANDIDATE excluida (solo LIVE)" "no" "$(printf '%s' "$OUT" | grep -q 'GAP-099' && echo yes || echo no)"

# ── 3. cap BITACORA_PUSH_MAX=2: entran top-2, queda afuera la 3ra ─────────────
OUT2="$(BITACORA_PUSH_MAX=2 run_push '{"source":"startup"}')"
check "cap=2: entra la 2da (GAP-003)" "yes" "$(printf '%s' "$OUT2" | grep -q 'GAP-003' && echo yes || echo no)"
check "cap=2: NO entra la 3ra (DRIFT-002)" "no" "$(printf '%s' "$OUT2" | grep -q 'DRIFT-002' && echo yes || echo no)"

# ── 4. presupuesto duro de chars: recorta con marcador ────────────────────────
OUT3="$(BITACORA_PUSH_MAX_CHARS=80 run_push '{"source":"startup"}')"
check "presupuesto: recorta con marcador" "yes" "$(printf '%s' "$OUT3" | grep -q 'recortado' && echo yes || echo no)"

# ── 5. off-switch → contexto vacío ────────────────────────────────────────────
OUT4="$(BITACORA_PUSH=off run_push '{"source":"startup"}')"
check "off: additionalContext vacío" "yes" "$(printf '%s' "$OUT4" | grep -q '"additionalContext":""' && echo yes || echo no)"

# ── 6. source=resume → no re-inyecta ──────────────────────────────────────────
OUT5="$(run_push '{"source":"resume"}')"
check "resume: additionalContext vacío" "yes" "$(printf '%s' "$OUT5" | grep -q '"additionalContext":""' && echo yes || echo no)"

# ── 7. INDEX ausente → vacío, exit 0 (fail-open) ──────────────────────────────
rm -f "$TMP/INDEX.md"
OUT6="$(run_push '{"source":"startup"}')"; RC6=$?
check "sin INDEX: vacío" "yes" "$(printf '%s' "$OUT6" | grep -q '"additionalContext":""' && echo yes || echo no)"
check "sin INDEX: exit 0 (fail-open)" "0" "$RC6"

# ── 8. cap inválido (basura) → cae al default y sigue emitiendo ───────────────
cat > "$TMP/INDEX.md" <<'EOF'
| SÍNTOMA OBSERVABLE (lo que ves) | TIPO | ACCIÓN (1 línea) | ENTRADA | validated_on | usos | estado |
|---|---|---|---|---|---|---|
| Sintoma X | GAP | Accion X | [GAP-001](entries/GAP-001.md) | 2026-07-01 | 1 | LIVE |
EOF
OUT7="$(BITACORA_PUSH_MAX=abc run_push '{"source":"startup"}')"
check "cap inválido: default y emite igual" "yes" "$(printf '%s' "$OUT7" | grep -q 'GAP-001' && echo yes || echo no)"

echo
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
