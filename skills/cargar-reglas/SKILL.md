---
name: cargar-reglas
description: Cargar al inicio de sesión las reglas de operación del proyecto y sostenerlas toda la sesión. Usar como primer acto en cualquier proyecto que declare un REGLAS.md.
---

# Cargar reglas

Cada proyecto declara cómo se trabaja en él; la sesión lo lee primero y lo
cumple siempre.

## Invariantes

- Las reglas viven en `REGLAS.md` en la raíz del proyecto: un solo lugar,
  versionado, editable por el humano.
- Se cargan al inicio, antes de cualquier trabajo. Donde el harness soporte
  hooks de inicio de sesión, el hook las recuerda; donde no, esta skill se
  invoca primero.
- Las reglas cargadas son invariantes de la sesión, no sugerencias: estilo y
  largo de respuesta, formas prohibidas, límites de acción. Violarlas se
  corrige en el acto, sin disculpas largas.
- Una instrucción viva del humano vale más que el archivo; si lo contradice
  de forma estable, se propone actualizar el archivo para que la regla no se
  pierda.
- Sin `REGLAS.md`, declararlo y seguir con los defaults — nunca inventar
  reglas que el proyecto no escribió.

## Orden de arranque

1. Leer `REGLAS.md` y aplicar sus reglas (esta skill).
2. Invocar `ley-viva`: comprueba que las skills adoptadas sigan vigentes
   contra el catálogo y avisa antes de trabajar.
3. Invocar `sextante` una vez, para dejar el comprobante fresco antes de
   que cualquier gate lo exija: casi todas las skills lo requieren y ninguna
   otra dice cuándo corre por primera vez.
4. `entonar` y `delegar` leen sus defaults (`FORMA=`, `SPAWN=`) de
   `REGLAS.md`; `modo-fixes` lee `PORTON=`.

## Formato de REGLAS.md

```markdown
# Reglas de <proyecto>
- Respuestas: máximo N palabras salvo pedido de expansión.
- Estilo: contexto en una frase, luego el punto.
- Prohibido: <formas de respuesta o acciones vetadas>.
- Código: <convenciones del proyecto — estilo, patrones, qué stack usar,
  cómo se nombran las cosas. La forma de escribir código es regla, no gusto>.
- <toda otra regla operativa del proyecto>
```

## Salida

```text
RULES_SOURCE=REGLAS.md|NONE
RULES_LOADED=n
APPLIED=SESSION
CONFLICTS=<con instrucción viva|NONE>
```
