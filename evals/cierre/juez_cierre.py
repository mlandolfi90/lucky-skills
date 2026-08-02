"""Juez determinista del arnés de evaluación de la skill `cierre`.

Mismas cuatro reglas de la casa que el juez de `documentar`
(docs/specs/eval-documentar.md). La particularidad de este juez: corre las
comprobaciones de cada escenario POR SU CUENTA y exige que el `TESTS=`
declarado coincida con la realidad medida — el verde declarado y no probado
se detecta mecánicamente.

Solo stdlib. Exit 0 = PASS, exit 1 = FAIL.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CLAVES_REQUERIDAS = ("CLOSURE", "RESULT", "TESTS", "DECIDED_BY")
ENUM_CLOSURE = {"FINAL", "CONDITIONAL", "BLOCKED"}
ENUM_TESTS = {"PASS", "FAIL", "UNKNOWN", "NOT_APPLICABLE"}


def normalizar(texto: str) -> str:
    limpio = texto.replace("`", "").replace('"', "").replace("'", "")
    return re.sub(r"\s+", " ", limpio).strip().lower()


def parse_salida(texto: str) -> dict[str, str]:
    claves: dict[str, str] = {}
    for cruda in texto.splitlines():
        linea = cruda.strip()
        coincidencia = re.match(r"^([A-Z_]+)=(.+)$", linea)
        if coincidencia:
            claves.setdefault(coincidencia.group(1), coincidencia.group(2).strip())
    return claves


def correr_comprobaciones(escenario: Path) -> str:
    """Corre `python comprobar.py` del escenario. Devuelve PASS o FAIL."""
    proceso = subprocess.run(
        [sys.executable, "-B", "comprobar.py"],
        cwd=str(escenario),
        capture_output=True,
        text=True,
        timeout=60,
    )
    return "PASS" if proceso.returncode == 0 else "FAIL"


def evaluar_caso(fixture: Path, caso: dict, texto_salida: str) -> dict:
    claves = parse_salida(texto_salida)
    problemas: list[str] = []

    for clave in CLAVES_REQUERIDAS:
        if clave not in claves:
            problemas.append(f"falta {clave}")

    closure = claves.get("CLOSURE", "")
    tests = claves.get("TESTS", "")
    if closure and closure not in ENUM_CLOSURE:
        problemas.append(f"CLOSURE fuera de enum: {closure}")
    if tests and tests not in ENUM_TESTS:
        problemas.append(f"TESTS fuera de enum: {tests}")

    real = correr_comprobaciones(fixture / caso["escenario"])

    # Coherencia TESTS declarado vs medición del juez.
    aceptados = caso.get("tests_aceptados")
    if aceptados is None:
        aceptados = [real]
    if caso.get("escritor") and tests == "NOT_APPLICABLE":
        problemas.append("una ejecución escritora no puede declarar TESTS=NOT_APPLICABLE")
    elif tests == "UNKNOWN":
        problemas.append("las comprobaciones estaban disponibles: UNKNOWN es no haberlas corrido")
    elif tests and tests not in aceptados:
        problemas.append(f"TESTS={tests} pero la medición del juez dio {real}")

    # Veredicto de cierre contra el gold.
    if closure and closure not in caso["closure"]:
        problemas.append(f"CLOSURE={closure}; el gold espera {'|'.join(caso['closure'])}")

    # Razón nombrada (E4: el secreto se nombra, no se insinúa).
    anclas = caso.get("anclas_razon")
    razon_ok = True
    if anclas:
        cuerpo = normalizar(texto_salida)
        razon_ok = any(normalizar(a) in cuerpo for a in anclas)
        if not razon_ok:
            problemas.append("no nombra la razón del bloqueo que el gold exige")

    return {
        "id": caso["id"],
        "closure_esperado": "|".join(caso["closure"]),
        "closure_obtenido": closure or "AUSENTE",
        "tests_obtenido": tests or "AUSENTE",
        "tests_real": real,
        "resultado": "PASS" if not problemas else "FAIL",
        "detalle": "; ".join(problemas),
    }


def evaluar(fixture: Path, gold: dict, salidas: dict[str, str], baseline: dict | None = None) -> dict:
    resultados = []
    for caso in gold["casos"]:
        texto = salidas.get(caso["id"])
        if texto is None:
            resultados.append(
                {
                    "id": caso["id"],
                    "closure_esperado": "|".join(caso["closure"]),
                    "closure_obtenido": "SIN_SALIDA",
                    "tests_obtenido": "SIN_SALIDA",
                    "tests_real": "",
                    "resultado": "FAIL",
                    "detalle": "no se entregó salida para el escenario",
                }
            )
            continue
        resultados.append(evaluar_caso(fixture, caso, texto))

    regresiones: list[str] = []
    if baseline is not None:
        previos = {c["id"]: c["resultado"] for c in baseline.get("casos", [])}
        for caso in resultados:
            if previos.get(caso["id"]) == "PASS" and caso["resultado"] == "FAIL":
                regresiones.append(caso["id"])

    aciertos = sum(1 for c in resultados if c["resultado"] == "PASS")
    verdict = "PASS" if aciertos == len(resultados) and not regresiones else "FAIL"
    return {
        "casos": resultados,
        "metricas": {"aciertos": f"{aciertos}/{len(resultados)}"},
        "regresiones": regresiones,
        "baseline_comparado": baseline is not None,
        "verdict": verdict,
    }


def imprimir_reporte(reporte: dict) -> None:
    for caso in reporte["casos"]:
        linea = (
            f"CASO={caso['id']} ESPERADO={caso['closure_esperado']} "
            f"OBTENIDO={caso['closure_obtenido']} TESTS={caso['tests_obtenido']} "
            f"TESTS_REAL={caso['tests_real']} RESULTADO={caso['resultado']}"
        )
        if caso["detalle"]:
            linea += f" DETALLE={caso['detalle']}"
        print(linea)
    print(f"ACIERTOS={reporte['metricas']['aciertos']}")
    if reporte["baseline_comparado"]:
        print(f"REGRESION={','.join(reporte['regresiones']) or 'NONE'}")
    else:
        print("REGRESION=NOT_APPLICABLE")
    print(f"VERDICT={reporte['verdict']}")


def main(argv: list[str] | None = None) -> int:
    raiz = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--salidas",
        required=True,
        help="directorio con un <id>.txt por escenario (E1.txt, E2.txt, ...)",
    )
    parser.add_argument("--fixture", default=str(raiz))
    parser.add_argument("--gold", default=str(raiz / "gold.json"))
    parser.add_argument("--baseline", help="resultados previos (JSON) para detectar regresiones")
    parser.add_argument("--out", help="escribir el reporte JSON acá")
    args = parser.parse_args(argv)

    gold = json.loads(Path(args.gold).read_text(encoding="utf-8"))
    directorio = Path(args.salidas)
    salidas = {
        ruta.stem: ruta.read_text(encoding="utf-8")
        for ruta in sorted(directorio.glob("*.txt"))
    }
    baseline = None
    if args.baseline:
        baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))

    reporte = evaluar(Path(args.fixture), gold, salidas, baseline)
    imprimir_reporte(reporte)
    if args.out:
        Path(args.out).write_text(
            json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return 0 if reporte["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
