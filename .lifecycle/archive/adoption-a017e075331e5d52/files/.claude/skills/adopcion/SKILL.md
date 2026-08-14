---
name: adopcion
description: Preparar o aplicar una skill en un repositorio. Usar al adoptar, migrar o cambiar de versión; exige Sextante, TARGET humano, plan exacto, archivo, validación y rollback.
---

# Adopción

Aplicar una transición de skills sin dejar estados mezclados.

## Invariantes

- Ejecutar la síntesis y la decisión desde la sesión madre.
- Consumir un comprobante vigente de Sextante con `WRITE_GATE=PASS` y
  `TARGET=CONFIRMED`.
- Adoptar una skill por transacción junto con sus dependencias obligatorias.
- Mantener `skills/` como fuente funcional y `.lifecycle/` como estado
  operativo.
- No modificar código de producto, datos o infraestructura. Declarar
  `EXTERNAL_CHANGE_REQUIRED` si la transición lo exige.
- No mezclar contenido semánticamente. Comparar rutas y huellas.
- No crear commit salvo autorización humana explícita.

## Preparar

1. Validar `SKILL.md`, `manifest.env`, dependencias y harness seleccionado.
2. Inventariar únicamente las rutas que serán creadas o reemplazadas.
3. Clasificar cada destino:
   - `CREATE`: no existe.
   - `UNCHANGED`: tiene la misma huella.
   - `ARCHIVE_REPLACE`: difiere.
   - `BLOCK`: no puede comprobarse con seguridad.
4. Detectar cambios paralelos y contenido sensible antes de autorizar.
5. Emitir:

```text
SOURCE=...
SKILL=...@...
TARGET=...
HARNESS=...
ACTION=...
COLLISIONS=...
REMOVES=...
COMMIT=YES|NO
PLAN_HASH=...
WRITE_GATE=BLOCK
NEEDS=CONFIRM_ADOPTION
```

El pedido de confirmación es corto por contrato: un renglón por hecho
decisivo, en lenguaje llano, sin prosa. El detalle completo vive en el plan;
la compuerta pide, no explica. Si algo va a borrarse, cada baja se lista en
una línea `REMOVE=` — lo que la compuerta no muestra, no queda autorizado.

## Aplicar

Aceptar confirmación natural solo para el `TARGET` y `PLAN_HASH` mostrados.
Después:

1. Adquirir el lock local de Adopción.
2. Volver a calcular el plan; detenerse si cambió.
3. Preparar la copia fuera de las rutas activas.
4. Archivar bajo `.lifecycle/archive/<ADOPTION_ID>/`, conservando rutas.
5. Validar la copia preparada.
6. Activar la fuente canónica y la proyección del único harness elegido.
7. Escribir `.lifecycle/state/skills/<skill-id>.env`.
8. Validar estructura, huellas, descubrimiento y rutas modificadas.
9. Dejar comprobante; crear commit solo si su alcance fue autorizado.

Tratar una instalación idéntica como `ALREADY_ADOPTED` sin reescribir.

## Revalidar

Un repo vivo avanza después de adoptar: el drift que Sextante detecta es
honesto, pero dejaba en deadlock toda ampliación del paquete. `revalidar`
es la vía legítima: re-corrobora el STATE-MAP con el estado actual, por
decisión humana, registrando el salto (commit y huella, antes y después)
en un recibo. No esconde drift — lo declara. El STATE-MAP jamás se edita
a mano.

## Recuperar

Corregir en el área preparada mientras exista una hipótesis nueva y progreso
verificable. Si se repite el mismo fallo, restaurar el estado anterior, liberar
el lock, emitir autopsia pendiente y consultar al humano.

## Adaptadores

Preferir el adaptador determinista expuesto por el harness. En este repositorio,
el adaptador de referencia se ejecuta con `run_adopcion.py`. Si no está
disponible, reproducir el mismo contrato con herramientas nativas y declarar el
nivel degradado.

