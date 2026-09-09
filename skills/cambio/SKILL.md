---
name: cambio
description: Registrar una observación, diagnosticarla y clasificar el siguiente escalón. Usar antes de tocar el repositorio por un fallo o una mejora, mientras no haya escalón elegido para ese trabajo.
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

Con `CURRENT_KIND=FEATURE` y alcance sin definir, el escalón siguiente es
`disenar` antes de construir. `CHANGE_ID` viaja a `microfix`, `hotfix` y al
`cierre`: el recibo final se ata a esta observación por ese id.

No ejecutar pasos vacíos. No rebajar la clasificación para evitar gates:
rebajar es apagarlos en silencio. Diferir un portón declarado
(`PORTON=bajo-autorizacion` en `REGLAS.md`, skill `modo-fixes`) no es
rebajar: la clasificación se mantiene y el portón queda `PENDIENTE` a la
vista. Los microfixes acumulados sobre una responsabilidad compartida se
promueven.

## Flujo

1. Capturar alcance `GLOBAL` o `LOCAL`, autor, evidencia y contexto.
2. Distinguir hecho, expectativa e hipótesis.
3. Consultar `precedente` (puerta `DIAGNOSTICO`) y diagnosticar antes de
   escoger una corrección.
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
TARGET=CONFIRMED|UNCONFIRMED   (la confirmación; el destino real lo declara microfix/hotfix en su TARGET=)
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
