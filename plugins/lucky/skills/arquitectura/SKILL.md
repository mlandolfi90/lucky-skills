---
name: arquitectura
description: >-
  Arquitectura — responde "¿dónde va este archivo/módulo?", "¿esto rompe la
  arquitectura?", "armá/revisá la estructura", "/arquitectura". Define la
  ESTRUCTURA de un proyecto (qué va dónde, naming, fronteras entre capas) y la
  hace consultable. Esqueleto HEXAGONAL (puertos & adaptadores) + MVC como
  adaptador de ENTRADA + Atomic Design en el frontend + 12-factor transversal.
  Disparar al ubicar/armar/revisar estructura, o al crear un
  módulo/adaptador/puerto/componente. DESCUBRE la forma real del repo antes de
  dictar — método, no mapa. Es el criterio que el Arquitecto del Crisol consulta
  y el Verificador hace cumplir. Solo lectura: describe y dictamina, no escribe
  estructura por su cuenta.
allowed-tools: Read, Grep, Glob, Bash
---

# arquitectura — ¿dónde va esto y qué no se cruza?

Cuatro ejes, sin excepción: **óptima** (separa por razón-de-cambio, no por
capricho) · **agnóstica** (sirve en cualquier lenguaje/stack) · **dura**
(frontera cruzada sin puerto = bandera roja) · **abierta** (crece por
adaptadores, no editando el corazón).

Es un **índice de carga progresiva**: este archivo es liviano; el detalle vive
en capas que se leen **solo cuando la tarea las necesita**. El método estructural
vive acá; el Crisol no lo duplica — lo consulta (Arquitecto) y lo hace cumplir
(Verificador). El *porqué* está en `references/contexto.md` — no hace falta para
ejecutar.

## Principio rector (LEER PRIMERO)

> **La skill lleva el MÉTODO de estructura, no el MAPA de tu proyecto.**
> Cero paths, nombres de módulo, dominios o raíces como verdad fija: la raíz del
> código, los nombres de los módulos y los adaptadores concretos se **DESCUBREN**
> en runtime o se **PARAMETRIZAN**. Cualquier ejemplo de carpeta es ilustrativo
> — adaptalo a tu lenguaje/framework. El invariante NO es el nombre de la
> carpeta: es la **separación de capas** y la **dirección de la dependencia**.

## §0 — Arranque (lo PRIMERO al cargar esta skill)

