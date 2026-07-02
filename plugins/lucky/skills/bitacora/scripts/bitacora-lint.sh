#!/usr/bin/env bash
# bitacora-lint — verifica que el INDEX no MIENTA sobre las entradas (coherencia
# mecánica INDEX↔entries/). El catálogo duplica estado/usos/validated_on en dos
# lugares (la entrada y su fila del INDEX): mantenidos a mano, divergen — y un
# INDEX que miente es DRIFT-001 aplicado a la propia bitácora (el runbook que
# miente causa el incidente que pretendía evitar).
#
# Filosofía: anti-pudrición MECÁNICO (la disciplina humana siempre falla en
# dev-solo). A diferencia de bitacora-stale (reporter fail-soft del heartbeat),
# este es un verificador FAIL-CLOSED del RITUAL DE RELEASE: la forja lo corre
# tras el leak-scan y ABORTA si el catálogo está incoherente (no se propaga por
# Ley viva un INDEX que miente a 21 repos). FRONTERA intacta: el gate de
# COMMITS (crisol_gate) sigue sin bloquear por la Bitácora — esto solo frena
# la FORJA, igual que el leak-scan. READ-ONLY: reporta, no edita.
#
# Chequea, por entrada y por fila:
#   1. bijección  — toda entries/<ID>.md tiene EXACTAMENTE una fila en INDEX.md
#                   (huérfana = sin fila; fantasma = fila sin archivo; duplicada).
#   2. título     — la 1ra línea es `## [<ID>] …` y el <ID> == nombre de archivo.
#   3. campos     — los obligatorios de la plantilla presentes (TIPO, SÍNTOMA,
#                   CAUSA-RAÍZ, ACCIÓN, ANTI-ACCIÓN, PREVENCIÓN, validated_on,
#                   stale_si, origen, usos, estado).
#   4. estado     — valor legal (CANDIDATE|LIVE|STALE|SUPERSEDED-BY:<id>|RETIRED)
#                   y ESPEJADO entrada↔INDEX.
#   5. usos       — numérico y espejado entrada↔INDEX.
#   6. fecha      — el validated_on del INDEX == fecha de la entrada.
#   7. tamaño     — ≤35 líneas (más que eso = es un ADR o un skill, no una entrada).
#   8. orden      — el INDEX ordenado por `usos` desc (lo que más duele, arriba).
#
# Uso:
#   bash bitacora-lint.sh              # skill-dir = padre de este script
#   bash bitacora-lint.sh <skill-dir>  # dir explícito (contiene INDEX.md + entries/)
# Exit: 0 = coherente (o sin bitácora que lintear); 1 = incoherencias halladas.
set -uo pipefail
export LC_ALL=C

DIR="${1:-}"
if [ -z "$DIR" ]; then
  SELF="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"
  DIR="$SELF/.."
fi
INDEX="$DIR/INDEX.md"
ENTRIES="$DIR/entries"

# Ausencia total ≠ incoherencia: sin bitácora no hay nada que lintear (fail-soft
# SOLO para la ausencia; toda incoherencia de un catálogo existente es FAIL).
if [ ! -f "$INDEX" ] && [ ! -d "$ENTRIES" ]; then
  echo "N/D — sin bitácora que lintear ($DIR)"; exit 0
fi

