# Release

- **Qué es:** versión validada y consumible de una skill del catálogo.
- **Cuándo:** después de un cierre suficiente y antes de ofrecer la versión a
  repositorios adoptantes.
- **Cómo:** validar el paquete con la versión propuesta en cada harness, elegir
  `PATCH`, `MINOR` o `MAJOR`, confirmar el plan y ejecutar solo las acciones
  Git autorizadas. Cada acción conserva su autorizador.
- **Fallo posterior al commit:** conservar el commit, no forzar tag ni push y
  emitir `HUMAN_REQUIRED` para resolución humana.
- **No es:** adopción automática, permiso implícito para push ni un historial
  duplicado fuera de Git.
- **Ejemplo:** corregir un contrato sin romper compatibilidad publica
  `1.0.1` como `PATCH`.
