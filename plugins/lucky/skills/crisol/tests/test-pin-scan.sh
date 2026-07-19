#!/usr/bin/env bash
# test-pin-scan — PIN_TOTAL cubre el pin de EJECUCIÓN, no solo el de identidad.
# Escanea los artefactos EJECUTABLES del repo buscando invocaciones FLOATING de
# runner (`npx`/`uvx`/`pipx run` SIN `@<versión>`): correr un binario que un
# runner resuelve al vuelo es floating aunque el input esté pineado.
#   A1: cero invocaciones floating en el árbol actual.
#   A2 (red-proof invertido): un fixture inline `npx foo link` DEBE ser detectado
#       por la MISMA función de scan — así el detector se prueba a sí mismo
#       (RED_GREEN sin worktree: si el scan quedara ciego, A2 grita).
# Alcance: plugins/**/SKILL.md, plugins/**/*.sh, scripts/*.sh, .github/workflows/*.yml.
# Excluido: CHANGELOG.md y docs/ (no son artefactos ejecutables), y las líneas de
# prosa que CITAN el comando para prohibirlo/rechazarlo (heurística de palabras).
set -uo pipefail
export LC_ALL=C

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="${PINSCAN_REPO_OVERRIDE:-$(cd "$TESTS_DIR/../../../../.." && pwd)}"
PYBIN="$(command -v python || command -v python3 || echo python)"

# scan_floating <archivo...> — imprime "archivo:linea:contenido" por cada
# invocación floating de runner. Una sola función, reusada por A1 y A2.
scan_floating() {
  "$PYBIN" - "$@" <<'PYEOF'
import re
import sys

# Líneas que citan el comando para PROHIBIRLO/rechazarlo -> no son invocaciones
# reales, son prosa de la ley. Heurística de palabras (case-insensitive).
EXCL = re.compile(r"prohibid|pelado|floating|rechazad|precedente|=\s*fail", re.I)

# runner + flags opcionales (--yes, -y, --foo=bar) + primer token de paquete.
INVOKE = re.compile(
    r"""(?:^|[^\w./-])
        (?:npx|uvx|pipx\s+run)
        (?:\s+(?:--?[A-Za-z][\w-]*(?:=\S+)?))*   # flags del runner
        \s+
        ["'`]?                                    # comilla de apertura opcional
        (?P<pkg>[^\s"'`;|&]+)                     # token del paquete
    """,
    re.X,
)

def pinned(pkg: str) -> bool:
    # `@` de scope npm (@scope/pkg) no es versión: se descarta el líder.
    core = pkg[1:] if pkg.startswith("@") else pkg
    # pineado = hay un `@<algo>` en el token (literal @X, variable @${...},
    # placeholder @<tag>, etc.). Sin `@` -> el runner elige la versión = floating.
    return "@" in core

hits = []
for path in sys.argv[1:]:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        continue
    for i, line in enumerate(text.splitlines(), 1):
        if EXCL.search(line):
            continue
        for m in INVOKE.finditer(line):
            if not pinned(m.group("pkg")):
                hits.append(f"{path}:{i}:{line.strip()}")

for h in hits:
    print(h)
sys.exit(0)
PYEOF
}

# Lista de artefactos ejecutables en alcance (excluye docs/ y CHANGELOG.md).
collect_files() {
  {
    [ -d "$REPO_ROOT/plugins" ] && find "$REPO_ROOT/plugins" \
      \( -name 'SKILL.md' -o -name '*.sh' \) -type f
    [ -d "$REPO_ROOT/scripts" ] && find "$REPO_ROOT/scripts" \
      -maxdepth 1 -name '*.sh' -type f
    [ -d "$REPO_ROOT/.github/workflows" ] && find "$REPO_ROOT/.github/workflows" \
      \( -name '*.yml' -o -name '*.yaml' \) -type f
  } 2>/dev/null | grep -vE '/docs/|/CHANGELOG\.md$|/test-pin-scan\.sh$'
  # auto-exclusión: este archivo contiene fixtures floating A PROPÓSITO (A2)
}

PASS=0; FAIL=0
ok(){ if eval "$2"; then PASS=$((PASS+1)); echo "  OK  $1"; else FAIL=$((FAIL+1)); echo "  XX  $1"; fi; }

echo "== test-pin-scan =="

# --- A1: árbol actual sin invocaciones floating ---
mapfile -t FILES < <(collect_files)
A1_OUT="$(scan_floating "${FILES[@]}")"
if [ -n "$A1_OUT" ]; then
  echo "  -- floating detectado en el árbol:"
  printf '     %s\n' "$A1_OUT"
fi
ok "A1: cero invocaciones floating en el árbol" '[ -z "$A1_OUT" ]'

# --- A2: el detector detecta un fixture floating conocido (red-proof) ---
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
FIX="$TMP/fixture.sh"
printf '%s\n' 'npx foo link --providers=claude' > "$FIX"
A2_OUT="$(scan_floating "$FIX")"
ok "A2: el scan detecta el fixture 'npx foo link'" 'printf "%s" "$A2_OUT" | grep -q "npx foo link"'
# el mismo scan NO marca la forma pineada (guardia contra falso positivo)
printf '%s\n' 'npx --yes "foo@1.2.3" link' > "$FIX"
A2B_OUT="$(scan_floating "$FIX")"
ok "A2: el scan NO marca 'npx foo@1.2.3' (pineado)" '[ -z "$A2B_OUT" ]'

echo
echo "RESULTADO: PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
