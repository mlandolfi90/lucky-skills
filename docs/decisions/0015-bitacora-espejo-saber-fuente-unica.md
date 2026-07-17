# 0015 — La bitácora local es un ESPEJO del saber central (saber = fuente de verdad)

- Estado: ACEPTADO
- Fecha: 2026-07-11

## Contexto

La bitácora nació LOCAL (en `lucky-skills`, autorada a mano, viaja a la flota por la LEY). El
proyecto MCP de conocimiento centralizó el saber en `lucky-saber` (servido por el MCP
`lucky-tool-saber`). Durante un tiempo coexistieron DOS bitácoras que divergieron (local 24, saber
snapshot 22); la skill decía "el local es el fallback autoritativo". El operador decidió cerrar la
divergencia: **el saber es la ÚNICA fuente de verdad; el local pasa a ESPEJO.**

## Decisión

El `INDEX.md` / `entries/` / `SENALES.md` de la skill `bitacora` son un **ESPEJO read-only regenerado
desde el saber**, NO autorado a mano:

1. **Generador `scripts/bitacora-espejo.py`:** clona `lucky-saber` (read-only), **DES-SCOPEA** (borra
   el campo `- **scope:**` de cada entry + la 8ª columna del INDEX → formato local 7-col, ≤35 líneas)
   y regenera el espejo. Idempotente (mirror byte-idéntico si el saber no cambió). Debe pasar el
   `bitacora-lint.sh` local.
2. **Captura → SIEMPRE al saber**, jamás al espejo: con el MCP, `saber_proponer_ficha` / `saber_senal`
   (→ `mcp-inbox`, el humano mergea con `saber_mergear`); OFFLINE (sin el connector), `/idea` (parking),
   propuesto al saber después. `Write, Edit` fuera del `allowed-tools` de la skill.
3. **Fleet-safety:** la flota SIN el MCP consume el espejo embebido en la LEY (grep del INDEX + el push
   hook del arranque); el espejo es el fallback FIEL, no una fuente independiente. El contrato de los
   hooks (tabla 7-col ordenada por `usos`, estado literal LIVE/CANDIDATE, link `[ID](entries/ID.md)`)
   se preserva por construcción.
4. **Refresh:** el operador corre el generador cuando el saber cambió y forja un release; la flota lo
   recibe por ley-live.

## Consecuencias

- La promoción CANDIDATE→LIVE, la poda y el ascenso ocurren en el SABER (el espejo los refleja tras la
  regeneración). El agente PROPONE; el humano mergea + promueve.
- Costo operativo: cada update de conocimiento para la flota OFFLINE pasa por saber → regenerar espejo
  → release de `lucky-skills` (un hop extra). Las sesiones ONLINE por el MCP ven el saber al instante.
- El generador se corre a mano (no acopla la forja a credenciales del saber). Reversible: el espejo es
  derivado; borrarlo/regenerarlo no pierde nada (la verdad vive en el saber).
- Relacionado: ADR 0002 de `lucky-tool-saber` (`saber_mergear`: merge en-sesión a main, additions-only-
  CANDIDATE, guardado estructuralmente).

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.7.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.
