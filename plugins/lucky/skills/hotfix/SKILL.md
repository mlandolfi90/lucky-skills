---
name: hotfix
description: >-
  Hotfix — permiso de trabajo en caliente: iterar un fix EN VIVO con el
  operador probando cada versión, sin pagar una corrida Crisol por intento.
  Disparar cuando el operador diga "/hotfix", "probemos rápido", "fix en
  caliente", "estoy acá mirando/probando", o cuando un debug entre en ciclo
  prueba-error con el humano presente dando veredictos. Abre UN permiso
  (ACTIVE + runState wip), versiona betas -bN con su veredicto guardado en un
  vault, y formaliza con UNA corrida Crisol al final solo con la solución.
  NO usar para cambios con solución ya conocida (eso es corrida Crisol
  directa), NI sin operador presente (sin veredicto humano no hay ciclo), NI
  contra @testing/@production (solo mesa caliente).
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# Hotfix — permiso de trabajo en caliente

En seguridad industrial, el trabajo con fuego no se prohíbe: se hace bajo
**permiso** — declarado, acotado, con vigía y con cierre. Acá igual: iterar
a ciegas quemó ~10 versiones y horas en el caso fundacional (popover-bleed);
pagar una corrida Crisol completa por cada intento fallido quema recursos.
Este carril usa lo que la ley YA permite (ACTIVE + `runState: wip` = editar
y WIP-commitear sin matriz; la matriz se paga UNA vez, al cierre) y le suma
la disciplina que evita la adivinanza serial.

## §Abrir (el permiso)

**0. Colisión:** si ya existe una entrada ACTIVE para el branch (hotfix u
otra), NO abras una segunda — el invariante es UNA ACTIVE por branch y el
gate juzgaría la matriz equivocada. O te sumás al hotfix existente (mismo
vault, continuás la numeración -bN donde quedó) o frenás y resolvés con el
humano cuál corrida manda.

**1. Entrada en RUN-LEDGER** — bloque mínimo COMPLETO (el gate exige Tier,
Fecha y TARGET reales o bloquea la primera edición):

```markdown
### <branch> — <fecha> (hotfix)
- STATUS: ACTIVE
- Tier: fast-path (provisional — se re-clasifica al cierre)
- Fecha: <fecha>
- TARGET: <target confirmado>
- MODEL: <modelo>
- Alcance: hotfix: <síntoma en una línea>
- BASE: <sha corto del commit base>
<!-- VEREDICTOS:BEGIN -->
- runState: wip
<!-- VEREDICTOS:END -->
```

El bloque VEREDICTOS va desde el día 0: el gate solo lee `runState:` DENTRO
del bloque — un `closing` escrito afuera es invisible y el cierre pasaría
SIN matriz (fail-open silencioso).

**2. Frontera de TARGET:** hotfix solo contra mesa caliente (`pc-local`,
`docker-local`, `paas:…@dev`). Contra `@testing`/`@production` se REHÚSA y
se redirige al carril de promoción; si el operador insiste igual, su
confirmación explícita queda registrada en el vault.

**3. El vault:** `docs/refactor/_hotfix/<slug>-<fecha>/` con `INTENTOS.md`.

**4. Versionado del artefacto:** fijá la gramática REAL del artefacto y la
etiqueta del stamp — extensiones de navegador: cuarto segmento entero
(`X.Y.Z.N`; el manifest no admite sufijos); semver/npm: `X.Y.Z-b.N`;
PEP 440: `X.Y.ZbN`. El stamp VISIBLE (UI/log/consola) siempre muestra la
etiqueta humana `vX.Y.Z-bN` — el operador confirma en segundos qué versión
prueba.

## §El registro (hotfix versionados con su resultado guardado)

`INTENTOS.md` = una tabla, una fila POR beta, escrita ANTES de la siguiente:

```markdown
cosechado: no

| versión | commit | hipótesis | cambio (1 línea) | veredicto | evidencia |
|---|---|---|---|---|---|
| v0.9.10-b2 | a1b2c3d | margin del checkbox | reset margin input | ✗ "sigue igual" | — |
```

- **WIP-commit POR CADA bump -bN** (no "cada tanto": un rollback perdería
  las betas intermedias y el vault guardaría el veredicto de -b3 sin su
  código). La columna `commit` ata cada fila al código exacto — el vault es
  consultable de verdad (`git show <commit>`). Protocolo seguro: add
  explícito de los paths tocados + vault, jamás `-A`.
- **Veredictos:** `✓` resuelto · `~` parcial · `✗` sin efecto/empeoró.
  Siempre símbolo + cita textual del operador. `~` NO quema la hipótesis
  (el siguiente -bN la REFINA, no salta a otra); `✗` suma strike.
- **Stamp confirmado o no hay fila:** el veredicto solo se registra si el
  operador confirmó el stamp de la versión que probó; stamp ≠ versión
  entregada ⇒ se repite la prueba (un ✗ sobre código viejo quema para
  siempre una hipótesis correcta — DRIFT-008).
