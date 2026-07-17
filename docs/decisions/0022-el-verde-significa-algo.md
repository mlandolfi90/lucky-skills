---
id: adr:0022
schema: decision/1
tipo: decision
estado: ACEPTADA
creado: 2026-07-17
supersede: null
superseded_by: null
refs: [corrida:2026-07-17-el-verde-significa-algo, adr:0016, adr:0017, adr:0018, bitacora:DRIFT-007, bitacora:FALSO-VERDE-004]
---

# 0022 — El verde significa algo: runner ajeno + RED_GREEN

## Contexto

La ley tiene una asimetría que nadie había nombrado: **verifica que el verde
EXISTA, nunca que SIGNIFIQUE algo.**

La REGLA 0 (`crisol/SKILL.md`, §2 "Anti-romper") es de las reglas más fuertes del
Crisol: *"el Verificador corre los tests ÉL MISMO, EN el `TARGET:` declarado…
Sin verde propio → FAIL automático. No se confía en reporte ajeno… Jamás en la PC
local"*. Es la doctrina correcta. **Y no hay con qué cumplirla.** Hoy la hace
cumplir un rol-LLM sobre sí mismo, en la máquina del operador — la única que la
regla nombra explícitamente como ilegal.

El repo tiene la evidencia de que eso duele, escrita por él mismo. La entrada
`bitacora:DRIFT-007` documenta el síntoma: el mismo hook da verde en Windows y
muere en Linux con `command not found` (exit 127), o falla **en silencio** por el
stub de Microsoft Store (exit 49). **Mordió dos veces** — la segunda, el paso 6b
de `/ley` usaba `command -v` y falló callado en una corrida real. Su línea de
prevención dice, textual: *"la corrida que lo toque corre la suite en Linux fiel
(REGLA 0 multi-OS)"*. Un runner Linux ajeno no es una mejora: es el cumplimiento
de una regla que el repo ya se dio y no podía honrar.

El segundo flanco lo trajo el análisis de `obra/superpowers` (cosecha
2026-07-17, endosada por el operador): ellos exigen **ver el test fallar antes**
de escribirlo, y probar el rojo de un test de regresión **revirtiendo el fix**.
La ley de acá no dice una palabra sobre cómo nace un test. Un test que nunca se
vio fallar no prueba nada: puede estar afirmando `true == true` con nombre de
feature.

Nota honesta de procedencia: el mismo análisis mostró que superpowers **le
prohíbe a su reviewer re-correr la suite** ("el implementador ya los corrió") —
o sea que su evidencia de TDD entra al review como texto. Escribieron la teoría
del autoengaño y dejaron abierto justo el agujero que la REGLA 0 cierra. Se roba
su ciclo, no su cadena de verificación.

## Decisión

1. **CI en runner ajeno.** `.github/workflows/` corriendo en `ubuntu-latest` en
   cada push: las suites de `plugins/lucky/skills/*/tests/`, `registros-lint.py`,
   `leak-scan.sh` y `proyectar.py --check`.
   - **El runner ES el TARGET ajeno que la REGLA 0 exige.** No es una regla
     nueva ni un guardián: es la infraestructura que hace verdadera una regla que
     ya existía. El CI no dictamina IDs del catálogo ni escribe líneas `[V]`.
   - **Linux, deliberadamente.** El operador trabaja en Windows/Git-Bash. Un
     runner que corra en su mismo OS no compra nada: la familia de bugs que ya
     mordió dos veces (`DRIFT-007`) es exactamente la que solo aparece cruzando
     de OS.
   - **Descubrimiento por glob, no por lista** (`*/tests/test-*.sh`): un test que
     el CI no corre es un test que no existe. Y **glob vacío = job rojo** — un
     glob que no matchea nada y pasa en verde sería el falso-verde que esta
     decisión vino a matar.
   - `leak-scan.sh` pasa a correr en **cada push**, no solo en la forja. Motivo
     concreto: su rama Windows estuvo muerta un tiempo indeterminado y se
     descubrió por un verificador fresco, no por el gate
     (`diagnostico:2026-07-16-leak-scan-ruta-windows-muerta`).
   - **Gate de drift de proyecciones**: `proyectar.py --check` en CI convierte
     *"proyecciones GENERADAS — jamás editar a mano"* (`registros.yaml`) de
     pedido en hecho. Patrón tomado de `garrytan/gstack`, que corre su generador
     en CI y hace `git diff --exit-code`.

2. **`RED_GREEN` — ID nuevo del catálogo §5.** Enunciado: *todo test que sostiene
   un PASS fue VISTO fallar antes de existir el código que lo hace pasar; todo
   test de regresión probó su rojo revirtiendo el fix.* Trigger: si el diff crea
   o modifica tests. Clase: **J** (juicio — lo dictamina un rol-LLM sobre
   evidencia, no un parser).
   - Ya se paga el costo caro (el Verificador corre los tests él mismo) y no se
     cobraba el beneficio: saber que el verde significa algo.
   - El microfix de ayer ya lo hizo **sin regla que lo obligue**: prueba A/B sobre
     el mismo archivo, script viejo exit 0 vs sonda exit 1
     (`microfix:2026-07-16-leak-scan-ruta-windows`). La regla convierte esa buena
     costumbre en ley.

3. **`TEST_COVERAGE: NONE` queda declarado como deuda, NO se toca acá.** Hoy
   `NONE` puede emitir `PASS` (solo bloquea el tag estable). Es un falso-verde con
   nombre propio, pero cambiar su semántica altera cuándo una corrida puede cerrar
   en **toda la flota**: merece su propia decisión del operador, no el arrastre de
   esta corrida.

## Consecuencias

- La REGLA 0 pasa de doctrina a hecho: existe un target ajeno, reproducible y que
  no es la máquina del operador.
- **El primer verificador de la forja que NO es un LLM.** Hasta hoy, todo veredicto
  de la matriz lo emitía un rol-LLM (los 2 gates mecánicos cubren *forma*: ¿hay
  fila ACTIVE con TARGET? ¿la matriz cierra sin FAIL?). El CI es el primero que
  juzga *verdad* — corre el código y el exit code no negocia.
- Se acota el hueco declarado en el RETRO de `corrida:2026-07-16-equipo-doc-v1-fix`
  y confirmado por dos análisis independientes: *"tus 13 suites las corre un
  rol-LLM que declara haberlas corrido"*.
- **Costo real, declarado:** el CI corre en cada push y puede ponerse rojo en
  `main`. Eso es el punto — hoy `main` puede estar roto en Linux y nadie lo sabe.
- **Límite explícito:** el CI verifica lo que es ejecutable. Las 15 reglas de
  clase **J** de la matriz siguen siendo juicio de rol-LLM y ningún runner las
  cubre. Esta decisión no cierra ese eje; lo acota.
- **Deuda declarada:** (a) la semántica de `TEST_COVERAGE: NONE`; (b) el
  pressure-testing de la prosa de la ley — que es donde vive el 90% del gobierno
  y hoy no es falsable (parkeado en la cosecha, descartado por el operador para
  esta corrida); (c) 10 de 15 skills no tienen `tests/`, así que el runner ajeno
  nace cubriendo solo un tercio del catálogo.
- **Considerado y descartado a propósito:** hacer del CI un guardián con celda en
  la matriz. El CI no es un rol del Crisol: es el suelo donde la REGLA 0 se para.
  Confundirlo sería inventar una regla para justificar una herramienta.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.6.0` (cache local, NO la ley).**
