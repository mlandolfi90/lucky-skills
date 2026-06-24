# RUN-LEDGER — lucky-skills (la ley bajo su propia ley)

### main — 2026-06-11
- STATUS: CLOSED
- Tier: completo
- Fecha: 2026-06-11
- Alcance: forja v1.0.0 — SKILL.md de crisol endurecido (3 rondas adversariales:
  31→10 y 59→38 hallazgos confirmados/aplicados, 42 refutados), brujula
  trunk-based + último tag + detección de corrida-a-medias, hook con validación
  de campos mínimos, fixture de test del hook, crisol-pulso, auditor-checklist
  sin-stdout. Corrida 0: la versión sin tag juzga el diff que crea v1.0.0 (§6).
- MIGRATION_STRATEGY: N/A (sin DDL)
- Veredictos: Steward APPROVE (síntesis de 104 agentes adversariales en 3
  rondas) · Verificador PASS (test-enforcer 7/7 verde, corrido por el
  verificador mismo) · smoke brujula PASS (bug de extracción de branch cazado
  y corregido EN la verificación).
- Iteraciones: 3 (corona → núcleo solar → síntesis)
- TEST_COVERAGE: hooks (tests/test-enforcer.sh)
- RETRO: cisma de formatos entre enforcers — el gate global (crisol_gate.py,
  formato `STATUS:`/`Branch:`) y el hook del skill (crisol-enforcer.sh, formato
  `###`/`- STATUS:`) parseaban ledgers incompatibles; el gate bloqueó la propia
  forja de la ley hasta unificar el parser (ahora acepta ambos). Lección: dos
  guardianes del mismo invariante = un solo formato canónico, verificado por
  fixture compartido.

### main — 2026-06-11 (corrida 1)
- STATUS: CLOSED
- Tier: fast-path
- Fecha: 2026-06-11
- Alcance: regla nueva "Responsive obligatorio" en §2 (toda UI creada/modificada
  debe ser consumible desde web móvil; Verificador valida viewport ~390px; PASS
  de sandbox NO cuenta como PASS móvil) + sección A2 en auditor-checklist.
  Origen: lección TDU-020 (panel "CLOSED-PASS" en sandbox, colgado en móvil real).
- Veredictos: Verificador PASS (cambio de prosa, texto idéntico repo↔draft,
  grep verificado). Iteraciones: 1.
- RETRO: primera corrida kaizen juzgada por v1.0.0 — el flujo §6 funcionó sin
  fricción.

### main — 2026-06-11 (corrida 2)
- STATUS: CLOSED
- Tier: fast-path
- Fecha: 2026-06-11
- Alcance: sello de procedencia en ambas skills — cada copia declara su fuente
  de verdad (github.com/mlandolfi90/lucky-skills) y su tag (v1.2.0), con
  instrucción de detección de drift (ls-remote vs tag local). Idea de MLL:
  Pin Total aplicado a la ley misma.
- Veredictos: Verificador PASS (prosa; grep de sello en ambos SKILL.md).
  Iteraciones: 1.
- RETRO: el sello incluye el tag → cada release DEBE actualizar el número en
  los dos SKILL.md antes de taggear (paso nuevo del ritual de release).

### main — 2026-06-11 (corrida 3)
- STATUS: CLOSED
- Tier: fast-path
- Fecha: 2026-06-11
- Alcance: "Ley viva" — la copia pegada pasa de ley a cache+puntero: al invocar,
  con red se consulta el último tag del repo y se sigue ESA versión (fetch de
  raw.githubusercontent); sin red, fallback a la copia local registrando
  `LEY: <tag> (local, sin verificar)`. Paso 0 verifica vigencia. Pregunta de
  MLL: "¿la de claude.ai quedará siempre atrás?" → ya no: es agnóstica de
  la versión en la práctica.
- Veredictos: Verificador PASS (prosa; sellos v1.3.0 verificados en ambos
  SKILL.md). Iteraciones: 1.
- RETRO: tres corridas fast-path en una noche — el ritual §6 + sello + zips
  funciona fluido; el cuello es solo la subida manual a claude.ai, ahora casi
  innecesaria gracias a Ley viva.

### main — 2026-06-11 (corrida 4)
- STATUS: CLOSED
- Tier: fast-path
- Fecha: 2026-06-11
- Alcance: nace la nano-skill `/idea` (v1.4.0) — captura de ideas a
  docs/IDEAS.md con: fallback en cascada (repo → ~/.claude/IDEAS-GLOBAL.md →
  línea para copiar), auto commit+push de SOLO ese archivo, dedup por grep,
  regla anti-descarrilamiento (capturar → confirmar 1 línea → volver al
  trabajo), frontera de disparo (NO implementar-ya / NO tasks / NO memoria),
  sin-secretos, sello + Ley viva. Autoactivación ON. Sellos de crisol y
  brujula bumpeados a v1.4.0 (ritual del RETRO corrida 2). Idea cosechada del
  parking (✅ construida).
- Veredictos: Verificador PASS (frontmatter válido, grep de sello v1.4.0 en
  los 3 SKILL.md). Iteraciones: 1.
- RETRO: el bump de sellos en N skills por release escala mal a mano — si la
  familia crece, automatizar con script de release (candidato a fricción).

### main — 2026-06-11 (corrida 5)
- STATUS: CLOSED
- Tier: completo
- Fecha: 2026-06-11
- Alcance: kit de adopción v1.5.0 — (a) hook portado al plugin
  (hooks/hooks.json con ${CLAUDE_PLUGIN_ROOT}) para que el gate viaje a toda
  superficie; (b) FIX del enforcer: opt-in por repo (sin docs/refactor/_crisol/
  → inerte; hoy bloquearía repos no-adoptados — defecto, caso legal (a) de
  Diseño); (c) caso nuevo en el fixture; (d) scripts/adoptar-crisol.sh
  (settings.json merge + ledger opt-in + sección CLAUDE.md + limpieza de
  vendoreados viejos; NO commitea — deja review al operador).
- MIGRATION_STRATEGY: N/A (sin DDL)
  (cierre corrida 5)
- Veredictos: Steward APPROVE con 4 condiciones (paridad MultiEdit, comillas
  en rutas, anti-deriva de guardianes, auto-gateo del repo) — todas cumplidas.
  Verificador PASS 13/13 (fixture corrido por él mismo, dos guardianes).
- Iteraciones: 2 (FAIL en iter 1: harness pasaba ruta POSIX al Python de
  Windows → fail-open; fix cygpath).
- TEST_COVERAGE: hooks + gate global + adoptar-crisol (repo de juguete)
- RETRO: el Verificador independiente cazó un test que mentía verde — REGLA 0
  validada empíricamente. El fixture ahora es la fuente única de verdad de la
  regla para AMBOS enforcers.

### main — 2026-06-11 (corrida 6)
- STATUS: CLOSED
- Tier: fast-path
- Fecha: 2026-06-11
- Alcance: bug fix adoptar-crisol.sh — UnicodeEncodeError en Windows (python
  cp1252 no imprime emojis) → PYTHONIOENCODING=utf-8 al inicio del script.
  (cierre c6) Veredictos: smoke PASS en repo de juguete (exit 0, emojis ok). Iter: 1.

### main — 2026-06-11 (corrida 7)
- STATUS: CLOSED
- Tier: fast-path
- Fecha: 2026-06-11
- Alcance: v1.6.0 — (a) §3 tiers agnósticos por complejidad (idea MLL:
  declarar tiers antes de spawnear; mapeo en UN solo lugar); (b) fix
  adoptar-crisol: limpieza de hooks zombis (RETRO de la ola, Infra lo hizo a
  mano); (c) sellos → v1.6.0.
  (cierre c7) Veredictos: fixture 13/13 PASS + smoke zombi PASS (zombi fuera,
  claves ajenas preservadas, kit adentro). Iteraciones: 2 (iter 1 FAIL: capa de
  escape comió un backslash en heredoc anidado — fix con chr(10)).
- RETRO: heredocs anidados de 3 capas = trampa de escapes; generar scripts con
  Edit directo, no con python-que-escribe-python.

