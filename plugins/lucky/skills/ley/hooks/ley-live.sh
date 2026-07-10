#!/usr/bin/env bash
# ley-live — SessionStart: trae la ley al último tag publicado (best-effort).
# Espejo silencioso de /ley: version-sort, tag-en-main, árbol limpio, ff-only.
# FAIL-OPEN TOTAL: cualquier duda/falla → exit 0 sin tocar nada (la sesión
# arranca con lo que haya; la brújula reporta el atraso como siempre).
# Off-switch: LEY_LIVE=off. /ley sigue siendo el camino manual VERIFICADO
# (integridad sha256 + reporte); este hook no lo reemplaza.

[ "${LEY_LIVE:-on}" = "off" ] && exit 0
command -v git >/dev/null 2>&1 || exit 0

CLON="${LEY_LIVE_CLON:-$HOME/.claude/plugins/marketplaces/lucky-skills}"
[ -d "$CLON/.git" ] || exit 0

REPO_URL="https://github.com/mlandolfi90/lucky-skills.git"

# último tag remoto — SIEMPRE version-sort (lexicográfico pone v1.9 > v1.20)
TAG="$(git ls-remote --tags --refs "$REPO_URL" 2>/dev/null \
  | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' | sort -V | tail -1)" || exit 0
[ -n "$TAG" ] || exit 0

LOCAL="$(git -C "$CLON" describe --tags --abbrev=0 2>/dev/null)"
[ "$LOCAL" = "$TAG" ] && exit 0

# el fetch puede quejarse por tags históricos divergentes (purga v1.7): tolerado
git -C "$CLON" fetch --tags --quiet origin >/dev/null 2>&1

# tag DIFERIDO (publicado, no mergeado a main) → no es nuestro problema: frenar
git -C "$CLON" merge-base --is-ancestor "$TAG" origin/main >/dev/null 2>&1 || exit 0

# árbol sucio (WIP de otra corrida) → jamás pisar
[ -z "$(git -C "$CLON" status --porcelain 2>/dev/null)" ] || exit 0

git -C "$CLON" pull --ff-only --quiet origin main >/dev/null 2>&1 || exit 0
exit 0
