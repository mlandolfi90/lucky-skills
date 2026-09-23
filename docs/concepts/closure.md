# Cierre

- **Qué es:** veredicto con evidencia que termina o condiciona una ejecución.
- **Cuándo:** después de implementar, recuperar o descartar un cambio.
- **Cómo:** comprobar TARGET, alcance, pruebas, arquitectura, colisiones,
  rollback y autorizaciones; emitir `FINAL`, `CONDITIONAL` o `BLOCKED`.
  `CONDITIONAL` siempre nombra su condición. Un descarte sin escritura puede
  usar pruebas `NOT_APPLICABLE`; una fase escritora no.
- **No es:** una señal para terminar por tiempo ni una forma de ocultar
  incertidumbre o trabajo obligatorio. Tampoco una verificación: el
  adaptador comprueba coherencia entre valores declarados —rechaza un
  `FINAL` cuyo `TESTS` no sea `PASS`— pero no ejecuta las pruebas. En
  los términos de [nivel de evidencia](evidence-level.md), `TESTS`,
  `ARCHITECTURE` y `COLLISION` son `DECLARED`: comprobó quien los
  tipeó. Por eso un `FINAL` no informa nada sobre `TESTS`, que es
  `PASS` por construcción.
- **Ejemplo:** el resultado funciona pero falta una validación autorizada:
  `CLOSURE=CONDITIONAL` con la condición exacta.
