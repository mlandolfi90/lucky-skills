# Manifest de skill

- **Qué es:** contrato portable y versionado que identifica una skill y sus
  dependencias con compatibilidad SemVer.
- **Cuándo:** al validar, adoptar, publicar, empaquetar o sincronizar una skill.
- **Cómo:** mantener `manifest.env` con formato, identificador, SemVer y
  requisitos; corroborarlo contra la carpeta y `SKILL.md`.
- **No es:** metadata exclusiva de un harness ni un lugar para credenciales o
  estado mutable del repositorio adoptante.
- **Ejemplo:** `REQUIRES="cambio@1.0.0,mapa-colisiones@1.0.0"` se satisface
  con esas versiones o con cualquier `PATCH`/`MINOR` posterior del mismo
  `MAJOR` (`cambio@1.2.0` cumple; `cambio@2.0.0` o una versión anterior, no).
