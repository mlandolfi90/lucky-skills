# Changelog — lucky-skills

Notas de release de la familia de skills Lucky. El historial completo del **proceso**
(corridas del Crisol, RETROs) vive en `docs/refactor/_crisol/RUN-LEDGER.md`; los tags
inmutables, en `git tag`. Formato: más nuevo arriba.

## v1.35.0 — 2026-07-10 — skill nueva: hotfix — permiso de trabajo en caliente (ADR 0012)

Pedido del operador: "un mecanismo para iterar rápido conmigo en frente", con "hotfix versionados
con su resultado guardado". Diseño perfeccionado por enjambre adversarial (5 lentes × panel de
jueces: 30 hallazgos, 24 incorporados).

- **El carril:** UN permiso (entrada ACTIVE + `runState: wip` dentro del bloque VEREDICTOS + `BASE:
  <sha>`) para todo el hotfix — la ley ya lo bancaba, la skill lo coreografía. Solo mesa caliente
  (pc-local / docker-local / paas@dev). Matriz UNA vez, al cierre, con la solución.
- **Betas versionadas con resultado guardado:** vault en el repo con INTENTOS.md — fila por beta
  (versión · commit · hipótesis · cambio · veredicto ✓/~/✗ textual · evidencia), WIP-commit por cada
  bump (cada fila apunta al código exacto), árbol revertido a BASE entre hipótesis, ZERO_LEAK con
  scrub. Gramática de versión adaptada al artefacto (manifest de extensión no admite sufijos).
- **Disciplina anti-adivinanza** cableada desde la bitácora: 2 strikes ⇒ instrumentar (GREP-004),
  stamp confirmado o no hay veredicto (DRIFT-008), releer diff tras replace_all (GAP-008), preview
  con validación cruzada (FALSO-VERDE-003). Exención del techo: betas con operador ≠ iteraciones
  Crisol.
- **Cierre mecánico:** restore a BASE + diff de la solución (forward-only), re-clasificación de Tier
  sobre ese diff, cosecha por INTENSIDAD común a ambas ramas (≥3 filas o sin solución) con marca
  `cosechado:` anti-duplicados.
- Satélites: ADR 0012 · escenario cumplimiento de 3 niveles (batería ahora 4 skills, ~12 subagentes)
  · README y GUIA-SKILLS actualizados · idea MCP-vault a IDEAS (parking).

## v1.34.0 — 2026-07-10 — Bitácora: primera cosecha por INTENSIDAD real — 6 entradas nuevas al INDEX (16 → 22)

El mecanismo forjado en v1.33.0 se usó por primera vez con el caso que lo motivó. Del postmortem
popover-bleed (otra sesión: ~10 versiones y horas en UN síntoma) se destilaron 5 lecciones, más la
promoción de una señal confirmada. Endoso del operador: directo a **LIVE** ("soluciones reales").

- **GAP-007** — la caja mide de más con box-props propios en 0 → medí al HIJO (flex toma la altura
  del hijo más alto), no sigas reseteando al padre.
- **GREP-004** — dos fixes visuales fallidos ⇒ instrumentá (`getComputedStyle` +
  `getBoundingClientRect`) antes del tercero; adivinar quemó ~5 versiones, medir resolvió en un tiro.
- **FALSO-VERDE-003** — un preview de UI que normaliza defaults del entorno MIENTE: debe
  reproducirlos (UA + bleed de la página), jamás limpiarlos.
- **DRIFT-008** — content script se refresca con F5 de la PÁGINA, no con ↻ de la extensión →
  version-stamp doble (panel + consola) para distinguir fix-roto de script-viejo.
- **GAP-008** — `replace_all` pisa la línea que RECIÉN agregaste si matchea el patrón → releer a
  mano la región editada tras todo reemplazo masivo.
- **FALSO-VERDE-004** (promovida desde SENALES, usos: 2) — gate/lint con pipe en cadena `&&` queda
  enmascarado (el exit es el de `tail`) → capturar salida y chequear `$?` desnudo.
