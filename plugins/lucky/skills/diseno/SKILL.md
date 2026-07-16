---
name: diseno
description: >-
  diseno — INTEGRADOR de diseño: conecta el repo actual con `impeccable`
  (pbakaus/impeccable, la autoridad de diseño anti-slop) y con el brand kit del
  operador (tokens Style Dictionary), sin definir UNA sola regla de diseño
  propia. Disparar con "/diseno", "integrá impeccable", "configurá el diseño de
  este repo", o ANTES de la primera tarea de UI de un repo que aún no tiene
  impeccable instalado. Instala PINEADO (submodule + tag exacto — jamás
  floating), vuelca los tokens del kit a design.json si existen, y corre un
  audit de humo. Las reglas de diseño viven en impeccable; la marca vive en el
  kit; esta skill solo tiende el puente.
allowed-tools: Bash, Read, Grep, Glob, Write, Edit
---

# diseno — el puente hacia impeccable (conductor, no autoridad)

Cadena: **esta skill (conduce) → impeccable (juzga la UI) → brand kit (los
valores contra los que juzga)**. Cero duplicación: acá NO hay paletas, ni
banderas, ni criterios estéticos — si los buscás, están en impeccable
(`/impeccable` una vez integrado) y en los tokens del kit.

**Ejes:** pineada (PIN_TOTAL del Crisol: versión exacta, jamás floating) ·
idempotente (correrla dos veces no rompe nada) · descubierta (el kit de marca
se detecta, no se asume) · honesta (sin kit → defaults de impeccable + aviso,
jamás inventa una marca).

## §0 — Arranque (al invocar, en orden; cada paso reporta en una línea)

1. **¿Impeccable ya está?** `Glob` por `.impeccable/` y por la skill instalada
   en `.claude/` (o el dir del harness activo). Si está: verificá el PIN —
   `git -C .impeccable describe --tags` debe dar un tag/commit EXACTO y el
   submodule debe estar commiteado. Pineado → saltá al paso 3. **Floating
   (rama suelta, sin submodule, o instalado por `npx` pelado) → bandera roja**:
   ofrecé re-instalar pineado (paso 2), no lo dejes pasar en silencio.
2. **Instalar PINEADO** (la única forma sancionada):
   ```bash
   git submodule add https://github.com/pbakaus/impeccable .impeccable
   TAG=$(git -C .impeccable tag --sort=-v:refname | head -1)
   git -C .impeccable checkout "$TAG"
   npx impeccable link --source=.impeccable --providers=claude
   ```
   Agregá el bloque `.gitignore` que impeccable documenta (config.local,
   caches, previews) y dejá trackeados `.impeccable/config.json`,
   `.impeccable/design.json` y la skill en `.claude/`. Commiteá el submodule
   pineado + el link en un commit propio (`chore: impeccable @ <tag> pineado`).
   PROHIBIDO: `npx impeccable install` a secas o `submodule update --remote`
   sin re-pin (floating de tercero — viola `PIN_TOTAL`).
3. **Cablear la marca (si hay kit).** Buscá tokens del brand kit en el repo:
   build de Style Dictionary (`tokens/` + config, o el output CSS/JSON que el
   kit distribuya). Hay kit → volcá sus valores a `.impeccable/design.json` y
   resumí la identidad en `DESIGN.md` (colores, tipografía, espaciado, voz):
   **la marca del operador manda sobre los defaults de impeccable**. Sin kit →
   avisá en una línea ("sin brand kit: impeccable juzga con sus defaults") y
   seguí — no inventes valores de marca.
4. **`PRODUCT.md`**: si no existe, creá el esqueleto con lo que el repo ya
   declara (README/propósito) y pedile al humano UNA línea de identidad si
   falta. Impeccable lo usa como contexto persistente.
5. **Humo:** corré `/impeccable audit` sobre una vista existente (si el repo
   aún no tiene UI, dejalo anotado y listo). Reportá el resultado tal cual —
   ese reporte es de impeccable, no tuyo.

## Actualizar impeccable (deliberado, jamás solo)

Update = **re-pin explícito**: `git -C .impeccable fetch --tags` → checkout
del tag nuevo → commit del submodule → corrida Crisol **fast-path** con
`BUMP_REASON: <tag-viejo> → <tag-nuevo>` en el ledger (regla `PIN_TOTAL`/
`BUMP_REASON` de la ley). `npx impeccable update` solo DESPUÉS del re-pin del
submodule (refresca el link, no elige la versión).

## Fronteras (fuente única — qué NO hace esta skill)

- **Reglas/criterios de diseño** → impeccable (sus detectores + comandos).
  Esta skill no opina de estética.
- **Valores de marca** → el brand kit del operador (tokens). Esta skill los
  transporta, no los define.
- **Gate duro de UI móvil** → la regla `RESPONSIVE` del Crisol (§2/§5), que
  sigue vigente e independiente: impeccable audita estética; el Crisol gatea
  proceso. No se pisan.
- **Estructura del frontend** → skill `arquitectura` (atomic-design). Sin
  cambios.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.4.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo
(`raw.githubusercontent.com/mlandolfi90/lucky-skills/<tag>/plugins/lucky/skills/diseno/SKILL.md`)
e informar al humano. **Caso de skill nueva:** si el tag remoto mayor existe
pero NO incluye `diseno/` (la skill nació en este bump), tratar como sin-red —
seguir esta copia y registrar `LEY: <tag> (local, skill nueva sin verificar)`.
Sin red: seguir esta copia y registrar `LEY: <tag> (local, sin verificar)`.
