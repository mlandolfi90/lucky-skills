# Capa 12-FACTOR — reglas transversales (agnósticas)

> Leé esta capa para config, logs, build, deploy, secretos o estado. No son una
> capa del hexágono: son el cómo se sostiene cualquier capa en cualquier
> proyecto. Son **invariantes que el Verificador chequea con sí/no** — valen
> igual en un servicio web, un worker, un CLI o un desktop.

**Eje rector:** *la app es agnóstica del entorno; el entorno la configura desde
afuera.* Cualquier diferencia entre dev, testing y prod va en **config
inyectada**, nunca en el código ni en una rama.

## F-1 · Config por entorno (un solo origen: el entorno)

- Toda config que **varía por entorno** (endpoints, puertos, flags, niveles de
  log, connection strings) entra por **variables de entorno**, no por archivos
  versionados ni `if (entorno == "prod")` en el código.
- En el código viven **nombres** (`DB_URL`, `BROKER_HOST`), nunca **valores**.
  El binario es idéntico en los 3 entornos; lo único que cambia es lo inyectado.
- Regla dura: un valor de entorno (IP, dominio, puerto productivo) hardcodeado
  en el código fuente → `REJECT`. Caso legal único: defaults de **desarrollo
  local** explícitamente marcados (`localhost`, valores ficticios), nunca de
  testing/prod.
- Adaptá al lenguaje (`os.environ` / `process.env` / `getenv()` / config
  provider) — la **fuente** siempre es el entorno.

## F-2 · Secretos: solo nombres en el repo, valores en runtime

- Un secreto es config que además es sensible. Misma regla que F-1 endurecida:
  el repo conoce el **nombre** (`API_KEY`, `DB_PASSWORD`, `<SERVICE_TOKEN>`), el
  **valor** llega en runtime desde el gestor de secretos. **Agnóstico de
  proveedor:** cualquier vault que inyecte por env sirve.
- **Prohibido en el repo:** valores de credenciales, tokens, passwords,
  connection strings con password embebido, ni "nombres con valor" (un nombre
  que filtre topología real). Cero hardcode, cero `.env` con valores commiteado.
- El `.env.example` lista **solo nombres + descripción + si es secreto**, jamás
  valores. Es contrato, no config.
- Inyección **late-binding**: el secreto se resuelve al arrancar el proceso,
  nunca se escribe a disco ni queda en logs/stdout/git/chat.
- Regla dura: artefacto (commit, log, ADR, ledger, captura) con un valor de
  secreto → `FAIL` inmediato. Solo nombres, valores ficticios (`<host>`,
  `example.com`) o `<REDACTED>`.

## F-3 · Build, release, run (tres etapas separadas e inmutables)

- **Build:** código → artefacto. Determinista y **sin secretos** (no se hornean
  credenciales en la imagen).
- **Release:** artefacto **inmutable** + config del entorno destino. El release
  tiene identidad propia (= el **tag**, según Crisol §Versionado).
- **Run:** ejecutar el release tal cual, sin recompilar.
- Regla dura: si para ir a prod hay que **rebuildear** código distinto del que
  pasó testing → `REJECT`. *Se promueve lo que se probó* (Crisol §Versionado le
  da el nombre y la razón).

## F-4 · Procesos sin estado (stateless, descartable)

- Cada proceso es **sin estado** y descartable: nada en memoria local ni en
  disco del proceso sobrevive a un reinicio. El estado vive en un **backing
  service** (DB, cache, cola), enchufable por URL/credencial inyectada.
- Sesión, archivos subidos, jobs en vuelo → backing service, no variable global
  ni `/tmp` del contenedor.
- **Cruce con el hexágono:** el backing service es un **adaptador de salida**
  detrás de un puerto. Cambiar de proveedor = adaptador nuevo, núcleo intacto.
- Regla dura: estado mutable nuevo que asume "el mismo proceso me atiende la
  próxima request" → `REJECT`. Tiene que sobrevivir a `kill -9` + restart.

## F-5 · Logs como streams (el proceso no gestiona su log)

- La app **escribe a stdout/stderr** y se desentiende. No abre archivos de log,
  no rota, no decide destino: eso lo hace el entorno.
- Logs estructurados (línea = evento), **sin secretos ni PII en claro** (cruce
  con F-2: el logger nunca vuelca un token).
- Regla dura: código que escribe a un path de log fijo, rota archivos o asume un
  destino → `REJECT`.

## F-6 · Paridad dev/prod (mismos backing services, gap mínimo)

- Dev, testing y prod usan el **mismo tipo** de backing service (no SQLite en
  dev y Postgres en prod). La diferencia es **config inyectada**, no sustancia.
- **Cruce con Crisol:** *dev es la mesa caliente*, testing/prod NO se tocan a
  mano (son promoción). Eso solo es seguro si hay paridad: si dev difiere en
  sustancia de prod, el Crisol valida en terreno falso.

## Caso legal (estado de proceso vs estado de aplicación)

Apps legítimamente con estado (desktop, jobs largos) NO violan F-4 si el estado
vive en un backing service o se rehidrata al reinicio. Lo que F-4 prohíbe es
estado de **proceso** que se asume persistente entre requests. No generar
`REJECT` espurios: la pregunta es "¿sobrevive a `kill -9` + restart?".

## Hook al Crisol (NO duplicar)

Estas reglas viven acá, no en Crisol. El Arquitecto las consulta al planificar
(¿mete estado en el proceso? ¿hardcodea un valor? ¿hornea un secreto? ¿escribe a
un log fijo?); el Verificador las hace cumplir como `REJECT`/`FAIL` binarios, al
mismo nivel que los criterios de Diseño. Crisol referencia esta capa por nombre,
no copia su cuerpo. Una regla 12-factor nueva se agrega acá sin tocar Crisol.
