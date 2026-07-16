#!/usr/bin/env bash
# telemetria-uso — hook PostToolUse FAIL-OPEN (ADR 0019 §4).
# Registra la CARGA de troncos (SKILL.md), ramas y skills como JSONL local:
#   $XDG_DATA_HOME/lucky/telemetria/uso.jsonl   (default ~/.local/share)
# Alimenta la poda de ley muerta (la cosecha revisa ramas con 0 hits).
# JAMÁS bloquea, JAMÁS escribe en el repo, JAMÁS toca la red. Off-switch:
#   LUCKY_TELEMETRIA=off
# El cuerpo python vive en telemetria-uso.py (archivo propio: un heredoc
# consumiría el stdin del hook y el JSON jamás llegaría — bug cazado en T3).
# Cualquier error → exit 0 en silencio.
set -u
[ "${LUCKY_TELEMETRIA:-on}" = "off" ] && exit 0

# Intérprete por SONDA (el alias del Microsoft Store pasa `command -v` pero no corre).
PY=""
for c in python3 python; do
  command -v "$c" >/dev/null 2>&1 && "$c" -c "" >/dev/null 2>&1 && { PY="$c"; break; }
done
[ -n "$PY" ] || exit 0

DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
"$PY" "$DIR/telemetria-uso.py" 2>/dev/null || true
exit 0
