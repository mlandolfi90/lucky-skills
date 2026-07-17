---
id: 2026-07-16-leak-scan-ruta-windows
schema: microfix/1
tipo: microfix
estado: FAVORABLE
creado: 2026-07-16
comportamiento: "leak-scan.sh debe salir 1 ante una ruta absoluta Windows de otro usuario (hoy sale 0: la rama Windows del ERE no matchea nada)"
punto_tocado: "scripts/leak-scan.sh:61 — la regla 3 (RUTA-ABSOLUTA), UNA línea"
target: "pc-local (el gate corre acá y en la forja; directiva explícita del operador para este repo)"
tope: microfix
observacion: "Prueba A/B sobre el MISMO archivo (ruta Windows de otro usuario, backslashes simples): script de v2.5.0 → exit 0 LIMPIO (el leak pasaba en verde); script con la sonda → exit 1 LEAK. Batería 5/5: caza Windows y /home/ de usuario ajeno; calla ante elipsis (… y ...) y placeholders <asi>. Repo real post-sonda: exit 0."
escalado_a: null
refs: [diagnostico:2026-07-16-leak-scan-ruta-windows-muerta, corrida:2026-07-16-leak-scan-puente]
---
# Sonda: ¿arreglando el nivel de escape, el gate caza la ruta?

Hereda `zona_sospechada` y evidencia de
`diagnostico:2026-07-16-leak-scan-ruta-windows-muerta`. Tope confirmado por el
operador ("corré el microfix"), que coincide con el `tope_sugerido` del
diagnóstico.

## El defecto de fondo (medido antes de tocar)

Las tres alternativas de la regla 3 no son simétricas:

- `/home/[A-Za-z0-9_.-]+/` y `/Users/[A-Za-z0-9_.-]+/` usan clase **positiva** →
  un placeholder (`<otro>`, `…`) NO matchea, porque `<` y `…` no están en la
  clase. Documentar un ejemplo NO dispara el gate.
- La rama Windows usa clase **negada** (`[^\\"]+`) → matchea CUALQUIER cosa,
  incluida la elipsis. Encima está muerta por doble-escape.

O sea: la rama Windows está rota **y** además, al revivirla tal cual, pasaría a
disparar sobre nuestra propia documentación (medido: 2 líneas —
`crisol-leak-verifier.md:28` y `bitacora/entries/DRIFT-007.md:6`, ambas
elipsis). La segunda vive en el **espejo read-only** de la bitácora: no se puede
corregir a mano (se regenera desde el saber). Arreglar solo el escape convertiría
el gate en un bloqueador permanente de la forja.

## La sonda

UN punto, UNA línea: alinear la rama Windows con sus hermanas — escape correcto
(un nivel menos) **y** clase positiva con inicial alfanumérica
(`[A-Za-z0-9][A-Za-z0-9_.-]*`). Así:

- `C:\Users\<usuario-real-o-ficticio>\…` → **matchea** (el gate no distingue real
  de ficticio, y está bien: es fail-closed).
- `C:\Users\…` / `C:\Users\...` / `C:\Users\<otro>\` → **no matchea** (elipsis y
  placeholders quedan fuera por construcción, igual que en `/home/`).

Esto NO es una válvula ni un allowlist: es la misma forma que las otras dos
alternativas ya tienen. La lección v1.8.0 ("re-leak al documentar un fix"), que
el scanner declara en prosa desde hace versiones, queda mecanizada de rebote —
por simetría, no por excepción.

## Prueba negativa (obligatoria — la exige el diagnóstico)

Un gate que nunca se vio morder no está verificado. La sonda no se declara
FAVORABLE sin ver el rojo con una ruta Windows ajena y el verde con placeholders.

**Corrida en repo temporal descartable** (cero residuo en el repo real), con los
casos escritos por Python: el shell come una capa de backslashes y ya engañó dos
veces hoy — al líder y al propio leak-verifier.

| caso | esperado | obtenido |
|---|---|---|
| ruta Windows de otro usuario (backslash simple) | exit 1 | ✅ exit 1 |
| ruta `/home/<otro-real>/` | exit 1 | ✅ exit 1 |
| elipsis unicode `C:\Users\…` | exit 0 | ✅ exit 0 |
| elipsis ascii `C:\Users\...` | exit 0 | ✅ exit 0 |
| placeholder `<usuario>` / `<otro>` | exit 0 | ✅ exit 0 |

**La prueba A/B, que es la que decide** — MISMO archivo, dos scripts:

- `leak-scan.sh` de `v2.5.0` → **exit 0 · "LIMPIO · OK para push"** (el leak
  viajaba en verde)
- `leak-scan.sh` con la sonda → **exit 1 · `LEAK [RUTA-ABSOLUTA]`**

Repo real con el gate arreglado: **exit 0** — las 2 líneas de documentación que
el radio de explosión había detectado (`crisol-leak-verifier.md:28` y el espejo
`bitacora/entries/DRIFT-007.md:6`) quedan fuera por la clase positiva, sin
tocarlas. Eso importa: la segunda es espejo READ-ONLY y corregirla a mano se
habría perdido en la próxima regeneración desde el saber.

## Veredicto: FAVORABLE

Un punto, una línea, comportamiento corregido y verificado en ambos sentidos.
Sin residuo: no hizo falta tocar ningún segundo lugar.

## Lo que amerita formalización (decide el operador, NO se hace acá)

La sonda mecanizó de rebote la lección v1.8.0 ("re-leak al DOCUMENTAR un fix"),
que el scanner declaraba **en prosa, en su cabecera, sin mecanismo**. Hoy quedó
como propiedad del regex (clase positiva ⇒ los placeholders no disparan), no
como disciplina. Si eso merece ADR o entrada de bitácora, es juicio del operador
— el microfix solo lo señala.

