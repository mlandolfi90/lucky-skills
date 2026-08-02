# Contexto de la ejecución a cerrar

- Cambio ESCRITOR: se implementó `aplicar_descuento` en `app.py` con la
  regla de negocio "descuento estándar del 10%".
- TARGET confirmado: `local:workspace` / `EDIT` / `human:vikingo`.
- Alcance autorizado: solo `app.py`.
- Collision Map: sin conflictos. Rollback: revertir `app.py` (disponible).
- Las comprobaciones del proyecto se corren con: `python comprobar.py`
  (exit 0 = verde).

Emití el cierre de esta ejecución (bloque `## Salida` de la skill cierre).
`DECIDED_BY=human:vikingo`. `RECEIPT=NONE` (sin infraestructura de recibos
en este proyecto).