- Cross-links de familia "la página se filtra a UI light-DOM": GAP-006 ↔ GAP-007 ↔ FALSO-VERDE-003.
- Meta-ruido descontado con honestidad: el ×35 del log era de la sesión que forjó la bitácora; la
  evidencia real de esta cosecha es el postmortem, no el log. La lección 6 (Shadow DOM) no entra:
  es arquitectura del repo de la extensión.
- Colisión resuelta: otra sesión cosechó el mismo postmortem en paralelo (3 CANDIDATEs gruesas);
  ganó lo endosado LIVE con grano fino por síntoma, absorbiendo sus detalles únicos (orden del
  barrido, grep-invariante, gotcha `:root`→`:host`, commit de validación).

## v1.33.0 — 2026-07-10 — Bitácora: "el costo agudo ES evidencia" — modo intensidad (enmienda 3 ADR 0010)

Primer kaizen generado POR el propio sistema: otra sesión del operador quemó horas en un solo
síntoma (postmortem + FALSO-VERDE ×35 en UNA sesión), la cosecha lo demeritó por `≥2 sesiones`, y
esa sesión escribió el change-request completo bajo la ley. Ejecutado acá:

- **Doctrina (Capturar):** el costo agudo de UNA sesión ES evidencia para el INDEX (ya estaba
  latente en "gap >30min"); `≥2 sesiones` queda EXPLÍCITO como exclusivo de SENALES. Dos rampas al
  INDEX: cierre del Crisol (clásica) + cosecha por intensidad (hot-iteration sin Crisol).
- **Cosecha, dos modos:** FRECUENCIA (≥2 sesiones → borrador de SEÑAL) e INTENSIDAD
  (`x ≥ BITACORA_INTENSIDAD_UMBRAL`, default 10, en una sesión → ofrecer destilado a
  INDEX-CANDIDATE). El log prueba QUE dolió, no QUÉ: el contenido sale del postmortem; sin material,
  no se inventa. Endoso humano y descuento de meta-ruido en ambos.
- **Timbre:** línea nueva de intensidad (sin timbre, la intensidad repetiría el gap "¿quién avisa?").
- Tests: push 33/33 (5 nuevos: suena con x35, no confunde intensidad con puente, umbral default,
  override por env, env inválido→default).

## v1.32.0 — 2026-07-09 — maquina-scan: el AgentShield hecho en casa (auditor de ~/.claude, cero paquetes de terceros)

Decisión del operador: NO ejecutar el `npx ecc-agentshield` de terceros (violaría PIN_TOTAL y el
espíritu del stack). La capacidad se EXTRAJO de la copia auditada de ECC/AgentShield (MIT) y se
forjó propia en `management/scripts/maquina-scan.sh` — auditor determinista de la MÁQUINA
(`~/.claude`), hermano del leak-scan (que audita el repo).

- Categorías (100% código, sin juicio LLM): SECRETO-CON-VALOR · CLAVE-PRIVADA · HOOK-PELIGROSO
  (curl|sh, base64|sh, eval de red, rm -rf raíz/HOME) · BYPASS-PERMISOS → CRITICAL (exit 2);
  PERMISO-ANCHO · HOOK-NO-PORTABLE (DRIFT-007 ascendida a regla determinista) → HIGH (exit 1);
  MCP-SUPERFICIE → INFO. Severidades de reglas-comunes; gate-able.
- Zero-leak: el reporte JAMÁS imprime el valor hallado, solo severidad+categoría+archivo:línea.
- Reusa los patrones de secreto/clave del leak-scan (costura) + corrige el suyo para claves JSON
  (`"API_KEY":` con comilla de cierre — bug cazado por el fixture).
- Router en management/SKILL.md + §Auditar la máquina. Tests: test-maquina-scan 18/18 (cada categoría
  hit/no-hit, zero-leak, severidad, prosa-no-dispara, dir inexistente).
