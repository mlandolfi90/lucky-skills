"""El eje de harnesses crece agregando: una entrada, una carpeta.

Antes el mismo dato vivía copiado a mano en cinco lugares y agregar un
harness obligaba a abrirlos todos (saber CAP-2c80bf0aae72). Acá se pinea la
prueba de fuego: la entrada nueva entra tocando SOLO su propio archivo.

Y la colisión de identidad es FATAL, no un aviso (saber CAP-185236db9b3d):
el prefijo de proyección decide DÓNDE se escriben archivos, así que un
archivo que declara la identidad de otro harness redirige escrituras.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from support import ADAPTER_ROOT, ROOT

sys.path.insert(0, str(ADAPTER_ROOT))

from lifecycle_core.harness_catalog import (  # noqa: E402
    harness_ids,
    load_harnesses,
)


class CatalogoDeHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        (self.repo / "adapters").mkdir()
        self._declarar("claude-code", ".claude/skills", "NO")
        self._declarar("codex", ".agents/skills", "YES")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _declarar(self, nombre: str, prefijo: str, metadata: str, *, id_: str | None = None) -> Path:
        carpeta = self.repo / "adapters" / nombre
        carpeta.mkdir(parents=True, exist_ok=True)
        contrato = carpeta / "PACKAGING.env"
        contrato.write_text(
            'FORMAT_VERSION="1"\n'
            f'HARNESS_ID="{id_ or nombre}"\n'
            'OUTPUT_KIND="DIRECTORY"\n'
            f'SKILL_PREFIX="{prefijo}"\n'
            f'INCLUDE_OPENAI_METADATA="{metadata}"\n'
            'ARCHIVE_SUFFIX=""\n',
            encoding="utf-8",
            newline="\n",
        )
        return contrato

    def test_prueba_de_fuego_una_entrada_un_archivo(self) -> None:
        antes = harness_ids(self.repo)
        self.assertNotIn("harness-nuevo", antes)
        # Agregar un harness = dejar su archivo. Nada más se toca.
        self._declarar("harness-nuevo", ".nuevo/skills", "NO")
        despues = load_harnesses(self.repo)
        self.assertIn("harness-nuevo", despues)
        self.assertEqual(despues["harness-nuevo"].skill_prefix, ".nuevo/skills")
        # Y los que ya estaban no cambiaron.
        self.assertEqual(set(antes) - set(despues), set())

    def test_las_exclusiones_salen_del_propio_contrato(self) -> None:
        catalogo = load_harnesses(self.repo)
        # `agents/` es metadato OpenAI: viaja donde el harness lo declara.
        self.assertEqual(catalogo["claude-code"].projection_excludes, ("agents",))
        self.assertEqual(catalogo["codex"].projection_excludes, ())

    def test_prefijo_vacio_significa_sin_proyeccion(self) -> None:
        self._declarar("sin-proyeccion", "", "NO")
        catalogo = load_harnesses(self.repo)
        self.assertFalse(catalogo["sin-proyeccion"].projects)
        self.assertTrue(catalogo["claude-code"].projects)

    def test_identidad_usurpada_es_fatal(self) -> None:
        # La carpeta dice una cosa y el archivo otra: sin este gate, el
        # prefijo de `impostor` se serviría bajo el nombre de claude-code y
        # las escrituras irían a otro lado.
        self._declarar("impostor", ".impostor/skills", "NO", id_="claude-code")
        with self.assertRaisesRegex(ValueError, "no coincide con su carpeta"):
            load_harnesses(self.repo)

    def test_contrato_incompleto_es_fatal(self) -> None:
        carpeta = self.repo / "adapters" / "roto"
        carpeta.mkdir()
        (carpeta / "PACKAGING.env").write_text(
            'FORMAT_VERSION="1"\nHARNESS_ID="roto"\n', encoding="utf-8", newline="\n"
        )
        with self.assertRaisesRegex(ValueError, "faltan"):
            load_harnesses(self.repo)

    def test_carpeta_sin_contrato_no_es_un_harness(self) -> None:
        (self.repo / "adapters" / "reference_python").mkdir()
        (self.repo / "adapters" / "notas").mkdir()
        self.assertEqual(set(harness_ids(self.repo)), {"claude-code", "codex"})

    def test_adopcion_y_empaquetado_son_ejes_distintos(self) -> None:
        # `generic` se adopta (instala la fuente canónica) pero no produce
        # artefacto. Conflacionar los dos ejes rompía el canary de release:
        # lo destapó agregar generic al catálogo, no un test escrito antes.
        from lifecycle_core.harness_catalog import packageable_harness_ids

        self._declarar("solo-adopcion", "", "NO")
        carpeta = self.repo / "adapters" / "solo-adopcion" / "PACKAGING.env"
        carpeta.write_text(
            carpeta.read_text(encoding="utf-8").replace(
                'OUTPUT_KIND="DIRECTORY"', 'OUTPUT_KIND="NONE"'
            ),
            encoding="utf-8",
            newline="\n",
        )
        catalogo = load_harnesses(self.repo)
        self.assertFalse(catalogo["solo-adopcion"].packageable)
        self.assertTrue(catalogo["claude-code"].packageable)
        self.assertIn("solo-adopcion", harness_ids(self.repo))
        self.assertNotIn("solo-adopcion", packageable_harness_ids(self.repo))

    def test_output_kind_invalido_es_fatal(self) -> None:
        contrato = self._declarar("raro", ".raro", "NO")
        contrato.write_text(
            contrato.read_text(encoding="utf-8").replace(
                'OUTPUT_KIND="DIRECTORY"', 'OUTPUT_KIND="INVENTADO"'
            ),
            encoding="utf-8",
            newline="\n",
        )
        with self.assertRaisesRegex(ValueError, "OUTPUT_KIND"):
            load_harnesses(self.repo)

    def test_catalogo_real_del_taller(self) -> None:
        catalogo = load_harnesses(ROOT)
        self.assertEqual(
            set(catalogo),
            {"generic", "claude-ai", "claude-code", "codex"},
        )
        self.assertEqual(catalogo["claude-code"].skill_prefix, ".claude/skills")
        self.assertEqual(catalogo["codex"].skill_prefix, ".agents/skills")
        self.assertFalse(catalogo["generic"].projects)

    def test_el_dato_no_esta_duplicado_en_codigo(self) -> None:
        # Mutante estructural: si alguien vuelve a escribir la tabla a mano,
        # este test lo caza. Las rutas de skills son harness-agnósticas.
        sospechosos = [
            ADAPTER_ROOT / "adopcion" / "planner.py",
            ADAPTER_ROOT / "skill_packaging" / "packager.py",
            ADAPTER_ROOT / "synchronization" / "registry.py",
        ]
        for ruta in sospechosos:
            texto = ruta.read_text(encoding="utf-8")
            for literal in ('".claude/skills"', '".agents/skills"'):
                self.assertNotIn(
                    literal,
                    texto,
                    f"{ruta.name} volvió a codificar el prefijo de un harness a mano",
                )


if __name__ == "__main__":
    unittest.main()
