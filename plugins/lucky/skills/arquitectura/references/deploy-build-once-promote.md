# Patrón de deploy — build-once-promote (CI → `<registry>` → pull del `<paas>`)

> Leé esta capa cuando el cambio toca CI/CD o la infra de despliegue. Es un MAPA
> ADICIONAL de cómo trabajar, descriptivo y reusable — **no** una regla nueva ni
> una modificación del proceso. El SKILL.md y los invariantes de estructura
> mandan; este reference describe un patrón de despliegue concreto, escrito en
> **roles** (`<paas>`, `<registry>`, `<secrets-vault>`, `CI`) para que sirva en
> cualquier stack. Los esqueletos YAML son **ejemplos ilustrativos** con
> placeholders, no plantillas a copiar al pie.
>
> **Cruce con el proceso:** cuando el cambio es de deploy/infra, este patrón se
> gobierna bajo el Crisol §Versionado (promoción-por-tags): *se promueve lo que se
> probó*, el release tiene identidad propia (el tag/sha) y el run ejecuta ese
> artefacto inmutable sin recompilar. Cruza también con 12-factor F-3
> (build≠release≠run) — este doc es el primo "deploy" de esa regla.

## §0 — El problema que resuelve

Deploys del `<paas>` lentos (orden de ~15-40 min en apps grandes). Causa raíz: el
build corría en el `<vps>` (cada deploy = `docker build` en el server, con cache
podado periódicamente y un build server compartido). El costo NO era "compilar":
era **dónde** corría el build. El patrón build-once-promote buildea **una sola
vez** en `CI` y **promueve** la misma imagen; el `<vps>` deja de buildear y solo
pullea una imagen prebuildeada. Resultado típico: deploy de ~100 s (pull en frío)
contra los ~15 min previos.

## §1 — Esquema antes/ahora

ANTES: `git push` → `<paas>` (webhook) → `<vps>`: `docker build` (lento) → `up`
(build server compartido, cache podado).

AHORA: `git push` (rama `dev`) → `CI` job **build** (matrix por servicio; el gate
de test va horneado en el build vía un stage `test` arrastrado por `COPY --from`;
`docker buildx build`+`push` → `<registry>/<owner>/<img>:sha-<commit>`) → `CI` job
**deploy** (`needs: build`; lee `<paas-deploy-token>` del `<secrets-vault>` en
runtime; dispara el deploy por la API del `<paas>`) → `<paas>` (`<vps>`):
`docker compose pull` (NO build); resuelve el sha del commit y lo interpola en
`image: …:sha-${SOURCE_COMMIT}` → pull desde `<registry>` → `up` → healthy.

Clave del patrón: el build vive en `CI` (off-`<vps>`, cache en el `CI`), el
`<vps>` solo pullea, y el disparo lo hace el job de `CI`, no el webhook de push.

## §2 — Piezas y rol

- **`CI`** (p. ej. GitHub Actions): buildea (con el gate de test horneado) y
  pushea al `<registry>`; dispara el deploy.
- **`<registry>`** (p. ej. un registry tipo GHCR): registro de imágenes, con tag
  inmutable `sha-<commit>`.
- **`<paas>`** sobre `<vps>`: solo pullea y levanta, no buildea.
- **`<secrets-vault>`**: único ancla de secretos; el `CI` lee el token en runtime.
- **Docker login del host**: el `config.json` del usuario del host autentica el
  pull privado; el `<paas>` lo consume (file-based, en el host).
- **`<service>` de sync de secretos**: servicio que renueva ese docker login en
  cada host de forma periódica e idempotente.

## §3 — Flujo end-to-end

1. push a la rama `dev`.
2. job **build** del `CI` (matrix por servicio): `buildx build` sin `target` →
   arrastra el stage `test` (gate horneado) vía `COPY --from=test`; `push` →
   `<registry>/<owner>/<img>:sha-<commit>` (sha completo, tag inmutable).
