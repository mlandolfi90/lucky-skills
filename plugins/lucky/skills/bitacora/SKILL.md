---
name: bitacora
description: >-
  La Bitácora — catálogo de patrones experienciales "cuando ves SÍNTOMA X →
  hacé ACCIÓN Y", indexado por síntoma para sortear gaps/greps/drifts sin
  re-derivar. Disparar cuando el agente o el usuario: re-deriva algo que ya se
  resolvió, grepea sin mapa o se pierde navegando ("¿dónde vive X?"), detecta
  que doc y código divergen, ve un test en verde que igual rompió (falso-verde),
  o pregunta "¿esto ya pasó?", "¿cómo se sorteaba esto?". "/bitacora" sin
  argumentos = mostrar el INDEX. NO disparar para implementar la solución (eso es
  trabajo normal), ni para capturar ideas a futuro (eso es /idea). Consultá →
  devolvé SOLO la línea de acción → volvé al trabajo.
allowed-tools: Read, Grep, Bash, Write, Edit
---

# La Bitácora — "esto ya pasó: así se sortea"

La brújula dice **dónde estás**; el Crisol dice **si está bien hacerlo**; la
Bitácora dice **cómo se sortea lo que ya pasó**. Complementa al Crisol, no lo
reemplaza. **Principio rector: la brújula LEE, el Crisol ESCRIBE.**

**Ejes:** indexada por SÍNTOMA (no por tema) · compacta (≤1 pantalla el INDEX) ·
viva (se pudre si no se valida → reloj `validated_on`) · *compass, not
encyclopedia* (devolvé la acción, jamás volqués el archivo entero).

## Consultar (AL PLANEAR / solucionar — pull, on-demand)

1. **Cuándo:** justo ANTES de planear o resolver algo (no al arranque de la sesión). **Grep del
   INDEX por el SÍNTOMA de la tarea** — las palabras de lo que vas a tocar:
   `grep -i "<lo que vas a tocar>" INDEX.md` (relativo a esta skill). **El síntoma ES el filtro;
   no hay "dominios".** El INDEX está ordenado por `usos` — lo que más duele, arriba.
2. **Match → abrí la entrada lazy:** leé SOLO `entries/<ID>.md` que matcheó. No
   leas todas; no vuelques el INDEX completo al contexto (eso reintroduce el
   context rot que la Bitácora cura).
3. **Devolvé SOLO la línea de ACCIÓN** (+ la ANTI-ACCIÓN, que evita re-derivar el
   camino muerto). Si la entrada está `STALE` → mostrala con la bandera
   **"⚠ verificar antes de confiar"**, no como verdad vigente.
4. **Sin match → seguí normal.** La Bitácora cubre lo *conocido-recurrente*; lo
   *nuevo* es Crisol/spike. Nunca inventes una entrada para responder.

`/bitacora` sin argumentos = mostrar el INDEX tal cual.

## Capturar (Destilación — la ESCRIBE el Crisol al cerrar)

No se escriben entradas sueltas a mano: nacen al cerrar una corrida del Crisol
(§4 paso 8). **Disparador OBJETIVO** (no "cuando parezca"): la corrida tuvo un
**gap que costó >30min**, un **grep que re-derivó algo ya sabido**, o un **drift
hallado**. Entonces:

1. **Destilá UNA entrada** con `templates/entrada.md`. Una entrada = un síntoma =
   una acción. El título ES el síntoma observable, con tag `[TIPO-NNN]`.
2. **Dedup primero:** `grep` del síntoma en `INDEX.md`. Si ya existe → NO crees
   otra: incrementá `usos` y refrescá `validated_on`.
3. **`validated_on` OBLIGATORIO** (`branch · fecha · commit`). Sin él, nace STALE.
4. **Propiedad humana sobre la promoción (anti documentation-theater):** el agente
   destila con `estado: CANDIDATE`; **el humano** promueve a `LIVE` como acto
   deliberado de cierre. El LLM destila, el humano decide qué es verdad.
5. Agregá la fila al `INDEX.md` y listá la entrada en el resumen de cierre del
   Crisol (junto al Parking de IDEAS.md).

## Mantener (mecánico, no por disciplina)

- **STALE:** `bash scripts/bitacora-stale.sh` marca toda entrada con
  `validated_on` > 90 días o sin `validated_on`. Read-only: reporta, no borra.
  Candidato a correr desde el heartbeat (`crisol-pulso`) o el CI.
- **Poda por tope (~40 entradas vivas):** superado el tope, la de menor `usos` +
  más vieja se archiva con su razón (*el por-qué-se-jubiló también es
  conocimiento*: evita re-proponer lo descartado).
- **Ascenso (válvula anti-pantano):** patrón con `usos ≥ 3` o explicado en >2
  RETROs → asciende y se reemplaza por un puntero: → **ADR** (decisión), →
  **skill** (proceso que el agente ejecuta), → **regla del gate** (invariante
  determinista). La Bitácora NO acumula: recicla hacia arriba. El éxito se mide en
  entradas RETIRADAS, no acumuladas.

## Reglas duras

- **Indexá por SÍNTOMA observable, no por tema.** Si no podés escribir el síntoma
  como algo que un agente OBSERVA literalmente, no es un patrón → va a `/idea`.
- **Cero secretos (invariante #1):** nombres de variable, nunca valores; rutas
  relativas, nunca absolutas; sin IPs/dominios/tokens. Lo cubre `leak-scan.sh`.
- **Máx ~20-35 líneas por entrada.** Más que eso = es un ADR o un skill, movelo.
- **El gate NO bloquea por la Bitácora** (sería anti-jidoka): el Crisol avisa, no
  exige. Es `.md` → exento del gate; la dureza la dan el origen (Crisol) + STALE.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v1.16.1` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags`), seguir la del repo e informar al humano.
