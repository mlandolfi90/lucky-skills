"""Kit de pruebas que el anfitrion HEREDA, para no reescribir las guardas.

Un retrofit termina cuando estas pruebas pasan en el repo anfitrion, no cuando
el codigo compila. La mayoria son de FUGA y no de formato: buscan un secreto
centinela en el TEXTO CRUDO del archivo, no en el objeto parseado, porque un
`json.loads` esconde justo lo que se quiere ver.

## Como se usa

    # tests/test_auditoria.py del anfitrion
    from lucky_auditoria import Auditor
    from lucky_auditoria.pruebas import KitDeAuditoria

    class TestAuditoria(KitDeAuditoria):
        def construir(self, tmp_path):
            return Auditor("mi-mcp", config="config/auditoria.toml")

pytest colecta los metodos heredados, asi que el que agrega un arnes o una
herramienta opaca hereda la guarda sin escribirla.

## Las dos expectativas, y por que la segunda

Las guardas son conscientes del MODO, con expectativa invertida: en redactado
el centinela NO aparece; en crudo SI debe aparecer. Sin la segunda, una
redaccion rota que borra todo pasa en verde y el modo de depurar deja de
depurar sin que nadie lo note. Una guarda que solo prueba ausencia se cumple
sola cuando el codigo no llego ahi.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from lucky_auditoria import arneses, identidad

# Un valor que no puede aparecer por casualidad en ningun lado.
CENTINELA = "pa55w0rd-centinela-8f21c3"


# --- las tres guardas del entorno, para el conftest del anfitrion -----------
#
# Se envian con el paquete y no se explican en un README porque un modismo que
# hay que copiar a mano se copia mal: la primera version de la tercera acusaba
# solo si la carpeta no existia antes, o sea que se apagaba sola en la maquina
# donde uno ya se habia ensuciado, y asi paso un defecto entero al CI.
#
#     # tests/conftest.py del anfitrion
#     from lucky_auditoria.pruebas import guardas_del_entorno
#     globals().update(guardas_del_entorno())


def _sin_proyecto_heredado(monkeypatch):
    """Ningun test ve el proyecto de quien corre la suite.

    Claude Code exporta `CLAUDE_PROJECT_DIR` al proceso hijo, asi que en la
    maquina de un desarrollador **todo test escribe en un proyecto real** si se
    olvida de fijar el suyo: el registro cae en el repo de al lado y la suite
    pasa igual. En el CI esa variable no existe y el mismo test se comporta
    distinto. Una suite que se comporta distinto segun quien la corre no esta
    midiendo lo que dice medir.

    Se arranca siempre desde "no hay proyecto", que es el unico estado igual en
    las dos maquinas; el que necesita uno lo declara. Tambien se limpia la
    cache de `identidad`, porque el primer test que resuelva la raiz se la deja
    puesta a todos los que siguen.
    """
    for arnes in arneses.catalogo():
        if arnes.testigo:
            monkeypatch.delenv(arnes.testigo, raising=False)
        for variable in arnes.campos:
            monkeypatch.delenv(variable, raising=False)
    monkeypatch.setattr(identidad, "_RAIZ_DEL_PROYECTO", None, raising=False)


def _corral_para_el_cwd(tmp_path_factory, monkeypatch):
    """Bajo HTTP el destino ES el cwd, y el cwd de pytest es el repo.

    Un test de transporte http que se olvide del `chdir` no falla: escribe en
    `<repo>/registro_auditoria/` y sigue verde. Arreglar el test que lo hizo
    hoy arregla ese; esto arregla el proximo, que es la misma leccion que la
    carpeta que se autoignora.

    El corral sale de `tmp_path_factory` y NO de `tmp_path`. La primera version
    lo creaba adentro del `tmp_path` del test, y ahi rompio tres pruebas de un
    anfitrion que afirman "este directorio quedo vacio": la guarda les metia una
    carpeta adentro. Una guarda que ensucia el area de trabajo del test es la
    misma familia de defecto que vino a cazar, y solo aparecio corriendo la
    suite ENTERA -sola, cada archivo pasaba-.

    El que necesite el cwd de verdad lo declara con su propio
    `monkeypatch.chdir`, que gana por ser posterior.
    """
    monkeypatch.chdir(tmp_path_factory.mktemp("cwd-de-pytest"))


def _archivos_de(carpeta: Path) -> set:
    if not carpeta.exists():
        return set()
    try:
        return {str(p) for p in carpeta.rglob("*") if p.is_file()}
    except OSError:
        return set()


def lugares_prohibidos(raiz_del_anfitrion: Path) -> set:
    """Donde la suite NO puede dejar un registro, con su motivo cada uno.

    - el estado del usuario, que desde 0.4.0 no se usa nunca. Si aparece algo
      ahi, quedo codigo de la version anterior.
    - **el repo del anfitrion**: ahora todo va a
      `<proyecto>/registro_auditoria/`, y un test que se olvide de apuntar el
      proyecto a su `tmp_path` lo escribe adentro del repo que corre la suite.
      Es el incidente que motivo R1, cometido por la suite que lo prueba.
    - **el cwd de pytest**, que bajo HTTP ES el destino. Suele coincidir con el
      repo, pero no tiene por que, y un lugar que solo se vigila por
      coincidencia no se esta vigilando.
    """
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_STATE_HOME")
    estado = Path(base) if base else Path.home() / ".local" / "state"
    return {
        estado / "registro_auditoria",
        Path(raiz_del_anfitrion) / "registro_auditoria",
        Path.cwd() / "registro_auditoria",
    }


def nuevos_desde(antes: dict) -> list:
    """Los archivos que aparecieron desde la foto `antes`.

    Es la comparacion de la guarda, sacada afuera para poder PROBARLA. La
    reversion mostro que rompiendola no fallaba nada: una guarda que nada
    ejerce es la que se pudre en silencio, y esta ya se pudrio una vez.
    """
    return sorted(
        archivo
        for sospechoso, previos in antes.items()
        for archivo in _archivos_de(sospechoso) - previos
    )


def guardas_del_entorno(raiz_del_anfitrion: Path | None = None) -> dict:
    """Las tres fixtures autouse, listas para `globals().update(...)`.

    `raiz_del_anfitrion` es el repo a vigilar; por defecto, el directorio desde
    el que se lanzo pytest.
    """
    raiz = Path(raiz_del_anfitrion) if raiz_del_anfitrion else Path.cwd()

    @pytest.fixture(autouse=True)
    def _ningun_test_hereda_un_proyecto_real(monkeypatch):
        _sin_proyecto_heredado(monkeypatch)

    @pytest.fixture(autouse=True)
    def _ningun_test_escribe_en_el_cwd_de_pytest(tmp_path_factory, monkeypatch):
        _corral_para_el_cwd(tmp_path_factory, monkeypatch)

    @pytest.fixture(autouse=True, scope="session")
    def _la_suite_no_ensucia_la_maquina():
        """Ninguna prueba puede dejar un registro fuera de su `tmp_path`.

        Se comparan ARCHIVOS y no si la carpeta existia. Preguntar
        `carpeta.exists()` antes y despues **se apaga solo en la maquina donde
        uno ya se ensucio**: creada una vez, toda corrida posterior la ve "de
        antes" y no acusa nada. Paso exactamente asi (2026-09-07): un test bajo
        HTTP sin `chdir` venia escribiendo en el repo del paquete, el worktree
        tenia la carpeta desde hacia horas, y la suite pasaba verde en local.
        Lo destapo el CI, que arranca de un checkout limpio, en seis celdas a
        la vez.

        Es la misma familia que el resto: la proteccion existia y una condicion
        la anulaba en silencio.
        """
        antes = {s: _archivos_de(s) for s in lugares_prohibidos(raiz)}
        yield
        nuevos = nuevos_desde(antes)
        if nuevos:
            raise AssertionError(
                "la suite escribio fuera de su tmp_path:\n"
                + "\n".join(nuevos[:10])
                + f"\n({len(nuevos)} archivos nuevos). Cada test tiene que apuntar "
                "el proyecto a su tmp_path, y los de transporte http tambien el cwd."
            )

    return {
        "_ningun_test_hereda_un_proyecto_real": _ningun_test_hereda_un_proyecto_real,
        "_ningun_test_escribe_en_el_cwd_de_pytest": _ningun_test_escribe_en_el_cwd_de_pytest,
        "_la_suite_no_ensucia_la_maquina": _la_suite_no_ensucia_la_maquina,
    }



class KitDeAuditoria:
    """Las guardas que todo MCP auditado tiene que pasar.

    El anfitrion implementa `construir` y hereda el resto.
    """

    # -- lo unico que el anfitrion escribe ----------------------------------

    def construir(self, tmp_path: Path):
        """Devolver el `Auditor` del anfitrion, ya configurado."""
        raise NotImplementedError(
            "El anfitrion tiene que implementar `construir(tmp_path)` "
            "devolviendo su Auditor."
        )

    # La herramienta y el argumento con los que se ejercita. El anfitrion los
    # pisa si sus nombres son otros; los de aca no tienen por que existir.
    herramienta_normal = "prueba"
    argumento_no_declarado = "parametro_que_no_existe"

    # -- infraestructura ----------------------------------------------------

    @pytest.fixture
    def auditor(self, tmp_path, monkeypatch):
        """Un auditor apuntado a `tmp_path`, con el interruptor en redactado.

        El `chdir` no es cosmetico: un interruptor mal escrito no deja de
        escribir, escribe con el directorio VACIO -o sea, en el cwd- y una
        prueba que solo mira `tmp_path` pasa con el interruptor roto. Al correr
        desde un directorio limpio, ese archivo aparece donde se lo ve.
        """
        cwd = tmp_path / "cwd-limpio"
        cwd.mkdir()
        monkeypatch.chdir(cwd)
        # Desde R1 de 1.5.0 el registro va a la carpeta del PROYECTO, asi que
        # el que tiene que estar en `tmp_path` es el proyecto, y cada prueba que
        # lo necesita usa el fixture `proyecto`. Antes habia que mover tambien
        # `LOCALAPPDATA` y `XDG_STATE_HOME`, porque el crudo iba al estado del
        # usuario: sin eso, correr la suite dejaba archivos CRUDOS -con el
        # centinela adentro- en el `%LOCALAPPDATA%` real de quien la corrio. Me
        # paso escribiendo estas mismas guardas. El peligro se mudo, no
        # desaparecio: ahora lo cubre la guarda de sesion del anfitrion.
        auditor = self.construir(tmp_path)
        monkeypatch.setenv(auditor.variable, str(tmp_path / "registro.jsonl"))
        return auditor

    def _texto(self, auditor) -> str:
        """El archivo tal cual esta en disco. Nunca parseado."""
        ruta = auditor.ruta()
        assert ruta is not None, "el auditor deberia estar encendido en esta prueba"
        return ruta.read_text(encoding="utf-8")

    # -- fuga, en los dos modos --------------------------------------------

    def test_redactado_no_escribe_el_valor_de_un_argumento_no_declarado(self, auditor):
        auditor.registrar(
            self.herramienta_normal, {self.argumento_no_declarado: CENTINELA}
        )

        assert CENTINELA not in self._texto(auditor)

    def test_crudo_SI_escribe_el_valor(self, auditor, monkeypatch, proyecto):
        # La expectativa invertida. Sin esta, una redaccion que borra todo pasa
        # en verde y el modo de depurar deja de depurar en silencio.
        monkeypatch.setenv(auditor.variable, "crudo")
        auditor.registrar(
            self.herramienta_normal, {self.argumento_no_declarado: CENTINELA}
        )

        assert CENTINELA in self._texto(auditor)

    def test_el_archivo_crudo_se_llama_a_gritos_y_cada_linea_lo_dice(
        self, auditor, monkeypatch, proyecto
    ):
        monkeypatch.setenv(auditor.variable, "crudo")
        auditor.registrar(self.herramienta_normal, {})

        assert "CRUDA-" in auditor.ruta().name
        assert '"modo": "crudo"' in self._texto(auditor)

    def test_una_herramienta_opaca_no_deja_ni_los_nombres_ni_el_tamano(self, auditor):
        if not auditor.redaccion.opacas:
            pytest.skip("este MCP no declara herramientas opacas")
        opaca = sorted(auditor.redaccion.opacas)[0]
        auditor.registrar(opaca, {"comando": CENTINELA, "usuario": "admin"})

        texto = self._texto(auditor)
        assert CENTINELA not in texto
        assert "comando" not in texto
        # El largo tambien filtra: mide la password. La primera version de esta
        # guarda buscaba `str(len(CENTINELA))` en el texto y daba rojo porque
        # ese numero aparecia en la marca de tiempo: era una carrera entre dos
        # cosas distintas, no una prueba. Se pregunta por la PROPIEDAD -que lo
        # anotado sea solo la forma opaca- en vez de por un numero suelto.
        anotado = json.loads(texto.splitlines()[-1])["argumentos"]
        assert set(anotado) == {"_opaco", "operaciones"}
        assert "largo" not in texto

    def test_el_mensaje_de_una_excepcion_no_se_copia(self, auditor):
        # El texto de una excepcion arrastra lo que se le paso a la herramienta.
        # Por eso se anota el TIPO, no el mensaje.
        auditor.registrar(
            self.herramienta_normal,
            {},
            resultado="error",
            error=type(ValueError(CENTINELA)).__name__,
        )

        assert CENTINELA not in self._texto(auditor)

    # -- el interruptor -----------------------------------------------------

    def test_apagado_no_escribe_nada_en_ningun_lado(self, auditor, monkeypatch, tmp_path):
        monkeypatch.delenv(auditor.variable, raising=False)
        auditor.registrar(self.herramienta_normal, {self.argumento_no_declarado: CENTINELA})

        assert auditor.ruta() is None
        # Ni archivo vacio ni directorio creado, y tampoco en el cwd: el
        # `chdir` de la fixture es lo que hace visible este segundo caso.
        assert list(Path(os.getcwd()).iterdir()) == []
        assert not list(tmp_path.glob("**/*.jsonl"))

    def test_una_palabra_desconocida_apaga_y_lo_dice(self, auditor, monkeypatch, caplog):
        # Caso medido: la variable quedo en `crude`, no estaba en la lista, se
        # tomo como RUTA, y la auditoria quedo redactada escribiendo
        # `crude-<sesion>.jsonl` sin que nadie se enterara.
        #
        # La primera correccion agrego el aviso y siguio escribiendo, que es la
        # mitad peor: un aviso que no cambia lo que pasa no es una proteccion.
        monkeypatch.setenv(auditor.variable, "cruod")
        with caplog.at_level("WARNING"):
            modo = auditor.modo()

        assert modo == "apagado"
        assert auditor.ruta() is None
        assert any("APAGADA" in r.message for r in caplog.records)

    def test_una_ruta_RELATIVA_apaga_en_vez_de_escribir_en_el_cwd(
        self, auditor, monkeypatch, tmp_path
    ):
        # Una ruta relativa cuelga el archivo del directorio de trabajo, que un
        # MCP hereda de quien lo lanzo: es el mismo daño que el directorio por
        # defecto vino a evitar, pedido por el operador sin querer.
        monkeypatch.setenv(auditor.variable, "registro/auditoria.jsonl")
        auditor.registrar(self.herramienta_normal, {})

        assert auditor.ruta() is None
        assert list(Path(os.getcwd()).iterdir()) == []

    def test_si_no_se_puede_crear_el_directorio_no_se_escribe_en_ningun_lado(
        self, auditor, monkeypatch
    ):
        # Habia una caida al cwd -"mejor el cwd que perder el registro"- y
        # estaba mal: no escribir no rompe nada, y la caida pone el archivo con
        # credenciales justo en el repo ajeno.
        monkeypatch.setenv(auditor.variable, "1")

        def no_se_puede(*_a, **_k):
            raise OSError("permiso denegado")

        monkeypatch.setattr(Path, "mkdir", no_se_puede)
        auditor.registrar(self.herramienta_normal, {})

        assert auditor.directorio_por_defecto() is None
        assert auditor.ruta() is None
        assert list(Path(os.getcwd()).iterdir()) == []

    # -- el nombre del archivo ---------------------------------------------

    def test_las_marcas_van_aunque_la_ruta_sea_explicita(self, auditor, monkeypatch, tmp_path):
        destino = tmp_path / "elegido.jsonl"
        monkeypatch.setenv(auditor.variable, str(destino))

        nombre = auditor.ruta().name
        assert nombre.startswith(auditor.nombre), "falta el nombre del MCP"
        assert "elegido" in nombre, "se perdio la eleccion del operador"

    def test_el_default_no_es_el_cwd(self, auditor, monkeypatch, tmp_path):
        # El cwd de un MCP por stdio lo hereda de quien lo lanzo: es `%TEMP%` o
        # el repo de otro, nunca una propiedad del proyecto.
        monkeypatch.setenv(auditor.variable, "1")
        monkeypatch.setattr(identidad, "raiz_del_proyecto", lambda: str(tmp_path / "proy"))

        assert Path(os.getcwd()) not in auditor.ruta().parents

    # -- R1: el proyecto que llamo, en una carpeta que se ignora sola -------

    @pytest.fixture
    def proyecto(self, tmp_path, monkeypatch):
        """Un proyecto que llamo, declarado como lo declararia el arnes."""
        raiz = tmp_path / "el-repo-que-llamo"
        raiz.mkdir()
        monkeypatch.setattr(identidad, "raiz_del_proyecto", lambda: str(raiz))
        return raiz

    def test_stdio_redactado_va_al_proyecto_que_llamo(
        self, auditor, monkeypatch, proyecto
    ):
        monkeypatch.setenv(auditor.variable, "1")
        auditor.registrar(self.herramienta_normal, {})

        assert auditor.ruta().parent == proyecto / "registro_auditoria"

    def test_stdio_CRUDO_va_A_LA_MISMA_carpeta_que_el_redactado(
        self, auditor, monkeypatch, proyecto
    ):
        """La celda que el humano cerro, y por que cambio de lado.

        Hasta 0.3.3 el crudo iba al estado del usuario, para que un zip, un
        `COPY .` o un sdist -que ignoran el `.gitignore`- no se lo llevaran.
        El precio resulto peor que el riesgo: el crudo quedaba en un arbol que
        no es de ningun proyecto, y para borrarlo habia que acordarse de que ese
        arbol existe. Nadie se acuerda, y el crudo con credenciales es
        justamente lo que no puede quedar olvidado.

        Ahora los dos modos comparten carpeta y la proteccion del crudo es la
        RETENCION (R7): `auditoria limpiar` lo borra desde donde uno ya esta
        mirando, y el `check` dice cuantos hay.
        """
        monkeypatch.setenv(auditor.variable, "crudo")
        auditor.registrar(self.herramienta_normal, {"clave": CENTINELA})

        assert auditor.ruta().parent == proyecto / "registro_auditoria"

    def test_el_crudo_se_puede_limpiar_desde_la_herramienta(
        self, auditor, monkeypatch, proyecto
    ):
        """Lo que hace que la celda de arriba sea sostenible y no un descuido.

        Sin esto, mover el crudo a la carpeta del proyecto seria solamente
        empeorar donde queda. Lo que lo vuelve una decision es que borrarlo pase
        a ser una accion a mano alzada desde el cliente, en el mismo lugar donde
        uno ya esta leyendo el registro.
        """
        from lucky_auditoria.herramienta import Lector

        monkeypatch.setenv(auditor.variable, "crudo")
        auditor.registrar(self.herramienta_normal, {"clave": CENTINELA})
        viejo = auditor.ruta()
        assert viejo.exists()
        # El que este proceso esta escribiendo NO se toca: en Windows falla, y
        # en Linux desapareceria del listado mientras se le sigue escribiendo,
        # que es peor porque parece limpio.
        otro = viejo.with_name(viejo.name.replace(identidad.escritor(), "otra-sesion"))
        otro.write_text(viejo.read_text(encoding="utf-8"), encoding="utf-8")

        salida = Lector(auditor).limpiar()

        assert otro.name in salida["borrados"] and not otro.exists()
        assert viejo.name in salida["en_uso"] and viejo.exists()

    def test_limpiar_no_toca_el_redactado(self, auditor, monkeypatch, proyecto):
        """El redactado es evidencia forense: no se tira por una herramienta.

        La primera version de esta guarda miraba el archivo del PROPIO proceso,
        y pasaba por la razon equivocada: ese archivo sobrevive porque esta EN
        USO, no porque sea redactado. Lo destapo la reversion -romper "limpiar
        solo borra crudos" no ponia nada en rojo-. Hace falta un redactado de
        OTRA sesion, que es el que un `limpiar` mal escrito se lleva puesto.
        """
        from lucky_auditoria.herramienta import Lector

        monkeypatch.setenv(auditor.variable, "1")
        auditor.registrar(self.herramienta_normal, {})
        propio = auditor.ruta()
        ajeno = propio.with_name(propio.name.replace(identidad.escritor(), "otra-sesion"))
        ajeno.write_text(propio.read_text(encoding="utf-8"), encoding="utf-8")

        salida = Lector(auditor).limpiar()

        assert ajeno.exists(), "se llevo puesto un redactado de otra sesion"
        assert propio.exists()
        assert salida["cuantos"] == 0

    def test_http_va_al_directorio_de_trabajo_del_servicio_y_sin_aviso(
        self, tmp_path, monkeypatch, caplog
    ):
        """Bajo HTTP el cwd SI se usa, y es lo correcto.

        El servidor es un contenedor de larga vida: su directorio de trabajo es
        suyo y no lo heredo de ningun proyecto. Es la diferencia exacta con
        stdio, donde el cwd es lo que el lanzador le dejo al hijo.

        No hay aviso a proposito: en stdio la ausencia de proyecto es señal, en
        HTTP seria ruido constante.
        """
        servicio = tmp_path / "adentro-del-contenedor"
        servicio.mkdir()
        monkeypatch.chdir(servicio)
        auditor = self.construir(tmp_path)
        auditor.transporte = "http"
        monkeypatch.setenv(auditor.variable, "1")
        with caplog.at_level("WARNING"):
            ruta = auditor.ruta()

        assert ruta.parent == servicio / "registro_auditoria"
        assert not any("sin proyecto" in r.message for r in caplog.records)

    def test_la_carpeta_nace_con_su_gitignore(self, auditor, monkeypatch, proyecto):
        monkeypatch.setenv(auditor.variable, "1")
        auditor.registrar(self.herramienta_normal, {})

        marca = proyecto / "registro_auditoria" / ".gitignore"
        assert marca.exists()
        assert marca.read_text(encoding="utf-8").strip().endswith("*")

    def test_git_no_levanta_el_registro_en_un_repo_de_verdad(
        self, auditor, monkeypatch, tmp_path
    ):
        """La guarda que importa: no que el archivo exista, sino que git lo ignore.

        Un `.gitignore` con la sintaxis equivocada existe igual y no protege
        nada. Se le pregunta a git, que es quien decide.
        """
        git = shutil.which("git")
        if git is None:
            pytest.skip("no hay git para preguntarle")
        repo = tmp_path / "repo-ajeno"
        repo.mkdir()
        subprocess.run([git, "init", "-q"], cwd=repo, check=True)
        monkeypatch.setenv(auditor.variable, "1")
        monkeypatch.setattr(identidad, "raiz_del_proyecto", lambda: str(repo))
        auditor.registrar(self.herramienta_normal, {"clave": CENTINELA})

        relativa = auditor.ruta().relative_to(repo).as_posix()
        ignorado = subprocess.run([git, "check-ignore", "-q", relativa], cwd=repo)
        assert ignorado.returncode == 0, f"git NO ignora {relativa}"

        # Y el control de punta a punta: el gesto que causo el incidente.
        subprocess.run([git, "add", "-A"], cwd=repo, check=True)
        listo = subprocess.run(
            [git, "diff", "--cached", "--name-only"], cwd=repo, capture_output=True, text=True
        ).stdout
        assert "registro_auditoria" not in listo, listo

    def test_la_raiz_del_proyecto_nunca_sale_del_cwd(self, monkeypatch, tmp_path):
        """La guarda sobre la FUENTE, no sobre quien la usa.

        La encontro la reversion: los tests de arriba monkeypatchean
        `raiz_del_proyecto`, asi que un respaldo al cwd DENTRO de esa funcion
        pasaba las cuatro en verde. Es el mismo patron que ya nos mordio dos
        veces -la proteccion existe y el respaldo la anula-, y esta vez el
        respaldo estaba en el unico lugar que las guardas no miraban.
        """
        cwd = tmp_path / "cwd-de-otro-repo"
        cwd.mkdir()
        monkeypatch.chdir(cwd)
        for arnes in arneses.catalogo():
            if arnes.testigo:
                monkeypatch.delenv(arnes.testigo, raising=False)
            for variable in arnes.campos:
                monkeypatch.delenv(variable, raising=False)
        monkeypatch.setattr(identidad, "_RAIZ_DEL_PROYECTO", None)

        # None, no el cwd: sin fuente no se adivina, y el que llama decide.
        assert identidad.raiz_del_proyecto() is None

    def test_sin_proyecto_NO_SE_ESCRIBE_y_se_avisa(
        self, auditor, monkeypatch, caplog
    ):
        """Ni el arnes ni los roots dijeron cual espacio de trabajo llamo.

        Hasta 0.3.3 esto caia en `<estado>/registro_auditoria/_sin_proyecto/`:
        una carpeta que nadie sabia que existia, acumulando lo que nadie iba a
        buscar. Desde R1 de 1.5.0 no se escribe en ningun lado. No escribir
        tampoco rompe -el escritor ya se traga sus fallos-, y un registro que
        nadie va a encontrar no vale su riesgo.
        """
        monkeypatch.setenv(auditor.variable, "1")
        monkeypatch.setattr(identidad, "raiz_del_proyecto", lambda: None)
        with caplog.at_level("WARNING"):
            ruta = auditor.ruta()
            auditor.registrar(self.herramienta_normal, {"clave": CENTINELA})

        assert ruta is None
        assert any("APAGADA" in r.message for r in caplog.records)

    def test_sin_proyecto_el_cwd_queda_intacto(self, auditor, monkeypatch, tmp_path):
        # El control de la de arriba: "no devuelve ruta" y "no escribe" son dos
        # cosas, y la que importa es la segunda.
        monkeypatch.setenv(auditor.variable, "crudo")
        monkeypatch.setattr(identidad, "raiz_del_proyecto", lambda: None)
        auditor.registrar(self.herramienta_normal, {"clave": CENTINELA})

        sucios = [str(p) for p in Path.cwd().rglob("*") if p.is_file()]
        assert not sucios, f"escribio igual: {sucios}"

    def test_el_aviso_es_una_vez_por_proceso_y_no_por_llamada(
        self, auditor, monkeypatch, tmp_path, caplog
    ):
        """Lo encontro la reversion, y no era lo que yo buscaba con ella.

        La mutacion que probe -"HTTP avisa como stdio"- resulto inalcanzable
        bajo HTTP, y en cambio destapo esto: nadie comprobaba que el aviso no se
        repitiera. Un aviso por llamada es la razon exacta por la que R1 decide
        NO avisar bajo HTTP: uno que suena siempre deja de leerse, y entonces
        tampoco se lee el que importa.
        """
        monkeypatch.setenv(auditor.variable, "1")
        monkeypatch.setattr(identidad, "raiz_del_proyecto", lambda: None)
        with caplog.at_level("WARNING"):
            for _ in range(5):
                auditor.registrar(self.herramienta_normal, {})

        assert sum("APAGADA" in r.message for r in caplog.records) == 1

    # -- no romper ----------------------------------------------------------

    def test_un_fallo_de_escritura_no_levanta(self, auditor, monkeypatch):
        def no_se_puede(*_a, **_k):
            raise OSError("disco lleno")

        monkeypatch.setattr(Path, "open", no_se_puede)
        # Si esto levanta, auditar se volvio un modo de fallo nuevo.
        auditor.registrar(self.herramienta_normal, {})

    def test_contar_mal_no_tumba_el_estado(self, auditor, monkeypatch):
        def no_se_puede(*_a, **_k):
            raise OSError("permiso denegado")

        monkeypatch.setattr(Path, "glob", no_se_puede)
        estado = auditor.estado()

        assert estado["acumulado"]["error"] == "OSError"
        assert estado["modo"] == "redactado"

    # -- el catalogo de arneses --------------------------------------------

    def test_ningun_arnes_declara_una_variable_que_se_llama_como_un_secreto(self):
        # Por CLASE, no caso por caso: corre sobre todo arnes registrado,
        # incluido el que el anfitrion agregue desde su propio paquete.
        assert arneses.prohibidas() == {}

    # -- la configuracion ---------------------------------------------------

    def test_la_redaccion_del_anfitrion_se_cargo_de_verdad(self, auditor):
        # Una redaccion cerrada por error de sintaxis pasa TODAS las pruebas de
        # fuga de arriba, porque no escribe nada. Esta es la que lo distingue de
        # una redaccion que funciona.
        assert auditor.redaccion.problema is None, auditor.redaccion.problema
        assert auditor.redaccion.argumentos, "el anfitrion no declaro ningun argumento seguro"
        assert auditor.redaccion.huella_config


def verificar_enganche(servidor) -> None:
    """Que el gancho este en la TABLA DE RUTEO, no solo declarado.

    Un gancho declarado no es un gancho que corre -medido: `on_initialize` de
    fastmcp 4.0.2 nunca dispara. Y un test que llama al override directo pasa
    por definicion: hay que preguntarle al servidor que va a ejecutar de verdad,
    para que falle el dia que el SDK deje de ligarlo.
    """
    from lucky_auditoria import enganches

    cual = enganches.detectar(servidor)
    if cual == "fastmcp4":
        from lucky_auditoria.enganches.fastmcp4 import AuditoriaMiddleware

        instalados = list(getattr(servidor, "middleware", []) or [])
        assert any(isinstance(m, AuditoriaMiddleware) for m in instalados), (
            "el middleware de auditoria no esta en la lista del servidor: "
            f"hay {[type(m).__name__ for m in instalados]}"
        )
        return
    from mcp.types import CallToolRequest

    handler = servidor.request_handlers.get(CallToolRequest)
    assert getattr(handler, "_lucky_auditoria", False), (
        "el handler de `tools/call` que el servidor tiene registrado no es el auditado"
    )
