"""Los dos hooks globales de Claude Code que viajan en el catálogo.

`skills/ley-viva/scripts/ley-viva-aviso.py` y
`skills/configurar-hooks/scripts/custodiar-skills.py` corren en cada sesión
desde una copia byte a byte en ~/.claude/hooks/. Acá se prueban sin red y sin
tocar el disco del usuario: el catálogo publicado se reemplaza por un
diccionario y la marca de tiempo del aviso se manda a un temporal.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from support import ROOT

LEY_VIVA = ROOT / "skills" / "ley-viva" / "scripts" / "ley-viva-aviso.py"
CUSTODIA = ROOT / "skills" / "configurar-hooks" / "scripts" / "custodiar-skills.py"


def cargar(ruta: Path, nombre: str):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    assert spec is not None and spec.loader is not None
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def repo_adoptante(base: Path, adoptadas: dict[str, str]) -> Path:
    raiz = base / "repo"
    estado = raiz / ".lifecycle" / "state" / "skills"
    estado.mkdir(parents=True)
    for skill, version in adoptadas.items():
        (estado / f"{skill}.env").write_text(
            f'SKILL_ID="{skill}"\nSKILL_VERSION="{version}"\n', encoding="utf-8"
        )
    (raiz / "adentro").mkdir()
    return raiz


class LeyVivaAvisoTest(unittest.TestCase):
    def setUp(self) -> None:
        self.modulo = cargar(LEY_VIVA, "ley_viva_aviso")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.cwd_original = os.getcwd()
        self.addCleanup(os.chdir, self.cwd_original)

    def correr(self, desde: Path, catalogo, argv: tuple[str, ...] = ()) -> str:
        salida = StringIO()
        os.chdir(desde)
        try:
            with mock.patch.object(self.modulo, "publicadas", return_value=catalogo), \
                    mock.patch.object(self.modulo, "_marca",
                                      return_value=self.base / "marca.stamp"), \
                    mock.patch.object(self.modulo.sys, "argv",
                                      ["ley-viva-aviso.py", *argv]), \
                    redirect_stdout(salida):
                codigo = self.modulo.main()
        finally:
            os.chdir(self.cwd_original)
        self.assertEqual(codigo, 0, "el aviso nunca bloquea")
        return salida.getvalue()

    def test_al_dia_se_afirma_solo_con_catalogo_leido(self) -> None:
        raiz = repo_adoptante(self.base, {"sextante": "2.0.2"})
        salida = self.correr(raiz, {"sextante": (2, 0, 2)})
        self.assertIn("CURRENCY=VERIFIED", salida)
        self.assertIn("ADOPTED=1 · CURRENT=1", salida)
        self.assertIn("al día", salida)

    def test_atras_distingue_fluida_de_adaptacion(self) -> None:
        raiz = repo_adoptante(self.base, {"sextante": "1.0.0", "cierre": "1.0.0"})
        salida = self.correr(raiz, {"sextante": (1, 0, 5), "cierre": (2, 0, 0)})
        self.assertIn("UPDATE_AVAILABLE: sextante 1.0.0->1.0.5", salida)
        self.assertIn("ADAPTATION_REQUIRED: cierre 1.0.0->2.0.0", salida)
        self.assertIn("CURRENT=0", salida)
        self.assertIn("Avisar no es actualizar", salida)

    def test_adelante_del_catalogo_no_es_al_dia(self) -> None:
        raiz = repo_adoptante(self.base, {"sextante": "9.9.9"})
        salida = self.correr(raiz, {"sextante": (1, 0, 0)})
        self.assertIn("ADOPTED_AHEAD: sextante 9.9.9 > 1.0.0 publicada", salida)
        self.assertIn("CURRENT=0", salida)
        self.assertNotIn("lo adoptado está al día", salida)

    def test_lo_nunca_adoptado_se_cuenta_no_se_lista(self) -> None:
        raiz = repo_adoptante(self.base, {"sextante": "1.0.0"})
        salida = self.correr(raiz, {"sextante": (1, 0, 0), "nueva": (1, 0, 0)})
        self.assertIn("NOT_ADOPTED=1", salida)
        self.assertNotIn("nueva", salida)

    def test_sin_catalogo_la_vigencia_es_unknown(self) -> None:
        raiz = repo_adoptante(self.base, {"sextante": "1.0.0"})
        salida = self.correr(raiz, None)
        self.assertIn("CATALOG=UNREACHABLE", salida)
        self.assertIn("CURRENCY=UNKNOWN", salida)
        self.assertNotIn("lo adoptado está al día", salida)

    def test_desde_una_subcarpeta_tambien_avisa(self) -> None:
        raiz = repo_adoptante(self.base, {"sextante": "1.0.0"})
        salida = self.correr(raiz / "adentro", {"sextante": (1, 0, 1)})
        self.assertIn("[ley-viva]", salida)

    def test_un_directorio_cualquiera_no_dice_nada(self) -> None:
        suelto = self.base / "suelto"
        suelto.mkdir()
        self.assertEqual(self.correr(suelto, {"sextante": (1, 0, 0)}), "")

    def test_el_recorte_se_declara(self) -> None:
        adoptadas = {f"skill-{i}": "1.0.0" for i in range(9)}
        raiz = repo_adoptante(self.base, adoptadas)
        salida = self.correr(raiz, {k: (1, 0, 1) for k in adoptadas})
        self.assertIn("y 3 más sin listar", salida)

    def test_el_throttle_calla_la_segunda_vez(self) -> None:
        raiz = repo_adoptante(self.base, {"sextante": "1.0.0"})
        primera = self.correr(raiz, {"sextante": (1, 0, 1)}, ("--throttle", "900"))
        segunda = self.correr(raiz, {"sextante": (1, 0, 1)}, ("--throttle", "900"))
        self.assertIn("[ley-viva]", primera)
        self.assertEqual(segunda, "")


class CustodiarSkillsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def correr(self, archivo: str = "", cwd: str = "", taller: Path | None = None,
               crudo: str | None = None):
        env = {k: v for k, v in os.environ.items() if k != "LUCKY_TALLER"}
        if taller is not None:
            env["LUCKY_TALLER"] = str(taller)
        texto = crudo if crudo is not None else json.dumps(
            {"tool_input": {"file_path": archivo}, "cwd": cwd}
        )
        salida = subprocess.run(
            [sys.executable, str(CUSTODIA)], input=texto, capture_output=True,
            text=True, timeout=60, check=False, env=env,
        )
        self.assertEqual(salida.returncode, 0, "la custodia nunca rompe una edición")
        return json.loads(salida.stdout) if salida.stdout.strip() else None

    def decision(self, respuesta) -> tuple[str, str]:
        self.assertIsNotNone(respuesta)
        especifico = respuesta["hookSpecificOutput"]
        return especifico["permissionDecision"], especifico["permissionDecisionReason"]

    def test_una_skill_del_catalogo_pide_permiso(self) -> None:
        decision, motivo = self.decision(
            self.correr(str(self.base / "repo" / "skills" / "cierre" / "SKILL.md"))
        )
        self.assertEqual(decision, "ask")
        self.assertIn("CUSTODIA DE SKILLS", motivo)

    def test_una_copia_instalada_pide_permiso(self) -> None:
        decision, _ = self.decision(
            self.correr(str(self.base / ".claude" / "skills" / "cierre" / "notas.md"))
        )
        self.assertEqual(decision, "ask")

    def test_un_archivo_comun_no_opina(self) -> None:
        self.assertIsNone(self.correr(str(self.base / "repo" / "src" / "main.py")))

    def test_una_tarea_programada_queda_fuera(self) -> None:
        ruta = self.base / "scheduled-tasks" / "diaria" / "SKILL.md"
        self.assertIsNone(self.correr(str(ruta)))

    def test_el_taller_desde_afuera_pide_permiso(self) -> None:
        taller = self.base / "lucky-skills"
        otro = self.base / "otro-repo"
        taller.mkdir()
        otro.mkdir()
        decision, motivo = self.decision(
            self.correr(str(taller / "README.md"), cwd=str(otro), taller=taller)
        )
        self.assertEqual(decision, "ask")
        self.assertIn("CUSTODIA DEL TALLER", motivo)

    def test_el_taller_desde_adentro_no_opina(self) -> None:
        taller = self.base / "lucky-skills"
        taller.mkdir()
        self.assertIsNone(
            self.correr(str(taller / "README.md"), cwd=str(taller), taller=taller)
        )

    def test_sin_taller_declarado_esa_mitad_no_opina(self) -> None:
        taller = self.base / "lucky-skills"
        otro = self.base / "otro-repo"
        taller.mkdir()
        otro.mkdir()
        self.assertIsNone(self.correr(str(taller / "README.md"), cwd=str(otro)))

    def test_una_entrada_rota_no_rompe_nada(self) -> None:
        self.assertIsNone(self.correr(crudo="esto no es json"))


if __name__ == "__main__":
    unittest.main()
