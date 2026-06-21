#!/usr/bin/env bash
# crisol-enforcer — PreToolUse hook (Edit|Write|MultiEdit)
# DURO: bloquea cambios de CÓDIGO sin entrada STATUS: ACTIVE *con campos mínimos*
# (Tier: + Fecha:) en el ledger. Una línea suelta con ACTIVE no habilita nada.
# OBJETIVO: regla binaria, sin criterio humano. Exit 2 = bloquea y avisa a Claude.
set -euo pipefail

LEDGER="docs/refactor/_crisol/RUN-LEDGER.md"

# 1. Ruta del archivo que se quiere tocar (viene en el JSON del hook por stdin)
INPUT="$(cat)"
FILE="$(printf '%s' "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*"file_path"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/')"
[ -z "$FILE" ] && exit 0   # sin ruta → no opina

# 2. EXENTOS (no son código→commit): docs, markdown, el propio ledger/templates
case "$FILE" in
  *.md|docs/*|*/docs/*|*.txt) exit 0 ;;
esac

# 3. Branch actual
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
[ -z "$BRANCH" ] && exit 0   # sin git → no aplica

# 3b. OPT-IN por repo: sin adopción del Crisol (docs/refactor/_crisol/) → inerte
[ -d "docs/refactor/_crisol" ] || exit 0

# 4. ¿Hay entrada ACTIVE para ESTE branch CON campos mínimos (Tier + Fecha + TARGET)?
#    (parseo por bloque ### — los campos pueden venir en cualquier orden)
#    TARGET cuenta solo si tiene valor real (no vacío, no <placeholder>): codear
#    sin declarar DÓNDE corre = verificar a ciegas (paridad con crisol_gate.py).
ACTIVE="$(awk -v b="$BRANCH" '
  /^### /      { entry=$0; st=""; tier=0; fecha=0; target=0 }
  /^- STATUS:/ { st=$0 }
  /^- Tier:/   { tier=1 }
  /^- Fecha:/  { fecha=1 }
  /^- TARGET:/ {
    v=$0; sub(/^- TARGET:[[:space:]]*/,"",v); lv=tolower(v)
    # paridad EXACTA con crisol_gate.py (_target_is_declared usa val.lower()):
    # placeholders comparados case-INSENSITIVE (TBD == tbd == Tbd).
    if (v != "" && v !~ /^</ && lv !~ /^(pendiente|tbd|n\/d|na|\?)[[:space:]]*$/) target=1
  }
  st ~ /ACTIVE/ && entry ~ b && tier && fecha && target { found=1 }
  END { print (found?"yes":"no") }
' "$LEDGER" 2>/dev/null || echo no)"

if [ "$ACTIVE" != "yes" ]; then
  echo "🚨 CRISOL BLOQUEADO: no hay entrada 'STATUS: ACTIVE' con campos mínimos (Tier: + Fecha: + TARGET:) para el branch '$BRANCH' en $LEDGER." >&2
  echo "Falta el ledger ACTIVE o el campo TARGET (dónde corre/verifica). Preguntá al humano dónde corre; no asumas local." >&2
  echo "Abrí/completá la corrida del Crisol (/crisol) — paso 2 — antes de tocar código fuente." >&2
  exit 2   # bloquea la tool-call y devuelve este texto a Claude
fi
exit 0
