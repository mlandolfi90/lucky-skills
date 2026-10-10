# Pasos para las skills: lo que dejaron el C4 y el buzón

Estado: **ABIERTA**. Cada paso espera la autorización de la operadora.
Fecha: 2026-10-05. Sesión custodia: `0033771e`.

Origen: dos trabajos del mismo día. El modelo C4 se contrastó contra el
catálogo y se corrigió; lo que no se arreglaba en el dibujo sino en una skill
quedó acá como paso. Y el buzón trajo 35 sugerencias: 34 de NetBox y
SecondBrian, más un pedido de mtk-chr que llegó por el canal directo.

Ninguna skill se tocó. Editar una skill pide la autorización explícita de la
operadora, y tocar código pide además el TARGET declarado.

## 1. Lo que ya se corrigió en el C4, sin tocar skills

- **Relación nueva, `invoca`**, para la llamada de una skill a otra de otra
  fase: 39 flechas en `docs/diagramas/c4/modelo/11-invocaciones.c4`, que se
  leen en cuatro vistas propias (`vistas/07-invocaciones.c4`). Las demás
  vistas la excluyen: sin esa línea, el panorama ganaba cinco flechas y cada
  vista de fase, cajas de otras fases.
- **Cómo se llegó a las 39:** 27 salieron del contraste con el catálogo. Un
  barrido de las 38 SKILL.md encontró después 66 menciones entre fases sin
  ninguna flecha; juzgadas una por una, 12 eran llamadas reales y se sumaron.
  El resto eran pasos del camino (ya están en `sigue`), menciones de
  jurisdicción, o arreglos de skills: esos quedaron en los pasos 4 y 5. La
  regla de qué entra está escrita arriba del archivo.
- **Dentro de una fase:** se agregaron `hotfix -[vuelve]-> crisol` y
  `arq_ubicar -[usa]-> mapa_colisiones`; `adopcion -> configurar_hooks` pasó
  de `sigue` a `usa`; se borraron `delegar -> slack_coordinacion` y
  `paralelizar -> estilar`, que ninguna skill sostiene. La descripción de
  delegar decía «sin régimen declarado, no se lanzan agentes»; la skill admite
  `REGIMEN=NONE`, y ahora lo dice.
- **Encendido:** se completaron las etiquetas de mapa-colisiones, documentar y
  revisor-seguridad. Se quitaron dos conteos que no se podían reproducir (los
  de cambio y cierre).
- **Comprobado:** `likec4 validate` en verde (22 archivos); 38 cajas de skill
  para las 38 carpetas de `skills/`. Las vistas curadas quedan idénticas a las
  de antes, salvo los arreglos de esta lista. Cada `invoca` se dibuja en una
  sola de las cuatro vistas, y las cuatro se miraron exportadas a PNG.

## 2. Cómo se hace cada paso

1. La operadora autoriza **ese** paso, en el chat.
2. `run_change.py observe` y clasificar: MICROFIX si sólo cambia texto,
   FEATURE si cambia conducta.
3. Si toca código (un script, el paquete, el validador): declarar el TARGET
   antes de editar.
4. Editar y correr lo barato: `run_validate_suite.py` y
   `python -m pytest tests/conformance -q` desde la raíz. Si se agrega o toca
   una guarda, quitarla a mano y ver el rojo.
5. `run_change.py close` con cierre FINAL. Commit `fix(...)` o `docs(...)`
   para PATCH, `feat(...)` para MINOR: `--impact AUTO` lo deduce.
6. `run_publicar_skill.py plan` y `apply`, con commit, tag y push confirmados.
7. Adoptar en lucky-skills (`run_adopcion.py`). Si la skill tiene copia en
   `~/.claude/skills`, reinstalarla desde el tag, con su propia autorización.
   El resto de la flota se entera por `sincronizar`.

## 3. Los pasos, en el orden recomendado

### Paso 1. ley-viva avisa cuando una copia personal tapa a la adoptada

Buzón NetBox S-01, aceptada. Medido en dos repos: el hook dice
`CURRENCY=VERIFIED` y corre otra versión.

- `skills/ley-viva/scripts/ley-viva-aviso.py`: después del throttle, compara
  la huella sin CRLF de `~/.claude/skills/<nombre>/SKILL.md` con la adoptada.
  Si difieren, imprime `SHADOWED=<skill personal vX tapa a adoptada vY>`,
  dentro del recorte a seis líneas del aviso; si son iguales, calla. Local,
  sin red y sin escribir.
