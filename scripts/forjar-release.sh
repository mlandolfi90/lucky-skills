#!/usr/bin/env bash
# forjar-release — ritual de release de la familia lucky-skills.
#
# Hace, en orden y SIN commitear:
#   1. enumera las skills de la familia y las clasifica:
#        - puro-metodo-autocontenido  -> kind=method,  loadable_as_data=true
#        - depende de tools de ejecucion (Bash/Write/Edit/...) -> requires_tools / requires_runtime,
#          loadable_as_data=false (el loader las RECHAZA como dato y rutea al fast-path);
#   2. bumpea el sello `vX.Y.Z` en CADA SKILL.md (5 skills + cargar), en cada
#      reference de cargar (references/*.md) y en docs/decisions/*.md, y VERIFICA
#      que TODOS los sellos queden consistentes con el tag objetivo
#      (salda la deuda RUN-LEDGER "bump N sellos a mano");
#   3. computa sha256 de cada SKILL.md (y de las references de cargar) y genera
#      registry.json (manifiesto liviano): schema, tag, commit=git rev-parse HEAD,
#      raw_base parametrizado, y por skill kind/loadable_as_data/requires_runtime/
#      requires_tools/path/url/sha256. La url es raw@COMMIT (inmutable de verdad;
#      un tag git es MUTABLE con `git -f`). El cliente verifica raw@commit;
#   4. corre scripts/leak-scan.sh sobre el arbol (gate zero-leak, fail-closed) y
#      bitacora-lint.sh (coherencia INDEX<->entradas de la bitacora, fail-closed).
#
# La firma minisign fue RETIRADA (ADR 0009, dueño unico del repo): el release ya
# NO firma nada. La integridad la dan los sha256 por archivo + el pin por commit
# del registry, verificados por codigo en el cliente (cargar-fetch-verify.sh).
#
# Deja TODO en el working tree para review humano (git status / git diff). NO
# commitea, NO pushea, NO crea el tag: eso lo hace el operador (MLL) bajo Crisol,
# con OK. El tag debe crearse ANOTADO (git tag -a); el ancla inmutable real es el
# COMMIT que el registry pinea (un tag es mutable con git -f).
#
# Entorno real: Git-Bash/PowerShell en Windows. Maneja CRLF (sed 's/\r$//' y
# normalizacion LF de los artefactos firmados), paths con espacios (todo entre
# comillas), anchor del sello ESCAPADO para ERE (grep -E / sed -E).
#
# Uso:
#   bash scripts/forjar-release.sh vX.Y.Z            # bump + registry + leak-scan
#   bash scripts/forjar-release.sh vX.Y.Z --dry-run  # no escribe nada, solo reporta
#   (--no-sign quedo OBSOLETA: se acepta como no-op con aviso — la firma ya no existe)
#
# Entorno:
#   - $SKILLS_REGISTRY_URL  -> ancla del catalogo; si falta, el registry usa el token
#                             ${SKILLS_REGISTRY_URL} literal (zero-leak; no hornea valor).
#
set -euo pipefail
export PYTHONIOENCODING=utf-8   # Windows: cp1252 no imprime ciertos caracteres del reporte

# ── ubicacion: el script vive en <repo>/scripts/ ─────────────────────────────
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
cd -- "$REPO_ROOT"

SKILLS_DIR="plugins/lucky/skills"
REGISTRY="$SKILLS_DIR/registry.json"
LEAK_SCAN="$SCRIPT_DIR/leak-scan.sh"
DECISIONS_DIR="docs/decisions"
CARGAR_REFS_DIR="$SKILLS_DIR/cargar/references"

# ── helpers de salida ────────────────────────────────────────────────────────
ok(){   printf '  OK %s\n' "$*"; }
info(){ printf '  .  %s\n' "$*"; }
warn(){ printf '  !! %s\n' "$*" >&2; }
die(){  printf 'XX %s\n' "$*" >&2; exit 1; }
line(){ printf '%s\n' "------------------------------------------------"; }

