# Buzón de lucky-skills

Sigue la convención de [buzón](../concepts/buzon.md): `inbox/` es lo que
llega, `outbox/` lo que manda la sesión custodia del catálogo.

Llegan sobre todo sugerencias de los proyectos que aplican una skill: algo
que la receta no cubre, algo que resultó falso o distinto en ese caso, o
algo que podría mejorar. Lo pidió la operadora el 2026-10-04: «dejarle las
mejoras a lucky skill en un buzon de sugerencias para levantar la sesion
luego».

**Cómo se procesa una sugerencia.** La custodia lee el mensaje, anota
`LEIDO` en la bitácora y decide sugerencia por sugerencia: aceptada (con el
commit que la aplica), rechazada (con el motivo) o «falta evidencia» (qué
medir). La decisión va debajo de cada sugerencia, y en la bitácora una línea
`RESUELTO` o `DESCARTADO` que la nombra. Una sugerencia que salió de un solo
caso es una hipótesis (Casos=1), no una ley.

**Qué lleva una sugerencia.** Qué dice la receta (archivo:línea), qué pasó
en ese caso con su evidencia, y qué se propone. La versión de la skill va en
`REFS` (su tag).

**Lo que no entra.** Valores de credenciales, rutas a secretos con su
contenido, o material crudo de una auditoría. Se nombran; nunca se copian.

Los tres mensajes anteriores a la convención (2026-10-04 y 2026-10-05) se
pasaron a `inbox/` con el encabezado armado a partir de lo que ya decían; lo
que no traían figura como `DESCONOCIDO`, y su cuerpo quedó como llegó.
