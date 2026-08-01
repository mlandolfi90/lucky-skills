# Registry

- **Qué es:** inventario versionado de repositorios adoptantes y datos mínimos
  para inspeccionarlos.
- **Cuándo:** al descubrir destinos de sincronización o actualizar su
  pertenencia a una skill o grupo.
- **Cómo:** guardar un archivo `registry/repos/<repo-id>.env` por repositorio
  y apuntar las herramientas al directorio `repos/` exacto (el escáner lee
  `*.env` de ese directorio, sin recursión: apuntar a la raíz produce un plan
  vacío),
  con remoto, rama, harness, selección de skills y estado.
- **No es:** almacén de credenciales, caché de estado observado ni autorización
  para escribir en los repositorios listados.
- **Ejemplo:** un registro activo declara el remoto, `main`, `codex` y
  `SKILLS="sextante,adopcion"`.
