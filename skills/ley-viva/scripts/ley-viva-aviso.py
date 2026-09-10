"""Aviso de vigencia al inicio de sesión (ADVISORY, jamás bloquea).

Compara las skills adoptadas del repo actual contra los tags publicados del
catálogo. Si el repo no adoptó nada, se calla y sale. Cualquier fallo degrada a
CURRENCY=UNKNOWN: se declara que no se sabe, nunca se afirma "al día".

Tres estados, no dos: atrás del catálogo (UPDATE_AVAILABLE o
ADAPTATION_REQUIRED) y también ADELANTE (ADOPTED_AHEAD), que no es estar al día
sino no tener explicación.

No enforcement, no escritura, sin secretos. Salida siempre exit 0.

Fuente de verdad: lucky-skills, skills/ley-viva/scripts/ley-viva-aviso.py,
sellada con la skill ley-viva. La copia que corre en cada sesión vive en
~/.claude/hooks/ y es byte a byte esta; se instala desde la skill adoptada y
no se edita a mano. Hasta el 2026-09-10 vivió solo en disco, sin historial
(lo midió lucky-tool-netbox).
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import time
from pathlib import Path

CATALOGO = "https://github.com/mlandolfi90/lucky-skills"
TAG = re.compile(r"refs/tags/skill-(?P<id>[a-z0-9][a-z0-9-]*)-v(?P<v>\d+\.\d+\.\d+)$")
TIEMPO_MAXIMO = 8
# Un aviso largo no se lee. Se recorta, pero el recorte SE DECLARA: un listado
# que trunca en silencio se lee como si fuera el total.
MAXIMO_LINEAS = 6


def raiz_adoptante(desde: Path) -> Path | None:
    """La carpeta con `.lifecycle/state/skills`, subiendo desde `desde`.

    Antes se asumia el directorio actual. Un hook que corre con el cwd en una
    subcarpeta no encontraba nada y salia callado, y "este repo no adopta el
    catalogo" se veia exactamente igual que "no mire donde habia que mirar".
    Un aviso que se calla por no encontrar es peor que uno que no existe.
    """
    for candidata in (desde, *desde.parents):
        if (candidata / ".lifecycle" / "state" / "skills").is_dir():
            return candidata
    return None


def adoptadas(raiz: Path) -> dict[str, tuple[int, int, int]]:
    """{skill_id: version} de lo instalado. Una entrada ilegible se saltea."""
    estado = raiz / ".lifecycle" / "state" / "skills"
    if not estado.is_dir():
        return {}
    fuera: dict[str, tuple[int, int, int]] = {}
    for archivo in sorted(estado.glob("*.env")):
        try:
            texto = archivo.read_text(encoding="utf-8")
        except OSError:
            continue
        identidad = _campo(texto, "SKILL_ID")
        version = _semver(_campo(texto, "SKILL_VERSION"))
        if identidad and version:
            fuera[identidad] = version
    return fuera


def _campo(texto: str, clave: str) -> str:
    for linea in texto.splitlines():
        if linea.startswith(f"{clave}="):
            return linea.split("=", 1)[1].strip().strip('"')
    return ""


def _semver(bruto: str) -> tuple[int, int, int] | None:
    partes = bruto.split(".")
    if len(partes) != 3 or not all(p.isdigit() for p in partes):
        return None
    return int(partes[0]), int(partes[1]), int(partes[2])


def publicadas() -> dict[str, tuple[int, int, int]] | None:
    """Última versión por skill según los tags del remoto. None si no se alcanzó."""
    try:
        salida = subprocess.run(
            ["git", "ls-remote", "--tags", CATALOGO],
            capture_output=True, text=True, timeout=TIEMPO_MAXIMO, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if salida.returncode != 0:
        return None
    fuera: dict[str, tuple[int, int, int]] = {}
    for linea in salida.stdout.splitlines():
        encaje = TAG.search(linea.strip())
        if not encaje:
            continue
        version = _semver(encaje.group("v"))
        identidad = encaje.group("id")
        if version and version > fuera.get(identidad, (-1, -1, -1)):
            fuera[identidad] = version
    return fuera or None


def _texto(v: tuple[int, int, int]) -> str:
    return ".".join(str(x) for x in v)


def _marca(raiz: Path) -> Path:
    """Una marca por workspace: dos repos distintos no se tapan el aviso."""
    clave = hashlib.sha256(str(raiz.resolve()).encode("utf-8")).hexdigest()[:16]
    return Path.home() / ".claude" / "hooks" / ".cache" / f"{clave}.stamp"


def _fresca(marca: Path, ventana: int) -> bool:
    try:
        return (time.time() - marca.stat().st_mtime) < ventana
    except OSError:
        return False


def _sellar(marca: Path) -> None:
    """Se sella pase lo que pase: un fallo tampoco debe golpear la red cada vez."""
    try:
        marca.parent.mkdir(parents=True, exist_ok=True)
        marca.write_text("", encoding="utf-8")
    except OSError:
        pass


def _ventana(argv: list[str]) -> int:
    """`--throttle <segundos>`; sin la bandera, 0 = comprobar siempre."""
    if "--throttle" in argv:
        indice = argv.index("--throttle") + 1
        if indice < len(argv) and argv[indice].isdigit():
            return int(argv[indice])
    return 0


def main() -> int:
    raiz = raiz_adoptante(Path.cwd())
    if raiz is None:
        return 0  # no hay repo adoptante por encima: no es asunto del hook
    instalado = adoptadas(raiz)
    if not instalado:
        return 0  # el directorio existe pero no declara nada legible

    ventana = _ventana(sys.argv[1:])
    marca = _marca(raiz)
    if ventana and _fresca(marca, ventana):
        return 0  # ya se avisó hace poco; el aviso no es un despertador
    _sellar(marca)

    catalogo = publicadas()
    if catalogo is None:
        print("[ley-viva] CATALOG=UNREACHABLE · CURRENCY=UNKNOWN — "
              "se trabaja con lo adoptado, sin afirmar que está al día.")
        return 0

    fluida: list[str] = []
    adaptacion: list[str] = []
    adelante: list[str] = []
    for identidad, tengo in sorted(instalado.items()):
        hay = catalogo.get(identidad)
        if hay is None or hay == tengo:
            continue
        if hay < tengo:
            # Adelante del catalogo no es al dia: es no tener explicacion. Sale
            # de adoptar una fuente sin sellar, o de un registro escrito a mano.
            # Este repo ya lo vivio: un SKILL_VERSION que no correspondia a
            # ningun tag publicado. Contado como "al dia", el aviso lo tapaba.
            adelante.append(f"{identidad} {_texto(tengo)} > {_texto(hay)} publicada")
            continue
        salto = f"{identidad} {_texto(tengo)}->{_texto(hay)}"
        (adaptacion if hay[0] > tengo[0] else fluida).append(salto)

    # Comparar sólo lo adoptado deja ciego al repo frente a una skill NUEVA:
    # diría "al día" mientras el catálogo creció. Se cuenta, no se lista — cuáles
    # convienen es decisión del repo, no del aviso.
    sin_adoptar = len(set(catalogo) - set(instalado))
    cola = f" · NOT_ADOPTED={sin_adoptar}" if sin_adoptar else ""

    if not fluida and not adaptacion and not adelante:
        print(f"[ley-viva] ADOPTED={len(instalado)} · CURRENT={len(instalado)} · "
              f"CURRENCY=VERIFIED{cola} — lo adoptado está al día.")
        return 0

    print(f"[ley-viva] ADOPTED={len(instalado)} · "
          f"CURRENT={len(instalado) - len(fluida) - len(adaptacion) - len(adelante)} · "
          f"CURRENCY=VERIFIED{cola}")
    mostradas = 0
    for etiqueta, saltos in (("ADOPTED_AHEAD", adelante),
                             ("ADAPTATION_REQUIRED", adaptacion),
                             ("UPDATE_AVAILABLE", fluida)):
        for salto in saltos:
            if mostradas >= MAXIMO_LINEAS:
                break
            print(f"[ley-viva] {etiqueta}: {salto}")
            mostradas += 1
    restantes = len(fluida) + len(adaptacion) + len(adelante) - mostradas
    if restantes:
        print(f"[ley-viva] ...y {restantes} más sin listar (aviso recortado, no es el total).")
    print("[ley-viva] Avisar no es actualizar: la transición la pide el humano.")
    return 0


if __name__ == "__main__":
    try:
        # Sin esto, en una consola cp1252 un solo carácter fuera de rango
        # convierte el aviso en un UnicodeEncodeError. El aviso no puede romperse
        # por su propia tipografía.
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.exit(main())
    except Exception as error:  # noqa: BLE001 - un aviso jamás rompe una sesión
        print(f"[ley-viva] CURRENCY=UNKNOWN — el aviso falló: "
              f"{type(error).__name__}. No bloquea.")
        sys.exit(0)
