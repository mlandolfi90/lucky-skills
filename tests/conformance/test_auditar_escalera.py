from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import ADAPTER_ROOT

sys.path.insert(0, str(ADAPTER_ROOT))

from escalera_audit.auditor import auditar  # noqa: E402


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


class EscaleraAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        _git(self.repo, "init", "-q")
        _git(self.repo, "config", "user.email", "test@example.invalid")
        _git(self.repo, "config", "user.name", "Test")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _commit(self, n: int) -> None:
        for i in range(n):
            (self.repo / f"f{i}.txt").write_text(f"{i}\n", encoding="utf-8")
            _git(self.repo, "add", "-A")
            _git(self.repo, "commit", "-q", "-m", f"commit {i}")

    def _cambio(self, nombre: str, registros: list[str]) -> None:
        carpeta = self.repo / ".lifecycle" / "changes" / nombre
        carpeta.mkdir(parents=True)
        for indice, kind in enumerate(registros, 1):
            (carpeta / f"{indice:03d}-{kind}.env").write_text(
                'FORMAT_VERSION="1"\n', encoding="utf-8"
            )

    def test_commits_sin_cierre_es_escalera_muda(self) -> None:
        self._commit(5)
        self._cambio("change-0001-aa", ["observation"])
        self._cambio("change-0002-bb", ["observation"])

        resultado = auditar(self.repo)
        self.assertEqual(resultado.commits_total, 5)
        self.assertEqual(len(resultado.cambios), 2)
        self.assertEqual(resultado.solo_observacion, 2)
        self.assertEqual(resultado.con_cierre, 0)
        self.assertEqual(resultado.veredicto, "ESCALERA_MUDA")

    def test_escalera_completa_es_viva(self) -> None:
        self._commit(3)
        self._cambio(
            "change-0001-aa",
            ["observation", "diagnosis", "closure"],
        )
        resultado = auditar(self.repo)
        self.assertEqual(resultado.con_diagnostico, 1)
        self.assertEqual(resultado.con_cierre, 1)
        self.assertEqual(resultado.veredicto, "ESCALERA_VIVA")

    def test_cierres_escasos_es_parcial(self) -> None:
        self._commit(25)
        self._cambio("change-0001-aa", ["observation", "closure"])
        resultado = auditar(self.repo)
        # 1 cierre para 25 commits: la escalera existe pero no acompaña.
        self.assertEqual(resultado.veredicto, "ESCALERA_PARCIAL")

    def test_sin_lifecycle_reporta_cero_cambios(self) -> None:
        self._commit(2)
        resultado = auditar(self.repo)
        self.assertEqual(len(resultado.cambios), 0)
        self.assertEqual(resultado.adoptado_desde, "N/D")
        self.assertEqual(resultado.veredicto, "ESCALERA_MUDA")

    def test_fecha_de_adopcion_acota_los_commits(self) -> None:
        self._commit(3)
        state = self.repo / ".lifecycle" / "state" / "skills"
        state.mkdir(parents=True)
        (state / "cambio.env").write_text(
            'FORMAT_VERSION="1"\nSKILL_ID="cambio"\n'
            'ADOPTED_AT="2099-01-01T00:00:00Z"\n',
            encoding="utf-8",
        )
        resultado = auditar(self.repo)
        self.assertEqual(resultado.commits_desde_adopcion, 0)
        self.assertEqual(resultado.adoptado_desde, "2099-01-01T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
