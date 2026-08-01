# Evento de hook

- **Qué es:** señal normalizada que un adaptador de harness entrega a un
  handler asesor y acotado.
- **Cuándo:** al iniciar o terminar sesión, antes o después de escribir, antes
  de push o después de una falla, si el harness lo soporta.
- **Cómo:** mapear el evento nativo al contrato común, ejecutar el runtime
  autónomo con timeout y devolver únicamente el formato asesor aceptado por el
  harness. Claude Code recibe contexto adicional; Codex recibe
  `systemMessage`.
- **No es:** un daemon, enforcement por defecto ni una capacidad que deba
  fingirse en harnesses sin hooks.
- **Ejemplo:** `BEFORE_PUSH` advierte que falta cierre; el humano todavía decide
  y Claude.ai declara `UNSUPPORTED`.
