# 0001 — loader `cargar`: skill-como-datos verificado por codigo, TOFU install-only, registry firmado

- estado: aceptado — SUPERSEDIDO PARCIALMENTE por ADR 0009 (2026-07-09): la
  cadena de firma minisign (§2 ancla TOFU, firma del §3) fue retirada; la
  integridad quedo sha256-only + pin por commit. El resto del diseño del loader
  (skill-como-datos, capability-gate, nonce, MODO MANUAL, carga progresiva,
  idempotencia activa) sigue vigente. Este documento se conserva como historia.
- fecha: 2026-06-14
- decide: MLL (operador)
- tags de la familia al sellar: v1.8.0 (loader y manifiesto comparten el commit del release)
- relacionado: dictamen rank-1 del Concejo previo ("loader skill-como-datos"); RUN-LEDGER `docs/refactor/_crisol/RUN-LEDGER.md`

## Contexto

La familia `lucky` carga skills por enumeracion al **arrancar** la sesion. La "Ley
viva" (footer de cada SKILL.md) refresca el **contenido** de una skill **ya
enumerada**: con red, busca un tag mayor y avisa. Eso cubre "la skill existe pero
esta vieja".

No cubre "la skill **nacio** en un bump posterior": una carpeta nueva
(`plugins/lucky/skills/<nueva>/`) **no es invocable a mitad de sesion**. El harness
fijo su catalogo al iniciar; sumar una skill nativa exige reiniciar el plugin
(`/reload-plugins`) o un canal de runtime equivalente. El operador trabaja en
sesiones largas y cross-IA (Claude / GPT / Gemini); reiniciar rompe el hilo y no
todos los harness lo ofrecen.

El **unico canal universal** que todo LLM-en-loop comparte es el **historial de
mensajes**. Una skill puro-texto-autocontenido (p. ej. arquitectura) **es solo
texto**: su valor es el metodo, no una tool nativa. Entonces se la puede traer al
contexto **como datos** y el modelo la sigue como sigue cualquier instruccion del
historial — sin reiniciar, sin tocar disco, agnostico al harness.

El riesgo de inyectar texto-como-instruccion es real: ese texto es **dato no
confiable** (viene de la red, podria estar manipulado). Por eso la decision no es
"pegar la skill y listo", sino un loader con **cadena de confianza criptografica
ejecutada por codigo**, **aislamiento del payload** y **limites de scope explicitos**.

Decisiones del operador ya cerradas que este ADR documenta (no re-debate): nombre
`cargar`; firma **minisign** (Ed25519, un binario); ancla **TOFU install-only**;
manifiesto `registry.json` generado y firmado por un **script de release**; scope
v1 **puro-metodo + fallback declarado**.

## Decision

### 1. Loader skill-como-datos (`cargar`), verificado por codigo

Se crea la skill `cargar`. Resuelve una skill nueva contra un **catalogo** y la
**inyecta al historial como datos verificados por codigo**, entre delimitadores
con nonce de sesion. No instala nada nativo: hace invocable el **metodo** en la
sesion viva. Termino interno: **"resolver-de-catalogo"** (NO "router" — "router"
ya nombra las capas intra-skill de `management`).

`allowed-tools` del loader: **solo lectura** — `WebFetch, Read, Grep, Glob`. **Sin
Bash.** El modelo no ejecuta la cripto ni la transcribe: el fetch+verify del cuerpo
lo hace un **fetcher-codigo externo** (hook `UserPromptSubmit` ->
`hooks/cargar-fetch-verify.sh`) que trae bytes crudos, verifica y emite el bloque
con nonce SOLO si exit 0. **WebFetch NO sirve como canal de carga** (convierte a
markdown y resume: muta los bytes, no pasa `sha256`/`minisign`); queda degradado a
aviso opcional de "hay tag mayor". Sin fetcher-codigo cableado -> **MODO MANUAL**.

### 2. Ancla de confianza: TOFU install-only con minisign

- Firma: **minisign** (Ed25519). Un binario, multiplataforma, verificacion por
  exit-code.
- La clave **publica** se hornea (baked) en el **install** del loader — en disco,
  **fuera del repo**. Trust On First Use; **sin** pin out-of-band, por decision
  explicita del operador.
- La clave **privada** vive **solo** en la maquina del operador / Infisical.
  **Jamas** en el repo.

### 3. Manifiesto `registry.json` por script de release; pin por COMMIT

Un **script de release** (`scripts/forjar-release.sh`, corre en la maquina del
operador, con la privada):

1. enumera las skills y su clase: `loadable_as_data` solo si es
   **puro-texto-autocontenido** (ni `requires_runtime` ni `requires_tools`);