- **Hallazgo real en la primera corrida**: cazó un plugin legacy (`crisol-enforcer`) con `python`
  pelado no-portable en `~/.claude` — el propio bug de DRIFT-007, en la máquina del operador.

## v1.31.0 — 2026-07-09 — Señales: puente log↔SENALES en el timbre + cosecha on-demand (enmienda 2 ADR 0010)

Segunda tanda de absorción del sistema de instincts de ECC, con la escalera de frecuencia
terminando SIEMPRE en endoso humano:

- **Puente (bitacora-push.sh):** etiquetas del log del observador con ≥2 sesiones acumuladas y SIN
  señal formal en SENALES.md → línea nueva en el ⚖ JUICIO PENDIENTE proponiendo la cosecha. Donde
  ECC auto-promueve al cruzar confianza 0.7, acá el umbral PROPONE.
- **Cosecha (`/bitacora cosechar`, §Cosechar):** on-demand, solo operador: el agente borra
  BORRADORES de señal desde el conteo real del log (visto: N como evidencia), presenta uno a uno,
  y solo lo endosado se escribe. Con descargo explícito de meta-ruido.
- Sin absorber (sigue): decay automático y promoción sin humano.
- Tests: push 28/28 (3 nuevos del puente: propone sin SENALES, cuenta bien, calla si ya formalizada).

## v1.30.2 — 2026-07-09 — Portabilidad multi-OS: los hooks/gates funcionan en Windows Y Linux

