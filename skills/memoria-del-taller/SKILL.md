---
name: memoria-del-taller
description: Hablar con la memoria de fichas del taller por verbos, contra la herramienta que el stack declare. Usar cuando una skill pida buscar, leer, proponer, señalar o reportar una ficha síntoma→acción.
---

# Memoria del taller

Que las skills le hablen a la memoria del taller sin saber qué herramienta
hay detrás, y que cambiar de herramienta no toque a ninguna.

Cuando la prosa de una skill dice "el saber", habla de esto: la memoria de
fichas síntoma→acción del taller, sea cual sea su backend. Hoy el backend es
el servicio saber; mañana puede ser otro, y la palabra sigue valiendo.

No es la memoria del harness (los archivos que la sesión guarda sobre el
humano y el proyecto). Ésa es de la sesión; ésta es del taller y la
comparten todas las sesiones de todos los repos.

## Default del catálogo

```text
MEMORIA_DEFAULT=saber:mcp
```

Es una línea mutable: si el taller cambia de herramienta, cambiarla es un
PATCH de esta skill, y ninguna skill que usa la memoria se entera.

## Los cinco verbos

Son los que las skills del catálogo le piden hoy a la memoria, leídos de su
prosa — no se inventó ninguno. Los que usan la memoria hablan en estos
verbos y **nunca** en nombres de herramienta.

| verbo | qué hace | naturaleza |
|---|---|---|
| `buscar` | fichas que matchean un síntoma observado | lectura |
| `leer` | el cuerpo completo de una ficha por su id | lectura |
| `proponer` | una ficha nueva: síntoma, causa, acción, anti-acción, prevención | escritura |
| `senalar` | una sospecha sin evidencia dura, para que se acumule y se cuente | escritura |
| `reportar` | si una ficha consultada sirvió, anclado al recibo de la corrida | escritura |

## Registro de backends

Cada herramienta vive en `references/backends/`, **un backend = un
archivo**. El archivo traduce los cinco verbos a llamadas concretas y deja
escrito cómo se comporta la herramienta de verdad: lo que cuesta, lo que
falla, lo que escribe sin avisar. Agregar un backend no toca esta skill ni
a los otros backends.

## Invariantes

- **Verbos, no herramientas.** El nombre de una herramienta vive sólo en su
  archivo de backend. Una skill que nombra una herramienta de memoria quedó
  atada a ella, y eso es drift esperando a pasar.
- **Un verbo de escritura nunca se usa para mirar.** `proponer`, `senalar`
  y `reportar` dejan rastro en la memoria compartida; para saber si algo
  existe se usa `buscar` o `leer`.
- **La disponibilidad se comprueba, no se supone.** La herramienta del
  backend tiene que estar `INVOKABLE` en esta sesión (concepto *estado de
  capacidad*). Si no lo está, la memoria es `UNAVAILABLE`, se declara, y el
  trabajo sigue: nunca se afirma haber consultado lo que no se consultó.
- **Un corte no es un vacío.** Si una lectura agota su tiempo, el resultado
  es `UNAVAILABLE`, no "no hay fichas". Confundirlos hace que una sesión
  resuelva de cero algo que ya estaba resuelto.
- **Nada secreto entra a la memoria.** Una ficha se escribe con nombres,
  nunca con valores, bajo las reglas de `custodiar-secretos`. Que el
  backend tenga su propio barrido no exime de esto.
- **Jurisdicción: esta skill sabe *cómo*, no *cuándo* ni *qué*.** Qué buscar
  y cuándo lo decide `precedente`; qué reportar al cerrar, `cierre`; qué
  proponer tras un fallo, `autopsia`. Solapamiento parcial declarado con
  `precedente`: ella busca en tres fuentes, y ésta es el conductor de una.
- **El backend por proyecto vive en `REGLAS.md`**, bajo la órbita de
  `cargar-reglas`: una línea `MEMORIA=<backend>:<modo>` alcanza, igual que
  `FORMA=` o `PORTON=`.

## Flujo

La invocan `precedente`, `cierre` y `autopsia` cuando necesitan la
memoria; no se dispara sola.

1. Resolver el backend: lo pedido en la sesión manda; si no, el
   `MEMORIA=` de `REGLAS.md`; si tampoco, el default del catálogo.
2. Comprobar que su herramienta esté `INVOKABLE`. Si no, devolver
   `MEMORIA=UNAVAILABLE` al invocante y terminar.
3. Leer el archivo del backend y traducir el verbo pedido a su llamada.
4. Ejecutar respetando el comportamiento que el archivo declara — por
   ejemplo, preparar la herramienta antes de la primera lectura si el
   backend lo pide.
5. Devolver al invocante el resultado y, si fue una escritura, qué quedó
   escrito y dónde.

## Salida

Se emite sólo cuando la skill actúa, dentro de la salida de quien la
invocó.

```text
MEMORIA=<backend:modo|UNAVAILABLE>
DECLARADA_EN=SESION|REGLAS.md|DEFAULT
VERBO=buscar|leer|proponer|senalar|reportar
ESCRIBIO=SI|NO
```
