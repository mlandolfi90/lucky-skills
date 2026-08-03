---
name: revisor-seguridad
description: Medir qué expone lo construido —puertos, archivos servidos, errores e imágenes— probando con canarios. Usar antes de publicar o exponer un servicio, y tras tocar compose, Dockerfile o el servidor.
---

# Revisor de seguridad

Medir lo que pasa, no leer lo que debería pasar. Una configuración que se ve
bien no es evidencia: el canario sí.

## Invariantes

- Exposición, no custodia: acá no hay ninguna credencial en la mano. Si el
  barrido encuentra un secreto, la custodia y la rotación pertenecen a
  Custodiar secretos; este revisor declara el hallazgo y entrega el relevo.
- Ningún canario lleva un valor real: una cadena única e inofensiva,
  identificable y sin significado fuera de la prueba.
- Un denylist de nombres no es una regla: lo que no puede filtrarse no vive
  bajo una carpeta servida.
- Todo puerto se publica con dirección explícita; sin prefijo, publica en
  toda la red.
- Un error no cuenta lo de adentro: el detalle va al log, afuera va lo
  mínimo.
- Lo horneado en una imagen es permanente: borrarlo en una capa posterior no
  lo retira de las capas anteriores.
- Retirar todo canario al terminar y declararlo; un canario olvidado es la
  fuga que vino a prevenir.
- Solo lectura sobre el sistema observado: probar no autoriza corregir. La
  corrección entra por el escalón que corresponda.

## Frontera

Este revisor mide la superficie del despliegue. La revisión de clases de
vulnerabilidad del código —inyección, XSS, SSRF, deserialización, control
de acceso— la cubren los revisores de código del harness; usarlos a la par y
declarar cuál corrió. Ninguno reemplaza al otro: uno lee el código escrito,
este mide lo que quedó expuesto.

## Flujo

1. Enumerar la superficie declarada: puertos publicados, carpetas servidas,
   endpoints, contextos de construcción de imagen.
2. Sembrar un canario por superficie y pedirlo por el camino que usaría un
   extraño; registrar el resultado observado, no el esperado.
3. Provocar un error real y observar qué devuelve al cliente.
4. Inspeccionar la imagen construida desde adentro, no el archivo de
   exclusión.
5. Retirar los canarios y comprobar que se fueron.
6. Clasificar cada hallazgo con su identificador público de debilidad cuando
   exista, y declarar la cobertura: qué se probó y qué quedó afuera.

## Salida

```text
PUERTOS=<lista dirección:puerto|NONE>
ARCHIVOS_SERVIDOS=<hallazgos|NONE>
ERRORES_FILTRAN=YES|NO|UNKNOWN
IMAGEN_HORNEA=<hallazgos|NONE|NOT_APPLICABLE>
CANARIOS=<probados>/<sembrados>
CANARIOS_RETIRADOS=YES|NO
HALLAZGOS=<id:CWE-nnn,...|NONE>
COVERAGE=<qué quedó sin probar|COMPLETE>
EXPOSURE=CLEAN|FOUND|UNKNOWN
HANDOFF=NONE|CUSTODIA|CAMBIO
```

Usar `UNKNOWN` cuando el canario no pudo probarse; una superficie no probada
jamás se declara limpia. Un hallazgo no autoriza la corrección: se registra
como observación y sube por la escalera.
