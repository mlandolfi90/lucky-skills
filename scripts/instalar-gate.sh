#!/usr/bin/env bash
# instalar-gate — instala/actualiza el gate GLOBAL del Crisol en ~/.claude.
#
# Hace, idempotente y NO destructivo:
#   1. copia plugins/lucky/skills/crisol/hooks/crisol_gate.py -> ~/.claude/hooks/
#      (solo si difiere);
#   2. cablea ~/.claude/settings.json (PreToolUse Edit|Write|MultiEdit + Bash) para
#      que llame al gate, PRESERVANDO theme/env/otros hooks (merge, no overwrite);
#   3. crea ~/.claude/CLAUDE.md con la regla global "TARGET antes de codear"
#      (append con guard de marcador; nunca sobreescribe lo existente);
#   4. crea ~/.claude/.target-cache/ (marcadores del piso TARGET).
#
# NO firma nada. NO toca repos del usuario. Entorno real: Git-Bash en Windows.
set -euo pipefail
export PYTHONIOENCODING=utf-8

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
GATE_SRC="$REPO_ROOT/plugins/lucky/skills/crisol/hooks/crisol_gate.py"
[ -f "$GATE_SRC" ] || { echo "XX no encuentro $GATE_SRC" >&2; exit 1; }

PYBIN=""
for c in python python3 py; do command -v "$c" >/dev/null 2>&1 && { PYBIN="$c"; break; }; done
[ -n "$PYBIN" ] || { echo "XX python no esta en PATH" >&2; exit 1; }

CLAUDE_DIR="$("$PYBIN" -c "from pathlib import Path; print(Path.home()/'.claude')")"
HOOKS_DIR="$CLAUDE_DIR/hooks"
GATE_DST="$HOOKS_DIR/crisol_gate.py"
SETTINGS="$CLAUDE_DIR/settings.json"
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
CACHE_DIR="$CLAUDE_DIR/.target-cache"
mkdir -p "$HOOKS_DIR" "$CACHE_DIR"

# 1. copiar el gate (solo si difiere)
if [ -f "$GATE_DST" ] && cmp -s "$GATE_SRC" "$GATE_DST"; then
  echo "  .  gate ya actualizado ($GATE_DST)"
else
  cp -f "$GATE_SRC" "$GATE_DST"
  echo "  OK gate copiado -> $GATE_DST"
fi

# ruta Windows del gate para el command de settings.json
GATE_WIN="$("$PYBIN" -c "import os,sys; print(os.path.abspath(sys.argv[1]).replace('/','\\\\'))" "$GATE_DST")"

# 2. cablear settings.json (merge no destructivo, idempotente)
SETTINGS="$SETTINGS" GATE_WIN="$GATE_WIN" "$PYBIN" - <<'PY'
import json, os
p = os.environ["SETTINGS"]; gate = os.environ["GATE_WIN"]
cmd = 'python "%s"' % gate
try:
    with open(p, encoding="utf-8") as fh: d = json.load(fh)
    if not isinstance(d, dict): d = {}
except Exception:
    d = {}
hooks = d.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
if not isinstance(pre, list): pre = []; hooks["PreToolUse"] = pre
changed = False
for matcher in ("Edit|Write|MultiEdit", "Bash"):
    entry = next((e for e in pre if isinstance(e, dict) and e.get("matcher") == matcher), None)
    if entry is None:
        entry = {"matcher": matcher, "hooks": []}; pre.append(entry); changed = True
    hl = entry.setdefault("hooks", [])
    if not any(isinstance(h, dict) and "crisol_gate.py" in (h.get("command") or "") for h in hl):
        hl.append({"type": "command", "command": cmd, "timeout": 12}); changed = True
if changed:
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=2); fh.write("\n")
    print("  OK settings.json cableado (PreToolUse Edit|Write|MultiEdit + Bash)")
else:
    print("  .  settings.json ya tenia el gate cableado (sin cambios)")
PY

# 3. CLAUDE.md global (append con guard de marcador)
if [ -f "$CLAUDE_MD" ] && grep -q 'crisol-target-floor' "$CLAUDE_MD" 2>/dev/null; then
  echo "  .  CLAUDE.md ya tiene la regla TARGET (sin cambios)"
else
  cat >> "$CLAUDE_MD" <<EOF
<!-- crisol-target-floor -->
# Regla global — TARGET antes de codear

Antes de editar CODIGO en CUALQUIER repo (no solo los que adoptaron el Crisol),
sabe DONDE corre ese codigo. Si no esta declarado, PREGUNTALE al humano:
"¿Donde corre este codigo?" — y elegi UNO:

- \`paas:<proyecto>/<app>@<env>\`  (env in dev | testing | production ; dev = default)
- \`docker-local\`  (contenedor Linux fiel en esta maquina)
- \`pc-local\`  (esta PC / Windows) — SOLO si el humano lo pide explicito

\`pc-local\` NO es el default. El default de desarrollo es un VPS Linux remoto.
Target ambiguo o desconocido -> PREGUNTAR y esperar, jamas asumir local.

En repos NO adoptados, tras confirmar el TARGET, registralo una vez por sesion
(si chocas el piso, el hook te da el comando exacto con session_id y repo ya
rellenados):

    python "$GATE_WIN" --register-target "<TARGET>" --session "<session_id>" --repo "<repo-root>"

Editar docs/.md o planificar nunca requiere TARGET.
<!-- /crisol-target-floor -->
EOF
  echo "  OK CLAUDE.md global creado/actualizado ($CLAUDE_MD)"
fi

echo "  OK instalacion completa. Cache de marcadores: $CACHE_DIR"
