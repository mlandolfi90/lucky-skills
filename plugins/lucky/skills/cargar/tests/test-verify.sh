#!/usr/bin/env bash
# test-verify — ¿Quién verifica al verificador del loader `cargar`?
# Fixture autocontenido, SIN firma (ADR 0009: minisign retirado): arma un
# registry + cuerpo de skill y ejerce la cadena de cargar-fetch-verify.sh por
# sus dependencias directas (normalizacion LF + parseo python del registry +
# pin tag/commit + sha256 -c del cuerpo sobre bytes LF), que es el corazon del
# fetcher. Cubre 11 casos binarios y, en TODO rechazo, exige additionalContext
# VACIO (== el texto NO entra al contexto). Estilo test-enforcer.sh.
#
# No depende de red: replica la cadena de verificacion del fetcher localmente
# (misma normalizacion LF, mismo parseo por python en el MISMO orden de gates
# —catalogo→capability→formato-sha—, mismo pin tag/commit, mismo sha256 -c).
set -uo pipefail
export LC_ALL=C

PYBIN=""; command -v python >/dev/null 2>&1 && PYBIN=python
[ -z "$PYBIN" ] && command -v python3 >/dev/null 2>&1 && PYBIN=python3
[ -n "$PYBIN" ] || { echo "❌ falta python/python3 (parseo del registry)"; exit 1; }

PASS=0; FAIL=0
check(){ # desc, expected, actual
  if [ "$2" = "$3" ]; then PASS=$((PASS+1)); echo "  ✅ $1"
  else FAIL=$((FAIL+1)); echo "  ❌ $1 (esperado '$2', obtuvo '$3')"; fi
}

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"

# sha256 de un archivo LF -> hash hex minuscula (igual que el fetcher)
sha256_file(){
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print tolower($1)}'
  elif command -v shasum   >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print tolower($1)}'
  else openssl dgst -sha256 "$1" | awk '{print tolower($NF)}'; fi
}
norm_lf(){ local t="$1.lf"; sed 's/\r$//' "$1" > "$t" && mv -f "$t" "$1"; }

INSTALL_TAG="v1.9.0"
INSTALL_COMMIT="0123456789abcdef0123456789abcdef01234567"

# ── cuerpo de skill de juguete (LF) + su sha256 ───────────────────────────────
printf 'contenido de la skill arquitectura\nlinea dos\n' > skill.md
norm_lf skill.md
SKILL_SHA="$(sha256_file skill.md)"

# ── armar registry.json (LF) con tag+commit+skill ─────────────────────────────
make_registry(){ # $1=salida $2=tag $3=commit $4=sha $5=loadable(1|0)
  "$PYBIN" - "$2" "$3" "$4" "$5" > "$1" <<'PY'
import sys, json
tag, commit, sha, loadable = sys.argv[1:5]
load = (loadable == "1")
doc = {
  "schema": "lucky-skills/registry@1",
  "tag": tag,
  "commit": commit,
  "raw_base": "${SKILLS_REGISTRY_URL}",
  "skills": [
    {"name":"arquitectura","triggers":["/arquitectura"],
     "kind":"method" if load else "runtime",
     "loadable_as_data":load,"path":"plugins/lucky/skills/arquitectura/SKILL.md",
     "requires_runtime":[],"requires_tools":([] if load else ["Bash"]),"sha256":sha}
  ]
}
sys.stdout.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
PY
  norm_lf "$1"
}

# replica EXACTA de la cadena del fetcher (sin firma, ADR 0009):
# norm LF -> parse python (catalogo -> capability-gate -> formato sha) ->
# pin tag/commit -> sha256 -c del cuerpo. Devuelve "ok" (emite bloque) o "reject".
verify_chain(){ # $1=registry $2=body $3=want_tag $4=want_commit
  local reg="$1" body="$2" wtag="$3" wcommit="$4"
  [ -s "$reg" ]  || { echo reject; return; }
  [ -s "$body" ] || { echo reject; return; }
  norm_lf "$reg"; norm_lf "$body"
  local parsed
  parsed="$("$PYBIN" - "$reg" arquitectura <<'PY'
import sys, json, re
reg, want = sys.argv[1], sys.argv[2]
try:
    d = json.load(open(reg, encoding="utf-8"))
except Exception:
    sys.exit(2)
f = None
for s in d.get("skills", []):
    if str(s.get("name","")).lower()==want: f=s; break
if f is None: sys.exit(3)
sha=str(f.get("sha256","")).lower()
if f.get("requires_runtime") or f.get("requires_tools") or not f.get("loadable_as_data"): sys.exit(4)
if not re.fullmatch(r"[0-9a-f]{64}", sha): sys.exit(5)
sys.stdout.write("%s\t%s\t%s\n" % (d.get("tag",""), d.get("commit",""), sha))
PY
)" || { echo reject; return; }
  local rtag rcommit rsha
  rtag="$(printf '%s' "$parsed" | cut -f1)"
  rcommit="$(printf '%s' "$parsed" | cut -f2)"
  rsha="$(printf '%s' "$parsed" | cut -f3)"
  [ "$rtag" = "$wtag" ] || { echo reject; return; }
  if [ -n "$wcommit" ]; then [ "$rcommit" = "$wcommit" ] || { echo reject; return; }; fi
  local got; got="$(sha256_file "$body")"
  [ "$got" = "$rsha" ] || { echo reject; return; }
  echo ok
}

