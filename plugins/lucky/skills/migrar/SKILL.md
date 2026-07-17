---
name: migrar
description: >-
  Migrar — retrofit de un repo que NO nació bajo la ley 2.0 (ADR 0020).
  Disparar con "/migrar", "ordená este repo", "poné este repo bajo el sistema
  de registros", o cuando la brújula/lint reporte un repo adoptado con ledger
  legacy o huérfanos. Inventaría el desorden real, CLASIFICA cada artefacto
  contra registros.yaml (¿fila? ¿narrativa? ¿config? ¿basura?), propone el
  mapeo completo y ESPERA EL ENDOSO del operador (decisión convocable) antes
  de mover NADA. Congela monolitos verbatim; termina con registros-lint en 0.
  Complementa a adoptar-crisol.sh: la adopción SIEMBRA lo nuevo — esta skill
  ORDENA lo viejo. NO usar en repos ya conformes (lint 0) ni para mover
  archivos sin endoso humano.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Migrar — ordenar lo que nació antes de la ley

La adopción siembra write-if-absent y JAMÁS pisa lo viejo (un ledger legacy
queda intacto). Este es el otro brazo: el retrofit deliberado, con juicio y
endoso, de todo lo que quedó tirado — la generalización de la corrida 0016
que migró esta misma fábrica.

**Ejes:** primero inventario, después juicio · el operador ENDOSA el mapeo
antes de que un archivo se mueva · la historia se congela, no se convierte ·
termina verificable (lint 0).

## Procedimiento

1. **Preparar**: correr `adoptar-crisol.sh` si el repo no está adoptado
   (siembra manifiesto + tools sin pisar nada). Corrida Crisol propia para el
   retrofit (es multi-archivo por definición).
2. **Inventariar** (read-only): `git ls-files` + scan del working tree —
   listar TODO lo que el lint marca (huérfanos, sin frontmatter, monolitos) y
   lo sospechoso fuera de tablas (docs sueltos, scripts sin dueño, evidencia
   de tests, caches). Nada se toca.
3. **Clasificar**: spawnear el agente canónico `migrar-clasificador`
   (`plugins/lucky/agents/migrar-clasificador.md`, prompt que se LEE) — por
   cada artefacto propone UNA de: `fila de <tabla> (+frontmatter propuesto)` ·
   `narrativa` · `config` · `congelar (monolito/histórico)` · `basura
   borrable` · `mover a scripts//tests//e2e-artefactos`.
4. **Proponer y ENDOSAR**: el mapeo completo se presenta como **decisión
   convocable** (rama crisol/003): fila `decision` PROPUESTA con la tabla
   artefacto→destino. El operador acepta, ajusta o rechaza POR ESCRITO.
   **Sin endoso no se mueve NADA** — un clasificador puede equivocarse; el
   operador es el dueño del taller.
5. **Ejecutar el mapeo endosado**, en commits atómicos por clase:
   - monolitos (ledgers/logs legacy) → congelar VERBATIM como
     `_archivo-*.md` de su tabla (la historia no se convierte — ADR 0016);
   - huérfanos con destino de tabla → mover + frontmatter mínimo
     (id/schema/tipo/estado/creado + nota de retrofit);
   - narrativa/config → declarar en `registros.yaml` del repo;
   - basura endosada como tal → borrar (queda listada en la fila de la
     corrida — borrar también es decisión registrada);
   - regenerar proyecciones en el MISMO commit (regla transaccional).
6. **Verificar**: `registros-lint.py` en 0 + `proyectar.py --check` en 0 +
   suite del repo si existe. Cerrar la corrida con la matriz.

## Reglas duras

- **Endoso previo o nada** (paso 4). La propuesta es barata; deshacer un
  mal movimiento masivo no.
- **Congelar > convertir**: contenido histórico jamás se reescribe al formato
  nuevo — se archiva verbatim y las filas nuevas nacen filas.
- **Secretos**: si el inventario encuentra material sensible suelto (el
  hallazgo real que motivó esta skill incluía un `ALL-SECRETS-*.md` en un
  escritorio), se reporta al operador COMO PRIMERA PRIORIDAD, no se mueve ni
  se borra sin su instrucción — y jamás se transcribe su contenido.
- **Un repo por corrida**: el retrofit de N repos son N corridas (rollback
  por repo).

---
**Fuente: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.7.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene tag
mayor, seguir la del repo. Caso skill nueva: si el tag mayor no incluye
`migrar/`, tratar como sin-red y registrar `LEY: <tag> (local, skill nueva)`.
