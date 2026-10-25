# Encargo de ejemplo

Un encargo chico y real, para ver cómo se llena la plantilla y, sobre todo,
cómo se escribe un criterio de hecho. Al final, criterios mal escritos y
su corrección.

---

```markdown
---
encargo: 003
estado: abierto
vuelta: 1
creado: 2026-10-25
carpeta: C:\Users\Vikingo\Desktop\Proyecto Afinamiento 1\Lucky-tool-NetBox
base: 7f3a9c2
hija: subagente
revision: si
modelo_trabajo: sonnet
esfuerzo_trabajo: high
modelo_revision: opus
esfuerzo_revision: high
sesion_id: ~
plazo: ~
cambios: ninguno
---

# 003: El cliente reintenta una vez ante 502 del NetBox

## Objetivo

Una llamada a la API que recibe 502 se reintenta una sola vez, tras 2
segundos, antes de fallar. Hoy falla a la primera.

## Contexto

- El cliente está en `src/lucky_netbox/cliente.py`; la función que hace
  las llamadas es `_pedir()` (línea 41 al momento de escribir esto).
- Medido el 2026-10-24: el NetBox de laboratorio devuelve 502 durante
  ~1 s al reiniciar; tres corridas del script nocturno fallaron por eso.
- La URL y el token llegan por `NETBOX_URL` y `NETBOX_TOKEN` (nombres;
  los valores los pone el `.env` local). No hace falta tocarlos.

## Convenciones que rigen

- `CLAUDE.md`
- `REGLAS.md` (sección «Errores»: ninguna excepción se traga en silencio)
- Los tests van en `tests/` con el mismo nombre que el módulo.

## Alcance

- Puede tocar: `src/lucky_netbox/cliente.py`, `tests/test_cliente.py`
- Puede ejecutar: `uv run pytest -m "not aceptacion"`, `uv run ruff check .`
- No toca: nada bajo `src/lucky_netbox/modelos/`, ni el `.env`, ni `pyproject.toml`

## Criterios de hecho

- [ ] Chequeo barato: `uv run ruff check . && uv run pytest -m "not aceptacion"` en verde.
- [ ] Un test nuevo en `tests/test_cliente.py` simula un 502 seguido de un
      200 y comprueba que `_pedir()` devuelve el 200 y que pasaron ≥ 2 s
      entre intentos (con el reloj simulado, no esperando de verdad).
- [ ] Un test nuevo simula dos 502 seguidos y comprueba que `_pedir()`
      levanta la misma excepción que hoy, con el 502 adentro.
- [ ] Ningún otro código de estado se reintenta: un test con 404 comprueba
      una sola llamada.
- [ ] El `git diff --stat` contra `base:` lista sólo los dos archivos del alcance.

## Preguntas para el humano

## Informe de la implementadora

## Dictamen de la revisora — vuelta 1
```

---

## Criterios mal escritos, y cómo quedan bien

| Mal | Por qué no sirve | Bien |
|---|---|---|
| «El reintento funciona.» | La revisora no puede verificarlo sin creerle a la hija. | «Un test simula 502→200 y comprueba que `_pedir()` devuelve el 200.» |
| «El código queda limpio.» | No tiene sí o no. | «`uv run ruff check .` en verde.» |
| «No se rompe nada.» | Ningún comando lo prueba. | «`uv run pytest -m "not aceptacion"` en verde.» |
| «Se agregan tests.» | ¿Cuántos, de qué? Un test vacío lo cumple. | Un criterio por comportamiento, cada uno con qué simula y qué espera. |
| «No tocar otros archivos.» | Es una regla de alcance, no un criterio; nadie la mide. | «`git diff --stat` contra `base:` lista sólo los archivos del alcance.» |

La prueba de un buen criterio: la revisora puede marcarlo cumplido o no
con un comando o una lectura, sin leer el informe.