3. job **deploy** (`needs: build` → espera todo el matrix): login al
   `<secrets-vault>` con la identidad `<ci-identity>`; fetch del
   `<paas-deploy-token>` (deploy-only) desde `<secrets-path>`; dispara el deploy
   por la API del `<paas>` (Bearer).
4. el `<paas>` encola: clona `dev`, resuelve `HEAD`→sha, inyecta
   `SOURCE_COMMIT=<sha>`; el compose hace `image: …:sha-${SOURCE_COMMIT}`;
   `docker pull` (host logueado al `<registry>`) + `up`.
5. contenedores healthy en `sha-<commit>`.

Atribución: con auto-deploy **apagado**, el único disparador es el job → el deploy
queda 1:1 con el commit/imagen que produjo el `CI`.

## §4 — Modelo de ramas

- rama `dev` → push → `CI` build+push → deploy al env `dev` (preview en vivo).
- merge a `main` → promover a `testing` (la MISMA imagen `sha-<X>`).
- `git tag` → promover a `production` (la MISMA imagen `sha-<X>`).

`dev` es la rama que el recurso `dev` del `<paas>` trackea. Promoción =
re-deployar la misma imagen `sha-<X>` (no rebuild). Feature: `<branch>/<tarea>` →
merge a `dev`. Para cambios fundacionales de la tubería conviene trabajar directo
en `dev` bajo el proceso.

### Invariante `entorno == @env` (1:1)

El `<env>` de la arquitectura (`dev` / `testing` / `production`) mapea **1:1** al
entorno REAL del recurso en el `<paas>`. El `@env` que el TARGET declara NO es una
etiqueta decorativa: es la afirmación verificable de DÓNDE vive el recurso. El
Crisol contrasta ese `@env` declarado contra el entorno real (regla `TARGET_ENV`)
— declarado y real coinciden, o es mismatch.

- **Auto-crear los 3 entornos al inicializar un proyecto.** Al dar de alta un
  proyecto en el `<paas>`, se crean de entrada los **tres** entornos
  (`dev` / `testing` / `production`), cada uno con su recurso. Así cada `@env`
  declarable tiene un destino real 1:1 desde el día cero y la promoción
  (`dev` → `testing` → `production`) siempre tiene a dónde aterrizar.
- **Trampa del entorno default (documentada).** El `<paas>` típicamente llama
  `production` a su **entorno default** y deja caer ahí cualquier recurso que no
  elija entorno explícito. **ESE default NO es el `<env>` de la arquitectura:** un
  recurso que cayó en el default del `<paas>` puede estar etiquetado `production`
  por el `<paas>` mientras el TARGET lo declara `@dev` → mismatch silencioso.
  **Manda el `@env` declarado:** la verificación contrasta el entorno real contra
  el `@env`, nunca contra el nombre que el `<paas>` le puso a su default.

## §5 — Decisiones clave y por qué

1. **El pull privado se autentica con el docker login del HOST**, no con env-vars
   del `<paas>`. El `<paas>` monta el `config.json` del usuario del server
   read-only en el helper del deploy (el job de deploy del `<paas>` chequea que
   el archivo exista; si falta → pide `docker login`). Una env-var del `<paas>` se
   inyecta DENTRO del contenedor → NO sirve para el pull, que es file-based, en el
   host, ANTES de levantar.
2. **Pin por `sha-${SOURCE_COMMIT}` en el compose** (no env-var manual). El
   `<paas>` resuelve `HEAD`→sha completo e inyecta `SOURCE_COMMIT` en runtime; el
   compose lo interpola como cualquier otra variable. El prefijo `sha-` es
   **literal** en el compose. Ventaja: el token de deploy puede ser deploy-only.
