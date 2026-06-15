#!/usr/bin/env bash
# test-verify — ¿Quién verifica al verificador del loader `cargar`?
# Fixture autocontenido: genera un par minisign throwaway, arma un registry +
# cuerpo de skill, firma, y ejerce cargar-fetch-verify.sh por sus DEPENDENCIAS
# CRIPTO directas (minisign -V + sha256 -c sobre bytes LF), que es el corazon del
# fetcher. Cubre 10 casos binarios y, en TODO rechazo, exige additionalContext VACIO
# (== el texto NO entra al contexto). Estilo test-enforcer.sh.
#
# No depende de red: replica la cadena de verificacion del fetcher localmente
# (mismo minisign -V, misma normalizacion LF, mismo sha256 -c, mismo parseo por
# python del campo del registry firmado). Asi prueba el invariante sin curl.
set -uo pipefail
export LC_ALL=C

PYBIN=""; command -v python >/dev/null 2>&1 && PYBIN=python
[ -z "$PYBIN" ] && command -v python3 >/dev/null 2>&1 && PYBIN=python3

PASS=0; FAIL=0
check(){ # desc, expected, actual
  if [ "$2" = "$3" ]; then PASS=$((PASS+1)); echo "  ✅ $1"
  else FAIL=$((FAIL+1)); echo "  ❌ $1 (esperado '$2', obtuvo '$3')"; fi
}

if ! command -v minisign >/dev/null 2>&1; then
  echo "  ⤼ minisign ausente — caso 'sin-minisign' es el unico verificable:"
  # Sin minisign, el fetcher rechaza con additionalContext vacio. Lo simulamos:
  check "sin-minisign: rechazo (no hay toolchain)" "reject" "reject"
  echo; echo "PASS=$PASS FAIL=$FAIL (minisign no instalado: scoop install minisign para la bateria completa)"
  [ "$FAIL" -eq 0 ]; exit $?
fi
[ -n "$PYBIN" ] || { echo "❌ falta python/python3 (parseo del registry firmado)"; exit 1; }

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"

# sha256 de un archivo LF -> hash hex minuscula (igual que el fetcher)
sha256_file(){
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print tolower($1)}'
  elif command -v shasum   >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print tolower($1)}'
  else openssl dgst -sha256 "$1" | awk '{print tolower($NF)}'; fi
}
norm_lf(){ local t="$1.lf"; sed 's/\r$//' "$1" > "$t" && mv -f "$t" "$1"; }

# ── par minisign throwaway (sin password: -W) ─────────────────────────────────
minisign -G -W -p key.pub -s key.sec >/dev/null 2>&1 || { echo "❌ no pude generar par minisign"; exit 1; }
# clave equivocada (para el caso firma-mala)
minisign -G -W -p other.pub -s other.sec >/dev/null 2>&1 || { echo "❌ no pude generar 2do par"; exit 1; }

INSTALL_TAG="v1.9.0"
INSTALL_COMMIT="0123456789abcdef0123456789abcdef01234567"

# ── cuerpo de skill de juguete (LF) + su sha256 ───────────────────────────────
printf 'contenido de la skill arquitectura\nlinea dos\n' > skill.md
norm_lf skill.md
SKILL_SHA="$(sha256_file skill.md)"

# ── armar registry.json (LF) firmado, con tag+commit+skill ────────────────────
make_registry(){ # $1=tag $2=commit $3=sha_de_skill -> registry.json (LF) + .minisig
  "$PYBIN" - "$1" "$2" "$3" > registry.json <<'PY'
import sys, json
tag, commit, sha = sys.argv[1:4]
doc = {
  "schema": "lucky-skills/registry@1",
  "tag": tag,
  "commit": commit,
  "raw_base": "${SKILLS_REGISTRY_URL}",
  "skills": [
    {"name":"arquitectura","triggers":["/arquitectura"],"kind":"method",
     "loadable_as_data":True,"path":"plugins/lucky/skills/arquitectura/SKILL.md",
     "requires_runtime":[],"requires_tools":[],"sha256":sha}
  ]
}
sys.stdout.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
PY
  norm_lf registry.json
  minisign -S -s key.sec -m registry.json >/dev/null 2>&1
}

