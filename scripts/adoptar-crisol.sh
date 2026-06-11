#!/usr/bin/env bash
# adoptar-crisol — pone un repo bajo la ley (lucky-skills). Correr UNA vez
# desde la RAÍZ del repo objetivo. Idempotente. NO commitea: deja el diff
# listo para review humano (git status) — la adopción se commitea a mano.
set -euo pipefail
export PYTHONIOENCODING=utf-8  # Windows: cp1252 no imprime emojis

[ -d ".git" ] || { echo "❌ Corré esto desde la raíz de un repo git."; exit 1; }
echo "⚒️  Adoptando el Crisol en: $(pwd)"
echo

# 1. .claude/settings.json — merge NO destructivo (preserva lo existente)
mkdir -p ".claude"
python - << 'PY'
import json, os
p = os.path.join(".claude", "settings.json")
data = {}
if os.path.exists(p):
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
mk = data.setdefault("extraKnownMarketplaces", {})
mk.setdefault("lucky-skills", {"source": {"source": "github", "repo": "mlandolfi90/lucky-skills"}})
ep = data.setdefault("enabledPlugins", {})
ep["lucky@lucky-skills"] = True
with open(p, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("  ✅ .claude/settings.json — marketplace lucky-skills + plugin lucky habilitado")
PY

# 2. Opt-in del enforcement: el ledger (su existencia activa ambos guardianes)
if [ ! -f "docs/refactor/_crisol/RUN-LEDGER.md" ]; then
  mkdir -p "docs/refactor/_crisol"
  printf '# RUN-LEDGER — %s (bajo el Crisol, lucky-skills)\n' "$(basename "$(pwd)")" > "docs/refactor/_crisol/RUN-LEDGER.md"
  echo "  ✅ docs/refactor/_crisol/RUN-LEDGER.md — opt-in creado (el gate ya muerde acá)"
else
  echo "  ↻ ledger ya existía — opt-in ya estaba activo"
fi

# 3. CLAUDE.md — directiva que TODA sesión lee al arrancar (idempotente)
MARK="<!-- crisol-adoptado -->"
if ! grep -q "$MARK" "CLAUDE.md" 2>/dev/null; then
  cat >> "CLAUDE.md" << 'MD'

<!-- crisol-adoptado -->
## Ley del repo — Crisol (lucky-skills)

Este repo está bajo el Crisol. Al iniciar sesión: correr la skill **brujula**
(ancla al estado real). Antes de tocar código: **/crisol** — la skill verifica
su propia vigencia al invocarse (Ley viva). Fuente de verdad del proceso:
`github.com/mlandolfi90/lucky-skills` (último tag).
MD
  echo "  ✅ CLAUDE.md — sección Crisol agregada"
else
  echo "  ↻ CLAUDE.md ya tenía la sección"
fi

# 3b. Hooks zombis: entradas de settings que apuntan a vendoreados viejos
python - << 'PYZ'
import json, os
p = os.path.join(".claude", "settings.json")
if os.path.exists(p):
    with open(p, encoding="utf-8") as f: d = json.load(f)
    h = d.get("hooks", {})
    changed = False
    for ev in list(h.keys()):
        keep = []
        for m in h[ev]:
            cmds = json.dumps(m)
            if "-lucky/" in cmds or "-lucky\\" in cmds: changed = True; continue
            keep.append(m)
        if keep: h[ev] = keep
        else: del h[ev]; changed = True
    if changed:
        if not h: d.pop("hooks", None)
        with open(p, "w", encoding="utf-8") as f: json.dump(d, f, indent=2, ensure_ascii=False); f.write(chr(10))
        print("  🧟 hooks zombis eliminados de settings.json")
PYZ

# 4. Limpieza: copias vendoreadas VIEJAS (fuente de ambigüedad de versión)
for d in ".claude/skills/crisol-lucky" ".claude/skills/brujula-lucky"; do
  if [ -d "$d" ]; then
    rm -rf -- "$d"
    echo "  🗑️  borrado vendoreado viejo: $d (la versión vigente llega por el plugin)"
  fi
done

echo
echo "Listo. Revisá el diff (git status / git diff) y commiteá la adopción."
echo "(Es cambio de docs+config: el gate no la bloquea, no requiere corrida.)"
