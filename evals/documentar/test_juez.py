"""Calibración del juez con canarios (regla 2 del spec).

Un juez que reprueba un canario bueno está roto ÉL, no la skill (lección del
issue #175 de microsoft/SkillOpt). Un juez que aprueba un canario malo es
decoración (FALSO-VERDE-012: probá el test con el mutante).
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

import juez  # noqa: E402

FIXTURE = RAIZ / "fixture"
GOLD = json.loads((RAIZ / "gold.json").read_text(encoding="utf-8"))
CANARIOS = RAIZ / "canarios"


def correr(nombre: str, baseline: dict | None = None) -> dict:
    texto = (CANARIOS / nombre).read_text(encoding="utf-8")
    return juez.evaluar(FIXTURE, GOLD, texto, baseline)


def casos_por_id(reporte: dict) -> dict:
    return {c["id"]: c for c in reporte["casos"]}


class CalibracionCanarios(unittest.TestCase):
    def test_bueno_pasa(self) -> None:
        reporte = correr("bueno.txt")
        self.assertEqual(reporte["verdict"], "PASS", reporte)
        self.assertEqual(reporte["metricas"]["precision"], 1.0)
        self.assertEqual(reporte["metricas"]["recall"], 1.0)
        self.assertEqual(reporte["extras"], [])
        self.assertTrue(reporte["schema"]["ok"])

    def test_formato_raro_tambien_pasa(self) -> None:
        # Anti-#175: mismo contenido, otro orden, prosa intercalada,
        # headings numerados, indentación — el juez no castiga formato.
        reporte = correr("bueno_formato_raro.txt")
        self.assertEqual(reporte["verdict"], "PASS", reporte)
        self.assertEqual(reporte["metricas"]["precision"], 1.0)
        self.assertEqual(reporte["metricas"]["recall"], 1.0)

    def test_falso_positivo_cae(self) -> None:
        reporte = correr("falso_positivo.txt")
        self.assertEqual(reporte["verdict"], "FAIL")
        self.assertEqual(casos_por_id(reporte)["C1"]["resultado"], "FAIL")
        self.assertLess(reporte["metricas"]["precision"], 1.0)
        # El resto de los drifts reales siguen bien detectados.
        self.assertEqual(reporte["metricas"]["recall"], 1.0)

    def test_cita_rota_cae(self) -> None:
        reporte = correr("cita_rota.txt")
        self.assertEqual(reporte["verdict"], "FAIL")
        c3 = casos_por_id(reporte)["C3"]
        self.assertEqual(c3["cita"], "ROTA")
        self.assertEqual(c3["resultado"], "FAIL")

    def test_incompleto_cae_por_recall(self) -> None:
        reporte = correr("incompleto.txt")
        self.assertEqual(reporte["verdict"], "FAIL")
        self.assertEqual(casos_por_id(reporte)["C2"]["obtenido"], "AUSENTE")
        self.assertAlmostEqual(reporte["metricas"]["recall"], 2 / 3, places=3)

    def test_contador_inflado_cae_por_schema(self) -> None:
        # Goodhart barato: inflar DRIFT_FOUND sin listar los hallazgos.
        reporte = correr("contador_inflado.txt")
        self.assertEqual(reporte["verdict"], "FAIL")
        self.assertFalse(reporte["schema"]["ok"])

    def test_adivinador_cae_por_disciplina_unverified(self) -> None:
        # Lo incomprobable se declara UNVERIFIED; marcarlo DRIFT es adivinar.
        reporte = correr("adivinador.txt")
        self.assertEqual(reporte["verdict"], "FAIL")
        self.assertEqual(casos_por_id(reporte)["C6"]["resultado"], "FAIL")


class Regresiones(unittest.TestCase):
    def test_regresion_contra_baseline_es_fail(self) -> None:
        # Regla 4: un caso que pasaba y ahora falla es FAIL, sin promedios.
        baseline = correr("bueno.txt")
        reporte = correr("incompleto.txt", baseline=baseline)
        self.assertIn("C2", reporte["regresiones"])
        self.assertEqual(reporte["verdict"], "FAIL")

    def test_mejora_contra_baseline_malo_no_es_regresion(self) -> None:
        baseline = correr("incompleto.txt")
        reporte = correr("bueno.txt", baseline=baseline)
        self.assertEqual(reporte["regresiones"], [])
        self.assertEqual(reporte["verdict"], "PASS")


class ContratoCli(unittest.TestCase):
    def _correr_cli(self, canario: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-B", str(RAIZ / "juez.py"), "--salida", str(CANARIOS / canario)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )

    def test_exit_cero_en_pass(self) -> None:
        proceso = self._correr_cli("bueno.txt")
        self.assertEqual(proceso.returncode, 0, proceso.stdout + proceso.stderr)
        self.assertIn("VERDICT=PASS", proceso.stdout)

    def test_exit_uno_en_fail(self) -> None:
        proceso = self._correr_cli("incompleto.txt")
        self.assertEqual(proceso.returncode, 1, proceso.stdout + proceso.stderr)
        self.assertIn("VERDICT=FAIL", proceso.stdout)


if __name__ == "__main__":
    unittest.main()
