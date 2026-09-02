# Investigación: gate medible de atomicidad y factorización

Estado: **CERRADA** — pase adversarial completo (4 escépticos + veredicto).
Fecha: 2026-08-25. Origen: el operador reporta que la arquitectura se respeta
pero la atomicidad y la factorización en archivos manejables no.

---

## 1. El problema, medido

Distribución de tamaño de archivos fuente (excluyendo `node_modules`, `.git`,
`venv`, `dist`, `build`):

```
repo                        n     p50   p90   max     >400L
Lucky-Auth-Plane            79    172   659   1422    16
Lucky-Debugger              358   60    843   11173   45
Lucky-DesignView            127   136   894   45812   33
Lucky-GNS3                  18    81    185   185     0
Lucky-LLMS                  35    100   271   329     0
Lucky-PizarraEvo            95    37    158   918     2
lucky-tool-binance-tunnel   18    81    185   185     0
lucky-tool-design           6     95    558   558     2
```

Los máximos de Debugger (11173) y DesignView (45812) son ruido: `.impeccable/`
vendoreado —duplicado seis veces— y `out/` de build. Los ofensores reales:

```
Lucky-Auth-Plane   keyring/server.py                1142
                   keyring/handlers/antigravity_direct.py  887
                   auth-portal/server.py             780
                   keyring/handlers/codex_direct.py  691
Lucky-DesignView   plugins/official/codex/codex-app-server-client.ts  1489
                   renderer/src/pages/App.tsx        1438
```

## 2. Anatomía: qué tienen adentro

Los seis son **MONOLITO**, no grandes-pero-coherentes.

| archivo | responsabilidades | corte natural |
|---|---|---|
| `keyring/server.py` | 9 | `cli_runner.py`, `routes/model_test.py`, `routes/oauth_vkey.py`, `routes/models.py` |
| `auth-portal/server.py` | 9 | `sesion.py`, `upstream.py`, `vistas.py`, `rutas.py` (tabla en vez de 18 `if`) |
| `antigravity_direct.py` | 6 | primero extraer lo compartido: `handlers/oauth_refresh.py`, `handlers/limits_cache.py` |
| `codex_direct.py` | 6 | ídem, más `codex_sse.py` y `codex_jwt.py` |
| `codex-app-server-client.ts` | 8 | `codex-executable-verification.ts`, `json-rpc-stdio.ts` |
| `App.tsx` | 9 | `graph/projection.ts` (los tests ya importan de ahí), `useHarness()` |

**El hallazgo mayor no es el tamaño: es la copia entre los cuatro handlers.**
`antigravity_direct` y `codex_direct` comparten la misma receta de refresh OAuth
de ocho pasos con comentarios casi textuales — *"CACHE PRIMERO — si el disco
falla"* aparece en los dos y en `claude_direct`. `_cache_hit` y `_TOKEN_CACHE`
están tres veces. `max(1, len(json.dumps(body)) // 4)` es idéntico carácter por
carácter. En DesignView pasa lo mismo: `writeResult`, `writeError` y
`extractRequestId` son idénticos byte a byte entre `plugins/official/codex/index.ts`
y `plugins/official/claude/index.ts`.

Ningún umbral de tamaño lo hubiera cazado: cada handler es defendible solo.

## 3. Qué señal sirve, y cuál no

Descartadas, medidas contra el código del operador:

- **Imports de dominios distintos** — no separa. `App.tsx`, de los peores, tiene
  2 imports; los archivos limpios tienen 6 a 8.
- **Profundidad de anidamiento** — no separa. `remote.py` (317 líneas, sano)
  tiene indentación promedio 9.0, la misma que `antigravity_direct.py` (887).
  Los monolitos de este operador son **anchos, no profundos**.
- **Churn de git** — correlaciona pero no decide. `keyring/server.py` y `App.tsx`
  son los archivos con más commits de su repo (21 y 9). Sirve para priorizar
  deuda, no para dictaminar un diff.
- **Líneas** — separan bien en su código (limpios p50 81-100, máx 329; marcados
  691-1489) pero avisan tarde, y no ven la duplicación.

Señal elegida: **bocas** — puntos de entrada al archivo desde afuera.

## 4. Cómo norma hoy el catálogo (y por qué no se cumple)