Reporte del operador: los hooks/gates dieron error en una sesión Linux ("no están hechos para
Linux"). Repro confirmado en WSL Ubuntu (python3-only): `instalar-gate.sh` cableaba el gate global
con RUTA WINDOWS horneada + binario `python` pelado → `python: command not found`, exit 127. El
CÓDIGO del gate siempre fue portable; el cableado no.

- **instalar-gate.sh:** el comando cableado ahora es portable — `$HOME` por-OS, PRUEBA el intérprete
  (`for PY in python3 python; do "$PY" -c "" && exec …`) en vez de confiar en `command -v` (el stub
  de Microsoft Store existe en PATH sin funcionar: exit 49, cazado por humo en Windows), y fail-open
  (`[ -f "$GATE" ] || exit 0`) para que una sandbox Linux/web fresca sin install jamás se rompa.
  MIGRA cableados viejos in situ (los repos que corran `/ley` → `instalar-gate.sh` quedan portables
  solos). Ídem la instrucción de registro de TARGET en el mensaje del gate y en el template global.
- **Verificación REGLA 0 multi-OS:** batería completa en WSL Ubuntu (python3-only, mawk presente):
  enforcer 110/0 · push 25/0 · observar 11/0 · verify 11/0 · atomicidad 8/0 · lint 35/0 · stale
  20/20 + fail-open sin gate + paridad en Windows Git-Bash. Bonus: `[[:cntrl:]]` (fix v1.30.1)
  verificado también bajo mawk.
- **DRIFT-007** destilada (CANDIDATE): "existir en PATH ≠ correr" — cableado portable con
  prueba de intérprete + verificación en el otro OS antes de forjar.

## v1.30.1 — 2026-07-09 — Timbre de juicio: la cola de juicio humano ahora suena sola (enmienda ADR 0010)

Pregunta del operador: *"¿qué mecanismo hay para que el humano sepa que tiene que juzgar?"* — la
acumulación (v1.30.0) era automática pero la cola de juicio dependía de la memoria humana. Cambio
quirúrgico: `bitacora-push.sh` suma la sección **⚖ JUICIO PENDIENTE** (solo si hay algo que juzgar):
cuenta señales con `visto ≥ 2` en el log del observador + entradas CANDIDATE esperando endoso, e
instruye al agente a avisar al humano en su primera respuesta. Timbre ANTES de los patrones
(sobrevive al presupuesto). Cero juicio automático. `bitacora-observar.sh` gana `--print-log-dir`
(paridad de resolución del log probada por fixture, patrón ADR 0008). Tests: push 22/22 (10 nuevos,
con aislamiento del log real de la máquina) · observar 11/11 sin regresión.

## v1.30.0 — 2026-07-09 — Absorción ECC lote 1: bitácora push, cumplimiento, perfiles de guardianes, guía de autoría, reglas por lenguaje

Cinco piezas absorbidas de github.com/affaan-m/ECC (analizado a fondo en clon local), adaptadas a la
doctrina lucky y traducidas — orden del operador: "aplica todo lo que propusiste hasta el final".

- **Bitácora push (ADR 0010):** hook `SessionStart` inyecta el top-N LIVE del INDEX (cap 6 +
  presupuesto 2KB + off-switch `BITACORA_PUSH`, fail-open) — el patrón llega ANTES del tropiezo;
  hook `SessionEnd` observa señales deterministas del transcript a un log local (`--resumen` las
  agrega; alimenta SENALES a criterio humano — nada entra al catálogo solo). NO se absorbió el
  confidence-por-LLM ni la escritura automática (chocan con "sin evidencia real, NO entra").
  Tests: test-push 12/12 · test-observar 11/11.
- **Skill nueva `cumplimiento`:** audita que las skills SE CUMPLEN (conducta observable, no código):
  escenario → subagente fresco que no sabe que es test → clasificación por significado → veredicto
  binario → degradación por presión (favorable/neutro/adverso = independencia del prompt). Pilotos:
  brujula, idea, ley. Válvula: NO-CUMPLE repetido → endurecer prosa o promover a hook/gate.
- **Perfiles de guardianes (ADR 0011):** `CRISOL_GATE_PROFILE` = estricto (default) | aviso
  (diagnóstico completo con marcador, sin bloquear) | off. Inválido → estricto (fail-closed a
  dureza). Paridad gate↔enforcer probada por fixture nuevo (Grupo K, 17 casos → enforcer 110/0).
  Aflojar el perfil es acto del OPERADOR, jamás del agente.
- **docs/GUIA-SKILLS.md:** doctrina de autoría destilada (200-500 líneas, description-como-trigger,
  mostrar-no-declamar, anti-patrones en pareja, progressive disclosure, checklist) + auditoría de
  tamaños: ninguna skill exige compactación hoy (crisol = larga-legítima, precedente v1.28.0).
- **arquitectura crece 3 references** (Router + capas): `reglas-comunes.md` (inmutabilidad,
  boundaries, seguridad, TDD/AAA, review con severidades), `python.md` y `typescript.md`
  (idiomáticas, extienden la común) — curadas del `rules/` de ECC (MIT), solo el oro atemporal,
  umbrales como recomendación.

## v1.29.0 — 2026-07-09 — cargar: minisign RETIRADO — integridad sha256-only + pin por commit (ADR 0009)

Decisión del operador (dueño único del repo): *"eliminar minisign, sacar definitivamente; en algún
momento se volverá pero no quiero más fastidio con eso."* La firma ya estaba DIFERIDA/dormida (el
registry se forjaba con `--no-sign`, ningún `.minisig` commiteado) pero `cargar-fetch-verify.sh` la
EXIGÍA → la vía-dato del loader estaba estructuralmente rota. Este release la des-rompe:

- **cargar-fetch-verify.sh:** cadena sha256-only — bytes crudos `raw@commit` (HTTPS) + pin
  tag/commit del install (state.env) + `sha256 -c` por cuerpo. Fail-closed intacto: `exit ≠ 0` →
  nada entra al contexto. El modelo sigue sin computar ni transcribir hashes.
- **install-trust.sh/.ps1:** ya no anclan clave pública; solo fijan el pin (registry-url/tag/commit).
- **forjar-release.sh:** sin paso de firma ni `MINISIGN_*`; `--no-sign` queda no-op con aviso;
  limpia `.minisig` residuales.
- **test-verify.sh:** reescrito a la cadena sin firma — 11/11 PASS (tag/commit-mismatch, JSON roto,
  sha malformado, requires_tools, cuerpo adulterado, CRLF en cuerpo y en registry, invariante
  todo-reject ⇒ contexto vacío).
