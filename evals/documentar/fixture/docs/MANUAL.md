# Manual de la calculadora

## Funciones

- `sumar(a, b)` recibe dos números y devuelve su suma.
- `sumar` valida que ambos argumentos sean enteros y rechaza floats con `TypeError`.
- `dividir` lanza `ZeroDivisionError` cuando el denominador es cero.
- `redondear` usa 2 decimales por defecto.

## Configuración

- El timeout por defecto es de 30 segundos (`DEFAULT_TIMEOUT = 30`).

## Rendimiento

- En producción, el servicio procesa 1000 solicitudes por segundo.
