---
id: 2026-07-16-equipo-doc
schema: concejo/1
tipo: concejo
estado: CERRADO
creado: 2026-07-16
pregunta: >-
  ¿Resiste el diseño del equipo de documentación (manualizador existente +
  lector-cero que gatea VIVA + verificador-frescura + señal de drift en
  brújula)?
angulos: [proceso, costo, frescura, ley, abuso]
sintesis: >-
  APRUEBA_CON_CAMBIOS unánime (5/5) — el núcleo (autor + juez fresco que
  gatea + señal no-normativa) resiste; caen tres pilares del boceto:
  ejecución real del tutorial, mecanismo de drift por fechas, y el
  verificador-frescura como agente v1 (diferido por YAGNI).
refs: [adr:0018, adr:0019, adr:0020]
---

# Concejo — equipo de documentación (lector-cero + frescura)

Panel de 5 jueces frescos (workflow, un lente c/u, leyendo el estado real del
repo), con orden de romper el diseño. Los 5 dictaminaron APRUEBA_CON_CAMBIOS.
Este archivo es la síntesis del orquestador; los veredictos crudos vivieron en
el temp de sesión (por eso esta fila existe — ADR 0019 §1).

## Diseño bajo juicio (boceto endosado en chat)

1 autor (manualizador, "no se toca") + 2 verificadores frescos sin Write/Edit:
lector-cero (juzga comprensibilidad ejecutando el tutorial a ciegas; PUEDE
frenar el pase a VIVA; bucle autor↔lector máx. 2 rondas, fail-closed a
EN-CONSTRUCCION) y verificador-frescura (juzga drift manual-vs-código; jamás
bloquea). Drift post-estreno: señal en brújula comparando fechas de commit
código-vs-doc.

## Enmiendas (lo que el concejo cambió)

### E1 — El lector-cero NO ejecuta: walkthrough estático (4/5 jueces)

"Ejecutar como usuario real" era: mutación vía Bash desde un juez
"read-only", TARGET indefinido, superficie de prompt-injection (el manual es
contenido no confiable), y FALLAs falsas por limitación ambiental (features
UI: no hay app corriendo ni manos). Queda: juzga por LECTURA — cada paso con
comando exacto, precondición y resultado observable; ningún concepto usado
antes de definirse; cero placeholders sin resolver. Tools: Read/Grep/Glob
(sin Bash, sin Write/Edit). Ejecución real = SOLO opt-in del operador con
TARGET declarado (disciplina REGLA 0). Paso no verificable con sus tools →
se evalúa por inspección, no es FALLA automático.

### E2 — Ceguera calibrada, no total (anti-Goodhart)

Ciego al código y a la conversación, pero recibe el cuerpo `funcionalidad`
de la fila feature (el contrato observable ≤15 líneas). La prueba: lograr
CADA comportamiento del contrato usando únicamente el manual — mide
comprensión + cobertura y mata el incentivo a sub-documentar para aprobar.
Tropiezos con severidad BLOQUEA|COSMETICO: solo BLOQUEA justifica FALLA;
FALLA sin tropiezo accionable = veredicto inválido (re-spawn único). El
juicio se limita a {PIEZAS_BAJO_JUICIO} (las que el manualizador reportó
escritas); tropiezos en piezas ajenas = observación no bloqueante.

### E3 — El veredicto deja huella mecánica (el gate deja de ser prosa)

Columna `doc_veredicto:` en la fila feature (PENDIENTE|PASA|FALLA + ronda +
ref); VIVA exige PASA y registros-lint lo valida (además de que `doc:`
apunte a archivo existente — hoy ni eso se lintea). Cada ronda se registra
en `intentos:`. El desempate tras 2 FALLAs se CONVOCA como decisión (ADR
0019 §2) → aparece en el TABLERO. El manualizador deja de escribir `doc:`:
esa columna la escribe el flujo /feature recién tras PASA. Un FALLA que
muere en el chat era exactamente el dolor que ADR 0019 ya había saldado.

### E4 — Drift por FECHAS nace muerto → cursor por SHA (3/5, mismo escenario)

Condena doble del mecanismo por fechas: (a) forjar-release.sh re-estampa el
sello en TODO el repo en cada release → 100% de falsos positivos a la
primera forja → señal ignorada = señal muerta; (b) un typo-fix en el doc
pone su fecha por encima del código y APAGA la señal con drift real (falso
negativo fatal: corregir una coma certifica exactitud técnica). Queda:
sidecar `docs/manual/_cobertura.yaml` (dueño único: manualizador; la
narrativa sigue sin frontmatter) con `{doc, cubre: [globs a nivel de skill],
deps: [paths], verificado_en: <sha>}`. Señal = `git rev-list --count
<sha>..HEAD -- <globs>` con filtro de commits de mantenimiento (prefijos
declarados), implementada DENTRO de brujula.sh — script, no prosa: cero
temperatura, "salida tal cual" real. El cursor solo se mueve por acto
explícito (el manualizador al escribir; ack por script tras dictamen "sin
drift") — jamás por mtime. Lint valida el sidecar (pieza sin entrada, glob
muerto, sha inválido = error). Fail-closed hablado: "manual sin mapa: N
piezas" — nunca silencio que se lea como salud.

