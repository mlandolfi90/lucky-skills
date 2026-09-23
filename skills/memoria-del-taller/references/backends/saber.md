# Backend: saber

```text
BACKEND=saber
MODO=mcp
VERSION=1.0.0
DECLARACION=MEMORIA=saber:mcp
SERVICIO=lucky-tool-saber (servidor FastMCP; sirve el repo privado lucky-saber)
MEDIDO=2026-09-23, desde lucky-skills, con la sesión de lucky-tool-saber
  corroborando contra su código
```

## Cómo se encuentran las herramientas

Se llaman `saber_<algo>`, pero **el prefijo depende de cómo el harness
monte el servidor**: por un conector de claude.ai aparecen como
`mcp__claude_ai_<conector>__lucky_saber-saber_buscar`; por el bus de litellm
`/mcp`, como `mcp__lucky-mcp__lucky_saber-saber_buscar`. Se buscan por el
nombre base. Puede haber más de un conector exponiendo las mismas
herramientas: son el mismo servicio.

## Los cinco verbos

| verbo | llamada | qué hay que saber |
|---|---|---|
| `buscar` | `saber_buscar(sintoma, scopes=["global"], k=5)` | Por defecto sólo fichas `LIVE` de scope `global`. Para algo específico se suma `stack:<tec>` o `repo:<nombre>`. Suma una consulta a la telemetría. |
| `leer` | `saber_ficha(id)` | Devuelve el cuerpo completo. También suma una consulta. |
| `proponer` | `saber_proponer_ficha(sintoma, tipo, causa_raiz, accion, anti_accion, prevencion, scope, sesion, proyecto)` | **No es un borrador: queda servida a todas las sesiones al instante**, en main, después de pasar lint y leak-scan. `tipo` es `GAP`, `GREP`, `DRIFT` o `FALSO-VERDE`. Idempotente por contenido. Sin `sesion`, la ficha no se puede contrastar después. |
| `senalar` | `saber_senal(sospecha, contexto)` | Escribe en `SENALES.md` en una rama de revisión, **nunca** en main. Es para lo que parece pasar y todavía no se puede afirmar. |
| `reportar` | `saber_telemetria(eventos=[{event_id, entry_id, run_ledger_ref, veredicto}])` | `run_ledger_ref` es obligatorio: en repos Skills v3 es `receipt:<RECEIPT_HASH>`. `veredicto` es `funciono`, `parcial` o `no_funciono`. Queda como **alegado**: no mueve el contador `usos`, que es de la destilación humana. |

## Herramientas de apoyo

No son verbos, pero sirven para operar el backend:

- `saber_frescura()` — el sha servido y si está stale o tainted. Barata.
- `saber_index(scopes, incluir_candidate)` — lista el catálogo servido.
- `saber_metricas(entry_id)` — contadores de telemetría por ficha.

## Comportamiento medido

**1. La primera lectura de una sesión puede cortarse a los 60 s, y no es
que el saber esté caído.** Cada herramienta de lectura pasa antes por un
refresco del repo bajo un lock: `git ls-remote` (tope 30 s); si el remoto
avanzó, además `fetch` (60 s) y el leak-scan (60 s). Después de un deploy,
la primera llamada además clona (180 s) y escanea el clon (60 s): unos
270 s, contra un corte de litellm a los 60. El hilo del servidor termina
igual, así que las llamadas siguientes salen rápido. Fuente:
`lucky-tool-saber` `config/settings.py:107-109`, `saber/source.py:77,156-225`.

Qué hacer: **tibiar con `saber_frescura()` y hacer la lectura real dentro
de los 30 s siguientes**, que es la ventana del debounce. Si igual cortó,
reintentar una vez pasado un minuto. Recién si falla de nuevo, `UNAVAILABLE`.

Según el compose del repo, el clon vive fuera del volumen montado, así que
cada contenedor nuevo vuelve a clonar. Producción no se midió.

**2. `saber_metricas` no cuenta fichas: cuenta filas de telemetría.** Incluye
entradas CANDIDATE sin endosar e ids huérfanos. Para contar fichas servidas
se usa `saber_index` con scope `global`. El 2026-09-23 la diferencia era de
62 contra 48 fichas de fallo según cuál se mirara.

**3. Leer también deja rastro.** `buscar` y `leer` suman una consulta a la
ficha. No es un problema, pero `leer` una ficha sólo para ver si existe le
infla el contador.

**4. Dos escrituras con consecuencias opuestas.** `proponer` publica para
todos al instante; `senalar` queda en una rama de revisión. Ante la duda,
es `senalar`: una señal que resultó cierta se promueve, una ficha
equivocada ya la leyeron otras sesiones.

## Degradación

- El servidor no está montado en la sesión → `MEMORIA=UNAVAILABLE`.
- Una lectura cortó, se tibió y se reintentó, y volvió a cortar →
  `MEMORIA=UNAVAILABLE`, declarado. Nunca "no hay fichas".
