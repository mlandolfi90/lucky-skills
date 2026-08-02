"""Comprobaciones del proyecto. Exit 0 = verde."""

from app import calcular_total

assert round(calcular_total(100), 2) == 121.0, "el IVA es 21%"
print("OK")
