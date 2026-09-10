"""Pruebas del aviso de ley-viva contra el catálogo real. Se corren a mano:

    python skills/ley-viva/scripts/test_ley_viva_aviso.py
    python ~/.claude/hooks/test_ley_viva_aviso.py      (la copia instalada)

Existen porque una guarda sin prueba propia se pudre en silencio: el aviso
puede dejar de avisar y nada se pone en rojo, porque su trabajo es justamente
no molestar cuando todo está bien. Consultan el catálogo real por red; las
mismas situaciones, sin red, viven en tests/conformance/test_hooks_globales.py.

No necesitan pytest. Salen 0 si pasa todo, 1 si algo falla.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

HOOK = pathlib.Path(__file__).parent / "ley-viva-aviso.py"

#: Una skill publicada de verdad, con una versión que nadie va a alcanzar. Se
#: consulta el catálogo real: falsearlo probaría el doble, no el aviso.
SKILL_REAL = "sextante"
VERSION_IMPOSIBLE = "9.9.9"


def correr(cwd: pathlib.Path) -> str:
    """El aviso tal como lo ve el harness: su salida, desde ese directorio."""
    salida = subprocess.run(  # noqa: S603 - argumentos fijos, sin shell
        [sys.executable, str(HOOK)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert salida.returncode == 0, f"el aviso salió con {salida.returncode}: nunca bloquea"
    return salida.stdout + salida.stderr


def repo_adoptante(base: pathlib.Path, version: str) -> pathlib.Path:
    """Un repo que declara `SKILL_REAL` en la versión pedida, con subcarpeta."""
    raiz = base / "repo"
    estado = raiz / ".lifecycle" / "state" / "skills"
    estado.mkdir(parents=True)
    (estado / f"{SKILL_REAL}.env").write_text(
        f'SKILL_ID="{SKILL_REAL}"\nSKILL_VERSION="{version}"\n', encoding="utf-8"
    )
    (raiz / "adentro" / "hondo").mkdir(parents=True)
    return raiz


def test_avisa_desde_una_subcarpeta(base: pathlib.Path) -> None:
    """La raíz se busca hacia arriba; antes se asumía el directorio actual.

    Con `Path.cwd()`, un hook lanzado desde una subcarpeta no encontraba
    `.lifecycle/state/skills` y salía callado. "Este repo no adopta el
    catálogo" se veía igual que "no miré donde había que mirar".
    """
    raiz = repo_adoptante(base, VERSION_IMPOSIBLE)

    for desde in (raiz, raiz / "adentro", raiz / "adentro" / "hondo"):
        assert "[ley-viva]" in correr(desde), f"silencio desde {desde}"


def test_adelante_del_catalogo_no_es_al_dia(base: pathlib.Path) -> None:
    """Una versión adoptada mayor que la publicada no tiene explicación.

    Sale de adoptar una fuente sin sellar o de un registro escrito a mano. La
    versión anterior la contaba como al día (`if hay <= tengo: continue`) y el
    aviso tapaba exactamente el caso que este repo ya vivió una vez.
    """
    salida = correr(repo_adoptante(base, VERSION_IMPOSIBLE))

    assert "ADOPTED_AHEAD" in salida, salida
    assert "CURRENT=0" in salida, salida
    assert "está al día" not in salida, salida


def test_atras_del_catalogo_se_reporta_como_atras(base: pathlib.Path) -> None:
    """El otro lado del mismo eje, que es el trabajo normal del aviso.

    Se pide 0.0.1: cualquier versión publicada le gana. No se afirma CUÁL de
    las dos etiquetas —`UPDATE_AVAILABLE` o `ADAPTATION_REQUIRED`— porque eso
    depende de si el salto cruza una mayor, y hoy cruza. Atarlo a la etiqueta
    exacta haría fallar esta prueba el día que la skill publique una mayor
    nueva, sin que nada esté mal.
    """
    salida = correr(repo_adoptante(base, "0.0.1"))

    assert "UPDATE_AVAILABLE" in salida or "ADAPTATION_REQUIRED" in salida, salida
    assert "ADOPTED_AHEAD" not in salida, salida


def test_un_directorio_cualquiera_no_dice_nada(base: pathlib.Path) -> None:
    """Buscar hacia arriba no puede convertir a cualquier carpeta en un repo."""
    suelto = base / "sin-nada"
    suelto.mkdir()

    assert correr(suelto).strip() == "", "avisó sobre un directorio que no adopta"


def main() -> int:
    pruebas = [
        test_avisa_desde_una_subcarpeta,
        test_adelante_del_catalogo_no_es_al_dia,
        test_atras_del_catalogo_se_reporta_como_atras,
        test_un_directorio_cualquiera_no_dice_nada,
    ]
    fallos = 0
    for prueba in pruebas:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                prueba(pathlib.Path(tmp))
            except AssertionError as error:
                print(f"FALLA  {prueba.__name__}: {error}")  # noqa: T201
                fallos += 1
            else:
                print(f"pasa   {prueba.__name__}")  # noqa: T201
    print(f"\n{len(pruebas) - fallos}/{len(pruebas)} pasan")  # noqa: T201
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