| ubicación | texto literal | medible |
|---|---|---|
| `arquitectura-verificar:32` | "Cambio atómico, archivos proporcionados y ausencia de duplicación evitable" | **no** |
| `arquitectura-verificar:28` | "Responsabilidad única y motivos de cambio concentrados" | no |
| `arquitectura-descubrir:25` | "Señalar ciclos, archivos grandes, responsabilidades mezcladas y seams" | no |
| `arquitectura-ubicar:36` | "Evitar archivos concentradores…" | mitad |
| `arquitectura-ubicar:8` | "Elegir el destino más pequeño…" | no |
| `cambio:34` | "Los microfixes acumulados sobre una responsabilidad compartida se promueven" | no |
| `microfix:40` | campo `PROMOTION=NONE\|ACCUMULATE\|CRISOL` | sin criterio |

### Tres huecos

1. **El tamaño no tiene dueño.** "Proporcionados" nunca dice a qué. Y
   `arquitectura-descubrir:29-30` dice "no prescribir hexagonal desde nombres o
   tamaño" — correcto en su contexto, pero deja el tamaño sin nadie que lo mida.
   Consecuencia exacta: un archivo pasa de 200 a 2000 líneas a +40 por microfix,
   y **cada microfix pasa todos los gates**. `microfix:20` pide "la unidad más
   pequeña", y la unidad más pequeña de un monolito es el monolito.
2. **Ningún gate mira la tendencia, todos miran el estado.** El campo
   `PROMOTION` existe y siempre vale `NONE` porque ninguna skill dice cuándo
   pasar de `NONE`. Contar "este archivo aparece en N recibos de los últimos M
   cierres" es un grep, no una ceremonia.
3. **Duplicación: nombrada una vez, definida cero veces.** Única mención en las
   32 skills, y el adjetivo "evitable" la anula sola.

### Siamesas detectadas

- **"Atómico" significa cuatro cosas en cinco skills**: transaccional
  (`sincronizar:69`), de una sola clase (`logalizar:46`), no tocar archivos
  compartidos (`crecer-agregando:39`), y nada verificable
  (`arquitectura-verificar:32`, `crisol:23`). Dueña propuesta:
  `arquitectura-verificar`; las otras deberían usar otra palabra.
- **"grandes" / "concentradores" / "proporcionados"**: el mismo miedo dicho tres
  veces sin número. Verbos distintos y correctos: `descubrir` reporta, `ubicar`
  evita, `verificar` bloquea.
- **Promoción por acumulación**: `cambio:34` y `microfix:44` dicen lo mismo.
  Dueña: `cambio`, que posee la Escalera. Hoy `microfix` se auto-juzga.
- Modelo sano a copiar: `madrina:16-19` declara su solape con
  `publicar-skill:21-24` en voz alta y por eso no queda siamés.

## 5. El gate propuesto

```markdown
9. Factorización por bocas. Una boca es cada punto por donde se entra al
   archivo sin pasar por otra cosa: definición de nivel superior o ruta
   declarada. Cuenta bocas, no líneas.
   - BLOCK si el diff le agrega una boca a un archivo que ya tenía 12 o más,
     o si crea uno nuevo con 12 o más.
   - PASS si sólo cambia cuerpos existentes, o si parte: las bocas del archivo
     bajan y aparece un destino nuevo en el mismo diff.
   - Un archivo tocado que ya estaba en 12 o más y no creció va a
     PREEXISTING_DEBT. No bloquea.
10. Hermano gemelo. BLOCK si el diff deja tres o más nombres de nivel superior
    repetidos entre archivos hermanos y no declarados como contrato en el
    índice de esa carpeta.
```

Excepción: `monolito-ok: <ruta> — <razón>` en el cuerpo del commit, auditable
con `git log --grep`. Más una lista permanente para archivos que crecen por
adición por diseño (raíz de composición, tabla de ruteo, índice de exports).

