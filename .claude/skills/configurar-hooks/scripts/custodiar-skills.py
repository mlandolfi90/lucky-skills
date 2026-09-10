"""Custodia de skills (PreToolUse): editar una skill exige permiso explícito.

Regla de la flota: una sesión sola jamás modifica una skill. Este hook no
bloquea — convierte la escritura en un PEDIDO DE PERMISO que el operador ve y
decide. La edición autorizada sigue siendo posible; la silenciosa deja de serlo.

Cubre las herramientas Edit/Write/MultiEdit/NotebookEdit. Una escritura por
shell (sed, heredoc) NO pasa por acá: límite declarado, no tapado.
Cualquier error del propio hook degrada a no-opinar (fail-open): la custodia
no puede romper la edición de archivos normales.

Fuente de verdad: lucky-skills, skills/configurar-hooks/scripts/custodiar-skills.py,
sellada con la skill configurar-hooks. La copia que corre en cada sesión vive
en ~/.claude/hooks/ y es byte a byte esta; se instala desde la skill adoptada
y no se edita a mano. Hasta el 2026-09-10 vivió solo en disco, sin historial.

Dónde está el Taller lo dice la máquina, no este archivo: la variable de
entorno LUCKY_TALLER o, si falta, la línea TALLER= de `custodia.env` junto a
la copia instalada (plantilla: custodia.env.example). Sin declaración, la
custodia del Taller no opina; la de skills sí, porque no depende de rutas.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path, PurePosixPath

PROTEGIDOS = {"SKILL.md", "manifest.env"}
VARIABLE = "LUCKY_TALLER"
ARCHIVO = "custodia.env"


def taller() -> Path | None:
    """El catálogo en esta máquina, si está declarado. None si no lo está."""
    bruto = os.environ.get(VARIABLE, "").strip()
    if not bruto:
        bruto = _de_archivo(Path(__file__).resolve().parent / ARCHIVO)
    return Path(bruto) if bruto else None


def _de_archivo(ruta: Path) -> str:
    try:
        texto = ruta.read_text(encoding="utf-8")
    except OSError:
        return ""
    for linea in texto.splitlines():
        if linea.startswith("TALLER="):
            return linea.split("=", 1)[1].strip().strip('"')
    return ""


def es_taller_desde_afuera(bruto: str, cwd: str, taller_declarado: Path | None) -> bool:
    """True si el destino está en el catálogo y la sesión no corre en él.

    Regla de la flota: sólo la sesión del Taller escribe en el Taller. Una
    sesión con cwd en otro repo que escribe acá —un /actualizar-skills
    apuntado mal, un registro, un revalidar— pide permiso antes.
    """
    if taller_declarado is None:
        return False
    try:
        taller_real = taller_declarado.resolve()
        destino = Path(bruto).resolve()
        origen = Path(cwd).resolve() if cwd else None
    except (OSError, ValueError):
        return False
    if destino != taller_real and taller_real not in destino.parents:
        return False
    if origen is not None and (origen == taller_real or taller_real in origen.parents):
        return False
    return True


def es_skill(bruto: str) -> bool:
    """True si la ruta apunta a un archivo de skill.

    Dos formas de serlo:
    - un SKILL.md / manifest.env cuyo directorio cuelga de una carpeta llamada
      exactamente `skills` (el catálogo y las copias adoptadas en repos);
    - cualquier archivo bajo una carpeta `.claude/skills/` (las copias
      instaladas que el harness carga).
    Las tareas programadas también usan SKILL.md pero viven en
    `scheduled-tasks/`, no en `skills/`: quedan fuera a propósito.
    """
    ruta = PurePosixPath(bruto.replace("\\", "/"))
    partes = ruta.parts
    if ".claude" in partes:
        i = partes.index(".claude")
        if i + 1 < len(partes) and partes[i + 1] == "skills":
            return True
    if ruta.name in PROTEGIDOS and len(partes) >= 3 and partes[-3] == "skills":
        return True
    return False


def main() -> int:
    datos = json.load(sys.stdin)
    objetivo = datos.get("tool_input", {}).get("file_path") or \
        datos.get("tool_input", {}).get("notebook_path") or ""
    if not objetivo:
        return 0
    cwd = datos.get("cwd") or ""
    if es_skill(str(objetivo)):
        motivo = (
            "CUSTODIA DE SKILLS - este archivo es una skill. Regla de la "
            "flota: modificarla exige autorizacion explicita del operador, "
            "y las modificaciones del catalogo salen de la sesion del "
            "Taller por la escalera (nunca editando una copia). Si el "
            "operador pidio 'actualizar', quiso ADOPTAR la version "
            "publicada, no editar el archivo. Si no autorizo ESTA "
            "modificacion en esta conversacion, frena y pedisela."
        )
    elif es_taller_desde_afuera(str(objetivo), cwd, taller()):
        motivo = (
            "CUSTODIA DEL TALLER - este archivo esta en el catalogo "
            "lucky-skills y esta sesion NO corre ahi. Regla de la flota: "
            "solo la sesion del Taller escribe en el Taller. Si el operador "
            "pidio explicitamente escribir aca desde esta sesion, segui; "
            "si no, frena y avisale que lo haga desde el Taller."
        )
    else:
        return 0
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": motivo,
        }
    }))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 - la custodia jamás rompe una edición ajena
        sys.exit(0)
