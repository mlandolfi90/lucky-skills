# Adopción

- **Qué es:** transacción coordinada que instala o actualiza una skill y sus
  dependencias en un repositorio confirmado.
- **Cuándo:** cuando un repositorio incorpora una skill o cambia su versión o
  harness.
- **Cómo:** validar, mostrar un plan exacto, confirmar su hash, archivar lo
  reemplazado, activar, comprobar y restaurar ante fallo.
- **No es:** una mezcla semántica, una refactorización del producto ni permiso
  implícito para commit, push o deploy.
- **Ejemplo:** adoptar `microfix@1.0.0` junto con `cambio`,
  `mapa-colisiones` y `sextante` en Codex después de confirmar el TARGET y el
  `PLAN_HASH`.
