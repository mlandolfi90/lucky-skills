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

# AISLAMIENTO: el timbre lee el log del observador — apuntarlo a un dir de
# fixture VACÍO para que el log real de la máquina jamás contamine los tests.
OBSDIR="$TMP/obs"; mkdir -p "$OBSDIR"
export BITACORA_OBSERVAR_DIR="$OBSDIR"

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

# ══ TIMBRE DE JUICIO (enmienda ADR 0010) ══════════════════════════════════════

# fixture con 2 LIVE + 1 CANDIDATE
cat > "$TMP/INDEX.md" <<'EOF'
| SÍNTOMA OBSERVABLE (lo que ves) | TIPO | ACCIÓN (1 línea) | ENTRADA | validated_on | usos | estado |
|---|---|---|---|---|---|---|
| Sintoma A | GAP | Accion A | [GAP-001](entries/GAP-001.md) | 2026-07-01 | 2 | LIVE |
| Sintoma B | DRIFT | Accion B | [DRIFT-001](entries/DRIFT-001.md) | 2026-07-02 | 1 | LIVE |
| Sospecha C | GAP | Accion C | [GAP-099](entries/GAP-099.md) | 2026-07-09 | 0 | CANDIDATE |
EOF

# ── 9. CANDIDATE presente → timbre con conteo ─────────────────────────────────
OUT9="$(run_push '{"source":"startup"}')"
check "timbre: CANDIDATE suena con conteo" "yes" "$(printf '%s' "$OUT9" | grep -q 'JUICIO PENDIENTE' && printf '%s' "$OUT9" | grep -q '1 entrada(s) CANDIDATE' && echo yes || echo no)"

# ── 10. señal con visto ≥ 2 en el log del observador → timbre ─────────────────
cat > "$OBSDIR/observaciones.log" <<'EOF'
2026-07-09 10:00 · repo-a · GATE-BLOQUEO · x2
2026-07-09 11:00 · repo-b · GATE-BLOQUEO · x1
2026-07-09 11:00 · repo-b · SUITE-ROJA · x1
EOF
OUT10="$(run_push '{"source":"startup"}')"
check "timbre: 1 señal visto≥2 (GATE-BLOQUEO x2 sesiones; SUITE-ROJA x1 no)" "yes" "$(printf '%s' "$OUT10" | grep -q '1 señal(es) con visto ≥ 2' && echo yes || echo no)"

# ── 11. timbre PRIMERO: sobrevive al recorte de presupuesto ───────────────────
check "timbre: aparece ANTES que los patrones" "yes" "$(printf '%s' "$OUT10" | awk '{i=index($0,"JUICIO"); p=index($0,"Patrones LIVE"); if (i>0 && p>0 && i<p) print "yes"; else print "no"}')"
OUT11="$(BITACORA_PUSH_MAX_CHARS=150 run_push '{"source":"startup"}')"
check "timbre: sobrevive presupuesto apretado (150c)" "yes" "$(printf '%s' "$OUT11" | grep -q 'JUICIO' && echo yes || echo no)"

# ── 12. timbre-solo: INDEX sin LIVE pero con CANDIDATE → emite igual ──────────
rm -f "$OBSDIR/observaciones.log"
cat > "$TMP/INDEX.md" <<'EOF'
| SÍNTOMA OBSERVABLE (lo que ves) | TIPO | ACCIÓN (1 línea) | ENTRADA | validated_on | usos | estado |
|---|---|---|---|---|---|---|
| Sospecha C | GAP | Accion C | [GAP-099](entries/GAP-099.md) | 2026-07-09 | 0 | CANDIDATE |
EOF
OUT12="$(run_push '{"source":"startup"}')"
check "timbre-solo: sin LIVE emite el timbre igual" "yes" "$(printf '%s' "$OUT12" | grep -q 'JUICIO PENDIENTE' && echo yes || echo no)"
check "timbre-solo: sin sección de patrones" "no" "$(printf '%s' "$OUT12" | grep -q 'Patrones LIVE' && echo yes || echo no)"

