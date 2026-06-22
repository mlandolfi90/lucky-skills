# Changelog — lucky-skills

Notas de release de la familia de skills Lucky. El historial completo del **proceso**
(corridas del Crisol, RETROs) vive en `docs/refactor/_crisol/RUN-LEDGER.md`; los tags
inmutables, en `git tag`. Formato: más nuevo arriba.

## v1.12.0 — 2026-06-21 — Crisol endurecido

Las reglas del Crisol ahora se **verifican por agente** y el cierre es **fail-closed**:
ninguna corrida se cierra con reglas sin verificar. Origen: tres fallas reales —
codear en `pc-local` sin preguntar el TARGET, romper Open/Closed, romper el diseño atómico.

- **Matriz de veredictos** en el RUN-LEDGER: un veredicto binario (`PASS`/`FAIL`/`N/A`)
  por regla aplicable, con catálogo canónico de 23 IDs (`crisol/SKILL.md` §5).
- **Roster de verificadores-juez frescos** (`design` / `scope` / `leak` / `conformidad` /
  `responsive`): cada uno mira **solo el diff** y emite su veredicto a la matriz.
- **Gate de cobertura fail-closed** (`crisol_gate.py`): un commit de cierre
  (`runState: closing`) con la matriz incompleta o con cualquier `FAIL` se **bloquea**
  (exit 2). Distinción clave: `ausente = skip → fail-closed` vs `ilegible = bug → fail-open`.
- **Colocación shift-left**: cada regla se chequea en su punto más temprano decidible
  (Steward sobre el plan en el Paso 4; auditor sobre el diff en el Paso 6; el gate de
  cobertura como **red** al cierre, no como detector).
- **ADR 0002** documenta la excepción fail-closed acotada al principio fail-open global.

Verificación: Steward APPROVE (7 condiciones) + Verificador de Integración PASS
(fixture `tests/test-enforcer.sh` **50/50** en docker-local, contrato matriz↔gate probado
en vivo sobre el dogfood). Re-sello de familia **9/9 == v1.12.0**. Firma minisign
**diferida** (`--no-sign`): el loader es infra dormida y la Ley-viva no depende de la firma.
