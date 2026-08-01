# Veredicto de arquitectura

- **Qué es:** dictamen acotado sobre un plan o diff frente a fronteras reales,
  SOLID, atomicidad y factorización.
- **Cuándo:** antes del cierre de cambios que alteren estructura, contratos o
  varias unidades.
- **Cómo:** emitir `PASS`, `BLOCK` o `UNKNOWN` con evidencia, deuda previa y
  acción requerida.
- **No es:** una corrección automática, una revisión ilimitada del repositorio
  ni un `PASS` inferido por falta de evidencia.
- **Ejemplo:** una dependencia del dominio hacia un framework nuevo produce
  `BLOCK`; una frontera no observable produce `UNKNOWN`.