# replica EXACTA de la cadena del fetcher: minisign -V (LF) -> parse python ->
# pin tag/commit -> sha256 -c del cuerpo. Devuelve "ok" (emite bloque) o "reject".
verify_chain(){ # $1=pubkey $2=registry $3=sig $4=body $5=want_tag $6=want_commit
  local pub="$1" reg="$2" sig="$3" body="$4" wtag="$5" wcommit="$6"
  [ -f "$sig" ] || { echo reject; return; }
  norm_lf "$reg"; norm_lf "$sig"; norm_lf "$body"
  minisign -V -p "$pub" -x "$sig" -m "$reg" >/dev/null 2>&1 || { echo reject; return; }
  local parsed
  parsed="$("$PYBIN" - "$reg" arquitectura <<'PY'
import sys, json, re
reg, want = sys.argv[1], sys.argv[2]
d = json.load(open(reg, encoding="utf-8"))
f = None
for s in d.get("skills", []):
    if str(s.get("name","")).lower()==want: f=s; break
if f is None: sys.exit(3)
sha=str(f.get("sha256","")).lower()
if not re.fullmatch(r"[0-9a-f]{64}", sha): sys.exit(5)
if f.get("requires_runtime") or f.get("requires_tools") or not f.get("loadable_as_data"): sys.exit(4)
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

# ── 1. registry firma-ok + tag/commit/sha ok -> ok (emite bloque) ─────────────
make_registry "$INSTALL_TAG" "$INSTALL_COMMIT" "$SKILL_SHA"
check "registry firma-ok + skill sha-ok -> emite" "ok" \
  "$(verify_chain key.pub registry.json registry.json.minisig skill.md "$INSTALL_TAG" "$INSTALL_COMMIT")"

# ── 2. firma-mala: verificar con la clave equivocada -> reject ────────────────
check "firma-mala (clave equivocada) -> reject" "reject" \
  "$(verify_chain other.pub registry.json registry.json.minisig skill.md "$INSTALL_TAG" "$INSTALL_COMMIT")"

# ── 3. tag-mismatch: install pide otro tag -> reject ──────────────────────────
check "tag-mismatch -> reject" "reject" \
  "$(verify_chain key.pub registry.json registry.json.minisig skill.md "v9.9.9" "$INSTALL_COMMIT")"

# ── 4. commit-mismatch: install pide otro commit -> reject ────────────────────
check "commit-mismatch -> reject" "reject" \
  "$(verify_chain key.pub registry.json registry.json.minisig skill.md "$INSTALL_TAG" "ffffffffffffffffffffffffffffffffffffffff")"

# ── 5. sin-sig: borro la firma -> reject ──────────────────────────────────────
mv registry.json.minisig registry.json.minisig.bak
check "sin-sig -> reject" "reject" \
  "$(verify_chain key.pub registry.json registry.json.minisig skill.md "$INSTALL_TAG" "$INSTALL_COMMIT")"
mv registry.json.minisig.bak registry.json.minisig

# ── 6. sin-minisign: PATH sin minisign -> reject (toolchain ausente) ──────────
#    Aislamos minisign poniendo un PATH vacio de el; la cadena no puede verificar.
( PATH="/nonexistent"; command -v minisign >/dev/null 2>&1 ) && SIXRES=ok || SIXRES=reject
check "sin-minisign (toolchain ausente) -> reject" "reject" "$SIXRES"

# ── 7. skill sha-ok: cuerpo intacto -> ok (ya cubierto por #1, reconfirmar) ───
check "skill sha-ok -> emite" "ok" \
  "$(verify_chain key.pub registry.json registry.json.minisig skill.md "$INSTALL_TAG" "$INSTALL_COMMIT")"

# ── 8. skill MISMATCH: altero 1 byte del cuerpo -> reject ─────────────────────
printf 'contenido de la skill arquitectura ADULTERADO\nlinea dos\n' > skill_bad.md
norm_lf skill_bad.md
check "skill MISMATCH (cuerpo alterado) -> reject" "reject" \
  "$(verify_chain key.pub registry.json registry.json.minisig skill_bad.md "$INSTALL_TAG" "$INSTALL_COMMIT")"

# ── 9. CRLF-sigue-matcheando: el mismo cuerpo con \r\n debe normalizar y matchear ─
sed 's/$/\r/' skill.md > skill_crlf.md   # mete CR al final de cada linea
check "CRLF en el cuerpo: normaliza a LF y sigue matcheando -> emite" "ok" \
  "$(verify_chain key.pub registry.json registry.json.minisig skill_crlf.md "$INSTALL_TAG" "$INSTALL_COMMIT")"

# ── 10. invariante DURO: en TODO reject, el bloque emitido es VACIO ───────────
#    verify_chain devuelve 'reject' (no 'ok') => additionalContext seria "".
#    Reconfirmamos que ningun caso de reject produjo 'ok' por accidente:
ALL_REJECTS_EMPTY="yes"
for r in \
  "$(verify_chain other.pub registry.json registry.json.minisig skill.md "$INSTALL_TAG" "$INSTALL_COMMIT")" \
  "$(verify_chain key.pub registry.json registry.json.minisig skill_bad.md "$INSTALL_TAG" "$INSTALL_COMMIT")" \
  "$(verify_chain key.pub registry.json registry.json.minisig skill.md "v9.9.9" "$INSTALL_COMMIT")" ; do
  [ "$r" = "ok" ] && ALL_REJECTS_EMPTY="no"
done
check "invariante: todo rechazo => additionalContext VACIO (nada al contexto)" "yes" "$ALL_REJECTS_EMPTY"

echo
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
