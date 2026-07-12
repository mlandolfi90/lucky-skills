# 0005 — La Bitácora: Capa 4 experiencial indexada por síntoma (complementa al Crisol)

- estado: aceptado
- fecha: 2026-06-28
- decide: MLL (operador) vía Steward del Crisol
- tags de la familia al sellar: ~v1.15.0 (skill `bitacora` nace bajo la ley v1.15.0)
- relacionado: ADR 0001 (loader `cargar`); `brujula/SKILL.md` §Fuentes (5ta fuente "Bitácora");
  `crisol/SKILL.md` §4 paso 8 (sub-paso "Destilación") · §Parking (IDEAS.md); `idea/SKILL.md`
  (parking hermano); `crisol/templates/run-ledger.md` (campo `BITACORA:`)

## Contexto

El Crisol responde **"¿está bien hacer este cambio?"** (jidoka, veredicto binario). La brújula
responde **"¿dónde estoy parado?"** (estado real). Ninguno responde la tercera pregunta que más
fricción genera sesión a sesión con agentes: **"esto ya pasó antes — ¿cómo se sortea?"**. El
operador la nombró como *sortear más rápido gaps, greps y drifts*:

- **GAP** — hueco de spec/conocimiento que aparece a mitad de tarea.
- **GREP** — re-derivar lo ya sabido, navegación ciega del codebase.
- **DRIFT** — divergencia docs↔código, config/arquitectura/contexto del agente.

Una investigación (15 investigadores + concejo de 10) confirmó que el artefacto **ya existe en la
industria, fragmentado**: *Runbook* (SRE: "cuando pasa X → hacé Y"), *Playbook*, *Postmortem/
Lessons-Learned DB*, *Pattern Language* (Contexto→Problema→Solución→Consecuencias), y el estándar
abierto **Agent Skills / Atomic Knowledge Unit** (Anthropic, dic-2025) — que es justamente lo que
esta familia ya implementa con sus `skills/`. El dolor tiene nombre industrial: **context rot** y
**agent/architectural drift**. Lo que NINGÚN precedente unifica es un catálogo **indexado por
SÍNTOMA OBSERVABLE**, **con fecha de validez que lo delate cuando miente**, **alimentado desde las
propias corridas del Crisol**.

El hueco no está en *capturar* (los `RETRO:` del RUN-LEDGER ya son postmortems blameless de facto):
está en **promover + indexar por síntoma + expirar**. Hoy el conocimiento experiencial vive mezclado
en RETROs (efímeros, por branch) e IDEAS.md (parking volátil) — ninguno es consultable por síntoma
en el momento del dolor.

## Decisión

> **Revisión 2026-06-28 (MLL):** el punto 1 original especificaba *push* (la brújula surfaceaba
> 1-3 entradas al anclar). Se corrige a **pull on-demand**: la brújula SEÑALA que la Capa 4 existe
> (puntero barato), y el Planificador del Crisol la consulta **por SÍNTOMA al planear**. Razón:
> alinear con la divulgación progresiva de las skills y no quemar ventana de contexto pre-cargando
> al arranque (cuando aún no se conoce el síntoma y el match es peor).

Nace la **Capa 4 — Bitácora**: una skill `bitacora` cuyo **consumo (vía brújula) es read-only** y
cuya **escritura (la destilación) la dispara el Crisol** al cerrar, que cataloga patrones
experienciales atómicos, indexados por síntoma, y los hace consultables por humano **y por agente**. NO es un manual
nuevo escrito a mano: es un **ciclo colgado del Crisol que ya corre**.

1. **Principio rector (separación de poderes, calcado de la brújula): la brújula LEE, el Crisol
   ESCRIBE.** La consulta es **pull / on-demand**: el agente, en el **Paso del Planificador** (antes
   de planear/solucionar), grepea la bitácora por el **síntoma de la tarea** y trae SOLO el match
   (línea de acción). La brújula solo **SEÑALA** que la bitácora existe (puntero liviano), **no carga
   contenido al arranque** — alineado con la divulgación progresiva de las skills y con la economía
   de la ventana de contexto (pre-cargar al inicio quema tokens y matchea mal, cuando aún no se sabe
   el síntoma). El Verificador del Crisol, al cerrar, destila UNA entrada si la corrida tuvo dolor real.

2. **Unidad atómica = entrada por SÍNTOMA.** El título ES el síntoma observable, con tag para
   Ctrl-F (`[GAP-001]`, `[DRIFT-003]`). Campos: tipo, síntoma, causa-raíz (1 línea), acción
   (≤7 pasos), anti-acción (el camino muerto, evita re-derivar), prevención, `validated_on`
   (branch·fecha·commit — OBLIGATORIO), `stale_si`, origen, usos, REFS, NEXT, estado. Plantilla:
   `skills/bitacora/templates/entrada.md`. Máx ~20-35 líneas: si necesita más, es un ADR
   (decisión) o un skill (proceso), no una entrada.

