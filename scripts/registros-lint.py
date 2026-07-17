#!/usr/bin/env python3
"""registros-lint — valida manifiesto (docs/registros.yaml) ↔ realidad (ADR 0016).

Fail-closed para la FORJA (forjar-release.sh lo corre antes de sellar): exit 0
limpio, exit 1 con hallazgos listados. Verifica:

  1. El manifiesto parsea y cada tabla declara path + duenio.
  2. Cada fila (archivo en el path de una tabla) matchea el patron declarado y
     lleva frontmatter valido: id == nombre de archivo, schema, tipo, estado
     (estado ∈ estados declarados). Exenciones: archivo_historico (particion
     congelada), proyecciones, decisiones legacy (< frontmatter_desde).
  3. Proyecciones declaradas: si existen, llevan el marcador GENERADO en las
     primeras lineas (nadie las edita a mano).
  4. Cero huerfanos bajo docs/ (metrica M3): todo archivo pertenece a una tabla,
     es proyeccion/archivo declarado, narrativa, config o sellos.
  5. Sellos (tabla sellado:true): fila en estado terminal → sha256 (bytes LF)
     presente y correcto en sellos.json; entrada de sellos sin archivo → drift.
  6. Cobertura del manual (ADR 0021 §5): sidecar docs/manual/_cobertura.yaml en
     FORMA CRUDA (contrato de awk), piezas mapeadas, globs vivos, cursor sha40
     existente y ancestro.
  7. Gate de doc (ADR 0021 §2): toda fila feature VIVA lleva `doc:` existente y
     `doc_veredicto.estado: PASA`. Chequeo INDEPENDIENTE del 6: son subsistemas
     distintos y el 6 es lazy — atarlos apagaba el gate donde no hay manual.

Dependencia: PyYAML (probado 6.0.1). Corre en la maquina de la forja; los repos
de la flota consumen el manifiesto como dato, no corren este lint.
Uso: python scripts/registros-lint.py [--repo <raiz>]
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # fail-closed con instruccion clara: el lint sin parser no "aprueba"
    sys.exit("XX registros-lint: falta PyYAML (pip install pyyaml). Lint NO corrido = NO verde.")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MARCADOR_GENERADO = "GENERADO por scripts/proyectar.py"
_FRONT_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_COBERTURA = "docs/manual/_cobertura.yaml"
_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
# FORMA CRUDA del sidecar = el contrato de awk (brujula.sh). El lint es A
# PROPOSITO mas estricto que el awk (indentacion exacta): rechazar de mas es
# ruidoso y se corrige; aceptar de mas es un falso-verde silencioso.
_C_BLOQUE = (
    ("doc", re.compile(r"^  - doc: (\S+)$")),
    ("cubre", re.compile(r"^    cubre: \[([^\]]*)\]$")),
    ("deps", re.compile(r"^    deps: \[([^\]]*)\]$")),
    ("verificado_en", re.compile(r"^    verificado_en: (\S+)$")),
)


def _sha256_lf(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _frontmatter(p: Path):
    """dict del frontmatter YAML, o None si el archivo no abre con `---`."""
    m = _FRONT_RE.match(p.read_text(encoding="utf-8-sig", errors="replace"))
    if not m:
        return None
    data = yaml.safe_load(m.group(1))
    return data if isinstance(data, dict) else None


def _git(repo: Path, *args: str) -> tuple[int, str]:
    """git capturado. FALSO-VERDE-004: se devuelve el returncode DESNUDO; el
    formateo lo hace el llamador. Sin git -> 127 (el llamador falla, no skipea)."""
    try:
        p = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        return 127, ""
    return p.returncode, p.stdout


def _lint_cobertura(repo: Path, f) -> None:
    """(6) Sidecar de cobertura del manual. UNA responsabilidad: el sidecar.

    Subsistema con DOS parsers (awk en brujula.sh, PyYAML aca) cuyo contrato es
    la FORMA CRUDA del texto, no solo que PyYAML parsee. ADR 0021 §5.

    NO contiene el gate de doc: ese vive en _lint_gate_doc() y main() lo llama
    APARTE. Todo `return` de aca abajo (lazy, forma rota, sin git) pertenece al
    subsistema sidecar y NO puede apagar el gate. Quien vuelva a meter el gate
    adentro de esta funcion reabre el falso-verde de [DRIFT-001]: ver el
    docstring de _lint_gate_doc().
    """
    manual = repo / "docs" / "manual"
    side = repo / _COBERTURA
    piezas = sorted(
        str(p.relative_to(repo)).replace("\\", "/")
        for p in manual.rglob("*.md")
        if not p.name.startswith("_")
    ) if manual.is_dir() else []

    if not side.is_file():
        # (i) DRIFT-001: hay sujeto y no hay mapa -> BLOQUEA, jamas skip silencioso.
        if piezas:
            f(f"cobertura: {len(piezas)} pieza(s) en docs/manual/ y no existe {_COBERTURA} "
              f"(la 1ra escritura del manualizador-2 crea la cabecera; ADR 0021 §5)")
        return  # lazy legitimo DEL SIDECAR: sin manual y sin mapa no hay que cubrir

    # ── (v) FORMA CRUDA — el chequeo que sostiene el doble parser ────────────
    # PyYAML acepta block-style y awk NO: block-style pasaria el YAML y el awk
    # malparsearia EN SILENCIO -> la brujula leeria basura y la senial mentiria.
    # Si el revisor recorta chequeos, este NO se recorta.
    lineas = side.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    if "piezas:" not in lineas:
        f(f"cobertura: {_COBERTURA} sin linea `piezas:` al margen (forma rigida; ADR 0021 §5)")
        return
    i_piezas = lineas.index("piezas:")
    cab = [x for x in lineas[:i_piezas] if x.strip() and not x.lstrip().startswith("#")]
    if cab != ["schema: lucky-cobertura/1"]:
        f(f"cobertura: {_COBERTURA} sin la cabecera exacta `schema: lucky-cobertura/1` antes de "
          f"`piezas:` (la escribe la PRIMERA escritura del manualizador-2; ADR 0021 §5)")
        return

    cuerpo = lineas[i_piezas + 1:]
    while cuerpo and not cuerpo[-1].strip():
        cuerpo.pop()
    if not cuerpo:
        f(f"cobertura: {_COBERTURA} existe con `piezas:` vacio — el sidecar es LAZY: "
          f"nace CON su primera pieza, no antes (ADR 0021 §5)")
        return
    if len(cuerpo) % 4 != 0:
        f(f"cobertura: {_COBERTURA} tiene {len(cuerpo)} linea(s) bajo `piezas:`, no multiplo de 4 "
          f"(4 claves por pieza, una por linea, sin comentarios dentro de `piezas:`)")
        return

    entradas: list[str] = []
    for k in range(0, len(cuerpo), 4):
        vals: list[str] = []
        for (clave, rx), linea in zip(_C_BLOQUE, cuerpo[k:k + 4]):
            m = rx.match(linea)
            if not m:
                f(f"cobertura: {_COBERTURA} pieza #{k // 4 + 1}: se esperaba `{clave}:` en forma "
                  f"rigida (4 claves en ESTE orden, una por linea; cubre/deps flow-style [a, b] "
                  f"en UNA linea) y hay: {linea.strip()!r}")
                return
            vals.append(m.group(1))
        doc, cubre_s, deps_s, sha = vals

        if doc in entradas:
            f(f"cobertura: {_COBERTURA} declara {doc} dos veces")
        entradas.append(doc)
        # (i-bis) espejo de (i): entrada cuyo doc: no existe = mapa que miente.
        if not (repo / doc).is_file():
            f(f"cobertura: {_COBERTURA} declara {doc} y el archivo no existe")

        # ── (ii) globs vivos, con el MATCHER DE GIT ─────────────────────────
        # NO pathlib.glob: la brujula matchea con pathspec de git. Dos matchers
        # distintos = un glob que pasa el lint y esta muerto en la brujula ->
        # el lint certificaria un mapa roto, el peor modo de falla del §5.
        paths = [x.strip() for x in f"{cubre_s},{deps_s}".split(",") if x.strip()]
        if not paths:
            f(f"cobertura: {_COBERTURA} {doc}: cubre/deps vacios — pieza sin paths no tiene senial")
        for x in paths:
            if re.search(r"\s", x):
                f(f"cobertura: {_COBERTURA} {doc}: path {x!r} lleva espacios — awk (brujula.sh) "
                  f"separa por espacio y lo malparsearia")
                continue
            rc, out = _git(repo, "ls-files", "--", x)
            if rc != 0:
                # Aborta el SIDECAR, no el lint: el gate de doc corre igual desde
                # main(). Sin git no se aprueba a ciegas lo que no se pudo mirar.
                f("cobertura: sin git no se puede verificar el sidecar (el lint NO aprueba a ciegas)")
                return
            if not out.strip():
                f(f"cobertura: {_COBERTURA} {doc} declara `{x}` y no matchea ningun archivo (glob muerto)")

        # ── (iii) cursor: formato + existe + ancestro ───────────────────────
        if not _SHA40_RE.match(sha):
            f(f"cobertura: {_COBERTURA} {doc}: verificado_en `{sha}` no es sha40 [0-9a-f]{{40}}")
            continue
        rc, _out = _git(repo, "cat-file", "-e", f"{sha}^{{commit}}")
        if rc != 0:
            f(f"cobertura: {_COBERTURA} {doc}: verificado_en {sha[:7]} no existe en la historia — "
              f"`rev-list {sha[:7]}..HEAD` falla y la brujula imprimiria N/D PARA SIEMPRE")
            continue
        rc, _out = _git(repo, "merge-base", "--is-ancestor", sha, "HEAD")
        if rc != 0:
            f(f"cobertura: {_COBERTURA} {doc}: verificado_en {sha[:7]} no es ancestro de HEAD — "
              f"el conteo de commits saldria inflado")

    # (i) toda pieza de docs/manual/ tiene entrada. Solo docs/manual/: el sidecar
    # ACEPTA doc: docs/sistema/... (opt-in del manualizador) pero no se EXIGE
    # (ADR 0021 §4: la mayoria de las features son audiencia: dev). Gap declarado.
    for p in piezas:
        if p not in entradas:
            f(f"cobertura: pieza {p} sin entrada en {_COBERTURA} (mapa incompleto = detector ciego)")


def _lint_gate_doc(repo: Path, f) -> None:
    """(7) Gate de doc de la fila feature VIVA (ADR 0021 §2).

    FUNCION SEPARADA DE _lint_cobertura, Y LA SEPARACION ES EL MECANISMO DEL
    GATE, NO COSMETICA. Mientras este bloque vivia dentro de _lint_cobertura, el
    `return` del caso lazy del sidecar corria ANTES: sin docs/manual/ (el caso
    DOMINANTE de esta forja — ADR 0021 §4 `audiencia: dev`, doc en docs/sistema/)
    una feature VIVA sin doc_veredicto.estado PASA salia EN VERDE. El chequeo
    existia y no mordia: [DRIFT-001] materializado. NO se vuelve a fusionar, y
    NINGUN estado del sidecar puede saltear esta funcion.

    UNICO skip legal: ausencia de SUJETO (la tabla feature no existe todavia),
    jamas ausencia de chequeo.

    La columna la ESCRIBE el carril B (registros.yaml:98 `duenio: skill:feature`)
    y su forma pineada es un MAPA ANIDADO:
      doc_veredicto: {estado: PENDIENTE, ronda: 0, ref: null}
    Se lee `doc_veredicto.estado`, JAMAS `doc_veredicto: PASA` plano: validar el
    campo plano seria un falso-verde estructural — el lint aprobaria un campo que
    nadie escribe y una feature VIVA sin PASA pasaria. El guard isinstance(dict)
    es esa mordida.
    """
    feats = repo / "docs" / "features"
    if not feats.is_dir():
        return  # ausencia de SUJETO: la tabla feature nace al primer uso
    for fila in sorted(feats.glob("*.md")):
        fm = _frontmatter(fila)
        if not isinstance(fm, dict) or str(fm.get("estado", "")) != "VIVA":
            continue  # 'sin frontmatter' ya lo reporta el loop de tablas: sin doble voz
        rel = str(fila.relative_to(repo)).replace("\\", "/")
        doc = str(fm.get("doc") or "")
        if not doc:
            f(f"gate de doc: {rel} esta VIVA sin `doc:` (regla dura 2; ADR 0021 §2)")
        elif not (repo / doc).is_file():
            f(f"gate de doc: {rel} esta VIVA y su `doc: {doc}` no existe")
        dv = fm.get("doc_veredicto")
        if not isinstance(dv, dict):
            f(f"gate de doc: {rel} esta VIVA y `doc_veredicto` no es el mapa "
              f"{{estado, ronda, ref}} que pinea la tabla feature (ausente o forma plana = "
              f"falso-verde; ADR 0021 §2)")
        elif str(dv.get("estado", "")) != "PASA":
            f(f"gate de doc: {rel} esta VIVA con doc_veredicto.estado `{dv.get('estado')}` != PASA "
              f"(VIVA lo exige; ADR 0021 §2)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    manifiesto = repo / "docs" / "registros.yaml"

    fallas: list[str] = []
    f = fallas.append

    if not manifiesto.is_file():
        print("XX no existe docs/registros.yaml")
        return 1
    try:
        cfg = yaml.safe_load(manifiesto.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        print(f"XX registros.yaml no parsea: {e}")
        return 1

    tablas = cfg.get("tablas") or {}
    if not isinstance(tablas, dict) or not tablas:
        print("XX registros.yaml sin bloque `tablas`")
        return 1

    # ── sellos.json ──────────────────────────────────────────────────────────
    sellos_path = repo / str(cfg.get("sellos", "docs/refactor/_crisol/sellos.json"))
    sellos: dict[str, str] = {}
    if sellos_path.is_file():
        try:
            doc = json.loads(sellos_path.read_text(encoding="utf-8"))
            sellos = doc.get("sellos", {}) if isinstance(doc, dict) else {}
        except json.JSONDecodeError:
            f(f"sellos ilegible (JSON invalido): {sellos_path.name}")

    # Rutas declaradas (para el chequeo de huerfanos), relativas al repo con /.
    declaradas: set[str] = set()

    def declara(rel: str) -> None:
        declaradas.add(rel.replace("\\", "/").rstrip("/"))

    declara("docs/registros.yaml")
    declara(str(sellos_path.relative_to(repo)))
    tablero = cfg.get("tablero")
    if tablero:
        declara(str(tablero))
        tp = repo / str(tablero)
        if tp.is_file():
            head = "\n".join(tp.read_text(encoding="utf-8-sig", errors="replace").splitlines()[:3])
            if MARCADOR_GENERADO not in head:
                f(f"proyeccion {tablero} SIN marcador `{MARCADOR_GENERADO}` (¿editada a mano?)")
    for rel in (cfg.get("narrativa") or []) + (cfg.get("config") or []):
        declara(str(rel))

    filas_selladas: set[str] = set()  # claves <tabla>:<id> que DEBEN estar en sellos

    # ── por tabla ────────────────────────────────────────────────────────────
    for nombre, t in tablas.items():
        if not isinstance(t, dict) or not t.get("path") or not t.get("duenio"):
            f(f"tabla `{nombre}`: falta path/duenio en el manifiesto")
            continue
        raw_path = str(t["path"])
        estados = set(t.get("estados") or [])
        terminales = set(t.get("terminales") or [])
        patron = t.get("patron")
        proyecciones = [str(p) for p in (t.get("proyecciones") or [])]
        archivo_hist = t.get("archivo_historico")
        fm_desde = t.get("frontmatter_desde")

        for pr in proyecciones:
            declara(pr)
        if archivo_hist:
            declara(str(archivo_hist))

        # tabla de una sola hoja (forma: linea) — solo declarar
        if t.get("forma") == "linea":
            declara(raw_path)
            continue

        # path con glob (ramas de skills) → expandir; sin glob → literal
        dirs = [d for d in repo.glob(raw_path.rstrip("/"))] if "*" in raw_path \
            else [repo / raw_path.rstrip("/")]
        for d in dirs:
            rel_dir = str(d.relative_to(repo)).replace("\\", "/")
            declara(rel_dir)
            if not d.is_dir():
                if not t.get("lazy"):
                    f(f"tabla `{nombre}`: path {rel_dir}/ no existe (y no es lazy)")
                continue
            for fila in sorted(d.iterdir()):
                if not fila.is_file():
                    continue
                rel = str(fila.relative_to(repo)).replace("\\", "/")
                declara(rel)
                if archivo_hist and rel == str(archivo_hist).replace("\\", "/"):
                    continue  # particion congelada: exenta de forma
                if rel in (proyecciones or []):
                    continue
                if patron and not fnmatch.fnmatch(fila.name, patron):
                    f(f"tabla `{nombre}`: {rel} no matchea el patron `{patron}` (huerfano en la tabla)")
                    continue
                # decisiones legacy: numeradas < frontmatter_desde quedan exentas
                if fm_desde is not None:
                    mnum = re.match(r"^(\d{4})-", fila.name)
                    if mnum and int(mnum.group(1)) < int(fm_desde):
                        continue
                fm = _frontmatter(fila)
                if fm is None:
                    f(f"tabla `{nombre}`: {rel} sin frontmatter (toda fila lleva columnas)")
                    continue
                fid = str(fm.get("id", ""))
                esperado = fila.stem
                # ids con prefijo de tabla (`adr:0016`) validan por sufijo numerico
                if fid not in (esperado, f"{nombre}:{esperado}") and not (
                    ":" in fid and esperado.startswith(fid.split(":", 1)[1])
                ):
                    f(f"tabla `{nombre}`: {rel} id `{fid}` != nombre de archivo `{esperado}`")
                if not fm.get("schema"):
                    f(f"tabla `{nombre}`: {rel} sin campo `schema`")
                estado = str(fm.get("estado", ""))
                if estados and estado not in estados:
                    f(f"tabla `{nombre}`: {rel} estado `{estado}` fuera de {sorted(estados)}")
                if t.get("sellado") and estado in terminales:
                    clave = f"{nombre}:{esperado}"
                    filas_selladas.add(clave)
                    got = sellos.get(clave)
                    if got is None:
                        f(f"sello FALTANTE: {clave} esta {estado} pero no figura en sellos.json")
                    elif got != _sha256_lf(fila):
                        f(f"sello ROTO: {clave} — el archivo cambio tras sellarse (M8)")

        # proyecciones: marcador GENERADO obligatorio
        for pr in proyecciones:
            p = repo / pr
            if p.is_file():
                head = "\n".join(p.read_text(encoding="utf-8-sig", errors="replace").splitlines()[:3])
                if MARCADOR_GENERADO not in head:
                    f(f"proyeccion {pr} SIN marcador `{MARCADOR_GENERADO}` (¿editada a mano?)")

    # sellos sin fila (drift inverso)
    for clave in sellos:
        if clave not in filas_selladas:
            tabla, _, fid = clave.partition(":")
            t = tablas.get(tabla) or {}
            d = repo / str(t.get("path", "")).rstrip("/")
            if not any(d.glob(f"{fid}.md")) if d.is_dir() else True:
                f(f"sello COLGADO: {clave} en sellos.json sin archivo correspondiente")

    _lint_cobertura(repo, f)
    _lint_gate_doc(repo, f)

    # ── huerfanos bajo docs/ (M3) ────────────────────────────────────────────
    docs = repo / "docs"
    for p in sorted(docs.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(repo)).replace("\\", "/")
        if rel in declaradas:
            continue
        if any(rel.startswith(d + "/") for d in declaradas):
            continue
        f(f"HUERFANO: {rel} no pertenece a ninguna tabla/narrativa/config del manifiesto")

    if fallas:
        print(f"XX registros-lint: {len(fallas)} hallazgo(s)")
        for x in fallas:
            print(f"   - {x}")
        return 1
    print("OK registros-lint: manifiesto y realidad coinciden (0 hallazgos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
