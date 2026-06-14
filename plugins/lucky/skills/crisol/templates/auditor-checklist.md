# Checklist del Verificador (quality-auditor + archaeologist)

> Deriva del checklist del quality-auditor (`feedback_three_agent_loop.md`) +
> el gate de crédito técnico (`feedback_technical_credit.md`, REGLA DE ORO).
> Se evalúa sobre **estado real** (diff + tests que corre el verificador), nunca
> sobre la prosa del Ingeniero. Veredicto **binario**: `PASS` / `FAIL`.
> Cualquier ítem en rojo → `FAIL` con defecto concreto `archivo:línea` → Paso 1.

## A. Funcional / tests
- [ ] Tests existen para lo nuevo/cambiado (unit + integration + e2e según capa).
- [ ] Suite **verde** corrida por el verificador (no reportada por el Ingeniero).
      Registrar SOLO: veredicto (PASS/FAIL) + conteo de casos + línea de error
      si FAIL. **Prohibido volcar stdout completo** — ningún valor de env var,
      connection string ni token en el ledger; si aparece, redactar antes de pegar.
- [ ] Cobertura ≥ umbral del dominio. Sin baja de cobertura.
- [ ] `lo staged == lo verificado` (diff real revisado).

## A2. UI / Responsive (solo si la corrida tocó UI)
- [ ] Render verificado en viewport móvil (~390px): sin overflow horizontal,
      sin elementos inaccesibles, sin cuelgues con datos reales.
- [ ] Interacciones primarias usables con touch (tap targets, scroll).
- [ ] PASS de sandbox/desktop NO sustituye la verificación móvil (lección TDU-020:
      "CLOSED-PASS" en sandbox, colgado en el teléfono real).

## B. Cero deuda técnica (`feedback_no_tech_debt.md`)
- [ ] SoC: cada módulo/clase/función con UNA responsabilidad.
- [ ] Factorizado: sin copy-paste, sin funciones gigantes, sin archivo mezcla-todo.
- [ ] Sin código muerto / sin duplicación.
- [ ] Sin `# TODO` huérfanos (si queda algo → issue separado, no en código).
- [ ] Dependencias pineadas exactas (ADR 0002).
- [ ] Type hints / typing completos.
- [ ] Logging estructurado.
- [ ] Convenciones del stack (naming, imports, error handling).

## C. Crédito técnico — GATE de PASS (REGLA DE ORO)
- [ ] Si el cambio toca arquitectura/patrón/contrato → ADR creado o referenciado.
- [ ] Frontmatter estructural / IMPACT-MATRIX / ARCHITECTURE.md actualizado si la
      estructura cambió.
- [ ] Annotation (ADR 0010) depositada donde corresponda.
- [ ] **Si había oportunidad de depositar crédito y no se depositó → `FAIL`.**

## D. Integridad estructural (consulta al archaeologist)
- [ ] El grafo final es íntegro: sin acoplamientos rotos.
- [ ] No faltan conexiones que el Ingeniero no actualizó.
- [ ] Sin dependencia circular nueva.
- [ ] No viola Growth-First (no se tocó core para "soportar" un worker).
- [ ] **(skill arquitectura)** Conformidad estructural: si el repo declaró
      `arquitectura`, corre su `templates/conformidad-checklist.md` (fuente
      única — localizar con `Glob`) sobre el diff. Resumen no-normativo:
      dependencias hacia adentro · núcleo sin I/O (todo por puerto) · un puerto
      por integración (capacidad nueva = adaptador nuevo, núcleo sin tocar).
      Sin skill → N/A → verde.

## D2. Infra / contenedores (si la corrida tocó servicios desplegados)
- [ ] Ningún cambio quedó SOLO dentro de un contenedor (terminal = solo
      diagnóstico; un cambio in-container se pierde en el próximo redeploy).
- [ ] Todo cambio real está en la fuente de verdad (Coolify panel/API o repo
      de la app). Parche de emergencia por terminal → replicado ANTES del PASS.

## E. Integración (solo si hubo carriles paralelos)
- [ ] El resultado **combinado** de todos los carriles compila/pasa junto.
- [ ] Archivos compartidos coherentes (los administró el team-lead).
- [ ] CI serial verde sobre el merge combinado.

---
`PASS` ⇔ TODOS los ítems aplicables en verde. Cualquier otro caso ⇒ `FAIL`.