**Convergencia**: tres agentes independientes —el que hizo la anatomía y dos
que redactaron desde lentes distintas ("motivos de cambio" y "costo de
revisar")— llegaron solos al mismo diseño: contar bocas, umbral 12, regla del
hermano con umbral 3, deuda previa exenta, escape por línea de commit.

### Calibración

Archivos de producción con ≥12 bocas: Lucky-GNS3 **0**, Lucky-LLMS **0**,
Auth-Plane 12 de 49, DesignView 7 de 51. Los seis monolitos arrancan en 18.
`keyring/server.py` tiene 74.

### Costo, medido

Sobre los últimos 80 commits de Auth-Plane el gate dispararía en **8** — uno de
cada diez — y los ocho son los que construyeron el monolito (`3c708ec`,
`41cb2ae`, `7c65502`, `d0c18f1` sumando rutas a `server.py`; `d37c8a1` a
antigravity). En GNS3 y LLMS: **cero**.

## 6. Defectos verificados de la propuesta

Encontrados **antes** de publicar. Los tres corroborados con comandos.

1. **Contar constantes de módulo confunde datos con responsabilidades.**
   `sextante/receipt_schema.py` da 19 bocas, pero 10 son regex y sets: 365
   líneas con **una** responsabilidad. Excluyendo constantes queda en 9 y deja
   de disparar. Efecto del cambio de patrón:

   ```
   repo                     n    >=12 con constantes   >=12 sin constantes
   lucky-skills/adapters    84   11                    6
   Lucky-Auth-Plane         79   37                    28
   Lucky-GNS3               18   2                     0
   Lucky-LLMS               35   9                     5
   ```

   Lucky-GNS3, el repo limpio, sólo llega a cero con el patrón sin constantes.

2. **La vía de excepción está mal ubicada.** `.lifecycle/.gitignore:1` dice
   `local/`. Un `BOCAS-OK` ahí **no viaja con el repo**: cada clon arranca sin
   excepciones y el gate vuelve a bloquear todo. Mismo detalle que ya mordió con
   los recibos de release.

3. **Falta declarar el alcance del conteo.** Un barrido ingenuo de Auth-Plane da
   79 archivos donde el conteo correcto da 49: la diferencia son tests y copias
   de skills adoptadas bajo `.claude/skills/`. Contar código que el repo no
   escribió es ruido. Excluir: tests, `.claude/skills/`, vendoreado
   (`.impeccable/`), build (`out/`, `dist/`).

## 7. Pendiente

- Falta 1 de 4 críticos (lente "solapamiento") y el veredicto consolidado.
- Sin resolver: qué hacer con "atómico" si se saca del gate 9 — verificar si
  `cierre:13` ya cubre que el diff toque sólo rutas esperadas.
- Sin resolver: el campo `PROMOTION` de `microfix` sigue sin criterio.
- Aparte, listo para publicar: `disenar/references/hexagonal-proporcionado.md`
  (borrador en el scratchpad de la sesión).

## 8. Procedencia

Dos corridas de workflow, ocho agentes. La primera se cortó por lentitud: un
agente se colgó 33 minutos leyendo código para calibrar un umbral numérico, y
las barreras entre fases estaban mal puestas. Se rescataron las dos mediciones
completas y dos de las tres propuestas.

---

## 9. Veredicto adversarial: PUBLICAR_CON_AJUSTES

Cuatro escépticos, nueve ajustes tomados, seis hallazgos descartados.
La propuesta de la sección 5 **estaba mal** en tres formas graves, todas
verificadas con comandos.

### El defecto que la mataba: el incentivo estaba invertido

Contar `^def` incluye los helpers privados. Entonces **engordar el cuerpo de una
función de 400 líneas era `PASS` explícito** ("sólo cambia cuerpos existentes"),
y **partirla en tres helpers privados era `BLOCK`** si el archivo ya estaba en 12.
El gate bloqueaba la descomposición y dejaba pasar el crecimiento interno —
exactamente al revés de lo que el operador pidió. Medido:
`adopcion/transaction.py` tiene 21 bocas, 19 privadas.

### Los otros dos verificados

- **Los tests disparaban.** Auth-Plane tiene 19 archivos de test con 12+ bocas
  (`test_auth_portal.py`=88, `tests/test_server.py`=72). Cada `def test_` contaba.
  Arreglás un bug, escribís el test que lo cubre, y el gate te bloquea por el test.
- **Los tipos y constantes contaban como responsabilidades.**
  `DesignView/src/core/domain/model.ts`: 320 líneas, 39 exports, de los cuales 38
  son `type`/`interface` y una sola función. Agregar un campo al dominio era `BLOCK`.

### Dos errores de diseño que nadie había visto

- **La excepción por trailer de commit es circular.** `arquitectura-verificar`
  corre sobre un diff o plan, **antes** de que el commit exista (en `crisol` es el
  carril 2, y Construir es el 4). Se elimina esa vía.
- **"PASS si parte en el mismo diff" fabrica el cambio mezclado** que la
  atomicidad existe para frenar: el que iba a agregar una función mete un refactor
  de partición para desbloquearse. Se elimina la cláusula.

### Gate final

```markdown
9. Cambio atómico, archivos proporcionados y ausencia de duplicación evitable.
   La proporción se mide por bocas públicas: funciones, clases, métodos de
   clase y rutas declaradas. No cuentan nombres privados, declaraciones de
   tipo, constantes de módulo ni archivos de prueba. Bloquea el diff que suma
   una boca a un archivo que ya llega a doce, o que crea uno con doce o más;
   el archivo tocado que ya estaba en doce y no creció es deuda previa.
   Bloquea también el nombre público nuevo repetido entre archivos hermanos
   sin declararlo como contrato en el índice de su carpeta; lo ya repetido es
   deuda previa. El conteo sale de un comando; sin conteo ejecutado el
   veredicto es `UNKNOWN`, no `BLOCK`.
```

Cambios respecto de la sección 5: **no hay gate 10** — se colapsa adentro del 9 y
el catálogo se queda en 12 gates. Se **conserva** el texto viejo (atomicidad y
duplicación evitable): las bocas operacionalizan "archivos proporcionados", no lo
reemplazan. El `frontmatter` promete atomicidad y ningún otro gate la verifica —
`cierre:13` mide alcance autorizado, que es otra cosa.

Excepción, vía única y versionada: `.lifecycle/state/BOCAS-OK` (no `local/`, que
está gitignoreado). Una línea por excepción, con el número congelado: exime lo que
ya hay, y si el diff lo supera vuelve a bloquear.

### Recalibración verificada

Conteo propio con la definición corregida (públicas, sin tests, sin copias
adoptadas, sin vendoreado):

```
repo                n archivos   con >=12 bocas
lucky-skills        108          0        <- el catálogo pasa su propio gate
Lucky-GNS3            9          0
Lucky-LLMS           18          0
Lucky-PizarraEvo      0          0
Lucky-Auth-Plane     40          5        keyring/server.py=67, mcp-oauth-proxy=15,
                                          oauth_vkey_store=13, core/catalog=13,
                                          handlers/common=12
```

`keyring/server.py` da 67, casi 6× el umbral. Los limpios dan cero. Separa.

**El "74 bocas" de la sección 5 era con la definición vieja y no vale.**

### Riesgo residual, declarado

1. **La calibración dinámica no se rehízo.** El "8 disparos en 80 commits" salió
   de la definición vieja. El número real con la definición nueva se desconoce:
   medirlo colgó al agente. El estado estático sí está medido y es bueno.
2. **La clase God sigue pasando limpia.** `AuthPortalHandler`: 437 líneas, 21
   métodos, 17 privados → cuenta 4 y pasa. Un archivo nuevo con una clase de 2000
   líneas nace en 1 boca y pasa. Es el monolito que el operador nombró y este gate
   no lo ve; lo tapa el gate 5, que juzga leyendo. Se aceptó a propósito: contar
   todos los métodos reinstalaba el incentivo invertido.
3. **El 12 es elegido, no derivado.** Defendible con la definición nueva. Si
   molesta, sube a 15 y Auth-Plane queda en 2 archivos.
4. **Definiciones anidadas adentro de una función escapan al conteo.** Sin arreglo
   barato: pide parsear el AST. Con el conteo de sólo-públicas pierde filo.

### Descartados

Seis hallazgos no entraron. Los dos que importan: contar todos los métodos de
clase (reinstala el incentivo invertido) y una lista negra de nombres de destino
—`helpers`, `utils`, `common`— porque dónde va un archivo lo decide
`arquitectura-ubicar`, no un conteo, y una lista de nombres prohibidos es la
ceremonia que el operador vetó.
