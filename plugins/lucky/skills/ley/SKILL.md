---
name: ley
description: >-
  Ley — actualiza la ley viva (el plugin lucky-skills) a su última versión
  publicada, de una sola llamada. Detecta el último tag del repo por
  version-sort, lo trae al clon local, re-instala el gate y reporta en una
  línea si estás al día, si acaba de actualizar, o si hay un tag DIFERIDO
  (publicado pero no mergeado a main). Invocar cuando el humano pida
  ("/ley", "actualizá la ley", "traé la última versión de las skills",
  "¿estoy en la última ley?", "poné al día el plugin"). Solo la corre el
  operador; jamás se auto-dispara. Fail-closed: sin red o conflicto → reporta
  y frena, no adivina.
allowed-tools: Bash, Read, Grep
disable-model-invocation: true
---

# Ley — poné al día la ley viva

Una llamada: descubre la última versión publicada de `lucky-skills`, la trae al
clon local que el harness carga, re-instala el gate global y te dice en UNA línea
dónde quedaste. El update ANTES era manual (`git pull` + `instalar-gate.sh` de
memoria) — esta skill lo hace bien, incluida la trampa del tag diferido.

**Ejes:** una llamada · objetiva (salida binaria) · dura (version-sort, no
lexicográfico) · fail-closed (sin red / conflicto → frena, no adivina).

## Constantes

- **Repo de la ley:** `github.com/mlandolfi90/lucky-skills` (fuente de verdad).
- **Clon local:** el directorio del marketplace que el harness carga
  (`~/.claude/plugins/marketplaces/lucky-skills`). Resolvé el path real: es el
  ancestro git de ESTE `SKILL.md` (`git -C <dir-de-esta-skill> rev-parse --show-toplevel`).
- **Sello local:** la línea `esta copia = tag vX.Y.Z` de cualquier `SKILL.md` de
  la familia (todas iguales tras una forja) — o `git describe --tags` del clon.

## Procedimiento (el agente lo ejecuta, en orden)

**1. Resolvé el clon y el sello local.** El sello (`esta copia = tag \n vX.Y.Z`)
suele venir ENVUELTO en 2 líneas — no lo grepees single-line (devolvería vacío).
Fuente primaria robusta: `git describe` del clon (tras una forja == el sello);
respaldo: grep con `-A1` tolerante al wrap.
```bash
CLON=$(git -C "<dir-de-esta-skill>" rev-parse --show-toplevel)
SELLO_LOCAL=$(git -C "$CLON" describe --tags --abbrev=0 2>/dev/null)
# respaldo si no hay tags localmente (clon shallow / sin fetch de tags):
[ -z "$SELLO_LOCAL" ] && SELLO_LOCAL=$(grep -rhA1 'esta copia = tag' "$CLON/plugins" \
  | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' | sort -V | tail -1)
```

**2. Descubrí el último tag remoto — SIEMPRE `sort -V` (version-sort), NUNCA orden
lexicográfico** (lexicográfico pone `v1.9.0` por encima de `v1.20.0`: bug real).
Sin red → **FRENÁ**: `LEY: <SELLO_LOCAL> (local, sin verificar — sin red)`.
```bash
TAG_REMOTO=$(git ls-remote --tags --refs "https://github.com/mlandolfi90/lucky-skills.git" \
  | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' | sort -V | tail -1)
```

**3. Compará.** Si `SELLO_LOCAL == TAG_REMOTO` **y** el working tree del clon está
limpio → ya estás al día:
`LEY: <SELLO_LOCAL> = remoto ✓` → FIN (no toques nada).

**4. Traé el tag y detectá DIFERIDO.** `git fetch --tags`. El caso trampa: existe
un tag mayor cuyo commit **NO es ancestro de `origin/main`** (publicado pero no
mergeado — el `git pull` crudo miente "Already up to date"). Detectalo y **FRENÁ**,
no lo mergees por tu cuenta:
```bash
git -C "$CLON" fetch --tags --quiet origin
if ! git -C "$CLON" merge-base --is-ancestor "$TAG_REMOTO" origin/main; then
  echo "LEY: tag $TAG_REMOTO DIFERIDO (publicado, no mergeado a main) → decide el humano"
  # reportá y detené: el humano decide merge del tag vs esperar el release a main.
fi
```

**5. Actualizá (solo si el tag SÍ está en `origin/main`).** Fast-forward del clon a
`origin/main`. Si el working tree tiene cambios locales (WIP de otra corrida) o el
FF no es limpio → **FRENÁ** y reportá (`git status`), no fuerces:
```bash
git -C "$CLON" pull --ff-only origin main
```

**6. Re-instalá el gate** (idempotente; actualiza el gate global activo):
```bash
bash "$CLON/scripts/instalar-gate.sh"
```

