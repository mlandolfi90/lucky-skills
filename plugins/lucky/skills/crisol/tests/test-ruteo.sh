#!/usr/bin/env bash
# test-ruteo — evals MECÁNICOS de ruteo del árbol (ADR 0020 §5, métrica M5).
# El árbol no solo crece: se verifica que siga siendo navegable.
#   R1: todo tronco (SKILL.md) declara disparadores en su description.
#   R2: toda rama estable tiene gatillo no vacío y útil (≥15 chars).
#   R3: dentro de una skill no hay dos ramas con el mismo gatillo.
# Los evals LLM-conducidos (¿elige la rama correcta ante el síntoma X?) son
# deuda declarada (harness pineado) — esto es el piso determinista.
set -uo pipefail

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="${RUTEO_REPO_OVERRIDE:-$(cd "$TESTS_DIR/../../../../.." && pwd)}"
PYBIN="$(command -v python || command -v python3 || echo python)"
"$PYBIN" -c "import yaml" 2>/dev/null || { echo "XX falta PyYAML"; exit 1; }

"$PYBIN" - "$REPO_ROOT" <<'PYEOF'
import re
import sys
from pathlib import Path

import yaml

repo = Path(sys.argv[1])
skills = repo / "plugins" / "lucky" / "skills"
front = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
fallas = []
troncos = ramas = 0

DISPARADORES = re.compile(r"(?i)(disparar|invocar|usar (al|cuando|para)|Ú?sala|use (this|when)|trigger)")

for sk in sorted(skills.iterdir()):
    tronco = sk / "SKILL.md"
    if not tronco.is_file():
        continue
    troncos += 1
    m = front.match(tronco.read_text(encoding="utf-8-sig", errors="replace"))
    fm = yaml.safe_load(m.group(1)) if m else None
    desc = str((fm or {}).get("description", ""))
    if not desc:
        fallas.append(f"R1 {sk.name}: SKILL.md sin description en frontmatter")
    elif not DISPARADORES.search(desc):
        fallas.append(f"R1 {sk.name}: description sin disparadores (¿cuándo se invoca?)")
    gatillos = {}
    rdir = sk / "ramas"
    if rdir.is_dir():
        for p in sorted(rdir.glob("[0-9][0-9][0-9]-*.md")):
            mm = front.match(p.read_text(encoding="utf-8-sig", errors="replace"))
            rfm = yaml.safe_load(mm.group(1)) if mm else None
            if not isinstance(rfm, dict):
                fallas.append(f"R2 {sk.name}/{p.name}: rama ilegible")
                continue
            if str(rfm.get("canal", "propuesta")).lower() != "estable":
                continue  # cuarentena: el ruteo no la ve
            ramas += 1
            g = str(rfm.get("gatillo", "")).strip()
            if len(g) < 15:
                fallas.append(f"R2 {sk.name}/{p.name}: gatillo vacío o inútil (<15 chars)")
                continue
            clave = g.lower()
            if clave in gatillos:
                fallas.append(f"R3 {sk.name}: gatillo DUPLICADO entre {gatillos[clave]} y {p.name}")
            gatillos[clave] = p.name

if fallas:
    print(f"XX test-ruteo: {len(fallas)} falla(s) ({troncos} troncos, {ramas} ramas estables)")
    for x in fallas:
        print(f"   - {x}")
    sys.exit(1)
print(f"OK test-ruteo: {troncos} troncos con disparadores · {ramas} ramas estables con gatillo único y útil")
PYEOF
