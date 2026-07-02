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
  Verificador corre el test ÉL MISMO en el TARGET (REGLA 0).
- **validated_on:** `main` · 2026-07-02 · `54a9176` (aplicada al propio catálogo: "el INDEX que miente" → nació `bitacora-lint`)
- **stale_si:** >90 días, o si el check pasa a ser fail-closed por contrato
- **origen:** RUN-LEDGER (lección recurrente "el test miente verde", c5/v1.11.0/v1.12.0; reaparecida cross-repo)   ·   **usos:** 3
- **REFS:** ADR 0002 (gate de cobertura fail-closed) · `bitacora-lint.sh` (ascenso parcial v1.19.0)   ·   **NEXT:** usos≥3 disparó la válvula: la mitad mecanizable YA ascendió (gate ADR 0002 + lint); queda decidir si "auditá el código, no el comentario" va a regla del Verificador
- **estado:** LIVE   <!-- promovida por delegación explícita de MLL ("decide tú", 2026-07-02) · panel 3/3 LIVE -->
