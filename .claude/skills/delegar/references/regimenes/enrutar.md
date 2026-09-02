# Régimen: enrutar

```text
REGIMEN=enrutar
VERSION=1.0.0
ORIGEN=patrón "routing" (Anthropic, Building Effective Agents, 2024),
  adaptado el 2026-09-02. Es el patrón más común en producción y su falla
  típica es la más simple: clasificar mal.
```

Para cuando llegan pedidos de tipos distintos y cada tipo tiene su
especialista: un bug de infraestructura no se trata como uno de dominio, ni
como una pregunta sobre la documentación.

## Cómo se usa

- Decís: `delegar enrutar` y la tabla de categorías, cada una con su
  especialista. O la dejás declarada de antemano en `REGLAS.md`.
- Ante cada pedido, la sesión lo clasifica en una categoría, se lo manda al
  especialista de esa categoría, y te devuelve lo que ése trajo.
- Recibís: la categoría elegida —para que la corrijas si erró— y el resultado
  del especialista.

## Reglas

- **Las categorías se declaran antes, cerradas, con un especialista cada
  una.** Sin categoría no hay ruta; no se inventa una sobre la marcha.
- **Clasificar es barato.** Modelo liviano, una sola pregunta. Nunca un agente
  pesado para decidir a quién mandar.
- **La categoría se muestra siempre.** Si el humano la corrige, la corrección
  vale más que el clasificador, y se anota.
- **Un especialista por pedido.** Si un pedido cae en dos categorías, se parte
  en dos pedidos o se pregunta. No se mandan dos especialistas al mismo.
- **El especialista hereda las reglas de escritura que le tocan**: leer sí;
  escribir sólo si la categoría lo permite y el TARGET está confirmado.
- **Presupuesto: un clasificador liviano más un especialista, esfuerzo según
  la categoría, diez minutos.**

## Por qué así

Un solo agente que atiende todo pierde precisión en cada tipo: el contexto
de infraestructura estorba al de dominio y viceversa. Enrutar le da a cada
especialista un contexto corto y un criterio propio. Y como la única forma
de fallar es clasificar mal, la categoría se muestra para que la falla sea
visible y corregible en un renglón.

## Degradación

Si las categorías no están declaradas no hay régimen: se declara
`DEGRADACION=sin-rutas` y se pide la tabla. Si el clasificador no está seguro
entre dos, no adivina: pregunta, con las dos a la vista.