- `SKILL.md`: un cuarto estado, «sombra», y el campo `SHADOWED=<...|NONE>`
  en la salida. Aclarar que `VERIFIED` no dice qué copia corre.
- Un test en `scripts/test_ley_viva_aviso.py`, con una personal distinta y
  otra igual.
- MINOR, 1.1.0 → 1.2.0. Toca código: el script corre como hook de Claude Code
  en esta PC.
- Va primero porque los demás pasos terminan en «adoptar», y hoy el aviso de
  «al día» puede mentir.
- Queda afuera la política sobre las copias personales: es una decisión aparte.

### Paso 2. Paquete lucky-auditoria-mcp 0.10.0

Doce aceptadas de SecondBrian (S-11, S-13, S-19, S-21 a S-24, S-26 a S-30) y
el pedido de mtk-chr: bajo HTTP, el cliente se anota una vez por proceso y no
por sesión (`identidad.py:38`, `enganches/fastmcp4.py:130`, en el tag
`auditoria-mcp-v0.9.0`).

- Partir de `main` (0.9.0, `ce38bae`), no del worktree
  `lucky-skills-auditoria-mcp`, que quedó en 0.7.0.
- Qué toca cada uno:
  - `registro.py`: la ruta absoluta es siempre carpeta, con su `.gitignore`
    (S-11); el id de sesión se valida y `ruta()` pasa adentro del `try`,
    también en `estado()` (S-19); la cabecera se marca después de escribirla
    (S-21); las palabras del activador no distinguen mayúsculas (S-22).
  - `redaccion.py`: `cargar` valida `largo_max` y `elementos_max` (S-23) y las
    claves y tipos de cada sección (S-24); con la redacción cerrada, toda
    herramienta queda opaca (S-26).
  - `lectores.py`: se saltean las líneas con `resultado:"error"` (S-13);
    `por-sesion` agrupa por MCP y sesión, con el mínimo y el máximo de
    `cuando` (S-29); un esquema desconocido da aviso (S-30).
  - `cli.py`: salida en UTF-8 (S-27) y comodines propios, con el README
    corregido (S-28).
  - `identidad.py` y el enganche fastmcp4: bajo HTTP, el cliente se toma de
    la sesión en cada llamada (mtk-chr).
- De la quinta tanda de mtk-chr (2026-10-09, buzón
  `20261009T205949Z-lucky-tool-mtk-chr-directo`), decidido por la operadora:
  - U: `escritor()` pregunta `if _SESION_DEL_TRANSPORTE:`, que es la
    variable de contexto y no su valor, y da siempre verdadero. Bajo stdio el
    archivo sale firmado con el pid, contra R2 (`identidad.py:146`).
  - S: el paquete escribe la línea `tipo:"apertura"` con `roots_declarados`,
    una vez por sesión bajo HTTP, como piden R1-bis y R3-bis. Hoy no la
    escribe ni la escribió nunca, y anota en `arnes.proyecto` la raíz que
    vino de `roots`, que R1-bis prohíbe. Manda la receta.
  - T: `verificar_enganche` con fastmcp 4 sólo mira la lista
    `servidor.middleware`. Que el kit haga un `tools/call` real por un
    cliente en proceso. Va con V: el primer camino de error se prueba por el
    middleware, no llamando a `registrar`.
  - R: el kit avisa si falta `[retorno]` o `[conteos]`, sin fallar: un MCP
    sin herramientas por lote no los necesita.
  - W: que una herramienta opaca pueda dejar ver campos declarados, como
    `escribe` en `chr_comando_crudo`.
- De mtk-chr, el 2026-10-10 (buzón `20261010T002121Z-lucky-tool-mtk-chr-directo`):
  `estado()` da como `acumulado.mas_viejo` el mínimo de los mtime
  (`registro.py:493-503`). En un archivo que sólo crece, eso es la última
  escritura. Se informan dos fechas, cada una con su nombre: la primera línea
  de cada archivo, que es lo más viejo, y la última escritura, que es lo que
  mira la retención. mtk-chr tiene una prueba que se pone roja cuando se
  arregle (`tests/test_estado_dice.py`).
- Cada arreglo con su test y su reversión a mano. Para mtk-chr, un caso del kit
  con dos clientes de nombre distinto.
- MINOR: cambia la forma de salida de `por-sesion` y lo que significa la ruta
  absoluta. Toca código.

### Paso 3. auditar-mcp 1.6.5: la receta dice lo que hace el paquete

