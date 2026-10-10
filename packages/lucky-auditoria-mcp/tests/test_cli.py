"""El CLI: comodines en cualquier shell (S-28) y la salida siempre en UTF-8 (S-27)."""

import json
import os
import subprocess
import sys
from pathlib import Path

from lucky_auditoria import cli


def _registro(ruta, sesion):
    cabecera = {"tipo": "cabecera", "esquema": 2, "mcp": {"nombre": "m"}}
    linea = {"sesion": sesion, "herramienta": "x", "resultado": "ok", "cuando": "1"}
    ruta.write_text(json.dumps(cabecera) + "\n" + json.dumps(linea) + "\n", encoding="utf-8")
    return ruta


class TestLosComodinesLosExpandeElCli:
    """S-28: Bash expande `*.jsonl` antes de llamar; PowerShell y cmd lo pasan
    tal cual, y llegaba como nombre de archivo: «no existen»."""

    def test_un_comodin_lee_todos(self, tmp_path, capsys):
        _registro(tmp_path / "a.jsonl", "uno")
        _registro(tmp_path / "b.jsonl", "dos")

        assert cli.main(["por-sesion", str(tmp_path / "*.jsonl")]) == 0
        assert set(json.loads(capsys.readouterr().out)) == {"uno", "dos"}

    def test_un_comodin_que_no_encuentra_nada_lo_dice(self, tmp_path, capsys):
        assert cli.main(["por-sesion", str(tmp_path / "*.jsonl")]) == 2
        assert "no existen" in capsys.readouterr().err


class TestLaSalidaEsSiempreUtf8:
    def test_por_un_pipe_con_otra_pagina_de_codigos(self, tmp_path):
        """S-27: por un pipe en Windows `print` escribe en la pagina de codigos
        de la consola (cp1252): una `ñ` deja de ser UTF-8, y un caracter que esa
        pagina no tiene tumba la salida con `UnicodeEncodeError`."""
        registro = _registro(tmp_path / "a.jsonl", "señal→1")
        entorno = dict(os.environ, PYTHONIOENCODING="cp1252")
        src = str(Path(cli.__file__).resolve().parents[1])
        entorno["PYTHONPATH"] = os.pathsep.join(p for p in (src, entorno.get("PYTHONPATH")) if p)

        hecho = subprocess.run(
            [sys.executable, "-m", "lucky_auditoria.cli", "por-sesion", str(registro)],
            capture_output=True,
            env=entorno,
        )

        assert hecho.returncode == 0, hecho.stderr.decode("utf-8", "replace")
        assert "señal→1".encode() in hecho.stdout
