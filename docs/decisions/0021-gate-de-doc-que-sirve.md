---
id: adr:0021
schema: decision/1
tipo: decision
estado: ACEPTADA
creado: 2026-07-16
supersede: null
superseded_by: null
refs: [corrida:2026-07-16-equipo-doc-v1, concejo:2026-07-16-equipo-doc, adr:0018, adr:0019, adr:0020]
---

# 0021 — El gate de doc exige que el manual SIRVA, no solo que exista

## Contexto

El ADR 0020 creó el `manualizador` (un autor) y el gate de doc: una feature no
llega a `VIVA` sin `doc:`. El operador cuestionó la forma: *"¿por qué es solo un
agente? debería ser un equipito de Agente/sub-agentes"*. El diagnóstico de esa
asimetría: el Crisol tiene 6 guardianes porque **verificar** mejora con miradas
independientes; **redactar** empeora con ellas (un manual con varios autores es
un manual con varias voces). Lo que faltaba no era un equipo de redactores: era
el **juez** alrededor del autor.

Además, el gate vigente mide lo que es fácil de medir (¿el archivo existe?) y no
lo que importa (¿el usuario logra hacer la cosa?). Un `doc:` apuntando a un
archivo vacío satisface la regla dura 2 al pie de la letra.

Un concejo de 5 jueces frescos (`concejo:2026-07-16-equipo-doc`, lentes proceso ·
costo · frescura · ley · abuso) atacó el diseño propuesto: **5/5
APRUEBA_CON_CAMBIOS**, con 8 enmiendas que voltearon tres pilares del boceto. El
operador endosó el alcance v1 ("vamos con 1" = un solo agente nuevo,
verificador-frescura diferido). Esta fila es ese endoso, convocado como decisión
(rama `crisol/ramas/003-decisiones-convocables`) para que no muera en el chat.

## Decisión

1. **`lector-cero` — agente canónico, dictamina `DOC_SIRVE`.** Juez FRESCO que
   lee el manual recién escrito y **el contrato observable de la feature** (el
   cuerpo `funcionalidad`, ≤15 líneas) — nada más: ni el código, ni los
   `intentos:`, ni la conversación. Su prueba: lograr CADA comportamiento del
   contrato usando únicamente el manual.
   - **Juzga por LECTURA, no ejecutando** (enmienda E1). "Ejecutar el tutorial
     como usuario real" era: mutación por la puerta de `Bash` desde un juez
     declarado read-only, `TARGET` indefinido, y superficie de inyección (el
     manual es contenido, no instrucciones). Sus tools son `Read/Grep/Glob` —
     sin `Bash`, sin `Write/Edit`. Ejecución real = opt-in del operador con
     TARGET declarado, jamás por default.
   - **Ceguera calibrada, no total** (E2, anti-Goodhart): sin el contrato, la
     estrategia dominante del autor sería escribir MENOS (menos texto = menos
     tropiezos = PASA), y el gate degeneraría de "que sirva" a "que se entienda".
   - **Tropiezos con severidad** `BLOQUEA` (impide completar un comportamiento
     del contrato) | `COSMETICO`. Solo `BLOQUEA` justifica `FALLA`; `FALLA` sin
     tropiezo concreto = veredicto inválido → re-spawn único.
2. **El veredicto deja huella mecánica** (E3): columna `doc_veredicto:` en la
   fila feature (`PENDIENTE|PASA|FALLA` + ronda + ref); `VIVA` la exige `PASA`, y
   `registros-lint.py` lo valida. Sin esto, un `FALLA` vivía solo en el chat y la
   sesión siguiente pasaba la feature a `VIVA` legalmente — el dolor exacto que
   el ADR 0019 ya había saldado para las decisiones. El `manualizador` deja de
   escribir `doc:`: esa columna la escribe el flujo `/feature` recién tras `PASA`.
3. **Bucle autor↔lector, máximo 2 rondas, fail-closed.** Escribe → juzga →
   `FALLA` → corrige con los tropiezos verbatim → re-juzga con lector FRESCO. Sin
   convergencia: la feature queda `EN-CONSTRUCCION` y el desempate se **convoca**
   como decisión (ADR 0019 §2) — así aparece en el TABLERO en vez de ser un
   zombie invisible. `NO documentable aún` del manualizador es un corte ANTES del
   bucle: no spawnea al lector ni consume ronda. El bucle corre FUERA del techo
   de 3 iteraciones del Crisol: es acto de `/feature`, no de cierre de corrida.
4. **`audiencia: user|dev` en la fila feature** (E-proceso): con `dev` el gate se
   satisface con doc en `docs/sistema/` y el juicio corre en modo comprensión (N
   preguntas respondibles solo con el doc). Sin esto, toda feature interna
   —la mayoría en esta forja— fallaría estructuralmente por no tener un tutorial
   que no debe tener, y el gate moriría por desempate perpetuo.
