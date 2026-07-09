#!/usr/bin/env bash
# crisol-enforcer — PreToolUse hook (Edit|Write|MultiEdit)
# DURO: bloquea cambios de CÓDIGO sin entrada STATUS: ACTIVE *con campos mínimos*
# (Tier: + Fecha: + TARGET:) en el ledger. Una línea suelta con ACTIVE no habilita nada.
# OBJETIVO: regla binaria, sin criterio humano. Exit 2 = bloquea y avisa a Claude.
#
# POLÍTICA DE DETECCIÓN DE CÓDIGO (allow-list, paridad EXACTA con crisol_gate.py:
# _CODE_EXTS + _CODE_FILENAMES): sólo esas extensiones/nombres se gatean; TODO lo
# demás (.json, .gitignore, LICENSE, .png, binarios, ...) pasa — no es código→commit.
# Fail-open por defecto: ante duda, permitir. Las dos listas se prueban idénticas
# por tests/test-enforcer.sh (extrae CODE_EXTS/CODE_FILENAMES de ambos guardianes).
set -euo pipefail

LEDGER="docs/refactor/_crisol/RUN-LEDGER.md"

# Allow-list de CÓDIGO — DEBE ser idéntica a crisol_gate.py:_CODE_EXTS/_CODE_FILENAMES
# (sin el punto inicial; el fixture verifica la paridad). Editar acá => editar allá.
CODE_EXTS="py js jsx ts tsx go rs java rb php c h hpp cpp cc cs sh bash ps1 psm1 sql yaml yml toml"
CODE_FILENAMES="dockerfile makefile"

# Modo introspección: imprime la política para el fixture de paridad y sale.
#   línea 1 = extensiones (sin punto) ; línea 2 = nombres de archivo completos.
if [ "${1:-}" = "--print-code-policy" ]; then
  printf '%s\n%s\n' "$CODE_EXTS" "$CODE_FILENAMES"
  exit 0
fi

# Umbral ATOMICIDAD (citación al juez, NO bloqueo): env → conf → default 400.
# Paridad EXACTA con crisol_gate.py:_atomicidad_threshold (mismo orden, mismo default).
_atomicidad_t() {
  local t=""
  if printf '%s' "${CRISOL_ATOMICIDAD_T:-}" | grep -qE '^[0-9]+$' 2>/dev/null; then
    t="${CRISOL_ATOMICIDAD_T}"
  elif [ -f docs/refactor/_crisol/atomicidad.conf ]; then
    t="$(grep -oE '^[0-9]+' docs/refactor/_crisol/atomicidad.conf 2>/dev/null | head -1 || true)"
  fi
  printf '%s' "$t" | grep -qE '^[0-9]+$' 2>/dev/null || t=400
  printf '%s' "$t"
}

# 1. Ruta del archivo que se quiere tocar (viene en el JSON del hook por stdin)
INPUT="$(cat)"
FILE="$(printf '%s' "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*"file_path"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/')"
[ -z "$FILE" ] && exit 0   # sin ruta → no opina

# 2. EXENTOS (paridad con crisol_gate.py:_is_excluded_path): docs, markdown/txt/rst,
#    y los segmentos .git / .claude — nunca son código→commit.
case "$FILE" in
  *.md|*.mdx|*.markdown|*.txt|*.rst) exit 0 ;;
  docs/*|*/docs/*) exit 0 ;;
  .git/*|*/.git/*|.claude/*|*/.claude/*) exit 0 ;;
esac

# 2b. ALLOW-LIST: sólo el código de la lista se gatea; el resto pasa (fail-open).
#     Paridad EXACTA con crisol_gate.py:_is_code_file (nombre completo, luego suffix).
BASE="${FILE##*/}"
LBASE="$(printf '%s' "$BASE" | tr '[:upper:]' '[:lower:]')"
IS_CODE=0
case " $CODE_FILENAMES " in *" $LBASE "*) IS_CODE=1 ;; esac
case "$LBASE" in
  ?*.*) EXT="${LBASE##*.}"; case " $CODE_EXTS " in *" $EXT "*) IS_CODE=1 ;; esac ;;
