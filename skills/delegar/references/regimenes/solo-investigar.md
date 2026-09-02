# Régimen: solo-investigar

```text
REGIMEN=solo-investigar
VERSION=1.0.0
ORIGEN=regla del operador del 2026-09-01, sesión del Taller: "sin refutadores,
  solo la investigación necesaria para el agente padre, quien decide qué hará
  y cómo spawnear"
```

Para cuando la sesión madre necesita ojos, no opiniones: los agentes traen
evidencia y la madre hace todo lo demás.

## Cómo se usa

- Decís: `delegar solo-investigar` y qué querés saber.
- La sesión escribe el esquema de lo que busca, lanza hasta cuatro agentes de
  lectura con alcance cerrado, y sintetiza ella.
- Recibís: la evidencia en ese esquema, lo que cada agente no pudo, y la
  decisión de la madre a partir de eso.

## Reglas

- **Sólo agentes de lectura.** Un agente bajo este régimen no escribe, no
  edita, no publica, no manda mensajes. Devuelve lo que vio.
- **Sin críticos, sin jueces, sin síntesis delegada.** Nadie refuta a nadie;
  nadie decide entre resultados. Eso lo hace la madre, con el humano.
- **Esquema de retorno declarado antes de lanzar.** El agente devuelve campos
  comprobables, no prosa. Si la madre no puede escribir el esquema, todavía
  no sabe qué está buscando y no lanza.
- **Alcance cerrado por agente.** Archivos, carpetas o preguntas concretas.
  "Mirá el repo" no es un alcance.
- **Presupuesto: hasta cuatro agentes por lanzamiento, esfuerzo normal, diez
  minutos por agente.** El que se pasa se corta y se declara `FALTO=<qué>`.
  Si hace falta más, es otro lanzamiento y la madre lo decide con lo que ya
  volvió.
- **La evidencia ya medida viaja en el prompt.** El agente no vuelve a contar
  lo que la madre ya contó.

## Por qué así

Un crítico cuesta lo mismo que un investigador y produce una opinión que la
madre igual tiene que juzgar. Bajo este régimen el juicio se hace una sola
vez, donde el humano lo ve. Se pierde la refutación cruzada; se gana tiempo,
tokens y una sola voz para discutir.

## Degradación

Cuando un resultado necesita ser refutado antes de actuar —algo que va a
entrar al catálogo, o a producción—, este régimen no alcanza. Se declara
`DEGRADACION=necesita-refutacion`, se le dice al humano qué régimen lo cubre
(`refutar`), y se espera. No se lanza un crítico "por esta vez".
