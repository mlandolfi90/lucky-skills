# Capa ACCESO (conectar)

**Capa de acceso.** Su única responsabilidad: dejar un canal SSH funcionando hacia los VPS.
No despliega ni opera servicios (eso es `operar.md`). No gestiona secretos (eso es `vault.md`).

## Principio rector (LEER PRIMERO)

> **No asumas IPs, endpoints ni fingerprints. Descubrílos** (de Infisical vía `vault.md`, o del propio
> Coolify vía `operar.md`). Lo único que el entorno provee es el **bootstrap de Infisical** (ver `vault.md`).
> Todo dato de conexión concreto que figure abajo es **snapshot ilustrativo, NO autoritativo** — re-verificá en runtime.

| Concepto | Cómo se obtiene |
|---|---|
| A qué servers conectar | Descubrir: `operar.md` → `GET $API/servers`, o las carpetas de Infisical |
| Endpoint del túnel | Descubrir de Infisical (carpeta del túnel del server) o del FQDN de la app en Coolify |
| Fingerprint del túnel | Descubrir de Infisical (`CHISEL_FINGERPRINT` en la carpeta del agent) — pin anti-MITM |
| Auth del túnel / clave SSH | Descubrir de Infisical (`CHISEL_AUTH`, `VPS_SSH_KEY`) vía `vault.md` |

---

## Método A — SSH directo (entorno con egress libre) · POR DEFECTO si aplica

Para una máquina que sale sin restricción al :22 de los VPS (ej. una PC con la clave y el `~/.ssh/config` ya armados).

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=12 <alias-o-ip-server> "hostname"
```

- Clave privada: la que tenga configurada el entorno (ej. `id_ed25519_<server>`). Si falta, traela de Infisical (`VPS_SSH_KEY`) vía `vault.md`, escribíla efímera (chmod 600), `shred` al terminar.
- **Descubrí los alias/IPs reales** contra `~/.ssh/config`/`known_hosts` o vía Coolify (`operar.md` → `GET $API/servers`). Esta capa no fija nombres de host.
- Scripts/funciones enviados al VPS desde Windows: forzá LF (ver `SKILL.md` §Gotchas F2) o `sed -i 's/\r$//'` antes de ejecutar.

### Verificación de host-key (SEGURO — no negociable)
- Las host-keys se validan contra `~/.ssh/known_hosts`.
- **PC nueva (TOFU bootstrap):** con `BatchMode=yes` la 1ª conexión **falla** (host-key desconocida, no la puede confiar sola). NO la desactives: pineá la key **verificándola contra una fuente independiente** y agregala una vez:
  ```powershell
  ssh-keyscan -t ed25519 <host> | ssh-keygen -lf -   # fingerprint → comparar con fuente de confianza (Coolify/otro VPS), recién ahí >> ~/.ssh/known_hosts
  ```
- **Si una host-key cambió: NO autoconfiar.** Cross-check desde el otro VPS:
  ```powershell
  ssh <otro-host> "ssh-keygen -l -F <host-a-verificar>"
  ```

---

## Método B — Túnel Chisel (sandbox solo-443 / sesión nueva en la nube)

Para entornos que **solo salen por 443** (ej. cloud de Anthropic). Acá NO hay alias ni clave preconfigurada:
**todo se descubre desde Infisical** con solo el bootstrap.

Arquitectura: **un túnel por server** = una app Coolify de túnel (`jpillora/chisel`) por server,
con **key persistente → fingerprint ESTABLE**. `secrets-sync` publica auth/key/fingerprint de cada túnel en su
carpeta de Infisical.

```bash
# 0) login + descubrir (ver vault.md §Descubrir): listá las carpetas con claves CHISEL_*.
#    Cada carpeta de túnel = un server. De ahí salen auth, fingerprint y (si está) endpoint.
#    Si el endpoint no está en Infisical, derivalo del FQDN de la app en Coolify (operar.md).
: "${CHISEL_AUTH:?descubrí de Infisical}"; : "${CHISEL_FP:?descubrí CHISEL_FINGERPRINT de Infisical}"
: "${CHISEL_ENDPOINT:?descubrí el endpoint (Infisical o FQDN Coolify)}"; : "${VPS_SSH_KEY:?descubrí de Infisical}"
LP="${CHISEL_LOCAL_PORT:-2222}"   # un puerto local por túnel si abrís varios a la vez
CHV="${CHISEL_VER:-1.10.1}"   # snapshot — re-verificá la última release estable en github.com/jpillora/chisel/releases
command -v chisel >/dev/null || { case "$(uname -m)" in x86_64) A=amd64;; aarch64|arm64) A=arm64;; *) A=amd64;; esac; \
  curl -fsSL "https://github.com/jpillora/chisel/releases/download/v${CHV}/chisel_${CHV}_linux_${A}.gz" | gunzip > /usr/local/bin/chisel && chmod +x /usr/local/bin/chisel; }
