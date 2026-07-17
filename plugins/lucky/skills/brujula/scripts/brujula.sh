#!/usr/bin/env bash
# brujula — ancla la sesión al estado REAL del repo y el deploy.
# REGLA DE ORO: si una fuente no se puede leer → "N/D". JAMÁS inferir.
# Solo lectura. No modifica nada.
set -uo pipefail
ND="N/D"

line(){ printf '%s\n' "────────────────────────────────"; }

# ── 1. REPO ───────────────────────────────────────────────
BRANCH="$ND"; STATUS_N="$ND"; AHEAD="$ND"; BEHIND="$ND"; EXPECTED="$ND"; TAG="$ND"; FLAG=""
if git rev-parse --git-dir >/dev/null 2>&1; then
  BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "$ND")"
  STATUS_N="$(git status --short 2>/dev/null | wc -l | tr -d ' ')"
  if git rev-parse --abbrev-ref '@{u}' >/dev/null 2>&1; then
    AHEAD="$(git rev-list --count '@{u}..HEAD' 2>/dev/null || echo "$ND")"
    BEHIND="$(git rev-list --count 'HEAD..@{u}' 2>/dev/null || echo "$ND")"
  else AHEAD="sin-remote"; BEHIND="sin-remote"; fi
  TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo "sin tags")"
  # trunk-based: lo esperado es main/master, salvo que el ledger ACTIVE diga otra cosa
  if git show-ref --verify --quiet refs/heads/main; then EXPECTED="main (trunk-based)"
  elif git show-ref --verify --quiet refs/heads/master; then EXPECTED="master (trunk-based)"
  fi
  # el RUN-LEDGER ACTIVE manda sobre el default
  LEDGER="docs/refactor/_crisol/RUN-LEDGER.md"
  if [ -f "$LEDGER" ]; then
    LB="$(awk '/^### /{e=$2} /^- STATUS:/ && /ACTIVE/ && e!=""{print e; exit}' "$LEDGER" 2>/dev/null || true)"
    [ -n "$LB" ] && EXPECTED="$LB (ledger ACTIVE)"
  fi
  # banderas duras
  [ "$BRANCH" = "HEAD" ] && FLAG="⚠️  detached HEAD — no estás en ninguna rama."
  EXP_BARE="${EXPECTED%% *}"
  if [ -z "$FLAG" ] && [ "$EXPECTED" != "$ND" ] && [ "$BRANCH" != "$EXP_BARE" ]; then
    FLAG="🚨 BRANCH INESPERADO: estás en '$BRANCH', lo esperado es '$EXPECTED'."
  fi
fi

# ── 2. DEPLOY ─────────────────────────────────────────────
DOCKER="$ND"; COMPOSE="$ND"
if docker ps >/dev/null 2>&1; then
  DOCKER="$(docker ps --format '{{.Names}} ({{.Status}})' 2>/dev/null | paste -sd', ' -)"
  [ -z "$DOCKER" ] && DOCKER="ninguno arriba"
  if ls docker-compose.y*ml compose.y*ml >/dev/null 2>&1; then
    COMPOSE="$(docker compose ps --format '{{.Name}} {{.Status}}' 2>/dev/null | paste -sd', ' - || echo "$ND")"
    [ -z "$COMPOSE" ] && COMPOSE="ninguno arriba"
  else COMPOSE="sin compose en repo"; fi
fi

