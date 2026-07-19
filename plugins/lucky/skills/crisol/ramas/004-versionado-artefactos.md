---
id: 004-versionado-artefactos
schema: rama/1
tipo: rama
estado: LIVE
canal: estable
creado: 2026-07-19
skill: crisol
gatillo: "el operador o un agente pregunta qué versión ponerle a una entrega/artefacto de producto, o hay que stampear una beta/entrega para probar"
origen: "regla nueva endosada por el operador (spec 2026-07-19) — nace estable por endoso registrado (precedente rama 003, ADR 0019 §2)"
ultima_validacion: corrida:2026-07-19-versionado-artefactos
refs: [adr:0026, adr:0018]
---
# Versionado de artefactos — la versión es LECTURA del proceso

La versión de un artefacto de producto no se elige: se LEE del proceso que lo
produjo. Cuatro segmentos, **`generacion.corridas.hotfixes.microfixes`**, cada
uno la cuenta ACUMULADA de veces que ese engranaje del Crisol corrió sobre el
artefacto. **Nunca se resetea a la derecha** (subir un segmento no pone en 0 los
de abajo): con reset, dos estados distintos se verían con el mismo número y la
lectura mentiría. Esta rama es la DEFINICIÓN única (ADR 0026); las demás skills
apuntan acá.

## Los 4 segmentos — disparador y fuente de verdad DERIVABLE

- **1 · generación** — cambio de fondo del artefacto (storage nuevo, reescritura
  de plataforma, ruptura conceptual). *Disparador:* un bump declarado. *Fuente:*
  disciplina declarada — la fila de la corrida lleva `GENERACION: bump` con la
  evidencia objetiva del cambio de fondo (no hay registro mecánico que lo cuente
  solo).
- **2 · corridas** — cada corrida Crisol que CERRÓ sobre el artefacto.
  *Disparador:* corrida a CLOSED. *Fuente derivable:* `docs/refactor/_crisol/runs/`
  con estado CLOSED — **NO `sellos.json`** (el sello es integridad de la copia de
  la ley, no un contador de corridas de producto; ver Deslindes).
- **3 · hotfixes** — cada hotfix formalizado sobre el artefacto. *Disparador:*
  hotfix a CLOSED. *Fuente derivable:* `docs/hotfixs/` con estado CLOSED.
- **4 · microfixes + entregas** — el segmento de grano fino: cada sonda microfix
  FAVORABLE Y cada entrega-para-probar (beta) que se le pasó al operador.
  *Disparador:* microfix FAVORABLE, o beta entregada. *Fuente derivable (una
  mitad):* `docs/microfixes/` con estado FAVORABLE; la otra mitad (entregas) es
  disciplina declarada — una entrega = un bump del 4to, no arranca de nuevo por
  abrir un hotfix (es el contador del ARTEFACTO, no del hotfix).

**Disciplina, no maquinaria prematura** (ADR 0026): los segmentos sin registro
mecánico se sostienen por disciplina declarada. El diente que lo automatice llega
cuando un repo real adopte la regla; hoy es prosa normativa.

## Ambigüedades cerradas

- Corrida **ESCALATED** no cuenta en el 2do (no cerró: escaló).
- Sonda microfix **NO_FAVORABLE** no cuenta en el 4to (no fue favorable).
- Artefacto **nace `0.0.0.0`**.
- **Rige de acá en adelante**: no se re-numeran artefactos viejos.

## Cómo se EXPRESA en cada ecosistema (expresión ≠ definición)

La semántica es una sola (arriba); cambia solo la GRAMÁTICA del string:

- **Extensión de navegador / PEP 440 / tag git** — 4 enteros tal cual: `X.Y.Z.N`
  (extensión), `1.12.4.16` (PEP 440), `vX.Y.Z.N` (tag). Cap por segmento **65535**
  (lo impone el manifest de extensiones): si un segmento se acerca al cap, es
  señal de que el artefacto pide una GENERACIÓN nueva, no un número más grande.
- **semver-de-3 estricto** (solo `MAJOR.MINOR.PATCH`) — la lectura de 4 segmentos
  no entra en 3 números; ahí la lectura vive en el commit + el ledger, y se cruza
  ese puente cuando exista un artefacto real bajo semver estricto (deuda
  declarada). Se **descartaron** a propósito `+build` y `-prerelease`: mapear el
  4to segmento ahí lo vuelve invisible al ordenamiento y deja de contar.

## Deslindes (de una línea)

- **vs TAG_GATE:** los tags `vX.Y.Z` de la LEY (lucky-skills) NO son esto — los
  gobierna el TAG_GATE de la forja y no se tocan; esta rama versiona PRODUCTO.
- **vs SELLOS:** el sha256 de `sellos.json` es integridad de la copia de la ley,
  no un contador de versión de producto.
- **vs PIN_TOTAL:** pinear una versión es CONGELAR la lectura en un punto para
  reproducir, no re-derivarla.

## Ejemplo trabajado (una jornada)

`1.12.4.16 → 2.13.4.27`: en el día hubo **11 entregas-para-probar** (4to:
16→27), **una corrida Crisol PASS** (2do: 12→13) y **un bump de generación** por
storage nuevo (1ro: 1→2); ningún hotfix se formalizó (3ro queda en 4). Sin reset:
el 2do subió a 13 y el 4to NO volvió a 0 — el número entero es la lectura fiel de
lo que pasó.

---
**Fuente: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.8.0` (cache local, NO la ley).**
