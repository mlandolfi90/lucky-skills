## [DRIFT-001] El test pasa en verde pero un check OBLIGATORIO está tras un `if` opcional

- **TIPO:** FALSO-VERDE / DRIFT (doc↔código)
- **SÍNTOMA (lo observable, NO la causa):** Una verificación pasa en verde, pero al
  auditar el código ves que un check que el comentario/spec marca como OBLIGATORIO
  está detrás de un `if opcional` que lo desactiva en silencio (ej.: una variable
  centinela ausente → el gate queda apagado y el verde no lo delata).
- **CAUSA-RAÍZ (1 línea):** El código derivó del contrato escrito; el verde mide que
  "no explotó", no que el invariante se aplicó.
- **ACCIÓN (pasos, máx 7):**
  1. Auditá lo que el CÓDIGO hace, no lo que el comentario promete.
  2. Confirmá que el check es fail-closed (config ausente → BLOQUEA, no pasa).
  3. Si era condicional → convertilo en invariante duro + test que falle sin él.
- **ANTI-ACCIÓN (evita re-derivar):** No confíes en el exit-code 0 ni en "verify
  pasó"; el verde NO garantiza que el invariante se aplicó. No leas solo el resumen
  del verificador previo: anclate al código real.
- **PREVENCIÓN:** verificación adversarial NO es opcional en código de seguridad; el
  Verificador corre el test ÉL MISMO en el TARGET (REGLA 0). Candidato a ascender a
  regla del gate.
- **validated_on:** `main` · 2026-06-13 · `<sha>`
- **stale_si:** >90 días, o si el check pasa a ser fail-closed por contrato
- **origen:** RUN-LEDGER (lección recurrente "el test miente verde", c5/v1.11.0/v1.12.0)   ·   **usos:** 2
- **REFS:** ADR 0002 (gate de cobertura fail-closed)   ·   **NEXT:** si reaparece en otro repo → ascenso a regla-gate
- **estado:** CANDIDATE   <!-- semilla destilada por el agente; el humano la promueve a LIVE -->
