# Registros de corrida — fila (fuente) + proyección (contrato del gate)

## La FILA — fuente de verdad (ADR 0016)

Una corrida = un archivo `docs/refactor/_crisol/runs/<YYYY-MM-DD-slug>.md`:

```
---
id: <YYYY-MM-DD-slug>        # = nombre de archivo → clave primaria; jamás se reusa
schema: corrida/1            # tipo/versión del formato
tipo: corrida
estado: ACTIVE               # ACTIVE → CLOSED | ESCALATED (inmutable al cerrar)
creado: <YYYY-MM-DD>
branch: <branch>
titulo: "<descripción corta>"
tier: "<completo|fast-path> (<justificación>)"
target: "<paas:<proyecto>/<app>@<env> | docker-local | pc-local> (<contexto>)"
model: "<alias> (uniforme) | default (frontera=X · alto=Y · económico=Z)"
ley: "<vX.Y.Z (verificada | local, sin verificar)>"
iteraciones: "<n>/3"
runState: wip                # wip | closing (closing SOLO en el commit de cierre)
veredictos: []               # [{regla: <ID §5>, veredicto: PASS|FAIL|N/A, quien: <rol>, evidencia: <archivo:línea|conteo>}]
refs: [adr:NNNN, bitacora:XXX-nnn]   # FKs tipadas <tabla>:<id>
cierre: "<YYYY-MM-DD HH:MM · commit <sha>>"   # al cerrar
---
- ORIGEN: <de dónde nace la corrida>
- Alcance: <qué se toca y por qué>
- MIGRATION_STRATEGY: <estrategia | N/A>     (obligatorio si el diff trae DDL)
- RETRO: <una línea sobre la fricción del PROCESO, al cerrar (blameless)>
```

Reglas: mutar la fila (veredicto, `runState`, cierre) exige regenerar las
proyecciones en el MISMO paso (`python scripts/proyectar.py`) y commitear
juntas. `RUN-LEDGER.md` y `_ACTIVE` son GENERADOS — editarlos a mano = drift
que el lint delata. Historia previa: `runs/_archivo-hasta-2026-07.md`
(congelada verbatim).

---

## La PROYECCIÓN — el contrato que los guardianes parsean (render de proyectar.py)

> ADR 0010 (self-awareness) aplicado al meta-proceso. Este formato legacy ya NO
> se escribe a mano: lo EMITE `scripts/proyectar.py` desde las filas (paridad
> probada por `tests/test-paridad.sh`). Sigue siendo contrato mientras dure la
> Fase 1 (los guardianes leen la proyección); la Fase 2 los enseñará a leer
> frontmatter y este render morirá.
> El hook `crisol-enforcer` LEE el ledger real (`docs/refactor/_crisol/RUN-LEDGER.md`):
> sin una entrada `STATUS: ACTIVE` cuyo **branch aparezca en el encabezado**
> `### <branch> — …` y que sea el branch git actual, todo cambio de código fuente
> en un repo que adoptó el Crisol queda **bloqueado** (exit 2). Docs/.md quedan exentos.
>
> Formato machine-checkable — el `awk` del enforcer exige LITERALMENTE: encabezado
> `### `, y los campos `- STATUS:`, `- Tier:`, `- Fecha:`, `- TARGET:` (con el guion
> inicial). El branch se matchea contra el encabezado (NO hay campo `Branch:` separado).

```
### <branch> — <YYYY-MM-DD> (<descripción corta, opcional>)
- STATUS: ACTIVE | CLOSED | ESCALATED | BOOTSTRAP
- Tier: completo | fast-path
- Fecha: <YYYY-MM-DD>
- TARGET: paas:<proyecto>/<app>@<env> | docker-local | pc-local   (dónde corre/verifica)
- MODEL: <alias> (uniforme) | default (por-rol)   (modelo de los sub-agentes; lo fija la Compuerta del Paso 0, fail-closed; la regla `MODEL` de la matriz exige su presencia al cierre)
- Alcance: <qué se tocó y por qué>
- MIGRATION_STRATEGY: <estrategia | N/A>     (obligatorio si el diff trae DDL)
- Conformidad-arq: PASS | FAIL (capa:archivo) | N/A
- Veredictos: <Planificador · Steward APPROVE|REJECT · Verificador PASS|FAIL · Integración>
- Iteraciones: <n>/3
- TEST_COVERAGE: <cobertura | NONE>
- Escalación: <none | detalle a MLL>
- BITACORA: <id(s) de entrada(s) destilada(s) a la Capa 4 | N/A>   (opcional, NO bloqueante; crisol §4 paso 8, Destilación)
- RETRO: <una línea sobre la fricción del PROCESO, al cerrar (blameless)>
- Cierre: <YYYY-MM-DD HH:MM> <commit-sha>
```

