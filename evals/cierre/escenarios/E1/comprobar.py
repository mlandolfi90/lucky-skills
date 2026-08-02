"""Comprobaciones del proyecto. Exit 0 = verde."""

from app import aplicar_descuento

assert aplicar_descuento(100) == 90, "el descuento estándar es 10%"
print("OK")
