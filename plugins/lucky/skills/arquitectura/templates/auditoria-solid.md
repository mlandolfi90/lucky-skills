# Auditoría SOLID retroactiva (modo READ-ONLY)

> Auditar código **YA existente** contra los invariantes vivos de la familia.
> **Independiente del Crisol:** NO gatea, NO bloquea, NO abre corridas — solo
> LEE y REPORTA. Pero **fuente única compartida:** no redefine ninguna regla; el
> criterio lo referencia POR NOMBRE al mismo catálogo que el Crisol hace cumplir
> y a las mismas capas de esta skill. *Mecanismo separado, criterio compartido*
> — evita el cisma de guardianes.
>
> **Postura de herramienta:** solo lectura, como `brujula`
> (`Read, Grep, Glob, Bash` en modo consulta — cero Write/Edit). La brújula LEE,
> el Crisol ESCRIBE; **esta auditoría LEE y RECOMIENDA** — el depósito lo hace el
> humano u otra corrida.

## De dónde sale el criterio (cero copia de enunciados)

No hay regla nueva acá. Cada lente apunta a su definición canónica y se juzga
CONTRA ella; este template solo aporta el **procedimiento** de detección.

| Lente | Criterio (referenciado POR NOMBRE, no redefinido) | Fuente de verdad |
|---|---|---|
| **S** | `ATOMICIDAD` | Crisol `SKILL.md` §2 (Diseño) · §5 (catálogo) |
| **O** | `OPEN_CLOSED` | Crisol `SKILL.md` §2 · §5 |
| **L** | `LISKOV` | Crisol `SKILL.md` §2 · §5 |
| **I** | `INTERFACE_SEGREGATION` | Crisol `SKILL.md` §2 · §5 |
| **D / capas** | los 3 invariantes mínimos **(a)** deps hacia adentro · **(b)** núcleo sin I/O · **(c)** un puerto por integración | `templates/conformidad-checklist.md` + `references/anti-patrones.md` |

> Regla dura: si algún enunciado de una regla no está claro, se **lee la fuente**
> — NO se parafrasea acá. Un catálogo que reescribe la ley termina driftando de
> ella (justo el defecto que esta auditoría caza).

## Procedimiento — detectá → clasificá → priorizá → reportá → alimentá

### 1. Detectá (por lente)

**Método, no mapa.** El núcleo, la raíz del código y las carpetas de capa se
**DESCUBREN** en runtime (`git ls-files` / `Glob`) — nunca se asumen. El `grep`
se **parametriza** contra lo descubierto; sobre cada hit decide el **juicio
LLM** (el grep encuentra candidatos, no dictamina). Las señales se expresan como
**invariantes independientes del lenguaje**; adaptá el mecanismo:

| Lente | Señal de detección (grep parametrizado + juicio) | Formas por lenguaje |
|---|---|---|
| **S** `ATOMICIDAD` | una unidad descubierta que acumula razones-de-cambio: tamaño desmedido, muchos concerns distintos, alto fan-out de imports heterogéneos, nombres con "y"/"and"/"manager" | función · clase · módulo · struct · paquete |
| **O** `OPEN_CLOSED` | `switch`/cadena `if tipo==…` que **crece** en una unidad estable para sumar comportamiento; ediciones del corazón estable para extender (cruza con churn, abajo) | dispatch por tipo · tabla de handlers que se edita en vez de registrarse |
| **L** `LISKOV` | una impl de una abstracción YA existente que rompe el contrato: guardas/excepciones extra para casos que el supertipo aceptaba (fortalece precondición), retorno degradado (debilita postcondición), o call-sites que preguntan cuál impl es (`isinstance`/type-check aguas abajo) | struct que llena una vtable · puntero-a-función asignado (C) · clase que `implements`/`extends` · trait (Rust) · protocolo (Swift/Python) · handler bajo una clave de dispatch |
| **I** `INTERFACE_SEGREGATION` | contrato ancho donde ningún cliente usa todo: implementadores que dejan métodos en stub/`NotImplemented`/no-op; clientes que tocan un subconjunto chico. La instancia hexagonal es `Puerto-Dios` (ver `anti-patrones.md`) | interfaz · puerto · protocolo · trait · header de C con demasiadas funciones |
| **D / capas** | `import` de framework/ORM/SDK/HTTP/env DENTRO del núcleo descubierto; `new`/instanciación de un concreto en el núcleo; puerto que nombra o filtra tecnología | ver el catálogo `anti-patrones.md` (síntoma → veredicto) |

