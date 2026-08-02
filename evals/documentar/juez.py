"""Juez determinista del arnés de evaluación de la skill `documentar`.

Reglas de la casa (docs/specs/eval-documentar.md):
1. Mide el síntoma (¿la cita archivo:línea existe y dice eso?), no el formato.
2. Se calibra con canarios (test_juez.py); si reprueba un caso bueno, el roto
   es el juez.
3. Solo lee y reporta: jamás edita una skill.
4. Reporte por caso; una regresión contra baseline es FAIL aunque el
   agregado mejore.

Solo stdlib. Exit 0 = PASS, exit 1 = FAIL (patrón de la casa).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HALLAZGO_PREFIX = "HALLAZGO="
CLAVES_REQUERIDAS = (
    "AUDIT_SCOPE",
    "DOCS_REVIEWED",
    "DRIFT_FOUND",
    "DRIFT_FIXED",
    "UNVERIFIED",
    "MAP_UPDATED",
)
TOLERANCIA_LINEAS = 2
VERDICTOS_HALLAZGO = {"DRIFT", "UNVERIFIED"}


def normalizar(texto: str) -> str:
    limpio = texto.replace("`", "").replace('"', "").replace("'", "")
    return re.sub(r"\s+", " ", limpio).strip().lower()


def _leer_lineas(root: Path, rel: str) -> list[str] | None:
    ruta = root / rel
    if not ruta.is_file():
        return None
    return ruta.read_text(encoding="utf-8").splitlines()


def linea_de_ancla(root: Path, rel: str, ancla: str) -> int:
    lineas = _leer_lineas(root, rel)
    if lineas is None:
        raise ValueError(f"gold inválido: {rel} no existe en el fixture")
    objetivo = normalizar(ancla)
    for numero, linea in enumerate(lineas, 1):
        if objetivo in normalizar(linea):
            return numero
    raise ValueError(f"gold inválido: ancla no encontrada en {rel}: {ancla}")


def ventana_contiene(root: Path, rel: str, numero: int, texto: str) -> bool:
    """¿La ventana ±N alrededor de la línea citada contiene el texto?"""
    lineas = _leer_lineas(root, rel)
    if lineas is None or not 1 <= numero <= len(lineas):
        return False
    desde = max(0, numero - 1 - TOLERANCIA_LINEAS)
    hasta = min(len(lineas), numero + TOLERANCIA_LINEAS)
    ventana = normalizar(" ".join(lineas[desde:hasta]))
    return normalizar(texto) in ventana


def parse_ref(ref: str) -> tuple[str, int] | None:
    ruta, sep, numero = ref.rpartition(":")
    if not sep or not ruta or not numero.isdigit():
        return None
    return ruta.replace("\\", "/"), int(numero)


def parse_salida(texto: str) -> tuple[dict, list[dict]]:
    claves: dict[str, str] = {}
    hallazgos: list[dict] = []
    for cruda in texto.splitlines():
        linea = cruda.strip()
        if linea.startswith(HALLAZGO_PREFIX):
            partes = [p.strip() for p in linea[len(HALLAZGO_PREFIX):].split("|")]
            if len(partes) != 4 or partes[0] not in VERDICTOS_HALLAZGO:
                hallazgos.append({"crudo": linea, "error": "FORMATO"})
                continue
            verdicto, doc_ref, cita, code_ref = partes
            hallazgos.append(
                {
                    "verdicto": verdicto,
                    "doc_ref": doc_ref,
                    "cita": cita,
                    "code_ref": code_ref,
                    "crudo": linea,
                }
            )
            continue
        coincidencia = re.match(r"^([A-Z_]+)=(.+)$", linea)
        if coincidencia and coincidencia.group(1) in CLAVES_REQUERIDAS:
            claves.setdefault(coincidencia.group(1), coincidencia.group(2).strip())
    return claves, hallazgos


def validar_schema(claves: dict, hallazgos: list[dict]) -> list[str]:
    problemas = []
    for clave in CLAVES_REQUERIDAS:
        if clave not in claves:
            problemas.append(f"falta {clave}")
    if any("error" in h for h in hallazgos):
        problemas.append("hallazgo con formato inválido")
    validos = [h for h in hallazgos if "error" not in h]
    drift_listados = sum(1 for h in validos if h["verdicto"] == "DRIFT")
    unverified_listados = sum(1 for h in validos if h["verdicto"] == "UNVERIFIED")
    if claves.get("AUDIT_SCOPE") not in {"FULL", "INCREMENTAL", None}:
        problemas.append("AUDIT_SCOPE fuera de enum")
    if claves.get("MAP_UPDATED") not in {"YES", "NO", None}:
        problemas.append("MAP_UPDATED fuera de enum")
    if claves.get("DRIFT_FOUND", "").isdigit():
        if int(claves["DRIFT_FOUND"]) != drift_listados:
            problemas.append(
                f"DRIFT_FOUND={claves['DRIFT_FOUND']} pero hay {drift_listados} hallazgos DRIFT"
            )
    elif "DRIFT_FOUND" in claves:
        problemas.append("DRIFT_FOUND no numérico")
    if claves.get("UNVERIFIED", "").isdigit():
        if int(claves["UNVERIFIED"]) != unverified_listados:
            problemas.append(
                f"UNVERIFIED={claves['UNVERIFIED']} pero hay {unverified_listados} hallazgos UNVERIFIED"
            )
    elif "UNVERIFIED" in claves:
        problemas.append("UNVERIFIED no numérico")
    return problemas


def _matchea(hallazgo: dict, caso: dict, linea_gold: int, texto_linea_gold: str) -> bool:
    """Match por CONTENIDO primero; la línea exacta es solo respaldo.

    La proximidad ±N acá cruzaría casos adyacentes de una lista — la
    tolerancia de líneas pertenece a la validez de la cita, no al match.
    """
    ref = parse_ref(hallazgo["doc_ref"])
    if ref is None or ref[0] != caso["doc"]:
        return False
    cita = normalizar(hallazgo["cita"])
    ancla = normalizar(caso["ancla"])
    linea = normalizar(texto_linea_gold)
    if ancla in cita or (len(cita) >= 8 and cita in linea):
        return True
    return ref[1] == linea_gold


def _cita_valida(root: Path, hallazgo: dict, caso: dict | None) -> tuple[bool, str]:
    ref = parse_ref(hallazgo["doc_ref"])
    if ref is None:
        return False, "doc_ref ilegible"
    if len(normalizar(hallazgo["cita"])) < 8:
        return False, "cita demasiado corta para verificar"
    if not ventana_contiene(root, ref[0], ref[1], hallazgo["cita"]):
        return False, f"la cita no aparece en {hallazgo['doc_ref']} (±{TOLERANCIA_LINEAS})"
    if hallazgo["verdicto"] == "DRIFT":
        code = parse_ref(hallazgo["code_ref"])
        if code is None:
            return False, "un DRIFT exige referencia de código"
        lineas = _leer_lineas(root, code[0])
        if lineas is None or not 1 <= code[1] <= len(lineas):
            return False, f"referencia de código inexistente: {hallazgo['code_ref']}"
        if caso and caso.get("ancla_codigo"):
            if not ventana_contiene(root, code[0], code[1], caso["ancla_codigo"]):
                return False, (
                    f"el código citado no contiene la evidencia esperada ({caso['ancla_codigo']})"
                )
    return True, "ok"


def evaluar(
    fixture: Path,
    gold: dict,
    texto_salida: str,
    baseline: dict | None = None,
) -> dict:
    claves, hallazgos = parse_salida(texto_salida)
    problemas_schema = validar_schema(claves, hallazgos)
    validos = [h for h in hallazgos if "error" not in h]

    resultados: list[dict] = []
    usados: set[int] = set()
    tp = fp = 0
    citas_total = citas_validas = 0
    total_drift_gold = sum(1 for c in gold["casos"] if c["esperado"] == "DRIFT")

    for caso in gold["casos"]:
        linea_gold = linea_de_ancla(fixture, caso["doc"], caso["ancla"])
        lineas_doc = _leer_lineas(fixture, caso["doc"]) or []
        texto_linea_gold = lineas_doc[linea_gold - 1] if linea_gold <= len(lineas_doc) else ""
        matches = [
            (i, h)
            for i, h in enumerate(validos)
            if i not in usados and _matchea(h, caso, linea_gold, texto_linea_gold)
        ]
        obtenido = "AUSENTE"
        cita_estado = "N/A"
        detalle = ""
        if matches:
            indice, hallazgo = matches[0]
            usados.add(indice)
            obtenido = hallazgo["verdicto"]
            citas_total += 1
            ok, razon = _cita_valida(fixture, hallazgo, caso)
            cita_estado = "VALIDA" if ok else "ROTA"
            if ok:
                citas_validas += 1
            else:
                detalle = razon

        esperado = caso["esperado"]
        if esperado == "DRIFT":
            paso = obtenido == "DRIFT" and cita_estado == "VALIDA"
            if obtenido == "DRIFT" and cita_estado == "VALIDA":
                tp += 1
            elif obtenido == "DRIFT":
                fp += 1  # lo marcó, pero la evidencia citada no sostiene
        elif esperado == "OK":
            paso = obtenido == "AUSENTE"
            if obtenido == "DRIFT":
                fp += 1
                detalle = detalle or "falso positivo: la doc coincide con el código"
        else:  # UNVERIFIED
            paso = obtenido == "UNVERIFIED" and cita_estado == "VALIDA"
            if obtenido == "DRIFT":
                fp += 1
                detalle = detalle or "adivinó: lo incomprobable se declara UNVERIFIED"
            elif obtenido == "AUSENTE":
                detalle = detalle or "no declaró la afirmación incomprobable"

        resultados.append(
            {
                "id": caso["id"],
                "esperado": esperado,
                "obtenido": obtenido,
                "cita": cita_estado,
                "resultado": "PASS" if paso else "FAIL",
                "detalle": detalle,
            }
        )

    extras = [h for i, h in enumerate(validos) if i not in usados]
    fp += len(extras)

    precision = 1.0 if (tp + fp) == 0 else tp / (tp + fp)
    recall = 0.0 if total_drift_gold == 0 else tp / total_drift_gold

    regresiones: list[str] = []
    if baseline is not None:
        previos = {c["id"]: c["resultado"] for c in baseline.get("casos", [])}
        for caso in resultados:
            if previos.get(caso["id"]) == "PASS" and caso["resultado"] == "FAIL":
                regresiones.append(caso["id"])

    todo_pass = all(c["resultado"] == "PASS" for c in resultados)
    verdict = (
        "PASS"
        if todo_pass
        and not extras
        and not problemas_schema
        and citas_validas == citas_total
        and not regresiones
        else "FAIL"
    )

    return {
        "casos": resultados,
        "extras": [h["crudo"] for h in extras],
        "schema": {"ok": not problemas_schema, "problemas": problemas_schema},
        "metricas": {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "citas": f"{citas_validas}/{citas_total}",
        },
        "regresiones": regresiones,
        "baseline_comparado": baseline is not None,
        "verdict": verdict,
    }


def imprimir_reporte(reporte: dict) -> None:
    for caso in reporte["casos"]:
        linea = (
            f"CASO={caso['id']} ESPERADO={caso['esperado']} "
            f"OBTENIDO={caso['obtenido']} CITA={caso['cita']} RESULTADO={caso['resultado']}"
        )
        if caso["detalle"]:
            linea += f" DETALLE={caso['detalle']}"
        print(linea)
    print(f"EXTRAS={len(reporte['extras'])}")
    schema = reporte["schema"]
    print(f"SCHEMA={'OK' if schema['ok'] else 'FAIL:' + '; '.join(schema['problemas'])}")
    print(f"PRECISION={reporte['metricas']['precision']:.2f}")
    print(f"RECALL={reporte['metricas']['recall']:.2f}")
    print(f"CITAS={reporte['metricas']['citas']}")
    if reporte["baseline_comparado"]:
        print(f"REGRESION={','.join(reporte['regresiones']) or 'NONE'}")
    else:
        print("REGRESION=NOT_APPLICABLE")
    print(f"VERDICT={reporte['verdict']}")


def main(argv: list[str] | None = None) -> int:
    raiz = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", required=True, help="archivo con la salida del evaluado")
    parser.add_argument("--fixture", default=str(raiz / "fixture"))
    parser.add_argument("--gold", default=str(raiz / "gold.json"))
    parser.add_argument("--baseline", help="resultados previos (JSON) para detectar regresiones")
    parser.add_argument("--out", help="escribir el reporte JSON acá")
    args = parser.parse_args(argv)

    texto = Path(args.salida).read_text(encoding="utf-8")
    gold = json.loads(Path(args.gold).read_text(encoding="utf-8"))
    baseline = None
    if args.baseline:
        baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))

    reporte = evaluar(Path(args.fixture), gold, texto, baseline)
    imprimir_reporte(reporte)
    if args.out:
        Path(args.out).write_text(
            json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return 0 if reporte["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
