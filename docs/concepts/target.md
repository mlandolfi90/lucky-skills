# Target

- **Qué es:** confirmación mínima de `WHERE`, `ACTION` y `CONFIRMED_BY`.
- **Cuándo:** antes de una acción de escritura.
- **Cómo:** confirmarlo explícitamente con un actor `human:`, exigir que ACTION
  coincida con la operación y que WHERE coincida con la identidad observada
  (`local:workspace`, remote/ref o `RUNTIME_TARGET`); mantenerlo separado de la
  inspección.
- **No es:** una fuente consultada ni autorización implícita. `CONFIRMED_BY`
  es atribución, no autenticación —`DECLARED` en los términos de [nivel de
  evidencia](evidence-level.md)—: el prefijo `human:` se comprueba como
  texto y nada en el ciclo prueba que una persona lo haya tipeado. Lo que
  sí ata es el hash del plan confirmado, donde exista: liga la
  confirmación a ese plan y no a otro.
- **Ejemplo:** consultar `dev` no autoriza desplegar en `dev`.
