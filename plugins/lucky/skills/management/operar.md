# Capa OPERACIÓN (Coolify)

**Capa de operación. Coolify = centro de mando.** Inventario, monitoreo, deploy, tests y gestión de servers.
Se apoya en `conectar.md` (acceso) y `vault.md` (token). No reimplementa ninguna de las dos.

## Principio rector (LEER PRIMERO)
> **Descubrí, no asumas.** Servers, proyectos, apps, environments, endpoints y el path del token se
> **descubren** (Coolify API / Infisical), nunca se hardcodean. Lo único fijo es el bootstrap de Infisical
> (ver `vault.md`). Todo dato concreto abajo es **snapshot ilustrativo, NO autoritativo**.

## Contexto (snapshot — verificar en runtime)
- **Acceso a la API (DEFAULT): por su FQDN público + Bearer token, desde CUALQUIER PC.** No requiere SSH.
  El FQDN del centro de mando se **descubre** (Infisical, o se pide 1 vez) — NUNCA se hardcodea.
- **Fallback:** desde *dentro* del host de Coolify, `http://localhost:8000/api/v1`
  (container: `http://host.docker.internal:8000/api/v1`). Útil si el FQDN no resuelve.
- **SSH = CONDICIONAL:** solo para **docker crudo** (inventario ground-truth §1/§2) o apps en **servers remotos**.
  Para tocar la API NO hace falta SSH. *(Snapshot no autoritativo: descubrí el host real, no lo presupongas.)*
- Servers, proyectos y apps: **autodescubrir SIEMPRE** (`$API/servers`, `$API/projects`, `$API/applications`)
  — NUNCA hardcodear cuántos/cuáles ni sus nombres (cambian; proyectos sin sufijos `-vps-*`). Snapshot, no ley.
- ⚠️ La API puede ser **intermitente** (`/servers` devolvió vacío en saneo). Por eso TODA lectura va con **retry+timeout**.

## Prerrequisitos (correr ANTES, en orden)
1. **`vault.md`** → materializa `COOLIFY_TOKEN` **y** el FQDN público de la API (ver INIT abajo).
2. `jq` (el procedimiento lo instala si falta).
3. **`conectar.md` — SOLO SI** vas a hacer docker crudo (§1/§2) o tocar un server remoto. Para la API NO se necesita.
   `SSH` es el **helper de `conectar.md` §Método B** (no un binario): existe solo si sourceaste esa capa en la misma shell.
   Verificá el canal contra el server destino descubierto, sin hardcodear alias:
   `ssh -o BatchMode=yes -o ConnectTimeout=10 root@"$(CURL -H "$AUTH" "$API/servers"|jq -r --arg n "$SERVER_NAME" 'map(select(.name==$n))[0].ip')" true`.

```bash
# ===== INIT — obtener token + FQDN + helpers (corre en cualquier PC; SSH NO requerido) =====
set -euo pipefail
command -v jq >/dev/null || (apt-get update -y && apt-get install -y jq)
# Token desde vault.md (runtime, NUNCA hardcode). DESCUBRÍ el path (no lo asumas):
#   listá el árbol (vault.md §Descubrir) y buscá la carpeta con el token de la API Coolify.
# LEAST PRIVILEGE (token mínimo por tarea — Coolify v4 soporta tokens con permisos):
#   • §1 inventario / §2 monitoreo  → token READ-ONLY  (clave ej. COOLIFY_RO_TOKEN)
#   • §3 deploy / §4 alta de server → token con WRITE/DEPLOY (clave ej. COOLIFY_DEPLOY_TOKEN)
#   • ROOT (COOLIFY_ROOT_API_TOKEN) → SOLO si no existe un token scoped. NO es el default.
# Elegí el nombre de clave según la tarea; no uses root para mirar.
CTOK_KEY="${COOLIFY_TOKEN_KEY:?elegí la clave del token de MENOR privilegio para esta tarea (RO para mirar)}"
CTOK_PATH="${COOLIFY_TOKEN_PATH:?descubrí el path real del token (vault.md §Descubrir)}"   # NO presupongas la carpeta
COOLIFY_TOKEN=$(infisical secrets get "$CTOK_KEY" \
  --projectId "$INFISICAL_PROJECT_ID" --env "${INFISICAL_ENV:?descubrí el env (vault.md §Descubrir)}" --path "$CTOK_PATH" --plain --silent)
: "${COOLIFY_TOKEN:?falta el token — descubrí su path real con vault.md §Descubrir}"
# API: DEFAULT por FQDN público (descubrir COOLIFY_URL de Infisical o pedirlo 1 vez); fallback localhost desde el host.
API="${COOLIFY_API:-${COOLIFY_URL:?descubrí el FQDN público (COOLIFY_URL en Infisical) o usá http://127.0.0.1:8000}/api/v1}"
AUTH="Authorization: Bearer $COOLIFY_TOKEN"
# Reintentos con BACKOFF EXPONENCIAL nativo de curl (sin --retry-delay fijo, que lo desactivaría):
CURL() { curl -fsS --retry 5 --retry-all-errors --retry-max-time 90 --max-time 20 "$@"; }   # API flaky (ESTABLE)
CURL -H "$AUTH" "$API/version"; echo   # sanity — si falla por FQDN, reintentá con API=http://127.0.0.1:8000/api/v1 dentro del host
```
> Cada bloque de abajo asume que ya corriste INIT en la misma sesión (la SSH solo hace falta para docker crudo).

