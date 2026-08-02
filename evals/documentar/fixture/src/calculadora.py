"""Calculadora de ejemplo para el arnés de evaluación de `documentar`."""

DEFAULT_TIMEOUT = 60


def sumar(a, b):
    """Suma dos números y devuelve el resultado."""
    return a + b


def dividir(numerador, denominador):
    """División segura: si el denominador es cero, devuelve None."""
    if denominador == 0:
        return None
    return numerador / denominador


def redondear(valor, decimales=2):
    """Redondea al número de decimales indicado (2 por defecto)."""
    return round(valor, decimales)
