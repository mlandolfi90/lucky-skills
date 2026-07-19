---
id: 2026-07-19-versionado-artefactos
schema: corrida/1
tipo: corrida
estado: ACTIVE
creado: 2026-07-19
branch: main
titulo: "Versionado de artefactos como lectura del proceso — generacion.corridas.hotfixes.microfixes (ADR 0026 + rama 004)"
tier: "completo (cambia contrato: hotfix §4 deja de definir el contador y el paso de cierre pierde el 'sin sufijo beta'; norma nueva transversal a la flota → ADR + rama; >1 archivo)"
target: "pc-local (la forja; directiva durable del operador para lucky-skills)"
model: "opus (subagentes; orden del operador — pidió 'opus 4.6', el disponible en el harness es opus 4.8) — líder fable"
ley: "v2.8.0 (sello local == último tag, forjado hoy)"
iteraciones: "1/3 (Steward APPROVE 1ª con 4 correcciones inline zanjadas; roster fresco 4/4 PASS 1ª — tercera corrida consecutiva sin quemar iteración)"
runState: closing
cierre: "2026-07-19 · commits c081c40 (apertura+proyecciones juntas — lección del RETRO aplicada) + a7f2479 (plan+supuestos) + c3ba40d (ADR 0026 + rama 004 + hotfix §4/§Cerrar) + cierre en dos commits. Re-sello/tag DIFERIDOS al próximo forjar-release.sh."
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: lider, evidencia: "pc-local (directiva durable del operador; el qa2 verificó AHÍ sin degradar)"}
  - {regla: MODEL, veredicto: PASS, quien: lider, evidencia: "opus en steward/ingeniero/roster (el operador pidió 'opus 4.6'; el disponible es opus 4.8 y se le informó) — líder fable"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: steward+design-verifier, evidencia: "A/B archivos NUEVOS; C = extracción-a-rama (ADR 0018 §5) y D = corrección acoplada acreditada por ADR 0026 — casos legales declarados en el plan y confirmados sobre el diff"}
  - {regla: ATOMICIDAD, veredicto: PASS, quien: steward+design-verifier, evidencia: "rama 004 = LA definición · ADR 0026 = LA decisión · hotfix §4 = puntero+expresión; la semántica no se duplica"}
  - {regla: COSTURA, veredicto: PASS, quien: steward+design-verifier, evidencia: "rama con gatillo propio donde el sistema varía; extracción-a-rama correcta contra 0018 §5 (NO caso (b): exigir DESAPARECE habría sido error — la definición reaparece por diseño); cero maquinaria especulativa (diente diferido declarado)"}
  - {regla: CASOS_LEGALES, veredicto: PASS, quien: steward, evidencia: "C y D nombrados en el plan con su marco legal ANTES de tocar código (corrección inline 3 del Steward, zanjada)"}
  - {regla: CREDITO, veredicto: PASS, quien: scope-verifier, evidencia: "ADR 0026 ACEPTADA, frontmatter válido, refs recíprocas corrida↔ADR↔rama trazables; INDEX regenerado"}
  - {regla: SCOPE_CREEP, veredicto: PASS, quien: scope-verifier, evidencia: "10 archivos, mapa 1:1 a los actos A-E + housekeeping; fidelidad a la spec punto por punto (acumulados sin reset PROBADO por el ejemplo: con reset sería 2.0.0.0, quedó 2.13.4.27)"}
  - {regla: PARKING, veredicto: PASS, quien: scope-verifier, evidencia: "los dos diferidos (mapeo semver-de-3, diente mecánico) capturados como deuda declarada en rama 004 y ADR"}
  - {regla: REGLA0, veredicto: PASS, quien: quality-auditor-2, evidencia: "17/17 suites exit 0 corridas por ÉL en pc-local + registros-lint 0 + proyectar --check byte-idéntico; intérprete sondado (python3 no existe → python)"}
  - {regla: TEST_COVERAGE, veredicto: PASS, quien: quality-auditor-2, evidencia: "prosa normativa; el único artefacto con contrato ejecutable (frontmatter rama 004) cubierto por proyectar --check + test-ramas.sh (8/8)"}
  - {regla: RED_GREEN, veredicto: "N/A", quien: lider, evidencia: "la corrida no crea ni modifica tests (decisión de la spec: disciplina, no maquinaria prematura)"}
  - {regla: ZERO_LEAK, veredicto: PASS, quien: leak-verifier, evidencia: "leak-scan exit=0 + 10 archivos y 3 commits a mano: 0 leaks (matches = URL pública del repo y números del esquema que parecen IPs y no lo son)"}
  - {regla: PIN_TOTAL, veredicto: "N/A", quien: design-verifier, evidencia: "diff 100% .md sin dependencias; test-pin-scan corrido por él: 3/3, árbol sin floating"}
  - {regla: LISKOV, veredicto: "N/A", quien: design-verifier, evidencia: "sin implementación de abstracción"}
  - {regla: INTERFACE_SEGREGATION, veredicto: "N/A", quien: design-verifier, evidencia: "sin contrato multi-cliente nuevo"}
  - {regla: CIERRE_TRAS_PASS, veredicto: PASS, quien: gate, evidencia: "cierre tras 4/4 roster + gates verdes"}
  - {regla: MIGRATION, veredicto: "N/A", quien: gate, evidencia: "sin DDL"}
  - {regla: RESPONSIVE, veredicto: "N/A", quien: gate, evidencia: "no toca UI"}
  - {regla: CONFORMIDAD, veredicto: "N/A", quien: gate, evidencia: "no toca código hexagonal"}
  - {regla: SELLOS, veredicto: "N/A", quien: gate, evidencia: "no habilita release; sellos v2.8.0 intactos (verificado por qa2)"}
  - {regla: TAG_GATE, veredicto: "N/A", quien: gate, evidencia: "no se crea tag (git tag --points-at HEAD vacío, verificado por scope)"}