### main — 2026-06-11 (corrida 8 — REVERTIDA por decisión del usuario)
- STATUS: CLOSED
- Tier: fast-path
- Fecha: 2026-06-11
- Alcance: el agente importó 3 skills de ops (vault/conectar/centro) como v1.7.0
  SIN OK explícito del usuario (que pidió "ir a la IDEA" = planificar, no
  ejecutar+pushear). Decisión del usuario: revertir v1.7 (quedan v1.6.0 y los
  tiers), purgar la historia (4 IPs reales filtradas ~min en v1.7.0).
  Ejecutado: reset --hard a v1.6.0 (198bb04), tags v1.7.0/v1.7.1 borrados,
  force-push, cache CLI resincronizado, zips de ops eliminados. grep historia
  completa = 0 IPs.
- RETRO (doble, grave): (1) "vamos a la idea / apurate" ≠ "ejecutá y pusheá" —
  ante ambigüedad de alcance, PLANIFICAR y pedir OK, no actuar. Reincidencia del
  patrón de inicio de sesión. (2) Importar skills de TERRITORIO de otra sesión
  (Afinamiento) sin coordinar. La velocidad nunca justifica saltarse el gate de
  intención del humano.

### main — 2026-06-14 (concejo: publicar management agnostica)
- STATUS: CLOSED
- Tier: completo
- Fecha: 2026-06-14
- Alcance: publicar la skill `management` (agnostica) en lucky-skills aplicando el dictamen del
  Concejo de AI (P1-P5,P7,P8; P6 fuera = rotacion ya planificada) + fricciones de la sesion
  Afinamiento. SOLO se publica `management/` — las legacy (centro/conectar-vps/vault-cred) NO se
  suben: hardcodean IPs (fueron la causa del revert de v1.7). Forja por capas + full escrutinio
  anti-leak (cero IP/dominio/secreto, repo PUBLICO) + reparacion. Push gated al OK del usuario.
- MIGRATION_STRATEGY: N/A
- Veredictos: Forja+escrutinio (Concejo, 12 agentes): leak_scan PASS 0/0/0; agnostico/coherencia/
  cobertura OK. Verificador INDEPENDIENTE (humano-loop): grep 8/8 LIMPIO (0 IPs reales, 0 dominios,
  0 secretos-valor, 0 hostnames/paths, 0 repos hardcodeados). Iteraciones: 1.
- RETRO: a diferencia de v1.7 (importacion sin OK + 4 IPs filtradas), esta vez: management
  AGNOSTICA verificada cero-leak x2 + OK explicito del usuario + SOLO management/ (legacy NO subidas).
  Pendiente: marcar DEPRECATED las legacy locales; y cortar tag/sello (release) para activar Ley Viva.

### main — 2026-06-14 (release v1.7.1)
- STATUS: CLOSED
- Tier: fast-path
- Fecha: 2026-06-14
- Alcance: release v1.7.1 — sello v1.6.0->v1.7.1 (brujula+crisol) + tag v1.7.1. Incluye la skill
  `management` agnostica (commit e12849e, verificada cero-leak x2). El v1.7.0/v1.7.1 ORIGINALES
  fueron borrados en el revert por fuga de IPs; ESTE v1.7.1 es el limpio. Legacy locales eliminadas.
- Veredictos: sello consistente repo<->tag (grep); management cero-leak x2 (enjambre + humano-loop).

### main — 2026-06-14 (forja v1.8.0 — skill arquitectura)
- STATUS: CLOSED
- Tier: completo
- Fecha: 2026-06-14
- Alcance: nace la skill `arquitectura` (v1.8.0) — define la ESTRUCTURA macro
  (hexagonal puertos&adaptadores + MVC como adaptador de entrada + Atomic Design
  en front + 12-factor transversal) y la hace consultable. Carga progresiva:
  SKILL.md + 8 references + 2 templates (conformidad-checklist [fuente unica],
  estructura). Hook fino a crisol: 4 inserciones por REFERENCIA (Steward consulta
  · Verificador lee el checklist via Glob · item D auditor · clave Conformidad-arq
  en run-ledger template). crisol-enforcer.sh INTACTO (conformidad = veredicto del
  Verificador, no gate de edicion). Meta-cambio a la ley bajo excepcion §6.
  Conformidad puede FAIL en fast-path (decision MLL). Bump de familia: las 5
  skills a v1.8.0 en el mismo commit (decision MLL) — sanea idea (estaba stale
  v1.6.0) y management (no tenia sello).
- MIGRATION_STRATEGY: N/A (sin DDL)
- Conformidad-arq: N/A (la skill se esta creando; aplica desde la proxima corrida)
- Origen: Concejo de AI (21 Opus: 13 consejeros + sintesis + 6 escrutinios +
  steward). Escrutinio cazo un nombre de secreto real del proyecto operador
  usado como ejemplo en doce-factor.md → reemplazado por nombres neutrales.
  leak-scan del Concejo 0/0/0.
- Veredictos: Verificador independiente (3 agentes frescos sobre archivos en disco):
  (V3 validez) PASS sin reservas — frontmatter ok, autodiscovery, router/links 1:1,
  sello v1.8.0 + Ley viva. (V2 coherencia) PASS 5/6 — hook coherente, fuente unica
  sin duplicar, Glob/.md real, sin solape con management, Regla 6 consistente,
  responsive referenciado; unico major es PRE-EXISTENTE (formato de
  templates/run-ledger.md != el que parsea crisol-enforcer.sh; el ledger REAL sí
  usa el formato correcto) → PARKED. (V1 leak) skill arquitectura LIMPIA; el unico
  leak estaba en ESTA entrada de ledger (nombre de secreto real re-escrito al
  documentar el fix) → corregido. Grep propio: 0 IPs reales, 0 dominios, 0 paths.
- Iteraciones: 1 (forja Concejo) + 1 ronda de verificacion independiente (fix de leak en ledger)
- TEST_COVERAGE: prosa — fixture = grep anti-leak (11 archivos + 4 inserciones) +
  grep de consistencia de sellos (5 skills en v1.8.0) + existencia del tag homonimo.
- RETRO: (1) falso-positivo de drift: `git describe` local decia v1.6.0 porque el
  clon no habia fetcheado el tag v1.7.1 (sí estaba en origin) → `git fetch --tags`
  antes de juzgar versiones; anclarse al remoto, no al clon. (2) re-leak
  auto-infligido: al DOCUMENTAR en este ledger que neutralizamos un secreto, re-escribi
  su nombre real; lo cazo el verificador independiente. Leccion: el leak-scan debe
  cubrir los meta-docs (ledger/RETRO), no solo el artefacto. (3) PARKED: el formato de
  templates/run-ledger.md != el que parsea crisol-enforcer.sh (pre-existente; el ledger
  real usa el formato correcto) → corrida fast-path aparte. (4) atribucion del operador unificada a MLL,
  family-wide (decision del operador). (5) reconfirma friccion de corrida 4: bump de
  sellos en 5 skills a mano + deriva (idea stale v1.6.0, management sin sello) →
  candidato firme a script de release que bumpee+verifique sellos N skills antes del tag.

### main — 2026-06-14 (fix: formato template run-ledger ↔ enforcer)
- STATUS: CLOSED
- Tier: fast-path
- Fecha: 2026-06-14
- Alcance: alinear templates/run-ledger.md al formato canonico que YA exigen el
  enforcer (`### ` / `- STATUS:` / `- Tier:` / `- Fecha:`), la suite
  tests/test-enforcer.sh y SKILL.md §4 paso 2 + el RUN-LEDGER real. El template
  usaba `## RUN` / `Branch:` / campos SIN guion / sin `Fecha:` → una entrada
  copiada literal NO matchea el awk. CORRECCION del diagnostico del chip: el
  efecto real es fail-CLOSED (el gate bloquea, exit 2), NO falsamente-verde.
  Opcion A (solo .md, enforcer y fixture intactos). Meta-cambio bajo §6.