- **Prosa activa** (cargar/SKILL.md, detectar-runtime.md, crisol §forja, README, registry.schema):
  el texto dice lo que el código hace. Historia intacta (ADR 0001 marcado supersedido-parcial,
  no reescrito).
- **ADR 0009:** modelo de amenaza delta (riesgo repo-comprometido ACEPTADO — dueño único + 2FA) y
  criterio de reversa explícito (multi-operador / terceros / señal de compromiso / contenido
  ejecutable por vía-dato).

Suite verde: verify 11/11 · enforcer 93/0 (contra el gate del repo) · atomicidad 8/0 · bitácora 35 PASS + 20/20.

## v1.19.2 — 2026-07-02 — Bitácora: regla "sin evidencia real, NO entra" — el catálogo guarda solo lo confirmado

Decisión del operador al ver el resultado del panel v1.19.1: *"¿de qué sirve guardar algo que no
está confirmado que funcione?"* — CANDIDATE venía funcionando como depósito de teoría (las semillas
bootstrap del concejo). Se corrige la doctrina y el contenido:

- **Regla dura nueva (SKILL.md):** el catálogo guarda SOLO lo confirmado por el uso (evidencia
  verificable: sha/ledger/postmortem). La previsión/teoría va a `/idea` (parking). `CANDIDATE` pasa a
  ser una transición corta — evidencia real esperando endoso humano — no un almacén.
- **GREP-001 y GAP-001 RETIRADAS del catálogo** → parkeadas en `docs/IDEAS.md` con su condición de
  regreso escrita (GREP: crear el mapa Key Files + 1er uso real; GAP: el próximo spike que corra el
  patrón la destila de vuelta). Texto completo preservado en git history (`02820ee`).

El catálogo queda **4/4 LIVE** (DRIFT-001/002/003, GAP-002): todo lo que un agente consulte está
confirmado por la realidad. Lint 4/4 coherente · leak-scan LIMPIO. Re-sello == v1.19.2.

## v1.19.1 — 2026-07-02 — Bitácora: promociones por panel (delegación explícita del operador)

El operador delegó la decisión sobre las 4 CANDIDATE ("decide tú"). Panel de 12 jueces
independientes (3 lentes por entrada: evidencia real en los ledgers, calidad adversarial de
catálogo, predicción de la decisión del operador):

- **DRIFT-001 → LIVE (3/3)** — evidencia viva doble en el ledger (oráculo ciego v1.11.0;
  KeyError que dejaba el gate INERTE v1.12.0) + 3er uso HOY ("el INDEX que miente" → parió
  `bitacora-lint`). `usos: 3`, `validated_on` con sha real `54a9176`. La válvula de ascenso quedó
  anotada en NEXT: la mitad mecanizable YA ascendió (gate ADR 0002 + lint).
- **GAP-002 → LIVE (3/3)** — la acción se ejecutó y verificó en la realidad (cadena de commits del
  retiro del canary en el repo origen). + prevención enriquecida: GitHub auto-desactiva `schedule`
  tras ~60 días sin actividad (el mismo teatro por otra puerta).
- **GREP-001 queda CANDIDATE (3/3)** — bootstrap del concejo, 0 usos reales, y la acción prescribe
  un mapa (Key Files/MAPA.md) que ningún repo tiene todavía. NEXT con condición de promoción explícita.
- **GAP-001 queda CANDIDATE (2/1)** — el patrón tiene espejo real (la corrida S2d de auth-plane
  desriesgó su cutover con un spike) pero cero usos post-nacimiento. Fixes de calidad aplicados:
  umbral unificado, "spike-log" desinventado, dónde vive el código del spike, `validated_on`
  anclado al evento real (2026-06-21) y REFS al ledger de origen.

Anti-teatro respetado: promover solo lo probado; lo teórico madura con condición de salida escrita.
Lint 6/6 coherente · stale 0 · leak-scan LIMPIO. Re-sello == v1.19.1; firma minisign diferida.

