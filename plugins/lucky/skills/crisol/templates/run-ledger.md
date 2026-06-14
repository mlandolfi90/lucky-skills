# RUN-LEDGER — historial de corridas del Crisol

> ADR 0010 (self-awareness) aplicado al meta-proceso. Lo mantiene el team-lead.
> El hook `crisol-enforcer` LEE el ledger real (`docs/refactor/_crisol/RUN-LEDGER.md`):
> sin una entrada `STATUS: ACTIVE` cuyo **branch aparezca en el encabezado**
> `### <branch> — …` y que sea el branch git actual, todo cambio de código fuente
> en un repo que adoptó el Crisol queda **bloqueado** (exit 2). Docs/.md quedan exentos.
>
> Formato machine-checkable — el `awk` del enforcer exige LITERALMENTE: encabezado
> `### `, y los campos `- STATUS:`, `- Tier:`, `- Fecha:` (con el guion inicial).
> El branch se matchea contra el encabezado (NO hay campo `Branch:` separado).

```
### <branch> — <YYYY-MM-DD> (<descripción corta, opcional>)
- STATUS: ACTIVE | CLOSED | ESCALATED | BOOTSTRAP
- Tier: completo | fast-path
- Fecha: <YYYY-MM-DD>
- Alcance: <qué se tocó y por qué>
- MIGRATION_STRATEGY: <estrategia | N/A>     (obligatorio si el diff trae DDL)
- Conformidad-arq: PASS | FAIL (capa:archivo) | N/A
- Veredictos: <Planificador · Steward APPROVE|REJECT · Verificador PASS|FAIL · Integración>
- Iteraciones: <n>/3
- TEST_COVERAGE: <cobertura | NONE>
- Escalación: <none | detalle a MLL>
- RETRO: <una línea sobre la fricción del PROCESO, al cerrar (blameless)>
- Cierre: <YYYY-MM-DD HH:MM> <commit-sha>
```

- **Load-bearing:** el `###` del encabezado y el guion `- ` de cada campo NO son
  cosméticos — el `awk` los exige tal cual. Un encabezado `## ` o un campo sin
  guion (`STATUS:` en vez de `- STATUS:`) NO matchea y la corrida queda invisible
  para el hook → el código queda bloqueado aunque hayas abierto la corrida.
- **Campos MÍNIMOS que habilitan código:** `- STATUS: ACTIVE` + `- Tier:` +
  `- Fecha:`. Una línea suelta con `ACTIVE` no habilita nada (anti ticket-propio).
- `STATUS: ACTIVE` → corrida abierta; el código fuente del branch puede mutarse.
- `STATUS: CLOSED` → corrida cerrada con commit; nuevas mutaciones requieren
  abrir una nueva corrida.
- `STATUS: ESCALATED` → superó el techo (3 iteraciones); decide MLL.
- `STATUS: BOOTSTRAP` → excepción declarada (creación del propio Crisol).
- **Invariante:** exactamente UNA entrada `ACTIVE` por branch.

> Fast-path: basta el bloque mínimo (encabezado + STATUS/Tier/Fecha). Los demás
> campos se completan al cerrar. La suite `tests/test-enforcer.sh` es la fuente
> única de verdad de QUÉ formato acepta el hook — este template la espeja.

---

### <branch-de-creacion-del-crisol> — 2026-05-15 (bootstrap del Crisol)
- STATUS: BOOTSTRAP
- Tier: completo
- Fecha: 2026-05-15
- Alcance: creación del Crisol (skill + hook + ADR 0018 + gobernanza). Meta-cambio.
- MIGRATION_STRATEGY: N/A
- Veredictos: Planificador 3 Explore agents (ADR / roles / infra, grounding verbatim) ·
  Arquitecto APPROVE (revisión directa MLL + team-lead, paradoja de bootstrap) ·
  Verificador PASS (hook + frontmatter + suite repo, end-to-end) · Integración N/A
- Iteraciones: 1/3
- Escalación: none
- Cierre: <pendiente al commit del bootstrap>