---

## §1 Inventario / observabilidad  · *(API: cualquier PC · docker crudo: por SSH)*

> **Dos fuentes, y su DELTA es lo que importa** (todo autodescubierto, nada fijo):
> 1. **Coolify API** (`$API/servers`, `$API/applications`) = lo que Coolify **gestiona**.
> 2. **docker crudo por SSH** (por cada server descubierto) = ground-truth de TODO lo que corre.
> El **delta (2 − 1)** = lo que aún NO está en Coolify (apps que corren como compose suelto). No lo asumas: calculalo.
> **F5 (SEGURO):** NUNCA vuelques el objeto app completo — `docker_compose`/envs traen **secretos en texto plano**. Seleccioná campos; para descubrir el nombre de un campo usá `jq -r '.[0]|keys[]'` (solo nombres), nunca `jq '.[0]'`.

```bash
# 1) DESCUBRIR (autoritativo — NUNCA hardcodear cuáles/cuántos servers):
CURL -H "$AUTH" "$API/servers"      | jq -r '.[]|"\(.name)\tip=\(.ip)\treach=\(.is_reachable)\tcoolify_host=\(.is_coolify_host)"'
# app→SERVER (join por API): cada app vive en UN server, no necesariamente el host de Coolify.
#   El campo del server varía por versión: probá .destination.server // .server_uuid. Descubrí el nombre del
#   campo con `jq -r '.[0]|keys[]'` (lista SOLO nombres) — JAMÁS `jq '.[0]'` a secas (F5: volcaría docker_compose/envs en claro).
CURL -H "$AUTH" "$API/applications" | jq -r '.[]|{name,status,fqdn,server:(.destination.server // .server_uuid // "?")}'
# 2) Inventario crudo por CADA server DESCUBIERTO (coolify_host=local; el resto=SSH con user/puerto DESCUBIERTOS del API).
#    LF: si editás esta función en Windows, forzá LF antes de enviarla (SKILL.md §Gotchas F2) — el CR rompe `declare -f` en el VPS.
inv() { docker ps -a --format 'table {{.Names}}\t{{.Status}}'; \
  for c in $(docker ps --format '{{.Names}}'); do docker inspect "$c" --format '{{.Name}} st={{.State.Status}} restarts={{.RestartCount}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}n/a{{end}}'; done; \
  uptime|tr -s ' '; free -h|head -2; df -h -x tmpfs -x devtmpfs|sort -k5 -hr|head -5; }
echo "== coolify-host (local) =="; inv
# user/puerto SON campos del server (descubrílos; fallback root/22 marcado snapshot — re-verificá el real en el API):
CURL -H "$AUTH" "$API/servers" | jq -r '.[]|select(.is_coolify_host|not)|select(.is_reachable)|"\(.ip)\t\(.user // "root")\t\(.port // 22)"' | \
while IFS=$'\t' read -r ip user port; do
  echo "== $user@$ip:$port =="; ssh -o BatchMode=yes -o ConnectTimeout=10 -p "$port" "$user@$ip" "$(declare -f inv); inv" 2>&1 || echo "  (sin acceso a $ip — usar conectar.md)"
done
```

