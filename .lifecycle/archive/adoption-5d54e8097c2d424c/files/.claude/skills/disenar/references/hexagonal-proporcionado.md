# Hexagonal proporcionado

Cómo se aplica puertos y adaptadores sin que el proyecto se vuelva ceremonia,
y cómo se ve en cada lenguaje. Sale de un prompt de terceros que traía la
dirección correcta y ejemplos que se contradecían con sus propias reglas.

## La pregunta va antes que el patrón

Hexagonal compra **una** cosa: poder cambiar la infraestructura sin tocar las
reglas de negocio, y poder probar las reglas sin levantarla. Todo lo demás
—las carpetas, las interfaces, la inyección— es el precio.

Antes de abrir un puerto, contestá:

1. ¿Hay **variación real**? ¿Existe hoy más de un adaptador, o hay uno
   comprometido para dentro de poco?
2. ¿Necesitás **probar el núcleo sin infraestructura**? ¿La regla es lo
   bastante rica como para que valga la pena aislarla?
3. ¿La infraestructura **va a cambiar**? Migración de base, cambio de
   proveedor, un segundo consumidor.

Si ninguna da que sí, un puerto es indirección sin comprador. Un CRUD de tres
tablas contra una sola base no mejora envolviéndolo en tres capas: empeora,
porque ahora hay que leer tres archivos para entender un `INSERT`.

Esto no es una licencia para saltearse el patrón: es el gate 2 de
`arquitectura-verificar` —tier proporcional— dicho para quien escribe.

## Las capas, y sobre todo qué NO entra

Las dependencias apuntan siempre hacia adentro:
`infrastructure -> application -> domain`. El dominio no importa a nadie.

### Dominio

Entidades, objetos de valor, errores de negocio y **puertos**.

- Prohibido: cualquier framework, ORM, cliente HTTP, logger concreto,
  variables de entorno, `datetime.now()` sin inyectar.
- Los **errores de negocio viven acá**. `SaldoInsuficiente` es una regla, no
  un detalle de transporte. El adaptador los traduce a HTTP 409 o a lo que
  corresponda; el dominio no sabe que existe el 409.
- **El puerto lo define la necesidad del núcleo, no la tecnología.** Un puerto
  que se llama `IMongoRepository` o que expone `find`, `aggregate` y `bulkWrite`
  no es un puerto: es la base de datos disfrazada. El nombre correcto sale de
  la pregunta que el núcleo hace —`¿existe un usuario con este mail?`—, no de
  cómo se contesta.

### Aplicación

Casos de uso y DTOs. Orquesta el flujo llamando puertos.

- Prohibido: HTTP, SQL, nombres de tabla, `req`/`res`, serialización.
- **Acá vive la frontera de la transacción.** Es la pregunta que casi todo
  ejemplo de hexagonal esquiva. El caso de uso decide qué es atómico; el
  dominio no puede saberlo y el controlador no debe. Se resuelve con un puerto
  más —una unidad de trabajo— que el adaptador implementa con la transacción
  real de la base.
- El DTO de salida es la frontera: **la entidad no cruza a infraestructura**.

### Infraestructura

Adaptadores que implementan los puertos, y controladores que reciben pedidos.

- Acá y solo acá: Express, Mongoose, SQLAlchemy, Spring, el cliente de S3.
- El adaptador **mapea** entre el modelo de persistencia y la entidad. Pasarle
  la entidad al ORM es el mismo leak que devolverla por HTTP, del otro lado.

## Los cuatro leaks que pasan igual

Los cuatro estaban en los ejemplos del prompt original, que predicaban las
capas y las violaban en la línea siguiente. Los ejemplos son lo que se copia:
si están rotos, el leak entra al repo con el patrón puesto.

**1. La entidad sale por HTTP.**

```ts
// mal — el dominio cruza a la respuesta
async register(req, res) {
  const user = await this.registerUserUseCase.execute(req.body.email)
  res.json(user)                       // ¿y el passwordHash?
}

// bien — el caso de uso devuelve DTO; el controlador solo transporta
async register(req, res) {
  const dto = await this.registerUserUseCase.execute(req.body.email)
  res.status(201).json(dto)
}
```

Si la entidad se serializa sola, cualquier campo que le agregues mañana
—`passwordHash`, `intentosFallidos`— se publica sin que nadie lo decida.

**2. La entidad entra al ORM.**