**6b. Refrescá el CACHE instalado del plugin.** El harness NO carga el clon:
carga el snapshot registrado en `~/.claude/plugins/installed_plugins.json`
(clave `lucky@lucky-skills` → `installPath`). Actualizar solo el clon deja a la
sesión cargando la ley vieja (incidente 2026-07-04). Si la clave no existe
(plugin no instalado por esa vía) → omití el paso y reportalo en una línea.
Ídem sin `python3` ni `python` en PATH (Linux moderno suele traer SOLO `python3`).
El intérprete se resuelve por SONDA (`"$c" -c ""`), jamás `command -v`: en
Windows el stub de la Store EXISTE en PATH pero no corre (exit 49) y el paso
fallaría en silencio — DRIFT-007, mordió acá mismo el 2026-07-10.
```bash
PLUGS="$HOME/.claude/plugins/installed_plugins.json"
PYBIN=""; for c in python3 python; do "$c" -c "" >/dev/null 2>&1 && PYBIN="$c" && break; done
DEST=$([ -n "$PYBIN" ] && "$PYBIN" -c "import json,sys;e=json.load(open(sys.argv[1],encoding='utf-8'))['plugins'].get('lucky@lucky-skills');print(e[0]['installPath'] if e else '')" "$PLUGS" 2>/dev/null)
if [ -n "$DEST" ]; then
  rm -rf "$DEST" && cp -r "$CLON/plugins/lucky" "$DEST"
  SHA=$(git -C "$CLON" rev-parse HEAD)
  "$PYBIN" - "$PLUGS" "$SHA" <<'PY'
import json, sys, datetime
p, sha = sys.argv[1], sys.argv[2]
d = json.load(open(p, encoding="utf-8"))
e = d["plugins"]["lucky@lucky-skills"][0]
e["gitCommitSha"] = sha
e["lastUpdated"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
json.dump(d, open(p, "w", encoding="utf-8"), indent=2)
PY
fi
```
El refresco pisa SOLO el snapshot del plugin (`installPath`), jamás otra cosa
de `~/.claude/plugins`. Las skills refrescadas cargan al reiniciar la sesión.

**6c. Snapshots adicionales del harness.** Algunos harness cargan el plugin
desde `~/.claude/plugins/cache/lucky-skills/lucky/<ver>/` (una COPIA, no el
clon). Dos remedios: (a) refrescarlo igual que 6b (`rm -rf` + `cp -r` desde
`$CLON/plugins/lucky`), o (b) — recomendado, una sola vez por máquina —
convertirlo en **junction/symlink al clon** para que nunca más divorcie:
```bash
# Windows (Git Bash, sin admin):  cmd //c mklink /J "<cache>" "<clon>\plugins\lucky"
# Linux/macOS:                    ln -sfn "$CLON/plugins/lucky" "<cache>"
```
Con el junction, este paso desaparece: cache == clon por construcción.

## Modo live (hook `ley-live`, desde v1.36.0)

`hooks/ley-live.sh` corre en cada SessionStart de la flota: espejo silencioso
de los pasos 2-5 (version-sort, tag-en-main, árbol limpio, ff-only) con
**fail-open total** — cualquier duda → no toca nada y la sesión arranca con lo
que haya. Off-switch: `LEY_LIVE=off`. Diferencias con `/ley` (que sigue siendo
el camino VERIFICADO): el hook no re-instala el gate, no verifica integridad
sha256 y no reporta — solo acerca el clon al último tag para que la próxima
enumeración cargue fresco. La brújula sigue siendo quien te AVISA el atraso.

**7. Verificación opcional de integridad.** Si hay `plugins/lucky/skills/registry.json`,
confirmá sha256 de al menos `crisol/SKILL.md` contra el registry (cadena de
suministro). Mismatch → reportá `LEY: INTEGRIDAD FALLA (sha ≠ registry)` y frená.

## Salida (binaria, UNA línea)

| Situación | Salida |
|---|---|
| Al día | `LEY: vX.Y.Z = remoto ✓` |
| Actualizada | `LEY: vA.B.C → vX.Y.Z ACTUALIZADA (gate re-instalado)` |
| Tag diferido | `LEY: tag vX.Y.Z DIFERIDO (no mergeado a main) → decide el humano` |
| Sin red | `LEY: vA.B.C (local, sin verificar — sin red)` |
| Árbol sucio / FF no limpio | `LEY: BLOQUEADA (working tree del clon sucio / FF no limpio) → git status` |
| Integridad falla | `LEY: INTEGRIDAD FALLA (sha ≠ registry) → no confiar en esta copia` |

Tras `ACTUALIZADA`: recordale al humano que las skills recién traídas **cargan al
reiniciar la sesión** (el gate ya quedó vivo sin reiniciar).

## Reglas duras

- **Nunca orden lexicográfico** para versiones — siempre `sort -V`.
- **Nunca `--force`, nunca resolver un merge/conflicto solo** — fail-closed: reportá y frená.
- **No auto-invocable** (`disable-model-invocation: true`): actualizar la ley es
  acto del operador. La **brújula SEÑALA** que estás atrasado; ejecutar `/ley` lo decidís vos.
- **Namespace:** según cómo el harness exponga el plugin, puede invocarse `/ley` o
  `/lucky:ley`. Los disparadores textuales ("actualizá la ley") cubren ambos.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v1.39.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.
