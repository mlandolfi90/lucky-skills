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
#   4. corre scripts/leak-scan.sh sobre el arbol (gate zero-leak, fail-closed);
#   5. firma registry.json con minisign (clave PRIVADA via Infisical/offline,
#      JAMAS hardcodeada ni en el repo) -> registry.json.minisig, y AUTO-VERIFICA
#      la firma si MINISIGN_PUBKEY esta seteada (no taggear algo que el loader
#      rechazaria).
#
# Deja TODO en el working tree para review humano (git status / git diff). NO
# commitea, NO pushea, NO crea el tag: eso lo hace el operador (MLL) bajo Crisol,
# con OK. El tag debe crearse ANOTADO (git tag -a), pero la inmutabilidad real la
# da la firma minisign del registry (ancla commit + sha256), no el tag.
#
# Entorno real: Git-Bash/PowerShell en Windows. Maneja CRLF (sed 's/\r$//' y
# normalizacion LF de los artefactos firmados), paths con espacios (todo entre
# comillas), anchor del sello ESCAPADO para ERE (grep -E / sed -E).
#
# Uso:
#   bash scripts/forjar-release.sh vX.Y.Z            # bump + registry + leak-scan + firma
#   bash scripts/forjar-release.sh vX.Y.Z --dry-run  # no escribe nada, solo reporta
#   bash scripts/forjar-release.sh vX.Y.Z --no-sign  # bump + registry + leak-scan, sin firmar
#
# Clave privada de firma (en orden de preferencia):
#   - $MINISIGN_SECRET_KEY  -> ruta a un archivo .key (lo provee Infisical en runtime)
#   - $MINISIGN_SECRET      -> contenido de la .key (Infisical lo inyecta como env);
#                             se materializa en un tmp con umask 077 y se borra (trap).
#   - si ninguna esta y no es --no-sign -> aborta pidiendo la clave (no inventa nada).
#   - $MINISIGN_PASSWORD    -> passphrase de la .key (si la clave la tiene); por stdin.
#   - $MINISIGN_PUBKEY      -> clave publica (contenido) para auto-verificar la firma.
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
TAG="${1:-}"; DRY=0; SIGN=1
shift || true
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    --no-sign) SIGN=0 ;;
    *) die "flag desconocida: $a (usa --dry-run / --no-sign)" ;;
  esac