```ts
// mal — Mongoose recibe el objeto de dominio
async save(user: User) { await UserModel.create(user) }

// bien — el adaptador mapea, y ese mapeo es su responsabilidad
async save(user: User) {
  await UserModel.updateOne(
    { _id: user.id },
    { email: user.email.value, createdAt: user.createdAt },
    { upsert: true },
  )
}
```

**3. El método que no usa su propio estado.**

```ts
// mal — recibe la edad por parámetro; User ni siquiera tiene edad
class User { isAdult(age: number) { return age >= 18 } }

// bien — la entidad decide con lo que sabe
class User {
  constructor(readonly id: string, readonly email: Email,
              readonly fechaNacimiento: Date) {}
  esMayor(hoy: Date): boolean { return años(this.fechaNacimiento, hoy) >= 18 }
}
```

Un método que ignora `this` es una función suelta con disfraz. Y `hoy` entra
por parámetro a propósito: el reloj es infraestructura.

**4. El puerto que espeja la base.** Ver arriba: el puerto sale de la pregunta
del núcleo, no del esquema.

## Cómo se ve en cada lenguaje

| | Entidad | Puerto | Trampa del lenguaje |
|---|---|---|---|
| **TypeScript** | `class` con campos `readonly` | `interface` | El `type` estructural deja pasar cualquier objeto con la forma: el puerto no protege por sí solo |
| **Python** | `@dataclass(frozen=True)` | `typing.Protocol` | `Protocol` no se chequea en runtime: sin `mypy` en CI, no existe |
| **Java** | POJO puro o `record` | `public interface` | **Prohibido `@Entity`, `@Table`, `@Column`.** El modelo de persistencia es otra clase, en infraestructura |
| **Go** | `struct` | `interface`, **declarada donde se consume** | Go satisface interfaces implícitamente: declarala del lado del consumidor, no del adaptador |

La fila de Go no es un detalle: en Go el puerto se declara donde se usa, así
que la dirección de dependencias sale sola si respetás la convención, y se
rompe sola si no.

## Utilidades: la línea que casi nadie traza

- **Helper técnico** —hashear, formatear una fecha para SQL, armar una query—
  va a `infrastructure/utils`.
- **Helper de negocio** —calcular un recargo, decidir un descuento— va a
  `domain/`, y casi siempre debería ser un método de una entidad o un objeto
  de valor, no una función suelta.

La prueba: si el helper cambiaría porque cambió la base de datos, es técnico.
Si cambiaría porque cambió una regla del negocio, es dominio.

## Una regla que no se chequea no es una regla

Esto es lo que separa este documento de un prompt. La dirección de
dependencias se puede **verificar en CI**, y si no se verifica, se incumple en
silencio hasta que alguien la audita:

- Python: `import-linter` con contratos por capa.
- Java: `ArchUnit`, como test normal.
- TypeScript: `dependency-cruiser` con reglas `forbidden`.
- Go: `go-arch-lint`, o `depguard` en `golangci-lint`.

Un solo contrato alcanza para empezar: *nada dentro de `domain/` importa nada
fuera de `domain/`*. Eso solo atrapa la mayoría de los leaks reales.

## Cuándo NO corresponde

- **El eje no varía.** Un puerto con un solo adaptador que nadie planea
  reemplazar es indirección sin comprador. Mismo criterio que
  [crecer agregando](crecer-agregando.md).
- **La lógica es anémica.** Si la entidad no tiene reglas —es un saco de
  campos— aislar el dominio no aísla nada. Ahí el patrón agrega archivos y
  cero garantías.
- **Un script, una herramienta interna, un spike.** Hexagonal se paga en
  mantenimiento a lo largo del tiempo; lo que no va a vivir, no lo paga.
- **Ya existe y funciona sin capas.** Migrar a hexagonal es un `REFACTOR` con
  su propia escalera y su propio rollback, no algo que se cuela adentro de una
  feature.

## Preguntas para el diseño

- Este puerto, ¿lo pide el núcleo o lo pide la base de datos?
- Si mañana cambio de base, ¿cuántos archivos fuera de `infrastructure/` se
  tocan? Si es más de cero, la frontera está mal.
- ¿Puedo probar este caso de uso sin levantar nada? Si no, el puerto no está
  cortando donde debería.
- ¿Qué entidad se está serializando en la respuesta HTTP? Si la respuesta es
  "una del dominio", ya tenés el leak.
- ¿Quién abre la transacción? Si no lo sabés, todavía no está diseñado.