# ── 13. cero pendientes → cero ruido (sin sección JUICIO) ─────────────────────
cat > "$TMP/INDEX.md" <<'EOF'
| SÍNTOMA OBSERVABLE (lo que ves) | TIPO | ACCIÓN (1 línea) | ENTRADA | validated_on | usos | estado |
|---|---|---|---|---|---|---|
| Sintoma A | GAP | Accion A | [GAP-001](entries/GAP-001.md) | 2026-07-01 | 1 | LIVE |
EOF
OUT13="$(run_push '{"source":"startup"}')"
check "cero pendientes: sin timbre (cero ruido)" "no" "$(printf '%s' "$OUT13" | grep -q 'JUICIO' && echo yes || echo no)"

# ── 14. off apaga TODO (timbre incluido) ──────────────────────────────────────
cat > "$OBSDIR/observaciones.log" <<'EOF'
2026-07-09 10:00 · r · GATE-BLOQUEO · x1
2026-07-09 11:00 · r · GATE-BLOQUEO · x1
EOF
OUT14="$(BITACORA_PUSH=off run_push '{"source":"startup"}')"
check "off: apaga también el timbre" "yes" "$(printf '%s' "$OUT14" | grep -q '"additionalContext":""' && echo yes || echo no)"
rm -f "$OBSDIR/observaciones.log"

# ── 15. control chars crudos en el INDEX no rompen el contrato JSON (RFC 8259) ─
#    (hallazgo del panel adversarial: ESC 0x1b de ANSI pegado en un síntoma)
printf '| S\303\215NTOMA OBSERVABLE (lo que ves) | TIPO | ACCI\303\223N (1 l\303\255nea) | ENTRADA | validated_on | usos | estado |\n|---|---|---|---|---|---|---|\n| log muestra \033[31mFAIL\033[0m con \001 crudo | GAP | mirar el gate | [EV-9](entries/EV-9.md) | 2026-07-09 | 2 | LIVE |\n' > "$TMP/INDEX.md"
OUT15="$(run_push '{"source":"startup"}')"
check "control-chars: cero bytes crudos U+0000-001F en la salida" "0" "$(printf '%s' "$OUT15" | grep -c $'\x1b' || true)"
PYJ=""; command -v python >/dev/null 2>&1 && PYJ=python; [ -z "$PYJ" ] && command -v python3 >/dev/null 2>&1 && PYJ=python3
if [ -n "$PYJ" ]; then
  check "control-chars: la salida sigue siendo JSON válido (json.loads)" "ok" "$(printf '%s' "$OUT15" | "$PYJ" -c 'import sys,json; json.loads(sys.stdin.read()); print("ok")' 2>/dev/null || echo broken)"
else
  echo "  ⤼ python ausente — check json.loads omitido"
fi
check "control-chars: el contenido útil sobrevive (sin ANSI)" "yes" "$(printf '%s' "$OUT15" | grep -q '31mFAIL' && echo yes || echo no)"

# ── 16. PARIDAD log_dir: push == observar (la copia jamás deriva) ─────────────
OBS_SRC="$HERE/../hooks/bitacora-observar.sh"
P1="$(BITACORA_OBSERVAR_DIR="/x/paridad" bash "$PUSH" --print-log-dir)"
O1="$(BITACORA_OBSERVAR_DIR="/x/paridad" bash "$OBS_SRC" --print-log-dir)"
check "paridad log_dir (override) push==observar" "$O1" "$P1"
P2="$(env -u BITACORA_OBSERVAR_DIR LOCALAPPDATA="$TMP/fake-lad" bash "$PUSH" --print-log-dir)"
O2="$(env -u BITACORA_OBSERVAR_DIR LOCALAPPDATA="$TMP/fake-lad" bash "$OBS_SRC" --print-log-dir)"
check "paridad log_dir (LOCALAPPDATA) push==observar" "$O2" "$P2"

echo
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
