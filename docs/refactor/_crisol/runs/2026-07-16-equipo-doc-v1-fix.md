---
id: 2026-07-16-equipo-doc-v1-fix
schema: corrida/1
tipo: corrida
estado: CLOSED
creado: 2026-07-16
branch: main
titulo: "Fix-forward de equipo-doc-v1 — la cita de la rama + release v2.5.0"
tier: "fast-path (1 archivo, 1 línea, solución CONOCIDA y dictada por el scope-verifier; no toca contratos ni arquitectura)"
target: "pc-local (la forja; directiva explícita del operador)"
model: "fable (uniforme)"
ley: "v2.4.0 (verificada — git ls-remote: máximo remoto == sello local)"
iteraciones: "1/3 (convergió a la primera: la solución era conocida)"
runState: closing
cierre: "2026-07-16 · commit de cierre + forja v2.5.0 (sella las 2 corridas terminales) + tag anotado + GitHub Release"
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: líder, evidencia: "pc-local (la forja; directiva explícita del operador)"}
  - {regla: MODEL, veredicto: PASS, quien: líder, evidencia: "fable (uniforme)"}
  - {regla: REGLA0, veredicto: PASS, quien: quality-auditor, evidencia: "13/13 suites corridas por él en pc-local + proyectar --check drift 0 + verificación FUNCIONAL del hecho (sed 42p: la línea 42 ES la regla 5; la 41 no) + control anti-clone sobre las 13 suites"}
  - {regla: TEST_COVERAGE, veredicto: PASS, quien: quality-auditor, evidencia: "bitacora(4) cargar(1) crisol(6) ley(1) management(1) = 13 runners, 13 PASS, 0 FAIL, 0 timeouts"}
  - {regla: ZERO_LEAK, veredicto: PASS, quien: leak-verifier, evidencia: "0 secretos reales; barrido propio con chr(92) sobre 182 tracked: ghp_/sk-/AKIA/eyJ/xox/conn-string/IPs = 0. Los 3 hits de RUTA-ABSOLUTA eran ejemplos ficticios de nuestra propia documentación (falso positivo, no leak) — saldados por la excepción declarada; leak-scan post-fix = exit 0 LIMPIO"}
  - {regla: INDEPENDENCIA, veredicto: PASS, quien: líder, evidencia: "verificadores FRESCOS (quality + leak) sobre el diff staged; el líder no verificó su propio fix — y el leak-verifier le encontró el bloqueo del release que el líder no había visto"}
  - {regla: SCOPE_CREEP, veredicto: PASS, quien: líder, evidencia: "diff = 2 archivos de la cita + la fila + proyecciones; el ancla de texto se declaró explícito en el Alcance ítem 1 antes de verificar; el defecto de leak-scan NO se coló (sigue parkeado)"}
  - {regla: PARKING, veredicto: PASS, quien: líder, evidencia: "3 ideas en docs/IDEAS.md: defecto leak-scan:61 (con escalón sugerido) + fase PIN paso 0 + citar por línea entre carriles"}
  - {regla: CIERRE_TRAS_PASS, veredicto: PASS, quien: líder, evidencia: "commit de cierre tras PASS de los 2 verificadores frescos"}
  - {regla: TECHO_ITER, veredicto: PASS, quien: líder, evidencia: "convergió en 1/3 — la solución venía dictada por el scope-verifier de la corrida madre"}
  - {regla: MIGRATION, veredicto: "N/A", quien: gate, evidencia: "sin DDL"}
  - {regla: OPEN_CLOSED, veredicto: "N/A", quien: líder, evidencia: "fast-path sin código: el diff es prosa de ley (2 citas). El design-verifier no se spawnea (su TRIGGER es 'si toca código')"}
  - {regla: CONFORMIDAD, veredicto: "N/A", quien: líder, evidencia: "tooling sin capas"}
  - {regla: TARGET_ENV, veredicto: "N/A", quien: líder, evidencia: "pc-local sin @env"}
  - {regla: RESPONSIVE, veredicto: "N/A", quien: líder, evidencia: "sin UI"}
  - {regla: FUENTE_VERDAD, veredicto: "N/A", quien: líder, evidencia: "no toca testing/prod"}
  - {regla: PIN_TOTAL, veredicto: "N/A", quien: líder, evidencia: "el diff no toca dependencias"}
  - {regla: SELLOS, veredicto: PASS, quien: forja, evidencia: "pre-flight del universo SEALED replicado a mano: 51 archivos, 1 ancla c/u, 0 fallas; re-sello uniforme a v2.5.0 por forjar-release.sh"}
  - {regla: FORJA, veredicto: PASS, quien: forja, evidencia: "sellos+registry+sellado de corridas en UNA pasada por forjar-release.sh v2.5.0 — nada a mano"}
  - {regla: TAG_GATE, veredicto: PASS, quien: líder, evidencia: "v2.5.0 nace tras esta corrida CLOSED con PASS; la corrida madre queda ESCALATED y su trabajo viaja verificado por su propio roster"}
