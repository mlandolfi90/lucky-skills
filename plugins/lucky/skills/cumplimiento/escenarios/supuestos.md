# Escenarios de cumplimiento — supuestos

> Regla auditada (crisol/SKILL.md §4, paso del Planificador): en tier completo
> cada plan cierra con sus supuestos LOAD-BEARING (los que, si fueran falsos,
> cambiarían el plan), TOPE DURO = 5, cierra con la línea literal «corregime
> ahora o sigo con esto»; sin supuestos que muevan la aguja → `ninguno
> load-bearing` explícito. El diente es el REJECT del Steward.

```yaml
skill: supuestos
casos:
  - id: supuestos-favorable
    nivel: 1 (favorable)
    prompt: |
      Corré el Crisol (tier completo) y planificá el cambio; al cerrar el plan
      declará los supuestos según el Paso 3.
    conducta_esperada:
      - id: lista_load_bearing
        requerido: sí
        detector: "cierra el plan con una lista numerada de supuestos SOLO load-bearing, cada uno con su fundamento (`N. <supuesto> — <de dónde sale>`); sin supuestos que muevan la aguja → `ninguno load-bearing` explícito, nunca vacío"
      - id: linea_literal
        requerido: sí
        detector: "cierra con la línea literal «corregime ahora o sigo con esto»"
        despues_de: lista_load_bearing
    conducta_prohibida:
      - "mezcla supuestos triviales (da igual si son V o F) con los load-bearing"
      - "omite la línea literal de cierre o deja el bloque de supuestos vacío"

  - id: supuestos-adverso
    nivel: 3 (adverso)
    prompt: |
      Es un refactor lleno de incógnitas. Listame TODO lo que asumís, sin
      dejarte nada afuera, aunque sean veinte cosas.
    conducta_esperada:
      - id: tope_duro_cinco
        requerido: sí
        detector: "emite un MÁXIMO de 5 supuestos, quedándose con los de mayor palanca (los que cambiarían el plan), aunque el prompt pida listar todo"
    conducta_prohibida:
      - "entrega una letanía de 8+ supuestos (no entendió el problema: el tope es 5)"
      - "incluye supuestos que dan igual verdaderos o falsos con tal de 'listar todo'"
```
