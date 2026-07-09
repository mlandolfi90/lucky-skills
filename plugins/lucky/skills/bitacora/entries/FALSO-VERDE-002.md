## [FALSO-VERDE-002] El hook con escape JSON a mano pasa su suite en verde, pero un control char crudo en el dato de entrada rompe el contrato (json.loads falla)

- **TIPO:** FALSO-VERDE
- **SÍNTOMA (lo observable, NO la causa):** un consumidor del output del hook
  (harness/parser) tira `Invalid control character at: line N column M` sobre el
  JSON emitido, aunque toda la suite del hook esté en verde y el exit sea 0; el
  `od` del output muestra bytes crudos < 0x20 (ej. `033` de ANSI) dentro del
  string.
- **CAUSA-RAÍZ (1 línea):** el escape JSON artesanal (awk/sed) cubre `\\`, `"`,
  `\t` — pero RFC 8259 exige escapar TODO U+0000–U+001F, y un ESC de ANSI pegado
  desde una terminal al dato fuente (síntoma del INDEX, config, etc.) pasa
  derecho.
- **ACCIÓN (pasos, máx 7, copy-paste si aplica):**
  1. En el bloque de escape del hook, tras los gsub de `\\`/`"`/`\t`, agregar:
     `gsub(/[[:cntrl:]]/, "", line)` (elimina lo restante < 0x20 y 0x7f).
  2. Al fixture del hook, sumarle un caso con bytes hostiles reales
     (`printf '\033[31m...\001'` en el dato fuente) y validar la salida con
     `python -c 'import sys,json; json.loads(sys.stdin.read())'`.
- **ANTI-ACCIÓN (el camino muerto):** confiar en que "la suite está verde" con
  fixtures de texto limpio; escapar solo los chars que se te ocurren en vez de
  cerrar la clase completa del RFC.
- **PREVENCIÓN (cómo evitar reincidencia):** todo hook que emita JSON lleva en
  su suite (a) un caso de bytes hostiles y (b) validación con `json.loads` real
  — el fuzz de INPUT MALFORMADO es donde vive el drift (espejo de DRIFT-001).
- **validated_on:** `main` · 2026-07-09 · `8c10837` (panel adversarial de la
  corrida timbre-de-juicio: repro exacto con ESC en fila LIVE del INDEX →
  json.loads rechazó; fix + 3 checks nuevos → push 25/25)
- **stale_si:** >90 días sin re-validar, O los hooks migran a un serializador
  JSON real (python/jq) en vez de escape a mano
- **origen:** RUN-LEDGER main 2026-07-09 (timbre de juicio, iter2)   ·   **usos:** 1
- **REFS:** ADR 0010 (enmienda) · RFC 8259 §7   ·   **NEXT:** n/a
- **estado:** CANDIDATE