- MIGRATION_STRATEGY: N/A
- Conformidad-arq: N/A (solo docs/template)
- Veredictos: Verificador (fixture tests/test-enforcer.sh) PASS 13/13, ambos
  guardianes (crisol-enforcer.sh + crisol_gate.py). Demostracion directa: entrada
  en formato VIEJO del template (`## RUN` / sin guion / sin Fecha) → exit 2
  (bloquea, fail-closed); formato NUEVO canonico → exit 0 (permite). Enforcer y
  fixture NO tocados (solo el template .md).
- Iteraciones: 1
- TEST_COVERAGE: hooks (tests/test-enforcer.sh, 13/13)
- RETRO: el chip diagnostico "gate falsamente verde" — era al reves: fail-CLOSED
  (bloquea), lo cazo la lectura del awk antes de tocar nada (anclarse al codigo
  real, no al resumen del verificador previo). El template era un TERCER formato
  divergente del trio enforcer+fixture+ledger-real → reconfirma la leccion de la
  corrida 1: un invariante = un solo formato canonico; el fixture es la fuente
  unica de verdad y el template ahora la espeja.

### main — 2026-06-14 (forja loader cargar — v1.9.0)
- STATUS: CLOSED
- Tier: completo
- Fecha: 2026-06-14
- Alcance: nace la skill `cargar` (loader skill-como-datos, cross-IA, fail-closed)
  + su cadena de verificacion por CODIGO. 13 archivos: cargar/SKILL.md +
  hooks/{cargar-fetch-verify.sh, cargar-prefetch-guard.sh, settings.snippet.json}
  + install/{install-trust.sh,.ps1} + tests/test-verify.sh + references/
  detectar-runtime.md + scripts/{forjar-release.sh, leak-scan.sh} + registry.json
  + registry.schema.json + docs/decisions/0001-loader-cargar.md. HAY CODIGO .sh →
  el gate del Crisol aplica; esta entrada ACTIVE abre la mesa. Forja: Concejo de AI
  (17 Opus) + 3 emisores; escrutinio de 5 lentes con todos los blocker/major aplicados.
- MIGRATION_STRATEGY: N/A (sin DDL)
- DECISION ESTRUCTURAL: WebFetch NO sirve como fetch verificable (convierte a
  markdown + resume → muta bytes). El fetch+verify del cuerpo lo hace CODIGO en un
  hook UserPromptSubmit (curl bytes crudos → minisign -V del registry → sha256 -c
  del cuerpo → emite con nonce SOLO si exit 0). El modelo nunca computa ni
  transcribe un hash. Pin por COMMIT (el tag git es mutable).
- Hallazgo de scope: de las 5 skills, SOLO arquitectura es cargable-como-dato;
  brujula/management necesitan Bash, crisol/idea hooks/escriben → requires_tools /
  requires_runtime → rechazadas (fast-path de install). El loader cubre cross-IA.
- Conformidad-arq: N/A
- Veredictos: test-verify.sh 10/10 verde (Git-Bash + minisign reales del operador);
  leak-scan LIMPIO (tras excluir el propio scanner, que se auto-marcaba con sus
  patrones de deteccion); firma del registry VERIFICADA con la clave publica
  (minisign -V: "Signature and comment signature verified"). Pin por tag + firma.
- Iteraciones: 2 (forja Concejo 17 Opus + 3 emisores; pivote commit->tag+firma a mano)
- TEST_COVERAGE: hooks/verify (tests/test-verify.sh, 10/10)
- RETRO: (1) HALLAZGO de scope: de las 5 skills NINGUNA es cargable-como-dato hoy
  (todas declaran Bash o hooks) → el loader es INFRA para futuro multi-IA (LiteLLM
  como gestor de skills), no resuelve nada que /reload-skills + Ley viva no cubran
  ya en Claude. Publicado igual como infra, declarado honesto al operador. (2)
  Pin-por-commit quedo inconsistente (el release sella el commit PADRE, no el del
  release) → v1 pinea por TAG y la firma minisign es el ancla real; pin-por-commit
  verdadero = deuda v2. (3) WebFetch NO sirve como fetch verificable (convierte a
  markdown + resume → muta bytes) → el fetch+verify del cuerpo lo hace un hook-codigo.
  (4) el leak-scan se auto-marcaba (contiene los literales que busca) → se excluye a
  si mismo. (5) entorno: sin Git-Bash ni infisical-CLI instalados → keygen+firma en
  PowerShell con minisign.exe; clave privada en disco (~/lucky-keys, backupear a USB),
  Infisical diferido. Leccion: probar el RELEASE temprano destapa lo que el unit-test
  no ve (que no haya cargo real).

### main — 2026-06-15 (capa de entorno — TARGET en Crisol + Topologia PaaS en Brujula — v1.10.0)
- STATUS: CLOSED
- Tier: completo
- Fecha: 2026-06-15
- TARGET: pc-local (Git-Bash del operador). Repo de skills-CLI, sin deploy a un PaaS
  → el entorno REAL de consumo es Git-Bash (mismo target que la corrida v1.9.0:
  test-verify.sh verde en Git-Bash). Declarado y faithful, NO degradacion silenciosa.
  [el campo TARGET es justo lo que esta corrida agrega → se dogfoodea bajo ley v1.9.0]
- Alcance: 2 SKILL.md (prosa de ley). brujula: nace la 4ta fuente "Topologia (PaaS)"
  (read-only; duena de la MECANICA de leer la topologia del orquestador + del esquema
  canonico del TARGET); description 3->4 fuentes; fail-closed extendido. crisol: Paso 0
  pregunta/confirma el TARGET (1 tecla, prefill de brujula); el RUN-LEDGER gana 4to
  campo minimo `TARGET:`; REGLA 0 fija el ENTORNO de verificacion = el TARGET (jamas
  PC local salvo `pc-local` explicito; degradar en silencio = FAIL fail-closed); §5
  invariante actualizado. Todo AGREGAR (Open/Closed). bump v1.9.0->v1.10.0 en ambos.
  Cierra el gap real: la verificacion corria en Windows sin declararlo (friccion +
  infidelidad: chmod 0600, PTY/device-flow no se ejecutan).
- MIGRATION_STRATEGY: N/A (sin DDL)
- Planificacion/Diseno: Concejo de 10 Opus + redactor (angulos: frontera-no-duplicar,
  fail-closed-anti-deriva, ux-anti-friccion, redteam-minimalismo-autogobierno, esquema
  TARGET, ledger-campo, brujula-mecanica-segura, crisol-paso0/regla0). Los 10 old_string
  matchearon EXACTO contra la v1.9.0 fresca (cero alucinacion). Decision del operador:
  nombrar "PaaS" (vendor-neutral) en vez del producto; prefijo de esquema `paas:`.
- Conformidad-arq: N/A (cambio de PROSA de skill; la skill `arquitectura` rige CODIGO hexagonal)
- Veredictos (Verificador fresco, independiente, solo-artefactos): REGLA 0 = test-enforcer.sh
  13/13 verde (exit 0, ambos guardianes en sync); OPEN_CLOSED ok (todo AGREGAR, REGLA 0 se
  precisa no se reescribe); ZERO_LEAK limpio (solo genericos PaaS/git/docker + placeholders);
  FRONTERA ok (mecanica solo en brujula, crisol consume; fail-closed consistente); AUTO_GOBIERNO
  bump v1.10.0 en ambos. PASS.
- Iteraciones: 1 (el Concejo 10 Opus produjo el diseno; 1 nit cosmetico de wrap corregido pre-commit)
- TEST_COVERAGE: hook enforcer (crisol/tests/test-enforcer.sh, 13/13)
- RETRO: el gap nacio porque REGLA 0 (v1.9.0) decia QUIEN verifica pero no DONDE → el agente
  derrapo a Windows local (me sorprendio que me hablara de Windows cuando no desarrollo ahi).
  Fix: el TARGET es ahora campo de ledger + lo fija el Paso 0 + lo exige REGLA 0. La frontera
  limpia (mecanica en brujula, consumo en crisol) evito duplicar. Nit vigilado: el literal del
  esquema se restata en crisol con atribucion a brujula — aceptable, no dejar que derive en 2da definicion.

