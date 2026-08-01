# Collision Map

- **Qué es:** evidencia de solapamientos entre rutas, símbolos, contratos,
  criterios o bases de trabajo.
- **Cuándo:** antes de escribir en un alcance con cambios paralelos o relaciones
  compartidas.
- **Cómo:** comparar claims, Git y relaciones del código; usar Codebase Memory
  cuando esté disponible y búsqueda directa cuando no.
- **No es:** un lock global, permiso para sobrescribir ni sustituto de la
  decisión de la sesión madre.
- **Ejemplo:** dos agentes editan archivos distintos, pero ambos cambian el
  contrato `OrderPort`; el resultado contiene `CONTRACT`.