3. **Taxonomía mínima centrada en el dolor:** `GAP` · `GREP` · `DRIFT` · `FALSO-VERDE`. La cuarta
   clase es el failure-mode dominante de esta familia según sus propios RETROs ("el comentario dice
   OBLIGATORIA pero el código hace condicional"; "el test miente verde") — el más peligroso porque
   *pasa el Verificador*. Cada tipo mapea a una postura Cynefin (GAP→complejo/spike; GREP→
   complicado/mapa; DRIFT→caótico/estabilizar).

4. **Índice grep-able por síntoma (`INDEX.md`), ≤1 pantalla.** Se grepea **on-demand al planear** (la 5ta fuente de la brújula solo lo SEÑALA / cuenta sus filas, no lo carga).
   Ordenado por `usos` (lo que más duele, arriba). El agente matchea lo que OBSERVA contra la
   columna "síntoma" — no re-deriva una taxonomía abstracta. Indexar por síntoma, NO por tema, es
   el diferencial: sin eso el catálogo existe pero no se consulta en el momento del dolor.

5. **Anti-pudrición mecánico (la disciplina humana siempre falla en dev-solo):**
   `scripts/bitacora-stale.sh` marca STALE toda entrada con `validated_on` más vieja que el umbral
   (default 90 días) o sin `validated_on` (nace STALE). STALE **no se borra: se degrada
   visiblemente** (al consultarla on-demand, el agente la muestra con bandera "⚠ verificar antes de confiar"). Un runbook que
   miente causa el incidente que pretendía evitar — por eso el reloj de validez es innegociable.

6. **Regla de ASCENSO (válvula anti-pantano).** Una entrada asciende y se reemplaza por un puntero
   cuando: → **ADR** si es una decisión arquitectónica; → **skill** si es un proceso repetible que
   el agente *ejecuta*; → **regla del gate** si es un invariante verificable deterministamente. El
   playbook NO acumula: recicla hacia arriba. Disparador: un patrón explicado en >2 RETROs distintos.

## Frontera y semántica (innegociable)

- **El gate NO bloquea por la Bitácora.** El Crisol gana un sub-paso "Destilación" (captura) y una
  nota suave, NO una regla dura de la matriz §5. Meter el playbook como obligatorio en
  `crisol_gate.py` pelearía con el propio jidoka: el gate frena *defectos de código*, no *ausencia
  de lecciones*. Bloquear el cierre por docs mata la captura (el dev-solo bajo presión saltea). Por
  eso esta corrida **NO agrega un ID a la matriz canónica** ni toca los guardianes.

- **Cuatro capas, cuatro vidas útiles, cero solapamiento** (separarlas ES el trabajo):

  | Artefacto | Vida útil | Pregunta que responde |
  |---|---|---|
  | **ADR** (`docs/decisions/`) | permanente, inmutable | ¿Por qué se decidió esto? (una vez) |
  | **RUN-LEDGER entry** | efímera, por branch | ¿Qué pasa en este branch ahora? |
  | **Bitácora** (Capa 4) | semi-estable, cross-branch | ¿Cuándo pasa X recurrente, cómo se sortea? |
  | **IDEAS.md** | volátil, parking | Feature/mejora sin destilar |

  Ante la duda bitácora-vs-ADR: *¿es una decisión o una receta?* Receta → bitácora.

- **Cross-repo por tag, no por copy-paste.** La Bitácora viaja con la familia `lucky-skills` (la
  Ley viva, §6) a los ~21 repos. Es un catálogo experiencial compartido; el agente lo consulta
  **por síntoma, on-demand al planear** (la 5ta fuente de la brújula solo lo señala) — nunca se
  vuelca entero, eso reintroduciría el context rot que cura.

- **Cero secretos (invariante #1).** Nombres de variable, nunca valores; rutas relativas, nunca
  absolutas; sin IPs/dominios/tokens. El `leak-scan.sh` cubre las entradas como cualquier `.md`. Un
  campo de la plantilla obliga a chequearlo en cada entrada.

- **Consumo por el AGENTE, no solo el humano.** El `description` de la skill lleva triggers
  observables ("cuando re-derivás algo ya resuelto", "cuando greps sin mapa", "cuando doc y código
  divergen") para auto-invocación; el cuerpo es un dispatcher liviano (lee el INDEX, abre la entrada
  lazy, devuelve SOLO la línea de acción). *Compass, not encyclopedia.*

## Consecuencias

- **Positivas:** reusa ~90% de la infra existente (skills, brújula, RUN-LEDGER, parking) — cero
  artefacto huérfano; el conocimiento experiencial deja de perderse entre RETROs efímeros e IDEAS
  volátil; el agente consulta el patrón **al planear** (pull, grepeando por síntoma), sin pre-cargar
  contexto al arranque; el reloj
  `validated_on` + la propiedad humana sobre la promoción evitan el wiki podrido; indexar por
  síntoma hace el lookup de segundos.
- **A vigilar:** el catálogo `.md` vive bajo `docs/`-equivalente exento del gate (sin piso
  automático de actualización) — la defensa es que el contenido NACE del Crisol + el validador STALE
  marca lo viejo; sin esos dos, se pudre en 90 días igual que cualquier wiki. La captura es por
  DOLOR (≥2 apariciones o >30min), no por previsión: el éxito se mide en entradas RETIRADAS (que
  ascendieron a test/regla), no acumuladas. La verificación del commit-ancla de `validated_on` es
  fiable solo intra-repo; cross-repo el validador se ancla a la FECHA (portable).

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v1.40.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.
