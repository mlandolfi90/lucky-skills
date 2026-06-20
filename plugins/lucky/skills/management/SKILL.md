---
name: management
description: >-
  Skill unificada de gestión de infraestructura Lucky. Úsala para CUALQUIER tarea de infra de los VPS
  gestionados — (1) ACCESO: conectarse a un VPS, abrir/levantar el túnel Chisel, verificar SSH,
  host-keys o salud del túnel; (2) SECRETOS: necesitar/auditar/rotar/buscar/shred una credencial en
  Infisical (token, clave SSH, password de servicio), saber qué hay cargado o dónde; (3) OPERACIÓN
  Coolify: inventariar/observar estado real (containers, recursos, health), monitorear alarmas,
  desplegar o crear apps, correr tests, dar de alta/alinear servers. Carga progresiva: este índice
  rutea a la capa que la tarea necesite. Las credenciales y datos de infra se DESCUBREN en runtime —
  nunca se hardcodean.
allowed-tools: Bash, Read, Grep, Glob
---

# management

Skill unificada de gestión de la infraestructura Lucky (N VPS + Coolify + Infisical).
Es un **índice de carga progresiva**: este archivo es liviano; el detalle vive en 3 capas que se leen
**solo cuando la tarea las necesita**.

## Principio rector (LEER PRIMERO)

> **La skill lleva el MÉTODO para ubicarse, no el MAPA de lo que hay.**
> Cero IPs, endpoints, paths o nombres de proyecto como verdad fija: todo se **descubre** en runtime
> (Infisical / Coolify). Cualquier dato concreto en las capas está marcado **"snapshot — re-verificar"**.
> El **único** ancla es el bootstrap mínimo de Infisical (abajo).

## Bootstrap mínimo (lo único que el entorno debe proveer)

Las únicas `.env` de una sesión nueva. Solo **nombres** — los valores viven en Infisical, jamás acá.

| Variable | Qué es | ¿Secreto? |
|---|---|---|
| `INFISICAL_CLIENT_ID` | Machine Identity (universal-auth) | sí |
| `INFISICAL_CLIENT_SECRET` | Machine Identity | sí |
| `INFISICAL_PROJECT_ID` | proyecto Infisical (ancla) | no (identificador) |
| `INFISICAL_API_URL` | host de Infisical *(opcional, default `https://app.infisical.com`)* | no |
| `INFISICAL_ENV` | entorno por defecto *(opcional — si falta, se **descubren** los entornos)* | no |

> Nada más: ni IPs, ni endpoints, ni paths, ni nombres de proyecto. El bootstrap NUNCA se embebe en la skill.

## Router — leé SOLO la capa que necesitás

| Tu tarea | Capa | Qué resuelve |
|---|---|---|
| Pedir/auditar/rotar/buscar/shred un secreto; saber qué hay y dónde en Infisical | **vault.md** | login a Infisical, **§Descubrir** estructura, fetch puntual, rotar/shred |
| Conectarse a un VPS, abrir túnel Chisel, verificar SSH/host-keys/salud del túnel | **conectar.md** | deja un canal SSH (Método A directo · Método B túnel Chisel) |
| Inventariar/monitorear/desplegar/crear apps/dar de alta servers en Coolify | **operar.md** | opera la API de Coolify (INIT, inventario, health, deploy, alta de server) |

> **API Coolify:** entra por su **FQDN público + Bearer token** (default, desde cualquier PC); `localhost:8000` es fallback solo dentro del host. SSH es **condicional** (docker crudo / apps remotas). El FQDN se descubre (Infisical o se pide 1 vez), nunca se hardcodea.

**Dependencias (orden de capas: vault → conectar → operar):**
- `vault.md` es la base: `conectar.md` y `operar.md` obtienen sus credenciales de ahí.
- `operar.md` usa la API por FQDN+token; SSH (`conectar.md`) **solo si** hace docker crudo o toca apps remotas.

## §0 — Arranque (lo PRIMERO al cargar esta skill, ACTIVO)

Cuando el usuario carga `management`, NO esperes instrucciones — arrancá:

1. **¿Están las `.env` del bootstrap?** Si faltan, **PEDISELAS al usuario**: los 3
   obligatorios (`INFISICAL_CLIENT_ID`, `INFISICAL_CLIENT_SECRET`,
   `INFISICAL_PROJECT_ID`) — los 2 opcionales solo si los tiene.
2. **Ubicate (mapa, NO el árbol entero)** → `vault.md` §Descubrir: login, listá
   los **entornos** y las **carpetas de primer nivel con conteo de claves**
   (forma del ejemplo: `/<area>/<servicio> (N) · /<area2>/<agente> (M)`). **NO vuelques
   todas las claves** — eso expone la topología completa y abruma. El detalle de una
   carpeta se lista **bajo demanda** ("¿qué hay en /<area>/<servicio>?").
3. **Decile al usuario: "Estás ubicado. ¿Qué hacemos?"** y **ruteá** (tabla
   Router) a la capa que pida: secretos→`vault.md`, acceso→`conectar.md`,
   operar→`operar.md`. `operar.md` entra a Coolify por **FQDN público + token**;
   `conectar.md` (SSH) es **condicional** (solo docker crudo / apps remotas).

## Seguridad (no negociable)

- Valores de secretos **solo** en Infisical: nunca a stdout/log/git/chat. A las capas se les pasan **nombres**.
- Túnel Chisel **siempre** con `--fingerprint` (anti-MITM), descubierto de Infisical.
- Coolify se toca **dentro del host del centro de mando**; confirmación interactiva antes de crear/deployar/alta.
- Claves SSH efímeras → `shred` en teardown.

## Gotchas del entorno operador (ajustar al tuyo)

Este snapshot es de un operador **Windows/PowerShell**; adaptá a tu shell/OS.

- **PowerShell `${var}:`** — antes de un `:` usá `${var}` (`$var:` rompe el parser): `"${url}:8000"`.
- **CRLF → LF** — scripts escritos en Windows fallan en Linux: `sed -i 's/\r$//' file` (o forzá LF al copiar; cuidá el shebang).
- **Windows case-insensitive** — si un repo colisiona (`Foo` vs `foo`), cloná a un nombre **distinto**.
- **`gh` sin scope `delete_repo`** — no podés borrar: desarchivá+renombrá-al-costado, o usá la UI.
- **Crisol** — abrí la entrada `STATUS: ACTIVE` del ledger **antes** del commit de código (el gate evalúa antes; commit+ledger en un solo comando queda bloqueado).

---

> *Procedencia: consolida las ex-skills vault-credenciales, conectar-vps y centro-de-mando (2026-06-11).*

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v1.10.3` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags`), seguir la del repo e informar al humano.
