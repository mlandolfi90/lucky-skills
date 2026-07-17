---
id: PLAN-equipo-doc-contratos
schema: plan/1
tipo: plan
estado: VIGENTE
creado: 2026-07-16
refs: [corrida:2026-07-16-equipo-doc-v1, adr:0021, adr:0018]
nota: "FASE PIN impuesta por el Steward (iter 1 → REJECT ×3): los 3 contratos cross-carril se fijan acá, en UN artefacto, antes de que ningún carril toque código"
---
# PIN de contratos — corrida `2026-07-16-equipo-doc-v1`

El Steward rechazó los 3 planes de la iteración 1. Los sets de archivos eran
**disjuntos** (cero colisión física): la colisión fue **100% contractual**, y
formaba un **ciclo** — A necesita el formato de C · B necesita el nombre de A ·
C necesita la forma de B. Cada plan declaró la interfaz ajena por su cuenta y
las tres declaraciones no coincidían. Ningún orden de carriles resuelve un
ciclo: por eso los tres valores se fijan ACÁ, y cada carril los **cita**, no los
re-enuncia.

## PIN 1 — `doc_veredicto` · dueño: carril B (`registros.yaml:98 duenio: skill:feature`)

Forma canónica (mapa anidado, no 3 columnas planas — el ADR 0021 §2 dice
"columna" en singular, y `corrida/1` ya usa mapas anidados en `veredictos:`):

```yaml
doc_veredicto: {estado: PENDIENTE, ronda: 0, ref: null}   # estado: PENDIENTE|PASA|FALLA
```

- **B** la escribe (dueño de la tabla `feature`).
- **C conforma**: el lint valida `doc_veredicto.estado == PASA`, **jamás**
  `doc_veredicto: PASA` literal. Validar el campo plano sería un falso-verde
  estructural: el lint aprobaría un campo que nadie escribe y una feature `VIVA`
  sin `PASA` pasaría (es [DRIFT-001] materializado — el check existe pero no
  muerde).

## PIN 2 — formato de `docs/manual/_cobertura.yaml` · dueño: carril C

C es dueño porque posee **los dos parsers** (awk en `brujula.sh`, PyYAML en
`registros-lint.py`). **A lo cita VERBATIM en la regla del prompt; no lo
re-enuncia con sus palabras.**

```yaml
# MANTENIDO por el manualizador (ADR 0021 §5). Dueño ÚNICO de escritura.
# Formato RÍGIDO: lo parsea awk (brujula.sh) Y PyYAML (registros-lint.py).
# Reglas: 4 claves por pieza, en ESTE orden, una por línea; cubre/deps SIEMPRE
# flow-style [a, b] en UNA línea; verificado_en = sha40. Sin comentarios dentro
# de `piezas:`. Paths sin ',' ni ']'.
schema: lucky-cobertura/1
piezas:
  - doc: docs/manual/<pieza>.md
    cubre: [plugins/lucky/skills/<x>/**, plugins/lucky/agents/<y>.md]
    deps: [docs/registros.yaml]
    verificado_en: <sha40>
```

Invariantes del contrato (los tres carriles los tratan como ley):

1. **Orden fijo de las 4 claves**, una por línea, prefijo fijo → awk las saca sin
   máquina de estados sobre YAML anidado.
2. **`cubre`/`deps` SIEMPRE flow-style en UNA línea.** Riesgo central: PyYAML
   acepta block-style y awk NO → block-style pasaría el lint y el awk
   malparsearía **en silencio**, y la señal mentiría. Por eso el lint valida la
   **FORMA CRUDA del texto**, no solo que PyYAML parsee. Esa validación es lo
   único que sostiene el contrato de awk.
3. **`verificado_en` = sha40** (`git rev-parse HEAD` ANTES del commit propio);
   la brújula muestra `sha7`.
4. **El archivo queda LAZY** — no se siembra en esta corrida (`docs/manual/` no
   existe todavía; un sidecar con `piezas: []` sería un artefacto con forma de
   mentira). Nace con la primera pieza.
