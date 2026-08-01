---
name: logalizar
description: Instrumentar un alcance con eventos de log estándar para capturar en runtime un error que la reproducción local no muestra. Usar en diagnóstico cuando correr el código a mano no reproduce el fallo.
---

# Logalizar

Hacer que el error se delate solo: en vez de perseguirlo con corridas que no lo
reproducen, instrumentar el alcance sospechoso y capturar evidencia del runtime
real.

## Invariantes

- La instrumentación solo agrega emisión de eventos; no cambia lógica de
  negocio. Arreglar es otro cambio, con su propio ciclo.
- Formato estándar de evento: uno solo, estructurado, por unidad de trabajo
  (wide event), emitido al completar o fallar, con esquema consistente:

  ```json
  {"ts":"<UTC>","level":"info|error","service":"...","correlation_id":"...",
   "unit":"<módulo.función>","outcome":"OK|ERROR","error":"<clase: mensaje>",
   "duration_ms":0,"context":{"<claves del sospechoso>":"..."}}
  ```

  El `correlation_id` se propaga a través de las unidades instrumentadas: una
  búsqueda por un id reconstruye el viaje completo.
- Nunca emitir secretos, credenciales, tokens ni datos personales; las query
  strings se recortan antes de loguear. Revisar los eventos con ese filtro
  antes de cerrar.
- Escribir instrumentación exige TARGET confirmado y consulta previa al mapa
  de colisiones sobre las rutas a tocar.
- La instrumentación no queda a medias: al cerrar el diagnóstico se retira, o
  se promueve explícitamente a observabilidad permanente con aprobación.

## Flujo

1. Delimitar el sospechoso: síntoma observado, rutas y unidades candidatas.
2. Diseñar los puntos de emisión en las fronteras de esas unidades (entrada,
   salida, error), declarando qué evento se espera ver si la hipótesis es
   cierta y cuál la contradice. El evento `error` se emite dentro del
   `except`, preservando el flujo original (re-raise o supresión intactos);
   el wide event de la unidad se emite en el `finally`, que corre siempre.
   Blanco prioritario: los `except` que suprimen el error sin registrarlo —
   ahí vive el fallo que una corrida manual nunca muestra. No sembrar trazas
   línea por línea: un evento por unidad, en sus fronteras.
3. Instrumentar como cambio atómico de solo-emisión.
4. Capturar: ejecutar el flujo real o esperar tráfico real; recolectar los
   eventos del alcance.
5. Diagnosticar desde la evidencia: el evento que contradice lo esperado
   señala la unidad culpable, con archivo y línea del emisor.
6. Cerrar: retirar o promover la instrumentación, y registrar el hallazgo en
   el ciclo de cambio que corresponda.

## Degradación

- Si el error no aparece en la captura, declararlo: `CAPTURE=NOT_REPRODUCED`
  no es fracaso, es evidencia que acota la hipótesis (el fallo no vive en el
  alcance instrumentado o depende de una condición no cubierta).
- Si el runtime no es observable (sin acceso a sus logs), declararlo y frenar;
  no inferir desde silencio.

## Salida

```text
LOGALIZE_ID=...
SCOPE=<rutas instrumentadas>
EVENTS_ADDED=n
CAPTURE=PENDING|CAPTURED|NOT_REPRODUCED
EVIDENCE=<ruta del log o extracto>|NONE
DIAGNOSIS=FOUND|UNRESOLVED
INSTRUMENTATION=REMOVED|PROMOTED|PENDING_DECISION
```
