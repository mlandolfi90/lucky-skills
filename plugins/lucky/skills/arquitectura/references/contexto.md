# arquitectura — contexto y fundamento (no es procedimiento)

> Leé solo si necesitás entender *por qué* esta skill es como es. El SKILL.md y
> las capas son lo accionable; esto es el respaldo conceptual.

## Por qué hexagonal como esqueleto

El enemigo de un proyecto a largo plazo no es la falta de features: es que la
lógica de negocio quede soldada a una base de datos, un framework o una UI que
tarde o temprano cambian. Hexagonal pone el negocio en el centro y todo lo
cambiable en el borde, detrás de puertos. La dependencia apunta hacia adentro:
el detalle depende de la abstracción, no al revés. Eso es lo que hace que sumar
capacidad sea **agregar un adaptador**, no editar el corazón — Open/Closed real,
el mismo invariante que el Crisol §2 protege en el grano.

## Por qué hexagonal NO por default

Hexagonal es un destino, no un peaje. Para un CRUD simple, un script o un spike,
el costo de puertos+adaptadores es ceremonia que no paga. Por eso la skill lleva
una **regla de tier** (`references/migracion.md`): hexagonal completo solo bajo
evidencia de variación; si no, MVC plano. El purismo es tan deuda como el
acoplamiento.

## Por qué MVC como adaptador de entrada (y no como arquitectura)

MVC ordena cómo entra y sale una request, pero no protege el dominio. El error
clásico es creer que "tengo controllers/models/views" = "soy hexagonal", y dejar
el Model soldado al ORM. MVC entra como UN adaptador de entrega; el "Model" se
parte en dominio puro (núcleo) + persistencia (adaptador de salida). Así el
mismo núcleo sirve a REST, CLI o cola sin tocarse.

## Por qué Atomic Design en el frontend

Es Open/Closed aplicado a la UI: una pantalla nueva se compone de átomos y
moléculas existentes en vez de reescribirse. El aislamiento del backend (solo la
página cruza la frontera) replica la regla de dependencia del hexágono en el
front: si cambia el backend, se toca la página, no los componentes de abajo.

## Por qué 12-factor transversal

No es una capa del hexágono: es el cómo se sostiene cualquier capa en cualquier
entorno. Config y secretos por entorno (nombres en el repo, valores en runtime),
build≠release≠run, procesos sin estado, logs a stdout, paridad dev/prod. Hace
que el binario sea idéntico en dev/testing/prod y que la mesa caliente de dev
valide terreno real (Crisol §Versionado, F-6).

## Método-no-mapa (la defensa central)

La skill DEFINE la forma (hexagonal + MVC-entrada + atomic + 12-factor); el
riesgo es que para "ilustrar" se cuele un mapa real. La regla madre:

> **La skill lleva el MOLDE de la arquitectura, NO el plano de TU sistema.**
> Cero rutas, dominios, IPs, nombres de proyecto/repo/servicio/tabla/cola/
> endpoint como verdad fija.

- **Se PARAMETRIZA** lo nombrable: dominio, entidad, caso de uso, puerto,
  adaptador, lenguaje, framework, raíz del proyecto, nombre de variable de
  config (solo el NOMBRE, valor inyectado en runtime).
- **Se DESCUBRE en runtime** lo existente: el árbol real del repo, el lenguaje/
  framework, los dominios/entidades, el naming vigente. La skill cede ante la
  convención real y la registra; no la inventa.

## Zero-leak (repo PÚBLICO)

0 IPs no-loopback, 0 dominios reales, 0 rutas absolutas, 0 nombres propios de
proyecto/repo/servicio, 0 secretos (ni nombres con valor). Antecedente de la
familia (v1.7): un import previo filtró 4 IPs reales y hubo que revertir + purgar
historia. Ante la duda, NO se pone. Placeholders permitidos como único
vocabulario de ejemplo: `<raiz>`, `<dominio>`, `<entidad>`, `<puerto>`,
`<adaptador>`, `<caso-de-uso>`, `example.com`, `<host>`, `localhost`/`127.0.0.1`
(loopback OK), `<VAR_DE_ENTORNO>` con valor `<inyectado-en-runtime>` o
`<REDACTED>`. Los **nombres de variable de ejemplo** son genéricos y neutrales
(`API_KEY`, `DB_URL`, `<SERVICE_TOKEN>`): jamás el nombre real de un secreto de
un proyecto concreto.

## Excepción declarada: el slug del propio repo

La "Ley viva" exige un fetch a un repo concreto para detectar drift de versión.
Por eso el sello cita `github.com/mlandolfi90/lucky-skills` y la URL raw — es la
**auto-referencia funcional** del propio repo público de la familia, idéntica en
brujula/crisol/idea. NO es leak de un tercero: es la convención preexistente y
necesaria del mecanismo. Si algún día se quisiera endurecer, sería parametrizar
el owner vía variable en las 5 skills a la vez (fuera del alcance de esta
forja). Queda registrado como leak conocido/aceptado, no como hallazgo nuevo.

## Prueba de agnosticismo (criterio binario)

"¿Esta skill sirve, sin editar una sola línea, en un repo de otro lenguaje/
dominio/empresa?" Si la respuesta exige tocar un dato concreto (que no sea el
slug del propio repo en el sello), ese dato es un mapa y se convierte en
placeholder. Binario, sin "casi".

## Frontera con el Crisol

Crisol §2 cubre el GRANO (Open/Closed, Atomicidad, costura, planificar dónde
varía el sistema) y el criterio **responsive móvil ~390px**. Esta skill cubre la
ESTRUCTURA MACRO (capas, puertos, MVC-entrada, atomic, 12-factor). Cada concepto
vive en UN solo lado; se referencian por nombre, no se copian. El Arquitecto del
Crisol consulta esta skill; el Verificador la hace cumplir leyendo el checklist
objetivo (`templates/conformidad-checklist.md`), resuelto por `Glob` — el
Verificador es un rol LLM que LEE el `.md` (como ya lee `auditor-checklist.md`),
NO hay enforcement automático por path (el hook `crisol-enforcer.sh` exime los
`.md`). Una sola fuente de verdad; el Crisol resume sus 3 invariantes como
recordatorio no-normativo.