MAX_LINEAS=35
viol=0
flag(){ viol=$((viol+1)); echo "  ✗ $1"; }
trim(){ printf '%s' "$1" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//'; }

# estado legal → imprime el token; vacío si no hay ninguno.
estado_token(){ printf '%s' "$1" | grep -oE '(CANDIDATE|LIVE|STALE|SUPERSEDED-BY:[A-Za-z0-9_-]+|RETIRED)' | head -1; }

echo "📓 BITÁCORA-LINT — $DIR"

# ── medio catálogo = incoherencia ────────────────────────────────────────────
[ -f "$INDEX" ]   || flag "falta INDEX.md pero entries/ existe (catálogo a medias)"
[ -d "$ENTRIES" ] || flag "falta entries/ pero INDEX.md existe (catálogo a medias)"

# ── filas de datos del INDEX (las que linkean a entries/) ────────────────────
ROWS=""
[ -f "$INDEX" ] && ROWS="$(grep -E '^\|.*\]\(entries/[^)]+\.md\)' "$INDEX" || true)"

# ── por ARCHIVO de entrada ───────────────────────────────────────────────────
if [ -d "$ENTRIES" ]; then
  for f in "$ENTRIES"/*.md; do
    [ -f "$f" ] || continue
    id="$(basename "$f" .md)"

    # 1. bijección: exactamente UNA fila
    n=0
    [ -n "$ROWS" ] && n="$(printf '%s\n' "$ROWS" | grep -cF "(entries/$id.md)" || true)"
    case "$n" in
      0) flag "$id · HUÉRFANA: existe entries/$id.md pero no hay fila en INDEX" ;;
      1) : ;;
      *) flag "$id · DUPLICADA: $n filas en INDEX para la misma entrada" ;;
    esac

    # 2. título == ID
    head -1 "$f" | grep -qE "^## \[$id\]" || \
      flag "$id · TÍTULO: la 1ra línea no es '## [$id] …' (dice: '$(head -1 "$f" | cut -c1-60)')"

    # 3. campos obligatorios de la plantilla (anclados al bullet)
    grep -qE '^- \*\*TIPO:'          "$f" || flag "$id · CAMPO faltante: TIPO"
    grep -qE '^- \*\*SÍNTOMA'        "$f" || flag "$id · CAMPO faltante: SÍNTOMA"
    grep -qE '^- \*\*CAUSA-RAÍZ'     "$f" || flag "$id · CAMPO faltante: CAUSA-RAÍZ"
    grep -qE '^- \*\*ACCIÓN'         "$f" || flag "$id · CAMPO faltante: ACCIÓN"
    grep -qE '^- \*\*ANTI-ACCIÓN'    "$f" || flag "$id · CAMPO faltante: ANTI-ACCIÓN"
    grep -qE '^- \*\*PREVENCIÓN'     "$f" || flag "$id · CAMPO faltante: PREVENCIÓN"
    grep -qE '^- \*\*validated_on:'  "$f" || flag "$id · CAMPO faltante: validated_on"
    grep -qE '^- \*\*stale_si:'      "$f" || flag "$id · CAMPO faltante: stale_si"
    grep -qE '^- \*\*origen:'        "$f" || flag "$id · CAMPO faltante: origen"
    grep -qE '\*\*usos:\*\*'         "$f" || flag "$id · CAMPO faltante: usos"
    grep -qE '^- \*\*estado:\*\*'    "$f" || flag "$id · CAMPO faltante: estado"

    # valores de la entrada (para espejo con el INDEX)
    eline="$(grep -E '^- \*\*estado:\*\*' "$f" | head -1 || true)"
    e_estado="$(estado_token "$eline")"
    if [ -n "$eline" ] && [ -z "$e_estado" ]; then
      flag "$id · ESTADO ilegal: '$(trim "${eline#*estado:\*\*}")' (∉ CANDIDATE|LIVE|STALE|SUPERSEDED-BY:<id>|RETIRED)"
    fi
    e_usos="$(grep -oE '\*\*usos:\*\*[[:space:]]*[0-9]+' "$f" | grep -oE '[0-9]+' | head -1 || true)"
    vline="$(grep -E '^- \*\*validated_on' "$f" | head -1 || true)"
    vrest="${vline#*·}"   # la fecha va DESPUÉS del primer '·' (el branch puede contener fechas)
    e_fecha="$(printf '%s' "$vrest" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1 || true)"

    # 7. tamaño
    lineas="$(wc -l < "$f" | tr -d ' ')"
    [ "$lineas" -le "$MAX_LINEAS" ] || flag "$id · TAMAÑO: $lineas líneas > $MAX_LINEAS (es un ADR o un skill, no una entrada)"

    # 4/5/6. espejo entrada↔INDEX (solo si la fila es única)
    if [ "$n" = "1" ]; then
      row="$(printf '%s\n' "$ROWS" | grep -F "(entries/$id.md)")"
      nf="$(printf '%s\n' "$row" | awk -F'|' '{print NF}')"
      if [ "$nf" != "9" ]; then
        flag "$id · FILA malformada en INDEX ($((nf-2)) columnas, esperadas 7)"
      else
        i_fecha="$(trim "$(printf '%s\n' "$row" | awk -F'|' '{print $6}')")"
        i_usos="$(trim "$(printf '%s\n' "$row" | awk -F'|' '{print $7}')")"
        i_estado="$(estado_token "$(printf '%s\n' "$row" | awk -F'|' '{print $8}')")"
        [ -n "$e_estado" ] && [ "$i_estado" != "$e_estado" ] && \
          flag "$id · ESTADO desespejado: entrada='$e_estado' vs INDEX='${i_estado:-?}'"
        [ -n "$e_usos" ] && [ "$i_usos" != "$e_usos" ] && \
          flag "$id · USOS desespejado: entrada='$e_usos' vs INDEX='$i_usos'"
        [ -n "$e_fecha" ] && [ "$i_fecha" != "$e_fecha" ] && \
          flag "$id · FECHA desespejada: entrada='$e_fecha' vs INDEX='$i_fecha'"
      fi
    fi
  done
fi

# ── por FILA del INDEX: fantasmas + orden por usos desc ──────────────────────
if [ -n "$ROWS" ]; then
  prev=""
  while IFS= read -r row; do
    ref="$(printf '%s\n' "$row" | grep -oE '\(entries/[^)]+\.md\)' | head -1 | tr -d '()')"
    rid="$(basename "$ref" .md)"
    [ -f "$ENTRIES/$rid.md" ] || flag "$rid · FANTASMA: fila en INDEX pero no existe entries/$rid.md"
    u="$(trim "$(printf '%s\n' "$row" | awk -F'|' '{print $7}')")"
    case "$u" in
      ''|*[!0-9]*) flag "$rid · USOS no-numérico en INDEX ('$u')" ;;
      *) if [ -n "$prev" ] && [ "$u" -gt "$prev" ]; then
           flag "$rid · ORDEN: usos=$u arriba de usos=$prev (el INDEX va por usos desc — lo que más duele, arriba)"
         fi
         prev="$u" ;;
    esac
  done <<< "$ROWS"
fi

total_e=0; [ -d "$ENTRIES" ] && total_e="$(ls "$ENTRIES"/*.md 2>/dev/null | wc -l | tr -d ' ')"
total_r=0; [ -n "$ROWS" ] && total_r="$(printf '%s\n' "$ROWS" | wc -l | tr -d ' ')"
echo "  Entradas: $total_e · filas INDEX: $total_r · incoherencias: $viol"
if [ "$viol" -gt 0 ]; then
  echo "  → el INDEX (o una entrada) MIENTE: corregí antes de forjar (un catálogo que miente causa el incidente que pretendía evitar)."
  exit 1
fi
echo "  ✓ coherente: el INDEX dice la verdad sobre las entradas."
exit 0
