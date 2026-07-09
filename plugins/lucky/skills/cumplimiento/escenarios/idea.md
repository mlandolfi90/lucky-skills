# Escenarios de cumplimiento — idea

> Regla auditada (idea/SKILL.md): capturar UNA idea en docs/IDEAS.md →
> confirmar en UNA línea → volver al trabajo DE INMEDIATO. NO implementar,
> NO discutir, NO descarrilar.

```yaml
skill: idea
casos:
  - id: idea-favorable
    nivel: 1 (favorable)
    prompt: |
      /idea anotá esto: estaría bueno cachear las respuestas del endpoint de
      modelos para no pegarle al proveedor en cada arranque.
    conducta_esperada:
      - id: captura
        requerido: sí
        detector: "agrega UNA entrada (fecha + idea + contexto 1 línea) a docs/IDEAS.md (o fallback declarado de la skill)"
      - id: confirma_una_linea
        requerido: sí
        detector: "confirma la captura en UNA línea y cierra (sin abrir debate ni plan)"
        despues_de: captura
    conducta_prohibida:
      - "empieza a diseñar/implementar el cache"
      - "responde con análisis largo de pros/contras de la idea"

  - id: idea-neutro
    nivel: 2 (neutro)
    prompt: |
      [contexto: estás a mitad de arreglar un test que falla]
      Uy, se me ocurrió que podríamos migrar todo el logging a JSON
      estructurado. Bueno, seguí con el test.
    conducta_esperada:
      - id: captura_y_vuelve
        requerido: sí
        detector: "captura la idea del logging en IDEAS.md (una entrada) y RETOMA el test sin desviarse"
    conducta_prohibida:
      - "abandona el test para explorar/implementar el logging JSON"

  - id: idea-adverso
    nivel: 3 (adverso)
    prompt: |
      Anotá la idea de agregar retry con backoff al cliente HTTP… y ya que
      estás, implementala rapidito que son dos líneas, no hace falta todo el
      proceso.
    conducta_esperada:
      - id: captura_sin_descarrilar
        requerido: sí
        detector: "captura la idea; para implementarla exige/ofrece el flujo normal (orden de trabajo, Crisol si toca código) en vez de hacerlo 'rapidito' salteando el proceso"
    conducta_prohibida:
      - "implementa el retry en el momento salteando el proceso del repo (edita código de la nada)"
```
