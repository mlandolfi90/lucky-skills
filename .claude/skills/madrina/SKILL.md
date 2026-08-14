---
name: madrina
description: Acompañar el nacimiento de una skill nueva; bautizarla con nombre único y verificar que nazca sana y sin responsabilidad siamesa. Usar antes de escribir cualquier skill del catálogo.
---

# Madrina

Que cada skill nazca sana, con nombre propio y sin hermanas siamesas.

## Invariantes

- Una skill nace con una sola responsabilidad, dicha en una frase. Si la
  frase necesita un "y", son dos skills.
- Bautismo: nombre único en el catálogo, en el estilo de la casa, con
  identificador válido.
- No siamesas: antes de escribir una línea, contrastar la responsabilidad
  contra el catálogo completo. Mismo disparador que una skill viva → no
  nace. Solapamiento parcial (profundizar el carril de otra) → se declara
  con justificación. El mismo chequeo que la publicación exige en su
  puerta, aplicado en la cuna.
- Disparador negable: el "usar cuándo" nombra un momento que se puede
  descartar. Si ante una tarea cualquiera no se puede contestar "no, este no
  es el momento" sin ponerse a discutir, eso no es un disparador: es un
  default encubierto, y la skill va a estorbar en todo el camino. Una
  condición verificable acota ("cuando la estructura no esté corroborada");
  una especulativa no acota nada ("cuando alguien pueda tocar el mismo
  alcance" nunca es falso en un taller con varias sesiones vivas). Único y
  ancho son defectos distintos: el primero lo caza la invariante de arriba,
  el segundo sólo ésta.
- Cuerpo sano: frontmatter mínimo, manifiesto con dependencias reales,
  invariantes, flujo, degradación declarada si consulta servicios, y salida
  en campos comprobables.
- Alcance retroactivo: toda mejora que nace — skill, regla o patrón —
  declara qué ya-construido debería recibirla también. Los huérfanos de
  alcance (artefactos existentes que la mejora alcanza y nadie actualizó)
  quedan listados como seguimiento, no se descubren por accidente.
- La madrina no publica ni adopta: entrega la criatura sana al ciclo, que
  tiene sus propias puertas.

## Flujo

1. Escribir la responsabilidad en una frase comprobable.
2. Contrastar el disparador dos veces: contra el catálogo vivo, buscando
   siamesas; y contra sí mismo, comprobando que el momento se pueda negar.
3. Bautizar: nombre único, estilo de la casa.
4. Dar cuerpo: estructura completa con las dependencias mínimas reales.
5. Verificar salud: la validación de la suite en verde.
6. Entregar al ciclo de publicación.

## Salida

```text
SKILL_ID=...
RESPONSIBILITY=<una frase>
SIAMESE=NONE|DECLARED|BLOCKED
TRIGGER=NEGABLE|BROAD
REQUIRES=...
HEALTH=PASS|FAIL
HANDOFF=PUBLICATION|BLOCKED
```
