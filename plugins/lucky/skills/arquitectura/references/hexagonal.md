# Capa NÚCLEO + puertos & adaptadores

> Leé esta capa cuando dudes dónde va lógica de dominio, un puerto o un
> adaptador, o si algo "entra al núcleo". Ejemplos ilustrativos — adaptá a tu
> lenguaje/framework. El invariante es la dirección de la dependencia y la
> pureza, no el nombre de la carpeta (método-no-mapa).

## El núcleo en una línea

El núcleo es **la lógica de negocio sin enchufar a nada**: lo que seguiría
siendo verdad si mañana cambiás de base de datos, de framework web o de UI. En
hexagonal es el centro; DB, HTTP, MVC y frontend atómico son adaptadores que lo
rodean. **La dependencia apunta SIEMPRE hacia adentro: el núcleo no conoce a
nadie de afuera.**

## Las 3 piezas que viven en el núcleo (y solo 3)

| Pieza | Qué es | Regla de oro |
|---|---|---|
| **Entidad** | objeto con identidad y ciclo de vida (un `id` que persiste aunque cambien sus datos) | protege sus invariantes: nace válida o no nace. Cero setters que la dejen inconsistente |
| **Value-object** | valor sin identidad, definido por su contenido (un monto, un email, un rango) | **inmutable** y auto-validado: si se construye, es válido. Dos con el mismo contenido son iguales |
| **Caso de uso** (servicio de aplicación) | orquesta UNA intención del negocio ("dar de alta X", "confirmar Y") | recibe datos planos, llama entidades/value-objects, devuelve un resultado. **Depende de puertos, nunca de adaptadores** |

> Para clasificar: ¿lo comparás por `id` o por contenido? `id` → entidad.
> Contenido → value-object. ¿Coordina varios para cumplir una intención? → caso
> de uso.

## Reglas de PUREZA (invariantes del diff — el Verificador las chequea)

Una unidad del núcleo es pura si su diff **no contiene ninguna de estas**.
Aparición sin justificación en el plan → `FAIL`:

1. **Cero I/O.** Ni disco, ni red, ni `print`/log a stdout, ni reloj/random
   directo. ¿Necesitás la hora o un id nuevo? entra **por parámetro o por
   puerto** (`Reloj`, `GeneradorId`), nunca `now()` adentro.
2. **Cero framework.** Ni anotaciones/decoradores de ORM, ni tipos del router
   HTTP, ni clases base del framework. Un `import` del núcleo que apunta a una
   librería de infraestructura → no es núcleo.
3. **Cero DB/HTTP.** El núcleo no sabe qué es una tabla, una query, un status
   code ni un endpoint. Habla con **puertos** que define acá y se implementan
   afuera.
4. **Cero estado global mutable.** Nada de singletons con estado, variables de
   módulo que mutan, config leída de entorno adentro. Las dependencias **se
   inyectan**.
5. **Determinista y testeable sin mocks de infra.** Mismos inputs → mismo
   output. Un test del núcleo no levanta DB ni servidor ni toca el reloj real.

> Litmus del Verificador: *"¿este archivo del núcleo se puede testear en
> memoria, sin red, sin DB, sin tocar el reloj, en milisegundos?"* No → `FAIL`.

## Cómo se testea el núcleo (el método que la pureza habilita)

La pureza no es un fin: es lo que vuelve el núcleo testeable sin infra. El
método, agnóstico de lenguaje:

1. Por cada **puerto de salida** que usa el caso de uso, escribís un **doble en
   memoria** (un mapa, una lista) que implementa la misma interfaz.
2. **Inyectás el doble** en el caso de uso (mismo constructor/parámetro que en
   prod usa el adaptador real).
3. Ejercés la regla de negocio y asertás sobre el resultado y/o el estado del
   doble. Sin red, sin DB, sin reloj real → milisegundos.

Esto cruza con la REGLA 0 del Crisol (el Verificador corre los tests él mismo):
un núcleo tocado **debe** tener su test en memoria y estar verde. Si el repo
tiene `TEST_COVERAGE: NONE`, el gate de verde es subjetivo y hereda el bloqueo
del tag estable del Crisol §2 (mismo degradado que `references/migracion.md`).

## Los dos tipos de puerto (la asimetría manda)

> Precisión: el **puerto** es la INTERFAZ (el contrato); el **caso de uso** es
> la IMPLEMENTACIÓN del puerto de entrada. No son lo mismo, aunque en proyectos
> chicos se colapsan (ver `templates/estructura.md`).

| Eje | Puerto **driving** (entrada) | Puerto **driven** (salida) |
|---|---|---|
| Quién llama | el mundo → llama al núcleo | el núcleo → llama al mundo |
| Quién **define** la interfaz | el núcleo (la firma del caso de uso) | el núcleo (lo que NECESITA) |
| Quién la **implementa** | el caso de uso (dentro del núcleo); el adaptador de entrada la INVOCA | adaptador de salida (repo, cliente HTTP, publisher) |
| Dirección del `import` | adaptador → puerto/núcleo | adaptador → puerto/núcleo |
| Ejemplo de nombre | `ParaConfirmarPedido` (puerto) → `ConfirmarPedido` (caso de uso) | `RepoPedidos`, `Reloj`, `Notificador` |