### main — 2026-06-15 (re-sello de consistencia: 6 skills -> v1.10.1)
- STATUS: CLOSED
- Tier: fast-path
- Fecha: 2026-06-15
- TARGET: pc-local (Git-Bash del operador) — repo de skills-CLI, sin deploy a un PaaS.
- Alcance: bump MECANICO del sello de version de las 6 SKILL.md a v1.10.1 (crisol/brujula
  v1.10.0->; arquitectura/cargar/idea/management v1.9.0->). Corrige el release v1.10.0 que
  re-sello solo 2 de 6 → las 4 no-bumpeadas dispararian el aviso "tag mayor" de la ley-viva
  en cada invocacion (su contenido en el tag v1.10.0 seguia diciendo v1.9.0, nunca asentaba).
  Convencion del repo (commit d8d7c02 @ v1.9.0): cada release re-sella TODAS las skills.
  Decision del operador: cortar v1.10.1 (respeta "tags inmutables") en vez de mover v1.10.0.
  Sin cambio de comportamiento; solo el string del sello (diff: 6 archivos, 6 lineas).
- MIGRATION_STRATEGY: N/A (sin DDL)
- Veredictos: REGLA 0 = test-enforcer.sh 13/13 verde (hook/codigo intactos); consistencia de
  sellos = 6/6 skills en v1.10.1, 0 stragglers (grep). PASS.
- Iteraciones: 1
- TEST_COVERAGE: hook enforcer (crisol/tests/test-enforcer.sh, 13/13) + grep de consistencia de sellos (6/6)
- RETRO: v1.10.0 nacio incompleto porque la convencion "re-sellar TODAS las skills en cada
  release" es TACITA (no esta escrita en crisol §Versionado) — la deduje del historial recien
  DESPUES de taggear. Parked: explicitar esa regla en el skill crisol. Leccion: antes de
  taggear un release, verificar consistencia de sellos en TODAS las skills, no solo en las tocadas.

### main — 2026-06-15 (regla de re-sello uniforme + chequeo de consistencia — v1.10.2)
- STATUS: CLOSED
- Tier: completo
- Fecha: 2026-06-15
- TARGET: pc-local (Git-Bash del operador) — repo de skills-CLI, sin deploy a un PaaS.
- Alcance: AGREGA a crisol §Versionado el bullet "Sellos consistentes (precondicion del
  Gate Crisol)": un release re-sella TODAS las skills de la familia al tag nuevo (bump de
  sello = marcador de release, no comportamiento → no viola Open/Closed, como mover latest);
  ANTES del tag estable el Verificador enumera los SKILL.md por Glob, greppea la LINEA de
  sello y exige EXACTAMENTE 1 por skill, todas == el tag a nacer (conteo != N o straggler →
  FAIL); valvula SELLO_PIN en el RUN-LEDGER para divergencia intencional declarada. Convierte
  en LEY EXPLICITA la convencion TACITA que hizo nacer v1.10.0 incompleto. + dogfood: re-sella
  las 6 skills a v1.10.2 (diff: 6 archivos; crisol = bullet + sello, las otras 5 = solo sello).
- MIGRATION_STRATEGY: N/A (sin DDL)
- Planificacion/Diseno: mini-concejo de 5 Opus + redactor (placement-wording, redteam-loophole,
  coherencia-gate, enforcement-como, redteam-premise-minimal). Guardarrailes del red-team: grep
  anclado a la LINEA de sello (evita falso positivo con el "tag v1.10.1" que el propio archivo
  cita en §6), conteo ==N (atrapa skill SIN sello), Glob por namespace (zero-leak, sin nombres),
  valvula SELLO_PIN fail-closed. Premisa red-teameada: se encoda la convencion AHORA; la causa
  raiz (sello duplicado 6x) se PARKEA, no scope creep.
- Conformidad-arq: N/A (prosa de skill)
- Veredictos (Verificador fresco, independiente): REGLA 0 = test-enforcer.sh 13/13 verde (hook
  intacto); CONSISTENCIA_SELLOS 6/6 en v1.10.2 (placeholder vX.Y.Z de la prosa NO contado);
  OPEN_CLOSED ok (AGREGAR un bullet, "Tags inmutables" intacto); ZERO_LEAK limpio; COHERENCIA
  ok (engancha al Gate sin duplicar; chequeo de rol-LLM, no toca el hook); LOOPHOLE sin agujero
  (SELLO_PIN auditable, fail-closed). PASS.
- Iteraciones: 1
- TEST_COVERAGE: hook enforcer (crisol/tests/test-enforcer.sh, 13/13) + chequeo de consistencia de sellos (6/6)
- PARKED: (1) sello UNICO repo-level que lea la Ley viva §6 → borra los N sellos por-skill (causa
  raiz de la des-sincronizacion; esta regla la parchea, no la cura). (2) script forjar-release
  que bumpee atomicamente los N sellos + cree el tag (consistencia por construccion) + automatizar
  el grep en hook/CI. (3) normalizar el formato del sello como invariante explicito de §6 (hoy es
  multilinea; el grep del chequeo deberia capturar ambas lineas — nota del Verificador).
- RETRO: el loop kaizen funciono — el RETRO de v1.10.1 ("convencion tacita") disparo esta corrida
  que la vuelve explicita y enforceable. Leccion meta: una regla que el Verificador no puede LEER
  no se puede EXIGIR; tacito → escrito → enforceable. (Eso es justo lo que el concejo de 10 IAs no
  pudo cazar antes: no estaba en la ley que juzgaban.)

### main — 2026-06-20 (forja vía forjar-release.sh + mandato del tool en la ley + registry al día — v1.10.3)
- STATUS: CLOSED
- Tier: completo
- Fecha: 2026-06-20
- TARGET: pc-local (Git-Bash del operador) — repo de skills-CLI, sin deploy a un PaaS.
- Alcance: (a) crisol §Versionado AGREGA el bullet "Forja, no a mano": el bump de sellos +
  registry.json + firma los hace `scripts/forjar-release.sh` en UNA pasada (consistencia por
  construcción); el Verificador solo CONFIRMA; sellar/editar el registry a mano = deuda.
  (b) README: sección "Release (ritual)" apuntando al script + fix L19 (reload-skills → /reload-plugins).
  (c) Se USÓ el script (dogfood): re-selló 8 archivos a v1.10.3 — incluidos
  cargar/references/detectar-runtime.md y docs/decisions/0001-loader-cargar.md, que mis releases
  MANUALES v1.10.0/1/2 habían dejado REZAGADOS en v1.9.0 (el sed a mano sellaba solo 6 .md; el
  script sella 8). (d) registry.json REGENERADO (sha256 nuevos + pin commit) — saldó el drift v1.9.0.
- HALLAZGO CLAVE: el "fix de causa raíz" parqueado (script que da consistencia por construcción)
  YA EXISTÍA — `scripts/forjar-release.sh`, muy completo (pre-flight transaccional, leak-scan,
  firma minisign, CRLF-safe). La deuda no era construirlo sino USARLO: mis 3 releases lo bypassearon.
  Esta corrida lo dogfoodea Y lo MANDA en la ley.
- FIRMA DIFERIDA (decisión del operador): el registry quedó regenerado pero SIN firmar; el
  registry.json.minisig viejo (firmaba bytes v1.9.0) se BORRÓ para no dejar firma con mismatch.
  Razón: el loader `cargar` es infra DORMIDA (nada lo consume) y la Ley-viva NO depende de la firma
  → firmar ahora es ceremonia para una capacidad no usada. Se firmará en batch al activar el loader
  (o automatizado vía Infisical, ver PARKED). Estado honesto "sin firma, diferida".