3. **auto-deploy-on-push apagado**; el deploy lo dispara el job de `CI`. Es un flag
   per-recurso (gate de "deployable"); el webhook del `<paas>` lo evalúa por-app,
   así que apagarlo en uno NO toca los demás. Si quedara encendido: el push
   dispararía el deploy ANTES de que el `CI` pushee el sha nuevo → pull-404 (race)
   y atribución contaminada.
4. **El token de deploy vive en el `<secrets-vault>` y se lee en RUNTIME** (no
   hardcodeado). El `CI` usa la identidad `<ci-identity>` (`<vault-client-id>` /
   `<vault-client-secret>` / `<vault-project-id>` como repo-secrets) → lee el
   `<paas-deploy-token>` del `<secrets-path>`. Ese token es deploy-only; para un
   `PATCH` de settings se usa un token ROOT que **no** va al `CI`.
5. **La renovación del docker login del host la hace el `<service>` de sync** (no
   manual). Servicio global, gateado por un `<docker-login-flag>`, que reusa el
   canal seguro del host para hacer `docker login --password-stdin`
   periódicamente. Idempotente, zero-leak (el PAT viaja solo por stdin).

## §6 — Anatomía de artefactos (esqueletos, EJEMPLO ilustrativo)

Los YAML de abajo son ilustrativos, con placeholders. Adaptalos a tu `CI`,
`<registry>` y `<paas>`.

### 6.1 — `<ci-build-workflow>` (p. ej. `.github/workflows/build.yml`)

```yaml
on:
  push: { branches: [dev] }
  workflow_dispatch: {}
permissions: { contents: read, packages: write }
env: { REGISTRY: <registry>, OWNER: <owner> }
jobs:
  build:
    strategy:
      matrix:
        include:
          - { service: <svc>, context: <ctx>, image: <img> }
    steps:
      - uses: <checkout-action>
      - uses: <setup-buildx-action>
      - uses: <registry-login-action>   # token efímero del CI → <registry>
      - uses: <build-push-action>
        with:
          context: ${{ matrix.context }}
          push: true
          tags: ${REGISTRY}/${OWNER}/${{ matrix.image }}:sha-${{ <commit-sha> }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          provenance: false
  deploy:
    needs: build           # espera el matrix entero, no una sola pata
    steps:
      # 1) login al <secrets-vault> (universal-auth) → access token
      # 2) fetch del <paas-deploy-token> (recursive + filtro client-side)
      # 3) GET <paas-api>/deploy?uuid=<paas-resource-uuid>&force=true  (Bearer)
      # NB zero-leak: nunca `set -x`; enmascarar el token ANTES de usarlo;
      #    curl sin -v/--trace; el token nunca en argv ni en outputs.
```

### 6.2 — `<compose-file>` (p. ej. `docker-compose.yml`)

```yaml
services:
  <svc>:
    image: <registry>/<owner>/<img>:sha-${SOURCE_COMMIT}   # sha- LITERAL
    # sin bloque build:  → el <vps> pullea, no buildea
    # healthcheck definido en el Dockerfile
```

### 6.3 — Config del recurso en el `<paas>` (vía API)

`build_pack=dockercompose`, `git_repository`, `git_branch=dev`,
`docker_compose_location`; auto-deploy **apagado** (`<docker-login-flag>` aparte);
SIN env-vars de tag; en el host: `docker login` al `<registry>` (lo mantiene el
`<service>` de sync).

## §7 — Cómo se gobierna con el proceso

Cuando el cambio toca el contrato de deploy + archivos compartidos
(`<compose-file>` / `<ci-build-workflow>`), aplica el tier completo del proceso:

1. **Excavar:** roles read-only en paralelo clavan los unknowns (mecanismo de
   auto-deploy; shape del endpoint probado con token/uuid inválido = respuestas
   401/404 inocuas; resolución empírica de `SOURCE_COMMIT` en un contenedor vivo).
   El trabajo sobre el repo es read-only / en worktree.
2. **Abrir el registro de la corrida** apuntando a `<paas>:<app>@dev`.
3. **Ingeniero:** el líder edita los archivos COMPARTIDOS (compose +
   `<ci-build-workflow>`); no se paralelizan ingenieros sobre compartidos.