# ── args ─────────────────────────────────────────────────────────────────────
TAG="${1:-}"; DRY=0
shift || true
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    --no-sign) warn "--no-sign quedo obsoleta: la firma fue retirada (ADR 0009); ignorada." ;;
    *) die "flag desconocida: $a (usa --dry-run)" ;;
  esac
done
[ -n "$TAG" ] || die "falta el tag. Uso: bash scripts/forjar-release.sh vX.Y.Z [--dry-run]"
[[ "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "tag invalido '$TAG' — formato esperado vMAJOR.MINOR.PATCH (ej. v1.9.0)"

# ── preflight de herramientas (entorno real, fallar TEMPRANO y claro) ────────
need(){ command -v "$1" >/dev/null 2>&1; }
need git       || die "git no esta en PATH."
need sha256sum || die "sha256sum no esta. Git-Bash lo trae en /usr/bin; o instala coreutils."
PYBIN=""
if need python;  then PYBIN="python";  fi
if [ -z "$PYBIN" ] && need python3; then PYBIN="python3"; fi
[ -n "$PYBIN" ] || die "python/python3 no esta en PATH (se usa para canonicalizar JSON sin jq)."

# ── el repo debe ser git y el tag NO debe existir aun ────────────────────────
git rev-parse --git-dir >/dev/null 2>&1 || die "no es un repo git."
git fetch --tags --quiet 2>/dev/null || warn "no se pudieron fetchear tags (sin red?) — sigo con lo local."
if git rev-parse "$TAG" >/dev/null 2>&1; then
  die "el tag '$TAG' YA existe. Un release no re-taggea: bumpea a la siguiente version, o borra el tag a mano si fue un error."
fi

# COMMIT del release: ancla inmutable de verdad (un tag es mutable con git -f).
RELEASE_COMMIT="$(git rev-parse HEAD)"
[[ "$RELEASE_COMMIT" =~ ^[0-9a-f]{40}$ ]] || die "git rev-parse HEAD no devolvio un SHA40 valido."

line
printf 'FORJANDO RELEASE %s%s\n' "$TAG" "$([ "$DRY" -eq 1 ] && echo '  (DRY-RUN, no escribe nada)')"
printf '   repo:   %s\n' "$REPO_ROOT"
printf '   commit: %s\n' "$RELEASE_COMMIT"
line

# ── 1. enumerar skills y clasificar metodo-autocontenido vs depende-de-tools ─
# requires_runtime: la skill necesita que el HARNESS le monte algo que el texto
#   no reproduce -> escritura/orquestacion (Write/Edit/MultiEdit/Agent/SendMessage/
#   TodoWrite), disable-model-invocation:true, o un hook enforcer/fetcher.
# requires_tools: la skill DEPENDE de ejecutar tools (Bash) para cumplir su metodo;
#   inyectada como dato es prosa inerte que apunta a comandos que el runtime no
#   puede correr -> tambien castrada (viola invariante 4), NO cargable como dato.
# Solo method+loadable=true: puro-texto-autocontenido (no depende de ejecutar nada).
RUNTIME_TOOLS='Write|Edit|MultiEdit|Agent|SendMessage|TodoWrite'
TOOLS_DEP='Bash'

frontmatter(){ awk 'NR==1&&$0!~/^---/{exit} /^---[[:space:]]*$/{c++; next} c==1{print} c>=2{exit}' "$1" | sed 's/\r$//'; }
fm_value(){ frontmatter "$1" | awk -v k="$2" 'BEGIN{FS=":"} $1==k{ $1=""; sub(/^:[[:space:]]*/,""); sub(/^[[:space:]]+/,""); print; exit }'; }

declare -a SKILLS=()
declare -A RR_OF=()   # name -> lista requires_runtime (espacios)
declare -A RT_OF=()   # name -> lista requires_tools (espacios)
declare -A KIND_OF=() # name -> method|runtime

for d in "$SKILLS_DIR"/*/; do
  sk="$(basename "$d")"
  f="$d/SKILL.md"
  [ -f "$f" ] || { warn "skill '$sk' tiene carpeta pero NO SKILL.md."; \
                   die "carpeta de skill a medio crear: $d (aborto antes de firmar)."; }
  SKILLS+=("$sk")
  rr=""; rt=""

  dmi="$(fm_value "$f" "disable-model-invocation")"
  [ "$dmi" = "true" ] && rr="${rr:+$rr }disable-invocation"

  declared_rr="$(fm_value "$f" "requires-runtime")"
  if [ -n "$declared_rr" ]; then
    for w in $declared_rr; do rr="${rr:+$rr }$w"; done
  fi

  tools="$(fm_value "$f" "allowed-tools")"
  if printf '%s' "$tools" | grep -Eq "(^|[ ,])($RUNTIME_TOOLS)([ ,]|\$)"; then
    rr="${rr:+$rr }allowed-tools-extra"
  fi
  if printf '%s' "$tools" | grep -Eq "(^|[ ,])($TOOLS_DEP)([ ,]|\$)"; then
    rt="${rt:+$rt }Bash"
  fi

  # hooks/*.sh|*.py -> enforcer/fetcher/gate de runtime (crisol: enforcer.sh +
  # gate.py global; cargar: fetcher.sh).
  if ls "$d"hooks/*.sh >/dev/null 2>&1 || ls "$d"hooks/*.py >/dev/null 2>&1; then
    rr="${rr:+$rr }hooks"
  fi

  # dedup conservando orden
  dedup(){ awk 'BEGIN{RS=" "} $0!="" && !seen[$0]++{printf "%s%s",(c++?" ":""),$0}'; }
  rr="$(printf '%s' "$rr" | dedup)"
  rt="$(printf '%s' "$rt" | dedup)"

  RR_OF["$sk"]="$rr"
  RT_OF["$sk"]="$rt"
  if [ -n "$rr" ] || [ -n "$rt" ]; then
    KIND_OF["$sk"]="runtime"
    info "NO cargable: $sk  (requires_runtime=[$rr] requires_tools=[$rt]) -> registro lo marca; loader rutea al fast-path"
  else
    KIND_OF["$sk"]="method"
    ok "puro-metodo-autocontenido: $sk (cargable como dato)"
  fi
done
[ "${#SKILLS[@]}" -gt 0 ] || die "no encontre skills en $SKILLS_DIR."
line

# ── 2. bumpear el sello vX.Y.Z + VERIFICAR consistencia (5 skills + cargar +
#      references de cargar + docs/decisions/*.md) ─────────────────────────────
# Anchor con parens ESCAPADOS para ERE (grep -E / sed -E): los '()' literales son
# grupos en ERE -> escaparlos o no matchea. crisol cierra distinto tras el sello
# ("** **Ley viva:**") pero el ancla `vX.Y.Z` (cache local, NO la ley) es identica.
SELLO_ANCLA_RE='\(cache local, NO la ley\)'

# Universo de archivos sellados: todos los SKILL.md, references de cargar, ADRs.
declare -a SEALED=()
for sk in "${SKILLS[@]}"; do SEALED+=("$SKILLS_DIR/$sk/SKILL.md"); done
if [ -d "$CARGAR_REFS_DIR" ]; then
  while IFS= read -r r; do [ -n "$r" ] && SEALED+=("$r"); done < <(find "$CARGAR_REFS_DIR" -type f -name '*.md' 2>/dev/null | sort)
fi
if [ -d "$DECISIONS_DIR" ]; then
  # INDEX.md es PROYECCIÓN generada (ADR 0016): no lleva sello — se excluye.
  while IFS= read -r a; do [ -n "$a" ] && SEALED+=("$a"); done < <(find "$DECISIONS_DIR" -type f -name '*.md' ! -name 'INDEX.md' 2>/dev/null | sort)
fi

# PRE-FLIGHT: validar EXACTAMENTE 1 sello ancla en TODOS los archivos ANTES de
# tocar ninguno. Asi un archivo sin sello aborta con CERO escrituras (transaccional).
for f in "${SEALED[@]}"; do
  n="$(grep -cE "\`v[0-9]+\.[0-9]+\.[0-9]+\` $SELLO_ANCLA_RE" "$f" || true)"
  [ "$n" = "1" ] || die "archivo '$f': esperaba EXACTAMENTE 1 sello ancla \`vX.Y.Z\` (cache local, NO la ley), encontre $n. No bumpeo a ciegas (cero archivos tocados)."
done
ok "pre-flight: ${#SEALED[@]} archivo(s) sellado(s) con exactamente 1 ancla"

bump_count=0
for f in "${SEALED[@]}"; do
  cur="$(grep -nE "\`v[0-9]+\.[0-9]+\.[0-9]+\` $SELLO_ANCLA_RE" "$f" | head -1 || true)"
  curver="$(printf '%s' "$cur" | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
  if [ "$curver" = "$TAG" ]; then
    info "sello $f ya en $TAG (idempotente, sin cambios)"
    continue
  fi
  if [ "$DRY" -eq 1 ]; then
    info "[dry] bump $f: $curver -> $TAG"
    bump_count=$((bump_count+1))
    continue
  fi
  tmp="$(mktemp)"
  sed -E "s/\`v[0-9]+\.[0-9]+\.[0-9]+\` $SELLO_ANCLA_RE/\`$TAG\` (cache local, NO la ley)/" "$f" > "$tmp"
  if grep -qE "\`$TAG\` $SELLO_ANCLA_RE" "$tmp" && [ "$(grep -oE "\`v[0-9]+\.[0-9]+\.[0-9]+\` $SELLO_ANCLA_RE" "$tmp" | grep -vc "$TAG")" = "0" ]; then
    mv "$tmp" "$f"
    ok "bump $f: $curver -> $TAG"
    bump_count=$((bump_count+1))
  else
    rm -f "$tmp"
    die "archivo '$f': el reemplazo del sello no quedo consistente — abortando sin tocar el archivo."
  fi
done

inconsist=0
for f in "${SEALED[@]}"; do
  if [ "$DRY" -eq 1 ]; then continue; fi
  got="$(grep -oE "\`v[0-9]+\.[0-9]+\.[0-9]+\` $SELLO_ANCLA_RE" "$f" | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
  if [ "$got" != "$TAG" ]; then
    warn "INCONSISTENCIA: $f tiene sello '$got', se esperaba '$TAG'"
    inconsist=$((inconsist+1))
  fi
done
[ "$inconsist" -eq 0 ] || die "$inconsist sello(s) inconsistente(s) con $TAG. Release ABORTADO (deuda de sellos NO saldada)."
[ "$DRY" -eq 1 ] && info "[dry] $bump_count sello(s) se bumpearian a $TAG" || ok "$bump_count sello(s) bumpeado(s); los ${#SEALED[@]} archivos sellados consistentes con $TAG"
line

# ── 2b. sincronizar plugin.json.version con el tag ───────────────────────────
# Sin esto la version del plugin queda fija (1.0.0 historico) y el instalador de
# plugins del harness JAMAS ve "version nueva" -> el cache instalado se congela
# al commit del dia del install (incidente 2026-07-04). El tag manda: version =
# TAG sin la 'v'. Transaccional: valida el JSON resultante antes de mover.
PLUGIN_JSON="plugins/lucky/.claude-plugin/plugin.json"
[ -f "$PLUGIN_JSON" ] || die "no existe $PLUGIN_JSON — el plugin perdio su manifiesto"
PLUGIN_VER="${TAG#v}"
cur_pver="$("$PYBIN" -c "import json,sys;print(json.load(open(sys.argv[1],encoding='utf-8')).get('version',''))" "$PLUGIN_JSON")"
if [ "$cur_pver" = "$PLUGIN_VER" ]; then
  info "plugin.json ya en version $PLUGIN_VER (idempotente, sin cambios)"
elif [ "$DRY" -eq 1 ]; then
  info "[dry] plugin.json: $cur_pver -> $PLUGIN_VER"
else
  tmp="$(mktemp)"
  "$PYBIN" - "$PLUGIN_JSON" "$PLUGIN_VER" > "$tmp" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
d["version"] = sys.argv[2]
print(json.dumps(d, indent=2, ensure_ascii=False))
PY
  "$PYBIN" -c "import json,sys;json.load(open(sys.argv[1],encoding='utf-8'))" "$tmp" || { rm -f "$tmp"; die "plugin.json resultante invalido — abortando sin tocar el archivo"; }
  mv "$tmp" "$PLUGIN_JSON"
  ok "plugin.json: $cur_pver -> $PLUGIN_VER"
fi
line

# ── 3. computar sha256 + generar registry.json (raw@commit, no raw@tag) ──────
# RAW_BASE: unico ancla. Si SKILLS_REGISTRY_URL no esta en env, NO se hornea un
# valor: queda el token literal ${SKILLS_REGISTRY_URL} (zero-leak; el cliente lo
# resuelve en runtime via Infisical). La url se compone raw@COMMIT (inmutable).
RAW_BASE="${SKILLS_REGISTRY_URL:-\${SKILLS_REGISTRY_URL}}"

HASHES_TSV="$(mktemp)"; META_TSV="$(mktemp)"
cleanup_tmp(){ rm -f "$HASHES_TSV" "$META_TSV"; }
trap cleanup_tmp EXIT

# sha256 sobre bytes NORMALIZADOS A LF: el cliente (cargar-fetch-verify.sh) verifica
# tras normalizar CRLF->LF, y el raw del repo sirve LF (via .gitattributes). Hashear
# el mismo byte-stream LF = paridad determinista en Windows (invariante 7).
sha256_lf(){ sed 's/\r$//' "$1" | sha256sum | awk '{print $1}'; }

for sk in "${SKILLS[@]}"; do
  f="$SKILLS_DIR/$sk/SKILL.md"
  h="$(sha256_lf "$f")"
  printf '%s\t%s\t%s\n' "$sk" "$h" "$f" >> "$HASHES_TSV"
  printf '%s\t%s\t%s\t%s\n' "$sk" "${KIND_OF[$sk]}" "${RR_OF[$sk]}" "${RT_OF[$sk]}" >> "$META_TSV"
done
# references de cargar: capas de carga progresiva, cada una con su sha256, kind=method.
if [ -d "$CARGAR_REFS_DIR" ]; then
  while IFS= read -r r; do
    [ -n "$r" ] || continue
    rid="cargar/$(basename "${r%.md}").ref"
    h="$(sha256_lf "$r")"
    printf '%s\t%s\t%s\n' "$rid" "$h" "$r" >> "$HASHES_TSV"
    printf '%s\t%s\t%s\t%s\n' "$rid" "method" "" "" >> "$META_TSV"
  done < <(find "$CARGAR_REFS_DIR" -type f -name '*.md' 2>/dev/null | sort)
fi

REGISTRY_JSON="$("$PYBIN" - "$TAG" "$RELEASE_COMMIT" "$RAW_BASE" "$HASHES_TSV" "$META_TSV" <<'PY'
import sys, json, collections
# Windows: python en modo texto traduce \n -> \r\n al escribir stdout. El registry
# se firma/verifica byte-a-byte (raw servido con LF) -> forzamos LF.
try: sys.stdout.reconfigure(newline="\n")
except Exception: pass
tag, commit, raw_base, hashes_tsv, meta_tsv = sys.argv[1:6]

meta = {}
with open(meta_tsv, encoding="utf-8") as fh:
    for ln in fh:
        ln = ln.rstrip("\n")
        if not ln: continue
        parts = ln.split("\t")
        name = parts[0]
        kind = parts[1] if len(parts) > 1 else "method"
        rr   = parts[2].split() if len(parts) > 2 and parts[2] else []
        rt   = parts[3].split() if len(parts) > 3 and parts[3] else []
        meta[name] = (kind, rr, rt)

skills = []
with open(hashes_tsv, encoding="utf-8") as fh:
    for ln in fh:
        ln = ln.rstrip("\n")
        if not ln: continue
        name, sha, path = ln.split("\t")
        kind, rr, rt = meta.get(name, ("method", [], []))
        loadable = (kind == "method" and not rr and not rt)
        # url anclada por TAG (v1); el ancla de seguridad es la FIRMA del registry
        url = f"{raw_base}/{tag}/{path}"
        skills.append(collections.OrderedDict([
            ("name", name),
            ("kind", kind),
            ("loadable_as_data", loadable),
            ("requires_runtime", rr),
            ("requires_tools", rt),
            ("path", path),
            ("url", url),
            ("sha256", sha),
        ]))
skills.sort(key=lambda s: s["name"])
doc = collections.OrderedDict([
    ("schema", "lucky-skills/registry@1"),
    ("tag", tag),
    ("commit", commit),
    ("raw_base", raw_base),
    ("note", "Verificacion de integridad por codigo externo: sha256 -c por archivo, sobre bytes LF, contra este registry traido raw@REF del install. El cliente NUNCA computa NI transcribe el hash. La firma minisign fue RETIRADA (ADR 0009, dueño unico del repo; vuelve si el trade-off cambia): el ancla es el PIN que fija el install en state.env — v1 pinea por TAG; el campo commit es informativo (la forja corre pre-commit; pin-por-commit real = v2). Solo se cargan como dato las skills loadable_as_data=true; requires_runtime/requires_tools -> fast-path de install."),
    ("skills", skills),
])
sys.stdout.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
PY
)"
# Defensa extra: LF puro pase lo que pase (el cliente verifica bytes).
REGISTRY_JSON="$(printf '%s' "$REGISTRY_JSON" | tr -d '\r')"

if [ "$DRY" -eq 1 ]; then
  info "[dry] registry.json que se generaria:"
  printf '%s\n' "$REGISTRY_JSON" | sed 's/^/      /'
else
  printf '%s\n' "$REGISTRY_JSON" > "$REGISTRY"
  ok "registry.json generado ($REGISTRY) — ${#SKILLS[@]} skills, pin commit ${RELEASE_COMMIT:0:12} (tag $TAG)"
fi
line

# ── 4. leak-scan (gate zero-leak fail-closed) ────────────────────────────────
if [ -f "$LEAK_SCAN" ]; then
  info "corriendo leak-scan sobre el arbol..."
  if bash "$LEAK_SCAN"; then
    ok "leak-scan LIMPIO"
  else
    die "leak-scan encontro HALLAZGOS. Release ABORTADO — limpia antes de firmar/taggear."
  fi
else
  warn "no encontre $LEAK_SCAN — SALTEO el gate zero-leak (recomendado tenerlo)."
fi
line

# ── 4b. bitacora-lint (coherencia INDEX↔entradas, fail-closed) ───────────────
# La bitacora viaja con el tag a los ~21 repos (Ley viva): no se forja un INDEX
# que MIENTE sobre sus entradas (estado/usos/fecha desespejados, huerfanas,
# fantasmas). Mismo rango que el leak-scan: aborta la FORJA; el gate de commits
# sigue sin bloquear por la Bitacora (frontera ADR 0005 intacta).
BITACORA_LINT="$SKILLS_DIR/bitacora/scripts/bitacora-lint.sh"
if [ -f "$BITACORA_LINT" ]; then
  info "corriendo bitacora-lint (coherencia INDEX<->entradas)..."
  if bash "$BITACORA_LINT"; then
    ok "bitacora coherente (el INDEX dice la verdad)"
  else
    die "bitacora INCOHERENTE. Release ABORTADO — un catalogo que miente causa el incidente que pretendia evitar."
  fi
else
  info "sin skill bitacora en este arbol — salteo el lint (no aplica)."
fi
line

# ── 4c. sistema de registros (ADR 0016): lint + no-drift de proyecciones ─────
REGISTROS_LINT="$SCRIPT_DIR/registros-lint.py"
PROYECTAR="$SCRIPT_DIR/proyectar.py"
if [ -f "$REGISTROS_LINT" ]; then
  info "corriendo registros-lint (manifiesto <-> realidad)..."
  if "$PYBIN" "$REGISTROS_LINT" --repo "$REPO_ROOT"; then
    ok "registros coherentes (0 huerfanos, frontmatter valido, sellos integros)"
  else
    die "registros-lint encontro HALLAZGOS. Release ABORTADO — el manifiesto y la realidad divergen."
  fi
fi
if [ -f "$PROYECTAR" ]; then
  info "verificando proyecciones (sin drift filas <-> RUN-LEDGER/_ACTIVE/INDEX)..."
  if "$PYBIN" "$PROYECTAR" --repo "$REPO_ROOT" --check; then
    ok "proyecciones byte-identicas a sus filas"
  else
    die "DRIFT de proyecciones. Regenera con 'python scripts/proyectar.py' y commitea junto a las filas."
  fi
fi
line

# ── 4d. sellar corridas en estado terminal (sha256 LF -> sellos.json) ─────────
# Patron Flyway: la historia cerrada queda sellada; editar una corrida CLOSED
# rompe el sello y el lint lo delata (metrica M8). Sello existente que no
# matchea = historia editada -> ABORTA. Sello nuevo = se agrega (idempotente).
RUNS_DIR="docs/refactor/_crisol/runs"
SELLOS_JSON="docs/refactor/_crisol/sellos.json"
if [ -d "$RUNS_DIR" ]; then
  if [ "$DRY" -eq 1 ]; then
    info "[dry] sellaria corridas terminales de $RUNS_DIR en $SELLOS_JSON"
  else
    "$PYBIN" - "$RUNS_DIR" "$SELLOS_JSON" <<'PY' || die "sellado de corridas FALLO (¿historia editada?). Release ABORTADO."
import hashlib, json, re, sys
from pathlib import Path
runs, sellos_p = Path(sys.argv[1]), Path(sys.argv[2])
doc = {"schema": "lucky-sellos/1", "sellos": {}}
if sellos_p.is_file():
    doc = json.loads(sellos_p.read_text(encoding="utf-8"))
    doc.setdefault("sellos", {})
front = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
estado_re = re.compile(r"^estado:\s*([A-Z_]+)\s*$", re.MULTILINE)
nuevos = 0
for p in sorted(runs.glob("*.md")):
    if p.name.startswith("_archivo"):
        continue
    m = front.match(p.read_text(encoding="utf-8-sig", errors="replace"))
    if not m:
        continue
    e = estado_re.search(m.group(1))
    if not e or e.group(1) not in ("CLOSED", "ESCALATED"):
        continue
    clave = f"corrida:{p.stem}"
    h = hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    prev = doc["sellos"].get(clave)
    if prev is None:
        doc["sellos"][clave] = h
        nuevos += 1
        print(f"  OK sello nuevo: {clave} = {h[:12]}...")
    elif prev != h:
        print(f"XX sello ROTO: {clave} — la corrida cambio tras sellarse.", file=sys.stderr)
        sys.exit(1)
doc["sellos"] = dict(sorted(doc["sellos"].items()))
with open(sellos_p, "w", encoding="utf-8", newline="\n") as f:
    json.dump(doc, f, indent=2, ensure_ascii=False)
    f.write("\n")
print(f"  OK sellos.json: {len(doc['sellos'])} sello(s), {nuevos} nuevo(s)")
PY
    ok "corridas terminales selladas ($SELLOS_JSON)"
  fi
fi
line

# ── 5. limpiar restos de firma (ADR 0009: el release ya no produce .minisig) ─
if [ "$DRY" -eq 0 ] && [ -f "$REGISTRY.minisig" ]; then
  rm -f "$REGISTRY.minisig"
  ok "resto de firma eliminado: $REGISTRY.minisig (ADR 0009)"
fi
line

echo "Listo para REVIEW (nada commiteado, nada pusheado, sin tag creado):"
echo
[ "$DRY" -eq 0 ] && git -c color.ui=always status --short "$SKILLS_DIR" "$DECISIONS_DIR" 2>/dev/null | sed 's/^/   /' || true
echo
echo "Proximos pasos (los hace el operador MLL, bajo Crisol, con OK):"
echo "   1. git diff $SKILLS_DIR $DECISIONS_DIR"
echo "   2. correr el Crisol sobre el cambio (Verificador: grep de sellos == $TAG; leak-scan limpio)"
echo "   3. git add -A && git commit"
echo "   4. git tag -a $TAG -m \"release $TAG\"   # TAG ANOTADO (ancla inmutable real: commit $RELEASE_COMMIT pineado en el registry + sha256)"
echo "   5. corregir README L19 (reload-skills -> /reload-plugins) si no se hizo aun"
echo "   6. git push && git push --tags"
line
