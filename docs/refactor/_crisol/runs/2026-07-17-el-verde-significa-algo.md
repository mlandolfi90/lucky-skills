---
id: 2026-07-17-el-verde-significa-algo
schema: corrida/1
tipo: corrida
estado: ACTIVE
creado: 2026-07-17
branch: main
titulo: "El verde significa algo — CI en runner ajeno + RED_GREEN"
tier: "completo (ID nuevo en el catálogo §5 = contrato; >1 archivo; establece patrón: el primer verificador que NO es un LLM)"
target: "pc-local (donde el líder y el roster verifican). NOTA de bootstrap: esta corrida CONSTRUYE el runner ajeno, así que su propia evidencia de CI se observa en GitHub Actions tras el push de respaldo — el runner no existe hasta que se pushea."
model: "fable (uniforme)"
ley: "v2.5.0 (verificada — git ls-remote: máximo remoto == sello local)"
iteraciones: "3/3 (plan APPROVE a la 1ª por el PIN · iter 2 = FAIL de scope por creep de jurisdicción · iter 2b = FAIL del líder por auditar el árbol y no la entrega)"
runState: closing
cierre: "2026-07-17 · commit de cierre + forja v2.6.0 (sella las 2 corridas terminales) + tag anotado + GitHub Release"
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: líder, evidencia: "pc-local (la forja; directiva explícita del operador). Bootstrap declarado: esta corrida CONSTRUYE el runner ajeno"}
  - {regla: MODEL, veredicto: PASS, quien: líder, evidencia: "fable (uniforme)"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: steward, evidencia: "shift-left: A = 1 archivo NUEVO (.github/ no existía), 0 editados · B = fila nueva (quality-auditor-2) + 2 líneas de transición + agregado puro al catálogo §5"}
  - {regla: ATOMICIDAD, veredicto: PASS, quien: steward, evidencia: "shift-left: ci.yml ~190L · quality-auditor-2 ~75L, ambos < T=400. SKILL.md 592→613 ya estaba citado: resuelto POR NOMBRE (tronco de ley, larga-legítima)"}
  - {regla: COSTURA, veredicto: PASS, quien: steward, evidencia: "shift-left: cero generalidad especulativa — sin matriz de OS, sin pull_request, sin redgreen-verifier nuevo. El único punto de extensión es el glob (PIN 1, con evidencia)"}
  - {regla: CASOS_LEGALES, veredicto: PASS, quien: steward, evidencia: "shift-left: A = AGREGA sin caso legal · B = (c) contrato pagado con ADR 0022 + transición de estado (única mutación legal de fila terminal), precedente manualizador-2"}
  - {regla: CREDITO, veredicto: PASS, quien: scope-verifier, evidencia: "ADR 0022 sellado, frontmatter válido, refleja lo implementado 3/3, refs recíprocas ambas direcciones; el patrón normativo NO vive solo en prosa: ID en §5 + enunciado en §2 + hogar en dictamina:. Supersede legal (ADR 0018 §4)"}
  - {regla: REGLA0, veredicto: PASS, quien: quality-auditor-2, evidencia: "13/13 suites corridas por él en pc-local (TARGET declarado) + lint con EXACTAMENTE el hallazgo esperado (justificado en forjar-release.sh:395-402) + proyectar --check rc=0 + leak-scan rc=0. Su ESTRENO: verificó la corrida que lo creó"}
  - {regla: TEST_COVERAGE, veredicto: PASS, quien: quality-auditor-2, evidencia: "13 runners: bitacora(4) cargar(1) crisol(6) ley(1) management(1) — no es NONE"}
  - {regla: RED_GREEN, veredicto: "N/A", quien: quality-auditor-2, evidencia: "el diff no crea ni modifica tests (1 .yml + 3 .md). Citación VACÍA verificada por él con git diff --name-only filtrado: 0 matches. N/A legítimo por la cláusula del propio enunciado; NO forzado a PASS"}
  - {regla: ZERO_LEAK, veredicto: PASS, quien: leak-verifier, evidencia: "leak-scan rc=0 + barrido propio calibrado contra control positivo (mordió 5/5 shapes reales, calló ante <REDACTED> y placeholders). ci.yml: permissions contents:read, cero secrets, cero pull_request_target, checkout pineado a SHA"}
  - {regla: INDEPENDENCIA, veredicto: PASS, quien: líder, evidencia: "4 verificadores FRESCOS + 2 Stewards frescos. El roster cazó al LÍDER dos veces: el creep de jurisdicción y el auditar-el-árbol-y-no-la-entrega"}
  - {regla: SCOPE_CREEP, veredicto: PASS, quien: scope-verifier, evidencia: "iter 3: 8 archivos staged mapeados 1:1 al Alcance; remedio verificado EN EL ÍNDICE (viñeta DRIFT-001 fuera, entera, sin jirón); 3 chequeos nuevos con ojo fresco, limpios. Los 2 [DRIFT-001] que sobreviven están en ci.yml como justificación de diseño del carril A, no como regla inyectada en un prompt"}
  - {regla: PARKING, veredicto: PASS, quien: scope-verifier, evidencia: "el NEXT sacado por el Steward tiene captura VIVA en el índice, con la doctrina adentro y destinatario 'decisión del operador'. TEST_COVERAGE: NONE parkeado en ADR 0022 §3"}
  - {regla: LISKOV, veredicto: PASS, quien: design-verifier, evidencia: "quality-auditor-2 implementa agente/1 y sustituye al viejo: mismo shape, mismos placeholders, dictamina: es SUPERSET → preserva postcondiciones. El llamador no se entera: los 4 de-ruteos migraron, cero refs vivas al nombre viejo"}
  - {regla: INTERFACE_SEGREGATION, veredicto: PASS, quien: design-verifier, evidencia: "la fila RED_GREEN en §5 no fuerza a ningún guardián a depender de lo que no usa: la segregación por cliente la da el dictamina: de cada agente — solo el -2 la lista"}
  - {regla: PIN_TOTAL, veredicto: PASS, quien: design-verifier, evidencia: "checkout pineado a COMMIT en las 3 apariciones, RE-RESUELTO por él (git ls-remote → 9c091bb…, sin línea ^{} = tag liviano) + pyyaml==6.0.1 exacto, versión que declara el propio registros-lint.py"}
  - {regla: TECHO_ITER, veredicto: PASS, quien: líder, evidencia: "convergió en 3/3, la última. Iter 1 la ganó el PIN; iter 2 la perdió el creep de jurisdicción; iter 2b la perdió el líder"}
  - {regla: CIERRE_TRAS_PASS, veredicto: PASS, quien: líder, evidencia: "commit de cierre tras PASS de los 4 verificadores frescos + el dictamen del Steward R2 aplicado y re-verificado"}
  - {regla: MIGRATION, veredicto: "N/A", quien: gate, evidencia: "sin DDL"}
  - {regla: CONFORMIDAD, veredicto: "N/A", quien: líder, evidencia: "tooling sin capas"}
  - {regla: TARGET_ENV, veredicto: "N/A", quien: líder, evidencia: "pc-local sin @env"}
  - {regla: RESPONSIVE, veredicto: "N/A", quien: líder, evidencia: "sin UI"}
  - {regla: FUENTE_VERDAD, veredicto: "N/A", quien: líder, evidencia: "no toca testing/prod"}
  - {regla: SELLOS, veredicto: PASS, quien: forja, evidencia: "re-sello uniforme a v2.6.0 por forjar-release.sh; pre-flight del universo SEALED"}
  - {regla: FORJA, veredicto: PASS, quien: forja, evidencia: "sellos+registry+sellado de las 2 corridas terminales en UNA pasada — nada a mano"}
  - {regla: TAG_GATE, veredicto: PASS, quien: líder, evidencia: "v2.6.0 nace tras esta corrida CLOSED con PASS"}
