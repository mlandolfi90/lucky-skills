# State Map

- **Qué es:** snapshot versionable del último estado corroborado del proyecto.
- **Cuándo:** una skill lo consulta antes de depender de sus valores.
- **Cómo:** corroborarlo contra fuentes reales y registrar contradicciones.
  El archivo usa UTF-8/LF canónico `CLAVE=<cadena JSON>`; cualquier variante
  no canónica es inválida antes de comparar.
  `GIT_LOCAL_COMMIT` guarda la identidad Git; `GIT_LOCAL_FINGERPRINT` guarda la
  identidad de contenido/modos y excluye de su propio material únicamente el
  valor canónico de ese mismo campo. `GIT_REMOTE_COMMIT` siempre se interpreta
  junto a `GIT_REMOTE_REF`. Cuando la huella local es conocida, es el criterio
  de alineación y el commit queda como base informativa anterior al commit del
  propio State Map; el commit solo actúa como fallback si la huella es
  `UNKNOWN`.
- **No es:** verdad automática, comprobante temporal ni sustituto de Git.
- **Ejemplo:** `GIT_LOCAL_COMMIT` distinto al observado produce drift.
