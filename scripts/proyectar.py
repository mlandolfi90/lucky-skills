#!/usr/bin/env python3
"""proyectar — regenera las PROYECCIONES del sistema de registros (ADR 0016).

Clon estructural de bitacora-espejo.py aplicado al Crisol: la fuente de verdad
son las FILAS (docs/refactor/_crisol/runs/*.md, docs/decisions/*.md); las
proyecciones se regeneran completas, byte-deterministas (orden por id, fechas
del dato — jamás del reloj, LF puro):

  1. docs/refactor/_crisol/RUN-LEDGER.md  — formato LEGACY, MISMO path: los
     guardianes (crisol_gate.py / crisol-enforcer.sh) siguen parseando el mismo
     archivo sin cambiar una línea (Fase 1 de la migración; la Fase 2 los
     enseñará a leer frontmatter y este render morirá).
     = marcador GENERADO + archivo histórico verbatim + render de cada run.
  2. docs/refactor/_crisol/_ACTIVE        — puntero O(1) a la corrida abierta.
     Línea 1 = id (o `(ninguna)`). Invariante: ≤1 ACTIVE; 2+ → exit 1.
  3. docs/decisions/INDEX.md              — una línea por ADR (nº, título,
     estado, supersede) parseando frontmatter (0016+) y legacy (0001-0015).

Regenerar N veces = byte-idéntico (métrica M6). Correr en el MISMO paso que
toda mutación de un run (regla de la skill crisol §5). Dependencia: PyYAML.
Uso: python scripts/proyectar.py [--repo <raiz>] [--check]
     --check: no escribe; exit 1 si alguna proyección en disco difiere (drift).
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("XX proyectar: falta PyYAML (pip install pyyaml).")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MARCADOR = "<!-- GENERADO por scripts/proyectar.py — NO EDITAR: fuente = las filas (ADR 0016) -->"
_FRONT_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _leer(p: Path) -> str:
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        return f.read().replace("\r\n", "\n")


def _escribir(p: Path, contenido: str, check: bool) -> bool:
    """True si hubo (o habría) cambio. En --check no escribe."""
    actual = _leer(p) if p.is_file() else None
    if actual == contenido:
        return False
    if not check:
        p.parent.mkdir(parents=True, exist_ok=True)
        with io.open(p, "w", encoding="utf-8", newline="") as f:
            f.write(contenido)
    return True


def _fila(p: Path):
    """(frontmatter dict, cuerpo str) de una fila; (None, None) si no parsea."""
    text = _leer(p)
    m = _FRONT_RE.match(text)
    if not m:
        return None, None
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None, None
    return (fm if isinstance(fm, dict) else None), text[m.end():]


def _render_run(fm: dict, cuerpo: str) -> str:
    """Fila de corrida → bloque legacy que los guardianes parsean HOY.

    El formato de salida es CONTRATO (test-paridad.sh lo verifica contra el
    gate real): `### <branch> — <fecha> (<titulo>)` + campos `- X:` + cuerpo
    verbatim + matriz VEREDICTOS + Iteraciones.
    """
    out: list[str] = []
    fecha = str(fm.get("creado", ""))
    titulo = str(fm.get("titulo", "")).strip()
    head = f"### {fm.get('branch', 'main')} — {fecha}"
    if titulo:
        head += f" ({titulo})"
    out.append(head)
    out.append(f"- STATUS: {fm.get('estado', '')}")
    out.append(f"- Tier: {fm.get('tier', '')}")
    out.append(f"- Fecha: {fecha}")
    out.append(f"- TARGET: {fm.get('target', '')}")
    if fm.get("model"):
        out.append(f"- MODEL: {fm['model']}")
    if fm.get("ley"):
        out.append(f"- LEY: {fm['ley']}")
    cuerpo = cuerpo.strip("\n")
    if cuerpo:
        out.append(cuerpo)
    out.append("<!-- VEREDICTOS:BEGIN -->")
    out.append(f"- runState: {fm.get('runState', 'wip')}")
    for v in fm.get("veredictos") or []:
        out.append(
            f"- [V] {v.get('regla')} · {v.get('veredicto')} · "
            f"{v.get('quien')} · {v.get('evidencia')}"
        )
    out.append("<!-- VEREDICTOS:END -->")
    if fm.get("iteraciones"):
        out.append(f"- Iteraciones: {fm['iteraciones']}")
    if fm.get("cierre"):
        out.append(f"- Cierre: {fm['cierre']}")
    return "\n".join(out) + "\n"


def proyectar_crisol(repo: Path, check: bool) -> tuple[bool, list[str]]:
    base = repo / "docs" / "refactor" / "_crisol"
    runs_dir = base / "runs"
    archivo = runs_dir / "_archivo-hasta-2026-07.md"
    ledger = base / "RUN-LEDGER.md"
    activo = base / "_ACTIVE"

    errores: list[str] = []
    partes: list[str] = [MARCADOR + "\n"]
    if archivo.is_file():
        partes.append(_leer(archivo))

    activos: list[str] = []
    for p in sorted(runs_dir.glob("*.md")) if runs_dir.is_dir() else []:
        if p.name.startswith("_archivo"):
            continue
        fm, cuerpo = _fila(p)
        if fm is None:
            errores.append(f"run ilegible (sin frontmatter valido): {p.name}")
            continue
        partes.append("\n" + _render_run(fm, cuerpo if cuerpo else ""))
        if str(fm.get("estado", "")).upper() == "ACTIVE":
            activos.append(str(fm.get("id", p.stem)))

    if len(activos) > 1:
        errores.append(f"INVARIANTE ROTA: {len(activos)} corridas ACTIVE ({', '.join(activos)})")

    cambio = _escribir(ledger, "".join(partes), check)
    puntero = (activos[0] if activos else "(ninguna)") + "\n" + \
        "<!-- GENERADO por scripts/proyectar.py — NO EDITAR (ADR 0016) -->\n"
    cambio |= _escribir(activo, puntero, check)
    return cambio, errores


def proyectar_decisiones(repo: Path, check: bool) -> bool:
    ddir = repo / "docs" / "decisions"
    if not ddir.is_dir():
        return False
    filas = []
    for p in sorted(ddir.glob("[0-9][0-9][0-9][0-9]-*.md")):
        num = p.name[:4]
        fm, _ = _fila(p)
        text = _leer(p)
        mt = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        titulo = mt.group(1).strip() if mt else p.stem
        titulo = re.sub(r"^\d{4}\s*[—-]\s*", "", titulo)
        estado = str((fm or {}).get("estado", "ACEPTADA·legado"))
        sup = (fm or {}).get("superseded_by") or ""
        filas.append((num, titulo, estado, str(sup), p.name))
    out = [MARCADOR, "", "# Decisiones (ADRs) — índice", "",
           "| Nº | Decisión | Estado | Superseded by |", "|---|---|---|---|"]
    for num, titulo, estado, sup, fname in filas:
        out.append(f"| {num} | [{titulo}]({fname}) | {estado} | {sup} |")
    return _escribir(ddir / "INDEX.md", "\n".join(out) + "\n", check)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--check", action="store_true",
                    help="no escribe; exit 1 si hay drift proyeccion↔filas")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()

    cambio_l, errores = proyectar_crisol(repo, args.check)
    cambio_d = proyectar_decisiones(repo, args.check)

    for e in errores:
        print(f"XX {e}")
    if errores:
        return 1
    if args.check:
        if cambio_l or cambio_d:
            print("XX drift: alguna proyeccion difiere de sus filas (regenerar y commitear juntas)")
            return 1
        print("OK proyecciones al dia (byte-identicas a sus filas)")
        return 0
    print(f"OK proyectado: RUN-LEDGER.md{' (cambio)' if cambio_l else ' (sin cambios)'} · "
          f"_ACTIVE · decisions/INDEX.md{' (cambio)' if cambio_d else ' (sin cambios)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
