"""La huella describe CONTENIDO VERSIONADO, no el transporte de bytes.

Caso que lo motivó (Lucky-PizarraEvo, 2026-08-03): con `core.autocrlf` git
reescribe finales de línea al bajar los archivos, así que un clon del mismo
commit producía una huella distinta a la del árbol que la selló — y
`revalidar` no convergía nunca. Los vectores golden de `conformance-v1.json`
pinnean el hash de registros DADOS; nadie pinneaba los registros EMITIDOS,
así que la suite entera pasaba con la huella rota.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import ADAPTER_ROOT

sys.path.insert(0, str(ADAPTER_ROOT))

from sextante.file_fingerprint import (  # noqa: E402
    WINDOWS_PATH_LIMIT,
    _fuera_de_alcance,
    _modo_observable,
    fingerprint_files,
)
from sextante.local_probe import probe_local  # noqa: E402

SONDA = dict(timeout_seconds=30, max_entries=1000)
LIMITES = dict(timeout_seconds=30, max_entries=1000)


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


class NoAlcanzarNoEsFaltarTests(unittest.TestCase):
    """Un archivo que existe y no se puede leer no es un archivo borrado.

    Windows corta las rutas en 260 caracteres; git las escribe igual porque
    usa su propia API. El archivo queda en disco y `lstat` no llega. Antes eso
    entraba como MISSING y el escaneo seguía declarándose COMPLETE, así que la
    huella salía distinta con cartel de ALIGNED. Medido en vivo sobre el mismo
    commit: ruta corta 0816f48a con 0 archivos fuera de alcance, ruta de 158
    chars 8921644e con 10 archivos de 260-266 — las dos diciendo COMPLETE.

    Lo grave no era la lectura: una huella así sellada en un STATE-MAP deja al
    repositorio reportando DRIFT para siempre.

    Los dos casos levantan FileNotFoundError, así que el errno no los separa;
    el largo de la ruta sí. Y separarlos importa en la otra dirección: borrar
    un archivo trackeado es trabajo corriente y no debe degradar nada.
    """

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_un_archivo_fuera_de_alcance_degrada_el_escaneo(self) -> None:
        if os.name != "nt":
            self.skipTest("el límite de ruta es de Windows")
        # No hace falta crear el archivo: `lstat` falla igual, y es
        # exactamente lo que pasa cuando git lo escribió y nosotros no
        # llegamos. Lo que se pinea es que el LARGO decide el veredicto.
        relleno = "d" * 120
        largo = f"{relleno}/{relleno}/archivo.md"
        self.assertGreaterEqual(len(str(self.workspace / largo)), WINDOWS_PATH_LIMIT)
        resultado = fingerprint_files(self.workspace, (largo,), **LIMITES)
        self.assertEqual(resultado.status, "PATH_LIMIT_REACHED")
        self.assertFalse(resultado.complete)

    def test_un_archivo_borrado_no_degrada_nada(self) -> None:
        # El caso corriente: git lo tiene en el índice y el humano lo borró.
        # Eso es un estado real y medido, no una medición fallida. Si esto
        # degradara, cualquier borrado sin commitear ensuciaría el veredicto.
        resultado = fingerprint_files(self.workspace, ("borrado.md",), **LIMITES)
        self.assertEqual(resultado.status, "COMPLETE")
        self.assertTrue(resultado.complete)

    def test_el_discriminante_es_el_largo_no_el_errno(self) -> None:
        if os.name != "nt":
            self.skipTest("el límite de ruta es de Windows")
        corto = self.workspace / "corto.md"
        largo = self.workspace / ("e" * (WINDOWS_PATH_LIMIT - len(str(self.workspace))))
        self.assertFalse(_fuera_de_alcance(corto))
        self.assertTrue(_fuera_de_alcance(largo))


class UnEjecutableSeMideComoCualquierArchivoTests(unittest.TestCase):
    """El modo sólo decide donde el sistema lo informa; donde lo fabrica, no.

    En Windows CPython sintetiza el bit de ejecución desde la EXTENSIÓN:
    `lstat` lo agrega para .bat/.cmd/.exe/.com y `fstat` nunca. El chequeo de
    estabilidad comparaba ambos, así que TODO ejecutable fallaba antes de leer
    un byte y salía por el camino que no registra contenido.

    Tres efectos del mismo origen, y el tercero es el grave:
      1. ningún repositorio Windows con un .bat podía adoptarse jamás
      2. esos archivos quedaban sucios para siempre con el árbol limpio
      3. su registro quedaba en ruta+estado+tamaño, así que dos ejecutables
         DISTINTOS del mismo tamaño producían la misma huella — la huella
         dejaba de describir el contenido, violando D-078

    Encontrado por la sesión de Suscripciones, que no podía adoptar el Taller
    en un repositorio con tres .bat. La suite daba 229/3 idéntico antes y
    después del arreglo: no había un solo fixture ejecutable, y el módulo ya
    declaraba el modo inobservable en `_working_tree_mode` mientras el chequeo
    de estabilidad lo comparaba igual.
    """

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _escribir(self, nombre: str, contenido: bytes) -> None:
        (self.workspace / nombre).write_bytes(contenido)

    def test_un_ejecutable_no_rompe_el_escaneo(self) -> None:
        # El fixture que faltaba: sin un ejecutable real en el árbol, este
        # camino no se recorría en ninguna dirección.
        self._escribir("script.bat", b"@echo off\r\n")
        self._escribir("otro.cmd", b"rem x\r\n")
        self._escribir("legible.txt", b"texto\n")
        resultado = fingerprint_files(
            self.workspace,
            ("script.bat", "otro.cmd", "legible.txt"),
            **LIMITES,
        )
        self.assertEqual(resultado.status, "COMPLETE")
        self.assertTrue(resultado.complete)

    def test_dos_ejecutables_distintos_del_mismo_tamano_no_comparten_huella(
        self,
    ) -> None:
        # La propiedad de integridad. Con el defecto, ambos registros eran
        # ENTRY|ruta|estado|tamaño y el contenido no entraba: mismo tamaño,
        # misma huella. Un ejecutable podía cambiar sin que nadie lo notara.
        #
        # MISMA RUTA en dos árboles distintos, y no dos rutas en uno: la ruta
        # ENTRA en el registro, así que dos nombres distintos dan material
        # distinto aunque el contenido nunca se lea. Ese test pasaría con el
        # defecto puesto y no probaría nada — lo destapó el mutante.
        primero = self.workspace / "uno"
        segundo = self.workspace / "dos"
        primero.mkdir()
        segundo.mkdir()
        (primero / "x.bat").write_bytes(b"@echo AAA")
        (segundo / "x.bat").write_bytes(b"@echo BBB")
        self.assertEqual(
            (primero / "x.bat").stat().st_size,
            (segundo / "x.bat").stat().st_size,
            "el fixture pierde sentido si los tamaños difieren",
        )
        uno = fingerprint_files(primero, ("x.bat",), **LIMITES)
        otro = fingerprint_files(segundo, ("x.bat",), **LIMITES)
        self.assertNotEqual(uno.material, otro.material)

    def test_el_modo_decide_solo_donde_el_sistema_lo_informa(self) -> None:
        # Un único predicado para las dos decisiones sobre el modo: antes
        # `_working_tree_mode` lo declaraba inobservable en Windows y
        # `_same_file` lo comparaba igual. Divergían.
        self.assertEqual(_modo_observable(), os.name != "nt")


if __name__ == "__main__":
    unittest.main()
