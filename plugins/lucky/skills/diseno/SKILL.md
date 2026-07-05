---
name: diseno
description: >-
  Diseño — método anti-slop para TODA interfaz que se cree o modifique (web,
  panel, dashboard, artifact HTML, reporte visual). Disparar al diseñar/armar/
  retocar UI, elegir colores/tipografía/layout, o cuando el humano diga "queda
  feo", "mejorá el diseño", "muy genérico", "/diseno". Primero DESCUBRE el brand
  kit del repo (tokens Style Dictionary / variables CSS) y CEDE ante él; sin kit,
  aplica el sistema neutro de esta skill. Reglas binarias: escala de espaciado,
  paleta por tokens, 1 acción primaria, contraste AA, banderas rojas explícitas
  de slop. Advisory: informa el self-check; el gate duro de móvil ya lo pone la
  regla RESPONSIVE del Crisol. Solo lectura: dictamina y guía, no impone marca.
allowed-tools: Read, Grep, Glob
---

# diseno — que la interfaz no parezca generada

El slop visual es reconocible y por eso es evitable con reglas **binarias**: no
es cuestión de gusto, es cuestión de sistema. Esta skill convierte "queda feo"
en un checklist sí/no.

**Ejes:** sistemática (todo valor visual sale de una escala/token, jamás suelto)
· descubierta (la marca del repo manda; la skill cede) · dura (bandera roja
presente sin justificación = rehacer) · sobria (menos acentos, menos sombras,
menos animación: el contenido es el protagonista).

## Principio rector (LEER PRIMERO)

> **La skill lleva el MÉTODO visual, no la MARCA de tu proyecto.** Cero hex,
> fuentes o logos como verdad fija acá: el brand kit se **DESCUBRE** en runtime.
> Si el repo (o el entorno) provee tokens, esos tokens SON la paleta, la
> tipografía y el espaciado — esta skill solo aporta las reglas de uso y las
> banderas rojas. Sin kit → el sistema neutro de abajo.

## §0 — Arranque (lo PRIMERO al cargar esta skill)

1. **DESCUBRÍ el brand kit** con `Glob`/`Grep`, en orden: config de Style
   Dictionary (`config.json`/`style-dictionary.config.*` + carpeta `tokens/`) ·
   variables CSS/tema (`:root`/`@theme`/`tailwind.config.*`/`theme.*`) ·
   convención visual existente (componentes ya estilados). Hay kit → **cede
   ante él**: consumí SUS tokens y registrá cuál usaste; NUNCA inventes un hex
   si existe un token equivalente.
2. **Sin kit** → aplicá el sistema neutro (reglas de abajo) y decilo en una
   línea ("sin brand kit en el repo: sistema neutro de `diseno`").
3. Diseñá/corregí y cerrá con el **self-check** (§final) informado al humano.

## Reglas duras (binarias — sí o no)

1. **Todo valor visual sale de una escala.** Espaciado: UNA escala (múltiplos
   de 4 u 8 px) — un margen de `13px` es bandera. Tamaños tipográficos: escala
   fija (p. ej. 12·14·16·20·24·32), jerarquía por tamaño+peso, `line-height`
   1.4–1.6 en cuerpo. Radios y sombras: máx 2 valores de cada uno en todo el
   proyecto.
2. **Paleta por tokens, restringida.** 1 color de acento (+ sus estados) ·
   neutros (fondo/superficie/borde/texto) · semánticos (ok/alerta/error). TODOS
   por variable/token — cero hex sueltos en componentes. ≥3 acentos = bandera.
3. **Tipografía: máx 2 familias** (una si alcanza; mono aparte para código).
   Jerarquía visible sin leer: título > sección > cuerpo > secundario.
4. **1 acción primaria por vista.** Un solo botón "lleno" protagonista; el
   resto, secundario/terciario. Dos primarios compitiendo = bandera.
