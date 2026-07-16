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


def _sha256_lf(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _frontmatter(p: Path):
    """dict del frontmatter YAML, o None si el archivo no abre con `---`."""
    m = _FRONT_RE.match(p.read_text(encoding="utf-8-sig", errors="replace"))
    if not m:
        return None
    data = yaml.safe_load(m.group(1))
    return data if isinstance(data, dict) else None


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