refs: [adr:0022, concejo:2026-07-16-equipo-doc, adr:0017, adr:0016]
---
- ORIGEN: el operador mandó analizar 4 repos ajenos (`obra/superpowers`,
  `thedotmack/claude-mem`, `awesome-skills/code-review-skill`, `garrytan/gstack`).
  De 21 borradores cosechados endosó DOS: CI y RED_GREEN ("1+2"). El resto quedó
  descartado o parkeado por él.
  **Los dos saldan el mismo dolor**, y por eso van juntos en una corrida y no en
  dos: hoy la ley verifica que el verde EXISTA, nunca que SIGNIFIQUE algo.
- EVIDENCIA que lo justifica (no es moda — es la propia bitácora del repo):
  - `bitacora/entries/DRIFT-007` documenta que el mismo hook da verde en Windows
    y muere en Linux (`command not found`, exit 127) o falla EN SILENCIO por el
    stub de Microsoft Store (exit 49). **Mordió DOS veces** (`validated_on`: 1ª
    `faa405c` con repro Linux real; 2ª el paso 6b de `/ley`, que usaba
    `command -v` y falló callado en una corrida real).
    Su línea de PREVENCIÓN, escrita por el propio repo: *"la corrida que lo toque
    corre la suite en Linux fiel (REGLA 0 multi-OS)"* — **y no hay con qué**.
  - `crisol/SKILL.md:57-61` (REGLA 0) exige que el Verificador corra los tests
    ÉL MISMO **en el TARGET**, "jamás en la PC local". Hoy eso lo hace cumplir un
    rol-LLM sobre sí mismo, en la máquina del operador. Un runner Linux ajeno
    **es** el target que la regla pide y que nadie provee.
  - `crisol/SKILL.md:65-68`: `TEST_COVERAGE: NONE` puede emitir `PASS` (solo
    bloquea el tag estable). Es un falso-verde con nombre propio.
  - `registros.yaml:8` prohíbe editar proyecciones a mano **con una frase**. Sin
    CI, "jamás editar a mano" es un pedido.
  - Hallazgo de hoy: `leak-scan.sh:61` tenía la rama Windows muerta vaya a saber
    desde cuándo (saldado por `microfix:2026-07-16-leak-scan-ruta-windows`). El
    scanner solo corre en la forja; con CI corre en cada push.
