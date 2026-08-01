# Estado de capacidad

- **Qué es:** disponibilidad efectiva de una herramienta o skill en la sesión.
- **Cuándo:** al inventariar lo que el harness expone actualmente.
- **Cómo:** usar `DETECTED`, `LOADED`, `INVOKABLE`, `UNAVAILABLE` o `UNKNOWN`.
  Solo `VERIFIED_DIRECT` o `HUMAN_PROVIDED` puede sostener
  `CAPABILITIES=ALIGNED`; evidencia `DECLARED` o `UNKNOWN` queda parcial.
- **No es:** catálogo de cosas instalables ni prueba basada en archivos del disco.
- **Ejemplo:** una tool callable es `INVOKABLE`; una carpeta encontrada no basta.