retro: "Primera corrida bajo las reglas de la cosecha de ayer, y las tres se estrenaron BIEN: (1) el plan cerró con 5 supuestos (ADR 0025) y el Steward los VERIFICÓ contra el repo — cazó un precedente mal citado (001 en vez de 003) que sin el bloque habría viajado invisible; (2) el mecanismo DESAPARECE (ADR 0024) obligó a clasificar C correctamente como extracción-a-rama en el plan — y el design-verifier confirmó que exigir DESAPARECE ahí habría sido un falso FAIL: la frontera extracción≠costura quedó ejercitada en vivo; (3) la apertura commiteó proyecciones JUNTAS (fricción TABLERO, dos RETROs seguidos — esta vez no pasó). Observación no bloqueante del design-verifier parkeable: hotfix §4 creció 6→11 líneas y el aterrizaje por ecosistema tiene dos hogares (anticipado por el supuesto 4; poda futura posible)."
bitacora: "N/A (sin disparador nuevo: la fricción TABLERO ya estaba capturada y esta vez se aplicó la lección; ningún falso-verde, ningún grep sin mapa)"
origen: "spec del operador (2026-07-19) optimizada por workflow de 9 agentes contra el repo real (fuentes de verdad derivables, conflicto hotfix §4 más profundo de lo declarado — la beta se caía al cerrar —, rama 004 como hogar, mapeo por ecosistema simplificado); spec final presentada y lanzada por orden: 'lanza la corrida tu fable tus sub agentes opus'"
alcance: "ADR 0026 (la decisión: 4 segmentos acumulados, sin reset a la derecha, commit por entrega ya-ley referenciada) · crisol/ramas/004-versionado-artefactos.md (la regla operativa, gatillo '¿qué versión le pongo?', nace estable por endoso registrado) · hotfix/SKILL.md §4 → puntero a rama 004 + conserva aterrizaje por ecosistema y stamp humano vX.Y.Z-bN · hotfix §Cerrar: reescribir 'Versión final SIN sufijo beta' (la beta ya no se cae: el 4to segmento acumula) · deslindes de una línea vs TAG_GATE/SELLOS/PIN_TOTAL"
nota_release: "re-sello + tag DIFERIDOS al próximo forjar-release.sh del operador (v2.8.0 se forjó hoy; no se forja en paralelo)"
---

Corrida abierta. Plan del líder (con supuestos, regla nueva de F3) → Steward
fresco (opus) → Ingeniero (opus) → roster fresco (opus) → cierre en dos
commits + sello.
