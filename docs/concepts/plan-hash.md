# Plan hash

- **Qué es:** SHA-256 del contenido canónico de un plan exacto.
- **Cuándo:** antes de autorizar una operación que escribirá, publicará o
  sincronizará.
- **Cómo:** ordenar y normalizar todas las acciones, calcular la huella,
  mostrarla y volver a calcularla inmediatamente antes de aplicar.
- **No es:** una firma de identidad, una autorización reutilizable ni permiso
  para acciones ausentes del plan.
- **Ejemplo:** si cambia una sola ruta entre propuesta y ejecución, cambia el
  `PLAN_HASH` y se solicita una confirmación nueva.
