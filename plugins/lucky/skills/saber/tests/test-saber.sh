#!/usr/bin/env bash
# test-saber — invariantes MECÁNICOS del equipo del saber (ADR 0023).
# Dogfood contra los archivos REALES del repo (no fixtures): el agente destilador,
# la skill saber, y el cableado vivo en crisol/bitacora. Verde ⟺ exit 0 + 0 FAIL.
# REGLA 0: el Verificador lo corre ÉL MISMO en el TARGET.
set -uo pipefail
export LC_ALL=C

HERE="$(cd "$(dirname "$0")" && pwd)"
# tests/ → saber → skills → lucky → plugins → repo-root (5 niveles arriba)
REPO_ROOT="$(cd "$HERE/../../../../.." && pwd)"

DEST="$REPO_ROOT/plugins/lucky/agents/destilador.md"
SABER="$REPO_ROOT/plugins/lucky/skills/saber/SKILL.md"
CRISOL="$REPO_ROOT/plugins/lucky/skills/crisol/SKILL.md"
BITACORA="$REPO_ROOT/plugins/lucky/skills/bitacora/SKILL.md"

PYBIN="$(command -v python || command -v python3 || true)"
[ -n "$PYBIN" ] || { echo "XX test-saber: falta Python (python|python3) — test NO corrido = NO verde"; exit 1; }
"$PYBIN" -c 'import yaml' 2>/dev/null || { echo "XX test-saber: falta PyYAML (pip install pyyaml) — NO verde"; exit 1; }

pass=0; fail=0
ok(){ pass=$((pass+1)); }
ko(){ fail=$((fail+1)); echo "  FAIL: $1"; }

# Ancla de sello de familia, version-agnóstica (assert 3). Backticks LITERALES
# (asignada entre comillas simples; la expansión no re-evalúa command-subst).
ANCHOR_RE='`v[0-9.]+` \(cache local, NO la ley\)'

# ── Asserts que dependen de PyYAML (1 y 6): una sola invocación de Python ────────
PYOUT="$("$PYBIN" - "$DEST" "$SABER" <<'PYEOF'
import re
import sys
from pathlib import Path

import yaml

dest, saber = Path(sys.argv[1]), Path(sys.argv[2])
front = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
# La MISMA regex de disparadores de crisol/tests/test-ruteo.sh (copia exacta).
DISPARADORES = re.compile(r"(?i)(disparar|invocar|usar (al|cuando|para)|Ú?sala|use (this|when)|trigger)")


def fm(p):
    if not p.is_file():
        return None
    m = front.match(p.read_text(encoding="utf-8-sig", errors="replace"))
    if not m:
        return None
    d = yaml.safe_load(m.group(1))
    return d if isinstance(d, dict) else None


# A1: destilador.md existe y su frontmatter cumple el contrato agente/1.
d = fm(dest)
if d is None:
    print("A1 FAIL destilador.md ausente o frontmatter ilegible")
else:
    bad = []
    if str(d.get("id")) != "destilador":
        bad.append(f"id={d.get('id')!r}")
    if str(d.get("schema")) != "agente/1":
        bad.append(f"schema={d.get('schema')!r}")
    if str(d.get("tipo")) != "agente":
        bad.append(f"tipo={d.get('tipo')!r}")
    if str(d.get("estado")) != "LIVE":
        bad.append(f"estado={d.get('estado')!r}")
    if d.get("dictamina") != []:
        bad.append(f"dictamina={d.get('dictamina')!r}")
    print("A1 PASS" if not bad else "A1 FAIL " + ", ".join(bad))

# A6: la description de saber matchea la regex de disparadores de test-ruteo.
s = fm(saber)
if s is None:
    print("A6 FAIL saber/SKILL.md ausente o frontmatter ilegible")
else:
    desc = str(s.get("description", ""))
    if not desc:
        print("A6 FAIL saber/SKILL.md sin description en frontmatter")
    elif not DISPARADORES.search(desc):
        print("A6 FAIL description de saber sin disparadores (regex test-ruteo)")
    else:
        print("A6 PASS")
PYEOF
)"
echo "$PYOUT"

A1LINE="$(grep '^A1 ' <<<"$PYOUT" || true)"
case "$A1LINE" in "A1 PASS") ok;; *) ko "${A1LINE:-A1 sin salida del helper Python}";; esac

A6LINE="$(grep '^A6 ' <<<"$PYOUT" || true)"
case "$A6LINE" in "A6 PASS") ok;; *) ko "${A6LINE:-A6 sin salida del helper Python}";; esac

# ── A2: la línea tools: del destilador NO contiene Write ni Edit (PIN 3) ─────────
if [ -f "$DEST" ]; then
  TOOLS_LINE="$(grep -m1 '^tools:' "$DEST" || true)"
  if [ -z "$TOOLS_LINE" ]; then
    ko "A2 destilador.md sin línea 'tools:'"
  elif grep -qE 'Write|Edit' <<<"$TOOLS_LINE"; then
    ko "A2 tools: de destilador contiene Write/Edit (viola read-only PIN 3) → $TOOLS_LINE"
  else
    ok
  fi
else
  ko "A2 destilador.md ausente (no se puede verificar read-only)"
fi

# ── A3: EXACTAMENTE 1 ancla de sello en destilador.md Y en saber/SKILL.md ────────
for f in "$DEST" "$SABER"; do
  if [ -f "$f" ]; then
    n="$(grep -cE "$ANCHOR_RE" "$f")"
    if [ "$n" -eq 1 ]; then ok; else ko "A3 $(basename "$f"): $n ancla(s) de sello (esperado exactamente 1)"; fi
  else
    ko "A3 $(basename "$f") ausente"
  fi
done

# ── A4: crisol nombra al destilador en el bloque Destilación + tiene BITACORA: ───
if [ -f "$CRISOL" ]; then
  # Ventana del bloque: desde el header en negrita "**Destilaci..." hasta el ítem 9.
  BLOQUE="$(awk '/[*][*]Destilaci/{f=1} f{print} /^9\. /{if(f)exit}' "$CRISOL")"
  a4=1
  grep -qF 'destilador' <<<"$BLOQUE" || a4=0
  grep -qF 'BITACORA:' "$CRISOL" || a4=0
  if [ "$a4" -eq 1 ]; then ok; else ko "A4 crisol: falta 'destilador' en el bloque Destilación o 'BITACORA:' en el archivo (cableado roto)"; fi
else
  ko "A4 crisol/SKILL.md ausente"
fi

# ── A5: bitacora apunta a la skill saber (cableado del puntero) ──────────────────
if [ -f "$BITACORA" ]; then
  if grep -qF 'skill **`saber`**' "$BITACORA"; then ok; else ko "A5 bitacora/SKILL.md sin puntero a la skill 'saber'"; fi
else
  ko "A5 bitacora/SKILL.md ausente"
fi

echo "────────"
echo "RESULTADO: $pass PASS · $fail FAIL"
[ "$fail" -eq 0 ] || exit 1
exit 0
