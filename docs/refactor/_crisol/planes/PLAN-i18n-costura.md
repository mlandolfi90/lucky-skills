---
id: PLAN-i18n-costura
schema: plan/1
tipo: plan
estado: VIGENTE
creado: 2026-06-24
refs: []
nota: "plan aprobado SIN ejecutar (espera decisión de MLL); la deuda lateral de CRLF que halló la saldó .gitattributes"
---
# PLAN quirúrgico — integración de i18n / selector-de-idioma a las skills

> **Modo:** Crisol PLAN-ONLY (no se implementa nada acá). Pedido por MLL: *"planificá bien
> cómo integrarla a las skills… ¿es una parte más de skills? planificación quirúrgica."*
> **Generado por:** workflow multi-agente `plan-i18n-seam` (21 agentes opus: 6 arqueología →
> 4 diseños + 3 jueces → Steward + 3 verificadores adversariales, 2 rondas). Ancla: v1.23.0.
> **Estado:** PLAN. No es decisión (no hay ADR todavía) ni corrida de código. Espera la
> autorización de MLL (pregunta 1).

---

## Veredicto directo: ¿es una parte más de skills?

**NO.** No es una skill nueva invocable (ni slash-command, ni entrada de registry firmada, ni
ID en la matriz §5). Los **3 jueces rankearon "skill nueva `idioma`" ÚLTIMO**.

Su hogar natural es una **extensión drop-in de la skill `arquitectura` YA existente** —vía su
mecanismo Open/Closed: reference nuevo + fila al Router, sin editar el núcleo (precedente vivo:
`arquitectura/references/deploy-build-once-promote.md`)—.

**PERO** (la corrección dura de la verificación adversarial): **la primera corrida NO crea ni
siquiera esa extensión.** Crear el reference/Router hoy, para una capacidad con **0 usos reales**,
sería la misma **generalidad especulativa** que el encuadre condena y que el repo ya castigó
(retiró GAP-001 / GREP-001 por 0 usos; regla viva *"sin evidencia real no entra al catálogo"*,
`IDEAS.md`). La propia idea manda *"corrida con ADR cuando el producto esté maduro"*.

**Lo único que aterriza HOY es una NORMA VIVA (no un artefacto):** el encuadre, el discriminador
RESPONSIVE↔i18n y la norma "dejá la costura", subsumidos en la regla **COSTURA** existente.

---

## Las dos vías (autorización resuelta por adelantado, no como pregunta abierta)

### Vía A — DEFECTO (sin autorización nueva; es lo que corre)
Aterrizaje **solo en `docs/IDEAS.md`** (signature-neutral) de:
1. El **encuadre** (i18n = capacidad plug-and-play, abierta).
2. El **discriminador**: `RESPONSIVE` gatea DURO (clase H — UI rota en móvil = **defecto de hoy** →
   FAIL) · `i18n` **NO gatea** (UI sin selector = capacidad-todavía-no-necesaria; gatearla violaría
   el Crisol: generalidad especulativa = deuda).
3. El **patrón de costura**: dispatch `(locale, key) → string`, **español como único locale poblado
   + fallback**, "i18n-ready pero MONOLINGÜE".
4. La norma **"dejá la costura de idioma"** como **instancia de la regla COSTURA existente** (clase J,
   N/A por defecto) — **sin ID nuevo**, con la **dirección del juicio fijada por escrito**: COSTURA
   sobre i18n juzga SOLO *ubicación-cuando-se-agrega-un-seam*; la **ausencia de seam i18n es N/A,
   NUNCA FAIL**.

En Vía A **no** se crea el reference, **no** se toca el Router, **no** se edita
`arquitectura/SKILL.md`. Cero footprint de firma.

### Vía B — solo si MLL confirma EXPLÍCITAMENTE que quiere el reference YA
Recién ahí se crea `arquitectura/references/i18n-costura.md` (descriptivo, sin sello, primo de
`deploy-build-once-promote.md`) — limitado al patrón + discriminador + self-check advisory con
guarda anti-promoción — **y** se edita `arquitectura/SKILL.md` (fila al Router + footer "Capas:"),
**bundleado en la misma entrega con `forjar-release` + annotation/ADR de CREDITO**. Ver "Cadena de
firma" para por qué el edit del SKILL.md sellado NO puede ir suelto.

