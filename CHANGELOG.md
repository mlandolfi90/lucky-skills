# Changelog — lucky-skills

Notas de release de la familia de skills Lucky. El historial completo del **proceso**
(corridas del Crisol, RETROs) vive en `docs/refactor/_crisol/RUN-LEDGER.md`; los tags
inmutables, en `git tag`. Formato: más nuevo arriba.

## v1.15.0 — 2026-06-27 — Invariante TARGET @env

El Crisol ahora **caza cuando un deploy aterriza en un entorno distinto al declarado**.
Origen: un deploy declarado `@dev` terminó en el entorno default del orquestador
(`production`) sin que el Crisol lo detectara — el `@env` del TARGET nunca se verificaba
contra el entorno REAL.

- **Regla `TARGET_ENV`** (matriz de veredictos): el `deploy-verifier` afirma
  `recurso.env == @env declarado`. **Dinámica** — una promoción a `@testing`/`@production`
  pasa; solo se caza la contradicción declarado↔real. `paas:` → chequeo por API;
  `local@<env>` → disciplina; sin `@env` / no-paas → N/A.
- **Esquema TARGET**: `@env` opcional en local (`docker-local@<env>`) para separar
  hot-dev de testing-estable.
- **Brújula**: bandera roja temprana (shift-left) si el recurso vive en otro entorno
  que el `@env`; el humano define el `@env`.
- **Apéndice de deploy**: invariante `entorno==@env`, auto-crear los 3 entornos al
  inicializar, trampa del "default = production", y **runbook de remediación agnóstico**.
- **ADR 0004**.

Crisol §6, Tier completo. Steward APPROVE (10 cond) + Verificador PASS. Re-sello de
familia **11/11 == v1.15.0**; firma minisign **diferida**.

## v1.14.0 — 2026-06-24 — Apéndice deploy build-once-promote

Nueva **referencia consultable** (en `arquitectura/references/`): el patrón de deploy
**build-once-promote**.

- Buildeás **una vez** en CI (con el test horneado en el build) y promovés la **misma imagen**
  `sha-<commit>`: el `<paas>` solo **pullea**, no buildea. Deploy de ~17 min a ~100 s.
- El deploy lo dispara el **job CI** (no el webhook), atado a `sha-<commit>` → atribución 1:1 commit↔imagen.
- Promoción `dev→testing→prod` = re-deploy de la **misma imagen** (no se rebuildea).
- **Agnóstico**: escrito en roles (`<paas>`/`<registry>`/`<secrets-vault>`/`CI`), reusable en
  cualquier stack. Incluye runbook, esqueletos y catálogo de footguns. Descriptivo, no normativo.

Generado bajo el Crisol (Steward APPROVE 8 cond + Verificador PASS, **zero-leak doble red**:
`leak-scan.sh` LIMPIO + 0/21 identificadores del piloto). `MODEL: opus` vía la Compuerta de
Modelo. Re-sello de familia **10/10 == v1.14.0**; firma minisign **diferida**.

## v1.13.0 — 2026-06-21 — Compuerta de modelo

El Crisol ahora **pregunta qué modelo usar** para los agentes ANTES de spawnear
(Paso 0, fail-closed).

- El líder **enumera en runtime** los modelos que el entorno ofrece
  (`opus`/`sonnet`/`haiku`/`fable`) + `default` — lista viva, no hardcodeada (patrón Ley viva).
- Elegís un alias → ese modelo para **todos** los agentes (uniforme).
- Elegís `default` → cada rol por complejidad (mecánico→`sonnet` · juicio→`opus` · síntesis→`fable`).
- Sin respuesta → **frena** (como el `TARGET`).

Se registra `MODEL:` en el ledger. **Enforcement por construcción**: la regla `MODEL`
en la matriz de veredictos hace que el gate de cobertura de v1.12.0 bloquee el cierre
sin `MODEL` — **cero código nuevo** (`crisol_gate.py` intacto). Decisión en **ADR 0003**.

Verificación: Steward APPROVE (5 condiciones) + Verificador fresco PASS (fixture
`tests/test-enforcer.sh` **50/50**, enforcement probado en vivo). Re-sello de familia
**10/10 == v1.13.0**. Firma minisign **diferida** (`--no-sign`).

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
