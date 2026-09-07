"""Los lectores. `cazar` es el que paga el paquete entero."""

import json

import pytest

from lucky_auditoria import lectores


def _escribir(ruta, lineas):
    with ruta.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"tipo": "cabecera", "esquema": 1}) + "\n")
        for linea in lineas:
            f.write(json.dumps(linea) + "\n")
    return ruta


@pytest.fixture
def registro(tmp_path):
    return tmp_path / "reg.jsonl"


class TestLeer:
    def test_la_cabecera_no_es_una_llamada(self, registro):
        _escribir(registro, [{"herramienta": "x"}])

        assert [x["herramienta"] for x in lectores.leer([registro])] == ["x"]

    def test_una_linea_rota_no_corta_la_lectura(self, registro):
        # Un registro se lee JUSTO cuando algo anduvo mal, y a veces lo que
        # anduvo mal fue el disco.
        _escribir(registro, [{"herramienta": "a"}])
        with registro.open("a", encoding="utf-8") as f:
            f.write("{esto no es json\n")
            f.write(json.dumps({"herramienta": "b"}) + "\n")

        assert [x["herramienta"] for x in lectores.leer([registro])] == ["a", "b"]

    def test_un_archivo_inexistente_no_levanta(self, tmp_path):
        assert list(lectores.leer([tmp_path / "no-existe.jsonl"])) == []


class TestCazar:
    def test_encuentra_el_argumento_que_no_vuelve(self, registro):
        _escribir(
            registro,
            [
                {
                    "modo": "crudo",
                    "herramienta": "node",
                    "argumentos": {"name": "R1", "descripcion": "se descarto"},
                    "respuesta": json.dumps({"name": "R1", "id": 7}),
                }
            ],
        )

        candidatos = lectores.cazar(lectores.leer([registro]))

        assert [c["argumento"] for c in candidatos] == ["descripcion"]

    def test_compara_por_valor_y_no_por_substring(self, registro):
        # `name="R1"` aparece DENTRO de "R10", que es otro dato. Contarlo como
        # devuelto taparia justo el caso que se busca.
        _escribir(
            registro,
            [
                {
                    "modo": "crudo",
                    "herramienta": "node",
                    "argumentos": {"name": "R1"},
                    "respuesta": json.dumps({"nodos": ["R10", "R11"]}),
                }
            ],
        )

        assert [c["argumento"] for c in lectores.cazar(lectores.leer([registro]))] == ["name"]

    def test_encuentra_el_valor_anidado_hondo(self, registro):
        _escribir(
            registro,
            [
                {
                    "modo": "crudo",
                    "herramienta": "node",
                    "argumentos": {"name": "R1"},
                    "respuesta": json.dumps({"a": {"b": [{"c": "R1"}]}}),
                }
            ],
        )

        assert lectores.cazar(lectores.leer([registro])) == []

    def test_una_linea_redactada_no_produce_candidatos(self, registro):
        # Sin la respuesta entera no hay contra que comparar.
        _escribir(
            registro,
            [{"modo": "redactado", "herramienta": "node", "argumentos": {"name": "R1"}}],
        )

        assert lectores.cazar(lectores.leer([registro])) == []

    def test_una_respuesta_recortada_no_produce_candidatos(self, registro):
        # Comparar contra media respuesta daria falsos positivos, y `cazar` ya
        # produce candidatos: sumarle ruido lo vuelve inservible.
        _escribir(
            registro,
            [
                {
                    "modo": "crudo",
                    "herramienta": "node",
                    "argumentos": {"name": "R1"},
                    "respuesta": json.dumps({"nodos": []}),
                    "respuesta_recortada_de": 90000,
                }
            ],
        )

        assert lectores.cazar(lectores.leer([registro])) == []


class TestRechazos:
    def test_encuentra_el_lote_que_salio_ok_con_fallos_adentro(self, registro):
        _escribir(
            registro,
            [
                {"herramienta": "a", "resultado": "ok", "retorno": {"fallaron": 3, "total": 15}},
                {"herramienta": "b", "resultado": "ok", "retorno": {"fallaron": 0}},
                {"herramienta": "c", "resultado": "ok"},
            ],
        )

        encontrados = lectores.rechazos(lectores.leer([registro]))

        assert [x["herramienta"] for x in encontrados] == ["a"]
        assert encontrados[0]["resultado"] == "ok", "la llamada salio bien y aun asi hubo fallos"


class TestPorSesion:
    def test_cuenta_lo_que_hizo_cada_una(self, registro):
        _escribir(
            registro,
            [
                {"sesion": "aaa", "herramienta": "project", "resultado": "ok", "cuando": "1"},
                {"sesion": "aaa", "herramienta": "project", "resultado": "error", "cuando": "2"},
                {"sesion": "bbb", "herramienta": "node", "resultado": "ok", "cuando": "3"},
            ],
        )

        cuentas = lectores.por_sesion(lectores.leer([registro]))

        assert cuentas["aaa"]["llamadas"] == 2
        assert cuentas["aaa"]["errores"] == 1
        assert cuentas["aaa"]["herramientas"] == {"project": 2}
        assert cuentas["aaa"]["hasta"] == "2"
        assert set(cuentas) == {"aaa", "bbb"}