## v1.19.0 — 2026-07-02 — Forja: gate de coherencia de la Bitácora (`bitacora-lint.sh`, fail-closed)

La bitácora duplicaba `estado`/`usos`/`validated_on` en dos lugares (la entrada y su fila del INDEX)
mantenidos a mano — nada detectaba cuándo el INDEX miente sobre las entradas (DRIFT-001 aplicado al
propio catálogo). Corrida autónoma (/goal del operador):

- **`bitacora/scripts/bitacora-lint.sh` (nuevo):** verificador mecánico read-only de coherencia:
  bijección INDEX↔`entries/` (huérfanas/fantasmas/duplicadas), título==ID, campos obligatorios de la
  plantilla, estado legal + espejado, `usos` y fecha espejados, ≤35 líneas por entrada, INDEX
  ordenado por `usos` desc. Exit 0/1; N/D fail-soft solo ante ausencia total de bitácora.
- **`forjar-release.sh` paso 4b (nuevo):** corre el lint tras el leak-scan, **fail-closed** — no se
  propaga por Ley viva un INDEX que miente a los ~21 repos. Frontera ADR 0005 intacta: el gate de
  COMMITS sigue sin bloquear por la Bitácora (esto solo frena la FORJA, igual que el leak-scan).
- **`tests/test-lint.sh` (nuevo):** 24 asserts (batería de mentiras + orden + catálogo-a-medias +
  dogfood sobre la bitácora real). Regresión test-stale 20/20 intacta.

Verificador fresco adversarial (11 ataques): ningún falso verde — todo fallo del lint aborta hacia
el lado seguro. 2 hallazgos menores parkeados en IDEAS.md. Re-sello == v1.19.0; firma minisign
diferida.

## v1.18.2 — 2026-07-01 — Bitácora: +GAP-002 (cron de Actions inerte fuera de la rama default) + cierre DRIFT-003

Segunda captura del mismo incidente de **Lucky-Auth-Plane** (cierre del postmortem, verificado en vivo)
+ refresh de DRIFT-003 con lo aprendido al cerrar:

- **GAP-002 (nueva, CANDIDATE):** agregás un workflow con `schedule:` (cron) y jamás corre — 0 runs,
  sin error visible. Causa: los cron de GitHub Actions corren SOLO desde la rama default; en un repo
  dev-only el canary queda INERTE (teatro de cobertura). Acción: el periódico va a un scheduler
  independiente de la rama (watchdog / monitor externo), NO a Actions. Origen: el repo origen agregó
  su canary y lo RETIRÓ al descubrir esto — ingeniería honesta que ahora es patrón de la familia.
- **DRIFT-003 (refresh, usos 2, sigue LIVE):** fix verificado EN VIVO (GET público → 200, antes 000)
  → `validated_on` con sha real (`6660073`). Prevención actualizada: (b) guarda de CI portable
  (`compose-guard.yml`: FALLA si `traefik.docker.network` usa `${...}`) aplicada en el repo origen;
  (d) HECHA — auditoría read-only de los ~21 repos: el label vive SOLO en 3 (el origen ya literal en
  su rama de deploy; los otros 2 aún `${...}` en `main`).

Re-sello de la familia == v1.18.2; firma minisign diferida.

## v1.18.1 — 2026-07-01 — Bitácora: +DRIFT-003 (portal healthy pero caído → label traefik literal)

Captura **cross-repo** (sobre v1.18.0) a la bitácora de un postmortem real de **Lucky-Auth-Plane**
(diagnóstico read-only, sin tocar prod):

- **DRIFT-003:** el PaaS reporta `running:healthy` pero la app no responde de afuera (`curl` →
  000/timeout — cuelgue, **no 503**) tras un reload del proxy. Causa: el label
  `traefik.docker.network: ${VAR:-}` no se interpola → el proxy elige una red inalcanzable. **Fix:**
  label a valor **LITERAL** + redeploy ("Restart Proxy" solo maquilla, deja la bomba armada).
  Prevención: check sintético externo end-to-end + prohibir `${VAR:-}` en labels de red críticos +
  auditar los otros repos con el mismo esquema PaaS+compose.

