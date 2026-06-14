# Checklist de conformidad estructural (skill `arquitectura`)

> Fuente única de verdad cross-skill. El Verificador del Crisol es un rol LLM:
> lo **localiza con `Glob`** (`**/skills/*/arquitectura/templates/
> conformidad-checklist.md`, o por el namespace declarado) y lo **lee** sobre el
> **diff real** (no sobre la prosa del plan), igual que hoy lee
> `auditor-checklist.md`. NO hay enforcement automático por path: el hook
> `crisol-enforcer.sh` exime los `.md`. Veredicto **binario**: `PASS` / `FAIL`.
> Cualquier ítem en rojo sin justificación en el plan → `FAIL` con
> `capa:archivo`. Si el `Glob` NO encuentra este archivo (el repo no adoptó la
> skill `arquitectura`) → todos los ítems son `N/A` → verde (cero fricción).

## Invariantes mínimos (agnósticos a lenguaje)

- [ ] **(a) Dependencias hacia adentro.** Ninguna capa interna importa una
      externa: entrada/infra → casos de uso → núcleo, nunca al revés. `grep` de
      `import` de framework/ORM/HTTP/SDK en la carpeta del núcleo: un solo hit
      → `FAIL`.
- [ ] **(b) Núcleo sin I/O.** Lógica de dominio sin red, disco, reloj, random,
      env ni framework directos — todo entra por puerto o parámetro. El núcleo
      se testea en memoria, sin red/DB/reloj.
- [ ] **(c) Un puerto por integración externa.** Capacidad/integración nueva =
      adaptador nuevo que implementa un puerto; el núcleo no se edita para
      sumarla. El puerto se nombra por intención de dominio, no por tecnología.

## Núcleo testeable (cruza con REGLA 0 del Crisol)

- [ ] El núcleo tocado tiene test **en memoria** (sin red/DB/reloj) y está
      verde, corrido por el Verificador. Con `TEST_COVERAGE: NONE` el gate de
      verde es subjetivo y hereda el bloqueo del tag estable (Crisol §2).

## Open/Closed estructural

- [ ] El diff NO edita el corazón de un núcleo/puerto estable para extender
      (salvo los 3 casos legales del Crisol §2: bug / refactor de costura en
      corrida propia / cambio de contrato con ADR).
- [ ] No se creó un puerto de entrada secundario / de variación con una sola
      implementación y cero variación prevista (generalidad especulativa =
      deuda). Si se creó → justificar o `FAIL`. (Los puertos de **salida del
      núcleo** son obligatorios día 1 y NO cuentan como especulación.)

## MVC / frontend (si la corrida los tocó)

- [ ] El controller/vista solo traduce transporte ↔ caso de uso; cero regla de
      negocio en el adaptador de entrada.
- [ ] Frontend: ningún nivel bajo importa uno alto; solo la página cruza al
      backend (vía `api/`).
- [ ] Responsive móvil: la UI nueva cumple el criterio de **Crisol §2
      ("Responsive obligatorio", ~390px)** / `auditor-checklist.md` §A2. (Este
      checklist NO redefine el criterio: lo referencia.)

## 12-factor + zero-leak (transversal)

- [ ] Config/secretos por entorno: solo NOMBRES en el código, valores
      inyectados en runtime. Cero hardcode de valor de entorno o secreto.
- [ ] Zero-leak: 0 IPs no-loopback, 0 dominios reales, 0 rutas absolutas, 0
      nombres propios de proyecto/repo/servicio en el diff y los artefactos.

---
`PASS` ⇔ TODOS los ítems aplicables en verde. Cualquier otro caso ⇒ `FAIL`.
Registrar en el RUN-LEDGER: `Conformidad-arq: PASS | FAIL (capa:archivo) | N/A`.
