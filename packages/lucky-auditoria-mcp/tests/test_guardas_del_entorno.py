"""Las guardas que vigilan a la suite, probadas ellas mismas.

Existen porque una guarda sin prueba se pudre en silencio, y esta ya se pudrio
una vez: la version anterior preguntaba si la carpeta `registro_auditoria/`
existia ANTES, asi que en la maquina donde uno ya se habia ensuciado no acusaba
nada. Un test bajo HTTP sin `chdir` escribio en el repo del paquete durante
horas con la suite en verde; lo destapo el CI, que arranca de un checkout
limpio, en seis celdas a la vez.

Lo encontro la pasada de reversion, no la lectura: romper la comparacion de la
guarda no ponia nada en rojo, porque nada la ejercia. Es el mismo defecto una
capa mas arriba -la proteccion existe y nadie comprueba que proteja-, y en un
paquete cuyo trabajo es cazar ese defecto no puede quedar asi.
"""

import os
from pathlib import Path

from lucky_auditoria import identidad
from lucky_auditoria.pruebas import (
    _archivos_de,
    _sin_proyecto_heredado,
    lugares_prohibidos,
    nuevos_desde,
)


class TestLaComparacionQueSeApagabaSola:
    def test_un_archivo_nuevo_en_una_carpeta_VIEJA_se_ve(self, tmp_path):
        """El caso exacto que se escapo al CI.

        La carpeta ya estaba de antes -es lo normal en la maquina de quien
        desarrolla-, y adentro aparece un archivo nuevo. Preguntar
        `carpeta.exists()` da True las dos veces y no acusa nada.
        """
        carpeta = tmp_path / "registro_auditoria"
        carpeta.mkdir()
        (carpeta / "de-ayer.jsonl").write_text("{}", encoding="utf-8")
        antes = {carpeta: _archivos_de(carpeta)}

        (carpeta / "de-esta-corrida.jsonl").write_text("{}", encoding="utf-8")

        nuevos = nuevos_desde(antes)
        assert len(nuevos) == 1
        assert "de-esta-corrida" in nuevos[0]

    def test_lo_que_ya_estaba_no_se_acusa(self, tmp_path):
        # El control. Sin el, una guarda que acusa SIEMPRE pasaria el test de
        # arriba y volveria roja cualquier maquina con una carpeta vieja, que
        # es la forma mas rapida de que alguien la apague.
        carpeta = tmp_path / "registro_auditoria"
        carpeta.mkdir()
        (carpeta / "de-ayer.jsonl").write_text("{}", encoding="utf-8")
        antes = {carpeta: _archivos_de(carpeta)}

        assert nuevos_desde(antes) == []

    def test_una_carpeta_que_no_existia_y_aparece_se_ve(self, tmp_path):
        carpeta = tmp_path / "registro_auditoria"
        antes = {carpeta: _archivos_de(carpeta)}
        carpeta.mkdir()
        (carpeta / "nueva.jsonl").write_text("{}", encoding="utf-8")

        assert len(nuevos_desde(antes)) == 1

    def test_una_carpeta_que_nunca_existe_no_molesta(self, tmp_path):
        antes = {tmp_path / "no-existe": _archivos_de(tmp_path / "no-existe")}

        assert nuevos_desde(antes) == []


class TestQueLugaresSeVigilan:
    def test_son_los_tres_declarados(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "estado"))
        corral = tmp_path / "corral"
        corral.mkdir()
        monkeypatch.chdir(corral)
        repo = tmp_path / "el-repo"

        lugares = lugares_prohibidos(repo)

        assert tmp_path / "estado" / "registro_auditoria" in lugares
        assert repo / "registro_auditoria" in lugares
        # El cwd, que bajo HTTP ES el destino. Sin el, ese camino solo se
        # vigilaria cuando por casualidad coincide con el repo.
        assert corral / "registro_auditoria" in lugares

    def test_el_estado_del_usuario_sigue_vigilado_aunque_ya_no_se_use(self, tmp_path, monkeypatch):
        # Desde 0.4.0 no se escribe ahi nunca. Se vigila igual: si aparece algo,
        # es que quedo codigo de la version anterior, y eso hay que verlo.
        monkeypatch.delenv("LOCALAPPDATA", raising=False)
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg"))

        assert tmp_path / "xdg" / "registro_auditoria" in lugares_prohibidos(tmp_path)


class TestNingunTestHeredaUnProyectoReal:
    def test_con_el_arnes_puesto_la_raiz_sigue_siendo_None(self, monkeypatch, tmp_path):
        """La razon de existir de la fixture.

        Claude Code exporta `CLAUDE_PROJECT_DIR` al hijo, asi que sin esto la
        suite corre contra un proyecto REAL en la maquina de quien desarrolla y
        contra ninguno en el CI. Dos comportamientos para el mismo test.
        """
        monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "una-sesion")
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path / "un-repo-real"))
        monkeypatch.setattr(identidad, "_RAIZ_DEL_PROYECTO", None, raising=False)
        assert identidad.raiz_del_proyecto() is not None, (
            "el control fallo: si esto ya era None, el test de abajo pasa solo"
        )

        _sin_proyecto_heredado(monkeypatch)

        assert identidad.raiz_del_proyecto() is None

    def test_tambien_limpia_la_cache(self, monkeypatch, tmp_path):
        # El primer test que resuelva la raiz se la deja puesta a todos los que
        # siguen: sin limpiar la cache, borrar la variable no alcanza.
        monkeypatch.setattr(identidad, "_RAIZ_DEL_PROYECTO", str(tmp_path / "cacheado"))

        _sin_proyecto_heredado(monkeypatch)

        assert identidad.raiz_del_proyecto() is None

    def test_no_toca_variables_ajenas(self, monkeypatch):
        # Solo las que declara el catalogo de arneses. Una fixture autouse que
        # limpia de mas rompe tests que no tienen nada que ver.
        monkeypatch.setenv("UNA_VARIABLE_DEL_ANFITRION", "sigue-viva")

        _sin_proyecto_heredado(monkeypatch)

        assert os.environ.get("UNA_VARIABLE_DEL_ANFITRION") == "sigue-viva"


def test_el_corral_del_cwd_mueve_a_pytest_fuera_del_repo(tmp_path):
    # La fixture autouse ya corrio para este test: el cwd no puede ser el repo.
    repo = Path(__file__).resolve().parents[1]

    assert Path.cwd() != repo
    assert Path.cwd().name == "cwd-de-pytest"
