---
name: hotfix
description: >-
  Hotfix — permiso de trabajo en caliente: iterar un fix EN VIVO con el
  operador probando cada versión, sin pagar una corrida Crisol por intento y
  sin caer en el CÍRCULO (arreglás X, se rompe Y). Disparar cuando el operador
  diga "/hotfix", "probemos rápido", "fix en caliente", "estoy acá
  mirando/probando", o cuando un debug entre en ciclo prueba-error con el
  humano presente dando veredictos. Abre UN permiso (ACTIVE + runState wip),
  versiona betas -bN con su veredicto, y va llenando
  docs/hotfixs/Bug-<frase-corta>.md (borrador vivo + memoria persistente) hasta
  formalizar con UNA corrida Crisol al cierre, solo con la solución. NO usar
  para cambios con solución ya conocida (eso es corrida Crisol directa), NI sin
  operador presente (sin veredicto humano no hay ciclo), NI contra
  @testing/@production (solo mesa caliente).
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# Hotfix — permiso de trabajo en caliente

En seguridad industrial, el trabajo con fuego no se prohíbe: se hace bajo
**permiso** — declarado, acotado, con vigía y con cierre. Acá igual: iterar
a ciegas quemó ~10 versiones y horas en el caso fundacional (popover-bleed);
pagar una corrida Crisol completa por cada intento fallido quema recursos.
Este carril usa lo que la ley YA permite (ACTIVE + `runState: wip` = editar
y WIP-commitear sin matriz; la matriz se paga UNA vez, al cierre) y le suma
la disciplina que evita la adivinanza serial.

Pero la adivinanza serial no es el único enemigo: el otro es el **CÍRCULO**
—arreglás X y se rompe Y, arreglás Y y se rompe X— donde cada beta pasa
cuando la probás sola, así que ningún breaker de mismo-síntoma salta. Ese
ciclo no nace de olvidar lo que rompiste, sino de perder de vista lo que YA
ANDABA: la tabla tiene memoria de lo que intentaste, no baseline de lo que
debe seguir siendo verdad. Por eso, **cuando más de un control gobierna un
estado**, la salida de este carril no es "el síntoma que tocaste quedó verde"
sino evidencia de una **cura entera**: el estado sostenido por todos los
controles que lo gobiernan.

## §Abrir (el permiso)

**0. Colisión:** si ya existe una entrada ACTIVE para el branch (hotfix u
otra), NO abras una segunda — el invariante es UNA ACTIVE por branch y el
gate juzgaría la matriz equivocada. O te sumás al hotfix existente (mismo
`Bug-`, continuás la numeración -bN donde quedó) o frenás y resolvés con el
humano cuál corrida manda.

**1. Entrada en RUN-LEDGER** — bloque mínimo COMPLETO (el gate exige Tier,
Fecha y TARGET reales o bloquea la primera edición):

```markdown
### <branch> — <fecha> (hotfix)
- STATUS: ACTIVE
- Tier: fast-path (provisional — se re-clasifica al cierre)
- Fecha: <fecha>
- TARGET: <target confirmado>
- MODEL: <modelo>
- Alcance: hotfix: <síntoma en una línea>
- BASE: <sha corto del commit base>
<!-- VEREDICTOS:BEGIN -->
- runState: wip
<!-- VEREDICTOS:END -->
```

El bloque VEREDICTOS va desde el día 0: el gate solo lee `runState:` DENTRO
del bloque — un `closing` escrito afuera es invisible y el cierre pasaría
SIN matriz (fail-open silencioso). El `BASE:` de acá es la fuente de verdad
del sha; el `Bug-` lo copia por conveniencia (§Cerrar lo consume desde ahí).

**2. Frontera de TARGET:** hotfix solo contra mesa caliente (`pc-local`,
`docker-local`, `paas:…@dev`). Contra `@testing`/`@production` se REHÚSA y
se redirige al carril de promoción; si el operador insiste igual, su
confirmación explícita queda registrada en el `Bug-`.