## §2 Monitoreo / health + alarmas  · *(FQDN + /version: cualquier PC · health-por-container: docker crudo, requiere `conectar.md`)*
```bash
# health de containers (docker crudo — requiere el helper SSH de conectar.md §Método B; saltealo si estás en una PC sin túnel)
SSH 'docker ps --format "{{.Names}}"|while read c; do h=$(docker inspect "$c" --format "{{if .State.Health}}{{.State.Health.Status}}{{else}}-{{end}}"); [ "$h" != "-" ] && echo "$c health=$h"; done'
# endpoints públicos (cualquier PC) — DESCUBRIR los FQDN reales en runtime (Coolify), NUNCA hardcodear hosts
for u in $(CURL -H "$AUTH" "$API/applications" | jq -r '.[]|select(.fqdn)|.fqdn' | tr ',' '\n' | sed 's/[[:space:]]//g' | grep -E '^https?://'); do
  echo "$u -> $(curl -s -o /dev/null -w '%{http_code}' --max-time 8 "$u/health" 2>/dev/null || echo n/d)"; done
CURL -H "$AUTH" "$API/version"; echo   # salud de la propia API Coolify
```
**Señales de alarma:** container `restarting`/`unhealthy`, `restarts` creciente, disco >85%, endpoint ≠ 2xx/3xx/404 esperado, `/version` sin responder, `is_reachable=false` en un server.

> **ANTES de declarar un dominio "caído", descartá EN ORDEN** (1 línea c/u): (a) mirá el server **REAL** de la app
> (join §1, NO el host de Coolify); (b) router traefik presente (`docker logs traefik|grep <fqdn>`); (c) `DOCKER-USER`/`expose`
> (`ss -ltnp`, `iptables -S DOCKER-USER`). ⚠️ Si un puerto interno no responde **NO asumas que lo bloquea el cloud** —
> Coolify **auto-inserta** reglas `DOCKER-USER`; verificá con `iptables`/`ss` antes de culpar al proveedor.

## §3 Deploy (Coolify) — confirmar antes de escribir  · *(API: cualquier PC)*
Inputs a pedir: `SERVER_NAME` **(OBLIGATORIO** — a qué server va), `PROJECT_NAME`, `APP_NAME`, `GIT_REPO` (público), `GIT_BRANCH`, `BUILD_PACK` (nixpacks|static|dockerfile|dockercompose), `PORT`. Opcional `APP_ENVIRONMENT` (default `production`).