Cero skill nueva, cero slash, cero entrada de registry propia, cero token nuevo en el gate — en
**ambas** vías.

---

## Plan por archivo

| Archivo | Acción | Por qué |
|---|---|---|
| `docs/IDEAS.md` | **EDITAR** (Vía A, 1ra corrida): registrar la norma viva (encuadre + discriminador + patrón de costura + norma "dejá la costura" subsumida en COSTURA con dirección de juicio fijada) + los diferimientos + la deuda `.gitattributes`. | Hogar del encuadre y del parking. **Genuinamente signature-neutral**: `docs/IDEAS.md` NO está en SEALED (cubre `docs/decisions`) ni en HASHES. Deja la idea ABIERTA sin pre-consumir autorización. |
| `arquitectura/references/i18n-costura.md` | **DIFERIR** (no crear en 1ra corrida). Solo Vía B: crear descriptivo, sin sello, acotado al patrón + discriminador + self-check advisory. | Crearlo hoy asume la autorización que la idea niega. Cuando se cree (Vía B) es signature-neutral (references/ no está en SEALED ni HASHES; viaja raw@commit como deploy). |
| `arquitectura/SKILL.md` | **DIFERIR** (no editar en 1ra corrida). Solo Vía B: +1 fila al Router + reference al footer "Capas:", bundleado con forja + annotation/ADR. | Está en **SEALED Y en HASHES** → cambiar sus bytes desincroniza `registry.json.sha256` del raw y **`cargar` FALLA** salvo re-forjar. Dispara CREDITO/CONFORMIDAD/SELLOS. Condición dura: preservar EXACTAMENTE 1 ancla de sello byte-idéntica; el pre-flight aborta con cero escrituras si hay ≠1 match. |
| `.gitattributes` | **FLAGGEAR como deuda de firma ACTUAL** (no crear sin su decisión). | `forjar-release.sh:256` (`sha256_lf`) asume que existe para servir el raw en LF byte-idéntico; su ausencia compromete la paridad LF que consume `cargar` **hoy** (UTF-8 multibyte), no solo el futuro language-pack. |
| `crisol/SKILL.md` §5 (matriz) | **NO TOCAR** (explícito). | Agregar un ID i18n con TRIGGER activo lo vuelve **fail-closed por construcción** (gate de cobertura Lane B: ausencia=FAIL, sin token WARN). i18n queda subsumido en COSTURA (N/A por defecto). |
| `arquitectura/templates/conformidad-checklist.md` | **NO TOCAR** (explícito). | Contrato **binario** (PASS ⟺ todo verde). Una fila "advisory" mete la 1ra excepción en un doc binario → riesgo de promoción accidental a gate. El self-check vive en la nota descriptiva. |
| `forjar-release.sh` · `registry.json/.schema` · `crisol/hooks/*` · templates · `brujula/SKILL.md` | **NO TOCAR** en 1ra corrida. En Vía B, `forjar-release` **se ejecuta** (no se edita) para re-hashear/re-firmar tras el edit del SKILL.md. | Cero cambio de la maquinaria fail-closed. En Vía A, cero footprint de firma. |

---

## Especificación de la COSTURA (lo que se deja, sin cablear)

Un **único punto de extensión** de dispatch de texto `(locale, key) → string`, colocado **donde el
sistema realmente varía**: el borde de presentación (MVC-dentro-del-adaptador de entrada). Propiedades:
- **Español = único locale poblado + fallback.**
- **i18n-READY pero MONOLINGÜE**: la seam existe porque *sabemos* que el texto visible-al-usuario es
  donde varía (costura **con evidencia**, no especulativa), pero **no** hay archivos de locale sin usar
  ni idiomas precableados.
- Agregar un idioma después = soltar `locales/<lang>.json` + registrarlo en el dispatch = trivial, sin
  tocar el núcleo ni el puerto estable (Open/Closed).
- La **elección de familia técnica** (pre-traducido byte-estable vs model-pack al vuelo), su firmabilidad
  y su compatibilidad con `cargar` **NO** son parte de esta costura: son propiedades de la **ruta firmada**
  (que hoy no existe) → van al ADR diferido del language-pack.