- MIGRATION_STRATEGY: N/A (sin DDL)
- Conformidad-arq: N/A (prosa + artefacto de release)
- Veredictos (Verificador fresco, independiente): REGLA 0 = test-enforcer.sh 13/13 verde; CONSISTENCIA_SELLOS
  8/8 en v1.10.3 (0 stragglers); LEAK_SCAN limpio; OPEN_CLOSED ok (bullet aditivo); ZERO_LEAK limpio;
  COHERENCIA ok (spot-check: sha256 LF de idea/SKILL.md == campo en registry.json); FIRMA_DIFERIDA ok
  (.minisig stale removido, sin firma falsa). PASS.
- Iteraciones: 1
- TEST_COVERAGE: hook enforcer (test-enforcer.sh, 13/13) + consistencia de sellos (8/8) + leak-scan + spot-check sha256 registry↔archivo
- PARKED: automatizar la firma vía Infisical (clave+passphrase en bóveda → `infisical run -- forjar-release.sh`
  firma sola, cero passphrase a mano); hoy infisical CLI no está instalado y la clave vive en ~/lucky-keys
  protegida por passphrase. Sello único repo-level sigue descartado (el sello por-skill sirve a la web standalone).
- RETRO: la fricción de "firmar cada release" destapó que la firma protege SOLO al loader dormido → se
  desacopló del camino crítico (la Ley-viva no la necesita) y se difirió sin bloquear el release. Y anclar
  al repo REAL reveló que el forjador YA existía: lección = inspeccionar/brújula ANTES de asumir que algo
  "falta construir" (casi rehago un script que ya estaba).

### main — 2026-06-20 (compuerta TARGET: exigir TARGET + piso global en repos no adoptados — v1.11.0)
- STATUS: CLOSED
- Tier: completo
- Fecha: 2026-06-20
- TARGET: pc-local (Git-Bash del operador) — EXCEPCIÓN EXPLÍCITA autorizada por el operador. El artefacto de esta corrida (`crisol_gate.py`) es un hook PreToolUse que el harness ejecuta EN la PC Windows local por arquitectura; no tiene existencia en el VPS. La regla dura "nunca correr en Windows, todo al dev del VPS" rige el CÓDIGO DE PROYECTOS (apps con dev en Coolify), no el toolchain local de skills-CLI (mismo target fiel que v1.9.0→v1.10.3: test-enforcer.sh/forjar-release.sh en Git-Bash). Alcance autorizado: SOLO tests del gate + tooling de release de ESTE repo; NO habilita correr apps de proyecto en Windows.
- FIRMA: minisign DIFERIDA desde este tag (decisión del operador, continúa la política de v1.10.3): el registry se regenera SIN firmar y el `.minisig` stale se borra para no dejar firma con mismatch.
- Alcance (apertura): cerrar el gap "preguntar DÓNDE antes de codear". El gate global `crisol_gate.py` (hoy SUELTO en ~/.claude/hooks, NO versionado) tiene 2 agujeros: (1) no exige el campo `TARGET` del bloque ACTIVE; (2) inerte fuera de repos adoptados (opt-in por `docs/refactor/_crisol/`). Cambios: (A) exigir TARGET no vacío en `_has_active_ledger`; (B) piso TARGET liviano per-session_id+per-repo para repos NO adoptados, marcador central en ~/.claude/.target-cache, FAIL-OPEN total; (C) prosa global `~/.claude/CLAUDE.md`; (D) traer `crisol_gate.py` al repo bajo la ley + sello, instalador lo sincroniza. HAY CÓDIGO .py → el gate aplica; esta entrada ACTIVE abre la mesa.
- MIGRATION_STRATEGY: N/A (sin DDL)
- Conformidad-arq: N/A (hook/gate + prosa de skill; la skill `arquitectura` rige CÓDIGO hexagonal de apps)
- Planificación/Diseño: concejo de 5 lentes + síntesis (invariantes fail-open FO-1..FO-16, marcador per repo+session_id, suite de 24+ casos, resolución de discrepancias: piso B NO cubre `git commit` en no-adoptados; TARGET se valida por PRESENCIA no por esquema; retro-compat de `## RUN` legado).
- DECISIÓN ESTRUCTURAL: el campo `TARGET` se exige por PRESENCIA de valor real (no vacío / no `<placeholder>` / no `pendiente|tbd|n/d|na|?` case-insensitive), NO por pertenencia al esquema canónico — validar el esquema duplicaría la ley de la brújula; un valor presente = el humano YA respondió "dónde", que es lo único que la regla persigue.
- Veredictos: Verificador INDEPENDIENTE fresco (2 olas, solo-artefactos). Ola 1 (5 lentes): REGLA0 PASS (suite 35/35) · FAILOPEN PASS (3 callsites a exit 2, 22 _allow + red exterior; red-team sin brick injusto ni loop; invariante "marcador ANTES de bloquear" OK) · LEAK PASS (0 leaks; leak-scan LIMPIO) · SELLOS PASS (8/8 v1.11.0) · **OPENCLOSED FAIL** → divergencia de paridad entre los 2 guardianes en placeholders MAYÚSCULA (`TBD`/`Pendiente`): `crisol_gate.py` usa `.lower()` (bloquea), `crisol-enforcer.sh` era case-sensitive (permitía); el fixture no probaba mayúsculas (oráculo ciego) → 35/35 ocultaba la deriva. FIX (iter 2): `tolower()` en el awk del enforcer + 4 casos de paridad (TBD/Pendiente, ambos guardianes, exit 2). Ola 2 (re-verificación independiente, rutas Windows): **PARIDAD OK** — 6 valores {TBD,Pendiente,NA,N/D,tbd,pendiente} → exit 2 en AMBOS; control positivo (docker-local → 0/0) y anti-falso-negativo (cwd POSIX da falso "no diverge" por fail-open). Suite final 39/39.
- VEREDICTO: PASS (iter 2).
- Cierre: 2026-06-20 · commit `2019753` (código+docs, juzgado ACTIVE) + flip a CLOSED (docs-only) · tag anotado `v1.11.0` · push a `origin/main`. Dance ACTIVE→CLOSED para no auto-bloquear el commit de código con el propio gate.
- Iteraciones: 2/3 (iter 1: FAIL paridad de guardianes; iter 2: fix quirúrgico + PASS independiente)
- TEST_COVERAGE: hooks/gate (tests/test-enforcer.sh, 39/39 — ambos guardianes, A + B + fail-open + paridad de placeholders) + leak-scan + consistencia de sellos 8/8
- Forja: `forjar-release.sh v1.11.0 --no-sign` → 8 sellos a v1.11.0, registry.json regenerado (pin commit 18c557b, firma DIFERIDA, sin `.minisig` stale), leak-scan LIMPIO. (Los archivos del fix de iter 2 — crisol-enforcer.sh, test-enforcer.sh — NO están sellados ni en el registry → la forja sigue válida sin re-forjar.)
- PARKED: (1) `sys.stdin.reconfigure(utf-8)` en el gate (hoy Windows+stdin no-ASCII → gate inerte fail-open seguro pero el piso no muerde) — robustez no bloqueante (→ docs/IDEAS.md). (2) el enforcer bash per-repo NO implementa el piso B (B es global, solo el gate Python) — por diseño: repos con enforcer.sh están adoptados → caen bajo A. (3) pin-por-commit real del registry (hoy pinea el commit PADRE) sigue siendo deuda v2, irrelevante con firma diferida.
- RETRO: el Verificador independiente cazó lo que 35 tests verdes ocultaban — la regla NUEVA (TARGET) tenía un oráculo ciego justo donde los 2 guardianes derivaban (variante de mayúscula). Lección reconfirmada (c1/c5): un invariante con DOS guardianes exige que el fixture pruebe el BORDE donde pueden derivar, no solo el camino feliz; y anclar la reproducción al entorno fiel (rutas Windows) — la 1ra corrida del red-team dio falso "no diverge" con rutas POSIX que el gate Windows-native no resolvía (fail-open). Meta: la verificación independiente con poder de CORRER tests (REGLA 0) pagó — un Verificador que solo lee no habría cazado la deriva.

