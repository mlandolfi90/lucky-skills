---
id: 003-decisiones-convocables
schema: rama/1
tipo: rama
estado: LIVE
canal: estable
creado: 2026-07-16
skill: crisol
gatillo: "el flujo necesita un JUICIO del operador (elección de diseño, trade-off, aprobación) que hoy quedaría solo en el chat"
origen: "endoso previo del operador (debate 2026-07-16, captura 'Decisiones CONVOCABLES') + ADR 0019 §2 — nace estable por endoso registrado"
ultima_validacion: corrida:2026-07-16-gobierno-observable
refs: [adr:0019]
---
# Decisiones convocables — el juicio del operador no vive en el chat

Cuando el trabajo llega a un punto donde SOLO el operador puede decidir
(cambio de contrato, trade-off de diseño, aprobación de excepción), NO se
resuelve con una pregunta suelta que muere al cerrar la sesión. Se **convoca**:

1. Crear la fila `docs/decisions/NNNN-<slug>.md` con `estado: PROPUESTA`
   (frontmatter `decision/1`, refs a la corrida/feature que la necesita) y el
   cuerpo: contexto en ≤10 líneas + las opciones con su trade-off.
2. Presentarla al operador (texto plano, opciones numeradas).
3. Su veredicto flipea el estado: `ACEPTADA` | `RECHAZADA` (+1 línea de
   por-qué si lo da). Regenerar proyecciones en el mismo paso.
4. Deprecarla a futuro = `SUPERSEDIDA` + `superseded_by` — jamás se borra.

El trabajo que dependía de la decisión cita `refs: [adr:NNNN]` — queda trazado
QUIÉN decidió QUÉ y qué se construyó sobre eso. Las decisiones `PROPUESTA` sin
responder aparecen en `docs/TABLERO.md` (bandeja del operador).

**No convocar** para lo que las reglas ya deciden (eso es leer la ley) ni para
lo trivial-reversible (eso es criterio propio + RETRO si salió mal).

---
**Fuente: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.2.0` (cache local, NO la ley).**
