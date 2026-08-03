"""Catálogo de harnesses: una entrada, una carpeta, detrás de un puerto.

El eje de los harnesses crece: nacen y seguirán naciendo. Estaba medio
cerrado — `adapters/<harness>/PACKAGING.env` ya declaraba prefijo y metadatos,
y aun así los mismos datos vivían copiados a mano en cinco lugares
(`HARNESSES` y `PROJECTION_EXCLUDES` del planificador de adopción, los
`choices` de su CLI, `SUPPORTED_HARNESSES` del empaquetador y el conjunto del
registro de sincronización). Agregar un harness obligaba a abrir los cinco:
la prueba de fuego fallaba (saber CAP-2c80bf0aae72).

Acá la pregunta es una sola —¿qué harnesses hay y cómo proyecta cada uno?— y
la contesta la carpeta. Un harness nuevo entra dejando su `PACKAGING.env` y
nada más.

Colisión de identidad: FATAL, jamás un aviso (saber CAP-185236db9b3d). Un
archivo que declara un `HARNESS_ID` distinto al de su carpeta secuestraría la
identidad de otro harness — y el prefijo de proyección decide dónde se
escriben archivos. Se frena nombrando el archivo y los dos identificadores.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .envfile import load_env

ADAPTERS_DIRNAME = "adapters"
PACKAGING_FILENAME = "PACKAGING.env"
# El adaptador de referencia es implementación, no un harness.
NON_HARNESS_DIRS = frozenset({"reference_python"})
REQUIRED_KEYS = (
    "FORMAT_VERSION",
    "HARNESS_ID",
    "OUTPUT_KIND",
    "SKILL_PREFIX",
    "INCLUDE_OPENAI_METADATA",
)
# `NONE` = el harness se adopta pero no produce artefacto de empaquetado.
# Adopción y empaquetado son dos ejes distintos sobre el mismo harness:
# `generic` instala la fuente canónica y no proyecta ni empaqueta.
OUTPUT_KINDS = frozenset({"DIRECTORY", "ZIP_PER_SKILL", "NONE"})


@dataclass(frozen=True)
class HarnessSpec:
    harness_id: str
    output_kind: str
    skill_prefix: str
    include_openai_metadata: bool

    @property
    def packageable(self) -> bool:
        """¿Produce un artefacto empaquetable, o sólo se adopta?"""
        return self.output_kind != "NONE"

    @property
    def projects(self) -> bool:
        """¿Aterriza una proyección en el árbol del repo adoptante?"""
        return bool(self.skill_prefix)

    @property
    def projection_excludes(self) -> tuple[str, ...]:
        """Qué queda fuera de la proyección, derivado del propio contrato.

        `agents/` es metadato OpenAI/Codex: viaja sólo donde el harness lo
        declara. Antes esto era una tabla aparte que había que recordar
        actualizar; ahora sale del mismo archivo que decide el resto.
        """
        return () if self.include_openai_metadata else ("agents",)


def load_harnesses(repository_root: Path) -> dict[str, HarnessSpec]:
    raiz = (repository_root / ADAPTERS_DIRNAME).resolve(strict=True)
    encontrados: dict[str, HarnessSpec] = {}
    for carpeta in sorted(raiz.iterdir(), key=lambda p: p.name):
        if not carpeta.is_dir() or carpeta.name in NON_HARNESS_DIRS:
            continue
        contrato = carpeta / PACKAGING_FILENAME
        if not contrato.is_file():
            continue
        values = load_env(contrato)
        faltantes = [clave for clave in REQUIRED_KEYS if clave not in values]
        if faltantes:
            raise ValueError(
                f"{carpeta.name}/{PACKAGING_FILENAME}: faltan {','.join(faltantes)}"
            )
        if values["FORMAT_VERSION"] != "1":
            raise ValueError(f"{carpeta.name}/{PACKAGING_FILENAME}: FORMAT_VERSION inválido")
        declarado = values["HARNESS_ID"]
        if declarado != carpeta.name:
            raise ValueError(
                f"{carpeta.name}/{PACKAGING_FILENAME}: HARNESS_ID={declarado!r} no "
                f"coincide con su carpeta {carpeta.name!r}; una entrada no puede "
                "declarar la identidad de otra"
            )
        output_kind = values["OUTPUT_KIND"]
        if output_kind not in OUTPUT_KINDS:
            raise ValueError(
                f"{carpeta.name}/{PACKAGING_FILENAME}: OUTPUT_KIND inválido"
            )
        metadata = values["INCLUDE_OPENAI_METADATA"]
        if metadata not in {"YES", "NO"}:
            raise ValueError(
                f"{carpeta.name}/{PACKAGING_FILENAME}: INCLUDE_OPENAI_METADATA inválido"
            )
        encontrados[declarado] = HarnessSpec(
            harness_id=declarado,
            output_kind=output_kind,
            skill_prefix=values["SKILL_PREFIX"],
            include_openai_metadata=metadata == "YES",
        )
    if not encontrados:
        raise ValueError(f"{raiz}: ningún harness declarado")
    return encontrados


def harness_ids(repository_root: Path) -> tuple[str, ...]:
    return tuple(load_harnesses(repository_root))


def packageable_harness_ids(repository_root: Path) -> tuple[str, ...]:
    """Los que producen artefacto: el canary y el empaquetador usan estos."""
    return tuple(
        nombre
        for nombre, spec in load_harnesses(repository_root).items()
        if spec.packageable
    )