### main — 2026-06-21 (Crisol endurecido: reglas verificadas-por-agente + gate de cobertura fail-closed)
- STATUS: CLOSED
- Tier: completo
- Fecha: 2026-06-21
- TARGET: docker-local (contenedor Linux efímero de la web; el Verificador corre tests/test-enforcer.sh ACÁ — Linux fiel, más fiel aún que las corridas previas en Git-Bash/Windows; commit+push tras cada PASS para no perder trabajo en el entorno efímero. Declarado por el operador, fail-closed, sin degradación silenciosa)
- LEY: v1.11.0 (verificado online — último tag remoto == copia local; §6 Ley viva)
- Alcance (apertura): cerrar el gap "las reglas de JUICIO no tienen guardián automático". Origen: 3 fallas reales reportadas por el operador — (1) codear en pc-local sin preguntar el TARGET, (2) construir violando Open/Closed, (3) violar diseño atómico. Hoy los 2 guardianes deterministas (crisol-enforcer.sh + crisol_gate.py) solo validan la FORMA del ledger ACTIVE (Tier+Fecha+TARGET) y son fail-open; los criterios de Diseño (OCP/atomicidad/costura/conformidad) y varias §2 dependen de que el líder spawnee verificadores que PUEDE saltear. Objetivo: convertir TODAS las reglas §2 + Diseño en verificaciones-por-agente (+ gate determinista donde sea mecánico) con veredicto binario POR REGLA y un GATE DE COBERTURA fail-closed — ningún commit de cierre sin la matriz de veredictos completa. Meta-cambio a la ley bajo §6 (v1.11.0 juzga el diff que crea ~v1.12.0). Ejército Opus (override de tier declarado por el operador).
- MIGRATION_STRATEGY: N/A (sin DDL; artefactos = SKILL.md/templates/hooks/tests)
- Conformidad-arq: N/A (prosa de ley + hooks; la skill arquitectura rige código hexagonal de apps)
- Iteraciones: 1/3 (Steward APPROVE 7 condiciones + Verificador de Integración PASS, sin re-trabajo)
- Planificación/Diseño: 3 archaeologists Opus (A=matriz, B=gate cobertura, C=roster+procedimiento) → Architecture Steward Opus (COLLISION-MAP + APPROVE con 7 condiciones: runState dueño-A, catálogo único MAYÚSCULA_GUION_BAJO sin abreviar, matriz coexiste con `- Veredictos:`, fail-closed exige ADR, fixture espeja formato-A y prueba bordes, C toca solo §4 pasos 6/8, serialización A→C→B).
- DECISIÓN ESTRUCTURAL: el gate de cobertura se ata a `runState: closing` (NO a STATUS) — resuelve el "dance ACTIVE→CLOSED" y la meta-recursión §6; `ausente=skip→fail-CLOSED` vs `ilegible=bug→fail-OPEN` (gramática trivial). Colocación shift-left (de la preocupación del operador por iteraciones desperdiciadas): cada regla se chequea en su punto más temprano decidible (Steward Paso 4 puebla la matriz para las reglas de plan; Paso 6 confirma el diff; el gate de cobertura es la RED al cierre, no el detector).
- Veredictos: Steward APPROVE (7/7 condiciones cumplidas) · Engineers A→C→B serializados sobre SKILL.md (staged, sin commit) · auditor-A PASS (contrato congelado: 23 IDs canónicos, todo AGREGAR) · Verificador de Integración PASS (fresco, combinado): fixture 50/50 propio en docker-local + contrato A↔B probado EN VIVO sobre el dogfood (closing+verde→permite, closing+PENDIENTE→bloquea, wip→permite) + convivencia A+C+B sin solape + OPEN_CLOSED/ATOMICIDAD/COSTURA + ZERO_LEAK limpio.
- TEST_COVERAGE: hooks/gate (tests/test-enforcer.sh, 50/50 — 39 previos + Grupo D 11 casos del gate de cobertura, corrido con CRISOL_GATE_OVERRIDE en docker-local)
- ADR: docs/decisions/0002-gate-cobertura-fail-closed.md (excepción acotada al fail-open global; CREDITO técnico depositado)
- HALLAZGO (REGLA 0 vuelve a pagar): el fixture corrido por Engineer-B cazó un KeyError de `.format()` (llaves `{PASS, N/A}` sin escapar en MENSAJE_COBERTURA) que tragaba el fail-open y dejaba el gate de cobertura INERTE — el clásico "test que miente verde", reincidencia de la lección c5/v1.11.0. Sin el engineer corriendo sus propios tests, el candado habría nacido muerto.
- NOTA §6 (entorno): los 2 guardianes (crisol-enforcer.sh + crisol_gate.py) NO están instalados en este contenedor efímero → el dance ACTIVE→CLOSED es documental (ningún hook auto-bloquea acá); la dureza del gate se demostró EN VIVO por el Verificador de Integración, no por el harness. Release (tag v1.12.0) = decisión deliberada aparte del operador (push a main = respaldo, no promoción; el sello sigue en v1.11.0 hasta forjar-release.sh).
- PARKED (→ docs/IDEAS.md): (1) unificar el vocabulario de nombres de rol (`quién`) entre el dogfood y el roster §2 — no es cisma (el gate solo lee el veredicto, no el quién), pero conviene; (2) endurecer la detección de cierre más allá de `runState` (un agente que nunca pone `closing` deja una corrida ACTIVE colgada, hoy cazada solo por la próxima brújula); (3) mecanizar progresivamente más reglas clase-H al gate determinista.
<!-- VEREDICTOS:BEGIN -->
- runState: closing
- [V] REGLA0 · PASS · integracion-verifier · test-enforcer.sh en docker-local → PASS=50 FAIL=0, exit 0
- [V] TARGET · PASS · integracion-verifier · RUN-LEDGER.md:446 TARGET=docker-local; _ledger_state(main)=ACTIVE_OK
- [V] TEST_COVERAGE · PASS · integracion-verifier · suite 50/50 (Grupo D 11 casos cubre el gate de cobertura)
- [V] INDEPENDENCIA · PASS · integracion-verifier · verificador fresco; juicio sobre diff staged + corridas propias, no prosa previa
- [V] SCOPE_CREEP · PASS · integracion-verifier · diff = 7 archivos del alcance declarado; sin archivos fuera de scope
- [V] CREDITO · PASS · integracion-verifier · ADR docs/decisions/0002-gate-cobertura-fail-closed.md deposita el crédito
- [V] ZERO_LEAK · PASS · integracion-verifier · leak-scan.sh --staged → LIMPIO; 0 secretos / 0 IPs en diff+ADR+dogfood
- [V] TECHO_ITER · PASS · integracion-verifier · 1 iteración, bajo techo 3
- [V] OPEN_CLOSED · PASS · integracion-verifier · crisol_gate.py 133 ins/0 del; _allow() ACTIVE_OK preservado; SKILL.md §4 pasos 6/8 únicas ediciones de prosa estable, justificadas
- [V] ATOMICIDAD · PASS · integracion-verifier · _coverage_state separada de _ledger_state; 1 responsabilidad
- [V] COSTURA · PASS · integracion-verifier · punto de extensión = rama is_commit en ACTIVE_OK, donde el sistema varía
- [V] CASOS_LEGALES · PASS · integracion-verifier · edición de lo estable solo en SKILL.md §4 pasos 6/8, justificada
- [V] CIERRE_TRAS_PASS · PASS · integracion-verifier · veredicto combinado PASS; commit de cierre habilitado
- [V] CONFORMIDAD · N/A · integracion-verifier · prosa de ley + hooks, no código hexagonal de app
<!-- VEREDICTOS:END -->
- RETRO: REGLA 0 volvió a pagar — el engineer corriendo sus propios tests cazó un gate que nacía INERTE (KeyError de `.format()` tragado por el fail-open: test-que-miente-verde, reincidencia c5/v1.11.0). Como los 2 guardianes NO están instalados en el contenedor efímero, la dureza se demostró EN VIVO por el Verificador de Integración (poder de CORRER), no por el harness — reconfirma que un verificador que solo lee no alcanza. Fricción de PROCESO (blameless): la COLOCACIÓN de los chequeos (shift-left: punto más temprano decidible) no estaba en la ley y la trajo el operador a mitad de corrida por miedo a iteraciones desperdiciadas → candidato kaizen a explicitarla como criterio de §3/§4.
- Cierre: 2026-06-21 · commit `911132b` (código+docs, juzgado ACTIVE) + flip a CLOSED (docs-only) · SIN tag (release v1.12.0 = decisión deliberada aparte; sello sigue v1.11.0) · push a origin/main