**3. El catálogo de fallas** — `docs/hotfixs/Bug-<frase-corta>.md` es el ÚNICO
artefacto del carril: borrador vivo mientras iterás Y memoria que queda para
el próximo que pise el bug. Una falla NACE cuando se presenta (no cuando se
resuelve). Antes de la primera beta, grepeá **primero** `docs/hotfixs/INDICE.md`
(C — la instancia de ESTE repo) y **después** el INDEX de la bitácora (A — el
patrón cross-repo), de lo más específico a lo más general; si ya existe el
`Bug-`, leé "Qué se intentó" para no repetir un camino muerto ☠️. Si no
existe, creá el `Bug-` (y la primera vez, el `INDICE.md`) copiando la
plantilla del propio skill (`<dir-base-del-skill>/templates/_PLANTILLA.md` e
`INDICE.md` — la invocación te informa el dir-base) hacia `docs/hotfixs/`:
los templates son fuente única en el plugin, no se siembran aparte.

**Régimen de verificación (universal — un control o varios):** anotá
`régimen: ciego|vidente` en el header del `Bug-`, porque cambia cómo se lee
cada veredicto. Vidente: corrés el flujo/tests y verificás cada camino vos,
cruzado contra el entorno real (FALSO-VERDE-003). Ciego: el operador es el
único instrumento de runtime — vos enumerás los caminos por código, él prueba
cada uno.

**4. Versionado del artefacto:** fijá la gramática REAL del artefacto y la
etiqueta del stamp — extensiones de navegador: cuarto segmento entero
(`X.Y.Z.N`; el manifest no admite sufijos); semver/npm: `X.Y.Z-b.N`;
PEP 440: `X.Y.ZbN`. El stamp VISIBLE (UI/log/consola) siempre muestra la
etiqueta humana `vX.Y.Z-bN` — el operador confirma en segundos qué versión
prueba.

**5. Mapeá los controles y decí quién MANDA** — *solo si el síntoma es de
ESTADO* (algo que "sigue activo/encendido/abierto" y que se prende o apaga
por más de un control). Un hotfix de un solo control (el margen de un
popover) no paga nada de esto. **Descubrir los controles = grep + vos, y
tienen que COINCIDIR.** Grepeás quién escribe/lee la señal del efecto (el
código ve señales que no se te ocurre nombrar); vos aportás los controles que
conocés de usarlo. El `modelo-estado:` cuenta como firme recién cuando las
dos listas cierran — si el grep encuentra una señal que no nombraste, o
nombrás un control que el grep no explica, ahí hay un hueco y se salda antes.
(Nada te frena de iterar mientras tanto; "firme" es etiqueta de calidad, no
candado.)

## §El registro (el Bug- como borrador vivo)

La sesión no abre un vault efímero: escribe directo en
`docs/hotfixs/Bug-<frase-corta>.md`. La sección **"Qué se intentó"** lleva una
fila POR beta, escrita ANTES de la siguiente:

```markdown
| versión | commit | hipótesis | cambio (1 línea) | veredicto | evidencia |
|---|---|---|---|---|---|
| v0.9.10-b2 | a1b2c3d | margin del checkbox | reset margin input | ✗ "sigue igual" | — |
```

- **WIP-commit POR CADA bump -bN** (no "cada tanto": un rollback perdería
  las betas intermedias y el `Bug-` guardaría el veredicto de -b3 sin su
  código). La columna `commit` ata cada fila al código exacto — el `Bug-` es
  consultable de verdad (`git show <commit>`). Protocolo seguro: add
  explícito del `Bug-` + los paths tocados, jamás `-A`.
- **Veredictos:** `✓` resuelto · `~` parcial · `✗` sin efecto/empeoró.
  Siempre símbolo + cita textual del operador. `~` NO quema la hipótesis
  (el siguiente -bN la REFINA, no salta a otra); `✗` suma strike.
- **Stamp confirmado o no hay fila:** el veredicto solo se registra si el
  operador confirmó el stamp de la versión que probó; stamp ≠ versión
  entregada ⇒ se repite la prueba (un ✗ sobre código viejo quema para
  siempre una hipótesis correcta — DRIFT-008).
- **Veredicto diferido:** el operador puede diferir ("lo pruebo después") →
  fila `pendiente`, tope UNA a la vez (dos betas sin veredicto no se
  distinguen al probar). Al cerrar, ninguna queda `pendiente`: se resuelve
  o se marca `no probada`.
- **Hipótesis quemada (✗) jamás se repite** — la tabla es la memoria
  anti-círculos.