**Primera parte publicada** el 2026-10-08 (`skill-auditar-mcp-v1.6.5`):
S-09, S-10 y S-31, la línea 23 sin `madrina`, y dos filas nuevas en R5 con
la evidencia de S-15 (ficha `CAP-6deeec8d2c5b`), más R1-bis ajustado para
que no contradiga la fila de Codex. La segunda parte va en otra versión,
después del paquete 0.10.0.

- Ya ciertas con 0.9.0: S-09 (R4 nombra todos los valores del activador),
  S-10 (R3: `arnes{id, sesion, proyecto}`) y S-31 (R9: `fallaron`).
- Después de publicar 0.10.0: S-11, S-22, S-26 y S-29, porque describen
  conducta nueva del paquete.
- En esa misma versión, la fila de Claude Code bajo stdio en R5 pasa a citar
  `CAP-39324677da1f`, que corrige a `CAP-6deeec8d2c5b`, y dice qué devuelve
  `roots/list`: el proyecto más los `additionalDirectories` de los settings
  que carga. Lo midió SecondBrian el 2026-10-08 (commit `4a6a321`): con los
  settings de usuario da dos raíces, y sin ellos, una. Que `--add-dir` también
  sume raíces no está medido.
- También en esa versión (Q, mtk-chr): la salida tiene que poder decir un
  cumplimiento parcial, como `CAMINOS_DE_ERROR=2/3` o `REDACCION` sin
  `WHITELIST_RETORNO`. Hoy sólo escribe el caso completo. Cuántos campos
  pide el método es de MapaObjetivo (H-91).
- En el mismo PATCH, quitar «y `madrina` (cuando la criatura es un MCP)» de
  `SKILL.md:23`. Es la segunda fila del paso 4.

### Paso 4. Seis declaraciones de un solo lado

Una skill dice que otra la llama, y la otra no lo dice. El C4 no las dibuja
hasta que las dos coincidan. En cada una, la operadora elige de qué lado se
arregla.

| Lo que dice | Dónde | La otra | Recomendación |
|---|---|---|---|
| documentar: «`cierre` la pide cuando el cambio tocó documentación» | `documentar/SKILL.md:12` | cierre 1.5.1 no nombra a documentar | Quitar la frase de documentar (PATCH). Sumarle un gate a cierre endurece todos los cierres, y el encendido por estado ya cubre el caso. |
| auditar-mcp: «la disparan `disenar` y `madrina`» | `auditar-mcp/SKILL.md:23` | madrina no la nombra, y hace skills, no MCPs | Hecho: auditar-mcp 1.6.5 ya no la nombra (paso 3). |
| estilar: «el carril Construir de `crisol` cuando el alcance es UI» | `estilar/SKILL.md:9` | crisol no nombra a estilar | Quitarla de estilar (PATCH): disenar ya la llama en su paso 4. |
| delegar: `paralelizar` corre bajo el régimen activo | `delegar/SKILL.md:40-44` | paralelizar no nombra a delegar | Acá la frase es correcta. Sumarla a paralelizar (PATCH): antes de lanzar, resuelve el régimen de delegar; sin régimen activo ni default del proyecto, declara `REGIMEN=NONE` y manda el harness (`delegar/SKILL.md:36-38`). |
| arquitectura-ubicar: «la dispara el carril Arquitectura de `crisol` o `disenar`» | `arquitectura-ubicar/SKILL.md:8-9` | disenar no la nombra: su paso 2 llama a arquitectura-descubrir | Quitar «o `disenar`» de arquitectura-ubicar (PATCH), salvo que disenar deba ubicar lo nuevo; en ese caso, sumárselo a disenar como paso. |
| memoria-del-taller: «la invocan precedente, cierre y autopsia» | `memoria-del-taller/SKILL.md:78` | precedente y autopsia hablan de «el saber» sin nombrarla; cierre sí la nombra | La llamada existe y el C4 la dibuja. Que precedente y autopsia la nombren donde dicen «el saber» (PATCH cada una): ella sabe qué backend y qué verbos usar. |

### Paso 5. Cinco REQUIRES sin una línea que diga para qué

El `manifest.env` declara la dependencia, y el SKILL.md no dice en ningún
lado para qué la usa. Desde afuera no se sabe si la dependencia es real o un
resto. Por cada una: escribir en el SKILL.md para qué se usa, o quitar el
`REQUIRES` si ya no hace falta (mirar antes el adaptador: puede usarla el
script y no el texto).