refs: [corrida:2026-07-16-equipo-doc-v1, adr:0021, concejo:2026-07-16-equipo-doc, plan:PLAN-equipo-doc-contratos]
---
- ORIGEN: `corrida:2026-07-16-equipo-doc-v1` cerró **ESCALATED** por techo (3/3)
  con un único FAIL del scope-verifier. El fix es conocido, de una línea, y NO se
  aplicó allá a propósito: hacerlo hubiera sido el workaround exacto que el techo
  prohíbe. El operador eligió el camino (1) — fix-forward — sobre la excepción de
  autor. La corrida ESCALATED no se reabre (§Fuente de verdad): esta es su
  sucesora con entrada `ACTIVE` propia y techo propio.
- Alcance (CERRADO — cualquier cosa fuera de esto es scope creep):
  1. `plugins/lucky/skills/feature/ramas/001-gate-de-doc.md:24` — la cita
     `manualizador.md:41` → `manualizador.md:42`. Causa: el carril A insertó
     `superseded_by:` (+1 línea) y corrió la referencia; la cita era correcta
     contra HEAD y falsa contra el árbol final. La rama es `canal: estable` y
     LIVE (ley que RUTEA), y esa cita es la única evidencia que sostiene la regla
     load-bearing del PIN 3 ("el nombre del llamador es el único de-ruteo").
     NOTA de fidelidad (declarada, para que el verificador no la lea como creep):
     la corrección no repone solo el número — ancla la cita por TEXTO ("su regla
     5, `manualizador.md:42`"). Es el antídoto que el RETRO de la corrida madre
     nombró: una cita por número puro vuelve a mentir la próxima vez que un
     vecino inserte una línea. Misma línea, mismo defecto, cero alcance nuevo.
  2. `docs/refactor/_crisol/planes/PLAN-equipo-doc-contratos.md:90` — el mismo
     arrastre (`:41` → `:42`). Es fila `plan` en estado VIGENTE (no terminal, no
     sellada): la corrección en el lugar es legal.
  3. Release **v2.5.0**: `forjar-release.sh` (re-sello uniforme + registry +
     sellado de las DOS corridas terminales) + tag anotado + GitHub Release.
  FUERA DE ALCANCE (heredado, sigue en pie): el agente `verificador-frescura`
  (ADR 0021 §8, YAGNI). Y el defecto de `leak-scan.sh:61` queda PARKEADO en
  `docs/IDEAS.md` — es un microfix propio con prueba negativa, no se cuela acá.
- EXCEPCIÓN DEL OPERADOR (declarada, no silenciosa) — mutación de fila TERMINAL:
  el leak-verifier halló que el release estaba BLOQUEADO por nuestra propia
  documentación: `leak-scan` (fail-closed dentro de la forja, `forjar-release.sh`
  :364-370) daba exit 1 sobre 3 artefactos. Ningún hit era un secreto — eran
  ejemplos FICTICIOS que la corrida madre introdujo AL DOCUMENTAR el defecto de
  `leak-scan.sh:61` (verificado: en el tag v2.4.0 no existían). Es exactamente la
  "lección v1.8.0 — re-leak al DOCUMENTAR un fix" que el propio scanner declara
  en su cabecera y no implementó. La ironía exacta: citar el regex roto literal
  disparaba la rama del regex roto.
  El nudo: `docs/IDEAS.md` es editable, pero `runs/2026-07-16-equipo-doc-v1.md`
  está ESCALATED = TERMINAL = inmutable por doctrina (`registros.yaml` §6-7).
  Agravante: arreglar el regex EMPEORA el bloqueo (al revivir la rama Windows, el
  ejemplo `C:`+`Users` de esa fila pasaría a matchear también).
  Presentado al operador con 2 caminos; eligió (1): **mutar la prosa de la fila
  terminal para usar placeholders `<usuario>`/`<otro>`**, en vez de aflojar un
  gate de seguridad para que acepte nuestra propia prosa.
  ALCANCE EXACTO de la mutación: 2 líneas de PROSA del bloque "HALLAZGOS NO
  BLOQUEANTES" (ítem 1). **Cero veredictos, cero hechos, cero campos del
  frontmatter, cero estado tocados** — el hallazgo dice lo mismo. La fila NO
  estaba sellada (el sello es el paso 4c de la forja, que aún no corrió), así que
  ningún sha256 se rompe y M8 no aplica. Evidencia: `leak-scan` pasó de exit 1
  (3 hits) a exit 0 (LIMPIO) sin tocar `scripts/leak-scan.sh`.
  DEUDA INTACTA: el defecto de `leak-scan.sh:61` sigue PARKEADO en `docs/IDEAS.md`
  como microfix con prueba negativa obligatoria. Esta excepción NO lo arregla ni
  lo tapa: lo deja igual de roto y igual de anotado — un path Windows de otro
  usuario se seguiría filtrando en silencio hasta que ese microfix corra.
- SELLO PENDIENTE (esperado, no es drift): `registros-lint.py` reporta 1 hallazgo
  — `sello FALTANTE: corrida:2026-07-16-equipo-doc-v1 esta ESCALATED pero no
  figura en sellos.json`. Es el estado normal entre el cierre y la forja: el
  sellador es el paso 4c de `forjar-release.sh`, que corre ANTES de su propio
  lint (4d) precisamente para que una corrida recién cerrada no aborte su propio
  release. El gate de esta corrida: lint POST-FORJA == 0.
- MIGRATION_STRATEGY: N/A (sin DDL)
- RETRO (blameless): el fast-path convergió a la primera porque la solución venía
  DICTADA por el scope-verifier de la corrida madre — el techo no se gastó en
  re-derivar lo ya sabido. Pero la corrida casi muere por un flanco que nadie
  modeló: **el gate de seguridad se disparó sobre la documentación del propio
  defecto que el gate no sabe cazar**. Dos lecciones con nombre, ambas
  parkeadas: (a) documentar un patrón CITÁNDOLO literal es re-introducirlo — los
  ejemplos van con placeholders `<asi>`, siempre (el scanner declara esta lección
  en su cabecera desde v1.8.0 y aun así nos mordió: una lección escrita en prosa
  que nadie mecaniza vuelve); (b) una fila TERMINAL puede quedar como rehén de un
  gate fail-closed — la doctrina de inmutabilidad no tiene válvula para el falso
  positivo, y hoy la válvula fue una excepción del operador. Candidato a regla:
  si el sello aún no se aplicó, la corrección de PROSA sin cambio de veredicto
  podría ser mutación legal declarada, en vez de excepción caso por caso.
  Nota de proceso honesta: el líder verificó el patrón mal DOS veces (el Bash
  tool come una capa de backslashes) y solo llegó a la verdad leyendo el ERE
  crudo del archivo y pasándolo al motor sin retipearlo — el mismo aviso
  metodológico que el leak-verifier había dejado escrito.
