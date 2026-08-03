"""La huella describe CONTENIDO VERSIONADO, no el transporte de bytes.

Caso que lo motivó (Lucky-PizarraEvo, 2026-08-03): con `core.autocrlf` git
reescribe finales de línea al bajar los archivos, así que un clon del mismo
commit producía una huella distinta a la del árbol que la selló — y
`revalidar` no convergía nunca. Los vectores golden de `conformance-v1.json`
pinnean el hash de registros DADOS; nadie pinneaba los registros EMITIDOS,
así que la suite entera pasaba con la huella rota.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import ADAPTER_ROOT

sys.path.insert(0, str(ADAPTER_ROOT))

from sextante.local_probe import probe_local  # noqa: E402

SONDA = dict(timeout_seconds=30, max_entries=1000)


class HuellaReproducibleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _workspace(self, nombre: str, contenido: bytes) -> Path:
        raiz = self.base / nombre
        (raiz / "src").mkdir(parents=True)
        (raiz / "src" / "modulo.txt").write_bytes(contenido)
        return raiz

    def test_mismo_contenido_distinto_fin_de_linea_misma_huella(self) -> None:
        lf = self._workspace("lf", b"alfa\nbeta\ngamma\n")
        crlf = self._workspace("crlf", b"alfa\r\nbeta\r\ngamma\r\n")
        con_lf, _ = probe_local(lf, **SONDA)
        con_crlf, _ = probe_local(crlf, **SONDA)
        self.assertEqual(con_lf.fingerprint, con_crlf.fingerprint)

    def test_contenido_distinto_sigue_dando_huellas_distintas(self) -> None:
        # Control: la normalización no puede volverla ciega al contenido.
        uno = self._workspace("uno", b"alfa\nbeta\n")
        otro = self._workspace("otro", b"alfa\nbetaX\n")
        a, _ = probe_local(uno, **SONDA)
        b, _ = probe_local(otro, **SONDA)
        self.assertNotEqual(a.fingerprint, b.fingerprint)

    def test_binario_no_se_normaliza(self) -> None:
        # Un binario con la secuencia CRLF adentro no se toca: cambiarle bytes
        # sería corromper la identidad de un archivo que git tampoco convierte.
        uno = self._workspace("bin-crlf", b"\x00\x01alfa\r\nbeta\x00")
        otro = self._workspace("bin-lf", b"\x00\x01alfa\nbeta\x00")
        a, _ = probe_local(uno, **SONDA)
        b, _ = probe_local(otro, **SONDA)
        self.assertNotEqual(a.fingerprint, b.fingerprint)

    def test_cr_suelto_no_se_toca(self) -> None:
        # git convierte CRLF, no CR solitario: el contrato lo copia.
        uno = self._workspace("cr", b"alfa\rbeta\n")
        otro = self._workspace("sin-cr", b"alfabeta\n")
        a, _ = probe_local(uno, **SONDA)
        b, _ = probe_local(otro, **SONDA)
        self.assertNotEqual(a.fingerprint, b.fingerprint)

    def test_crlf_partido_entre_chunks(self) -> None:
        # El normalizador es de streaming: un CR al final de un chunk y su LF
        # al principio del siguiente tienen que unirse igual.
        from sextante.file_fingerprint import CHUNK_BYTES, _EolNormalizer

        relleno = b"x" * (CHUNK_BYTES - 1)
        grande = self._workspace("grande", relleno + b"\r\nfin\n")
        chico = self._workspace("chico", relleno + b"\nfin\n")
        a, _ = probe_local(grande, **SONDA)
        b, _ = probe_local(chico, **SONDA)
        self.assertEqual(a.fingerprint, b.fingerprint)

        # Y directo sobre el normalizador, sin depender del tamaño de chunk.
        n = _EolNormalizer()
        salida = n.feed(b"alfa\r") + n.feed(b"\nbeta") + n.finish()
        self.assertEqual(salida, b"alfa\nbeta")


class HuellaSobreviveAlClonTests(unittest.TestCase):
    """La propiedad que importa de verdad: clon y árbol coinciden."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _git(self, repo: Path, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
        )

    def test_clon_del_mismo_commit_reproduce_la_huella(self) -> None:
        repo = self.base / "repo"
        repo.mkdir()
        self._git(repo, "init", "-q")
        self._git(repo, "config", "user.email", "test@example.invalid")
        self._git(repo, "config", "user.name", "Test")
        # autocrlf=true es la condición que rompía la huella: el clon baja los
        # archivos con CRLF aunque el repositorio guarde LF.
        self._git(repo, "config", "core.autocrlf", "true")
        (repo / "doc.md").write_bytes(b"linea uno\nlinea dos\n")
        (repo / "codigo.py").write_bytes(b"print('hola')\n")
        self._git(repo, "add", "-A")
        self._git(repo, "commit", "-q", "-m", "contenido")

        clone = self.base / "clon"
        subprocess.run(
            ["git", "clone", "-q", "-c", "core.autocrlf=true", str(repo), str(clone)],
            check=True,
            capture_output=True,
        )

        original, _ = probe_local(repo, **SONDA)
        copia, _ = probe_local(clone, **SONDA)
        self.assertEqual(original.fingerprint, copia.fingerprint)
        self.assertEqual(original.dirty_count, copia.dirty_count)


if __name__ == "__main__":
    unittest.main()
