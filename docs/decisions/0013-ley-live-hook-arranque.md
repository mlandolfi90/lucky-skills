# 0013 — ley-live: la ley se trae sola en cada arranque de sesión

- estado: aceptado
- fecha: 2026-07-10
- decide: MLL (operador) — "plomo aplica", tras el incidente del mismo día:
  una sesión nueva cargó v1.27.0 con v1.35.0 publicada
- tags de la familia al sellar: v1.36.0
- relacionado: skill ley (/ley sigue siendo el camino verificado); ADR 0006
  (autoUpdate de consumidores); DRIFT-007 (mordió en el 6b de /ley y se
  corrige acá); ADR 0010 (patrón de hooks de flota: fail-open + off-switch)

## Contexto

El autoupdate (ADR 0006) entrega al ARRANQUE de sesión, pero dependía de un
acto manual (`/ley`) para acercar el clon local al último tag. Resultado
real: el operador abrió una sesión y el harness sirvió la ley 8 versiones
atrás (v1.27.0 vs v1.35.0), con `/cumplimiento` inexistente como comando.
Peor: en esa máquina el harness cargaba desde un TERCER lugar
(`plugins/cache/...`) que ni el clon ni `installed_plugins.json` cubrían.
El flujo del desarrollador era: arrancar → notar el atraso → `/ley` →
REINICIAR → trabajar. Dos arranques y un comando para estar al día.

## Decisión

1. **Hook `ley-live.sh` (SessionStart, en el plugin → toda la flota):**
   espejo silencioso de los pasos 2-5 de /ley — último tag por version-sort,
   solo si el tag está en `origin/main` (respeta el caso DIFERIDO), solo con
   árbol limpio, `pull --ff-only`. **FAIL-OPEN total**: cualquier duda → no
   toca nada, la sesión arranca con lo que haya. Off-switch `LEY_LIVE=off`.
   No re-instala gate, no verifica integridad, no reporta: para eso está
   `/ley` (el camino verificado a demanda). La brújula sigue siendo el aviso.
2. **Junction cache→clon (acto de máquina, documentado en /ley paso 6c):**
   el snapshot del harness deja de ser copia y pasa a ser espejo del clon —
   muere la clase "actualicé el clon pero el harness carga otra carpeta".
3. **Fix del 6b de /ley:** el intérprete se resuelve por SONDA (`"$c" -c ""`),
   jamás `command -v` — el stub de la Store pasó ese check y el paso falló
   en silencio durante una corrida real (2ª validación de DRIFT-007, que
   sube a usos: 2).

## Postura de seguridad (lo que el operador firmó)

La actualización pasa de acto explícito a automática por arranque. Mitiga:
repo propio del único dueño, ff-only (jamás merge/force), solo tags ya en
main, fail-open (no puede bloquear una sesión), off-switch por env. El
camino con verificación de integridad sha256 (/ley paso 7) sigue existiendo
y es el recomendado ante cualquier sospecha.

## Consecuencias

- (+) Flujo del desarrollador: "abrí sesión y trabajá" — cada sesión NUEVA
  arranca con el último tag sin comandos ni doble arranque.
- (+) El costo es ~1 llamada de red por arranque (ls-remote); sin red la
  sesión arranca normal.
- (−) Un tag malo publicado llega solo a la flota en el próximo arranque —
  mitigado porque publicar tags es acto exclusivo del operador (forja+push).
- (=) Límite honesto: lo que el harness enumera al arranque sigue congelado
  POR sesión; el hook garantiza frescura del arranque siguiente, no del
  presente. Los CUERPOS de las skills sí se leen frescos al invocarlas.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.3.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.