**Clave:** en AMBOS casos el `import` apunta al núcleo. Eso es la regla de
dependencia, y para el puerto de salida exige **inversión de dependencia**.

## Inversión de dependencia (lo que hace posible el puerto de salida)

Sin inversión, el caso de uso llamaría directo a la base → el núcleo dependería
de la infra (flecha al revés). Con inversión:

1. El núcleo **declara** un puerto de salida (interfaz) con la firma que el caso
   de uso necesita, en *términos de dominio* (`guardar(Pedido)`, no `INSERT`).
2. El adaptador de salida **implementa** esa interfaz traduciendo a la
   tecnología concreta.
3. En el arranque (**composition root**, el ÚNICO lugar que conoce ambos lados)
   se **inyecta** la implementación concreta en el caso de uso.

Dependés de la **abstracción** que vos definís, no del detalle.

## Ejemplo agnóstico — un puerto, dos adaptadores intercambiables

```
# NÚCLEO — define el puerto de salida en términos de dominio (pseudocódigo)
interface RepoPedidos:                 # ← puerto driven, propiedad del núcleo
    guardar(p: Pedido) -> void
    porId(id: PedidoId) -> Pedido | null

# NÚCLEO — el caso de uso depende SOLO del puerto, no de una impl
class ConfirmarPedido:                 # ← implementa el puerto driving ParaConfirmarPedido
    constructor(repo: RepoPedidos)     # se inyecta la abstracción
    ejecutar(id):
        p = repo.porId(id); p.confirmar(); repo.guardar(p)
```
```
# BORDE — adaptador de salida A: persistencia relacional
class RepoPedidosSql implements RepoPedidos:
    # traduce Pedido <-> filas; aquí (y SOLO aquí) vive el driver SQL

# BORDE — adaptador de salida B: en memoria, para tests
class RepoPedidosMemoria implements RepoPedidos:
    # un mapa; cero infraestructura — ESTE es el doble que testea el núcleo
```
```
# COMPOSITION ROOT (arranque) — el único que conoce ambos lados
caso = ConfirmarPedido(RepoPedidosSql(conn))   # prod
caso = ConfirmarPedido(RepoPedidosMemoria())   # test — núcleo sin infra
```

Cambiar de base, testear sin base, o sumar un tercer adaptador = **adaptador
nuevo, núcleo intacto**. Eso es Open/Closed real.

## El modelo atómico aplicado al núcleo

- **Una unidad = una responsabilidad.** Una entidad protege SUS invariantes; un
  value-object representa UN concepto; un caso de uso cumple UNA intención.
- **Lo grande se arma componiendo lo chico** — no un método de 200 líneas.
- **Open/Closed real:** comportamiento nuevo = unidad nueva, NO editar una
  entidad estable que ya pasó un Crisol. Variar el dominio = componer.
- **Dependencias por parámetro/interfaz**, cero estado global nuevo.

## Qué NUNCA entra al núcleo (lista de rechazo)

- SQL, queries, nombres de tabla/columna, clientes de DB, migraciones.
- Tipos del framework HTTP: request, response, status code, router, middleware,
  DTOs de la API.
- Clientes de red, llamadas a APIs externas, colas/mensajería concretas, ORM,
  anotaciones de persistencia.
- Acceso a config/entorno, lectura de variables, **nombres de secretos** (los
  secretos viven inyectados en el adaptador, jamás en el dominio).
- Logging concreto, `print`, reloj/random sin inyectar.
- Lógica de presentación/UI (Atomic Design — otro adaptador).
- Lógica del controlador MVC (MVC es adaptador de ENTRADA; traduce HTTP→caso de
  uso; no es dominio).

> Test de pertenencia ante la duda: ¿sobreviviría intacto si cambiás de DB, de
> framework y de UI? Sí → núcleo. No → adaptador.

> Smells y veredictos consolidados en `references/anti-patrones.md` (núcleo que
> importa el ORM, `if tipo==...` que crece en lo estable, puerto-Dios, puerto
> que nombra infra, etc.). Acá vive la regla; el catálogo vive allá, una sola
> vez.

## Esqueleto ilustrativo (adaptá nombres a tu proyecto)

```
<nucleo>/                    # puro: cero imports de infraestructura
  dominio/
    entidades/               # objetos con id + invariantes
    value_objects/           # valores inmutables auto-validados
    servicios/               # lógica que no cae en una sola entidad
    eventos/                 # hechos de dominio (en pasado)
  aplicacion/
    casos_de_uso/            # orquesta intenciones, depende SOLO de puertos
  puertos/
    entrada/                 # driving — interfaces de los casos de uso
    salida/                  # driven — RepoX, Reloj, GeneradorId, Notificador
<adaptadores>/               # afuera del núcleo — implementan los puertos
  entrada/ (MVC, CLI, cola)
  salida/  (DB, HTTP, mensajería)
<composition-root>/          # arranque: inyecta adaptadores; lee config (12-factor)
```

> Los nombres de carpeta los DESCUBRÍS o PARAMETRIZÁS por proyecto. Lo que NO se
> negocia es la **dirección de la dependencia** (siempre hacia el núcleo) y la
> **pureza** de lo que vive adentro. El composition root es el ÚNICO que cablea
> dependencias concretas; ningún otro punto las nombra.