5. **Frescura por CURSOR SHA, no por fechas** (E4). El mecanismo por fechas de
   commit nace muerto por dos condenas independientes: (a) `forjar-release.sh`
   re-estampa el sello en TODO el repo en cada release → 100% de falsos positivos
   a la primera forja → señal ignorada = señal muerta; (b) un typo-fix en el doc
   pone su fecha por encima del código y APAGA la señal con drift real —
   corregir una coma certificaría exactitud técnica. Queda:
   - sidecar `docs/manual/_cobertura.yaml` (dueño único de escritura: el
     `manualizador`) con `{doc, cubre: [globs a nivel de unidad estable], deps,
     verificado_en: <sha>}`. Vive en sidecar y no como frontmatter de las piezas
     porque `docs/manual/` es **narrativa** (sin frontmatter exigido) y es
     **producto** que la app renderiza: meterle frontmatter impondría un contrato
     de stripping a cada consumidor.
   - señal = `git rev-list --count <sha>..HEAD -- <globs>` con filtro de commits
     de mantenimiento declarados, implementada **dentro de `brujula.sh`** — no en
     su prosa: solo el script cumple la garantía "salida tal cual" con cero
     temperatura.
   - el cursor se mueve SOLO por acto explícito de verificación (el manualizador
     al escribir; ack tras dictamen "sin drift") — jamás por mtime.
   - `registros-lint.py` valida el sidecar (pieza sin entrada, glob muerto, sha
     inválido = error): un mapa de cobertura que driftea en silencio es el peor
     modo de falla de un detector de drift.
   - fail-closed HABLADO: "manual sin mapa de cobertura: N piezas" — nunca
     silencio, que se leería como salud.
6. **`leak-scan.sh` corre en el gate de doc antes de admitir `PASA`** (E8).
   `docs/manual/` es visibilidad **producto** (viaja a la app) y la transición a
   `VIVA` puede ocurrir fuera de una corrida Crisol → el `leak-verifier` nunca lo
   barre. Los prompts nuevos llevan la cláusula del leak-verifier: citar
   `archivo:línea` SIN transcribir valores.
7. **El `manualizador` cambia por la vía legal** (E6): supersede (ADR 0018 §4),
   jamás edición in-place de una fila `LIVE`. "No se toca" era incompatible con
   el propio bucle: sin gatillo de corrección ni `{TROPIEZOS}` como placeholder,
   el líder tendría que redactar el mandato a mano en cada ronda — el
   no-determinismo que los agentes canónicos vinieron a matar.
8. **`verificador-frescura` DIFERIDO** (E5, YAGNI). v1 construye UN agente nuevo:
   el que **gatea** (ahí la separación autor/juez paga). Un verificador que
   "jamás bloquea" y lee el mismo contexto que el autor no compra nada: ante
   drift real se paga la lectura dos veces. Su dictamen lo da el `manualizador`
   en **modo dictamen** (solo reporta, no escribe), y los desvíos confirmados se
   archivan como fila `diagnostico` ABIERTO — señalar sin persistir es susurrar.
   El agente propio nace recién si la telemetría muestra dictámenes
   desperdiciados: decisión con evidencia, no con sensación.

## Consecuencias

- El gate de doc pasa de "el archivo existe" a "el usuario logra hacer la cosa",
  con diente mecánico (lint) en vez de prosa: sobrevive al crash de sesión.
- El costo queda declarado, no descubierto: **+1 spawn barato por transición a
  VIVA** (nominal); peor caso 4 spawns + desempate convocado.
- **Regla de recalibración:** si los desempates superan a los `PASA` en N
  features consecutivas, el prompt del `lector-cero` pasa a `EN_DUDA` (ADR 0019
  §5) y se abre corrida de recalibración. El gate se ajusta con evidencia en vez
  de morir por bypass.
- La telemetría (ADR 0019 §4, fail-open) cosecha rondas, `PASA`/`FALLA` y
  desempates — insumo de la recalibración y de los evals del ADR 0020.
- **Considerado y descartado a propósito:** proyectar la frescura al
  `TABLERO.md`. El tablero es proyección determinista de filas
  (`proyectar.py` idempotente); la frescura depende del estado de git al momento
  de la consulta y rompería esa idempotencia. La frescura pertenece a la brújula
  (snapshot de sesión), no al tablero (proyección de registros). Escrito acá para
  que nadie lo "mejore" después.
- **Límite explícito, declarado:** la señal detecta "código tocado después de la
  última verificación del doc", NO drift semántico; el comportamiento que cambia
  sin tocar los paths cubiertos no se ve (residuo inherente a toda señal por
  paths, mitigado por globs a nivel de unidad y `deps:`). Por eso se llama
  *"manual posiblemente desactualizado"*, no *"drift detectado"* — el operador
  calibra confianza desde el día uno.
- Deuda declarada: el agente `verificador-frescura` (punto 8); y la paridad
  prosa↔script de las otras dos señales de la brújula (`ley atrasada`, `deuda
  SOLID`) sigue viviendo en prosa — esta nace en el script, pero migrar aquellas
  es corrida aparte.
- El `lector-cero` NO es guardián del roster del Crisol: no corre dentro de una
  corrida ni escribe en la matriz de veredictos. Es una clase nueva —
  **verificador de registro** — y su `DOC_SIRVE` tiene fuente única en el gate de
  doc de la skill `feature`, NO en el catálogo §5 del crisol (cuya matriz es la
  corrida, no la fila feature).

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.5.0` (cache local, NO la ley).**