- Alcance (CERRADO):
  1. **CI en runner ajeno** — `.github/workflows/` que corra en `ubuntu-latest`:
     las suites de `plugins/lucky/skills/*/tests/`, `registros-lint.py`,
     `leak-scan.sh` y `proyectar.py --check` (gate de drift de proyecciones).
  2. **`RED_GREEN`** — ID nuevo en el catálogo §5 + enunciado en §2 + su hogar en
     el `dictamina:` del guardián que corresponda: todo test que sostiene un PASS
     fue VISTO fallar antes; todo test de regresión probó su rojo por revert.
  3. **El falso-verde de `TEST_COVERAGE: NONE`** — revisar que `NONE` no siga
     emitiendo `PASS` sin más.
  4. **ADR 0022** — la decisión y su porqué.
  FUERA DE ALCANCE (el operador descartó explícitamente, hoy): multi-harness
  (verificado: superpowers porta 10 harnesses con UN solo evento `sessionStart`
  y CERO bloqueo — la portabilidad es consecuencia de no tener nada que perder);
  pressure-testing de la prosa (caro, queda para su corrida); gate de mtime
  (necesita diseño); doble voz cross-modelo (no hay 2º proveedor hoy).
- SELLO PENDIENTE (esperado, no es drift): el lint reporta 1 hallazgo —
  `corrida:2026-07-16-leak-scan-puente` CLOSED sin sello. Es la ventana normal
  entre cierre y forja: el sellador es el paso 4c de `forjar-release.sh`. La forja
  de cierre de ESTA corrida lo salda. Gate: lint POST-FORJA == 0.
