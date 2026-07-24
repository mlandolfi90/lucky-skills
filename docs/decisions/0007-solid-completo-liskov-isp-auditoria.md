# 0007 — SOLID completo: LISKOV + INTERFACE_SEGREGATION al catálogo, y auditoría retroactiva como modo read-only

- **Estado:** aceptada (corrida Crisol 2026-07-05, Tier Completo)
- **Contexto previo:** `docs/refactor/_crisol/PLAN-solid.md` (investigación de 6 agentes, ancla v1.24.0)

## Contexto

El Crisol ya encarnaba ~4/5 de SOLID por construcción: `ATOMICIDAD` (S),
`OPEN_CLOSED` (O, la más completa), `CONFORMIDAD`+inyección (D fuerte-en-hexagonal),
ISP parcial (solo vía anti-patrón `Puerto-Dios`, condicional a hexagonal). El único
ausente genuino era **Liskov (sustituibilidad)** — y la demo del plan lo probó en
carne propia: los dos guardianes del propio Crisol (`crisol_gate.py` /
`crisol-enforcer.sh`) eran dos implementaciones NO sustituibles de la misma regla
(false-PASS de branch por match substring en el enforcer), el "cisma de guardianes"
resucitado.

## Decisión

1. **Dos reglas nuevas al catálogo (§2 Diseño + §5), ambas clase J, gate fail-closed:**
   - `LISKOV`: una implementación nueva de una abstracción existente sustituye al
     supertipo sin romper su contrato semántico. Válvula: cambio de contrato
     declarado en el plan (caso legal (c) → tier completo + ADR).
   - `INTERFACE_SEGREGATION`: el contrato se parte por necesidad de cliente; ningún
     cliente depende de métodos que no usa. Distinta de `ATOMICIDAD` (SRP = la
     unidad; ISP = el contrato expuesto — provider-side vs consumer-side).
   - Las dictamina el **`design-verifier` existente** (cobertura dinámica, cero
     spawn nuevo). Fuente única del enunciado: crisol SKILL.md §2/§5;
     `auditor-checklist.md` referencia por nombre. `Puerto-Dios`
     (`arquitectura/references/anti-patrones.md`) queda como **instancia hexagonal**
     de `INTERFACE_SEGREGATION` — apunta al ID canónico, no lo redefine.
2. **Auditoría retroactiva = modo read-only de `arquitectura`, NO skill nueva, NO
   corrida Crisol:** `arquitectura/templates/auditoria-solid.md` + 1 fila al Router
   (crecimiento Open/Closed de la propia skill). Independiente del método de
   creación (nunca gatea código viejo — castigar retroactivo es injusto) pero con
   **criterio compartido** (grano S/O/L/I → catálogo del Crisol por nombre;
   estructura D/capas → `conformidad-checklist.md` + `anti-patrones.md`). Severidad
   ALTA = "el gate lo rechazaría si naciera hoy" (anclada al set vivo §5). Alimenta
   al Crisol **por dato, no por acople**: ALTA→IDEAS · MEDIA recurrente→bitácora
   CANDIDATE (DRIFT) · BAJA→SENALES (`visto:N`). Kaizen evidence-triggered: la misma
   violación recurrente en varios repos es la evidencia que asciende una regla.
3. **Paridad de guardianes como caso Liskov saldado:** el enforcer adopta branch y
   STATUS por comparación EXACTA y la **allow-list del gate** como política única de
   detección de código (deja el deny-by-default); la paridad de listas queda
   **probada por el fixture** (`tests/test-enforcer.sh` extrae ambas y compara),
   no prometida por comentario.

## Consecuencias

- La matriz de una corrida que cree/modifique implementaciones de abstracciones
  existentes o contratos multi-cliente exige veredicto `LISKOV`/`INTERFACE_SEGREGATION`
  (Lane B fail-closed, cobertura dinámica: N/A si el trigger no aplica).
- El mecanismo del gate no cambió (patrón "una fila al catálogo": mecanismo cerrado,
  set de reglas abierto). Camino a clase H cuando aparezca una rebanada decidible
  por código (ej. exhaustividad de handlers).
- La auditoría retroactiva es portable a los repos adoptados (Glob-discovery,
  N/A-si-ausente) y produce backlog con evidencia real, no especulación.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.10.1` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.
