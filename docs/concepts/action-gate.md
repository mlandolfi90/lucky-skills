# Gate de acción

- **Qué es:** resultado operativo `PASS`, `WARN` o `BLOCK`.
- **Cuándo:** antes de lectura, escritura o acción externa.
- **Cómo:** evaluarlo según la fuente relevante y vigencia del comprobante.
- **No es:** descripción del estado ni sustituto de autorización humana.
- **Ejemplo:** un comprobante stale produce `READ_GATE=WARN` y
  `WRITE_GATE=BLOCK`.