```bash
# (asume INIT ya corrido)
: "${SERVER_NAME:?SERVER_NAME es OBLIGATORIO — a qué server destino va la app}"
# server por NOMBRE (no .[0]: hay >1 server). Capturá is_coolify_host para el PLAN.
SRVJ=$(CURL -H "$AUTH" "$API/servers" | jq -c --arg n "$SERVER_NAME" 'map(select(.name==$n))[0] // empty')
[ -n "$SRVJ" ] || { echo "server '$SERVER_NAME' no encontrado"; exit 1; }
SRV=$(jq -r '.uuid' <<<"$SRVJ"); IS_CH=$(jq -r '.is_coolify_host' <<<"$SRVJ")
# proyecto: reusar o crear (idempotente a nivel PROYECTO)
PROJ=$(CURL -H "$AUTH" "$API/projects" | jq -r --arg n "$PROJECT_NAME" '.[]|select(.name==$n)|.uuid' | head -1)
PROJ_EXISTIA="$PROJ"   # para el PLAN: ¿el proyecto ya existía o lo vamos a crear?
[ -z "$PROJ" ] && PROJ=$(CURL -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d "$(jq -nc --arg n "$PROJECT_NAME" '{name:$n,description:"centro-de-mando"}')" "$API/projects" | jq -r '.uuid')
# idempotencia a nivel APP: matchear por NOMBRE **Y PROYECTO** (no nombre global + head -1: distintos proyectos pueden repetir nombre)
APP=$(CURL -H "$AUTH" "$API/applications" | jq -r --arg n "$APP_NAME" --arg p "$PROJ" \
  '.[]|select(.name==$n)|select((.project_uuid // .environment.project.uuid)==$p)|.uuid' | head -1)
# --- PLAN (dry-run): mostrar TODO lo que va a cambiar ANTES de tocar nada ---
echo "── PLAN ─────────────────────────────────────────"
echo "  server destino    : $SERVER_NAME (is_coolify_host=$IS_CH)"
[ -z "$PROJ_EXISTIA" ] && echo "  + CREAR proyecto  : $PROJECT_NAME" || echo "  = reusar proyecto : $PROJECT_NAME"
if [ -z "$APP" ]; then
  echo "  + CREAR app       : $APP_NAME (repo $GIT_REPO, branch $GIT_BRANCH, pack $BUILD_PACK, port $PORT)"
  echo "  → env             : ${APP_ENVIRONMENT:-production}"
else
  echo "  = app existente   : $APP_NAME → re-deploy del commit actual (no se recrea)"
fi
echo "─────────────────────────────────────────────────"
# --- CONFIRMACIÓN real (crea/deploya recursos en vivo) ---
printf '¿Aplicar este PLAN? (s/n) '
read -r REPLY; [ "$REPLY" = s ] || [ "$REPLY" = S ] || { echo "abortado"; exit 0; }
if [ -z "$APP" ]; then   # crear solo si no existe
  APP=$(CURL -X POST -H "$AUTH" -H "Content-Type: application/json" -d "$(jq -nc \
    --arg p "$PROJ" --arg s "$SRV" --arg r "$GIT_REPO" --arg b "$GIT_BRANCH" --arg bp "$BUILD_PACK" \
    --arg port "$PORT" --arg name "$APP_NAME" --arg envn "${APP_ENVIRONMENT:-production}" \
    '{project_uuid:$p,server_uuid:$s,environment_name:$envn,name:$name,git_repository:$r,git_branch:$b,build_pack:$bp,ports_exposes:$port}')" \
    "$API/applications/public" | jq -r '.uuid')
  [ -n "$APP" ] || { echo "no se creó la app"; exit 1; }
fi
# force: app NUEVA o re-deploy de commit ya construido → force=true (encola un deployment real, evita el falso-OK);
#   si confiás en que el commit cambió, force=false ahorra rebuild. Sin un deployment encolado, el poll confirma el estado PREVIO.
FORCE="${DEPLOY_FORCE:-true}"
CURL -H "$AUTH" "$API/deploy?uuid=$APP&force=$FORCE"; echo
# POLL REAL con DEADLINE + detección de FALLO (no un GET único). F5: seleccioná campos, nunca el objeto entero.
DL=$(( $(date +%s) + 300 ))   # 5 min de techo
while :; do
  ST=$(CURL -H "$AUTH" "$API/applications/$APP" | jq -r '.status'); echo "status=$ST"
  case "$ST" in running*) break;; *fail*|*error*|exited*|*degraded*) echo "DEPLOY FALLÓ: $ST"; exit 1;; esac
  [ "$(date +%s)" -ge "$DL" ] && { echo "TIMEOUT esperando running"; exit 1; }
  sleep 6
done
# VERIFICAR el dominio (reusá el mismo curl que §2): el deploy no terminó hasta que el FQDN responde.
FQDN=$(CURL -H "$AUTH" "$API/applications/$APP" | jq -r '.fqdn // empty' | tr ',' '\n' | grep -E '^https?://' | head -1)
[ -n "$FQDN" ] && echo "$FQDN -> $(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$FQDN" || echo n/d)"
# AUDIT TRAIL: el path DEBE resolver — si no, FALLA ruidoso (la default era una ruta de la PC, huérfana dentro del VPS).
: "${OPS_AUDIT_LOG:?definí el ledger del repo (ruta ABSOLUTA y existente); NO uses una ruta de tu PC dentro del VPS}"
[ -d "$(dirname "$OPS_AUDIT_LOG")" ] || { echo "AUDIT: la carpeta de '$OPS_AUDIT_LOG' no existe — corregí la ruta"; exit 1; }
echo "$(date -u +%FT%TZ) deploy app=$APP_NAME proj=$PROJECT_NAME server=$SERVER_NAME env=${APP_ENVIRONMENT:-production} by=management" >> "$OPS_AUDIT_LOG"
```
> Repos privados: usar el endpoint con GitHub App (otro flujo).
> **Fase posterior (mencionar, no obligatorio):** rollback automático ante fallo + separar el PLAN de la confirmación en dos pasos auditables.

### Reglas apps docker-compose (`BUILD_PACK=dockercompose`) — checklist PRE-deploy
Un único principio: **el container expone su puerto a la red interna de Coolify; traefik (no el host) publica al mundo.**
- **`expose: [<puerto>]`, NUNCA `ports:`** en el compose. `ports:` publica al **host** → fuga que salta el firewall.
- **NO hardcodear `name:` en `networks:`** — 2 instancias comparten la red y **colisionan los alias DNS**. Dejá que Coolify la nombre.
- **Dominio con `:<puerto>`** (ej. `https://<dominio>:<puerto>`, el mismo del `expose`). Sin `:puerto`, Coolify genera
  routers traefik **sin servicio explícito** y traefik **los descarta en silencio** (404 / no enruta, sin error visible).
