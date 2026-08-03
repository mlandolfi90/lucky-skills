"""Detección del anti-patrón "registro central que crece por edición".

La firma en la historia git es medible SIN correr la escalera: un archivo
vivo que acumula ediciones netamente ADITIVAS y chicas (se le agregan
entradas) es un candidato a violar abierto/cerrado — cada tipo/plugin/caso
nuevo obliga a abrirlo. La prueba de fuego correcta (saber
CAP-2c80bf0aae72): una entrada nueva debe tocar SOLO su propio archivo —
carpeta detrás de un puerto, jamás un archivo compartido. (Ojo: la ficha
CAP-c32b718f796c dice "solo el archivo del catálogo" — es la versión que
fosiliza el archivo central; nació auto-capturada del diseño defectuoso de
PizarraEvo y su corrección está pendiente de destilación.)

Asesora por diseño: reporta candidatos con evidencia, jamás bloquea.
Solo stdlib; solo lectura sobre el repo.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

# Pistas de nombre: no deciden solas, suman señal.
PISTA_NOMBRE = re.compile(
    r"catalog|registr|tipos|types|index|lista|enum|mapping|factory|switch",
    re.IGNORECASE,
)
# Extensiones de código donde el patrón importa (un .md que crece es normal).
EXTENSIONES_CODIGO = (
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".go", ".rs",
    ".java", ".rb", ".php", ".cs", ".c", ".cc", ".cpp", ".h", ".yaml",
    ".yml", ".toml", ".json",
)


@dataclass(frozen=True)
class Candidato:
    ruta: str
    ediciones_aditivas: int
    ediciones_totales: int
    pista_nombre: bool

    @property
    def score(self) -> int:
        return self.ediciones_aditivas + (2 if self.pista_nombre else 0)


def _git(repo: Path, *args: str) -> str:
    proceso = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if proceso.returncode != 0:
        raise ValueError(f"git {' '.join(args[:2])}: {proceso.stderr.strip()[:200]}")
    return proceso.stdout


def _archivos_vivos(repo: Path, rev: str) -> set[str]:
    salida = _git(repo, "ls-tree", "-r", "--name-only", rev)
    return {linea for linea in salida.splitlines() if linea}


def _historia_por_archivo(
    repo: Path, rev: str, ultimos: int | None = None
) -> dict[str, list[tuple[int, int]]]:
    """ruta -> [(adds, dels)] en orden nuevo→viejo (el último es el nacimiento)."""
    extra = ["-n", str(ultimos)] if ultimos else []
    salida = _git(repo, "log", rev, *extra, "--numstat", "--no-renames", "--format=@%H")
    historia: dict[str, list[tuple[int, int]]] = {}
    for linea in salida.splitlines():
        if not linea or linea.startswith("@"):
            continue
        partes = linea.split("\t", 2)
        if len(partes) != 3 or partes[0] == "-":
            continue  # binarios o líneas ajenas
        try:
            adds, dels = int(partes[0]), int(partes[1])
        except ValueError:
            continue
        historia.setdefault(partes[2], []).append((adds, dels))
    return historia


def escanear(
    repo: Path,
    *,
    rev: str = "HEAD",
    min_ediciones: int = 2,
    max_lineas_por_edicion: int = 40,
    ratio_min: float = 0.75,
    ultimos: int | None = None,
) -> list[Candidato]:
    """Candidatos a registro-que-crece-por-edición.

    - `ratio_min`: pureza aditiva mínima (aditivas/ediciones). Un registro
      crece casi SOLO agregando (≈1.0); un componente en desarrollo activo
      mezcla agregados con reescrituras y queda por debajo.
    - `ultimos`: ventana de commits recientes — el modo "al momento" para
      hooks. Sin ventana se analiza toda la historia y se descuenta el
      commit de nacimiento; con ventana no se descuenta (aproximación
      declarada: un archivo nacido dentro de la ventana suma una edición).
    """
    vivos = _archivos_vivos(repo, rev)
    historia = _historia_por_archivo(repo, rev, ultimos)
    candidatos: list[Candidato] = []
    for ruta, ediciones in historia.items():
        if ruta not in vivos:
            continue  # ya no existe: si era un registro, alguien ya lo arregló
        if not ruta.lower().endswith(EXTENSIONES_CODIGO):
            continue
        crecimientos = ediciones if ultimos else ediciones[:-1]
        if not crecimientos:
            continue
        # Aditiva: agrega sin borrar (aunque sea UNA línea — la entrada
        # típica de un registro), o agrega al menos el doble de lo que toca.
        aditivas = [
            (a, d)
            for a, d in crecimientos
            if 0 < a <= max_lineas_por_edicion and (d == 0 or a >= 2 * d)
        ]
        if len(aditivas) < min_ediciones:
            continue
        if len(aditivas) / len(crecimientos) < ratio_min:
            continue  # crece, pero mezclado con reescritura: churn, no registro
        pista = bool(PISTA_NOMBRE.search(Path(ruta).name))
        # Sin pista de nombre se exige una edición aditiva más: el nombre no
        # decide, pero baja el umbral de sospecha.
        if not pista and len(aditivas) < min_ediciones + 1:
            continue
        candidatos.append(
            Candidato(
                ruta=ruta,
                ediciones_aditivas=len(aditivas),
                ediciones_totales=len(crecimientos),
                pista_nombre=pista,
            )
        )
    return sorted(
        candidatos,
        key=lambda c: (not c.pista_nombre, -c.ediciones_aditivas, c.ruta),
    )
