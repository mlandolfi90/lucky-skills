# Régimen: corregir-en-loop

```text
REGIMEN=corregir-en-loop
VERSION=1.0.0
ORIGEN=patrón "evaluator-optimizer" (Anthropic, Building Effective Agents,
  2024), adaptado el 2026-09-02 con el criterio de la casa: el evaluador es
  un comando, no una opinión.
```

Para cuando hay un criterio de éxito que se puede **correr** —tests, un
linter, una suite de validación, un esquema— y el primer intento casi nunca
lo pasa entero.

## Cómo se usa

- Decís: `delegar corregir-en-loop`, qué hay que producir, y **qué comando
  dice si está bien**.
- La sesión lanza un agente que hace, corre el comando, y si falla le devuelve
  la falla al mismo agente para que corrija. Hasta un tope de vueltas.
- Recibís: el resultado que pasó y cuántas vueltas costó, con qué falló en
  cada una. O el mejor intento, con lo que sigue fallando declarado.

## Reglas

- **El evaluador es un comando, no un agente.** `pytest`, el linter, la suite
  de validación. Un agente evaluando a otro es `refutar`, no esto.
- **Tope de vueltas: tres.** La cuarta no se da; se entrega el mejor intento
  con su falla. Un agente que insiste con la misma hipótesis no converge.
- **Cada vuelta recibe sólo la falla nueva**, no todo el historial. El
  contexto no crece sin control.
- **Un solo agente escritor por lanzamiento.** Escribe en área preparada; la
  madre decide si entra al repo.
- **La madre no corrige a mano entre vueltas.** Si lo hace, el loop terminó y
  lo que sigue es trabajo de la madre.
- **Presupuesto: un agente, esfuerzo normal, quince minutos en total.**

## Por qué así

Un loop con evaluador mecánico converge: el criterio no se mueve. Uno con
evaluador humano o agente diverge, porque cada vuelta cambia lo que se pide.
Y el tope de tres evita la falla medida en todos lados: el agente que repite
la misma corrección esperando otro resultado.

## Degradación

Sin comando que evalúe no hay régimen: se declara
`DEGRADACION=sin-criterio-ejecutable` y se pregunta qué comando lo mediría.
Si el agente repite la misma falla dos vueltas seguidas, se corta antes del
tope: no hay hipótesis nueva, y sin hipótesis nueva no hay vuelta que valga.