- **Verificación** = un JUICIO (instancia de COSTURA, clase J), NUNCA una medida mecánica ni un gate.
  Dirección fijada: juzga *ubicación-cuando-se-agrega-un-seam*; **ausencia de seam = N/A, nunca FAIL**.

---

## Enforcement SUAVE (resolviendo honestamente la contradicción que marcaron los verificadores)

Se **elimina** la afirmación absoluta "nunca puede volverse fail-closed". Se declara con honestidad:
al rutearse por COSTURA, la costura i18n **hereda** el juicio de COSTURA (clase J) sobre ubicación-de-seam,
riel que **ya está presente** (el design-verifier ya lo dictamina, el Steward ya lo juzga shift-left).
La suavidad viene de **tres acotaciones concretas**, no de "no existe maquinaria":
1. **No se agrega ID a §5** → el gate de cobertura de Lane B (fail-closed) **no alcanza** a i18n; queda
   subsumido en COSTURA (N/A por defecto).
2. **La dirección del juicio de COSTURA sobre i18n está acotada por escrito**: solo ubicación-cuando-se-
   agrega-un-seam; ausencia de seam = N/A, nunca FAIL. (Blinda contra un design-verifier que quisiera
   FALLAR un plan de UI por un seam i18n "especulativo".)
3. La **"pregunta de checklist"** vive como **self-check advisory FENCED con guarda anti-promoción**:
   *"> Señal no-normativa; NO puede citarse por sí sola como base de un FAIL de COSTURA por ausencia de
   seam. ¿Dejaste la costura de idioma?"* — nunca como checkbox en el conformidad-checklist binario.

