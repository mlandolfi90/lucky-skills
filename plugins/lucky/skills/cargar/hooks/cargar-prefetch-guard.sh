#!/usr/bin/env bash
# cargar-prefetch-guard — PreToolUse hook (WebFetch) del loader `cargar`.
#
# WebFetch en `cargar` SOLO sirve para el aviso "¿hay un tag mayor?" (compara el
# string del tag). NUNCA para traer un cuerpo que se inyecte: WebFetch muta los
# bytes (markdown + resumen) y su salida no pasa sha256. El cuerpo lo
# trae+verifica cargar-fetch-verify.sh (curl, codigo externo).
#
# Este guard impone que CUALQUIER WebFetch del loader caiga dentro del unico
# origen permitido (SKILLS_REGISTRY_URL) y sin query/fragmento/@ (anti-exfiltracion).
# Si la url no canoniza -> exit 2 (bloquea la tool-call: el texto jamas entra).
# FAIL-CLOSED: sin SKILLS_REGISTRY_URL en el env del proceso -> bloquea.
set -uo pipefail

INPUT="$(cat)"
URL="$(printf '%s' "$INPUT" | grep -oE '"url"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*"url"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/')"
[ -z "$URL" ] && exit 0   # WebFetch sin url visible -> no opina (no es del loader)

BASE="${SKILLS_REGISTRY_URL:-}"
if [ -z "$BASE" ]; then
  echo "CARGAR BLOQUEADO: SKILLS_REGISTRY_URL no esta en el env del proceso del hook." >&2
  echo "Exportala (infisical run ... que la mapee a env real) antes de usar el loader." >&2
  exit 2
fi

# La url debe empezar EXACTO por el ancla. Si no es del catalogo, no es asunto del
# loader -> permitir (no bloqueamos WebFetch ajenos al loader).
case "$URL" in
  "$BASE/"*) : ;;
  *) exit 0 ;;
esac

# Es del catalogo: exigir higiene de URL.
case "$URL" in
  *\?*|*\#*|*@*|*..*)
    echo "CARGAR BLOQUEADO: WebFetch al catalogo con query/fragmento/@/.. prohibido (anti-exfiltracion)." >&2
    exit 2 ;;
esac
exit 0
