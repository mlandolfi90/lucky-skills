## [DRIFT-004] Una pestaña abierta de ANTES del deploy manda el payload viejo al server nuevo y causa efectos destructivos

- **TIPO:** DRIFT (cliente-en-memoria ↔ contrato del server desplegado)
- **SÍNTOMA (lo observable, NO la causa):** Tras uno o varios deploys, una acción normal de la UI
  (ej. "Guardar") produce un efecto masivo/destructivo inesperado (ej. 17 de 21 modelos borrados
  del router), sin error visible. El server está sano y es la última versión.
- **CAUSA-RAÍZ (1 línea):** el JS de una pestaña se carga UNA vez y queda en memoria — no se
  actualiza con el deploy; la pestaña vieja manda el payload del contrato viejo y el server
  (retro-compatible) lo ejecuta con la semántica vieja (ej. `{active}` sin `disabled` = borrar
  todo lo no-activo).
- **ACCIÓN (pasos, máx 7):**
  1. Exponé la VERSIÓN de build del front (sha horneado en la imagen) en un endpoint liviano.
  2. Usá el poll que ya exista (ej. status cada 2s) para comparar versión servida vs versión cargada.
  3. Ante mismatch: banner "La página se ha actualizado — Actualizar ahora / Luego".
  4. Con "Luego": aviso persistente discreto Y **deshabilitá las acciones de ESCRITURA** hasta
     recargar (leer sí, guardar no) — el vector es el write con payload viejo.
  5. Restauración del incidente: re-apply del set completo desde la fuente de verdad (catálogo).
- **ANTI-ACCIÓN (el camino muerto — evita re-derivar):** NO lo resuelvas solo con una guardia
  server-side anti-borrado-masivo (parche del síntoma: molesta al uso legítimo y no cura otras
  divergencias de contrato); NO fuerces `location.reload()` sin preguntar (pisa la edición a
  medio hacer del operador).
- **PREVENCIÓN (cómo evitar reincidencia):** todo front con polling + deploys frecuentes lleva
  detección de versión desde el día 1; al diseñar contratos v2 retro-compat, preguntate qué hace
  un CLIENTE v1 vivo contra el server v2 (la retro-compat del server es exactamente lo que
  ejecuta la semántica vieja).
- **validated_on:** `dev` · 2026-07-03 · `f8feddc` (incidente) — fix del aviso: corrida
  portal-version-notice (en curso al destilar)
- **stale_si:** >90 días, o si el portal deja de ser SPA-de-pestaña-larga / cambia el mecanismo de deploy
- **origen:** Lucky-Auth-Plane RUN-LEDGER (models-disable-route, INCIDENTE anexo 17-modelos)   ·   **usos:** 1
- **REFS:** ADR 0010 (contrato apply v2)   ·   **NEXT:** si reaparece en otro front del stack → patrón cross-repo, candidato a checklist de UI
- **estado:** CANDIDATE
