from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import ADAPTER_ROOT

sys.path.insert(0, str(ADAPTER_ROOT))

from sonda_abierto_cerrado.scanner import escanear  # noqa: E402


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


class SondaAbiertoCerradoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        _git(self.repo, "init", "-q")
        _git(self.repo, "config", "user.email", "test@example.invalid")
        _git(self.repo, "config", "user.name", "Test")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _commit(self, mensaje: str) -> None:
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", mensaje)

    def _crecer(self, ruta: Path, lineas: list[str], mensaje: str) -> None:
        with ruta.open("a", encoding="utf-8") as f:
            f.write("\n".join(lineas) + "\n")
        self._commit(mensaje)

    def test_registro_que_crece_por_edicion_es_candidato(self) -> None:
        registro = self.repo / "catalogo-widgets.js"
        registro.write_text("export const TIPOS = {\n};\n", encoding="utf-8")
        self._commit("nace el catalogo")
        self._crecer(registro, ["// tipo nota"], "agrega nota")
        self._crecer(registro, ["// tipo tarea"], "agrega tarea")

        candidatos = escanear(self.repo)
        rutas = [c.ruta for c in candidatos]
        self.assertIn("catalogo-widgets.js", rutas)
        top = candidatos[0]
        self.assertTrue(top.pista_nombre)
        self.assertEqual(top.ediciones_aditivas, 2)

    def test_churn_mezclado_no_es_candidato(self) -> None:
        # Un componente en desarrollo activo agrega Y reescribe: no es un
        # registro, y la sonda no debe gritarle.
        comp = self.repo / "vista.js"
        comp.write_text("linea\n" * 10, encoding="utf-8")
        self._commit("nace la vista")
        for i in range(3):
            comp.write_text("otra\n" * (8 + i), encoding="utf-8")  # reescritura
            self._commit(f"reescribe {i}")

        candidatos = escanear(self.repo)
        self.assertEqual([c.ruta for c in candidatos], [])

    def test_registro_ya_eliminado_no_grita(self) -> None:
        # Si el registro se refactorizó (ya no existe), el problema está
        # resuelto: la sonda mira archivos vivos.
        registro = self.repo / "registry-tipos.py"
        registro.write_text("TIPOS = []\n", encoding="utf-8")
        self._commit("nace")
        self._crecer(registro, ["# uno"], "agrega uno")
        self._crecer(registro, ["# dos"], "agrega dos")
        _git(self.repo, "rm", "-q", "registry-tipos.py")
        self._commit("refactor: el registro sale a carpetas")

        candidatos = escanear(self.repo)
        self.assertEqual([c.ruta for c in candidatos], [])

    def test_sin_pista_de_nombre_exige_mas_evidencia(self) -> None:
        plano = self.repo / "handlers.js"
        plano.write_text("export const H = {\n};\n", encoding="utf-8")
        self._commit("nace")
        self._crecer(plano, ["// h1"], "agrega h1")
        self._crecer(plano, ["// h2"], "agrega h2")
        # 2 aditivas sin pista: NO alcanza…
        self.assertEqual([c.ruta for c in escanear(self.repo)], [])
        # …con la tercera, sí.
        self._crecer(plano, ["// h3"], "agrega h3")
        self.assertEqual([c.ruta for c in escanear(self.repo)], ["handlers.js"])

    def test_features_inconexas_marcan_temas(self) -> None:
        # Dos features que no comparten NADA abren el mismo registro: la
        # firma del discriminante (aporte PizarraEvo 2026-08-03).
        registro = self.repo / "catalogo-rutas.js"
        registro.write_text("export const R = {\n};\n", encoding="utf-8")
        self._commit("nace")
        (self.repo / "feature_a.js").write_text("// a\n", encoding="utf-8")
        with registro.open("a", encoding="utf-8") as f:
            f.write("// ruta de a\n")
        self._commit("feature a")
        (self.repo / "feature_b.js").write_text("// b\n", encoding="utf-8")
        with registro.open("a", encoding="utf-8") as f:
            f.write("// ruta de b\n")
        self._commit("feature b")

        candidatos = escanear(self.repo)
        top = candidatos[0]
        self.assertEqual(top.ruta, "catalogo-rutas.js")
        self.assertEqual(top.temas, "INCONEXOS")

    def test_raiz_de_composicion_se_rotula_y_baja(self) -> None:
        # Un archivo que solo cablea (imports/wiring) crece por diseño:
        # se marca y va al fondo del ranking, no se calla.
        raiz = self.repo / "index-tipos.js"
        raiz.write_text(
            "import a from './a.js'\nimport b from './b.js'\n"
            "export { a } from './a.js'\n",
            encoding="utf-8",
        )
        self._commit("nace la raiz")
        self._crecer(raiz, ["import c from './c.js'"], "cablea c")
        self._crecer(raiz, ["import d from './d.js'"], "cablea d")

        candidatos = escanear(self.repo)
        top = candidatos[0]
        self.assertEqual(top.ruta, "index-tipos.js")
        self.assertTrue(top.raiz_composicion)

    def test_ventana_reciente_modo_hook(self) -> None:
        registro = self.repo / "tipos-index.js"
        registro.write_text("export const X = {\n};\n", encoding="utf-8")
        self._commit("nace")
        self._crecer(registro, ["// a"], "agrega a")
        self._crecer(registro, ["// b"], "agrega b")
        candidatos = escanear(self.repo, ultimos=3)
        self.assertEqual(candidatos[0].ruta, "tipos-index.js")


if __name__ == "__main__":
    unittest.main()