Entrada **LIVE** (endosada por MLL). Verificador fresco: leak/calidad/scope PASS. Re-sello 14/14 ==
v1.18.1; firma minisign diferida.

## v1.17.2 — 2026-06-28 — Bitácora: +DRIFT-002 (CSRF login vencido tras redeploy → PRG)

Captura **cross-repo** a la bitácora de un aprendizaje real de **Lucky-Auth-Plane** (que vivía en su
rama `dev`, sin llegar a la bitácora ni a otros repos):

- **DRIFT-002:** tras un redeploy, loguear al portal da `{"detail":"csrf token invalid"}` (el token
  CSRF del form vive ~15 min) y el hard-reload no recupera. **Fix:** Post/Redirect/Get — ante CSRF
  inválido en un FORM → **303** a `GET /login?expired=1` (cookie+token frescos); 403 JSON solo para API.

Entrada LIVE (promovida por MLL). La Ley viva la propaga a los 21 repos: el próximo portal con CSRF
+ redeploys la recibe al planear. Re-sello 13/13 == v1.17.2; firma minisign diferida.

## v1.17.1 — 2026-06-28 — Bitácora: consulta pull/on-demand (no push)

Ajuste pedido por MLL por **economía de ventana de contexto**, rebasado sobre v1.17.0. La consulta
de la bitácora pasa de **push** (la brújula surfaceaba 1-3 entradas al anclar — token-caro, mal
matcheado) a **pull / on-demand**:

- **Brújula**: la 5ta fuente es ahora un **puntero liviano** — solo SEÑALA que la bitácora existe,
  no carga contenido.
- **Crisol**: el Planificador (Paso 3 + fast-path) **grepea por el SÍNTOMA de la tarea** justo antes
  de planear → recall garantizado (paso del flujo), pull barato y bien-matcheado. Sin filtros duros:
  el síntoma es el filtro, no hay "dominios".
- **ADR 0005**: refinado (push→pull + nota de Revisión), alineado con la divulgación progresiva de
  las Agent Skills.

Planificado por concejo de 5 Opus. Crisol Tier completo: verificador fresco, 2 iteraciones (iter 1
cazó 2 residuos del modelo push en el ADR), 0 FAIL. Re-sello 13/13 == v1.17.1; firma diferida.
(Reemplaza el v1.16.2 abortado: main había avanzado a v1.17.0 independientemente; este cambio se
rebasó encima.)

## v1.17.0 — 2026-06-28 — REGLA 0: el gate-test va horneado en el CI, no en el VPS

Clarificación dura de **REGLA 0** (jidoka) para builds de imagen: la suite de tests se hornea
en el stage `test` del Dockerfile multi-stage y corre DURANTE el build del `CI` (runner Linux =
entorno fiel del TARGET). El build vive en el `CI` (build-once-promote); **NO se pre-buildea en
el `<vps>`** (`scp` + `docker build` local) — era redundante con el stage `test` del `CI` y
cargaba el server. El Verificador satisface REGLA 0 observando el stage `test` verde en el `CI`
(gate determinista, no reporte ajeno) + la provenance (imagen desplegada == `sha-<commit>` del
`CI`) + su verificación **funcional/e2e propia** contra el artefacto. Único build fuera del
`CI`: minutos del `CI` agotados (fallback).

- `crisol/SKILL.md` §2: sub-cláusula de REGLA 0 (builds de imagen → gate horneado en el `CI`).
- `arquitectura/references/deploy-build-once-promote.md` §9: footgun (pre-build en el `<vps>` = redundante).

Origen: corrida real (operador) donde el pre-build en el `<vps>` metía relay de desarrollo sin
valor — el stage `test` del `CI` ya es el gate. Feedback: "no se buildea nunca en el VPS salvo
que se acaben los minutos de CI". Firma minisign **diferida** (consistente con v1.16.1).

