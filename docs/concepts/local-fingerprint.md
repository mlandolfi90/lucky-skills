# Huella local

- **Qué es:** hash de contenido acotado, modos y estructura observable
  index/tree/branch del workspace; el commit se registra aparte.
- **Cuándo:** al inicio y al final de Sextante y como ancla de contexto.
- **Cómo:** usar `INDEX_CONTENT_BOUNDED` con Git o `TREE_CONTENT_BOUNDED` sin
  Git; comparar dirty de forma conservadora sobre bytes crudos, sin ejecutar
  filtros Git; incluir el modo ejecutable cuando el sistema POSIX lo expone;
  nunca guardar el contenido ni una salida bruta. V3 encuadra cada registro
  como array JSON ASCII compacto, los une con LF sin LF final y calcula
  SHA-256. El mtime sirve para detectar carreras, pero no forma parte de la
  identidad. La identidad del commit vive por separado en `GIT_LOCAL_COMMIT`.
- **Regla anti-autorreferencia:** para
  `.lifecycle/state/STATE-MAP.env`, normalizar únicamente el valor de la línea
  canónica `GIT_LOCAL_FINGERPRINT="..."` tanto en el workspace como en los
  blobs Git. El resto de los bytes y el modo siguen participando. La marca de
  tiempo de este archivo no participa porque no permite distinguir una
  actualización del campo excluido; `LOCAL_DIRTY` conserva, sin normalizar, la
  verdad de Git.
- **Commit del mapa:** como el archivo no puede contener el hash del commit que
  todavía no existe, una huella conocida prevalece para alineación y
  `GIT_LOCAL_COMMIT` queda como base/fallback.
- **No es:** una prueba exhaustiva cuando se alcanza el límite de entradas,
  bytes o tiempo; en ese caso `LOCAL=PARTIAL`.
- **Ejemplo:** cambiar bytes de un archivo, aunque conserve tamaño y mtime,
  cambia la huella; cambiar solo el valor autorreferencial del State Map no.
