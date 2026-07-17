---
id: 2026-07-16-leak-scan-puente
schema: corrida/1
tipo: corrida
estado: CLOSED
creado: 2026-07-16
branch: main
titulo: "Puente de gate del microfix leak-scan (regla 6 de la escalera)"
tier: "fast-path (1 archivo, 1 línea, solución conocida del diagnóstico; no toca contratos)"
target: "pc-local (el gate corre acá; directiva explícita del operador)"
model: "fable (uniforme)"
ley: "v2.5.0 (recién forjada en esta sesión)"
iteraciones: "1/3 (convergió: solución conocida del diagnóstico)"
runState: closing
cierre: "2026-07-16 · commit del toque · el juicio vive en microfix:2026-07-16-leak-scan-ruta-windows"
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: líder, evidencia: "pc-local (el gate corre acá; directiva explícita del operador)"}
  - {regla: MODEL, veredicto: PASS, quien: líder, evidencia: "fable (uniforme) — sin subagentes: sonda de 1 línea"}
  - {regla: REGLA0, veredicto: PASS, quien: líder, evidencia: "batería 5/5 en repo temporal + prueba A/B sobre el mismo archivo: script v2.5.0 exit 0 (leak en verde) vs sonda exit 1 (bloquea); repo real exit 0. Casos escritos por Python: el shell come backslashes"}
  - {regla: TEST_COVERAGE, veredicto: PASS, quien: líder, evidencia: "prueba negativa manual 5/5 + A/B; leak-scan no tiene suite propia en el repo (brecha ya declarada en la corrida equipo-doc-v1)"}
  - {regla: ZERO_LEAK, veredicto: PASS, quien: líder, evidencia: "leak-scan (arreglado) sobre el repo real: exit 0 LIMPIO. Los casos de prueba vivieron en repo temporal descartado; cero rutas reales en los artefactos"}
  - {regla: SCOPE_CREEP, veredicto: PASS, quien: líder, evidencia: "1 línea (leak-scan.sh:61), exactamente el punto del diagnóstico; las 2 líneas de doc del radio de explosión NO se tocaron (la clase positiva las deja fuera)"}
  - {regla: PARKING, veredicto: PASS, quien: líder, evidencia: "la formalización de la lección v1.8.0 se SEÑALA en la fila del microfix como juicio del operador; no se implementa acá"}
  - {regla: CIERRE_TRAS_PASS, veredicto: PASS, quien: líder, evidencia: "commit tras veredicto FAVORABLE verificado"}
  - {regla: TECHO_ITER, veredicto: PASS, quien: líder, evidencia: "1/3"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: líder, evidencia: "caso legal (a) BUG: la rama Windows del ERE no matchea nada — se toca directo, OCP protege comportamiento correcto, no defectos"}
  - {regla: ATOMICIDAD, veredicto: PASS, quien: líder, evidencia: "1 línea; leak-scan.sh 105 líneas vs T=400"}
  - {regla: MIGRATION, veredicto: "N/A", quien: gate, evidencia: "sin DDL"}
  - {regla: CONFORMIDAD, veredicto: "N/A", quien: líder, evidencia: "tooling sin capas"}
  - {regla: TARGET_ENV, veredicto: "N/A", quien: líder, evidencia: "pc-local sin @env"}
  - {regla: RESPONSIVE, veredicto: "N/A", quien: líder, evidencia: "sin UI"}
  - {regla: FUENTE_VERDAD, veredicto: "N/A", quien: líder, evidencia: "no toca testing/prod"}
  - {regla: PIN_TOTAL, veredicto: "N/A", quien: líder, evidencia: "no toca dependencias"}
  - {regla: INDEPENDENCIA, veredicto: "N/A", quien: líder, evidencia: "fast-path/puente sin subagentes; la independencia la aporta la prueba A/B contra el script de v2.5.0 (artefacto real, no prosa)"}
refs: [microfix:2026-07-16-leak-scan-ruta-windows, diagnostico:2026-07-16-leak-scan-ruta-windows-muerta]
---
- ORIGEN: **puente de gate**, no corrida propia. La regla 6 de la skill
  `microfix` lo manda: la sonda toca código en un repo adoptado y el gate
  (Fase 1) exige una fila `ACTIVE` proyectada al RUN-LEDGER para desbloquear la
  edición. Los guardianes todavía no saben leer peldaños de la escalera; cuando
  la Fase 2 se lo enseñe, este puente muere y el microfix será su propio permiso.
  **El juicio real vive en la fila del microfix** — acá solo está el permiso.
- Alcance: exactamente el del microfix — `scripts/leak-scan.sh:61`, una línea.
  Nada más entra.
- MIGRATION_STRATEGY: N/A (sin DDL)
- RETRO (blameless): el puente hizo lo suyo — la sonda pudo tocar código sin
  inventar una corrida completa para 1 línea. Lo que el puente NO evita: hay que
  abrir DOS filas (microfix + corrida) para un cambio de una línea, y el juicio
  vive en una mientras el permiso vive en la otra. Es el costo declarado de la
  Fase 1 del gate, y la Fase 2 (guardianes que leen peldaños) lo borra. Segunda
  vez en el día que el escapado del shell engaña a un verificador: los casos de
  prueba de patrones se escriben por Python, nunca retipeando en bash.
