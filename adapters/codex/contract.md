# Adaptador Codex de Sextante

- **Qué hace:** traduce capacidades de la sesión Codex al contrato portable.
- **Cuándo:** al invocar Sextante dentro de Codex.
- **Cómo:** la sesión madre enumera únicamente skills/tools expuestas, usa
  consultas especializadas de solo lectura para runtime y pasa observaciones al
  adaptador Python.
- **No hace:** recorrer el disco buscando skills, delegar la síntesis, instalar
  tools o mutar el proyecto.
- **Ejemplo:** pasar
  `--capability "skill|skill-creator|LOADED|UNKNOWN"` al ejecutable de referencia.

Si una observación no puede verificarse, pasar `UNKNOWN` o dejarla ausente. No
convertir disponibilidad del catálogo en capacidad de la sesión.
Declarar `--capabilities-evidence VERIFIED_DIRECT` solo para capacidades
realmente expuestas por la sesión; catálogo o archivos del disco son
`DECLARED` y no habilitan escritura.
