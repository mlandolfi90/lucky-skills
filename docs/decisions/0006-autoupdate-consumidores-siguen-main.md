# 0006 — `autoUpdate: true` en la adopción: los consumidores auto-siguen main HEAD del plugin propio (el tag deja de ser el pin de distribución)

- estado: aceptado
- fecha: 2026-06-29
- decide: MLL (operador) vía Steward del Crisol
- tags de la familia al sellar: ~v1.17.2 (Crisol con adopción auto-actualizante)
- relacionado: ADR 0002 (gate de cobertura fail-closed, que junto al hook gatea main y vuelve seguro auto-seguirlo); `crisol/SKILL.md` §2 «Tags y promoción» (el tag ES el acto de promoción) · §2 «Pin total (cadena de suministro)» :222-229 (la regla cuya tensión se resuelve acá); `scripts/adoptar-crisol.sh` (donde se inyecta el flag); `.claude/settings.json` (dogfood del propio repo); `docs/IDEAS.md` (footer-bug y borde-del-Steward parqueados)

## Contexto

La "Ley viva" del Crisol vive en **dos capas**: (1) el **plugin instalado en
disco** (las skills que el host ejecuta de verdad) y (2) el **sello-prosa** (el
footer `esta copia = tag vX.Y.Z` que cada `.md` declara y que la red secundaria
de detección contrasta contra el repo). La capa que MANDA en ejecución es la
primera: lo que corre es el plugin cacheado, no lo que diga la prosa.

En Claude Code, un marketplace **github de TERCEROS** tiene el auto-update **OFF
por defecto**. Lo confirmamos con la doc oficial: una entrada de
`extraKnownMarketplaces` SIN `ref` sigue el **default branch (= main HEAD)**,
pero sin `autoUpdate` el host CLI **cachea el plugin al instalar** y queda
**pinneado** a esa copia hasta un `/plugin marketplace update` **manual**. El
resultado es una asimetría entre superficies: la **WEB** clona el repo fresco
por sesión (siempre al día), el **CLI NO** → los repos consumidores **"quedan
atrás"** respecto de main, aunque su prosa diga otra cosa.

Origen real del hallazgo: el operador shipeó varios releases en pocas horas y
notó que repos ya adoptados seguían corriendo una versión vieja del plugin —
la distribución por tag/cache no se propagaba sola al CLI.

## Decisión

`adoptar-crisol.sh` activa **`autoUpdate: true`** en la entrada `lucky-skills`
de `extraKnownMarketplaces` (y el propio repo lo dogfoodea en su
`.claude/settings.json`). Con el flag, los consumidores **auto-siguen main HEAD**
del plugin propio: el host re-sincroniza sin intervención, igual que la web.

Consecuencia de modelo: **el tag deja de ser el pin de distribución**. Pasa a ser
un **checkpoint nombrado** (release notes, punto de rollback, sello de
consistencia de la familia). **main ES el deploy** — lo que está en main HEAD es
lo que corre la flota.

## Tensión con Pin total (PIN_TOTAL) — resuelta

La regla §2 «Pin total» prohíbe el floating en lo que CONSUMIMOS de TERCEROS.
Literal (`crisol/SKILL.md` :226-227):

> **Prohibido floating** (`latest`, `main`, `*`, rangos abiertos) en lo que
> CONSUMIMOS. Una promoción ajena JAMÁS debe poder romper nuestro build.

`autoUpdate`-sigue-main **NO viola** esa regla, por dos razones que se sostienen
juntas:

1. **Artefacto PROPIO, no de un tercero.** lucky-skills es del MISMO `owner`
   (`mlandolfi90/lucky-skills`). El matiz §tags lo dice textual (:228-229):

   > **Matiz con §tags:** `latest` lo **publicamos** para nuestros propios
   > artefactos; **nunca lo consumimos** de un tercero.

   El floating prohibido = consumir `*`/`main` de un **tercero** (una promoción
   AJENA que no controlamos). Auto-seguir **nuestro propio** artefacto es la cara
   permitida del mismo matiz: lo publicamos y lo seguimos, no lo consumimos de
   afuera.

2. **main está gateado por el Crisol.** Una promoción a main solo ocurre tras un
   `PASS` cerrado (matriz de veredictos + el doble guardián, ADR 0002). No hay
   "promoción ajena" que pueda colarse: el único camino a main HEAD pasa por el
   gate. Por eso "una promoción ajena jamás debe romper nuestro build" se respeta
   por construcción — la promoción nunca es ajena ni nunca es no-gateada.

La regla protege contra el floating-de-tercero; acá hay auto-seguimiento del
propio artefacto Crisol-gateado. Son cosas distintas: la prohibición no aplica.

## Consecuencias

- **Positivas:** propagación **automática como la web** — cero fan-out manual,
  fin del "quedan atrás"; un release se vuelve visible para toda la flota sin
  tocar cada repo. main-gateado-por-Crisol significa que **"siempre-último" ==
  "siempre-aprobado"**: lo que se auto-sigue ya pasó el gate, así que seguir el
  borde no baja la calidad.
- **A vigilar:** un push a main llega a **TODOS** los consumidores **al
  instante** → el Crisol es ahora el **ÚNICO** gate de la distribución; su rigor
  es **load-bearing para toda la flota** (un FAIL que se cuele se propaga solo).
  **Back-fill:** las adopciones VIEJAS reciben el flag recién en su próxima
  corrida de `adoptar-crisol.sh` (la línea es incondicional para back-fillear
  entradas preexistentes) o editando su `settings.json` a mano.
- **Frontera / residual:** hosts **offline** o con **autoUpdate des-activado a
  mano** NO se actualizan; ahí la propagación automática no llega y entra la red
  secundaria de detección — el **footer Ley-viva** — para cazar el drift. Ese
  footer HOY tiene un bug (resuelve `git ls-remote` contra el origin del repo
  consumidor, no contra lucky-skills): parqueado, ver `docs/IDEAS.md`.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.3.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.
