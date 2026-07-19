---
id: PLAN-versionado-artefactos
schema: plan/1
tipo: plan
estado: EJECUTADO
creado: 2026-07-19
refs: [corrida:2026-07-19-versionado-artefactos, adr:0018, adr:0014, adr:0016, adr:0024, adr:0025, adr:0026]
nota: "Un solo carril (rama 004 y hotfix §4 comparten el contrato del 4to segmento: partirlo sería el REJECT de 'dos planes sobre el mismo contrato'). Primer plan bajo la regla de supuestos (ADR 0025, estrenada acá)."
---
# Plan — corrida `2026-07-19-versionado-artefactos`

Spec del operador (2026-07-19) optimizada y endosada. Un carril, cinco actos:

**A. ADR 0026** (`docs/decisions/0026-versionado-lectura-del-proceso.md`) — la
DECISIÓN: la versión de un artefacto es lectura del proceso,
`generacion.corridas.hotfixes.microfixes`, contadores ACUMULADOS (sin reset a
la derecha: con reset dos versiones distintas se ven iguales); commit por
entrega NO se re-legisla (ya es ley dura en hotfix §El registro, :119-127 — se
referencia); conflicto con hotfix §4 resuelto por opción (a): las betas SON
entregas-para-probar. Formato de 0024/0025, estado ACEPTADA.

**B. Rama `crisol/ramas/004-versionado-artefactos.md`** — la regla OPERATIVA
(formato rama/1 de 001-003; canal: estable — ley endosada por el operador,
ADR 0018 §2; gatillo: "¿qué versión le pongo a esta entrega/artefacto?").
Contenido: los 4 segmentos con sus disparadores; fuente de verdad derivable
(seg 2 = `runs/` CLOSED — NO sellos.json; seg 3 = `hotfixs/` CLOSED; seg 4
mitad microfix = `microfixes/` FAVORABLE; seg 1 y entregas = disciplina
declarada, flag `GENERACION: bump` en la fila de corrida con evidencia
objetiva); ambigüedades cerradas (ESCALATED no cuenta; sonda NO_FAVORABLE no
cuenta; nacimiento 0.0.0.0; rige de acá en adelante); mapeo por ecosistema
(extensión/PEP 440/tag git = 4 enteros tal cual, cap 65535 con una frase
defensiva; semver-de-3 estricto = la lectura vive en commit+ledger, se cruza
ese puente cuando exista; descartados +build y -prerelease); deslindes de una
línea vs TAG_GATE, SELLOS y PIN_TOTAL; ejemplo trabajado de la jornada
(1.12.4.16 → 2.13.4.27: 11 entregas, una corrida PASS, un bump de storage).

**C. `hotfix/SKILL.md` §4** (:93-98) — caso legal: extracción-a-rama (ADR
0018 §5, el tronco adelgaza — NO caso (b) costura: el contador "reaparece" en
la 004 y el mecanismo DESAPARECE lo leería como relocalización). Deja de
DEFINIR el contador: puntero a la rama 004 + conserva SOLO el aterrizaje por
ecosistema MARCADO EXPLÍCITO como expresión ("cómo se expresa — la semántica
vive en la rama 004"); el grep del acto E lo whitelistea como "apunta, no
define" (`X.Y.Z.N` /
`X.Y.Z-b.N` / `X.Y.ZbN`) y el stamp humano visible `vX.Y.Z-bN`.

**D. `hotfix/SKILL.md` §Cerrar paso 5** (:232) — caso legal: corrección
acoplada acreditada por ADR 0026 (la semántica acumulada vuelve FALSA la
frase vieja). Reescribir «Versión final SIN
sufijo beta»: bajo contadores acumulados la beta NO se cae al cerrar — el
número queda donde la última entrega lo dejó; lo que marca el cierre es la
fila del `Bug-` en CLOSED y la corrida de formalización, no un decremento
cosmético del string. El stamp humano `-bN` sí desaparece de la UI (era
etiqueta de prueba, no parte del contador).

**E. Verificación transversal** — grep de "cuarto segmento"/"X.Y.Z.N" en todas
las skills: UNA definición (rama 004), las demás apuntan. El bloque
RAMAS:BEGIN de crisol lo regenera `proyectar.py` (no a mano).

Sin código ejecutable nuevo: cero tests nuevos (la regla es prosa normativa;
el diente mecánico llegará cuando un repo real la adopte — decisión de la
spec, "disciplina, no maquinaria prematura").

## Supuestos del plan (ADR 0025 — tope 5, solo load-bearing)

1. **La rama 004 puede nacer `canal: estable`** — porque la regla ya fue
   endosada por el operador (spec presentada y orden de lanzar), y ADR 0018 §2
   dice que ley endosada nace estable. Si fuera falso (endoso de spec ≠ endoso
   de rama), la rama nace en cuarentena y no rutea. — Fundamento: precedente de la rama
   003 (nace estable por endoso REGISTRADO, ADR 0019 §2); zanjado por el
   operador: su spec endosada dice textual "nace estable por endoso
   registrado" y la orden de lanzar lo ratifica.
2. **`docs/hotfixs/` vacío en TODA la flota** — no hay `Bug-*.md` legado cuyo
   numerado de betas cambie de significado. Si fuera falso, hace falta nota de
   migración. — Fundamento: no existe en lucky-skills (verificado); los repos
   de producto adoptaron el Crisol después de esta ley.
3. **`proyectar.py` regenera el bloque RAMAS de crisol al agregar la rama 004
   con frontmatter válido** — sin tocar el bloque a mano. Si fuera falso, el
   bloque se edita a mano y viola el marcador GENERADO. — Fundamento: el
   marcador del bloque lo dice; 001-003 entraron así.
4. **El aterrizaje por ecosistema en hotfix §4 no duplica la norma** — es
   "cómo se expresa", no "qué significa" (la semántica queda solo en 004). Si
   fuera falso (el Steward lo lee como definición duplicada), C se reduce a
   puntero seco y el aterrizaje se muda a la rama. — Fundamento: la regla del
   repo es "una define, la otra apunta"; expresar ≠ definir.
5. **Ningún consumidor parsea hoy el string de versión de un artefacto de
   producto** — cambiar la semántica del número no rompe ningún awk/regex de
   la forja (el único parseo de versiones en lucky-skills es sobre tags
   `vX.Y.Z` de la LEY, que no se tocan). Si fuera falso, F5-style fixture
   antes de esta corrida. — Fundamento: deslinde TAG_GATE/SELLOS; grep de la
   cosecha F5 no halló consumidores de versiones de producto en la forja.

**Corregime ahora o sigo con esto.**
