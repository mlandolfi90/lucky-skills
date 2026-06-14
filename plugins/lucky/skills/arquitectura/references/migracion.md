# Capa MIGRACIÓN — del MVC plano al hexagonal sin big-bang

> Leé esta capa cuando algo ya existe en MVC plano y dudás si migrarlo, o si
> hexagonal es overkill para lo que vas a hacer. El camino para llegar a la
> arquitectura sin ceremonia que paralice.

## Principio rector

> **La arquitectura es un destino, no un peaje.** Un MVC plano que funciona NO
> se reescribe: se estrangula. Cada feature nueva nace hexagonal; lo viejo migra
> SOLO cuando lo tocás. Cero refactor especulativo: "donde no hay evidencia de
> variación, código simple" (la misma regla del Steward en Crisol §2).

## Regla de TIER (hexagonal NO por default)

Hexagonal no es gratis. Aplicá el costo donde hay variación REAL.

Checklist. **Cualquier "SÍ" → hexagonal completo.** Todos "NO" → **MVC plano**
(controller→servicio→DB directo, sin puertos ni adaptadores):

- [ ] ¿Hay (o se anticipa con evidencia) más de UN canal de entrada o de salida
      para la misma lógica?
- [ ] ¿La lógica de negocio es lo bastante densa como para querer testearla SIN
      tocar DB/red?
- [ ] ¿Se prevé cambiar una pieza de infraestructura (DB, broker, proveedor)
      durante la vida del proyecto?
- [ ] ¿Múltiples personas/sesiones van a extender esto en paralelo (la costura
      evita pisadas)?

| Tier | Forma | Cuándo |
|---|---|---|
| **Plano (MVC)** | controller → servicio → DB, sin puertos | CRUD simple, script, spike, prototipo, un solo canal y sin lógica densa |
| **Hexagonal completo** | entrada → caso de uso → puerto → salida | cualquier SÍ del checklist |

## El mínimo viable hexagonal (MVH) — la barra de entrada

Un proyecto chico NO necesita 6 capas. El MVH son **3 cosas**, agnóstico de
lenguaje:

1. **Dominio puro** — la lógica de negocio en funciones/clases SIN imports de
   framework, DB ni HTTP. Si podés testearla sin levantar nada, ya es hexagonal.
2. **Un puerto por dependencia externa** — interfaz para "lo que sale" (DB,
   cola, API externa). El dominio habla con la interfaz, no con la librería.
3. **El adaptador de entrada es tu MVC** — el controller/handler que ya tenés ES
   el adaptador primario. No lo tirás: lo adelgazás (que solo traduzca
   request→caso-de-uso→response).

> Si tenés esas 3, sos hexagonal. Lo demás (CQRS, event sourcing, múltiples
> adaptadores) es **escalar bajo evidencia**, no requisito.

## Anti-sobreingeniería (gate del Arquitecto)

Un puerto con **una sola implementación y cero variación prevista** es deuda
especulativa → no se crea todavía. **Excepción dura:** las dependencias de
**salida del núcleo** (DB, reloj, random, red, notificador) llevan puerto desde
el día 1 aunque tengan una sola implementación, porque la pureza/testabilidad
del núcleo lo exige (ver `references/hexagonal.md`, Regla 6 del SKILL.md). La
anti-especulación aplica a la **variación de adaptadores** y a puertos de
entrada secundarios: ahí el puerto nace con el 2º adaptador real, o cuando el
test necesita un doble. "1 implementación de un puerto de entrada secundario, 1
uso, cero variación" = clase concreta directa.

## Estrangulamiento por pasos (la receta, sin big-bang)

Cada paso deja el sistema **verde y deployable** (sin esto, no es
estrangulamiento, es reescritura disfrazada):

- **Paso 0 — costura.** Identificar UN caso de uso a migrar (el que vas a tocar
  igual). NO migrar por migrar.
- **Paso 1 — extraer dominio.** Sacar la lógica de negocio del controller a una
  función/clase pura. Comportamiento idéntico (verde antes = verde después).
  Esto es el caso legal (b) del Steward: refactor que abre costura primero,
  extensión después, **corridas Crisol separadas**.
- **Paso 2 — invertir la dependencia.** Lo que el dominio llamaba directo
  (DB/API) pasa a entrar por parámetro/interfaz (puerto). El MVC inyecta la
  implementación concreta en el composition root.
- **Paso 3 — el controller queda fino.** Solo traduce; la regla de negocio ya no
  vive ahí.
- **Repetir** caso por caso. El MVC plano y el hexagonal **conviven**
  indefinidamente; no hay deadline de migración total.

## Atomic Design en el frontend, mismo criterio

Migrar bajo demanda: cuando tocás una pantalla, extraés el componente repetido a
átomo/molécula. **No se hace un design-system upfront** para un front chico —
es la misma trampa de generalidad especulativa. Mini-procedimiento de
estrangulamiento del front: al tocar una pantalla, (1) detectá el bloque
repetido, (2) extraelo al nivel atómico que corresponda (átomo si es
indivisible, molécula si agrupa), (3) recomponé la pantalla usando la pieza
extraída; verde antes = verde después. No migres pantallas que no tocás.

## Tabla "para agregar X → hacé Y" (Open/Closed operativo)

| Querés agregar… | Hacés… | NO tocás… |
|---|---|---|
| Nuevo canal de entrada (CLI, cola, webhook) | adaptador nuevo en entrada que traduce el protocolo y llama al MISMO caso de uso | el caso de uso, el puerto |
| Cambiar la DB (SQL → otro motor, o caché) | adaptador nuevo que implementa el MISMO puerto de salida; recableás en el composition root | el puerto, el caso de uso |
| Nuevo caso de uso | función/clase nueva en aplicación + puerto nuevo si necesita algo del mundo que aún no existe | los casos de uso existentes |
| Nuevo destino de salida (evento, mail) | puerto nuevo + adaptador que lo implementa; el caso de uso lo recibe por parámetro | adaptadores ya escritos |
| Componente de UI nuevo | átomo/molécula nuevo; se COMPONE, no se infla un componente existente | los componentes ya estables |
| Cambiar framework web | reescribís SOLO el adaptador de entrada; el núcleo no se entera | el núcleo entero |

Mnemónico: **capacidad nueva = adaptador o caso de uso nuevo; tecnología
distinta = adaptador que cumple el mismo puerto.** Editar el núcleo solo en los
3 casos legales del Crisol.

## Checklist binario de migración (el Verificador lo corre)

Cualquier NO con violación sin justificar → `FAIL`:

- [ ] ¿El paso dejó el sistema verde? (mismo PASS que Crisol REGLA 0)
- [ ] ¿El dominio extraído no importa framework/DB/HTTP?
- [ ] ¿Se creó algún puerto de entrada secundario / de variación con 1 sola
      implementación y cero variación prevista? (si SÍ → sobreingeniería, `FAIL`
      salvo justificación; NO aplica a puertos de salida del núcleo, que son
      obligatorios día 1)
- [ ] ¿El controller solo traduce (no tiene regla de negocio nueva)?
- [ ] 12-factor: ¿config sensible inyectada en runtime, cero hardcode?

> Nota: "sistema verde después de cada paso" presupone suite de tests. Con
> `TEST_COVERAGE: NONE` el gate de verde es subjetivo y hereda el bloqueo de tag
> estable del Crisol §2.
