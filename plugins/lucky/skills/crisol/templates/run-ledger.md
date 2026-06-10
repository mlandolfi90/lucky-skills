# RUN-LEDGER — historial de corridas del Crisol

> ADR 0010 (self-awareness) aplicado al meta-proceso. Lo mantiene el team-lead.
> El hook `crisol-enforcer` LEE este archivo: sin una entrada `STATUS: ACTIVE`
> cuyo `Branch:` sea el branch git actual, todo cambio de código fuente en un
> repo que adoptó el Crisol queda **bloqueado**.
>
> Formato de entrada (machine-checkable — respetar las claves exactas):

```
## RUN <run-id>
STATUS: ACTIVE | CLOSED | ESCALATED | BOOTSTRAP
Branch: <git-branch>
Tier: completo | fast-path
Alcance: <descripción corta>
Carriles: <dominio-A>, <dominio-B>
Planificador: <veredicto/resumen>
Arquitecto: APPROVE | REJECT (motivo)
Ingeniero: <archivos staged>
Verificador: PASS | FAIL (defecto archivo:línea)
Integración: PASS | FAIL | N/A
Iteraciones: <n>/3
Escalación: <none | detalle a Vikingo>
Cierre: <YYYY-MM-DD HH:MM> <commit-sha>
```

- `STATUS: ACTIVE` → corrida abierta; el código fuente del branch puede mutarse.
- `STATUS: CLOSED` → corrida cerrada con commit; nuevas mutaciones requieren
  abrir una nueva corrida.
- `STATUS: ESCALATED` → superó el techo (3 iteraciones); decide Vikingo.
- `STATUS: BOOTSTRAP` → excepción declarada (creación del propio Crisol).

---

## RUN 20260515-bootstrap
STATUS: BOOTSTRAP
Branch: <branch-de-creacion-del-crisol>
Tier: completo
Alcance: Creación del Crisol (skill + hook + ADR 0018 + gobernanza). Meta-cambio.
Carriles: governance (single)
Planificador: 3 Explore agents (ADR system / roles / infra) — grounding verbatim
Arquitecto: APPROVE — revisión directa Vikingo + team-lead (paradoja de bootstrap)
Ingeniero: team-lead (artefactos doc/config; sin código de feature)
Verificador: PASS — verificación end-to-end del hook + frontmatter + suite repo
Integración: N/A
Iteraciones: 1/3
Escalación: none
Cierre: <pendiente al commit del bootstrap>
