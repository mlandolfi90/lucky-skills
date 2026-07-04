## [DRIFT-007] El parking (IDEAS.md) marca un ítem "pendiente" que un ADR/RUN-LEDGER posterior ya dio por EJECUTADO y cerrado — actuar sobre el parking re-corre una operación (acá destructiva)

- **TIPO:** DRIFT (parking ↔ ADR/ledger: mismo hecho, estado contradictorio)
- **SÍNTOMA (lo observable, NO la causa):** una entrada del parking dice `[X — pendiente]`
  (p.ej. `docs/IDEAS.md` "[C9 — pendiente] LITELLM_SALT_KEY UNSET… GATE DURO") y la tomás como
  trabajo a hacer; pero al leer el ADR relacionado (adenda) o una entrada más tardía del
  RUN-LEDGER, el ítem YA fue ejecutado y verificado (FIEL). Si la acción parkeada es destructiva
  (acá: `TRUNCATE LiteLLM_ProxyModelTable` + re-seed), re-correrla a ciegas es el daño.
- **CAUSA-RAÍZ (1 línea):** el parking es append-only y NO se cierra retroactivamente cuando el
  trabajo se ejecuta en otra corrida/ADR el mismo día → el "pendiente" queda fósil.
- **ACCIÓN (pasos, máx 7):**
  1. NUNCA trates el parking como dispositivo del estado. Es una lista de captura, no la verdad.
  2. Antes de ejecutar un ítem parkeado, cruzá el ADR relacionado (buscá su **Adenda**) y el
     RUN-LEDGER por el mismo tag (`grep -n "C9\|<tag>"`), quedate con el registro MÁS TARDÍO.
  3. Si el ADR/ledger dice EJECUTADO con FIEL (hash/completion 200), la acción está HECHA:
     NO la re-ejecutes.
  4. Resolvé el drift: tachá la entrada del parking marcándola `[HECHO — ver ADR NNNN Adenda]`
     (mismo patrón que las líneas ya cerradas del IDEAS.md).
  5. Si querés confirmación viva, verificá leak-safe (presencia + sha8, jamás el valor) — puede
     estar bloqueado por el clasificador (ver ANTI-ACCIÓN).
- **ANTI-ACCIÓN (el camino muerto — evita re-derivar):** NO re-correr la operación destructiva
  "por si acaso" (el `TRUNCATE`+re-seed ya se hizo; repetirlo es churn con riesgo). NO asumir que
  el `chequeo en vivo` está disponible: autenticarse al Infisical de prod y leer el salt/master
  (aún leak-safe) lo BLOQUEA el clasificador auto-mode ("Credential Exploration") — si lo necesitás,
  pedile al owner permiso explícito / token de Coolify, no lo fuerces.
- **PREVENCIÓN (cómo evitar reincidencia):** cuando una corrida CIERRA un ítem que vive en el
  parking, tacharlo en `IDEAS.md` es parte del cierre (no un extra); el veredicto `PARKING` de la
  corrida debe apuntar al parking que actualizó.
- **validated_on:** `dev` · 2026-07-04 · cross-read `Lucky-Auth-Plane` ADR 0009 Adenda II (C9 EJECUTADO: salt sha8 `dfa7b417`, litellm `/v1/models`=20, completion 200) vs `IDEAS.md:13` + `RUN-LEDGER:265` (ambos "[C9 — pendiente]")
- **stale_si:** >90 días, o si IDEAS.md pasa a cerrarse retroactivamente por convención (tacha automática)
- **origen:** Lucky-Auth-Plane ADR 0009 (durabilidad master key) + RUN-LEDGER corrida ROTACIÓN 2026-06-26   ·   **usos:** 1
- **REFS:** ADR 0009 Adenda II   ·   **NEXT:** si un ítem parkeado toca datos/secretos → cruzar ADR+ledger ANTES de ejecutar
- **estado:** CANDIDATE
