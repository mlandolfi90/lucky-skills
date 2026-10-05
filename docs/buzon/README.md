# Buzón de sugerencias de lucky-skills

Sugerencias que dejan los proyectos que aplican una skill del catálogo. Cada una es algo que la
receta no cubre, algo que resultó falso o distinto en ese caso, o algo que podría mejorar. Se
dejan acá cuando no hay una sesión custodia abierta que las reciba por mensaje (R12 de
`auditar-mcp`). Lo pidió la operadora el 2026-10-04: «dejarle las mejoras a lucky skill en un
buzon de sugerencias para levantar la sesion luego».

**Cómo se procesa.** La sesión que custodia el catálogo lee cada archivo y decide sugerencia por
sugerencia: aceptada (con el commit que la aplica), rechazada (con el motivo) o «falta
evidencia» (qué medir). Anota la decisión debajo de cada una y mueve el archivo a `procesadas/`
cuando no le queda ninguna abierta. Una sugerencia que salió de un solo caso es una hipótesis
(Casos=1), no una ley.

**Formato.** Un archivo por envío: `AAAA-MM-DD-<skill>-desde-<proyecto>.md`. Arriba van quién
lo deja, sobre qué versión de la skill y desde qué commit del proyecto. Cada sugerencia lleva:
qué dice la receta (archivo:línea), qué pasó en ese caso, con su evidencia, y qué se propone.

**Lo que no entra.** Valores de credenciales, rutas a secretos con su contenido, o material
crudo de una auditoría. Se nombran; nunca se copian.