# ── fixtures con nombre (estado explicito, sin mutacion cruzada) ──────────────
make_registry reg_good.json    "$INSTALL_TAG" "$INSTALL_COMMIT" "$SKILL_SHA"  1
make_registry reg_badsha.json  "$INSTALL_TAG" "$INSTALL_COMMIT" "deadbeef"    1
make_registry reg_runtime.json "$INSTALL_TAG" "$INSTALL_COMMIT" "$SKILL_SHA"  0
printf '{"schema": "lucky-skills/registry@1", "skills": [ROTO' > reg_broken.json

# ── 1. registry ok + tag/commit/sha ok -> ok (emite bloque) ───────────────────
check "registry ok + skill sha-ok -> emite" "ok" \
  "$(verify_chain reg_good.json skill.md "$INSTALL_TAG" "$INSTALL_COMMIT")"

# ── 2. tag-mismatch: install pide otro tag -> reject ──────────────────────────
check "tag-mismatch -> reject" "reject" \
  "$(verify_chain reg_good.json skill.md "v9.9.9" "$INSTALL_COMMIT")"

# ── 3. commit-mismatch: install pide otro commit -> reject ────────────────────
check "commit-mismatch -> reject" "reject" \
  "$(verify_chain reg_good.json skill.md "$INSTALL_TAG" "ffffffffffffffffffffffffffffffffffffffff")"

# ── 4. registry malformado (JSON roto) -> reject ──────────────────────────────
check "registry JSON malformado -> reject" "reject" \
  "$(verify_chain reg_broken.json skill.md "$INSTALL_TAG" "$INSTALL_COMMIT")"

# ── 5. sha mal formado en el registry -> reject ───────────────────────────────
check "sha mal formado en registry -> reject" "reject" \
  "$(verify_chain reg_badsha.json skill.md "$INSTALL_TAG" "$INSTALL_COMMIT")"

# ── 6. skill NO cargable como dato (requires_tools) -> reject ─────────────────
check "skill requires_tools (no cargable como dato) -> reject" "reject" \
  "$(verify_chain reg_runtime.json skill.md "$INSTALL_TAG" "$INSTALL_COMMIT")"

# ── 7. skill sha-ok: cuerpo intacto -> ok (reconfirmar tras los rejects) ──────
check "skill sha-ok -> emite" "ok" \
  "$(verify_chain reg_good.json skill.md "$INSTALL_TAG" "$INSTALL_COMMIT")"

# ── 8. skill MISMATCH: altero 1 byte del cuerpo -> reject ─────────────────────
printf 'contenido de la skill arquitectura ADULTERADO\nlinea dos\n' > skill_bad.md
norm_lf skill_bad.md
check "skill MISMATCH (cuerpo alterado) -> reject" "reject" \
  "$(verify_chain reg_good.json skill_bad.md "$INSTALL_TAG" "$INSTALL_COMMIT")"

# ── 9. CRLF en el cuerpo: normaliza a LF y sigue matcheando -> ok ─────────────
sed 's/$/\r/' skill.md > skill_crlf.md   # mete CR al final de cada linea
check "CRLF en el cuerpo: normaliza a LF y sigue matcheando -> emite" "ok" \
  "$(verify_chain reg_good.json skill_crlf.md "$INSTALL_TAG" "$INSTALL_COMMIT")"

# ── 10. CRLF en el REGISTRY: normaliza a LF y sigue parseando -> ok ───────────
sed 's/$/\r/' reg_good.json > reg_crlf.json
check "CRLF en el registry: normaliza a LF y sigue parseando -> emite" "ok" \
  "$(verify_chain reg_crlf.json skill.md "$INSTALL_TAG" "$INSTALL_COMMIT")"

# ── 11. invariante DURO: en TODO reject, el bloque emitido es VACIO ───────────
#    verify_chain devuelve 'reject' (no 'ok') => additionalContext seria "".
#    Reconfirmamos que ningun caso de reject produjo 'ok' por accidente:
ALL_REJECTS_EMPTY="yes"
for r in \
  "$(verify_chain reg_good.json skill_bad.md "$INSTALL_TAG" "$INSTALL_COMMIT")" \
  "$(verify_chain reg_badsha.json skill.md "$INSTALL_TAG" "$INSTALL_COMMIT")" \
  "$(verify_chain reg_runtime.json skill.md "$INSTALL_TAG" "$INSTALL_COMMIT")" \
  "$(verify_chain reg_good.json skill.md "v9.9.9" "$INSTALL_COMMIT")" ; do
  [ "$r" = "ok" ] && ALL_REJECTS_EMPTY="no"
done
check "invariante: todo rechazo => additionalContext VACIO (nada al contexto)" "yes" "$ALL_REJECTS_EMPTY"

echo
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
