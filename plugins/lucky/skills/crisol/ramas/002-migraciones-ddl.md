---
id: 002-migraciones-ddl
schema: rama/1
tipo: rama
estado: LIVE
canal: estable
creado: 2026-07-16
skill: crisol
gatillo: "el diff incluye DDL destructivo (ALTER, DROP, CREATE TABLE) o cualquier migración de schema"
origen: "extraída del tronco crisol §2 (ley ya endosada que solo se muda — nace estable, ADR 0018 §2)"
ultima_validacion: corrida:2026-07-16-ramas-agentes-canonicos
refs: [adr:0018]
---
# Migraciones de schema — MIGRATION_STRATEGY o REJECT

Si el cambio incluye DDL destructivo (ALTER, DROP, tabla nueva), el
Planificador registra en la fila de la corrida:

```
MIGRATION_STRATEGY: reversible | irreversible + <estrategia>
```

Sin ese campo → `REJECT` automático del Steward.

**Rollback por tag NO des-migra datos.** Ante migración irreversible decide el
humano; tras su decisión:
- **fix-forward** → corrida nueva;
- **revertir la DB** → la ejecuta el humano (el código acompañante = corrida
  nueva);
- **rollback solo de código** → re-deploy del tag estable anterior.

---
**Fuente: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.6.0` (cache local, NO la ley).**
