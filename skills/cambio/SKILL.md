---
name: cambio
description: Registrar una observación, diagnosticarla y clasificar el siguiente escalón. Usar al capturar algo visto o deseado antes de elegir microfix, hotfix, feature, quality, refactor o migration.
---

# Cambio

Convertir una observación en una transición explícita sin confundirla con una
solución.

## Taxonomía

- `OBSERVATION`: hecho visto, comportamiento esperado o necesidad esbozada.
- `DIAGNOSIS`: causa o brecha corroborada.
- `MICROFIX`: prueba o corrección mínima y reversible.
- `HOTFIX`: corrección urgente sobre un TARGET operativo.
- `FEATURE`: comportamiento nuevo.
- `QUALITY`: el comportamiento es correcto y se mejora su calidad.
- `REFACTOR`: cambia estructura sin cambiar comportamiento esperado.
- `MIGRATION`: transición entre estados o contratos.

No usar `IDEA` como estado del flujo.

## Escalera

Empezar por el escalón mínimo seguro y promoverlo cuando crezcan alcance,
riesgo, colisiones o deuda:

```text
OBSERVATION → DIAGNOSIS → CHANGE_KIND → QUALITY/CRISOL → CLOSURE
```

No ejecutar pasos vacíos. No rebajar la clasificación para evitar gates. Los
microfixes acumulados sobre una responsabilidad compartida se promueven.

## Flujo

1. Capturar alcance `GLOBAL` o `LOCAL`, autor, evidencia y contexto.
2. Distinguir hecho, expectativa e hipótesis.
3. Diagnosticar antes de escoger una corrección.
4. Elegir un solo `NEXT_STEP` y explicar por qué los demás no aplican.
5. Confirmar TARGET antes de cualquier fase escritora.
6. Registrar autor y comprobante de cada transición.

## Salida

```text
CHANGE_ID=...
CURRENT_KIND=...
SCOPE=GLOBAL|LOCAL
OBSERVED=...
EXPECTED=...
DIAGNOSIS=...
NEXT_STEP=...
TARGET=CONFIRMED|UNCONFIRMED
AUTHOR=...
RECEIPT=...
```

Una idea parqueada del proyecto es una observación: se registra acá, en el
lifecycle, nunca en archivos sueltos (`IDEAS.md` y similares son el patrón
viejo y driftean). La frontera con el saber es trabajo vs conocimiento: lo
que hay que CONSTRUIR va acá y tiene ciclo; lo que se APRENDIÓ
(síntoma→acción) va al saber en su scope — global si sirve a todos,
`repo:<nombre>` si es propio de este repo.

Una observación puede investigarse, descartarse o promoverse. No implementar el
cambio desde esta skill.
