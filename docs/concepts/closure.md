# Cierre

- **Qué es:** veredicto con evidencia que termina o condiciona una ejecución.
- **Cuándo:** después de implementar, recuperar o descartar un cambio.
- **Cómo:** comprobar TARGET, alcance, pruebas, arquitectura, colisiones,
  rollback y autorizaciones; emitir `FINAL`, `CONDITIONAL` o `BLOCKED`.
  `CONDITIONAL` siempre nombra su condición. Un descarte sin escritura puede
  usar pruebas `NOT_APPLICABLE`; una fase escritora no.
- **No es:** una señal para terminar por tiempo ni una forma de ocultar
  incertidumbre o trabajo obligatorio.
- **Ejemplo:** el resultado funciona pero falta una validación autorizada:
  `CLOSURE=CONDITIONAL` con la condición exacta.
