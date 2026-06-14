# Capa FRONTEND — Atomic Design como OCP en el front

> Leé esta capa cuando dudes dónde va un componente de UI. El frontend es el
> **adaptador de entrada visual** del hexágono: consume los adaptadores de
> entrada del backend (los controllers MVC / la API), nunca el núcleo ni los
> puertos directos. Ejemplos ilustrativos — adaptá a tu framework. Si el
> proyecto NO tiene UI propia (API-only, SSR puro, CLI, worker) → esta lente es
> N/A, no un defecto.

Atomic Design hace al front **abierto a extensión, cerrado a modificación**: una
pantalla nueva se **compone** de piezas existentes, no se reescribe.

## Los 5 niveles (qué es cada uno, regla de pureza)

| Nivel | Qué es | ¿conoce el backend? | ¿estado? |
|---|---|---|---|
| **átomo** | pieza indivisible sin sentido propio (botón, input, label, ícono, spinner) | NO | sin estado (props puras) |
| **molécula** | grupo chico de átomos con UNA función (campo-con-label, search-box) | NO | sin estado de dominio |
| **organismo** | sección autónoma y reusable (formulario, navbar, tabla) | NO directo — recibe datos/callbacks por props | local de UI (abierto/cerrado), nunca fetch |
| **template** | esqueleto de layout SIN datos reales (slots/placeholders) | NO | ninguno |
| **página** | template + datos REALES; **único nivel** que habla con el backend | SÍ — vía capa `api/` | orquesta estado y side-effects |

> **Dirección de dependencia:** los niveles bajos NUNCA importan a los altos.
> Átomo no importa molécula; molécula no importa organismo. Solo se compone
> hacia arriba. Una flecha al revés → `FAIL`.

> **Aislamiento (clave del hexágono):** del átomo al template son **agnósticos
> del backend** — no saben de URLs, DTOs ni endpoints. SOLO la **página** conoce
> la forma de los datos y los pide. Si cambia el backend, se toca la página, no
> los 200 componentes de abajo.

## Cómo el front consume el adaptador de entrada del backend

Contrato: **solo la carpeta `api/` y las páginas cruzan la frontera**. El resto
del árbol ni se entera de que existe un backend.

```
página → api/ → [HTTP] → adaptador de entrada (controller MVC / REST) → puerto → núcleo
```

- La base-url y credenciales se **inyectan por entorno** (12-factor): solo el
  NOMBRE en el código (`API_BASE_URL`), jamás hardcode ni dominio real.
- `api/` mapea respuesta del backend → tipo del front (anti-corruption layer
  chico). Si cambia un DTO, se toca acá, no en los componentes.
- Los organismos reciben **datos ya resueltos** y **callbacks** por props (ej.
  `onSubmit`); no llaman a `api/` ellos mismos. Eso los deja reusables y
  testeables sin red.

## Cómo se testea un organismo (sin red)

Un organismo se testea pasándole **datos + callbacks por props** y asertando
render/interacción; no se le inyecta `api/` ni se levanta backend. Si para
testearlo necesitás red, el organismo está acoplado de más → extraé el fetch a
la página.

## Carpeta y naming (descubrir, no imponer)

Estructura de referencia (adaptá la raíz `<src>/` a lo que tu stack ya use —
`src/`, `app/`, `lib/`; **descubrí** la convención existente antes de crear):

```
<src>/
  components/
    atoms/        boton/ input/ etiqueta/ icono/
    molecules/    campo-form/ search-box/ card-header/
    organisms/    form-login/ navbar/ tabla-usuarios/
  templates/      layout-dashboard/ layout-auth/
  pages/          login/ dashboard/ detalle-usuario/
  api/            cliente http + funciones por recurso (la costura al backend)
```

- Carpeta por componente; nombre = **rol**, no implementación (el variant es
  prop, no archivo nuevo).
- 1 componente = 1 carpeta con su test y sus estilos colocados (co-location).
- Prohibido `utils.js` cajón-de-sastre en components: cada pieza es atómica.
- Idioma del naming: cedé a la convención DESCUBIERTA del proyecto (inglés o
  español) — la skill verifica coherencia, no la cambia.

## Por qué esto ES OCP en el front (componer, no reescribir)

- **Feature nueva = pieza nueva + composición.** Se agrega un átomo/molécula/
  organismo y se **compone** una página; las piezas estables no se editan.
- **La variación entra por prop o slot** (la costura), no editando el componente
  estable. Costura ausente → primero refactor que la abre (verde antes/después),
  después la extensión — dos pasos, como manda el Crisol §2.
- **El átomo estable es intocable:** un botón que ya pasó el Crisol no se
  modifica para una pantalla nueva; se **envuelve** o se **parametriza**.
  Editarlo para una feature puntual → `REJECT`.
- **Atomicidad literal:** cada componente tiene UNA responsabilidad y recibe
  dependencias por props (cero estado global nuevo).

> Estado compartido entre páginas (store/context global): vive en una capa de
> estado de aplicación del front (agnóstica de la librería concreta), fuera del
> árbol atómico. Si lo metés en un organismo, reintroducís el acoplamiento que
> el árbol evita.

## Responsive móvil

La regla de **responsive obligatorio (~390px)** y su criterio de PASS/FAIL
(incluido "PASS de sandbox/desktop NO cuenta como PASS móvil") vive UNA sola vez
en **Crisol §2 ("Responsive obligatorio")** y en su `auditor-checklist.md` §A2.
Esta capa NO la redefine: la **referencia por nombre**. Toda página/organismo
nuevo o modificado queda sujeto a ese criterio del Crisol.

## Criterios de FAIL/REJECT del front (el Verificador los aplica)

- import de nivel bajo → alto (dirección de dependencia rota) → `FAIL`
- componente bajo template que importa `api/`/fetch (aislamiento roto) → `FAIL`
- dominio/url real hardcodeado en vez de variable de entorno → `FAIL`
  (zero-leak + 12-factor)
- edición del corazón de un componente estable para extenderlo sin
  justificación → `REJECT` (OCP)
- UI nueva sin PASS móvil → `FAIL` (criterio: Crisol §2 / auditor §A2)

> Frameworks que imponen su propia estructura (server components, módulos): la
> skill lleva el MÉTODO — DESCUBRÍ y adaptá la convención existente, no impongas
> el árbol literal.