- ITER 1 — Steward: **APPROVE ×2**. Convergió a la primera. La FASE PIN aplicada
  ANTES de planificar (lección del RETRO de `corrida:2026-07-16-equipo-doc-v1`)
  hizo exactamente lo que prometía: aquella corrida gastó 2 de 3 iteraciones
  descubriendo un ciclo de contratos con el primer REJECT; ésta no tuvo ninguno.
  El Steward verificó los contratos por REFERENCIA, no por path — y confirmó cero
  disputa con evidencia del manifiesto (la tabla `agente` no tiene `proyecciones:`
  ni `sellado: true` → las filas de B no driftean el `--check` que corre A).
- CONDICIÓN VINCULANTE del Steward al carril A (y es la mejor línea del día): el
  plan traía una instrucción para que el líder dejara `.github/` FUERA de los
  WIP-commits "si se prefiere que el primerísimo run sea verde". El Steward la
  eliminó: *"retener el CI de un WIP-push para que la primera foto salga verde es
  optimizar la ÓPTICA de la señal, en la corrida que vino a matar eso"* — y además
  contradice el propósito del WIP-commit (respaldo, no vidriera). `.github/` entra
  al WIP y el rojo del sello es verdadero.
- HALLAZGOS del reconocimiento que justifican la corrida (los desenterró el
  archaeologist de A, midiendo en vez de asumir):
  1. **`test-paridad.sh` habría dado VERDE SIN CORRER NADA en el runner.** Su
     línea `[ -f "$GATE" ] || { echo "SKIP..."; exit 0; }` apunta a
     `$HOME/.claude/hooks/crisol_gate.py`, que en una máquina limpia NO existe.
     El falso-verde que esta corrida vino a matar, esperándonos en el paso 1. Se
     neutraliza desde el `env:` del workflow (`CRISOL_GATE_OVERRIDE` a la copia
     versionada), sin editar el `.sh`.
  2. **El clon shallow dormiría un check.** `registros-lint.py` necesita historia
     (`git cat-file` / `merge-base`) para el cursor `verificado_en`; hoy ese
     chequeo duerme porque no existe `docs/manual/`, así que `fetch-depth: 1`
     pasaría verde HOY y despertaría rojo el día que nazca el manual. [DRIFT-001]
     literal. Por eso `fetch-depth: 0` solo en el job que lo necesita.
  3. Las suites resuelven el intérprete con `command -v python || command -v
     python3` — el anti-patrón exacto de [DRIFT-007]. En el runner se ataca con un
     venv que provee AMBOS nombres en un solo prefijo, sin tocar los `.sh`.
- ITER 2 — roster fresco: quality-auditor-2 PASS (su ESTRENO: verificó la corrida
  que lo creó) · leak PASS · design PASS · **scope FAIL**. El scope cazó *creep de
  JURISDICCIÓN*: el bloque "DISCIPLINA DE EXIT CODE" del prompt canónico nuevo
  traía TRES viñetas y solo el `<PY>` (DRIFT-007) tenía pasaporte; las otras dos
  se colaron por esa puerta. Su argumento: *"la coartada temática no alcanza —
  «el verde significa algo» es el TEMA de la corrida, no su Alcance, y el Alcance
  dice CERRADO"*. Fue honesto en las dos direcciones: declaró el atenuante
  (restatean prevención ya vinculante, archivo nuevo, sin ID ni celda; riesgo
  bajo) y ofreció el remedio en vez de solo condenar.
  **Steward R2 dictaminó por viñeta**: RATIFICA `FALSO-VERDE-004` (instrumental:
  el enunciado aprobado exige *"exit codes REALES"*, y los dos defectos son el
  MISMO — el exit que decide no es el del sujeto: 127/49 del shell vs el de
  `tail`; sin ella el lado B del A/B lee `exit 0` y emitiría FAIL contra un test
  que SÍ probaba su rojo). **SACA `DRIFT-001`**: no es instrumental (el A/B cierra
  sin ella), su hogar es REGLA 0, y su promoción "a regla del Verificador" es un
  **NEXT ABIERTO** (`DRIFT-001.md:22`) que esta corrida estaría respondiendo por
  efecto colateral, sin ADR y sin el operador — precedente del movimiento
  correcto: `TEST_COVERAGE: NONE` (ADR 0022 §3 + PIN 3). Su cierre, que vale como
  doctrina: *"si «restatea una prevención ya vinculante» bastara como pasaporte,
  toda entrada de la bitácora sería injertable en todo prompt canónico de toda
  corrida cuyo TEMA roce — y «Alcance (CERRADO)» dejaría de significar algo. En
  una corrida titulada «el verde significa algo», dejar que CERRADO no signifique
  nada es la ironía que no vamos a firmar"*. Aplicado: 3 líneas borradas + NEXT
  parkeado en `docs/IDEAS.md` con el argumento adentro.