### E5 — verificador-frescura DIFERIDO (YAGNI)

v1 construye UN solo agente nuevo: lector-cero (el único que gatea — ahí la
separación autor/juez paga). El dictamen on-demand de drift lo da el
manualizador en "modo dictamen" (solo reporta desvíos, no escribe); sus
hallazgos confirmados se archivan como fila `diagnostico` ABIERTO (tabla
existente) para no morir en el chat. El agente dedicado se construye recién
si la telemetría muestra corridas de dictamen desperdiciadas — medible, no
por sensación. Queda como deuda declarada.

### E6 — El manualizador SÍ se toca, por la vía legal (supersede ADR 0018 §4)

"No se toca" era incompatible con el propio bucle. Supersede con: gatillo
(c) ronda de corrección (recibe {TROPIEZOS} verbatim como dato — el mandato
se LEE, no se redacta por temperatura); escribe/actualiza `_cobertura.yaml`
y bumpea su cursor al escribir; deja de escribir `doc:`; modo dictamen (E5).

### E7 — Dónde vive la ley (para que sea ley y no costumbre)

ADR 0021 + el bucle escrito en la skill feature (regla dura 2 ampliada:
existir Y aprobar; el detalle puede ir como rama del gate). Lector-cero =
agente canónico fila `agente/1` con `dictamina: [DOC_SIRVE]` — el enunciado
fuente-única vive en el gate de feature, NO en el catálogo §5 del crisol (su
matriz es la fila feature, no la corrida). Formato de matriz espejo guardián:
`DOC_SIRVE · PASA|FALLA · lector-cero · <tropiezos B/C>`. La fila feature
declara `audiencia: user|dev`: con dev el gate se satisface con doc en
docs/sistema/ y el juicio corre en modo comprensión (N preguntas
respondibles solo con el doc) — jamás FALLA estructural por ausencia de un
tutorial que la feature no debe tener (acá la mayoría de las features son
internas: sin esto, gate muerto por desempate perpetuo). `feature` suma
`Agent` a sus allowed-tools (hoy no puede spawnear ni al manualizador).

### E8 — ZERO_LEAK en el gate de doc

docs/manual/ es visibilidad producto (viaja a la app) y la transición a VIVA
puede ocurrir fuera de una corrida Crisol → el leak-verifier no la barre.
Queda: `scripts/leak-scan.sh` corre sobre las piezas escritas ANTES de
admitir PASA (exit code real, fail-closed), y los prompts canónicos nuevos
llevan la cláusula del leak-verifier: citar paso/archivo:línea SIN
transcribir valores.

## Injertos adoptados

- Telemetría fail-open (uso.jsonl): rondas, PASA/FALLA, desempates — la
  recalibración del gate se decide con evidencia; si los desempates superan
  a los PASA, el prompt del lector-cero pasa a EN_DUDA.
- TABLERO: los juicios pendientes de doc aparecen vía las filas (decisión
  convocable + diagnostico) — sin sección nueva ad-hoc.
- NO proyectar frescura al TABLERO: depende del estado de git al momento de
  la consulta y rompería la idempotencia de proyectar.py (M6). La frescura
  pertenece a la brújula (snapshot), no al tablero (proyección). Escrito acá
  para que nadie lo "mejore" después.
- El bucle autor↔lector corre FUERA del techo de 3 iteraciones del Crisol:
  es acto de /feature, no del cierre de corrida — un FALLA de doc jamás
  quema iteraciones de código ni bloquea el commit de una corrida PASS.
- Al PASA, el lector-cero devuelve 1 línea por pieza ("qué logré hacer con
  ella") — spot-check humano barato.
- Refuerzo independiente y barato, útil ya: lint de `doc:` existente para
  toda feature VIVA.

## Riesgos residuales (declarados, no resueltos)

- Drift semántico transitivo: comportamiento que cambia sin tocar los paths
  cubiertos no se detecta — límite inherente a toda señal por paths.
  Mitigado por globs a nivel skill + `deps:` + dictamen on-demand. La señal
  se llama "manual posiblemente desactualizado", no "drift detectado".
- Tasa real de FALLAs falsas del lector-cero: desconocida hasta cosechar
  telemetría. La regla de recalibración existe desde el día uno.
- El gate sigue puenteable editando la fila a mano; el lint reduce la
  ventana (VIVA sin PASA = error de forja), no la elimina.

## Estado

Veredicto listo para endoso del operador. Si endosa: corrida Crisol tier
completo que deposite ADR 0021 + supersede del manualizador + agente
lector-cero + sidecar/señal/lint + skill feature ampliada.
