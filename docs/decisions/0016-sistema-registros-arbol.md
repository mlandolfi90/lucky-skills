---
id: adr:0016
schema: decision/1
tipo: decision
estado: ACEPTADA
creado: 2026-07-16
supersede: null
superseded_by: null
refs: [corrida:2026-07-16-refactor-arbol-registros]
---

# 0016 — Sistema de registros: la ley como árbol que crece y todo documento como fila

## Contexto

El sistema documental creció útil pero pesado, con cuatro dolores medidos:

1. **Monolito**: `docs/refactor/_crisol/RUN-LEDGER.md` acumuló 2.536 líneas (~71
   corridas). El agente paga el archivo entero para leer una corrida; los
   guardianes lo re-parsean completo en cada tool-call.
2. **Troncos que engordan**: `crisol/SKILL.md` = 562 líneas (el límite oficial de
   authoring de Anthropic es <500; el umbral local de atomicidad es 400). Todo
   aprendizaje nuevo entra EDITANDO el tronco — exactamente lo que Open/Closed
   prohíbe para el código, aplicado a la ley misma.
3. **Huérfanos**: `PLAN-*.md`, `CUMPLIMIENTO-*.md` viven sueltos, sin estado ni
   dueño; el COLLISION-MAP por corrida no tiene lugar fijo; los veredictos de
   concejos multi-agente mueren en directorios temporales de sesión.
4. **Sin mapa**: no existe un lugar único que responda "¿qué tabla vive dónde y
   quién la escribe?".

La industria converge (investigación verificada 2026-07-16, fuentes primarias en
el debate): registro-por-corrida + índice generado (GitHub Actions runs, MLflow,
Flyway, towncrier); proyecciones regenerables marcadas como generadas (CQRS /
`go generate` / linguist-generated); inmutabilidad post-cierre con supersede
(MADR 4.0 / AWS / Backstage); determinismo byte-a-byte (reproducible-builds);
bloques delimitados re-emplazables (Ansible blockinfile). MLflow deprecó su
backend de archivos: la estructura que migra barato a DB es la que ya mapea
1:1 archivo→fila.

El operador fijó además dos requisitos de futuro: (a) la documentación de cada
repo debe poder mudarse a una base de datos local o remota sin cambiar el
proceso; (b) al liberar un proyecto, la retroalimentación del proceso (el
"taller") no debe viajar con el producto.

## Decisión

1. **Todo documento del proceso es una FILA**: frontmatter YAML = columnas
   (`id` = nombre de archivo = clave primaria; `schema: <tipo>/<versión>`;
   `tipo`; `estado`; `creado`; `refs:` tipadas `<tabla>:<id>`); cuerpo markdown
   = payload. Carpeta = tabla.
2. **Manifiesto** `docs/registros.yaml` = el DDL: declara tabla → path → dueño →
   estados terminales → proyecciones → visibilidad (`producto` | `taller`).
   `scripts/registros-lint.py` valida manifiesto↔realidad (fail-closed en la
   forja).
3. **El ledger se parte**: una corrida = un archivo en
   `docs/refactor/_crisol/runs/`; el monolito histórico se CONGELA verbatim en
   `runs/_archivo-hasta-2026-07.md` (la historia no se convierte — se archiva);
   `RUN-LEDGER.md` pasa a ser PROYECCIÓN generada por `scripts/proyectar.py`
   **en el formato legacy y en el MISMO path** — los guardianes
   (`crisol_gate.py`, `crisol-enforcer.sh`) no se tocan en esta fase (son
   fail-open: un renombre los apagaría en silencio). `_ACTIVE` = puntero O(1) a
   la corrida abierta (proyección). Prueba de paridad obligatoria: el gate emite
   el MISMO veredicto sobre monolito original y proyección regenerada.
   **Fase 2 (corrida futura, jamás junta con esta):** los guardianes aprenden a
   leer `_ACTIVE` + frontmatter y muere el parser de prosa.
4. **Reglas de escritura**: un dueño por tabla; fila nueva = archivo nuevo;
   inmutable post-cierre (única mutación: transición de `estado` +
   `superseded_by`); proyecciones jamás se editan (marcador GENERADO +
   `linguist-generated`); regeneración byte-determinista; write-if-absent en
   scripts de migración/adopción; corridas CLOSED selladas con sha256 sobre
   bytes LF (`.gitattributes` fija `eol=lf` — sin esto, `autocrlf` de Windows
   rompería sellos en masa).
5. **El árbol de skills**: el tronco común de ruteo YA existe (skill `ley` +
   `registry.json` + descriptions) — se declara, no se construye. El
   aprendizaje nuevo entra como RAMA (`<skill>/ramas/NNN-slug.md` + una línea en
   el bloque índice del tronco), jamás reescribiendo el tronco; techo de tronco
   400 líneas como CITACIÓN (mecanismo de atomicidad, ADR 0008). Las ramas y
   los agentes canónicos NO se migran preventivamente: nacen cuando toque.
6. **Futuro DB (diferido)**: la forma archivo=fila ES el contrato; el puerto de
   4 operaciones (`poner/traer/listar/proyectar`) se materializa recién con el
   segundo backend; `registros.yaml` será el DDL; un solo backend autoritativo
   de escritura por repo (campo `backend: fs`), el otro solo proyección.
7. **Visibilidad y liberación**: tablas del proceso = `taller` (jamás viajan);
   docs de producto = `producto`. Liberar = EXPORTAR un repo nuevo limpio —
   nunca publicar el repo de trabajo (el historial git es taller).

## Consecuencias

- El agente abre UNA corrida (~30-60 líneas), no 2.536; los troncos dejan de
  engordar; los huérfanos quedan explicados por su `estado`.
- Nueva ventana de riesgo transitoria: el gate lee una proyección — mitigada
  por (a) regenerar en el MISMO paso que toda mutación del run, (b) `_ACTIVE`,
  (c) la prueba de paridad como gate de la migración, hasta que la Fase 2 la
  cierre de raíz.
- El volcado futuro a DB es un loop mecánico sobre el manifiesto; la historia
  congelada entra como partición histórica (parser solo si algún día se
  necesita).
- La espec completa del debate (escalera diagnóstico→microfix→hotfix→crisol,
  features, decisiones convocables, concejos archivados, agentes canónicos,
  cuarentena de ramas, telemetría, tablero, docs 3 audiencias, evaluador de
  forma, métricas M1-M9) queda capturada en `docs/IDEAS.md` (2026-07-16) como
  backlog aprobado: cada pieza entra por su propia corrida chica, por agregado.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.8.0` (cache local, NO la ley).**
