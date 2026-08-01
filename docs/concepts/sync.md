# Sincronización

- **Qué es:** coordinación de una release con los repositorios registrados que
  pueden adoptarla.
- **Cuándo:** después de publicar o cuando el humano solicita comparar
  versiones.
- **Cómo:** clasificar cada destino, confirmar alcance y ejecutar una adopción
  atómica independiente por repositorio. El plan confirmado incluye el
  prefijo y la rama exacta propuesta para cada destino.
- **No es:** una transacción global, force-push ni permiso continuo sin
  repositorios, acciones, ramas y fin definidos.
- **Ejemplo:** actualizar tres repositorios produce dos `COMPLETE` y un
  `BLOCKED` sin revertir los dos resultados válidos.