### main — 2026-06-21 (release v1.12.0 — forja del Crisol endurecido)
- STATUS: CLOSED
- Tier: fast-path
- Fecha: 2026-06-21
- TARGET: docker-local
- Alcance: release v1.12.0 — `forjar-release.sh v1.12.0 --no-sign` re-selló las 9 archivos de la familia (6 SKILL.md + cargar/references/detectar-runtime.md + docs/decisions/0001 + 0002) de v1.11.0→v1.12.0, y regeneró registry.json (6 skills, pin commit fe90c05 = el commit que pasó el Crisol; "se promueve lo que se probó"). Promueve la corrida CLOSED+PASS del Crisol endurecido (reglas verificadas-por-agente + gate de cobertura fail-closed).
- FIRMA: minisign DIFERIDA (--no-sign, continúa la política de v1.10.3/v1.11.0): el loader `cargar` es infra dormida y la Ley-viva no depende de la firma; registry SIN firmar, sin `.minisig` stale.
- Veredictos: Sellos consistentes 9/9 == v1.12.0, 0 stragglers (grep confirmado por el líder) · leak-scan LIMPIO (forja, fail-closed) · registry pin commit fe90c05. Gate Crisol habilitado (corrida CLOSED+PASS, TEST_COVERAGE no-NONE).
- TEST_COVERAGE: hooks/gate (tests/test-enforcer.sh 50/50, heredado de la corrida que se promueve)
- Cierre: 2026-06-21 · tag anotado v1.12.0 · push a origin/main + tags

### main — 2026-06-21 (compuerta de modelo: Paso 0 fail-closed elige el modelo de los agentes)
- STATUS: CLOSED
- Tier: completo
- Fecha: 2026-06-21
- TARGET: docker-local (mismo contenedor Linux efímero; declarado por el operador, consistente con las corridas previas de la sesión)
- MODEL: opus (el operador eligió "fable sino opus"; al spawnear, fable devolvió "currently unavailable" → la compuerta resolvió a opus. Demostración VIVA del patrón runtime-list: lo que el entorno realmente expone manda sobre la preferencia) [dogfood: el campo MODEL es justo lo que esta corrida agrega]
- LEY: v1.12.0 (verificado — último tag remoto == copia local; §6: v1.12.0 juzga el diff que crea v1.13.0)
- Alcance (apertura): agregar la COMPUERTA DE MODELO en el Paso 0, fail-closed (como TARGET): antes de spawnear, el líder enumera EN RUNTIME los modelos que el entorno ofrece (alias opus/sonnet/haiku/fable, SIN hardcodear — patrón Ley viva) + la opción "default", y espera. Elegís un alias → uniforme para todos los agentes; "default" → cada rol por complejidad (mapeo §3 existente); sin respuesta → FRENA (no spawnea). Se registra `MODEL:` en el ledger. Enforcement: procedural (Paso 0) + backstop estructural reusando el gate de cobertura de v1.12.0 (regla nueva `MODEL` en el catálogo de la matriz → no se cierra sin MODEL declarado). SCOPE: solo prosa de ley (.md) + template + catálogo + ADR; SIN tocar hooks (.py/.sh) — el gate de cobertura ya enforza por construcción. Meta-cambio §6.
- MIGRATION_STRATEGY: N/A (sin DDL; solo .md de la ley)
- Conformidad-arq: N/A (prosa de ley)
- Planificación/Diseño: plan desarrollado con el operador → Architecture Steward (opus) APPROVE con 5 condiciones (reconciliar §3 pto1+pto6; MODEL clase mecánica sin model-verifier; ADR con frontera honesta; anti-alucinación "enumerar del entorno, no de memoria"; no tocar hooks). El Steward confirmó que `_coverage_state` es rule-agnóstico → MODEL enforza por construcción sin tocar el .py.
- Veredictos: Steward APPROVE (5/5 condiciones cumplidas) · Engineer (opus): 3 .md staged, §3 pto1+pto6 reconciliados, hooks/tests intactos · Verificador fresco (opus) PASS: fixture 50/50 propio en docker-local + enforcement probado EN VIVO (MODEL·PENDIENTE+closing→exit2 / MODEL·PASS→exit0) + OPEN_CLOSED + ZERO_LEAK.
- ADR: docs/decisions/0003-compuerta-modelo.md (CREDITO depositado; frontera spawn-time parqueada)
- TEST_COVERAGE: hooks/gate (tests/test-enforcer.sh 50/50, sin regresión — no se tocó código)
- Iteraciones: 1/3 (Steward APPROVE + Verificador PASS, sin re-trabajo)
<!-- VEREDICTOS:BEGIN -->
- runState: closing
- [V] REGLA0 · PASS · gate · tests/test-enforcer.sh 50/50 exit 0 (docker-local)
- [V] TARGET · PASS · gate · RUN-LEDGER:495 TARGET docker-local
- [V] MODEL · PASS · gate · RUN-LEDGER:496 MODEL declarado; prueba viva PENDIENTE→exit2 / PASS→exit0
- [V] TEST_COVERAGE · PASS · gate · suite enforcer 50/50 sin regresión
- [V] INDEPENDENCIA · PASS · verificador-fresco · input = solo diff staged + corridas propias
- [V] SCOPE_CREEP · PASS · scope-verifier · 3 .md staged; 0 .py/.sh/hooks/tests
- [V] CREDITO · PASS · scope-verifier · ADR 0003 deposita el crédito del meta-cambio de ley
- [V] ZERO_LEAK · PASS · leak-verifier · 0 secretos en diff staged + ADR 0003
- [V] TECHO_ITER · PASS · gate · 1/3 iteraciones, bajo techo
- [V] OPEN_CLOSED · PASS · design-verifier · estable editado = §3 pto1+pto6 (caso legal c); resto AGREGA
- [V] ATOMICIDAD · PASS · design-verifier · 1 responsabilidad; lista de modelos runtime, no hardcode
- [V] COSTURA · PASS · design-verifier · reusa _coverage_state existente, sin generalidad especulativa
- [V] CASOS_LEGALES · PASS · scope-verifier · edición de estable justificada por cambio de contrato (c)
- [V] CIERRE_TRAS_PASS · PASS · gate · veredicto combinado PASS
- [V] CONFORMIDAD · N/A · design-verifier · prosa de ley, no código hexagonal
<!-- VEREDICTOS:END -->
- RETRO: la feature se dogfoodeó DOS veces — el operador la usó (declaró el modelo "fable sino opus") ANTES de que existiera, y el fallback se ejecutó solo cuando fable dio "unavailable", validando en vivo que la runtime-list debe mandar sobre la preferencia. Proceso (blameless): cero fricción; el Crisol lean (3 agentes para 1 dominio prose) confirmó la lección shift-left/minimalismo de v1.12.0 sin re-trabajo.
- Cierre: 2026-06-21 · commit de cierre único (.md-only: SKILL.md + template + ADR 0003 + ledger; sin código → el gate de cobertura no engancha en este commit) · SIN tag (release v1.13.0 = decisión deliberada aparte) · push a origin/main

