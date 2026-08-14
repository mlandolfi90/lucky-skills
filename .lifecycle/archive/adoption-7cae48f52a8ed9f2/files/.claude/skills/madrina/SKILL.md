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
2. Buscar siamesas en el catálogo: disparadores y responsabilidades de
   todas las skills vivas.
3. Bautizar: nombre único, estilo de la casa.
4. Dar cuerpo: estructura completa con las dependencias mínimas reales.
5. Verificar salud: la validación de la suite en verde.
6. Entregar al ciclo de publicación.

## Salida

```text
SKILL_ID=...
RESPONSIBILITY=<una frase>
SIAMESE=NONE|DECLARED|BLOCKED
REQUIRES=...
HEALTH=PASS|FAIL
HANDOFF=PUBLICATION|BLOCKED
```
