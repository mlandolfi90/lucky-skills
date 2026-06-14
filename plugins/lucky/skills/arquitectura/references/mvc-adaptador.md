# Capa MVC como adaptador de ENTRADA

> Leé esta capa cuando entra una request (HTTP/CLI/evento) y dudás si va al
> controlador, al modelo o a la vista. Ejemplos ilustrativos — adaptá a tu
> lenguaje/framework.

**Regla de oro:** en hexagonal, MVC NO es la arquitectura — es **un adaptador de
entrega más**, conectado al núcleo por un puerto. El núcleo no sabe que existe un
controller. Si lo supiera, no es hexagonal.

## Dónde cae cada letra de MVC

| Pieza MVC | Capa hexagonal | Rol concreto |
|---|---|---|
| **Controller** | adaptador de entrada (driving) | traduce request crudo → llamada a un **puerto de entrada** (caso de uso). No decide reglas, no toca DB |
| **Vista** | adaptador de entrada (presentación) | renderiza el resultado al transporte (JSON/HTML). Solo formatea — usá un DTO/view-model, no la entidad cruda |
| **Model "clásico"** | **se PARTE en dos** | acá está el malentendido — ver abajo |

## El "Model" se parte en dos (esto es lo que casi todos hacen mal)

El `Model` de MVC mezcla dos cosas que hexagonal separa con un puerto en el
medio:

- **Dominio puro → núcleo.** Entidades + reglas + casos de uso. Cero `import` de
  framework, ORM, HTTP o SQL. Si tu "Model" extiende la clase base del ORM,
  **NO es dominio**: es persistencia disfrazada.
- **Persistencia → adaptador de salida (driven).** El acceso a datos vive detrás
  de un **puerto de salida** (ej. `RepositorioDePedidos`). El núcleo declara la
  interfaz; el adaptador (ORM/SQL/archivo) la implementa. El núcleo depende de
  la interfaz, **nunca al revés**.

## Flujo de una request (la costura completa)

```
request → Controller (adaptador entrada)
            ↓ llama
        Puerto de entrada (interfaz del caso de uso)   ← borde del núcleo
            ↓ ejecuta
        Caso de uso + dominio puro (NÚCLEO)
            ↓ necesita datos → llama
        Puerto de salida (interfaz repositorio)        ← borde del núcleo
            ↓ implementado por
        Adaptador de persistencia (ORM/SQL)
            ↓ devuelve dominio
        ...resultado sube...
        Vista (adaptador entrada) → response
```
*(Ilustrativo — adaptá los nombres a tu lenguaje/framework. Para verlo de punta
a punta con frontend incluido: `references/end-to-end.md`.)*

## El malentendido "¿MVC ya es hexagonal?" — 3 reglas accionables

1. **MVC organiza el borde, no el centro.** Te ordena *cómo entra y sale* la
   request. NO define el núcleo ni protege el dominio. Tener MVC ≠ tener
   hexagonal: te falta partir el Model y meter los puertos.
2. **Controller que hace negocio o toca DB = MVC gordo, no hexagonal.** Controller
   que valida reglas, arma queries o decide flujo de dominio = lógica que
   pertenece a un caso de uso. **Test objetivo:** ¿podés ejercer toda la regla
   de negocio SIN levantar el controller ni la DB (solo el núcleo)? Si no → la
   lógica está atrapada en el adaptador → `REJECT`.
3. **El dominio no importa nada de afuera.** Regla binaria: `grep` de `import`
   de framework/ORM/HTTP/SQL dentro de la carpeta del núcleo. Un solo hit →
   `FAIL`.

## Dónde cae la validación de input

- **Sintáctica / de transporte** (¿el body parsea? ¿el campo existe y es del
  tipo correcto?) → en el controller/middleware (adaptador de entrada).
- **De negocio** (¿el monto es positivo? ¿la transición de estado es legal?) →
  en el value-object o el caso de uso (núcleo).

## Beneficio Open/Closed (por qué vale la pena)

Canal de entrada nuevo (REST → +CLI, +gRPC, +cola) = **adaptador de entrada
nuevo** contra el mismo puerto. El núcleo no se toca. Cambiar de ORM/DB =
adaptador de salida nuevo contra el mismo puerto de salida. Capacidad nueva =
adaptador nuevo, núcleo cerrado a modificación.

## Esqueleto ilustrativo (adaptá a tu lenguaje)

```
<dominio>/        entidades + reglas. Cero deps externas.
<aplicacion>/     casos de uso; DEFINE los puertos (entrada y salida).
<adaptadores>/entrada/   controllers + vistas (MVC vive ACÁ) + CLI + consumers de cola.
<adaptadores>/salida/    repos/persistencia, clientes externos.
```

> Naming sugerido = esqueleto, no atadura: descubrí la convención del repo y
> cedé ante ella. El invariante es la separación, no el nombre.