# ── 3. DECISIONES ─────────────────────────────────────────
ADR="$ND"; CRISOL="$ND"
if ls docs/decisions/*.md >/dev/null 2>&1; then
  ADR="$(ls -1 docs/decisions/*.md 2>/dev/null | sort | tail -1 | xargs -r basename || echo "$ND")"
fi
if [ -f "docs/refactor/_crisol/RUN-LEDGER.md" ]; then
  if grep -m1 'STATUS: ACTIVE' docs/refactor/_crisol/RUN-LEDGER.md >/dev/null 2>&1; then
    CRISOL="activo"
    WIP="$(git log --oneline -10 2>/dev/null | grep -m1 'wip: crisol iter' || true)"
    [ -n "$WIP" ] && CRISOL="activo · corrida a medias respaldada → $WIP"
  else CRISOL="ninguno activo"; fi
fi

# ── 4. MANUAL (frescura por cursor SHA — ADR 0021 §5) ─────
# SEÑAL, no norma: "código tocado después de la última verificación del doc".
# NO detecta drift semántico (límite declarado en el ADR) — por eso dice
# "posiblemente desactualizado", jamás "drift detectado".
#
# Commits de MANTENIMIENTO excluidos del conteo. DECLARADO, con evidencia:
# forjar-release.sh re-estampa el sello de la familia en 49 archivos y el
# operador lo commitea como `crisol <T>-close:`; bajo un dir de skill esos
# commits son 1+/1- puro sello (verificado con --numstat en T1..T4-close) →
# sin este filtro la PRIMERA forja tras escribir un doc lo marcaría viejo:
# 100% de falsos positivos = señal ignorada = señal muerta (E4a).
# NO se filtra `^release`: los `release…` legacy SÍ llevan código real bajo
# dirs de skill (1c0e965 ley/SKILL.md 117+/0-) y son TODOS ancestros de la era
# v2.0.0 → inalcanzables desde cualquier cursor nacido hoy. Filtro ancho =
# falso negativo SILENCIOSO (la condena E4b); angosto = falso positivo
# ruidoso, visible, corregible. Angosto: el más angosto que mate los falsos
# positivos medidos, y ni un carácter más.
MANT_RE='^crisol [A-Za-z0-9]+-close:'
SIDECAR="docs/manual/_cobertura.yaml"
MANUAL_SEN=""
sen(){ MANUAL_SEN="${MANUAL_SEN}  ${1}"$'\n'; }

# Caso 0 (fail-open): sin git o sin docs/manual/ con piezas → se OMITE la señal
# entera; no se rompe la brújula ("sin red, sin señal", precedente de `ley atrasada`).
PIEZAS=""
if git rev-parse --git-dir >/dev/null 2>&1 && [ -d docs/manual ]; then
  # Matcher = pathspec de git, el MISMO que usa el lint. Dos matchers distintos
  # dejarían pasar un glob muerto en el lint y ciego en la brújula.
  if ! LSM="$(git ls-files -- docs/manual 2>/dev/null)"; then LSM=""; fi
  PIEZAS="$(printf '%s\n' "$LSM" | awk '/\.md$/{n=split($0,p,"/"); if (substr(p[n],1,1)!="_") print}')"
fi

if [ -n "$PIEZAS" ]; then
  NPZ="$(printf '%s\n' "$PIEZAS" | awk 'END{print NR}')"
  if [ ! -f "$SIDECAR" ]; then
    # DRIFT-001: chequeo obligatorio, jamás detrás de un `if` opcional, y HABLADO.
    # El silencio se leería como salud. La cabecera la crea la 1ra escritura del
    # manualizador-2 (ADR 0021 §5).
    sen "manual sin mapa de cobertura: $NPZ pieza(s) → falta $SIDECAR (lo crea el manualizador-2)"
  # FALSO-VERDE-004: el awk que DECIDE corre SIN pipe; salida capturada, $? desnudo.
  elif ! MAPA="$(awk '
      function lst(s,   a,b,r){ a=index(s,"["); b=index(s,"]");
                                if(a==0||b==0) return "!"          # block-style: awk NO lo lee
                                r=substr(s,a+1,b-a-1); gsub(/,/," ",r); return r }
      /^piezas:[[:space:]]*$/                            { inp=1; next }
      inp && /^[^[:space:]]/                             { inp=0 }
      inp && /^[[:space:]]*-[[:space:]]+doc:[[:space:]]/ { d=$3; c="!"; p="!"; next }
      inp && /^[[:space:]]+cubre:/                       { c=lst($0); next }
      inp && /^[[:space:]]+deps:/                        { p=lst($0); next }
      inp && /^[[:space:]]+verificado_en:[[:space:]]/ && d!="" {
              if (c=="!" || p=="!") { print "?\t" d; d=""; next }
              print $2 "\t" d "\t" c " " p; d="" }
    ' "$SIDECAR" 2>/dev/null)"; then
    sen "cobertura: $ND (sidecar ilegible)"                       # REGLA DE ORO
  elif [ -z "$MAPA" ]; then
    sen "cobertura: $ND (sidecar ilegible)"
  else
    # Here-string, NO pipe: `while read` detrás de un pipe corre en SUBSHELL y
    # las señales acumuladas por sen() se perderían al cerrar el bucle.
    while IFS=$'\t' read -r SHA DOC GLOBS; do
      [ -z "$SHA" ] && continue
      if [ "$SHA" = "?" ]; then
        sen "cobertura rota: $DOC — cubre/deps no está en flow-style [a, b] de una línea"
        continue
      fi
      ROTO=""
      for g in $GLOBS; do          # sin comillas A PROPÓSITO: split a pathspecs
        if ! OUT="$(git ls-files -- "$g" 2>/dev/null)"; then OUT=""; fi
        # `git ls-files` sale 0 aun SIN matches: la decisión de "glob muerto" es
        # por CONTENIDO vacío, no por exit code. Deliberado y documentado.
        if [ -z "$OUT" ]; then
          sen "cobertura rota: $DOC declara $g inexistente"
          ROTO=1
        fi
      done
      [ -n "$ROTO" ] && continue
      if ! CNT="$(git rev-list --count --extended-regexp --invert-grep \
                  --grep="$MANT_RE" "$SHA..HEAD" -- $GLOBS 2>/dev/null)"; then
        sen "cobertura: $ND ($DOC — cursor ${SHA:0:7} no resuelve)"
        continue
      fi
      case "$CNT" in
        ''|*[!0-9]*) sen "cobertura: $ND ($DOC — conteo ilegible)" ;;
        0)           : ;;
        *)           sen "manual posiblemente desactualizado: $DOC ($CNT commit(s) desde ${SHA:0:7})" ;;
      esac
    done <<< "$MAPA"
  fi
fi

# ── SNAPSHOT ──────────────────────────────────────────────
[ -n "$FLAG" ] && { echo "$FLAG"; line; }
echo "📍 BRÚJULA — estás acá:"
echo "  Repo     : branch '$BRANCH' · $STATUS_N archivo(s) sin commitear · ↑$AHEAD ↓$BEHIND vs remote"
echo "  Release  : último tag → $TAG"
echo "  Esperado : $EXPECTED"
echo "  Deploy   : docker → $DOCKER"
echo "             compose → $COMPOSE"
echo "  Decisión : último ADR → $ADR · Crisol → $CRISOL"
[ -n "$MANUAL_SEN" ] && printf '%s' "$MANUAL_SEN"
line
echo "(N/D = no se pudo leer esa fuente; NO se infiere)"
