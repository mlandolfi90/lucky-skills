"""Módulo de precios."""

from config import PRECIO_MINIMO


def aplicar_descuento(precio):
    """Aplica el descuento estándar del 10%."""
    return max(PRECIO_MINIMO, precio * 0.90)