5. **Contraste AA verificado** sobre el fondo real (cálculo o herramienta, no
   a ojo): ≥4.5:1 en cuerpo · ≥3:1 en texto grande (≥18pt o 14pt bold). Texto
   sobre imagen/gradiente sin capa de contraste = bandera. Y el **foco de
   teclado se VE** (`:focus-visible` con contraste propio): foco invisible =
   bandera, tan binaria como el AA.
6. **Claro/oscuro por tokens, no por colores duros.** Si el medio soporta
   ambos temas, los dos se prueban; un solo tema deliberado también vale — pero
   se declara, no se descubre roto.
7. **Grid y alineación.** Los elementos se alinean a una retícula; el
   whitespace es deliberado (separa grupos), no relleno. Lo ancho (tablas,
   código, diagramas) scrollea en su PROPIO contenedor, jamás la página. La
   prosa tiene medida: `max-width` ≈ 60–75ch — texto corrido a todo el ancho
   de la pantalla = bandera.
8. **Contenido real.** Datos/textos verosímiles del dominio — lorem ipsum o
   "Welcome to..." genérico = bandera.
9. **Móvil gatea DURO — pero no acá:** eso ya lo hace la regla `RESPONSIVE`
   del Crisol (§2/§5: viewport ~390px, sin overflow, touch usable). Esta skill
   la referencia por nombre y no la re-enuncia (fuente única).

## Banderas rojas de slop (cualquiera presente sin justificación → rehacer)

- Gradiente decorativo por defecto (el morado→azul de siempre) o texto en degradé.
- Glassmorphism/blur, glow y sombras multicapa **gratuitos** (sin función).
- **Emojis como iconografía** de una UI seria (en prosa conversacional valen;
  en botones, headers y métricas, no).
- `border-radius` gigante en TODO, tarjeta-dentro-de-tarjeta, todo-centrado.
- Animación en cada elemento (la animación señala cambio de estado, no decora).
- Hero genérico, métricas inventadas, badges/pills multicolor sin semántica.
- Densidad extrema en cualquier dirección: pantalla-póster con 3 palabras, o
  muro sin jerarquía.

La justificación válida vive en el pedido o el plan ("es una landing lúdica",
"el cliente pide glass"), no en el gusto del agente.

## Self-check de salida (advisory — se INFORMA, no bloquea)

`tokens/escala ✔·✘ · 1-acento ✔·✘ · 1-primaria ✔·✘ · AA verificado ✔·✘ ·
temas ✔·✘·N/A · banderas-rojas 0..N · RESPONSIVE → la juzga el Crisol`

Es un espejo del patrón i18n (norma viva): la estética NO gatea commits — lo
duro (móvil roto) ya lo gatea `RESPONSIVE`. El self-check hace visible el
criterio; el humano decide.

## Relación con la familia (fuente única, cero duplicación)

- **`arquitectura`** pone la ESTRUCTURA del frontend (`references/atomic-design.md`:
  atoms→pages, solo la página cruza al backend). Esta skill pone la CAPA VISUAL
  encima — no redefine dónde va un componente.
- **Crisol `RESPONSIVE`**: el único enforcement duro de UI, referenciado por
  nombre (regla 9).
- **Brand kit externo** (tokens Style Dictionary del operador): se descubre y
  se consume (§0); crecer esta skill = agregar un adaptador/reference nuevo,
  no editar estas reglas (Open/Closed).

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v1.26.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo
(`raw.githubusercontent.com/mlandolfi90/lucky-skills/<tag>/plugins/lucky/skills/diseno/SKILL.md`)
e informar al humano. **Caso de skill nueva:** si el tag remoto mayor existe
pero NO incluye `diseno/` (la skill nació en este bump), tratar como sin-red —
seguir esta copia y registrar `LEY: <tag> (local, skill nueva sin verificar)`.
Sin red: seguir esta copia y registrar `LEY: <tag> (local, sin verificar)`.
