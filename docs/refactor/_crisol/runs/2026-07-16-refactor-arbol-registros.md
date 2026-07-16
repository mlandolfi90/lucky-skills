---
id: 2026-07-16-refactor-arbol-registros
schema: corrida/1
tipo: corrida
estado: ACTIVE
creado: 2026-07-16
branch: main
titulo: "v2.0.0 — refactor árbol/registros: ledger por corrida + manifiesto + proyecciones"
tier: "completo (multi-archivo de código + cambia el patrón del sistema documental — la ley que viaja a la flota)"
target: "pc-local (Git-Bash del operador — forja la familia de skills; directiva del operador, debate 2026-07-16)"
model: "fable (uniforme — Compuerta del Paso 0 respondida por el operador en el debate)"
ley: "v1.41.0 (verificada contra remoto en esta sesión)"
iteraciones: "1/3"
runState: wip
veredictos: []
refs: [adr:0016]
---
- ORIGEN: debate operador↔agente 2026-07-16 (capturas en docs/IDEAS.md) + concejo de diseño (3 diseños · 3 jueces → ganador git-nativo-mínimo con injertos) + concejo 4-criterios (12 mejoras). PLAY del operador: "aplicar la refactorización por pasos atómicos, terminar sin mi intervención, commits atómicos para rollback, tag final con título y notas".
- Alcance: migración aprobada (Punto 5 del debate), commits atómicos C1..C8: [C1] ADR 0016; [C2] docs/registros.yaml + .gitattributes + scripts/registros-lint.py; [C3] congelar monolito → runs/_archivo-hasta-2026-07.md + runs/2026-07-16-refactor-arbol-registros.md + scripts/proyectar.py (RUN-LEDGER.md pasa a PROYECCIÓN legacy en el MISMO path — cero cambios en guardianes) + _ACTIVE + prueba de paridad; [C4] skill crisol abre corridas como registros (prosa); [C5] huérfanos → planes/ con frontmatter estado; [C6] forja sella corridas CLOSED (sha256 LF) + adoptar-crisol siembra manifiesto write-if-absent; [C7] roster de verificadores frescos; [C8] cierre + forja v2.0.0 + tag anotado + GitHub Release. FASE 2 del gate (guardianes leen frontmatter) = corrida FUTURA separada (decisión del debate: jamás juntas).
- MIGRATION_STRATEGY: N/A (sin DDL; migración de archivos reversible por commit atómico)
