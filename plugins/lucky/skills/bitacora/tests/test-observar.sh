#!/usr/bin/env bash
# test-observar — fixture del hook SessionEnd bitacora-observar.sh (ADR 0010).
# Prueba: detección determinista de señales, zero-leak (solo etiqueta+conteo),
# off-switch, sin transcript → silencio, rotación dura, --resumen, exit 0 SIEMPRE.
set -uo pipefail
export LC_ALL=C

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
OBS="$HERE/../hooks/bitacora-observar.sh"

PASS=0; FAIL=0
check(){ if [ "$2" = "$3" ]; then PASS=$((PASS+1)); echo "  ✅ $1"; else FAIL=$((FAIL+1)); echo "  ❌ $1 (esperado '$2', obtuvo '$3')"; fi; }

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
LOGDIR="$TMP/logdir"; LOG="$LOGDIR/observaciones.log"

# transcript fixture: 2 bloqueos de gate + 1 suite roja (JSONL simulado)
TRX="$TMP/transcript.jsonl"
cat > "$TRX" <<'EOF'
{"type":"tool_result","content":"[CRISOL] BLOQUEADO: este cambio no paso por el Crisol"}
{"type":"text","content":"reintento la edicion"}
{"type":"tool_result","content":"[CRISOL] BLOQUEADO: la corrida ACTIVE no declara TARGET"}
{"type":"tool_result","content":"PASS=7 FAIL=2"}
{"type":"text","content":"todo verde ahora: PASS=9 FAIL=0"}
EOF

json(){ printf '{"transcript_path":"%s","cwd":"%s","session_id":"s1"}' "$1" "$2"; }

# ── 1. detecta señales con conteo correcto ────────────────────────────────────
BITACORA_OBSERVAR_DIR="$LOGDIR" bash "$OBS" <<< "$(json "$TRX" "$TMP/mi-repo-secreto")"
check "exit 0 en hook" "0" "$?"
check "GATE-BLOQUEO x2" "yes" "$(grep -q 'GATE-BLOQUEO · x2' "$LOG" 2>/dev/null && echo yes || echo no)"
check "SUITE-ROJA x1 (FAIL=0 no cuenta)" "yes" "$(grep -q 'SUITE-ROJA · x1' "$LOG" 2>/dev/null && echo yes || echo no)"

# ── 2. zero-leak: solo basename del repo, jamás la ruta completa ──────────────
check "zero-leak: registra basename del repo" "yes" "$(grep -q 'mi-repo-secreto' "$LOG" 2>/dev/null && echo yes || echo no)"
check "zero-leak: NO registra la ruta completa" "no" "$(grep -qF "$TMP" "$LOG" 2>/dev/null && echo yes || echo no)"
check "zero-leak: NO registra contenido del transcript" "no" "$(grep -q 'reintento la edicion' "$LOG" 2>/dev/null && echo yes || echo no)"

# ── 3. off-switch → no escribe nada ───────────────────────────────────────────
LOGDIR2="$TMP/logdir2"
BITACORA_OBSERVAR=off BITACORA_OBSERVAR_DIR="$LOGDIR2" bash "$OBS" <<< "$(json "$TRX" "$TMP/r")"
check "off: no crea log" "no" "$([ -f "$LOGDIR2/observaciones.log" ] && echo yes || echo no)"

# ── 4. sin transcript_path → silencio, exit 0 ─────────────────────────────────
BITACORA_OBSERVAR_DIR="$LOGDIR2" bash "$OBS" <<< '{"cwd":"/x"}'
check "sin transcript: exit 0 y sin log" "no" "$([ -f "$LOGDIR2/observaciones.log" ] && echo yes || echo no)"

# ── 5. transcript sin señales → no agrega líneas ──────────────────────────────
TRX2="$TMP/limpio.jsonl"; echo '{"type":"text","content":"sesion tranquila"}' > "$TRX2"
BEFORE="$(wc -l < "$LOG" | tr -d ' ')"
BITACORA_OBSERVAR_DIR="$LOGDIR" bash "$OBS" <<< "$(json "$TRX2" "$TMP/r")"
AFTER="$(wc -l < "$LOG" | tr -d ' ')"
check "sin señales: log intacto" "$BEFORE" "$AFTER"

# ── 6. rotación dura: el log jamás supera ~400 líneas ─────────────────────────
for i in $(seq 1 500); do echo "2026-07-09 00:00 · relleno · GATE-BLOQUEO · x1" >> "$LOG"; done
BITACORA_OBSERVAR_DIR="$LOGDIR" bash "$OBS" <<< "$(json "$TRX" "$TMP/r")"
N="$(wc -l < "$LOG" | tr -d ' ')"
check "rotación: ≤ 400 líneas tras la corrida" "yes" "$([ "$N" -le 400 ] && echo yes || echo no)"

# ── 7. --resumen agrega por señal ─────────────────────────────────────────────
RES="$(BITACORA_OBSERVAR_DIR="$LOGDIR" bash "$OBS" --resumen)"
check "--resumen: agrega GATE-BLOQUEO" "yes" "$(printf '%s' "$RES" | grep -q 'GATE-BLOQUEO' && echo yes || echo no)"

echo
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