- **Veredicto diferido:** el operador puede diferir ("lo pruebo después") →
  fila `pendiente`, tope UNA a la vez (dos betas sin veredicto no se
  distinguen al probar). Al cerrar, ninguna queda `pendiente`: se resuelve
  o se marca `no probada`.
- **Hipótesis quemada (✗) jamás se repite** — la tabla es la memoria
  anti-círculos.
- **ZERO_LEAK:** los veredictos se transcriben con scrub (rutas→`<ruta>`,
  hosts/IPs→`<host>`, jamás volcados de consola completos). El vault viaja
  a un repo público y el leak-scan de TODAS las forjas futuras barre
  `git ls-files`: un vault sucio brickea los releases.

## §Ciclo (la disciplina)

1. **UN cambio por ciclo** — jamás dos hipótesis juntas. Bump + stamp +
   WIP-commit.
2. **Revertí la hipótesis descartada ANTES del próximo ciclo**
   (`git restore` del archivo tocado): cada -bN = BASE + hipótesis viva.
   El árbol nunca acumula hacks — un veredicto sobre árbol sucio está
   contaminado por las betas anteriores.
3. Entregá al operador **QUÉ probar en 1 línea** (pasos exactos, incluido
   el refresh correcto — F5 de la PÁGINA si es extensión) → esperá su
   veredicto → fila en la tabla.
4. **2 strikes ⇒ instrumentar** (GREP-004): segundo `✗` sobre el mismo
   síntoma → obligatorio medir (log de estado real) antes del tercer
   intento. También: 3 `~` consecutivos sobre la misma hipótesis ⇒
   instrumentar (refinar a ciegas es la misma adivinanza).
5. Tras todo reemplazo masivo (`replace_all`/sed global): releé el diff con
   foco en las líneas agregadas en esta sesión ANTES de entregar (GAP-008 —
   una beta rota por edición quema un round-trip entero del operador).
6. Si armás un preview/harness: REPRODUCE los defaults del entorno, jamás
   los normalices, y **validación cruzada obligatoria** — ninguna medición
   del preview alimenta una hipótesis hasta coincidir con la misma medición
   en el entorno real (FALSO-VERDE-003).
7. Al primer síntoma que matchee el INDEX de la bitácora: abrí esa entrada
   (pull dirigido).

**Techo de iteraciones:** los ciclos beta con operador presente NO cuentan
para el techo de 3 del Crisol (ese techo es para loops Plan↔FAIL autónomos;
acá el circuit-breaker es 2-strikes + el operador decide seguir o parar).
`Iteraciones: n/3` del cierre cuenta SOLO los ciclos de la formalización.

## §Cerrar (la formalización)

**Con solución** — secuencia exacta, forward-only (los WIP quedan en la
historia como respaldo; jamás rewrite):
1. `SOLUCION.md` en el vault (el fix exacto + qué intentos se descartan) y
   el patch de referencia: `git diff <BASE> -- <paths>` → `hotfix-fuente.patch`.
2. Árbol a BASE+solución: `git restore --source=<BASE> -- <paths tocados>`
   → aplicar SOLO el diff de la solución.
3. **Re-clasificá el Tier** con el checklist §1 del Crisol sobre el diff de
   la SOLUCIÓN — si da completo, el cierre lleva Steward/COLLISION-MAP
   (sin esto el carril sería un bypass fast-path para diffs grandes).
4. Matriz completa + `runState: closing` DENTRO del bloque VEREDICTOS +
   commit de cierre. Versión final SIN sufijo beta.

**Sin solución** (se agota tiempo/paciencia): WIP-commit del vault PRIMERO,
fuente revertida a BASE, cierre honesto (RETRO), vault preservado.

**Cosecha — común a ambas ramas** (el caso fundacional cerró CON solución y
aun así produjo 6 entradas): si dolió — **≥3 filas en INTENTOS.md o cierre
sin solución** — ofrecé la cosecha por INTENSIDAD de la bitácora con el
vault como material. ANTES de ofrecer: leé la marca `cosechado:` del header;
si ya tiene fecha e IDs, reportalos y NO destiles de nuevo. Al cosechar:
estampá `cosechado: <fecha> → <IDs>`.

El vault entra a los INPUTS del leak-verifier del cierre (viajó en
WIP-commits antes de que nadie lo mirara — el cierre lo revisa entero).

**Huérfana:** si encontrás una ACTIVE con `Alcance: hotfix:` de una sesión
muerta — con el operador presente: reanudá desde INTENTOS.md y continuá la
numeración; sin operador: cierre honesto, vault preservado, fuente
revertida a BASE. (El protocolo de huérfanas del Crisol no aplica acá: un
hotfix no tiene techo 3 ni COLLISION-MAP.)

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v1.35.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.