## v1.16.1 — 2026-06-28 — Fixes de la skill `bitacora` (review adversarial)

Review adversarial (12 reviewers + 7 verificadores) sobre la skill `bitacora` recién nacida:
23 hallazgos crudos → 15 confirmados → **12 arreglados**, 1 parqueado (pre-existente).

- **Validador de fechas (`bitacora-stale.sh`)** — los bugs más serios del reloj de validez:
  - Anclaje a **UTC** (`date -u -d`): cruzando un cambio de DST, el cálculo daba un veredicto STALE
    distinto según el huso horario del runner (no-determinismo del corazón de la skill).
  - Parser **anclado al bullet** y fecha tomada **después del primer `·`**: un branch fechado
    (`release-2026-01-01`) o una mención en prosa ya no engañan la extracción.
  - `--umbral` valida numérico (un typo ya no se traga el directorio); `gdate` en BSD/macOS;
    `RETIRED/SUPERSEDED` case-insensitive.
- **Tests** (8/8 → **20/20**): +DST cross-TZ, +branch-fechado, +umbral no-numérico, +fecha-ilegible,
  +directorio-inexistente.
- **Entradas semilla**: `estado: LIVE` → `CANDIDATE` (la skill dogfoodea su propia regla: el agente
  destila CANDIDATE, el humano promueve LIVE).
- **Prosa**: brújula §Uso (script = 3 fuentes; 4-5 agent-driven + Glob para localizar el INDEX
  cross-repo); ADR 0005 ("read-only" → consumo read-only / escritura por Crisol); ref `§8` → `§4 paso 8`.

Crisol Tier completo: 2 verificadores frescos (opus), **0 FAIL**, iteración 1. Re-sello 13/13 ==
v1.16.1; firma minisign **diferida**.

## v1.16.0 — 2026-06-28 — Skill `bitacora`: Capa 4 experiencial

Nace **`bitacora`**, un catálogo de patrones *"cuando ves SÍNTOMA X → hacé ACCIÓN Y"*
**indexado por síntoma observable**, para sortear **gaps/greps/drifts** sin re-derivar.
Complementa al Crisol; no lo reemplaza. **Principio rector: la brújula LEE, el Crisol
ESCRIBE.** Producto de una investigación (15 investigadores) + concejo (10 Opus)
sintetizado en blueprint, y aterrizado a la infra real de la familia.

- **Skill `bitacora`** read-only auto-invocable (dispatcher liviano): grep del `INDEX.md`
  por síntoma → entrada lazy → devuelve SOLO la línea de acción (*compass, not encyclopedia*).
- **Taxonomía** centrada en el dolor: `GAP` · `GREP` · `DRIFT` · `FALSO-VERDE` (el verde
  que miente — failure-mode dominante de la familia). 3 entradas semilla agnósticas.
- **Anti-pudrición mecánico**: `bitacora-stale.sh` marca STALE toda entrada con
  `validated_on` > 90 días o ausente (read-only, fail-soft, `--today` inyectable; test 8/8).
- **Brújula**: nace la **5ta fuente "Bitácora"** (prosa) — empuja 1-3 entradas relevantes
  al anclar, ANTES de grepar. `brujula.sh` intacto.
- **Crisol**: sub-paso **"Destilación"** al cierre (captura por dolor objetivo: gap >30min /
  grep re-derivado / drift) — el Crisol **AVISA, no exige** (fiel al jidoka) + campo `BITACORA:`
  en el ledger.
- **ADR 0005**. NO toca los guardianes (`crisol_gate.py`/`crisol-enforcer.sh`/`test-enforcer.sh`).

Crisol Tier completo: 5 verificadores frescos (opus), **0 FAIL**, iteración 1. Re-sello de
familia **13/13 == v1.16.0**; registry con `bitacora`; firma minisign **diferida**.

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