5. **AUTOR DE LA CABECERA (el hueco que hundió la iter 1): la PRIMERA escritura
   del `manualizador-2` crea el archivo con la cabecera** (`schema:
   lucky-cobertura/1` + `piezas:`) y recién después su entrada. Sin dueño
   asignado, en la primera pieza no había cabecera que leer → el lint de forma
   cruda daba rojo y el awk malparseaba. La regla del prompt de A lo dice
   explícito.
6. `doc:` **acepta** `docs/sistema/…` (audiencia dev, opt-in del manualizador),
   pero el lint **solo exige** entrada para las piezas de `docs/manual/`.

## PIN 3 — nombre del agente autor · dueño: carril A

- El supersede del `manualizador` (ADR 0018 §4) produce **`manualizador-2`**
  (archivo nuevo); la fila vieja muta SOLO `estado: SUPERSEDED` +
  `superseded_by:` (la única mutación legal sobre fila terminal, `registros.yaml`
  §6-7).
- **B conforma**: la rama y el paso 3 de `feature/SKILL.md` nombran
  **`manualizador-2`** explícito. Evidencia que lo vuelve obligatorio: el harness
  descubre `plugins/lucky/agents/*.md` **por directorio y no lee `estado:`** → el
  **nombre del llamador es el ÚNICO de-ruteo existente**. Con el nombre viejo, el
  supersede es decorativo: correría el prompt viejo, que sigue escribiendo `doc:`
  (`manualizador.md:41`) — justo lo que el ADR 0021 §2 prohíbe.
- `lector-cero` nace con `dictamina: [DOC_SIRVE]` y **`tools: Read, Grep, Glob`
  (sin `Bash`)**: es el mecanismo de la enmienda E1 / ADR 0021 §1, no una
  omisión. Quien agregue `Bash` reabre E1 sin ADR.

## PIN 4 — etiqueta legal del carril C (corrección del Steward)

C invocaba **(b) costura faltante** para `brujula.sh` y `registros-lint.py`. Es
ilegal acá: (b) exige **DOS corridas separadas** (`crisol/SKILL.md:158-163`) y el
plan hacía el trabajo en ésta. Y no hace falta — el propio plan prueba lo
contrario: bloque nuevo + función nueva + 1 call-site, **ninguna línea existente
cambia de comportamiento**. Se re-etiqueta a **AGREGA, sin caso legal**. La 2ª
corrida sigue siendo la que gana la costura cuando aparezca el 2º cliente.

## Orden de ejecución (impuesto por el Steward)

1. **FASE PIN** — este artefacto. Hecho.
2. **A · B · C corren EN PARALELO** (sets de archivos disjuntos; los contratos ya
   no están en disputa).
3. `python scripts/proyectar.py` → verificación (roster fresco) → cierre.

## Ratificaciones del Steward que sobreviven al re-plan (no se re-litigan)

- Filtro de mantenimiento **angosto** `^crisol [A-Za-z0-9]+-close:`, medido con
  `--numstat`: los `release…` legacy llevan código real bajo dirs de skill y son
  ancestros de v2.0.0 → inalcanzables desde cualquier cursor nacido hoy. Filtro
  ancho = falso negativo silencioso = la condena E4(b) del ADR.
- **NO** `.gitattributes linguist-generated` para el sidecar: el cursor debe ser
  **ruidoso en review** (ADR 0021 §5: se mueve solo por acto explícito).
- **NO** proyectar frescura al TABLERO (ADR 0021, Consecuencias — explícito).
- `agente` **no** es `sellado: true` → el `manualizador` SUPERSEDED **no** lleva
  entrada en `sellos.json` (agregarla dispararía "sello COLGADO").
- La rama de `feature` nace `canal: estable` por precedente exacto
  (`crisol/ramas/003`: ley nueva, no extraída, nacida estable por endoso
  registrado). **ADR 0021 ACEPTADA es esa firma.**
- Lectura de ADR 0018 §5 ("el tronco solo adelgaza"): presiona al contenido
  **condicional**; la norma **incondicional** (schema de la fila, regla dura)
  entra al tronco.
