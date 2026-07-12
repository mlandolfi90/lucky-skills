#!/usr/bin/env python3
"""bitacora-espejo — regenera el ESPEJO local de la bitácora DESDE el saber central.

El saber (`lucky-saber`, servido por el MCP `lucky-tool-saber`) es la ÚNICA fuente de verdad
(release v1.39.0 / ADR del flip). Este script clona el saber read-only y regenera
`plugins/lucky/skills/bitacora/{INDEX.md, entries/*.md, SENALES.md}` como un MIRROR: NO se
autora a mano. La flota SIN el MCP consume este mirror embebido en la LEY (grep + push hook).

DES-SCOPEO: el saber lleva `scope` (global | stack:x | repo:x) que el formato local NO tiene.
El mirror = el saber menos el scope: se borra la 8ª columna del INDEX (→ 7 col) y la línea
`- **scope:**` de cada entry (→ ≤35 líneas). Así el mirror pasa el `bitacora-lint.sh` local.

Uso:
    python scripts/bitacora-espejo.py [--saber <ruta-a-un-clone>] [--dest <bitacora-dir>]

Sin --saber: clona `lucky-saber` con `gh` (read-only, main) a un dir temporal. El operador lo
corre en pc-local cuando el saber cambió; después forja un release para propagar a la flota.
Zero-leak: el contenido del saber ya pasó su leak-scan; el forja re-corre el leak-scan local.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SABER_REPO = "mlandolfi90/lucky-saber"
_SCOPE_LINE = re.compile(r"^\s*-\s*\*\*scope:\*\*")
_TABLE_LINE = re.compile(r"^\s*\|.*\|\s*$")


def _drop_last_column(line: str) -> str:
    """Quita la ÚLTIMA columna de una fila de tabla markdown (header, separador o datos).
    `| a | b | scope |` → `| a | b |`. Uniforme: des-scopea todo el INDEX de 8→7 columnas."""
    cells = [c for c in line.strip().split("|")]
    # `| a | b |` → ['', ' a ', ' b ', '']; las celdas reales son cells[1:-1].
    inner = cells[1:-1]
    if len(inner) <= 1:
        return line  # no hay columna que quitar (fila degenerada); dejala igual
    kept = [c.strip() for c in inner[:-1]]
    return "| " + " | ".join(kept) + " |"


def descope_index(text: str) -> str:
    """INDEX del saber (8 col) → INDEX local (7 col): a cada fila de tabla le quita la col scope.
    Las líneas de prosa (título, notas) se preservan tal cual. El separador (`|---|...`) se emite
    COMPACTO para calzar el estilo local."""
    out = []
    for ln in text.split("\n"):
        if not _TABLE_LINE.match(ln):
            out.append(ln)
            continue
        dropped = _drop_last_column(ln)
        cells = [c.strip() for c in dropped.strip().strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-+:?", c) for c in cells):  # fila separadora → compacta
            dropped = "|" + "|".join(cells) + "|"
        out.append(dropped)
    return "\n".join(out)


def descope_entry(text: str) -> str:
    """Entry del saber → entry local: borra la línea `- **scope:** ...` (el resto intacto)."""
    return "\n".join(ln for ln in text.split("\n") if not _SCOPE_LINE.match(ln))


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), capture_output=True, text=True, encoding="utf-8", errors="replace")


def _clone_saber(dst: Path) -> None:
    print(f"  clonando {SABER_REPO} (read-only, main) con gh…")
    r = _run("gh", "repo", "clone", SABER_REPO, str(dst), "--", "--depth", "1", "--branch", "main")
    if r.returncode != 0:
        sys.exit("ERROR: no se pudo clonar el saber con gh (¿logueado? ¿acceso al repo privado?)")


def regenerate(saber_bitacora: Path, dest: Path) -> None:
    si, se, ss = saber_bitacora / "INDEX.md", saber_bitacora / "entries", saber_bitacora / "SENALES.md"
    if not si.is_file() or not se.is_dir():
        sys.exit(f"ERROR: el clone del saber no tiene bitacora/INDEX.md + entries/ ({saber_bitacora})")

    # 1) entries: limpiar el mirror y reescribir cada entry del saber des-scopeada (mirror fiel).
    dest_entries = dest / "entries"
    dest_entries.mkdir(parents=True, exist_ok=True)
    for old in dest_entries.glob("*.md"):
        old.unlink()
    n = 0
    for f in sorted(se.glob("*.md")):
        body = descope_entry(f.read_text(encoding="utf-8"))
        (dest_entries / f.name).write_text(body, encoding="utf-8", newline="\n")
        n += 1

    # 2) INDEX: des-scopear 8→7 columnas.
    (dest / "INDEX.md").write_text(descope_index(si.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")

    # 3) SENALES: copiar tal cual (el saber no lo scopea).
    if ss.is_file():
        (dest / "SENALES.md").write_text(ss.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

    print(f"  espejo regenerado: {n} entries + INDEX + SENALES → {dest}")
    print("  RECORDÁ: corré `bash scripts/forjar-release.sh vX.Y.Z` (leak-scan + bitacora-lint) para propagar a la flota.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Regenera el espejo local de la bitácora desde el saber.")
    ap.add_argument("--saber", help="ruta a un clone de lucky-saber (si no, se clona con gh)")
    here = Path(__file__).resolve().parent.parent
    ap.add_argument("--dest", default=str(here / "plugins" / "lucky" / "skills" / "bitacora"),
                    help="dir de la bitácora local (destino del espejo)")
    a = ap.parse_args()
    tmp = None
    try:
        if a.saber:
            saber_root = Path(a.saber)
        else:
            tmp = Path(tempfile.mkdtemp(prefix="saber-espejo-"))
            _clone_saber(tmp)
            saber_root = tmp
        regenerate(saber_root / "bitacora", Path(a.dest))
    finally:
        if tmp and tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