### main — 2026-06-21 (release v1.13.0 — compuerta de modelo)
- STATUS: CLOSED
- Tier: fast-path
- Fecha: 2026-06-21
- TARGET: docker-local
- MODEL: opus (sello/forja mecánica; el operador autorizó el release "vamos por 1.13")
- Alcance: release v1.13.0 — `forjar-release.sh v1.13.0 --no-sign` re-selló los 10 archivos de la familia (6 SKILL.md + cargar/references/detectar-runtime.md + docs/decisions/0001/0002/0003) de v1.12.0→v1.13.0, y regeneró registry.json (6 skills, pin commit 7d4380f = el commit que pasó el Crisol de la compuerta de modelo; "se promueve lo que se probó"). Promueve la corrida CLOSED+PASS de la Compuerta de Modelo (Paso 0 fail-closed).
- FIRMA: minisign DIFERIDA (--no-sign, continúa la política de v1.10.3→v1.12.0): registry SIN firmar, sin `.minisig` stale.
- Veredictos: Sellos consistentes 10/10 == v1.13.0, 0 stragglers (grep confirmado por el líder) · leak-scan LIMPIO (forja, fail-closed) · registry pin commit 7d4380f. Gate Crisol habilitado (corrida CLOSED+PASS, TEST_COVERAGE no-NONE).
- TEST_COVERAGE: hooks/gate (tests/test-enforcer.sh 50/50, heredado de la corrida que se promueve)
- Cierre: 2026-06-21 · tag anotado v1.13.0 (lo crea el operador desde el navegador — el sandbox bloquea push de tags) · push del re-sello a origin/main

### main — 2026-06-24 (apéndice consultable: patrón de deploy build-once-promote, agnóstico + zero-leak)
- STATUS: CLOSED
- Tier: completo
- Fecha: 2026-06-24
- TARGET: docker-local (contenedor Linux efímero; el oráculo de esta corrida de prosa es scripts/leak-scan.sh + coherencia, corrido ACÁ)
- MODEL: opus (uniforme — el operador eligió "opus" pasando por la Compuerta de Modelo del Paso 0, fail-closed; PRIMER uso real de la feature v1.13.0)
- LEY: v1.13.0 (verificado — último tag remoto == copia local; §6)
- Alcance (apertura): agregar el patrón de deploy **build-once-promote** (CI buildea+pushea a un registry con REGLA 0 horneada → el PaaS solo pullea la imagen `sha-<commit>` → deploy disparado por el job CI, no por webhook) como **referencia consultable, descriptiva (NO normativa)** en `plugins/lucky/skills/arquitectura/references/deploy-build-once-promote.md` (el Steward la movió de crisol/references a **arquitectura/references** — es patrón de deploy/CD, primo de doce-factor.md; + 1 fila en el Router de arquitectura/SKILL.md; confirmado por el operador). Origen: doc local del operador validado en un proyecto piloto. CRÍTICO: el doc original trae identificadores específicos del proyecto (nombres de app/VPS/usuario, rutas de secretos, identities, productos vendor) → debe quedar **AGNÓSTICO + ZERO-LEAK** para el repo PÚBLICO: project-specifics → placeholders (`<app>`, `<owner>`, `<env>`, `<secrets-path>`); vendor-neutral (`PaaS`/`registry`/`secrets-vault`/`CI`, como el precedente "PaaS" de v1.10.0). El patrón queda intacto, lo específico se borra. Las references NO llevan sello ni registry (la forja no las enumera). Meta-cambio §6.
- MIGRATION_STRATEGY: N/A (sin DDL; solo .md de referencia)
- Conformidad-arq: N/A (referencia descriptiva, no código hexagonal)
- Iteraciones: 1/3 (Steward APPROVE 8 condiciones + Verificador PASS, sin re-trabajo)
- Planificación/Diseño: plan con el operador → Architecture Steward (opus) APPROVE con 8 condiciones. Decisión clave: ubicación arquitectura/references/ (NO crisol/) por razón-de-cambio (patrón deploy/CD, primo de doce-factor.md), confirmada por el operador. El Steward cazó huecos críticos en la lista de scrub: FQDNs/dominios (el leak-scan NO los caza — clase del leak v1.7), Lucky-* como prefijo, UUIDs/SHAs/slugs ajenos.
- Veredictos: Steward APPROVE (8/8) · Engineer (opus): 2 .md staged, scrub exhaustivo (~25 identificadores → placeholders/roles), fila en Router SKILL.md:76 · Verificador fresco (opus) PASS: DOBLE RED zero-leak (leak-scan.sh LIMPIO + grep de 21 identificadores del piloto = 0 ocurrencias; Coolify=0, ghcr/GHA=1 "p.ej." c/u, dominios=solo slug propio, IPs/UUIDs=0) + C4 descriptivo + OPEN_CLOSED + REGLA0 test-enforcer 50/50.
- TEST_COVERAGE: N/A (solo-docs, 2 .md; suite enforcer verde sin regresión)
<!-- VEREDICTOS:BEGIN -->
- runState: closing
- [V] REGLA0 · PASS · verificador · test-enforcer 50/50 exit 0 (docker-local)
- [V] TARGET · PASS · gate · docker-local; reference agnóstico, sin acción sobre infra real
- [V] MODEL · PASS · gate · opus (Compuerta de Modelo, primer uso real)
- [V] TEST_COVERAGE · N/A · verificador · solo-docs sin código testeable; suite enforcer verde
- [V] INDEPENDENCIA · PASS · verificador · fresco; evidencia propia (leak-scan + greps + test corridos por él)
- [V] SCOPE_CREEP · PASS · verificador · diff = 2 .md; núcleo SKILL.md intacto salvo 1 fila Router
- [V] ZERO_LEAK · PASS · verificador · leak-scan LIMPIO + 0/21 identificadores piloto + dominios/IP/UUID limpios
- [V] TECHO_ITER · PASS · gate · 1/3 iteraciones, bajo techo
- [V] OPEN_CLOSED · PASS · verificador · AGREGAR puro (reference nuevo) + 1 fila Router, formato consistente
- [V] ATOMICIDAD · PASS · verificador · 1 reference = 1 tema (build-once-promote), §0–§11
- [V] CIERRE_TRAS_PASS · PASS · gate · veredicto combinado PASS
- [V] CONFORMIDAD · N/A · verificador · referencia descriptiva, no código hexagonal
<!-- VEREDICTOS:END -->
- RETRO: el Steward cazó lo que el leak-scan NO ve — FQDNs/dominios del piloto (clase del leak v1.7 pero por dominio en vez de IP). Lección reconfirmada: para zero-leak en repo público, el scan mecánico es red de VALORES; los NOMBRES (proyecto/app/dominio) los caza el verificador-LLM. La doble red (scan + grep semántico) es lo que hace el cierre confiable. Proceso (blameless): cero fricción; Crisol lean (Steward→engineer→verificador) en 1 iteración.
- Cierre: 2026-06-24 · commit único (.md-only: 2 archivos de skill + ledger; sin código → el gate de cobertura no engancha) · referencia consultable, sin sello/registry/tag · push a origin/main

### main — 2026-06-24 (release v1.14.0 — apéndice de deploy build-once-promote)
- STATUS: CLOSED
- Tier: fast-path
- Fecha: 2026-06-24
- TARGET: docker-local
- MODEL: opus (sello/forja mecánica; el operador autorizó el release "se puede terminar de forjar")
- Alcance: release v1.14.0 — `forjar-release.sh v1.14.0 --no-sign` re-selló los 10 archivos de la familia de v1.13.0→v1.14.0, y regeneró registry.json (6 skills, pin commit 1d40c9e). Promueve la corrida CLOSED+PASS del apéndice consultable build-once-promote en `arquitectura/references/`: la referencia (que no lleva sello) viaja con el bundle de `arquitectura`, cuyo SKILL.md sí se re-selló a v1.14.0 → ahora la Ley-viva la ve en el tag.
- FIRMA: minisign DIFERIDA (--no-sign, continúa la política): registry SIN firmar, sin `.minisig` stale.
- Veredictos: Sellos consistentes 10/10 == v1.14.0, 0 stragglers (grep confirmado por el líder) · leak-scan LIMPIO (forja, fail-closed) · registry pin commit 1d40c9e. Gate Crisol habilitado (corrida CLOSED+PASS).
- TEST_COVERAGE: hooks/gate (tests/test-enforcer.sh 50/50, heredado)
- Cierre: 2026-06-24 · tag anotado v1.14.0 (lo crea el operador desde el navegador — el sandbox bloquea push de tags) · push del re-sello a origin/main