### 2. Clasificá (severidad objetiva, anclada al gate)

- **ALTA** — *vive una violación que el gate del Crisol **rechazaría si este
  código naciera hoy***. Por definición está anclada al **set vivo** del
  catálogo (Crisol §5): la severidad sigue a la ley, no a la opinión.
- **MEDIA** — violación real pero **localizada** (blast-radius chico, sin
  propagación silenciosa).
- **BAJA / SEÑAL** — *smell* sin evidencia dura; sospecha que aún no prueba daño.

> Consecuencia Kaizen (ver §Kaizen): cuando una regla asciende al set §5, los
> hallazgos que eran BAJA/SEÑAL contra ella **se releen como ALTA** sin cambiar
> el procedimiento — la ancla se mueve sola.

### 3. Priorizá (worst-first)

Ordená por **severidad × blast-radius × churn**:

- **blast-radius** = fan-in: cuántos call-sites dependen de la pieza (contá las
  referencias descubiertas). Una violación polimórfica que corrompe muchos
  llamadores en silencio pesa más.
- **churn** = `git log --oneline -- <path> | wc -l`: lo que más se toca y más
  duele es lo que primero conviene arreglar.

El tope de la lista es lo que un humano debería mirar **primero**.

### 4. Reportá (tabla única)

| # | Principio | Sev | Dónde (archivo:línea) | Qué | Evidencia |
|---|---|---|---|---|---|
| … | S/O/L/I/D | ALTA/MEDIA/BAJA | `<path>:<n>` | una línea | el hit + por qué |

Fuente ilegible o ambigua → **N/D** en esa celda; nunca se rellena por
inferencia.

### 5. Alimentá (SOLO RECOMENDACIONES de ruteo)

El modo es **read-only**: NO escribe en ninguno de estos destinos. Emite, al pie
del reporte, las líneas **candidatas** para que el HUMANO u otra corrida las
deposite:

- **ALTA** → línea candidata para `docs/IDEAS.md` (formato de esa lista;
  candidata a **corrida Crisol** que la arregle).
- **MEDIA recurrente** → entrada **CANDIDATE** tipo **DRIFT** para la skill
  `bitacora` (la ley promete SOLID, el código lo viola).
- **BAJA / SEÑAL** → línea `visto: N` para `bitacora/SENALES.md` (la frecuencia
  del casi-incidente es la que importa).

## Postura — duro con los hechos, blando con la sanción

- **Duro con los hechos:** fuente ilegible → N/D, **jamás** infiere.
- **Blando con la sanción:** nunca bloquea, nunca gatea; hallazgo **≠ culpa**
  (blameless — el código viejo nació bajo otras reglas o sin ellas).

## Kaizen — evidence-triggered, no especulativo

La **misma** violación recurrente en varios repos es **evidencia** para ascender
su regla al catálogo del Crisol (§5) — el disparador es la evidencia acumulada,
NO la especulación. Es el mismo camino que llevó a proponer `LISKOV` e
`INTERFACE_SEGREGATION`: se prueban en lo ya hecho antes de volverse ley.

## Portabilidad (a cualquier repo, cualquier lenguaje)

- **Glob-discovery + N/A-si-ausente:** si una lente no aplica al repo (sin
  núcleo hexagonal reconocible, sin interfaces, sin front) → **N/A**, no defecto.
- **Agnóstico a lenguaje:** las señales son invariantes del código, no keywords
  de un framework — adaptá la forma (punteros a función en C, interfaces, traits,
  protocolos, tablas de dispatch) al stack real.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills`.** Ley viva: con red,
si el repo tiene un tag mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo
(`raw.githubusercontent.com/mlandolfi90/lucky-skills/<tag>/plugins/lucky/skills/arquitectura/templates/auditoria-solid.md`)
e informar al humano. **Caso de skill/plantilla nueva:** si el tag remoto mayor
existe pero NO incluye este archivo (nació en este bump), tratar como sin-red —
seguir esta copia y registrar `LEY: <tag> (local, plantilla nueva sin
verificar)`. Sin red: seguir esta copia y registrar `LEY: <tag> (local, sin
verificar)` en el ledger.