done
[ -n "$TAG" ] || die "falta el tag. Uso: bash scripts/forjar-release.sh vX.Y.Z [--dry-run|--no-sign]"
[[ "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "tag invalido '$TAG' — formato esperado vMAJOR.MINOR.PATCH (ej. v1.9.0)"

# ── preflight de herramientas (entorno real, fallar TEMPRANO y claro) ────────
need(){ command -v "$1" >/dev/null 2>&1; }
need git       || die "git no esta en PATH."
need sha256sum || die "sha256sum no esta. Git-Bash lo trae en /usr/bin; o instala coreutils."
PYBIN=""
if need python;  then PYBIN="python";  fi
if [ -z "$PYBIN" ] && need python3; then PYBIN="python3"; fi
[ -n "$PYBIN" ] || die "python/python3 no esta en PATH (se usa para canonicalizar JSON sin jq)."
if [ "$SIGN" -eq 1 ] && [ "$DRY" -eq 0 ]; then
  need minisign || die "minisign no esta en PATH. Obtenelo:
     - scoop install minisign     (o)  choco install minisign
     - o binario de github.com/jedisct1/minisign/releases (poné el .exe en PATH)
   O corré con --no-sign para generar el registry sin firmar (firma diferida)."
fi

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
  while IFS= read -r a; do [ -n "$a" ] && SEALED+=("$a"); done < <(find "$DECISIONS_DIR" -type f -name '*.md' 2>/dev/null | sort)
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
    ("note", "Verificacion cripto la hace codigo externo (minisign -V del .minisig + sha256 -c por archivo, sobre bytes LF). El cliente NUNCA computa NI transcribe el hash. El ancla de seguridad es la FIRMA del registry (un tag movido con registry falso no valida sin la clave privada); v1 pinea por tag, el campo commit es informativo (pin-por-commit real = v2). Solo se cargan como dato las skills loadable_as_data=true; requires_runtime/requires_tools -> fast-path de install."),
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

# ── 5. firmar registry.json con minisign + auto-verificar ────────────────────
if [ "$SIGN" -eq 0 ]; then
  warn "--no-sign: registry.json SIN firmar. El loader lo rechazara hasta que lo firmes:
     minisign -S -s <clave.key> -m \"$REGISTRY\""
elif [ "$DRY" -eq 1 ]; then
  info "[dry] se firmaria: minisign -S -s <clave> -m $REGISTRY -> $REGISTRY.minisig"
else
  KEYFILE=""; KEY_IS_TMP=0
  if [ -n "${MINISIGN_SECRET_KEY:-}" ]; then
    [ -f "$MINISIGN_SECRET_KEY" ] || die "MINISIGN_SECRET_KEY apunta a un archivo inexistente: $MINISIGN_SECRET_KEY"
    KEYFILE="$MINISIGN_SECRET_KEY"
    info "firma con clave en archivo (MINISIGN_SECRET_KEY)"
  elif [ -n "${MINISIGN_SECRET:-}" ]; then
    umask 077
    KEYFILE="$(mktemp)"; KEY_IS_TMP=1
    printf '%s' "$MINISIGN_SECRET" > "$KEYFILE"
    info "firma con clave inyectada (MINISIGN_SECRET) — materializada en tmp 077, se borra al salir"
  else
    die "no hay clave privada para firmar. Sete MINISIGN_SECRET_KEY (ruta) o MINISIGN_SECRET (contenido),
   tipicamente via:  infisical run --env=dev -- bash scripts/forjar-release.sh $TAG
   O corré con --no-sign para firmar despues."
  fi
  if [ "$KEY_IS_TMP" -eq 1 ]; then
    trap 'cleanup_tmp; rm -f "$KEYFILE"' EXIT
  fi
  rm -f "$REGISTRY.minisig"
  # trusted comment lleva tag + commit (no es vinculante por si solo; el binding
  # fuerte es la firma sobre el contenido que YA ancla commit+sha256).
  TC="lucky-skills $TAG commit=$RELEASE_COMMIT"
  if [ -n "${MINISIGN_PASSWORD:-}" ]; then
    printf '%s\n' "$MINISIGN_PASSWORD" | minisign -S -s "$KEYFILE" -m "$REGISTRY" \
      -t "$TC" -c "registry de la familia lucky-skills, $TC" \
      || die "minisign fallo al firmar."
  else
    minisign -S -s "$KEYFILE" -m "$REGISTRY" \
      -t "$TC" -c "registry de la familia lucky-skills, $TC" \
      </dev/null \
      || die "minisign fallo al firmar (passphrase? sete MINISIGN_PASSWORD o corré en terminal interactiva)."
  fi
  [ -f "$REGISTRY.minisig" ] || die "minisign no produjo $REGISTRY.minisig."
  ok "registry.json firmado -> $REGISTRY.minisig"
  if [ -n "${MINISIGN_PUBKEY:-}" ]; then
    if printf '%s' "$MINISIGN_PUBKEY" | grep -q 'minisign public key\|^RW'; then
      pub_tmp="$(mktemp)"; printf '%s\n' "$MINISIGN_PUBKEY" > "$pub_tmp"
      if minisign -V -p "$pub_tmp" -m "$REGISTRY" >/dev/null 2>&1; then
        ok "auto-verificacion minisign -V con MINISIGN_PUBKEY: OK"
      else
        rm -f "$pub_tmp"; die "auto-verificacion FALLO: la firma no valida con MINISIGN_PUBKEY. NO taggear."
      fi
      rm -f "$pub_tmp"
    else
      warn "MINISIGN_PUBKEY no parece una clave publica minisign — salto la auto-verificacion."
    fi
  else
    info "MINISIGN_PUBKEY no seteada -> omito auto-verificacion (el loader la hara en runtime)."
  fi
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
echo "   4. git tag -a $TAG -m \"release $TAG\"   # TAG ANOTADO (la inmutabilidad real la da la firma del registry: ancla commit $RELEASE_COMMIT + sha256)"
echo "   5. corregir README L19 (reload-skills -> /reload-plugins) si no se hizo aun"
echo "   6. git push && git push --tags"
line
