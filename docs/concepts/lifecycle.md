# Lifecycle

- **Qué es:** árbol normalizado de estado, configuración y registros del proyecto.
- **Cuándo:** después de que una futura skill de adopción lo cree explícitamente.
- **Cómo:** usar `.lifecycle/` y dejar como última regla activa `local/` en
  `.lifecycle/.gitignore`; Sextante no crea ni corrige esa regla.
- **No es:** requisito para que Sextante pueda aterrizar.
- **Ejemplo:** sin adopción, el comprobante se guarda fuera del repositorio.
