#!/usr/bin/env bash
# install-trust — empotra la clave publica minisign del loader `cargar` en disco,
# FUERA del repo (ancla TOFU install-only), y fija el estado del install (tag,
# commit, registry-url) que el fetcher lee SIN depender del env que el modelo controla.
# Idempotente. Verifica antes de fijar. Soporta ROTATE explicito.
#
# Uso:
#   bash install-trust.sh <cargar-release.pub> --tag vX.Y.Z [--commit <sha40>] [--registry-url <BASE>]
#   ROTATE=1 bash install-trust.sh <cargar-release.pub> --tag vX.Y.Z ...   # reanclar
#
# BASE/registry-url es el unico ancla; si no se pasa, se toma de SKILLS_REGISTRY_URL
# del env (Infisical). Nunca se hornea un dominio.
set -euo pipefail

SRC=""; TAG=""; COMMIT=""; REGURL="${SKILLS_REGISTRY_URL:-}"
while [ $# -gt 0 ]; do
  case "$1" in
    --tag)          TAG="${2:-}"; shift 2 ;;
    --commit)       COMMIT="${2:-}"; shift 2 ;;
    --registry-url) REGURL="${2:-}"; shift 2 ;;
    -*)             echo "flag desconocida: $1" >&2; exit 1 ;;
    *)              SRC="$1"; shift ;;
  esac
done
[ -n "$SRC" ] || { echo "Uso: bash install-trust.sh <cargar-release.pub> --tag vX.Y.Z [--commit <sha40>] [--registry-url <BASE>]" >&2; exit 1; }
[ -f "$SRC" ] || { echo "No existe: $SRC" >&2; exit 1; }
[ -n "$TAG" ] || { echo "Falta --tag (el fetcher pinea contra el)" >&2; exit 1; }
[ -n "$REGURL" ] || { echo "Falta el ancla: pasá --registry-url o exportá SKILLS_REGISTRY_URL" >&2; exit 1; }

# 1) Destino FUERA del repo (por-usuario, agnostico de OS).
if [ -n "${LOCALAPPDATA:-}" ]; then
  STATE_DIR="$(cygpath -u "$LOCALAPPDATA" 2>/dev/null || printf '%s' "$LOCALAPPDATA")/lucky/cargar"
else
  STATE_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/lucky/cargar"
fi
TRUST_DIR="$STATE_DIR/trust"
DEST="$TRUST_DIR/cargar-release.pub"
STATE="$STATE_DIR/state.env"

# 2) Sanidad: que sea una publica minisign (1 linea RW...), no una privada.
grep -q '^untrusted comment:' "$SRC" || { echo "No parece una clave minisign." >&2; exit 1; }
grep -q '^RW' "$SRC"                 || { echo "No hallé la linea publica (RW...)." >&2; exit 1; }
if grep -qi 'secret key' "$SRC"; then echo "¡Esto es una clave PRIVADA! Abortá." >&2; exit 1; fi

# 3) CRLF->LF (Windows rompe el parseo de minisign si la publica trae \r).
TMP="$(mktemp)"; trap 'rm -f "$TMP"' EXIT
sed 's/\r$//' "$SRC" > "$TMP"

# 4) TOFU: si ya hay una publica anclada y es DISTINTA -> no la pisás en silencio.
mkdir -p "$TRUST_DIR"
if [ -f "$DEST" ] && ! diff -q "$DEST" "$TMP" >/dev/null 2>&1; then
  echo "Ya hay una clave anclada DISTINTA en: $DEST" >&2
  echo "Esto es una ROTACION o un intento de suplantacion." >&2
  if [ "${ROTATE:-0}" != "1" ]; then
    echo "Si es rotacion legitima, re-corré con:  ROTATE=1 bash install-trust.sh \"$SRC\" --tag $TAG ..." >&2
    exit 2
  fi
  cp -f "$DEST" "$DEST.prev.$(date +%Y%m%d%H%M%S)"
fi

# 5) Fijar el ancla (la publica no es secreta; permisos para integridad del ancla).
install -m 0644 "$TMP" "$DEST" 2>/dev/null || cp -f "$TMP" "$DEST"

# 6) Fijar el estado del install (tag/commit/registry-url). LF puro.
{
  printf 'SKILLS_REGISTRY_URL=%s\n' "$REGURL"
  printf 'CARGAR_TAG=%s\n' "$TAG"
  [ -n "$COMMIT" ] && printf 'CARGAR_COMMIT=%s\n' "$COMMIT"
} > "$STATE.tmp"
sed 's/\r$//' "$STATE.tmp" > "$STATE" && rm -f "$STATE.tmp"
chmod 0644 "$STATE" 2>/dev/null || true

echo "Clave publica anclada (TOFU) en: $DEST"
grep '^untrusted comment:' "$DEST" | sed 's/^/   /'
echo "Estado del install fijado en: $STATE"
echo "   tag=$TAG${COMMIT:+ commit=$COMMIT}"
echo "   cotejá el key-id de arriba contra el que anotaste al generar la clave."