Mecánica heredada del **precedente canónico soft del repo**: la Destilación/Bitácora (*"exento del gate;
el Crisol AVISA, no exige"*), **NO** la de RESPONSIVE (que sí gatea).

---

## Cadena de firma — resolución (tres niveles, honesto)

1. **Vía A (1ra corrida) — genuinamente signature-neutral:** único archivo tocado = `docs/IDEAS.md`
   (no en SEALED, no en HASHES). Cero footprint, cero re-forja, cero riesgo sobre `cargar`.
2. **Vía B — impacto REAL:** el reference bajo `references/` sí es signature-neutral; **el edit de
   `arquitectura/SKILL.md` NO** (está en SEALED Y HASHES). Commitearlo sin re-forjar deja
   `registry.json.sha256` desincronizado → `cargar` FALLA. Por eso Vía B **exige, en la misma entrega**:
   correr `forjar-release` (re-hash + re-firma atómica por tag; no hay firma incremental) o diferir el
   edit hasta bundlearlo con la próxima release. **Prohibido el SKILL.md editado suelto.** Condición dura:
   preservar EXACTAMENTE 1 ancla de sello byte-idéntica; si hay ≠1 match, el pre-flight aborta con cero
   escrituras. Dispara CREDITO + CONFORMIDAD + SELLOS → se produce la annotation/IMPACT-MATRIX o ADR.
3. **Deuda de firma ACTUAL (no diferida):** `.gitattributes` **ausente** — `forjar:256` lo asume para
   servir el raw en LF byte-idéntico; sin él, la paridad LF que consume `cargar` es frágil HOY.
4. **Diferido al ADR del language-pack:** separar el set SEALED del set HASHES (hoy casi idénticos; una
   traducción sin el sello español EXACTO abortaría la forja); LF sin BOM; capability-gate; y la regla de
   que Familia A (model-pack al vuelo) nunca entra en la ruta firmada (no determinista/no hasheable).

---

## Riesgos

1. **Riel COSTURA ya presente** → un design-verifier podría FALLAR un plan de UI por un seam i18n
   "especulativo" que el propio encuadre incitó. *Mitigado:* dirección de juicio fijada (ausencia = N/A) +
   guarda anti-promoción.
2. **Especulación residual:** aterrizar la norma en `IDEAS.md` con 0 productos roza *"sin evidencia real
   no entra al catálogo"*. *Mitigado:* norma viva subsumida en COSTURA (sin ID, sin artefacto), reversible.
3. **Vía B sin bundlear la forja** → `cargar` FALLA. *Mitigado:* prohibición dura + chequeo del ancla.
4. **Deuda `.gitattributes`** compromete la paridad LF servida a `cargar` HOY.
5. **Drift documental (Vía B):** agregar al Router pero no al footer "Capas:" repite el desync que hoy
   sufre `deploy`. *Mitigado:* exigido en ambos lugares.
6. **Promoción accidental a gate:** un editor futuro podría mover el self-check a un checkbox/ID §5.
   *Mitigado:* doc descriptivo (sin contrato binario) + guarda anti-promoción.
7. **Enforcement suave = débil (honesto):** una señal que "avisa no exige" es fácil de ignorar; la costura
   puede no dejarse nunca. Es el **costo aceptado** del encuadre defecto/capacidad, no un bug.
8. **Caso-PROSA** puede sentirse como esquivar media pregunta. *Mitigado:* es la respuesta categórica
   correcta (el LLM ya es multilingüe → no es feature de runtime), no evasión.
9. **Deuda de firma diferida, no eliminada:** el language-pack exigirá separar SEALED de HASHES, extender
   `forjar`, LF sin BOM y capability-gate — llega con su ADR.

---

## Preguntas para MLL (las decisiones que el plan surfacea)

1. **AUTORIZACIÓN (la que gobierna el alcance):** la 1ra corrida por defecto (Vía A) aterriza SOLO la
   norma en `IDEAS.md` y DIFIERE el reference+Router+edit-SKILL.md a evidence-triggered (primer APPS real).
   **¿Confirmás ese diferimiento, o autorizás EXPLÍCITAMENTE crear el reference YA (Vía B)** —sabiendo que
   arrastra editar el SKILL.md sellado, correr `forjar-release` en la misma entrega y producir la
   annotation/ADR de CREDITO?
2. **Ubicación de la "pregunta de checklist":** ¿te alcanza como self-check advisory con guarda
   anti-promoción, o la querés literal en el checklist binario (no recomendado — mete una excepción)?
3. **Componente drop-in:** ¿diferido a evidence-triggered (recomendación del panel) o querés el scaffold
   opinado (Familia B, i18next) ya?
4. **SEÑAL en la brújula** (clon de "ley atrasada", no-normativa): ¿en la 1ra corrida o diferida?
5. **Language-pack de prosa-de-skills:** ¿confirmás que queda 100% parqueado a su propio ADR (separar
   SEALED/HASHES, tocar `forjar-release.sh`), con el español canónico como única fuente firmada?
6. **Deuda `.gitattributes`:** ¿la saldamos como fix de firma independiente (afecta la paridad LF HOY) o
   la agendamos?

---

## Parqueado explícito (lo que NO se hace ahora)

- Reference-registrado-en-Router: diferido a evidence-triggered o a Vía B explícita.
- Componente/librería drop-in (scaffold i18next): diferido a evidence-triggered.
- Reglas de admisibilidad de familias (prohibir Familia A, fijar Familia B): al ADR del language-pack.
- Language-pack pre-traducido de prosa: a su propio ADR (separar SEALED/HASHES + tocar `forjar`).
- ID propio en §5 (p.ej. `COSTURA_IDIOMA`): **nunca** (lo volvería fail-closed). Vive subsumido en COSTURA.
- Fila/checkbox en `conformidad-checklist.md`: no (mantenerlo 100% binario).
- Skill invocable `idioma`: descartada hoy; reconsiderable solo si un producto exige el artefacto
  shippable, vía ADR.
- Localización de la prosa de las skills: "no hace falta feature" (el LLM ya es multilingüe).

---

## Nota de verificación adversarial

2 rondas (techo). Round final: `enforcement-suave` **SÓLIDO**, `firma-integridad` **SÓLIDO**,
`scope-especulación` **DÉBIL** (residual). El DÉBIL residual es honesto: *incluso* aterrizar la norma en
`IDEAS.md` con 0 productos reales roza la especulación — mitigado manteniéndolo como norma viva reversible
(sin ID, sin artefacto) y difiriendo todo lo material. Los verificadores empujaron el plan a ser **más
conservador**, no menos: la versión inicial creaba el reference; la final lo difiere.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · PLAN (no ley, no ADR). Ancla: v1.23.0.**