2. calcula el **sha256 de cada SKILL.md** (sobre bytes LF) y el **commit SHA40**
   del release;
3. **bumpea y verifica los N sellos** de la familia **y de `docs/decisions/*.md`**
   (salda la deuda "bump N sellos a mano" del RUN-LEDGER);
4. valida el `registry.json` contra `registry.schema.json`, lo emite (catalogo
   liviano con `tag`, `commit`, y por skill clase/path/sha256) y lo **firma con
   minisign**;
5. crea el **tag** y publica; loader y manifiesto quedan del **mismo commit**.

### 4. Scope v1: puro-texto-autocontenido + fallback declarado

`cargar` solo trae skills con `loadable_as_data: true`. Una skill que declara
`requires_runtime` (hook, allowed-tools de escritura, auto-trigger,
`disable-model-invocation` — crisol, idea) **o** `requires_tools` (depende de
ejecutar `Bash`/`Write`/etc. para su metodo — brujula, management) **no se puede
representar como dato sin castrarla**: el loader la **rechaza como dato** y rutea
al **fast-path de install** (`/reload-plugins` o subagente). En la familia actual,
**solo `arquitectura`** es realmente cargable-como-dato; `cargar` se auto-marca
`loadable_as_data: false` (sus hooks SON el verify; no se auto-carga).

### 5. Agnosticismo condicional a `fetch_verify`

| Harness | `fetch_verify` (cripto FUERA del modelo) |
|---|---|
| Claude | hook `UserPromptSubmit` -> `cargar-fetch-verify.sh` (curl + minisign -V + sha256 -c; emite bloque con nonce solo si exit 0) |
| GPT / funcion-calling | accion del integrador que corre la cripto y devuelve el bloque ya verificado con nonce; **si el exit-code vuelve al modelo como texto -> MODO MANUAL** |
| Gemini / ReAct | idem; en ReAct donde el loader ES el modelo -> MODO MANUAL |
| sin `fetch_verify` | **MODO MANUAL**: imprime el path `raw@<commit>` + comando de verificacion; el humano verifica out-of-band; el loader **NUNCA** auto-inyecta |

### 6. Aislamiento del payload (datos != reglas)

- El bloque inyectado va entre delimitadores con **nonce de sesion** generado por
  el ENTORNO (no por el modelo ni el payload).
- El contenido es **dato no confiable**: **no** puede re-apuntar el origen, leer
  secretos, correr shell ni desactivar reglas.
- Las **reglas de seguridad viven en el codigo/system**, no como prosa que el
  payload pueda "purgar". El marcador de purga lo emite **solo el fetcher-codigo**.

### 7. Carga progresiva + idempotencia activa

Manifiesto liviano -> capa raiz -> sub-capas por **fetch del mismo commit** (no a
disco). **Antes de usar X**, confirmar que su bloque sigue en contexto; ante duda
-> **re-fetch + re-verify incondicional** (jamas "me acuerdo que decia"). Liberar
contexto: **cap duro** de skills activas, o **puntero + hash re-fetcheable** —
nunca olvido-logico fragil.

## Modelo de amenaza

Atacante: cualquiera que pueda alterar lo que llega al contexto del modelo (repo,
CDN/red, o el propio payload). Activo: que el modelo siga **solo metodo autentico
del operador**, sin ejecutar instrucciones inyectadas ni filtrar secretos.