4. **Arquitecto/Steward FRESCO** revisa el diff (scope, zero-leak, open/closed,
   footguns del §9).
5. Acciones sobre el `<paas>` = por API, **nunca** por terminal del contenedor.
   Apagar auto-deploy ANTES del push de prueba.
6. **Verificación fiel = el deploy real verde** (oráculo), no los gates estáticos.
   Un auditor FRESCO reúne evidencia propia: imagen corriendo = `sha-<commit>`,
   digest del contenedor == el del `<registry>`, `SOURCE_COMMIT` presente en el
   contenedor, atribución (auto-deploy apagado + job HTTP 2xx único disparador),
   zero-leak en el log del job (token enmascarado), funcional.
7. **Cerrar el registro** + matriz + retro.
8. Higiene post-verde.

Lección: para CI/CD los gates **estáticos** no alcanzan — un "invalid reference
format" o un pull-404 solo emergen al correr. El run/deploy verde es la única
prueba.

## §8 — Runbook: aplicar a una app NUEVA

Precondición global (una vez por host): `docker login` al `<registry>` en el host
+ el `<service>` de sync con ese server en `<docker-login-servers>`. Bajo el
proceso (tier completo), en la rama `dev` del repo de la app:

1. `<ci-build-workflow>`: job **build** (matrix, gate de test horneado, push
   `sha-<commit>`) + job **deploy** (`needs: build`, lee `<paas-deploy-token>` del
   `<secrets-vault>`, dispara el deploy por API). Trigger `push: [dev]` +
   `paths-ignore: [docs/**, **/*.md]`.
2. `<compose-file>`: `image: <registry>/<owner>/<img>:sha-${SOURCE_COMMIT}` sin
   bloque `build:`.
3. Repo-secrets: `<vault-client-id>` / `<vault-client-secret>` /
   `<vault-project-id>` (identidad `<ci-identity>`).
4. `<paas>` (API, token ROOT): recurso `dockercompose` apuntando a `dev`,
   auto-deploy apagado.
5. **Verificación fiel:** apagar auto-deploy → push a `dev` → `CI` verde → job
   deploy HTTP 2xx → contenedores `sha-<commit>` healthy. Un auditor fresco
   confirma. Cerrar el registro.

## §8.1 — Runbook: remediar un mismatch `entorno ≠ @env`

Reusable en cualquier repo (estandarizado o no). Todo en roles `<paas>`/`<env>`,
sin nombres propios. Aplica cuando la brújula flagea, o `TARGET_ENV` falla, o se
detecta que un recurso vive en un entorno distinto al `@env` declarado (caso
típico: cayó en el entorno default del `<paas>`).

1. **Detectar el mismatch.** Confirmar por la API read-only del `<paas>` (o por
   compose-project / puerto / directorio en local) cuál es el entorno REAL del
   recurso y compararlo con el `@env` declarado en el TARGET. Si difieren →
   mismatch confirmado.
