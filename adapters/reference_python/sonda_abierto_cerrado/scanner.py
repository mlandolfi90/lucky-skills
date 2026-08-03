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
    # Señal 2 (aporte PizarraEvo 2026-08-03): el discriminante fuerte no es
    # "¿crece?" sino "¿features inconexas abren el mismo archivo?". Proxy
    # medible: los co-cambios de sus ediciones aditivas son disjuntos.
    temas: str = "N/D"  # INCONEXOS | CONEXOS | N/D
    # Señal 3: una raíz de composición crece por adición POR DISEÑO (cablear
    # está bien). Proxy: densidad de imports/wiring en el contenido actual.
    raiz_composicion: bool = False

    @property
    def score(self) -> int:
        base = self.ediciones_aditivas + (2 if self.pista_nombre else 0)
        if self.temas == "INCONEXOS":
            base += 2
        if self.raiz_composicion:
            base -= 2
        return base


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


def _log_completo(
    repo: Path, rev: str, ultimos: int | None = None
) -> list[dict[str, tuple[int, int]]]:
    """Lista de commits (nuevo→viejo); cada uno: ruta -> (adds, dels)."""
    extra = ["-n", str(ultimos)] if ultimos else []
    salida = _git(repo, "log", rev, *extra, "--numstat", "--no-renames", "--format=@%H")
    commits: list[dict[str, tuple[int, int]]] = []
    for linea in salida.splitlines():
        if linea.startswith("@"):
            commits.append({})
            continue
        if not linea or not commits:
            continue
        partes = linea.split("\t", 2)
        if len(partes) != 3 or partes[0] == "-":
            continue  # binarios o líneas ajenas
        try:
            adds, dels = int(partes[0]), int(partes[1])
        except ValueError:
            continue
        commits[-1][partes[2]] = (adds, dels)
    return commits


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def _temas(commits: list[dict[str, tuple[int, int]]], indices: list[int], ruta: str) -> str:
    """INCONEXOS si los co-cambios de las ediciones aditivas casi no se solapan."""
    conjuntos = [set(commits[i]) - {ruta} for i in indices]
    conjuntos = [c for c in conjuntos if c]  # commits-solo-este-archivo no opinan
    if len(conjuntos) < 2:
        return "N/D"
    pares = [
        _jaccard(conjuntos[i], conjuntos[j])
        for i in range(len(conjuntos))
        for j in range(i + 1, len(conjuntos))
    ]
    promedio = sum(pares) / len(pares)
    return "INCONEXOS" if promedio <= 0.2 else "CONEXOS"


_IMPORT_PATTERN = re.compile(
    r"^\s*(import\s|from\s.+\simport|const\s.+=\s*require\(|require\(|"
    r"export\s+\{[^}]*\}\s*from|module\.exports|app\.use\()"
)


def _es_raiz_de_composicion(repo: Path, rev: str, ruta: str) -> bool:
    """Cablear está bien: un archivo mayormente de imports/wiring crece por diseño."""
    try:
        contenido = _git(repo, "show", f"{rev}:{ruta}")
    except ValueError:
        return False
    lineas = [l for l in contenido.splitlines() if l.strip()]
    if not lineas:
        return False
    wiring = sum(1 for l in lineas if _IMPORT_PATTERN.match(l))
    return wiring / len(lineas) >= 0.5


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
    commits = _log_completo(repo, rev, ultimos)
    historia: dict[str, list[tuple[int, tuple[int, int]]]] = {}
    for indice, archivos in enumerate(commits):
        for ruta, stats in archivos.items():
            historia.setdefault(ruta, []).append((indice, stats))

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
            (indice, (a, d))
            for indice, (a, d) in crecimientos
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
                temas=_temas(commits, [i for i, _ in aditivas], ruta),
                raiz_composicion=_es_raiz_de_composicion(repo, rev, ruta),
            )
        )
    # El discriminante manda (aporte PizarraEvo): features inconexas abriendo
    # el mismo archivo pesa más que cualquier conteo bruto. Después la pista
    # de nombre, después el volumen. Una raíz de composición baja al fondo.
    return sorted(
        candidatos,
        key=lambda c: (
            c.raiz_composicion,
            c.temas != "INCONEXOS",
            not c.pista_nombre,
            -c.ediciones_aditivas,
            c.ruta,
        ),
    )
