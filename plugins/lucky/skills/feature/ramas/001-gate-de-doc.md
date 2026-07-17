---
id: 001-gate-de-doc
schema: rama/1
tipo: rama
estado: LIVE
canal: estable
creado: 2026-07-16
skill: feature
gatillo: "una feature transiciona a VIVA y el gate de doc muerde (autor↔lector, veredicto, desempate)"
origen: "endoso del operador (concejo:2026-07-16-equipo-doc, 5/5 APRUEBA_CON_CAMBIOS) + ADR 0021 §3 — nace estable por endoso registrado (precedente: crisol/ramas/003-decisiones-convocables)"
ultima_validacion: corrida:2026-07-16-equipo-doc-v1
refs: [adr:0021, adr:0019, adr:0020, adr:0018]
---
# Gate de doc — el bucle autor↔lector

El manual no vale porque exista: vale porque el usuario logra hacer la cosa
(ADR 0021). Esta rama es el CÓMO del paso 3 del tronco. El QUÉ (las dos
condiciones de `VIVA`) vive allá, siempre en contexto.

**El autor es `manualizador-2`, por nombre, siempre.** No es cosmética: el
harness descubre `plugins/lucky/agents/*.md` **por directorio y no lee
`estado:`** → el nombre del llamador es el ÚNICO de-ruteo existente. Spawnear
`manualizador` correría el prompt SUPERSEDED, que sigue escribiendo `doc:`
(su regla 5, `manualizador.md:42`) — justo lo que el ADR 0021 §2 prohíbe, y el
supersede quedaría decorativo.

## El bucle

1. **Corte previo — NO consume ronda.** `manualizador-2` devuelve
   `NO documentable aún: <qué falta>` → corte ANTES del bucle: **no** se
   spawnea al `lector-cero`, **no** se consume ronda. Se registra el motivo en
   `intentos:`; la feature sigue `EN-CONSTRUCCION`. (ADR 0021 §3)
2. **Ronda N — escritura.** Spawn de `manualizador-2` → escribe las piezas
   (`docs/manual/` si `audiencia: user`; `docs/sistema/` si `dev`, ADR 0021 §4)
   → reporta `{PIEZAS_BAJO_JUICIO}`. **No escribe `doc:`** (ADR 0021 §2).
3. **Leak-scan — fail-closed, ANTES del juicio** (ADR 0021 §6). `leak-scan.sh
   --staged` barre `git diff --cached` (:27-28) — lo staged, no lo untracked;
   sin flag barre `git ls-files` (:30) — lo trackeado. En ambos modos una
   pieza recién escrita y no agregada es INVISIBLE: el scan sale 0 sin mirarla.
   Por eso el `git add` es previo y obligatorio. Literal:

   ```bash
   git add docs/manual/ docs/sistema/
   OUT="$(bash scripts/leak-scan.sh --staged)"; RC=$?
   [ "$RC" -eq 0 ] || { echo "$OUT" | tail -5; exit 1; }
   ```

   El `$?` se lee **desnudo**; se formatea DESPUÉS. **PROHIBIDO**
   `bash scripts/leak-scan.sh --staged | tail -3 && …`: el exit del pipeline es
   el del `tail` → siempre 0 → gate decorativo. Hit → no hay `PASA` posible: se
   limpia y se re-corre. **No consume ronda** (es higiene, no comprensión).
4. **Juicio.** Spawn `lector-cero` **FRESCO** (`Read/Grep/Glob`, sin `Bash`; ve
   el manual + el cuerpo `funcionalidad` ≤15 líneas, nada más) → `PASA` |
   `FALLA` + tropiezos con severidad `BLOQUEA` | `COSMETICO`. Solo `BLOQUEA`
   justifica `FALLA`; `FALLA` sin tropiezo concreto = veredicto inválido →
   **re-spawn único**. Modo según `audiencia`: `user` = lograr CADA
   comportamiento del contrato; `dev` = N preguntas respondibles solo con el
   doc. (ADR 0021 §1/§4)
5. **Registro de CADA ronda — la huella es mecánica.** `intentos:` +=
   `{que: "doc ronda N", resultado: ..., ref: ...}` **y**
   `doc_veredicto: {estado: FALLA, ronda: N, ref: ...}`. Un `FALLA` jamás vive
   solo en el chat (ADR 0021 §2).
6. **FALLA ronda 1 → corrección.** Re-spawn de `manualizador-2` recibiendo
   `{TROPIEZOS}` **verbatim como dato** (se LEE, no se redacta: es el gatillo
   de corrección que el supersede del ADR 0021 §7 vino a dar) → volver a 3 →
   `lector-cero` **FRESCO** ronda 2.
7. **FALLA ronda 2 → sin tercer intento.** La feature queda
   `EN-CONSTRUCCION` y el desempate se **CONVOCA como decisión**
   (`crisol/ramas/003-decisiones-convocables` + ADR 0019 §2) → aparece en
   `TABLERO.md`. Nunca un tercer intento silencioso.
8. **PASA → el FLUJO cierra.** `/feature` (no el agente) escribe `doc:` +
   `doc_veredicto: {estado: PASA, ronda: N, ref: ...}` → la transición a `VIVA`
   es legal → regenerar proyecciones.
9. **Techo.** El bucle corre **FUERA del techo de 3 iteraciones del Crisol**:
   es acto de `/feature`, no de cierre de corrida. Un `FALLA` de doc no quema
   iteraciones de código ni bloquea el commit de una corrida PASS.
10. **Al `PASA`**, el `lector-cero` devuelve **1 línea por pieza** ("qué logré
    hacer con ella") — spot-check humano barato.

---
**Fuente: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.5.0` (cache local, NO la ley).**
