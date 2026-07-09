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
# NO firma nada. NO toca repos del usuario. Entorno real: Git-Bash en Windows
# Y Linux/macOS — el cableado que escribe es PORTABLE ($HOME por-OS +
# python3||python + fail-open si el gate no esta instalado en esa maquina).
# Antes horneaba ruta Windows + `python` pelado -> exit 127 en Linux moderno
# (solo trae python3); repro y fix: corrida multi-OS 2026-07-09.
set -euo pipefail
export PYTHONIOENCODING=utf-8

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
GATE_SRC="$REPO_ROOT/plugins/lucky/skills/crisol/hooks/crisol_gate.py"
[ -f "$GATE_SRC" ] || { echo "XX no encuentro $GATE_SRC" >&2; exit 1; }

# PROBAR el interprete (no solo command -v): el stub de Microsoft Store existe
# en PATH pero no corre (exit 49 + "Python was not found").
PYBIN=""
for c in python python3 py; do "$c" -c "" >/dev/null 2>&1 && { PYBIN="$c"; break; }; done
[ -n "$PYBIN" ] || { echo "XX ningun python FUNCIONAL en PATH (stub de Store no cuenta)" >&2; exit 1; }

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

# 2. cablear settings.json (merge no destructivo, idempotente, PORTABLE)
#    El comando NO hornea ruta ni binario: $HOME se resuelve por-OS en runtime,
#    python3||python cubre Linux moderno (sin `python`) y Windows Git-Bash, y
#    el fail-open ([ -f ] || exit 0) garantiza que una sesion Linux/web SIN el
#    gate instalado jamas se rompa por el hook. MIGRA cableados viejos (ruta
#    Windows horneada / `python` pelado) reemplazando el command in situ.
SETTINGS="$SETTINGS" "$PYBIN" - <<'PY'
import json, os
p = os.environ["SETTINGS"]
# OJO Windows: `command -v python3` puede resolver al STUB de Microsoft Store
# (imprime "Python was not found", exit 49). Existir en PATH != funcionar:
# el comando PRUEBA cada interprete (`-c ""`) y usa el primero que corre.
cmd = ("bash -c 'GATE=\"$HOME/.claude/hooks/crisol_gate.py\"; "
       "[ -f \"$GATE\" ] || exit 0; "
       "for PY in python3 python; do "
       "\"$PY\" -c \"\" >/dev/null 2>&1 && exec \"$PY\" \"$GATE\"; "
       "done; exit 0'")
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
    found = False
    for h in hl:
        if isinstance(h, dict) and "crisol_gate.py" in (h.get("command") or ""):
            found = True
            if h.get("command") != cmd:  # migra el cableado viejo no-portable
                h["command"] = cmd
                h.setdefault("timeout", 12)
                changed = True
    if not found:
        hl.append({"type": "command", "command": cmd, "timeout": 12}); changed = True
if changed:
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=2); fh.write("\n")
    print("  OK settings.json cableado PORTABLE (migrado si habia cableado viejo)")
else:
    print("  .  settings.json ya tenia el cableado portable (sin cambios)")
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

    for PY in python3 python; do "\$PY" -c "" >/dev/null 2>&1 && break; done; \\
      "\$PY" "\$HOME/.claude/hooks/crisol_gate.py" --register-target "<TARGET>" --session "<session_id>" --repo "<repo-root>"

Editar docs/.md o planificar nunca requiere TARGET.
<!-- /crisol-target-floor -->
EOF
  echo "  OK CLAUDE.md global creado/actualizado ($CLAUDE_MD)"
fi

echo "  OK instalacion completa. Cache de marcadores: $CACHE_DIR"
