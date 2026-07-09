# 0010 — Bitácora push: inyección SessionStart + observador SessionEnd (absorción ECC)

- estado: aceptado
- fecha: 2026-07-09
- decide: MLL (operador) — orden "aplica todo lo que propusiste hasta el final"
- tags de la familia al sellar: v1.30.0
- relacionado: skill bitácora (ADR 0005 — capa experiencial); ECC
  `continuous-learning-v2` (github.com/affaan-m/ECC, clon local analizado
  2026-07-09); RUN-LEDGER corrida `main — 2026-07-09 (absorción ECC lote 1)`

## Contexto

La Bitácora era **pull-only**: el agente debía acordarse de grepear el INDEX al
ver un síntoma. ECC demuestra el valor del modelo **push** (instincts inyectados
en SessionStart con umbral de confianza, cap de 6 y presupuesto de 8KB) y de la
**observación por hooks** (eventos de sesión → candidatos a patrón). Su enfoque
NO se puede copiar literal: los instincts de ECC entran al sistema con
confidence calculada por un LLM observador, sin evidencia verificable — lo que
choca de frente con la regla dura de la Bitácora ("**sin evidencia real, NO
entra**"; el catálogo no guarda teoría).

## Decisión

Se absorbe el MECANISMO (push + observación) preservando la DOCTRINA lucky:

1. **`bitacora-push.sh` (hook SessionStart del plugin).** Inyecta el top-N de
   filas **LIVE** del INDEX (síntoma → acción → ID), que ya está ordenado por
   `usos`. El equivalente lucky del confidence de ECC es el par
   `usos + validated_on` — evidencia real, no estimación de un LLM.
   - Cap `BITACORA_PUSH_MAX` (default 6, como ECC) + presupuesto duro
     `BITACORA_PUSH_MAX_CHARS` (default 2000; ECC usa 8000 para TODO su
     contexto — acá solo viaja la bitácora, alcanza con menos).
   - Solo `source=startup` (paridad con la decisión de ECC: resume/clear/
     compact no re-inyectan).
   - CANDIDATE y STALE jamás se inyectan (solo lo confirmado).
   - Off-switch: `BITACORA_PUSH=off`. FAIL-OPEN: cualquier error →
     `additionalContext` vacío, exit 0.
2. **`bitacora-observar.sh` (hook SessionEnd del plugin).** Donde ECC pone un
   LLM observador (Haiku) que escribe instincts, lucky pone **grep determinista
   de señales conocidas** (bloqueos del gate, suites rojas, fallas de
   integridad, ley diferida, falso-verde) sobre el transcript, y acumula SOLO
   `fecha · repo-basename · etiqueta · conteo` en un log local por máquina
   (rotación dura 400 líneas). `--resumen` lo agrega para el humano.
   - El log es **evidencia cruda**, NO catálogo: alimenta los contadores de
     `SENALES.md` (hiyari-hatto) a criterio del operador. La promoción a
     INDEX sigue exigiendo corrida real + endoso humano (ADR 0005 intacto).
   - Zero-leak por construcción: jamás contenido del transcript, jamás rutas
     completas.
   - Off-switch: `BITACORA_OBSERVAR=off`. FAIL-OPEN total.
3. **Cableado en `plugins/lucky/hooks/hooks.json`** (SessionStart + SessionEnd
   junto al PreToolUse existente). Por `autoUpdate: true` esto llega a TODA la
   flota → por eso ambos hooks son deterministas, con presupuesto, off-switch y
   fail-open desde el día 1.

## Lo que NO se absorbe (y por qué)

- **Confidence scoring por LLM** (0.3–0.85 por frecuencia estimada): la Bitácora
  ya tiene métrica superior — `usos` reales con `validated_on` verificable.
- **Escritura automática de instincts/entradas**: violaría "sin evidencia real,
  NO entra" y el endoso humano (documentation-theater que la regla del
  2026-07-02 mató). El observador junta señales; el humano decide.
- **`/evolve` (clusterizar → generar skills)**: la Bitácora ya tiene su válvula
  de ascenso (usos ≥ 3 → ADR / skill / regla del gate) con juicio humano;
  generar skills por plantilla determinista desde clusters es teatro de
  contenido. Se reevalúa si el volumen de entradas algún día lo amerita.

## Consecuencias

- (+) Los patrones confirmados llegan al agente ANTES del tropiezo, en toda la
  flota, por ~1-2KB de contexto.
- (+) Las señales débiles se ACUMULAN solas (antes dependían de que alguien se
  acordara de anotar el near-miss); `visto ≥ 2 → investigar` ahora tiene
  alimentación automática.
- (−) +2 hooks corriendo en cada sesión de la flota (costo: ~decenas de ms,
  mitigado por fail-open y off-switches).
- (=) Doctrina intacta: INDEX curado por humanos, consulta dirigida sigue
  siendo pull, SENALES sigue sin decidir acciones.

## Enmienda (2026-07-09) — timbre de juicio

Pregunta del operador que la disparó: *"¿qué mecanismo hay para que el humano
sepa que tiene que juzgar?"* — la acumulación era automática pero la cola de
juicio no tenía timbre (mismo defecto que ECC: sus instincts se apilan y
`/instinct-status` es manual).

**Se agrega al push la sección `⚖ JUICIO PENDIENTE`** (solo si hay algo que
juzgar; cero ruido si no):

- cuenta **señales con visto ≥ 2** en el log local del observador (líneas =
  sesiones avistadas por etiqueta — la semántica `visto: N` de SENALES.md) →
  remite a `bitacora-observar.sh --resumen`;
- cuenta **entradas CANDIDATE** del INDEX esperando endoso → LIVE o retirar;
- **instruye al agente a avisarle al humano en su primera respuesta** — el
  additionalContext lo lee el modelo, no el humano: el relevo explícito ES el
  timbre;
- va **antes** de los patrones en el bloque (sobrevive al recorte de
  presupuesto);
- **cero juicio automático**: solo conteo y aviso — quién investiga, refuta,
  promueve o retira sigue siendo el humano (invariante de este ADR intacto).

`bitacora-push.sh` copia `log_dir` de `bitacora-observar.sh` (comentario
"editar acá => editar allá") y la paridad se prueba por introspección
`--print-log-dir` en ambos hooks (patrón ADR 0008). El ítem "edad de las ideas
parkeadas" quedó fuera por alcance quirúrgico (IDEAS es por-repo, no del
plugin; se reevalúa si duele).

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v1.30.1` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.