mkdir -p ~/.ssh && chmod 700 ~/.ssh; printf '%s\n' "$VPS_SSH_KEY" > ~/.ssh/vps_key && chmod 600 ~/.ssh/vps_key
chisel client --keepalive 25s --fingerprint "$CHISEL_FP" --auth "$CHISEL_AUTH" \
  "$CHISEL_ENDPOINT" "${LP}:host.docker.internal:22" > /tmp/chisel.log 2>&1 &
echo $! > /tmp/chisel.pid
# readiness FAIL-CLOSED: si el pid de chisel murió, abortá ruidoso (no toques un puerto que quedó libre/secuestrado)
for i in $(seq 1 20); do kill -0 "$(cat /tmp/chisel.pid)" 2>/dev/null || { echo "chisel MURIÓ — ver /tmp/chisel.log"; cat /tmp/chisel.log; exit 1; }; \
  (exec 3<>/dev/tcp/127.0.0.1/$LP) 2>/dev/null && break; sleep 1; done
SSH() { ssh -p "$LP" -i ~/.ssh/vps_key -o StrictHostKeyChecking=accept-new \
  -o UserKnownHostsFile=~/.ssh/known_hosts_tunnel root@127.0.0.1 "$@"; }
SSH hostname   # sanity
```
**Teardown (efímeros, SEGURO):**
```bash
kill "$(cat /tmp/chisel.pid)" 2>/dev/null; shred -u ~/.ssh/vps_key 2>/dev/null || rm -f ~/.ssh/vps_key
```

> **Método, no mapa:** cada carpeta `CHISEL_*` de Infisical = un server (descubrí los paths reales con
> `vault.md` §Descubrir; no se listan nombres ni cantidad acá). Si abrís varios túneles a la vez, usá
> puertos locales distintos (2222 / 2223 / …).

---

## Verificar salud del túnel

```bash
# contra el container del túnel del server (descubrir nombre con docker ps | grep chisel)
# y contra el endpoint público descubierto:
SSH 'docker ps --filter name=chisel --format "{{.Names}} | {{.Status}}"; docker logs $(docker ps --format "{{.Names}}"|grep chisel|head -1) --tail 40 2>&1 | grep -iE "fingerprint|listening|session"'
curl -sS -o /dev/null -w 'tunnel http=%{http_code} tls=%{ssl_verify_result}\n' --max-time 10 "$CHISEL_ENDPOINT/"
```
> Sano = container `Up`/healthy, `listening` en logs, endpoint `http 404 + tls 0` (404 normal sin WS upgrade; tls=0 = cert OK).
> El fingerprint en logs debe **coincidir** con el pineado (estable; si difiere, NO autoconfiar). Logs por **lista-blanca** (solo `fingerprint|listening|session`) — todo lo demás se descarta, no se filtra por lista-negra (SEGURO).

---

## Recuperación ante lockout (te quedaste afuera por el firewall)

Si una regla de firewall te dejó sin SSH (vos o `operar.md` al endurecer un server):
1. **2ª sesión viva PRIMERO:** abrí y conservá una sesión SSH **antes** de cualquier cambio de reglas — es tu vía de rescate si la nueva regla te corta.
2. **Dead-man switch:** todo cambio riesgoso va con restore temporizado (backup de iptables + `at`/`sleep` que revierte solo si no lo confirmás). Bloquearte = esperar el timeout, no perder el server.
3. **Validá desde AFUERA:** confirmá el acceso desde una PC externa **antes** de persistir/confirmar; recién ahí cancelás el dead-man.
4. Las **reglas concretas** (orden DOCKER-USER, restore, dead-man) viven en el **README/ADR del firewall** — descubrílo por su rol en el control-plane (no por path: cambia). Esta capa **linkea**, no reescribe sus reglas.

---

## Ejes

- **CONFIABLE:** datos de conexión (servers, endpoint, fingerprint, auth) se **descubren** en runtime, nunca se afirman de memoria; lo literal está marcado snapshot no-autoritativo; sanity con `hostname`.
- **ESTABLE:** `ConnectTimeout`, `--keepalive 25s`, retry-loop de readiness **fail-closed** (aborta si muere el pid de chisel); fingerprints estables (key persistente) → el pin no se rompe en restarts; un túnel por server (blast-radius acotado); lockout → 2ª sesión + dead-man + validar desde afuera.
- **SEGURO:** `--fingerprint` SIEMPRE (anti-MITM), descubierto de Infisical; host-key TOFU verificada contra fuente independiente y cross-check ante cambios (no autoconfiar); clave efímera con `shred` en teardown; secretos solo vía `vault.md`; logs por lista-blanca.
