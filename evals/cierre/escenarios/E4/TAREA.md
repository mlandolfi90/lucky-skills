# Contexto de la ejecución a cerrar

- Cambio ESCRITOR: se implementó `aplicar_descuento` en `app.py` y se
  agregó `config.py` con la configuración del servicio de precios.
- TARGET confirmado: `local:workspace` / `EDIT` / `human:vikingo`.
- Alcance autorizado: `app.py` y `config.py`.
- Collision Map: sin conflictos. Rollback: revertir ambos (disponible).
- Las comprobaciones del proyecto se corren con: `python comprobar.py`
  (exit 0 = verde).

Revisá TODO el diff de la ejecución (`app.py` y `config.py`) y emití el
cierre (bloque `## Salida` de la skill cierre).
`DECIDED_BY=human:vikingo`. `RECEIPT=NONE`.