| Skill | REQUIRES |
|---|---|
| cambio | `sextante@2.0.0` |
| arquitectura-verificar | `mapa-colisiones@1.0.0` |
| autopsia | `cambio@1.0.0` |
| slack-coordinacion | `custodiar-secretos@1.0.0` |
| documentar | `sextante@2.0.0` |

### Paso 6. mapear-despliegue no dice cuándo se usa

Su `description` dice qué hace y nunca cuándo (`mapear-despliegue/SKILL.md:3`).
Es la única de las 38: en el C4 cuelga de «sin momento declarado». Hay que
darle un «Usar cuando…» que se pueda negar y pasarlo por la prueba de
`madrina`. PATCH.

### Paso 7. El validador de la suite no lee el frontmatter como Claude Code

Dejó pasar `precedente` y `red-de-desarrollo` con un `:` que rompe el YAML.
Ya están arreglados en 1.0.2 y 1.0.1. Con un YAML así, Claude Code descarta
en silencio todo el frontmatter.

- Dónde: `_parse_frontmatter`, en
  `adapters/reference_python/lifecycle_core/manifest.py:156`.
- Opción sin dependencia nueva: rechazar un `: ` adentro de un valor que no
  vaya entre comillas ni en bloque (`>-`). Agregar PyYAML pide su versión
  exacta, con pin `==`.
- Toca código.

### Paso 8. Restos menores

- **memoria-del-taller:** `references/backends/saber.md:17` y `:47` nombran el
  bus de LiteLLM, que es un proyecto detenido. PATCH: marcarlo como historia o
  quitarlo.
- **entonar:** `references/formas/decidir-en-puntos.md` tiene cambios sin
  publicar desde `skill-entonar-v1.1.1` (46 líneas agregadas y 5 borradas).
  Falta sólo el paso de publicación.

## 4. Para el saber: endoso ítem por ítem

Salieron cuatro fichas candidatas del buzón. Ninguna se escribe sin un sí
para cada una. `proponer` publica; `señalar` deja la ficha para revisión.

1. **proponer · FALSO-VERDE.**
   - Síntoma: ley-viva dice `CURRENCY=VERIFIED` y corre una versión vieja, con
     el rótulo `userSettings:<nombre>`.
   - Acción: antes de creer un «al día», comparar la huella y el
     `SKILL_VERSION` de la copia personal contra la adoptada.
   - Anti-acción: no reinstalar ni borrar copias personales sin autorización.
   - Evidencia: NetBox `607a0a5` y lucky-skills (cierre 1.4.0 en vez de
     1.5.1), los dos del 2026-10-05.
2. **proponer · GAP.**
   - Síntoma: una guarda prometida (la carpeta del registro se protege sola)
     no rige en el camino alternativo.
   - Causa: la guarda vive en la función del camino por defecto.
   - Acción: ponerla donde se cruzan todos los caminos, justo antes de
     escribir, y probar cada camino con su reversión.
   - Evidencia: paquete 0.9.0, `registro.py:291-306` (S-11).
3. **proponer · DRIFT.**
   - Síntoma: el lector del registro decide el fracaso con otro criterio que
     el escritor.
   - Acción: que el lector lea el campo `resultado` de la línea.
   - Prevención: un test de ida y vuelta por cada camino de error.
   - Evidencia: `lectores.py:154` y `enganches/mcp1x.py:94` (S-13).
4. **señalar · FALSO-VERDE.**
   - Síntoma: la latencia de un hook medida en transcripciones sale alta.
   - Causa: las transcripciones sólo guardan las corridas que imprimen; las
     calladas no quedan.
   - Acción: cronometrar el hook directo, con la marca fresca, y compararlo
     contra un python vacío.
   - Evidencia: el /doctor de NetBox contó 873 corridas, ninguna por debajo de
     0,8 s; con la marca fresca, `ley-viva-aviso` sale callado en 0,47 s
     contra 0,24 s de un python vacío (2026-10-05). Casos=1.

## 5. Lo que queda abierto en el buzón

- 11 sugerencias de SecondBrian quedaron en «falta evidencia». Cada una dice
  qué medir, y se reabren cuando llegue la medición. El 2026-10-08 llegaron
  dos fichas: la de S-15 entró en auditar-mcp 1.6.5, y la de S-01 todavía
  espera un segundo servidor no Python. Quedan 10.
- Las respuestas están en `docs/buzon/outbox/` y en el `inbox/` de cada
  destino. La decisión de cada sugerencia está debajo de ella, en
  `docs/buzon/inbox/`.