- ITER 2b — **el líder auditó su árbol, no su entrega** (error del líder, sin
  atenuante). Tras aplicar la supresión, el scope-verifier FRESCO volvió a dar
  FAIL: el borrado y el parking existían en el working tree y **nunca se
  stagearon**. Contra `--cached` —que es lo que un commit shippea— la viñeta
  seguía y el parking no estaba. Commitear así habría shippeado el creep Y
  perdido la captura: el peor de los dos mundos, en la corrida que vino a matar
  los falsos-verdes. Es la MISMA clase de defecto que el diff bajo juicio
  combate: verificar el sujeto equivocado. Saldado con `git add` + verificación
  contra el ÍNDICE (`git show :<archivo>`), no contra el disco.
  Se aplicó además su observación no-bloqueante: `adr:0022` suma
  `bitacora:FALSO-VERDE-004` a sus `refs` — quedó citada normativamente en el
  prompt canónico por la ratificación del Steward, y CREDITO exige que el ADR
  refleje lo implementado. La fila `decision` en `ACEPTADA` NO es terminal
  (`registros.yaml`: terminales = [RECHAZADA, SUPERSEDIDA]) → la corrección en el
  lugar es legal.
- MIGRATION_STRATEGY: N/A (sin DDL)
- RETRO (blameless): la corrida salió BIEN por lo que aprendió de la anterior y
  MAL por lo mismo que ataca — y las dos mitades enseñan.
  **Lo que funcionó:** la FASE PIN antes de planificar (lección del RETRO de
  `corrida:2026-07-16-equipo-doc-v1`) hizo converger el plan a la PRIMERA. Aquella
  gastó 2 de 3 iteraciones en un ciclo de contratos y murió ESCALATED; ésta no
  tuvo un solo REJECT de plan. Una lección de RETRO se pagó sola en 24 horas: eso
  es lo que hace que escribir RETROs valga.
  **Lo que falló, dos veces, y las dos son la MISMA falla:** verificar el sujeto
  equivocado. (1) El prompt canónico nuevo se llevó puestas dos prevenciones de
  bitácora por la puerta que el Steward abrió para UNA — creep de jurisdicción,
  con la coartada del TEMA. (2) El LÍDER borró la viñeta y escribió el parking en
  su árbol, verificó con grep sobre el DISCO, y reportó "hecho": nunca stageó.
  Contra `--cached` —lo que un commit shippea— el creep seguía y la captura no
  existía. Es exactamente el defecto que el diff bajo juicio combate: el `| tail`
  que devuelve su propio exit code en vez del del test; el `command -v` que
  bendice un stub que no corre; el líder que audita su árbol y no su entrega.
  Tres capas distintas, un solo error.
  **Por qué se cazó:** porque el verificador es FRESCO y no le cree al líder. Un
  roster que fuera el mismo que hizo el trabajo habría dado verde a las dos.
  **Lección con nombre, para la bitácora:** *verificá el ARTEFACTO QUE VIAJA, no
  el que tenés a mano* — el índice y no el disco, el exit del sujeto y no el del
  formateador, el intérprete que CORRE y no el que está en PATH. Candidata a
  entrada (síntoma observable: "el verificador reporta que la remediación no está,
  y al mirar el árbol SÍ está"), y candidata a ascenso: el CI que nace hoy mata la
  variante del disco-vs-índice sin pedirle disciplina a nadie.