> Coherencia: `:puerto` en el dominio y `expose:` apuntan al **MISMO** puerto interno del container — no al host. No se contradicen.
> *(Las apps gestionadas por Coolify auto-respaldan sus env-vars vía `secrets-sync`.)*

## §4 Alta / alineación de servers (referencia)
Procedimiento para alinear un VPS bajo Coolify (futuros servers, o re-alta). **Un stack existente (swarm/compose) NO se importa**
(sigue corriendo tal cual); Coolify solo gana visibilidad y puede deployar ahí. *(Snapshot — re-verificar el inventario real con §1.)*

1. Coolify → "Add Server": genera/elige una **SSH key** (pública).
2. En el server (vía `conectar.md`): agregar esa pública a `/root/.ssh/authorized_keys`.
3. Coolify valida la conexión → el server queda **gestionado**.
4. Verificar: `CURL -H "$AUTH" "$API/servers" | jq -r '.[]|{name,ip,is_reachable,is_usable}'` → debe aparecer `is_reachable=true`.
5. **GATE de ENDURECIMIENTO (abajo) — obligatorio antes de declararlo "usable".**
6. **Audit:** `echo "$(date -u +%FT%TZ) alta-server name=<servidor> by=management" >> "$OPS_AUDIT_LOG"` (mismo ledger que §3; ruta absoluta que exista).

### GATE de endurecimiento (correr ANTES de declarar el server "usable")
`is_coolify_host` se deriva del API (paso 4). **Servers remotos: OBLIGATORIO. Host de Coolify: redundante** (Coolify ya gestiona su firewall) — saltealo si `is_coolify_host=true`.
1. **Descubrí el repo/skill del firewall POR ROL, no por path literal** (el path cambia): buscá el rol "firewall del control-plane"
   (ej. tag/marker conocido), no una carpeta fija. Si no aparece, **pará y pedilo** — no improvises reglas.
2. **Red de seguridad ANTES de tocar nada:** `iptables-save > /root/fw.bak` y armá un **dead-man switch** (restore temporizado:
   `at`/`sleep`+`iptables-restore` en background que revierte si NO lo cancelás tras validar). Así un lockout se auto-cura.
3. **audit → dry-run → apply** con el tooling del repo de firewall (no a mano).
4. **Validá desde una PC EXTERNA** (no desde la sesión SSH actual): los puertos que deben estar abiertos lo están y los demás NO.
5. Si todo OK: cancelá el dead-man y **persistí**. Si algo falla: dejá que el dead-man revierta y diagnosticá.
> Reglas concretas, orden de cadenas y restore detallado → **README/ADR del firewall** (no se copian acá; se descubren por rol).

> API alternativa: `POST $API/servers` (ip+puerto+user+private_key_uuid). **Confirmá con el usuario antes** (operación de admin sobre infra en vivo).

---

## Ejes

- **CONFIABLE:** API por **FQDN público + token** (default, cualquier PC; localhost fallback dentro del host); token se **obtiene** en INIT; **servers autodescubiertos** (NUNCA hardcode — escala a N VPS solo); UUIDs se **descubren**; server por **nombre** + `SERVER_NAME` **obligatorio**; app→server **vinculada** por join API; idempotente a nivel proyecto **y app** (match por nombre **+ proyecto**); inventario = **delta** Coolify-vs-docker; **endpoints autodescubiertos** vía `.fqdn`.
- **ESTABLE:** `CURL` con **backoff exponencial** + `--max-time` contra la API intermitente; `set -euo pipefail`; deploy con **poll REAL** (deadline + detección de fallo, no un GET único) + **verificación del FQDN**; antes de "dominio caído" se descarta server-real→traefik→`DOCKER-USER`/`expose` (Coolify auto-inserta `DOCKER-USER`: no culpar al cloud); compose con `expose:`+`:puerto` al MISMO puerto interno.
- **SEGURO:** **least-privilege** (token del MENOR scope; root solo si no hay scoped); token/FQDN solo desde `vault.md` (runtime); **F5: nunca volcar el objeto app** (trae secretos) → seleccionar campos; compose con `expose:` (NUNCA `ports:` → fuga que salta el firewall) y `networks:` sin `name:` fijo; **GATE de endurecimiento** (firewall por rol + dead-man + validar desde afuera) antes de "usable"; **PLAN antes de confirmar** (muestra server+is_coolify_host); **audit trail ruidoso** (falla si la ruta no resuelve).
