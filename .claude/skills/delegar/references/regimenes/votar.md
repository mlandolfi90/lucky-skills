# Régimen: votar

```text
REGIMEN=votar
VERSION=1.0.0
ORIGEN=investigación del 2026-09-01. "Debate or Vote" (arXiv 2508.17536) mide
  que la mayor parte de la ganancia del debate multiagente viene de la
  votación simple; "Can LLM Agents Really Debate?" (arXiv 2511.07784) mide
  que con cómputo igualado un agente solo empata al debate.
```

Para preguntas con una respuesta única y comprobable, cuando un solo intento
puede errar por azar: ¿cuál de estos tres archivos causa el bug? ¿este diff
rompe el contrato? ¿el umbral correcto es 12 o 15?

## Cómo se usa

- Decís: `delegar votar` y la pregunta. La pregunta tiene que admitir una
  respuesta corta que se pueda comparar entre agentes.
- La sesión lanza N agentes con el **mismo** pedido, cada uno sin ver a los
  otros, y compara las respuestas.
- Recibís: la respuesta ganadora, cuántos votos tuvo, y las disidencias con
  su razón. Sin mayoría clara, recibís eso mismo y decidís vos.

## Reglas

- **La misma pregunta, el mismo contexto, N veces.** Los agentes no se ven
  entre sí. Si se ven, es debate, y el debate converge a la mayoría aunque
  esté errada.
- **N impar, entre tres y cinco.** Con tres se empieza; cinco si el tres dio
  empate. Más de cinco no compra nada medible.
- **Se compara la respuesta, no el razonamiento.** Por eso la pregunta tiene
  que admitir respuesta corta. El razonamiento se guarda como disidencia.
- **Sin mayoría no hay ganador.** Si ningún valor supera la mitad, se declara
  `VOTO=SIN_MAYORIA` y la madre decide con las disidencias a la vista.
- **Presupuesto: hasta cinco agentes, esfuerzo normal, cinco minutos cada
  uno.** Sólo lectura: un voto no escribe.

## Por qué así

Votar compra lo que el debate compra —cubrir el error de un intento solo— sin
que los agentes se convenzan entre sí. La evidencia mide que casi toda la
ganancia del debate es la votación que lleva adentro; lo demás es agentes
arrastrándose a la opinión mayoritaria. Votar a ciegas se queda con la parte
que sirve.

## Degradación

Si la pregunta no admite respuesta corta —"¿cómo refactorizo esto?"— votar no
sirve: N ensayos distintos no se comparan. Se declara
`DEGRADACION=pregunta-abierta` y se nombra el régimen que la cubre
(`solo-investigar` o `refutar`).