El arranque ACTIVO (escaneo + reporte) aplica cuando el disparador es
**ubicar/armar/revisar la estructura real** (`/arquitectura`, "armá/revisá la
estructura", "¿dónde va X?" sobre el repo). Si el disparo fue por matching
implícito a mitad de otra tarea o es una **consulta conceptual** ("¿qué es un
puerto?"), NO escanees: confirmá la intención en una línea y respondé a nivel
método. Cuando sí corresponde escanear:

1. **DESCUBRÍ la forma real.** `git ls-files` / `Glob` para mapear la raíz del
   código y las carpetas de primer nivel (NO asumas `src/`). Identificá
   lenguaje/framework por los manifiestos presentes. Si ya hay convención de
   naming → la skill **cede ante ella** y la registra; no la reescribe.
2. **MAPEÁ lo encontrado a las lentes APLICABLES** (núcleo · MVC-entrada ·
   atomic · 12-factor) y reportá una línea por lente: qué capa existe, cuál
   falta, qué está mezclado. Marcá como **N/A** la lente que el repo no usa (atomic y
   MVC-entrada no aplican a un CLI, una librería o un worker sin UI/entrada web)
   — N/A NO es un defecto.
3. **Aplicá la regla de tier antes de ofrecer esqueleto**
   (`references/migracion.md`). Si el checklist de tier da todos NO → recomendá **MVC plano**
   (controller→servicio→DB), no el árbol hexagonal completo. Hexagonal no es por
   default; el purismo es deuda.
4. **Si NO hay estructura reconocible y el tier lo justifica** → ofrecé el
   esqueleto (`templates/estructura.md`) parametrizado a la raíz y nombres
   descubiertos. **Si SÍ la hay** → no la reescribas: señalá los desvíos y
   ruteá.
5. **Decile al usuario: "Estás ubicado en la arquitectura. ¿Dónde va lo que
   querés meter, o qué reviso?"** y ruteá por la tabla Router.

## Router — leé SOLO la capa que necesitás

| Tu tarea | Capa | Qué resuelve |
|---|---|---|
| ¿Dónde va esta lógica de dominio / un puerto / un adaptador? ¿qué entra al núcleo? ¿cómo testeo el núcleo? | `references/hexagonal.md` | núcleo puro, puertos como interfaces, adaptadores en el borde, dirección de la dependencia, test en memoria |
| Entra una request HTTP/CLI/cola — ¿controlador, modelo, vista? | `references/mvc-adaptador.md` | MVC es el adaptador de ENTRADA, no la arquitectura global; el "Model" se parte en dos |
| ¿Dónde va un componente de UI? | `references/atomic-design.md` | atoms→…→pages; dónde corta cada nivel; solo la página cruza al backend |
| Config, logs, build, deploy, secretos, estado | `references/doce-factor.md` | las reglas transversales, agnósticas; nombres en repo, valores en runtime |
| El cambio toca CI/CD o infra de deploy — ¿cómo se buildea/promueve una imagen sin rebuildear en prod? | `references/deploy-build-once-promote.md` | patrón build-once-promote: CI buildea una vez, el `<paas>` solo pullea y promueve la misma imagen `sha-<commit>`; roles vendor-neutral, footguns |
| Esto ya existe en MVC plano — ¿cómo migro sin big-bang? ¿hexagonal es overkill? | `references/migracion.md` | mínimo viable hexagonal, regla de tier, estrangulamiento paso a paso |
| Quiero ver UNA feature ubicada de punta a punta en las 4 capas | `references/end-to-end.md` | walkthrough de una feature cruzando front → MVC → puerto → núcleo → puerto → adaptador |
| ¿Cuáles son los anti-patrones que rechaza? | `references/anti-patrones.md` | catálogo transversal: síntoma → por qué rompe → veredicto |
| Auditar si el código YA existente cumple SOLID (retroactivo, read-only) — ¿qué violaciones viven y cuáles duelen primero? | `templates/auditoria-solid.md` | procedimiento detectá→clasificá→priorizá→reportá→alimentá con severidad anclada al gate del Crisol |
| ¿Por qué esta arquitectura? | `references/contexto.md` | fundamento, no procedimiento |

## Reglas de estructura (innegociables, binarias)

El corazón que el Verificador del Crisol hace cumplir. Son **invariantes del
diff** (sí/no), no jerga de framework: valen igual en C (punteros a función),
interfaces (Java/C#/TS), traits (Rust), protocolos (Python/Swift). El detalle de
QUÉ capa es cuál lo definen las capas; acá viven los invariantes universales.

1. **Dependencias hacia adentro.** Todo apunta al núcleo; el núcleo no importa
   NADA externo (framework, ORM, SDK, HTTP, env). Un `import` del núcleo que
   nombra infraestructura → bandera roja.
2. **Núcleo puro, sin I/O.** Lógica de dominio sin red, disco, reloj, random,
   env ni framework directos. Lo que necesita del mundo entra por **puerto**
   (interfaz) o por parámetro. Litmus: si no se testea en memoria, sin red/DB/
   reloj, en milisegundos → no es núcleo.
3. **Toda E/S cruza por un PUERTO.** El núcleo POSEE y DEFINE las interfaces; el
   borde las IMPLEMENTA. Naming del puerto = intención del dominio
   (`<Entidad>Repositorio`, `Notificador`), NUNCA la tecnología (la tecnología
   nombra al adaptador: `<Entidad>RepositorioSql`, `NotificadorSmtp`).
4. **MVC vive DENTRO del adaptador de entrada.** Controladores/vistas traducen
   transporte→caso de uso y no contienen reglas de negocio. El frontend atómico
   es otro adaptador de entrada: solo la página cruza al backend.
5. **Open/Closed real.** Capacidad nueva = adaptador o caso de uso NUEVO;
   tecnología distinta = adaptador que cumple el MISMO puerto. El núcleo y los
   puertos estables NO se editan para extender — se extiende COMPONIENDO. (Tocar lo estable
   solo en los 3 casos legales del Crisol §2: bug, falta-la-costura con corrida
   propia, o cambio de contrato con ADR.)
6. **Un puerto por capacidad que VARÍA — con una excepción dura.** La
   anti-especulación (no crear un puerto con una sola implementación y cero
   variación prevista) aplica a la **variación de adaptadores** y a los puertos
   de **entrada secundarios**. NO aplica a las **dependencias de salida del
   núcleo** (DB, reloj, random, red, notificador): esas exigen puerto desde el
   día 1, porque la pureza de la Regla 2 lo obliga (el test en memoria necesita
   el doble desde el inicio). Resumen: salida-del-núcleo → puerto siempre;
   variación de tecnología → puerto cuando hay 2º adaptador real o el test pide
   un doble.
7. **12-factor transversal.** Config/secretos por entorno: en el código solo
   **nombres**, valores inyectados en runtime; build≠release≠run; procesos sin
   estado; logs a stdout. Detalle y criterios en `references/doce-factor.md`.
8. **Naming descubierto, no impuesto.** La skill verifica COHERENCIA con la
   convención existente del repo, no la cambia. El idioma de dominio/casos de
   uso es el del negocio (ubiquitous language), no jerga de framework.

> Regla de tier (hexagonal NO por default): hexagonal completo solo si hay (o se
> anticipa con evidencia) más de un canal de E/S para la misma lógica, lógica
> densa que querés testear sin DB, cambio de infra previsto, o extensión en
> paralelo. Si no → MVC plano (controller→servicio→DB). Migración sin big-bang en
> `references/migracion.md`.

## El hook fino al Crisol (sin duplicar, sin inflar)

Mecanismo de dos puntas, una sola fuente de verdad:

- **El Arquitecto (Architecture Steward) la CONSULTA** al planificar: ¿dónde cae
  la pieza? ¿es puerto driving o driven? ¿entra por la costura existente o exige
  adaptador nuevo? El Steward NO redefine la estructura: la lee de esta skill.
- **El Verificador la HACE CUMPLIR** sobre el diff real: LEE
  `templates/conformidad-checklist.md` (igual que hoy lee `auditor-checklist.md`
  — es prosa para un rol LLM, NO un enforcement automático; el hook
  `crisol-enforcer.sh` exime los `.md` y no cambia). Aplica los 3 invariantes
  mínimos + zero-leak. Violación de capa sin justificación en el plan → `FAIL`,
  igual que el resto de invariantes del diff.

> **Cómo resuelve el Verificador el checklist (no hay magia de path):** corre un
> `Glob` por `**/skills/*/arquitectura/templates/conformidad-checklist.md` (o por
> el namespace declarado `arquitectura`/`lucky:arquitectura`). Si lo encuentra →
> lo lee y lo aplica. Si NO lo encuentra (repo que no adoptó la skill) → los
> ítems marcan `N/A` y dan verde: cero fricción. El checklist canónico vive UNA
> sola vez, acá; el Crisol lo referencia por nombre y resume sus 3 invariantes
> como recordatorio **no-normativo** (la fuente es este archivo, no la copia del
> Crisol). Frontera limpia: Crisol §2 cubre el GRANO (Open/Closed, Atomicidad,
> costura); esta skill cubre la ESTRUCTURA MACRO (capas/puertos/MVC-entrada/
> atomic/12-factor). Cada concepto en UN solo lado, referenciado por nombre.

## Open/Closed en la propia skill

Ampliar = agregar un `reference` nuevo (`references/cqrs.md`,
`references/event-driven.md`) + una fila al Router. El SKILL.md (núcleo) NO se
edita para sumar un estilo. Es Open/Closed aplicado a la skill misma.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v1.27.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo
(`raw.githubusercontent.com/mlandolfi90/lucky-skills/<tag>/plugins/lucky/skills/arquitectura/SKILL.md`)
e informar al humano. **Caso de skill nueva:** si el tag remoto mayor existe
pero NO incluye `arquitectura/` (la skill nació en este bump), tratar como
sin-red — seguir esta copia y registrar `LEY: <tag> (local, skill nueva sin
verificar)`. Sin red: seguir esta copia y registrar `LEY: <tag> (local, sin
verificar)` en el ledger.

**Capas:** `references/hexagonal.md` · `references/mvc-adaptador.md` ·
`references/atomic-design.md` · `references/doce-factor.md` ·
`references/migracion.md` · `references/end-to-end.md` ·
`references/anti-patrones.md` · `references/contexto.md`
**Templates:** `templates/conformidad-checklist.md` · `templates/estructura.md`