- **ZERO_LEAK:** los veredictos se transcriben con scrub (rutas→`<ruta>`,
  hosts/IPs→`<host>`, jamás volcados de consola completos). El `Bug-` es un
  archivo del repo y viaja a forjas públicas: el leak-scan barre
  `git ls-files` y un `Bug-` sucio brickea los releases.

**Tres toques más — solo si el síntoma es de ESTADO (>1 control):**

- El `✗`/`~` dice POR CUÁL camino se rompió (dentro de la misma celda de
  veredicto), no solo "sigue igual". Sin ese dato, una regresión cruzada es
  idéntica a un strike del mismo síntoma y el choque cruzado no se puede ver.
- Un `✓` de síntoma es PROVISIONAL — `✓ (una vía)` — hasta que la misma beta
  pase por todos los caminos conocidos. Poner verde el camino que probaste no
  dice que el estado quedó sano.
- `modelo-estado:` (definido en §Abrir 5) vive en la sección **"Invariantes"**
  del `Bug-` — persiste el mapa de controles, así la próxima vez no se
  re-descubre la superficie desde cero. Si re-modelás, los `✓`/`~` del modelo
  viejo se marcan `revalidar`: un verde bajo el maestro equivocado es falso y
  no cuenta como memoria.

## §Ciclo (la disciplina)

1. **UN cambio por ciclo** — jamás dos hipótesis juntas. Bump + stamp +
   WIP-commit.
2. **Revertí la hipótesis descartada ANTES del próximo ciclo**
   (`git restore` SOLO de los paths de fuente tocados — el `Bug-` nunca se
   revierte, es el log que persiste beta a beta): cada -bN = BASE + hipótesis
   viva. El árbol nunca acumula hacks — un veredicto sobre árbol sucio está
   contaminado por las betas anteriores.
3. Entregá al operador **QUÉ probar en 1 línea** (pasos exactos, incluido
   el refresh correcto — F5 de la PÁGINA si es extensión) → esperá su
   veredicto → fila en la tabla. Si el estado tiene >1 control, el "qué
   probar" incluye re-chequear los caminos que una beta anterior dejó en
   verde — en ciego es la única forma de que la regresión se VEA mientras
   iterás.
4. **2 strikes ⇒ conviene instrumentar** (GREP-004): al segundo `✗` sobre el
   mismo síntoma conviene frenar la adivinanza y medir (log de estado real)
   antes de tirar otra beta — refinar a ciegas es la misma adivinanza serial.
   El carril te lo avisa; vos decidís si instrumentás o seguís. Misma señal
   con 3 `~` consecutivos sobre la misma hipótesis: medí antes de seguir
   refinando.
5. Tras todo reemplazo masivo (`replace_all`/sed global): releé el diff con
   foco en las líneas agregadas en esta sesión ANTES de entregar (GAP-008 —
   una beta rota por edición quema un round-trip entero del operador).
6. Si armás un preview/harness: REPRODUCE los defaults del entorno, jamás
   los normalices, y cruzá contra el entorno real antes de fiarte de una
   medición del preview — un verde del harness que no matchea el entorno real
   es un falso-verde (FALSO-VERDE-003). Si no coincide, no lo tomes como
   evidencia.
7. Al primer síntoma que matchee el INDEX de la bitácora: abrí esa entrada
   (pull dirigido).

**Choque cruzado** (solo si >1 control) — hermano ortogonal del 2-strikes.
El 2-strikes mira el MISMO síntoma fallando dos veces → conviene instrumentar.
El choque cruzado es lo otro: un control que una beta anterior dejó en `✓`
vuelve a `✗`/`~` — su firma es "un fix hizo regresar un verde". Al primer
rebote conviene parar y re-modelar (es un AVISO, no un candado): dos señales
independientes gobiernan lo que vivís como un estado; fijá el `modelo-estado:`
y consultá DRIFT-009 (pull dirigido, Regla 7). Vos decidís si parás o seguís;
si seguís, queda anotado. Falso positivo a cuidar: por la Regla 2, un verde
puede "regresar" solo porque revertiste su fix — el rebote cuenta cuando
aparece en una beta que decía RESOLVER el estado, no cuando un verde regresa
por revert.

**Techo de iteraciones:** los ciclos beta con operador presente NO cuentan
para el techo de 3 del Crisol (ese techo es para loops Plan↔FAIL autónomos;
acá el circuit-breaker es 2-strikes + el operador decide seguir o parar).
`Iteraciones: n/3` del cierre cuenta SOLO los ciclos de la formalización.

