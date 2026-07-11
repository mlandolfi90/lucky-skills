# Bug-<frase-corta> — <la falla en una línea>

> Plantilla de una falla del catálogo `hotfixs/`. Copiala a
> `Bug-<frase-corta>.md` (kebab-case) e indexá la falla en `INDICE.md`.
>
> **Cuándo nace:** cuando la falla se PRESENTA, no cuando se resuelve. Al
> observarla se crea este archivo con la descripción y lo intentado hasta el
> momento.
> **Qué es este archivo:** el borrador VIVO mientras se itera —se escribe
> beta a beta, con WIP-commit por cada una, así `git show <commit>` reconstruye
> el código exacto de cada intento— y la memoria PERSISTENTE después. Un solo
> artefacto para las dos cosas.
> **Indexá por SÍNTOMA OBSERVABLE** ("ESC no cierra"), no por tema ("problema
> de foco").
> **Cero secretos:** nombres de variable y rutas relativas; nunca tokens, IPs
> ni valores reales. Los veredictos se transcriben con scrub
> (rutas→`<ruta>`, hosts/IPs→`<host>`, jamás volcados de consola completos):
> este archivo viaja en la historia pública y el leak-scan lo barre.

## Falla

<qué se observa y en qué condición — el SÍNTOMA, no la causa>

## Estado

<⏳ abierta | 🔧 resuelta (pendiente re-aplicar/verificar) | ✅ resuelta+verificada> · <versión/contexto>

- régimen: <ciego | vidente>
  <!-- vidente: el modelo corre el flujo/tests y verifica cada camino, cruzado
       contra el entorno real. ciego: el operador es el ÚNICO instrumento de
       runtime — el modelo enumera los caminos por código, el operador prueba
       cada uno. Determina cómo se lee cada veredicto de "Qué se intentó".
       Universal: se declara aunque haya un solo control. -->
- BASE: <sha corto del commit base>
  <!-- copia del BASE del RUN-LEDGER (esa es la fuente de verdad del sha);
       ancla del `git diff <BASE> -- <paths>` que va en "Cómo se resolvió". -->
- cosechado: no
  <!-- guard de idempotencia de la cosecha por intensidad: §Cerrar lo LEE antes
       de ofrecer destilar y, al cosechar, lo reescribe a `<fecha> → <IDs-BITACORA>`.
       Si ya tiene fecha e IDs, NO se vuelve a destilar en una re-apertura. -->

> Pasa a ✅ SOLO cuando el humano lo confirma.

## Invariantes

> Esta sección se paga solo si **>1 control** gobierna el estado. Una falla de
> un único control no la necesita: borrala. Cuando hay varios controles, este
> mapa es lo que ataca el círculo "arreglo 1, rompo 2" en la RAÍZ —persiste
> quién manda, así la superficie no se re-descubre en cada sesión.

- **modelo-estado:** `<quién MANDA>` es el maestro · `<quién/es es CONFIG>` obedece(n).
  - Arranca **provisional**. Se marca **firme** recién cuando la lista del GREP
    (quién escribe/lee la señal del efecto en el código) y la lista del operador
    (los controles que percibe de usarlo) COINCIDEN. Si el grep encuentra una
    señal que nadie nombró, o se nombra un control que el grep no explica, ahí
    hay un hueco y se salda antes de darlo por firme. `firme` es etiqueta de
    calidad, no candado: nada frena iterar mientras tanto.
  - Si se **re-modela**, los `✓`/`~` tomados bajo el modelo viejo se marcan
    `revalidar`: un verde bajo el maestro equivocado es falso y no cuenta como
    memoria.
- **invariante 1:** nunca el efecto activo sin su indicador (p. ej. mic caliente sin su caja).
- **invariante 2:** nunca el indicador sin el efecto.

## Cómo se resolvió

<la cura concreta: archivos/funciones tocadas + la referencia git
 `git diff <BASE> -- <paths>`. Si sigue abierta: — (abierta).>

> Si la cura cerró con un `✓ (una vía)` sin barrer todos los caminos + los dos
> invariantes, anotalo acá EXPLÍCITO: la cura no es entera y quedó constancia de
> que pasó media cura a la corrida cara.

## Qué se intentó

> Log vivo de betas, una fila por intento, escrita ANTES de la siguiente. La
> memoria anti-círculo: una hipótesis quemada (`✗`) no se repite. Incluí los
> caminos muertos (☠️) para no volver a pisarlos.
>
> **Veredictos:** `✓` resuelto · `~` parcial · `✗` sin efecto/empeoró — siempre
> símbolo **+ cita textual del operador**.
> - `✓ (una vía)`: verde PROVISIONAL. El camino que se probó quedó verde, pero
>   la misma beta todavía no pasó por todos los caminos conocidos. No es cura
>   entera.
> - El `✗`/`~` **nombra POR CUÁL camino se rompió** (dentro de la celda de
>   veredicto), no solo "sigue igual". Sin ese dato, una regresión cruzada es
>   idéntica a un strike del mismo síntoma y el choque cruzado (un control que
>   una beta anterior dejó en `✓` y vuelve a `✗`/`~`) no se puede ver.
> - **Stamp confirmado o no hay fila:** el veredicto solo entra si el operador
>   confirmó el stamp de la versión que probó; stamp ≠ versión entregada ⇒ se
>   repite la prueba (un `✗` sobre código viejo quema para siempre una hipótesis
>   correcta — DRIFT-008).
> - La columna `commit` ata cada fila al código exacto: WIP-commit por beta →
>   el log es consultable con `git show <commit>`.
> - La columna `evidencia` es dónde apoyás el veredicto cuando instrumentaste
>   (el log de estado real del 2-strikes); `—` si no hizo falta.
>
> (Para una falla trivial de un solo control alcanzan dos viñetas; la tabla es
> para el arco iterado.)

| versión | commit | hipótesis | cambio (1 línea) | veredicto | evidencia |
|---|---|---|---|---|---|
| v0.9.10-b2 | a1b2c3d | margin del checkbox | reset margin del input | ✗ "sigue igual" (rompe por el atajo ☠️) | — |
| v0.9.10-b3 | b4c5d6e | espejar por el gate real | mirror del estado efectivo | ✓ (una vía) "anda por toggle" | log de estado |

## Relacionadas

[[Bug-<frase-corta>]]

> Si esta falla RECURRE como CLASE (no como instancia), se cosecha a la Bitácora
> —asciende de bug a patrón— y se anota su ID acá: patrón → `<ID-BITACORA>`.
