"""Adoptado no es ejercido: este auditor mide la diferencia.

Compara la historia git de un repo adoptado contra sus registros de
`.lifecycle/changes/` y responde con números: cuántos commits, cuántos
cambios abiertos, hasta qué peldaño subió cada uno (observación →
diagnóstico → ... → cierre). Una escalera instalada y muda produce
exactamente la firma que este auditor declara.

Solo lectura, solo stdlib, asesor: reporta, jamás bloquea.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

RECORD_PATTERN = re.compile(r"^(\d{3})-([a-z_-]+)\.env$")
KINDS_CIERRE = {"closure", "cierre"}
KINDS_DIAGNOSTICO = {"diagnosis", "diagnostico"}


@dataclass(frozen=True)
class Cambio:
    cambio_id: str
    registros: tuple[str, ...]

    @property
    def tiene_diagnostico(self) -> bool:
        return any(r in KINDS_DIAGNOSTICO for r in self.registros)

    @property
    def tiene_cierre(self) -> bool:
        return any(r in KINDS_CIERRE for r in self.registros)

    @property
    def solo_observacion(self) -> bool:
        return self.registros == ("observation",)


@dataclass(frozen=True)
class Auditoria:
    commits_total: int
    commits_desde_adopcion: int | None
    adoptado_desde: str
    cambios: tuple[Cambio, ...]

    @property
    def solo_observacion(self) -> int:
        return sum(1 for c in self.cambios if c.solo_observacion)

    @property
    def con_diagnostico(self) -> int:
        return sum(1 for c in self.cambios if c.tiene_diagnostico)

    @property
    def con_cierre(self) -> int:
        return sum(1 for c in self.cambios if c.tiene_cierre)

    @property
    def veredicto(self) -> str:
        commits = (
            self.commits_desde_adopcion
            if self.commits_desde_adopcion is not None
            else self.commits_total
        )
        if not self.cambios and commits == 0:
            return "SIN_ACTIVIDAD"
        if self.con_cierre == 0 and commits > 0:
            return "ESCALERA_MUDA"
        if commits > 0 and self.con_cierre * 10 < commits:
            return "ESCALERA_PARCIAL"
        return "ESCALERA_VIVA"


def _git(repo: Path, *args: str) -> str:
    proceso = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if proceso.returncode != 0:
        raise ValueError(f"git {' '.join(args[:2])}: {proceso.stderr.strip()[:200]}")
    return proceso.stdout


def _primer_adopcion(target: Path) -> str:
    """Timestamp ISO de la adopción más vieja registrada, o ''."""
    state = target / ".lifecycle" / "state" / "skills"
    fechas = []
    if state.is_dir():
        for env in sorted(state.glob("*.env")):
            for linea in env.read_text(encoding="utf-8").splitlines():
                if linea.startswith("ADOPTED_AT="):
                    fechas.append(linea.split("=", 1)[1].strip().strip('"'))
    return min(fechas) if fechas else ""


def _leer_cambios(target: Path) -> tuple[Cambio, ...]:
    raiz = target / ".lifecycle" / "changes"
    cambios: list[Cambio] = []
    if not raiz.is_dir():
        return ()
    for carpeta in sorted(raiz.iterdir()):
        if not carpeta.is_dir():
            continue
        registros = []
        for archivo in sorted(carpeta.iterdir()):
            match = RECORD_PATTERN.match(archivo.name)
            if match:
                registros.append(match.group(2))
        cambios.append(Cambio(cambio_id=carpeta.name, registros=tuple(registros)))
    return tuple(cambios)


def auditar(target: Path) -> Auditoria:
    objetivo = target.resolve(strict=True)
    commits_total = int(_git(objetivo, "rev-list", "--count", "HEAD").strip())
    adoptado = _primer_adopcion(objetivo)
    commits_desde = None
    if adoptado:
        salida = _git(objetivo, "rev-list", "--count", f"--since={adoptado}", "HEAD")
        commits_desde = int(salida.strip())
    return Auditoria(
        commits_total=commits_total,
        commits_desde_adopcion=commits_desde,
        adoptado_desde=adoptado or "N/D",
        cambios=_leer_cambios(objetivo),
    )
