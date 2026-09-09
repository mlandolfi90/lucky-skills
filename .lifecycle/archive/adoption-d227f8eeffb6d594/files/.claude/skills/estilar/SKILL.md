---
name: estilar
description: Aplicar el estilo visual vigente leyendo su fuente viva de tokens y guías. Usar al construir o revisar UI para que el diseño salga de la marca real, nunca de memoria.
---

# Estilar

El estilo vive en su repo; esta skill lo trae fresco cada vez.

## Fuente

```text
STYLE_SOURCE=github.com/mlandolfi90/lucky-estilo
REF=último tag publicado; sin tags, la rama default
```

La fuente es una sola línea mutable: si la marca se muda de repo, cambiar
esta línea es un PATCH de esta skill. Nada más se toca.

## Invariantes

- Leer el estilo vivo de la fuente en el momento de usarlo: tokens, guías y
  plantillas. Jamás recitar valores de marca de memoria ni de caché.
- Los valores de marca no se inventan ni se aproximan: sin acceso a la
  fuente, se declara y se frena la decisión de estilo. Un color adivinado es
  drift de marca.
- Consumir lo publicado por la fuente (su `dist/` o formato equivalente), no
  sus internos.
- No copiar el estilo al proyecto: consumirlo o referenciarlo según lo que
  la fuente disponga; la copia local nace vencida.
- Toda aplicación cita fuente y versión usada.

## Flujo

1. Resolver la fuente a su referencia vigente.
2. Leer los tokens y guías del alcance que la tarea necesita.
3. Aplicar en el proyecto, citando `STYLE_SOURCE@ref`.
4. Declarar en la salida qué versión del estilo se usó.

## Salida

```text
STYLE_SOURCE=<repo@ref>
SCOPE=<tokens/guías leídas>
APPLIED=<dónde>
FRESHNESS=LIVE
RESULT=APPLIED|UNREACHABLE
```