2. **Crear los entornos faltantes.** Si el proyecto no tiene los tres entornos
   (`dev` / `testing` / `production`), crearlos (ver §4 "Auto-crear los 3
   entornos"). Sin entorno destino no hay a dónde mover el recurso.
3. **Mover el recurso al entorno correcto.** Reubicar el recurso desde el entorno
   donde cayó (p. ej. el default del `<paas>`) al `<env>` que el `@env` declara.
   Por API / panel del `<paas>`, **nunca** por terminal del contenedor (§9: lo
   in-container se pierde en el redeploy).
4. **Re-verificar.** Volver a contrastar entorno real vs `@env` declarado
   (`TARGET_ENV`): deben coincidir. Recién con la coincidencia confirmada el
   recurso está remediado; registrar el resultado en la corrida.

## §9 — Catálogo de footguns

- Tag de rama con `/` usado como tag de docker → "invalid reference format". Usar
  solo `sha-<commit>`.
- `${SOURCE_COMMIT}` sin el prefijo → pull-404. Escribir `sha-${SOURCE_COMMIT}`.
- auto-deploy encendido → el push dispara el deploy antes del build → pull-404 /
  atribución sucia. Apagarlo y verificar ANTES del push.
- Token equivocado → un token deploy-only da 403 en `PATCH` de settings. Usar
  token ROOT para `PATCH`, deploy-only para el job de deploy.
- `secretPath` explícito en el fetch del vault que da error de validación →
  `recursive=true` + filtrar client-side.
- `needs:` a una sola pata del matrix → usar `needs: build` (el job entero).
- `concurrency cancel-in-progress` top-level → un 2º push cancela el deploy. Un
  push por verificación; grupo de concurrency propio para el deploy.
- Leak del token en logs → sin `set -x`; enmascarar ANTES de usar; `curl` sin
  `-v`/`--trace`; el token nunca en argv ni en outputs del job.
- Push docs-only → rebuild redundante. `paths-ignore: [docs/**, **/*.md]`.
- **Pre-build de REGLA-0 en el `<vps>`** (`scp` del repo + `docker build` local antes del
  push) → redundante con el stage `test` horneado en el build del `CI`, y carga el `<vps>`
  (el build NO vive en el server). El gate-test se hornea en el `CI` (runner Linux); el
  Verificador lo confirma por el stage `test` verde + provenance + e2e propia. Solo caer a
  build fuera del `CI` si se agotan los minutos del `CI` (fallback). Cruza con REGLA 0.
- Pin por tag (no por digest) → un re-push movería el contenido. Pinear por
  `@sha256:` cuando se quiera inmutabilidad fuerte.
- Cambiar algo por la terminal del contenedor → se pierde en el redeploy. Todo
  por API / repo.
- Recurso en el entorno default del `<paas>` sin coincidir con el `@env`
  declarado → mismatch silencioso (el `<paas>` lo etiqueta `production`, el TARGET
  dice `@dev`). Verificar con `TARGET_ENV`; remediar con §8.1 (crear entornos →
  mover el recurso al `<env>` correcto → re-verificar).

## §10 — Endpoints y rutas (roles, no valores)

- **`<registry>`:** `<registry>/<owner>/<img>:sha-<commit>`; listado de tags por
  el endpoint de tags del registry (con el bearer del propio registry).
- **API del `<paas>`** (base `<paas-api>`): listar aplicaciones; leer/`PATCH` una
  aplicación (togglear el flag de auto-deploy); leer/bulk/borrar env-vars;
  `GET /deploy?uuid=<paas-resource-uuid>[&force=true]` → devuelve el id del
  deployment; consultar el estado del deployment. (El flag de auto-deploy puede
  no serializarse en el GET → verificarlo por la herramienta administrativa o la
  UI del `<paas>`.)
- **`<secrets-vault>`:** login universal-auth → access token; leer secretos
  (`recursive=true`, filtrar por path + key client-side). Token ROOT para `PATCH`
  de settings/envs; token deploy-only para disparar el deploy.

## §11 — Estado de referencia

Patrón validado end-to-end en un proyecto piloto del operador: CI → `<registry>`
(push), pull del `<paas>`, y deploy automático disparado por el job, cerrados. La
renovación del login del host la cubre el `<service>` de sync, corriendo y
verificado. Pendiente/parking típico: pin por `@sha256:`; `paths-ignore` de docs;
grupo de concurrency propio para el deploy; roll-out al resto de las apps (cada
una bajo su propia corrida del proceso).

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills`.** Reference de
arquitectura (descriptivo, sin sello): describe un patrón de deploy, no lo dicta.
Patrón validado en un proyecto piloto del operador; se gobierna bajo el Crisol
cuando el cambio toca CI/CD o infra de despliegue.
