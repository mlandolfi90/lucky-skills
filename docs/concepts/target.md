# Target

- **Qué es:** confirmación mínima de `WHERE`, `ACTION` y `CONFIRMED_BY`.
- **Cuándo:** antes de una acción de escritura.
- **Cómo:** confirmarlo explícitamente con un actor `human:`, exigir que ACTION
  coincida con la operación y que WHERE coincida con la identidad observada
  (`local:workspace`, remote/ref o `RUNTIME_TARGET`); mantenerlo separado de la
  inspección.
- **No es:** una fuente consultada ni autorización implícita.
- **Ejemplo:** consultar `dev` no autoriza desplegar en `dev`.
