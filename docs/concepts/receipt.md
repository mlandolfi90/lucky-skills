# Comprobante

- **Qué es:** snapshot detallado, inmutable y verificable de una ejecución.
- **Cuándo:** en cada invocación de Sextante.
- **Cómo:** guardar `CLAVE=VALOR` localmente con creación atómica sin
  sobrescritura, huella del adaptador y límite temporal explícito; sin commit
  automático.
- **No es:** `STATE-MAP`, historial Git, firma del autor ni garantía de
  vigencia; SHA-256 detecta alteración, no autentica origen.
- **Ejemplo:** `.lifecycle/local/sextante/sextante-...env` solo si `local/` es
  la última regla activa del ignore; de lo contrario, almacenamiento externo
  del harness que además se comprueba fuera del workspace.