def _cruda(respuesta, argumentos=None):
    return {
        "modo": "crudo",
        "herramienta": "verbo",
        "argumentos": argumentos or {},
        "respuesta": json.dumps(respuesta),
    }


class TestAfirmaciones:
    def test_exito_con_TODAS_las_listas_vacias(self, registro):
        _escribir(registro, [_cruda({"ok": True, "hallazgos": [], "total": 0})])

        salida = lectores.afirmaciones(lectores.leer([registro]))

        assert salida[0]["señales"] == ["exito_con_efecto_vacio"]
        assert salida[0]["vacios"] == ["hallazgos", "total"]

    def test_una_lista_vacia_entre_llenas_NO_es_señal(self, registro):
        # La condicion que separa la señal del ruido. Sin ella, cualquier
        # respuesta con un campo opcional vacio seria un candidato.
        _escribir(registro, [_cruda({"ok": True, "nodos": ["R1"], "errores": []})])

        assert lectores.afirmaciones(lectores.leer([registro])) == []

    def test_un_cero_que_no_nombra_una_cuenta_no_se_reporta(self, registro):
        # `puerto: 0` no es un efecto vacio, es un puerto. La primera version de
        # esta guarda ponia `nodos: ["R1"]` al lado, asi que no se marcaba nada
        # y pasaba igual con la regla borrada: se cumplia sola. Lo caza la
        # reversion. Ahora la linea SI se marca, y lo que se comprueba es que el
        # cero no aparezca entre los vacios.
        _escribir(registro, [_cruda({"ok": True, "puerto": 0, "nodos": []})])

        salida = lectores.afirmaciones(lectores.leer([registro]))

        assert salida[0]["señales"] == ["exito_con_efecto_vacio"]
        assert salida[0]["vacios"] == ["nodos"]

    def test_no_es_recursivo_a_proposito(self, registro):
        # Anidado da demasiado ruido: la señal deja de servir. Mismo defecto que
        # el de arriba en su primera version, y misma correccion: la linea se
        # marca, y lo que se mira es que el dict vacio no entre en los vacios.
        _escribir(registro, [_cruda({"ok": True, "datos": {}, "n": []})])

        salida = lectores.afirmaciones(lectores.leer([registro]))

        assert salida[0]["vacios"] == ["n"]

    def test_un_anidado_con_listas_vacias_no_alcanza_para_la_señal(self, registro):
        _escribir(registro, [_cruda({"ok": True, "datos": {"items": []}, "n": ["x"]})])

        assert lectores.afirmaciones(lectores.leer([registro])) == []

    def test_respuesta_flaca_por_umbral_absoluto(self, registro):
        _escribir(registro, [_cruda({"ok": True, "mensaje": "listo"})])

        assert "respuesta_flaca" in lectores.afirmaciones(lectores.leer([registro]))[0]["señales"]

    def test_una_respuesta_gorda_no_es_flaca(self, registro):
        _escribir(registro, [_cruda({"ok": True, "a": 1, "b": 2, "c": 3})])

        assert lectores.afirmaciones(lectores.leer([registro])) == []

    def test_un_rechazo_nunca_es_una_afirmacion(self, registro):
        # `ok: false` ya dice que no paso nada: no hay nada que denunciar.
        _escribir(registro, [_cruda({"ok": False, "items": []})])

        assert lectores.afirmaciones(lectores.leer([registro])) == []

    def test_sin_ok_declarado_no_se_supone_que_salio_bien(self, registro):
        _escribir(registro, [_cruda({"items": []})])

        assert lectores.afirmaciones(lectores.leer([registro])) == []


class TestCazarSalteaLoQueNoVuelve:
    def test_un_booleano_no_es_candidato(self, registro):
        # Un booleano no "vuelve": cambia el camino. Compararlo es ruido
        # garantizado, y `cazar` ya produce candidatos.
        _escribir(registro, [_cruda({"nombre": "R1"}, {"forzar": True, "nombre": "R1"})])

        assert lectores.cazar(lectores.leer([registro])) == []

    def test_en_un_rechazo_no_se_caza_nada(self, registro):
        # Es normal que el argumento no haya tenido efecto: lo rechazaron.
        _escribir(registro, [_cruda({"ok": False}, {"nombre": "R1"})])

        assert lectores.cazar(lectores.leer([registro])) == []

    def test_un_exito_sin_ok_declarado_si_se_caza(self, registro):
        # El control: la guarda de arriba no puede apagar el caso normal.
        _escribir(registro, [_cruda({"otra": "cosa"}, {"nombre": "R1"})])

        assert [c["argumento"] for c in lectores.cazar(lectores.leer([registro]))] == ["nombre"]