esac
[ "$IS_CODE" -eq 1 ] || exit 0   # no es código fuente → no opina (paridad con gate)

# 2c. ATOMICIDAD (Cambio 3): citación NO bloqueante si el archivo ya tiene ≥ T
#     líneas. A stderr; NUNCA cambia el exit. `wc -l` = newlines = paridad exacta
#     con crisol_gate.py (read_bytes().count(b"\n")). Mensaje byte-idéntico al gate.
if [ -f "$FILE" ]; then
  _AT_T="$(_atomicidad_t)"
  _AT_N="$(wc -l < "$FILE" 2>/dev/null | tr -d ' ' || true)"
  if printf '%s' "$_AT_N" | grep -qE '^[0-9]+$' 2>/dev/null && [ "$_AT_N" -ge "$_AT_T" ]; then
    printf '%s\n' "[CRISOL-ATOMICIDAD] $FILE: $_AT_N lineas (umbral $_AT_T) - SRP: parti antes de extender; citacion al juez, no bloqueo. Ajusta el umbral por chat -> docs/refactor/_crisol/atomicidad.conf" >&2
  fi
fi

# 3. Branch actual
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
[ -z "$BRANCH" ] && exit 0   # sin git → no aplica

# 3b. OPT-IN por repo: sin adopción del Crisol (docs/refactor/_crisol/) → inerte
[ -d "docs/refactor/_crisol" ] || exit 0

# 4. ¿Hay entrada ACTIVE para ESTE branch CON campos mínimos (Tier + Fecha + TARGET)?
#    (parseo por bloque ### — los campos pueden venir en cualquier orden)
#    Branch match EXACTO (== , no substring): la cabecera '### <branch> — <fecha>' se
#    parsea igual que crisol_gate.py (corta en ' — ' / ' - '). Así, en branch 'main',
#    una entrada '### main-hotfix' NO abre el gate (era false-PASS con match substring).
#    STATUS match EXACTO ('ACTIVE', no substring: 'INACTIVE' ya no cuenta).
#    TARGET cuenta solo si tiene valor real (no vacío, no <placeholder>): codear
#    sin declarar DÓNDE corre = verificar a ciegas (paridad con crisol_gate.py).
ACTIVE="$(awk -v b="$BRANCH" '
  /^### / {
    head=$0; sub(/^### /,"",head)
    p=index(head," \342\200\224 "); if (p==0) p=index(head," - ")   # em-dash o " - "
    if (p>0) head=substr(head,1,p-1)
    gsub(/^[ \t]+|[ \t]+$/,"",head)
    branch=head; st=""; tier=0; fecha=0; target=0
  }
  /^- STATUS:/ { st=$0; sub(/^- STATUS:[[:space:]]*/,"",st); st=toupper(st); gsub(/[ \t]+$/,"",st) }
  /^- Tier:/   { tier=1 }
  /^- Fecha:/  { fecha=1 }
  /^- TARGET:/ {
    v=$0; sub(/^- TARGET:[[:space:]]*/,"",v); lv=tolower(v)
    # paridad EXACTA con crisol_gate.py (_target_is_declared usa val.lower()):
    # placeholders comparados case-INSENSITIVE (TBD == tbd == Tbd).
    if (v != "" && v !~ /^</ && lv !~ /^(pendiente|tbd|n\/d|na|\?)[[:space:]]*$/) target=1
  }
  st == "ACTIVE" && branch == b && tier && fecha && target { found=1 }
  END { print (found?"yes":"no") }
' "$LEDGER" 2>/dev/null || echo no)"

if [ "$ACTIVE" != "yes" ]; then
  echo "🚨 CRISOL BLOQUEADO: no hay entrada 'STATUS: ACTIVE' con campos mínimos (Tier: + Fecha: + TARGET:) para el branch '$BRANCH' en $LEDGER." >&2
  echo "Falta el ledger ACTIVE o el campo TARGET (dónde corre/verifica). Preguntá al humano dónde corre; no asumas local." >&2
  echo "Abrí/completá la corrida del Crisol (/crisol) — paso 2 — antes de tocar código fuente." >&2
  exit 2   # bloquea la tool-call y devuelve este texto a Claude
fi
exit 0