### Matriz de veredictos (machine-checkable — la consume `crisol_gate.py`)

DENTRO del bloque de corrida, COEXISTIENDO con `- Veredictos:` (la prosa de
veredictos NO se borra: la matriz la complementa, no la reemplaza). El gate de
cobertura parsea SOLO lo que está entre los delimitadores HTML; el `awk` del
enforcer per-repo los ignora (son comentarios HTML).

```
<!-- VEREDICTOS:BEGIN -->
- runState: wip | closing
- [V] <ID> · <PASS|FAIL|N/A> · <quién> · <evidencia>
- [V] <ID> · <PASS|FAIL|N/A> · <quién> · <evidencia>
<!-- VEREDICTOS:END -->
```

Donde:
- `runState`: `wip` durante las iteraciones; `closing` SOLO en el commit de
  cierre. Lo define Lane A, lo consume el gate de Lane B.
- `<ID>`: uno EXACTO del catálogo canónico (SKILL.md §5 — MAYÚSCULA_GUION_BAJO,
  sin abreviar). La matriz solo lista las reglas cuyo TRIGGER se cumple para el
  diff de la corrida (cobertura dinámica).
- `<PASS|FAIL|N/A>`: veredicto binario por regla. `N/A` SOLO si el trigger de la
  regla NO aplica a este diff.
- `<quién>`: `gate` (verificación determinista) o `<concern>-verifier` (rol-LLM).
- `<evidencia>`: `archivo:línea` o un conteo (ej. `tests/test-enforcer.sh:39/39`).
  SIN secretos (igual que el resto de los artefactos del Crisol).

- **Load-bearing:** estas líneas las parsea el gate de cobertura
  (`crisol_gate.py`) — el formato es tan rígido como `- STATUS:`. El delimitador
  `<!-- VEREDICTOS:BEGIN -->`/`<!-- VEREDICTOS:END -->`, el prefijo `- [V] `, los
  separadores ` · ` y el orden de los 4 campos NO son cosméticos. Con
  `runState: closing`, una matriz incompleta o con cualquier `FAIL` → exit 2 (no
  cierra). **Ausencia de veredicto para una regla con TRIGGER activo = FAIL** (no
  N/A): no listar una regla aplicable NO la exime. `N/A` vale SOLO cuando el
  trigger de la regla NO aplica al diff. Con `runState: wip` el gate no exige
  matriz completa (iteración en curso).

- **Ejemplo (lleno, corto):**
```
<!-- VEREDICTOS:BEGIN -->
- runState: closing
- [V] REGLA0 · PASS · gate · tests/test-enforcer.sh:39/39
- [V] OPEN_CLOSED · PASS · open_closed-verifier · SKILL.md:104 (todo AGREGAR)
- [V] TEST_COVERAGE · PASS · gate · tests/test-enforcer.sh:39/39
- [V] ZERO_LEAK · PASS · zero_leak-verifier · leak-scan:0/0/0
- [V] MIGRATION · N/A · gate · sin DDL en el diff
<!-- VEREDICTOS:END -->
```

- **Load-bearing:** el `###` del encabezado y el guion `- ` de cada campo NO son
  cosméticos — el `awk` los exige tal cual. Un encabezado `## ` o un campo sin
  guion (`STATUS:` en vez de `- STATUS:`) NO matchea y la corrida queda invisible
  para el hook → el código queda bloqueado aunque hayas abierto la corrida.
- **Campos MÍNIMOS que habilitan código:** `- STATUS: ACTIVE` + `- Tier:` +
  `- Fecha:` + `- TARGET:` (con valor real, no vacío ni `<placeholder>`). Una línea
  suelta con `ACTIVE`, o un bloque sin `TARGET`, no habilita nada (anti ticket-propio /
  anti verificar-a-ciegas): codear sin declarar DÓNDE corre se bloquea (exit 2).
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
