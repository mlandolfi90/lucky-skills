#!/usr/bin/env bash
# test-racionalizaciones — verifica la COSTURA entre la tabla de excusas del
# autor (docs/GUIA-SKILLS.md §Racionalizaciones) y los casos adversos reales en
# cumplimiento/escenarios/*.md. La tabla es de tentaciones, no un índice: cada
# fila debe apuntar a un escenario que EXISTE (A2); no todo escenario adverso
# necesita fila (A3 es aviso, no falla).
set -uo pipefail
export LC_ALL=C

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
GUIA="$HERE/../../../../../docs/GUIA-SKILLS.md"
ESC_DIR="$HERE/../escenarios"

pass=0; fail=0
ok(){ pass=$((pass+1)); echo "  ✅ $1"; }
no(){ fail=$((fail+1)); echo "  ❌ $1"; }

# ── Extrae las filas de datos de la sección Racionalizaciones ─────────────────
# (líneas de tabla dentro de la sección, menos el header y el separador ---)
section_rows(){
  awk 'f && /^## /{f=0} /^## Racionalizaciones/{f=1; next} f && /^\|/{print}' "$GUIA" 2>/dev/null
}

# filas de datos = líneas de tabla que NO son header ("Excusa") ni separador (---)
data_rows(){ section_rows | grep -v 'Excusa canónica' | grep -v '^\s*|[-: |]*$'; }

# ── A1: la sección existe y la tabla tiene ≥4 filas de datos ──────────────────
if grep -q '^## Racionalizaciones' "$GUIA"; then
  n_rows="$(data_rows | grep -c '.')"
  if [ "$n_rows" -ge 4 ]; then
    ok "A1: sección Racionalizaciones con $n_rows filas de datos (≥4)"
  else
    no "A1: la tabla tiene $n_rows filas de datos (se esperaban ≥4)"
  fi
else
  no "A1: no existe la sección '## Racionalizaciones' en $GUIA"
fi

# ── Ids citados en la columna 3 ("Caso adverso") ──────────────────────────────
# tercer campo entre pipes, trim de espacios
cited_ids(){
  data_rows | awk -F'|' '{gsub(/^[ \t]+|[ \t]+$/,"",$4); if($4!="") print $4}' | sort -u
}

# ── A2: cada id citado existe como `id:` en algún escenario ───────────────────
a2_fail=0
for id in $(cited_ids); do
  if grep -Rqs "id: ${id}\b" "$ESC_DIR"/*.md 2>/dev/null || \
     grep -Rqs "id: ${id}$" "$ESC_DIR"/*.md 2>/dev/null; then
    echo "     · '$id' → encontrado en escenarios/"
  else
    a2_fail=$((a2_fail+1))
    echo "     · '$id' → NO existe en ningún escenarios/*.md"
  fi
done
if [ "$a2_fail" -eq 0 ]; then
  ok "A2: todos los ids citados existen como id: en escenarios/"
else
  no "A2: $a2_fail id(s) citados no existen en escenarios/"
fi

# ── A3 (aviso, no falla): escenarios nivel 3/adverso sin fila en la tabla ─────
echo "  ℹ️  A3 (aviso): escenarios adversos no citados en la tabla ─"
cited="$(cited_ids)"
for f in "$ESC_DIR"/*.md; do
  [ -f "$f" ] || continue
  # ids cuyo bloque declara nivel 3 / adverso: id seguido (dentro del caso) de
  # una línea nivel: 3 o "adverso". Heurística: id que contiene "adverso", o
  # cualquier id declarado en un archivo donde ese id lleva "adverso" en el nombre.
  grep -oE 'id: [a-z0-9-]*adverso[a-z0-9-]*' "$f" 2>/dev/null | sed 's/^id: //' | while read -r aid; do
    [ -z "$aid" ] && continue
    if printf '%s\n' $cited | grep -qx "$aid"; then :; else
      echo "     · $aid ($(basename "$f")) — adverso sin fila (ok, la tabla es de excusas)"
    fi
  done
done

echo
echo "RESULTADO: $pass PASS · $fail FAIL"
[ "$fail" -eq 0 ]
