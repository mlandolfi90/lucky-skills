---
id: adr:0017
schema: decision/1
tipo: decision
estado: ACEPTADA
creado: 2026-07-16
supersede: null
superseded_by: null
refs: [corrida:2026-07-16-escalera-diagnostico-microfix, adr:0016, adr:0012, adr:0014]
---

# 0017 — Escalera de calidad: peldaños 0–3, entrada default y escalada sin saltos

## Contexto

El operador definió en el debate 2026-07-16 (capturas en `docs/IDEAS.md`) que
los ciclos de calidad deben ser **aditivos y crecientes**: "dividir los pasos
en etapas agregables; el flujo crece y va cumpliendo etapas". Dolor real que
lo motiva: correcciones que arrancan con ceremonia desproporcionada ("corridas
locas" para explorar) o en el lugar equivocado ("a veces se empieza a codear
en la PC local cuando el fix se hace en el entorno caliente — eso no tiene
sentido"). El hotfix ya existía (ADR 0012, 0014) como permiso de trabajo en
caliente; faltaban los peldaños de abajo y la doctrina del conjunto.

## Decisión

**La escalera:** `diagnostico (0) → microfix (1) → hotfix (2) → crisol (3)`.

1. **Peldaño 0 — diagnóstico** (skill `diagnostico`): evaluador PASIVO
   read-only. Reproduce, localiza (bitácora por síntoma + arquitectura por
   capa), hipotetiza con evidencia-o-N/D, y recomienda escalón + tope. Cero
   mutación del sistema observado → **legal en cualquier entorno, incluso
   producción** (formaliza la línea preexistente del crisol: "contenedor de
   testing/prod = solo diagnóstico"). Única escritura: su fila
   (`docs/diagnosticos/`, taller).
2. **Peldaño 1 — microfix** (skill `microfix`): sonda de UN comportamiento
   tocando UN punto. **Entrada DEFAULT de toda corrección**: si el operador no
   indicó el tope, el flujo PREGUNTA *"¿hasta qué escalón llega esto?"* antes
   de tocar código — sin respuesta, no se toca. Veredicto binario
   favorable/no-favorable; sonda no favorable se revierte (sin residuo).
3. **Sin saltos, con cadena:** se escala de a un peldaño llevándose los
   `refs:` (diagnostico → microfix → hotfix → corrida de cierre). **Excepción
   única 1→3:** si la sonda revela que la solución es CONOCIDA y toca
   contrato/multi-archivo, el microfix cierra `ESCALADO` y se abre crisol
   directo — porque el hotfix intermedio sería ceremonia vacía (el hotfix
   investiga hasta camino claro; acá el camino YA está claro), y la cadena de
   refs se preserva igual.
4. **TARGET por peldaño, siempre declarado:** el env legal varía por peldaño y
   caso — diagnóstico: cualquiera (read-only); microfix/hotfix: dev = mesa
   caliente default, `pc-local` SOLO por pedido explícito del operador para un
   caso especial; **producción jamás se sondea** (síntoma de prod →
   diagnóstico en prod + sonda en dev). Nunca implícito.
5. **Puente de gate (transitorio, Fase 1):** el gate actual exige corrida para
   tocar código; el microfix que toca código abre TAMBIÉN una corrida
   fast-path mínima con refs cruzadas. Este puente **muere en la Fase 2**
   (cuando los guardianes aprendan a leer frontmatter/peldaños — corrida
   futura ya decretada en ADR 0016 §3), y el microfix pasará a ser su propio
   permiso. Mismo patrón de transición supersedible que el ledger.
6. **Dos tablas nuevas del taller** (DDL aditivo, lazy, sin datos):
   `diagnostico` (ABIERTO → RESPONDIDO | DESCARTADO) y `microfix`
   (ACTIVE → FAVORABLE | NO_FAVORABLE | ESCALADO), declaradas en
   `registros.yaml` y sembradas por `adoptar-crisol.sh`.

## Consecuencias

- La ceremonia se paga proporcional al conocimiento: explorar es barato
  (peldaños 0-1), formalizar es riguroso (peldaño 3) — y el crisol vuelve a su
  rol de formalizador del final, no herramienta de exploración.
- La cadena de refs hace auditable el camino completo de cada corrección.
- Queda deuda declarada: el agente canónico de localización del diagnóstico y
  el peldaño propio del gate (Fase 2) — en backlog aprobado (`docs/IDEAS.md`),
  entran por sus corridas.
- El peldaño 2 (hotfix) no cambia de flujo: solo gana membresía explícita en
  la escalera (sección aditiva) — ADR 0012/0014 siguen vigentes.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.5.0` (cache local, NO la ley).**
