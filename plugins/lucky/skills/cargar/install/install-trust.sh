#!/usr/bin/env bash
# install-trust — fija el estado del install del loader `cargar` en disco, FUERA
# del repo: el PIN (tag, commit, registry-url) que el fetcher lee SIN depender
# del env que el modelo controla. Idempotente.
#
# La clave publica minisign YA NO se ancla: la firma fue RETIRADA (ADR 0009,
# dueño unico del repo; vuelve si el trade-off cambia). El ancla de confianza es
# este pin (TAG hoy; COMMIT cuando se fije — v2) + los sha256 del registry,
# verificados por codigo (cargar-fetch-verify.sh).
#
# Uso:
#   bash install-trust.sh --tag vX.Y.Z [--commit <sha40>] [--registry-url <BASE>]
#
# BASE/registry-url es el unico ancla; si no se pasa, se toma de SKILLS_REGISTRY_URL
# del env (Infisical). Nunca se hornea un dominio.
set -euo pipefail

TAG=""; COMMIT=""; REGURL="${SKILLS_REGISTRY_URL:-}"
while [ $# -gt 0 ]; do
  case "$1" in
    --tag)          TAG="${2:-}"; shift 2 ;;
    --commit)       COMMIT="${2:-}"; shift 2 ;;
    --registry-url) REGURL="${2:-}"; shift 2 ;;
    *)              echo "flag desconocida: $1" >&2; exit 1 ;;
  esac
done
[ -n "$TAG" ]    || { echo "Uso: bash install-trust.sh --tag vX.Y.Z [--commit <sha40>] [--registry-url <BASE>]" >&2; exit 1; }
[ -n "$REGURL" ] || { echo "Falta el ancla: pasá --registry-url o exportá SKILLS_REGISTRY_URL" >&2; exit 1; }
if [ -n "$COMMIT" ] && ! printf '%s' "$COMMIT" | grep -qE '^[0-9a-f]{40}$'; then
  echo "--commit debe ser un SHA40 hex minúscula (el pin inmutable)." >&2; exit 1
fi

# 1) Destino FUERA del repo (por-usuario, agnostico de OS).
if [ -n "${LOCALAPPDATA:-}" ]; then
  STATE_DIR="$(cygpath -u "$LOCALAPPDATA" 2>/dev/null || printf '%s' "$LOCALAPPDATA")/lucky/cargar"
else
  STATE_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/lucky/cargar"
fi
STATE="$STATE_DIR/state.env"
mkdir -p "$STATE_DIR"

# 2) Fijar el estado del install (tag/commit/registry-url). LF puro.
{
  printf 'SKILLS_REGISTRY_URL=%s\n' "$REGURL"
  printf 'CARGAR_TAG=%s\n' "$TAG"
  if [ -n "$COMMIT" ]; then printf 'CARGAR_COMMIT=%s\n' "$COMMIT"; fi
} > "$STATE.tmp"
sed 's/\r$//' "$STATE.tmp" > "$STATE" && rm -f "$STATE.tmp"
chmod 0644 "$STATE" 2>/dev/null || true

echo "Estado del install (pin) fijado en: $STATE"
echo "   tag=$TAG${COMMIT:+ commit=$COMMIT}"
echo "   sin firma: integridad = sha256 contra el registry del pin (ADR 0009)."