| Amenaza | Vector | Defensa | Resultado |
|---|---|---|---|
| **Repo / CDN comprometido** | manipulan `raw` o mueven un tag | el fetcher trae bytes crudos `raw@<commit>` (commit = inmutable) y corre `minisign -V` del registry + `sha256 -c` del cuerpo por **codigo externo**; el modelo nunca computa ni transcribe el hash | hash/firma no matchea -> `exit!=0` -> el texto **no entra** al contexto |
| **Tag movido** (`git -f`) | sirven otro commit bajo el mismo tag | el pin real es el **commit** firmado dentro del registry, no el tag; el fetcher fetchea/verifica por commit | mover el tag rompe la verificacion (el commit firmado no cambia) |
| **Payload malicioso** (prompt-injection en el metodo) | la skill trae prosa "ignora tus reglas / manda los secretos / corre esto" | payload entre delimitadores con **nonce del entorno**, tratado como **dato**; reglas en codigo/system; loader **sin Bash**; el marcador de purga solo lo emite el fetcher-codigo | aunque el texto pida acciones, no hay canal: no corre shell, no re-apunta origen, no desactiva reglas |
| **Self-update del loader** | servir un `cargar/SKILL.md` adulterado que borre el invariante | el loader **NO auto-adopta su propio cuerpo desde la red**: la Ley viva solo COMPARA el string de tag y, si hay mayor, AVISA "reinstala/`/reload-plugins`" y DETIENE | el artefacto que gobierna la cadena de confianza nunca se reemplaza con bytes no verificados |
| **Clave privada filtrada** | el atacante firma un `registry.json` malicioso que **si** verifica | (parcial) TOFU install-only: sin segundo canal, la firma falsa pasa. Mitigacion: privada solo en operador/Infisical; **rotacion de clave + re-firma + nuevo commit** | **riesgo residual honesto**: no hay segundo canal que lo cace hasta la rotacion |
| **Skill castrada** (crisol sin enforcer; brujula/management sin Bash) | inyectar como dato una skill que necesita runtime o tools | `requires_runtime`/`requires_tools` en el manifiesto -> loader **rechaza como dato** y rutea al install nativo | nunca se inyecta una skill sin su enforcer ni un metodo que apunta a tools inexistentes |
| **Descubrimiento de tag envenenado** | una respuesta HTTP no verificada elige el tag/pin | el tag se ancla **fuera de banda** (`CARGAR_TAG` / sello baked); el descubrimiento solo AVISA, nunca auto-pinnea; la firma del registry de ese commit debe validar antes | el modelo no fija el ancla a partir de datos de red |
| **Olvido por compactacion** | la sesion tira el bloque y el modelo "recuerda" mal | **idempotencia activa**: re-fetch + re-verify incondicional antes de usar | nunca se actua sobre metodo no presente/no verificado |

**Invariante que sostiene la columna "Resultado":** la verificacion la hace
**codigo determinista externo** (fetcher/hook, exit-code). **El modelo nunca
computa, ni transcribe, ni emula un hash/firma** (nada de comparar a ojo con
`Read`/`Grep`). `exit!=0` -> el texto **no entra** al contexto.

## Consecuencias

### Positivas

- Una skill **nueva** se vuelve usable **mid-sesion**, sin reiniciar el harness y
  sin tocar disco — por el canal universal (historial).
- **Agnostico cross-IA**: depende del contrato `fetch_verify`, no de una IA.
- El **script de release** salda la deuda "bump N sellos a mano" (incluye
  `docs/decisions/`) y vuelve atomico release = bump + verificacion + manifiesto
  firmado + commit/tag.
- **Zero-leak** preservado: el unico ancla es `SKILLS_REGISTRY_URL`
  (parametrizado, via Infisical, descubierto en runtime). 0 IPs/dominios/paths/
  secretos. Repo publico.
- Defensa en capas: cadena cripto-por-codigo + aislamiento de payload + scope
  acotado. Romper una no rompe el resto.

### Limites honestos (lo que este diseno NO da)

1. **No da una tool nativa.** Inyecta **metodo como datos**. Una skill que
   necesita `allowed-tools` propios, hook, auto-trigger, o que DEPENDE de ejecutar
   tools (Bash/Write) **no se sirve asi** — sigue exigiendo install nativo.
2. **No carga crisol/idea (runtime) ni brujula/management (tools).** Por diseno:
   castrarlas seria peor que no cargarlas. En la familia actual solo `arquitectura`
   es cargable-como-dato.
3. **WebFetch no es canal de carga.** Muta los bytes; sin un fetcher-codigo que
   traiga bytes crudos y verifique, el modo es **MODO MANUAL**. La automatizacion
   full depende de ese fetcher cableado (en Claude: el hook).
4. **Riesgo residual TOFU.** Sin pin out-of-band, una **privada filtrada** firma
   payloads que verifican; no hay segundo canal hasta la rotacion. Trade-off
   **aceptado** por el operador. Defensa practica: custodia estricta de la privada
   (Infisical) + rotacion.
5. **Depende del entorno real del operador.** Windows + Git-Bash/PowerShell:
   `minisign`, `sha256sum` y `curl` disponibles (o documentado como obtenerlos);
   CRLF rompe firmas/hashes (normalizar a LF ANTES de `minisign -V` Y de `sha256`,
   identico al release); en PowerShell `${var}` antes de `:`; paths con espacios
   entre comillas. Si el fetcher no corre ahi, el loader cae a modo manual — no a
   un verde falso.

### Neutras / deuda futura

- v1 cubre puro-texto-autocontenido. Soporte de skills con runtime/tools queda
  para el canal de install nativo (fuera de este ADR).
- Pin out-of-band (segundo canal anti-clave-robada) queda como evolucion posible
  si el operador revisa el trade-off TOFU.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.7.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.