## §Cerrar (la formalización)

**Con solución** — secuencia forward-only (los WIP quedan en la historia
como respaldo; jamás rewrite):

1. Escribí la cura en la sección **"Cómo se resolvió"** del `Bug-` (el fix
   exacto + qué intentos se descartan) y dejá la referencia git de la fuente:
   `git diff <BASE> -- <paths>`.
2. Árbol a BASE+solución: `git restore --source=<BASE> -- <paths tocados>`
   → aplicar SOLO el diff de la solución.
3. **Barrido de cura entera** (advisory — solo si >1 control): antes de
   re-clasificar, conviene barrer la solución por todos los caminos + los dos
   invariantes (nunca el efecto sin su indicador, ni el indicador sin el
   efecto), en un solo build. Un `✓ (una vía)` que llega a la matriz es la
   regresión que este carril existía para no pagar cara: si lo dejás, la cura
   no es entera y lo anotás explícito en "Cómo se resolvió". Cerrar igual es
   decisión tuya — el carril no bloquea — pero que quede escrito que pasó
   media cura a la corrida cara.
4. **Re-clasificá el Tier** con el checklist §1 del Crisol sobre el diff de
   la SOLUCIÓN — si da completo, el cierre lleva Steward/COLLISION-MAP
   (sin esto el carril sería un bypass fast-path para diffs grandes).
5. Matriz completa + `runState: closing` DENTRO del bloque VEREDICTOS +
   commit de cierre. Versión final SIN sufijo beta. Marcá el estado del
   `Bug-` como resuelta (pendiente confirmación del humano para
   resuelta+verificada) y actualizá su fila en `INDICE.md`.

**Sin solución** (se agota tiempo/paciencia): WIP-commit del `Bug-` PRIMERO,
fuente revertida a BASE, cierre honesto (RETRO). El `Bug-` queda abierto en
el catálogo — es memoria, no basura.

**Cosecha — común a ambas ramas.** Dos ascensos posibles:

- **C→A (a la Bitácora):** si el `Bug-` recurre como CLASE y no como
  instancia (el mismo patrón pisado en otro lado), ofrecé cosecharlo a la
  bitácora — asciende de bug concreto a patrón cross-repo.
- **Por intensidad:** si dolió — **≥3 filas en "Qué se intentó" o cierre sin
  solución** — ofrecé la cosecha por INTENSIDAD de la bitácora con el `Bug-`
  como material (el caso fundacional cerró CON solución y aun así produjo 6
  entradas). ANTES de ofrecer: leé la marca `cosechado:` del `Bug-`; si ya
  tiene fecha e IDs, reportalos y NO destiles de nuevo. Al cosechar: estampá
  `cosechado: <fecha> → <IDs>` en el `Bug-`.

El `Bug-` entra a los INPUTS del leak-verifier del cierre (viajó en
WIP-commits antes de que nadie lo mirara — el cierre lo revisa entero).

**Huérfana:** si encontrás una ACTIVE con `Alcance: hotfix:` de una sesión
muerta — con el operador presente: reanudá desde el `Bug-` (su "Qué se
intentó") y continuá la numeración; sin operador: cierre honesto, `Bug-`
preservado, fuente revertida a BASE. (El protocolo de huérfanas del Crisol
no aplica acá: un hotfix no tiene techo 3 ni COLLISION-MAP.)

## Peldaño 2 de la escalera (ADR 0017 — aditivo, no cambia el flujo)

El hotfix es el peldaño **2** de `diagnostico → microfix → hotfix → crisol`:
- Puede nacer **por escalada** de un microfix que reveló profundidad: hereda
  el contexto vía `refs: [microfix:<id>, diagnostico:<id>]` en su `Bug-` —
  la cadena queda trazada de punta a punta.
- **Sin saltos:** al hotfix se llega desde el 1 (o directo si el operador fija
  el tope acá); del hotfix se sale al 3 — el cierre con UNA corrida Crisol
  que esta skill YA exige es exactamente ese peldaño.
- **TARGET por peldaño:** la mesa caliente del hotfix es dev (como siempre);
  el env legal lo fija el caso y queda declarado en el `Bug-`.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.4.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.
