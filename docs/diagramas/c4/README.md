# Flujo de las skills — modelo LikeC4

El diagrama del **camino**: de una observación hasta un deploy, y el ciclo aparte
con el que el Taller fabrica las skills que ese camino usa.

No confundir con [`docs/diagrams/skills-interconexion.drawio`](../../diagrams/skills-interconexion.drawio),
que dibuja otra cosa: el grafo de `REQUIRES` entre las 37 skills. Aquel dice
**qué skill necesita cuál**; éste dice **en qué orden se usan**.

## Verlo

```bash
likec4 serve docs/diagramas/c4        # navegador, con recarga en caliente al editar
likec4 export png docs/diagramas/c4 -o /tmp/salida
```

Las vistas, de más general a más detallada:

| vista | qué muestra |
|---|---|
| `index` | Panorama: las fases y cómo se encadenan |
| `recorrido` | El camino feliz, numerado paso a paso |
| `*_detalle` | Qué skills viven dentro de cada fase |
| `catalogo_detalle` | El ciclo propio del Taller |

## Cómo está partido, y por qué

Cada archivo contesta **una** pregunta, para que un cambio toque un solo lugar:

```
specification.c4          Qué clases de cosa hay y cómo se ven. Cero contenido.
modelo/00-actores.c4      Quién decide y qué queda escrito.
modelo/01..09-*.c4        Qué skills viven en cada fase. Una fase, un archivo.
modelo/99-flujo.c4        EL CAMINO: cómo se encadenan las fases entre sí.
vistas/*.c4               Qué se dibuja y con qué layout.
```

La separación que más rinde es la de `99-flujo.c4`: los archivos de fase dicen
**qué hay adentro**, y solo ese dice **cómo se conecta**. Reordenar el flujo no
obliga a tocar ninguna skill, y agregar una skill no obliga a tocar el flujo.

## Recetas

**Agregar una skill nueva.** Un solo archivo — el de su fase:

```likec4
mi_skill = skill 'mi-skill' {
  description 'Qué hace, en una frase.'
}
```

El identificador va con guión bajo (`mi_skill`) porque LikeC4 no acepta guiones
medios ahí; el nombre real va entre comillas y ése es el que se dibuja. No hace
falta tocar las vistas: `include *` la levanta sola.

**Mover una skill de fase.** Cortar el bloque y pegarlo en el otro archivo. Si
alguna relación la nombraba por ruta larga (`construir.estilar`), corregir esa
línea.

**Cambiar el orden del flujo.** Solo `modelo/99-flujo.c4`.

**Cambiar colores o formas.** Solo `specification.c4`.

**Relaciones.** Hay tres clases declaradas, y el color las distingue sin leer:

```likec4
a -[sigue]-> b 'el camino normal'          // verde
a -[usa]-> b 'se la invoca desde acá'      // gris punteado
a -[vuelve]-> b 'algo no cerró'            // rojo cortado
```

## Tres cosas medidas, para no repetir el tropiezo

- **Las etiquetas (`#tag`) no entraron.** Se probó `tag transversal` y
  `tag #transversal` en `specification.c4`, y en las dos el compilador dejó
  `tags: []` **y además cortó el parseo** del resto del bloque: catorce skills
  desaparecieron del modelo en silencio, sin error visible. Por eso acá no hay
  ninguna etiqueta, y lo que hubieran marcado (portón, autoriza) está dicho en
  la `description`. Si alguien las hace andar, que lo anote acá.
- **El modelo se comprueba contra el repo**, no a ojo. Las 37 cajas son las 37
  carpetas de `skills/`: ni una inventada ni una faltante, verificado el
  2026-09-23. Al agregar una skill al catálogo, este modelo queda corto — y no
  avisa solo.
- **`include X -> *` colapsa los destinos en su fase.** Medido el 2026-09-23 al
  escribir las vistas de encendido: `include pedido, pedido -> *` dibujó las
  cinco *fases* en vez de las nueve *skills*, y fundió dos etiquetas en `[...]`.
  La vista existía y no daba error: simplemente mostraba otra cosa. En estas
  vistas los destinos van **nombrados uno por uno**. Es verboso y es correcto.

## La capa de encendido (2026-09-23)

`modelo/10-disparadores.c4` contesta una pregunta que el resto del modelo no
contestaba: **qué prende cada skill y, sobre todo, qué la deja apagada.**

`madrina` exige que el disparador sea *negable* — que ante una tarea cualquiera
se pueda contestar "no, este no es el momento" sin ponerse a discutir. Un
disparador que nunca es falso es un default encubierto. Las siete cajas agrupan
los 37 disparadores reales, leídos del `description` de cada `SKILL.md`:

| forma | cuántas | cómo se niega |
|---|---|---|
| el humano la nombra | 9 | si no la nombraste, no entra |
| una línea del repo la declara | 4 | abrís el archivo: está o no está |
| la invoca otra skill | 4 | si la invocante no corrió, no entra |
| el punto del camino | 16 | si el trabajo no llegó ahí, no entra |
| lo que se está tocando | 8 | se mira el diff, no la intención |
| corre sola | 1 | **no se puede negar** |
| sin momento declarado | 1 | **no se puede negar: no está escrito** |

Las 43 flechas cubren las 37 skills; varias cuelgan de más de una condición, y
eso no es un error: `modo-fixes` se enciende por la línea de `REGLAS.md` **o**
porque el humano lo pide, y las dos son verdad.

Los dos últimos renglones de la tabla son hallazgos, no formas. `ley-viva` corre
sola por diseño —y por eso su costo tiene que ser casi cero y su salida silenciosa
cuando no hay nada que decir—. `mapear-despliegue` es otra cosa: su `description`
dice qué hace y nunca cuándo, así que no hay cómo negarla. Es el único caso en 37.

