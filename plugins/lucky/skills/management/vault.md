# Capa SECRETOS (vault)

**Capa base / transversal.** Provee secretos a las otras capas y gestiona su ciclo de vida
(login · **descubrir** · fetch · auditar · rotar · shred). NUNCA imprime valores; nunca los persiste fuera de Infisical.

Las capas `conectar.md` y `operar.md` obtienen sus secretos de acá. Los valores SOLO viven en Infisical
— nunca en git, en una capa ni en el chat.

## Principio rector (LEER PRIMERO)

> **La skill lleva el MÉTODO para ubicarse, no el MAPA de lo que hay.**
> NO asumas la estructura de Infisical (proyectos, entornos, carpetas, nombres). **Descubríla en runtime**
> (§Descubrir). Un mapa hardcodeado se pudre con el primer cambio de infra. Lo único fijo es el **bootstrap mínimo**.

- Los **valores** de secretos viven SOLO en Infisical. Nunca en repos, capas, docs ni chat.
- A las capas se les pasan **nombres** de secreto (ej. `CHISEL_AUTH`), nunca valores.

## Bootstrap mínimo (lo único que el entorno debe proveer)

Las `.env` mínimas de una sesión nueva (y NADA más — el resto se descubre): **ver la tabla en `SKILL.md` §Bootstrap**
(`INFISICAL_CLIENT_ID`/`INFISICAL_CLIENT_SECRET`/`INFISICAL_PROJECT_ID` + opcionales `INFISICAL_API_URL`/`INFISICAL_ENV`).

> **Verificá la inyección PRIMERO** (`test -n "$INFISICAL_CLIENT_ID"` / `if (-not $env:INFISICAL_CLIENT_ID)`):
> si el entorno ya inyecta por `infisical run --env=<env>`, usá eso y no toques disco.
> Lectura desde un archivo es FALLBACK DEPRECATED → en cuanto la inyección funcione, `shred` el archivo (§Rotar/Shred).
> Si caés al fallback, **ruta ABSOLUTA** al archivo (ej. `/opt/bootstrap.env`, no `./...`: `$PWD` cambia tras `cd`).
> NUNCA hardcodear `CLIENT_ID`/`CLIENT_SECRET` en la capa.

## Login (Método A — CLI · recomendado)

```bash
command -v infisical >/dev/null || (curl -1sLf 'https://artifacts-cli.infisical.com/setup.deb.sh' | bash && apt-get install -y infisical)
export INFISICAL_TOKEN=$(infisical login --method=universal-auth \
  --client-id="$INFISICAL_CLIENT_ID" --client-secret="$INFISICAL_CLIENT_SECRET" --silent --plain)
# correr algo con TODO un path inyectado (preferido — no materializa valores sueltos):
infisical run --projectId "$INFISICAL_PROJECT_ID" --env "${INFISICAL_ENV:?descubrí el env}" --path <PATH_DESCUBIERTO> -- <comando>
```

## Login (Método B — REST · fallback PowerShell / sin CLI)

```powershell
$base = ($env:INFISICAL_API_URL) ; if (-not $base) { $base = 'https://app.infisical.com' }
$proj = $env:INFISICAL_PROJECT_ID
$tok  = (Invoke-RestMethod -TimeoutSec 20 -Method Post -Uri "$base/api/v1/auth/universal-auth/login" `
  -ContentType 'application/json' -Body (@{clientId=$env:INFISICAL_CLIENT_ID; clientSecret=$env:INFISICAL_CLIENT_SECRET}|ConvertTo-Json)).accessToken
$h = @{ Authorization = "Bearer $tok" }   # $tok efímero, NUNCA a stdout
```

---

## §Descubrir (el corazón — ubicarse SIN asumir)

**Antes de buscar un secreto, descubrí dónde vivís.** Tres pasos, todo runtime:

```powershell
# 1) ENTORNOS del proyecto (no asumas dev/staging/prod):
$ws = Invoke-RestMethod -TimeoutSec 20 -Uri "$base/api/v1/workspace/$proj" -Headers $h
$ws.workspace.environments | ForEach-Object { "$($_.name)  slug=$($_.slug)" }

# 2a) MAPA para UBICARSE — carpetas + CONTEO de claves (NO vuelques todas las claves):
#     da el panorama sin exponer la topología completa ni abrumar. Esto es lo que se muestra al arrancar.
$envSlug = ($env:INFISICAL_ENV) ; if (-not $envSlug) { $envSlug = $ws.workspace.environments[0].slug }
$all = Invoke-RestMethod -TimeoutSec 30 -Uri "$base/api/v3/secrets/raw?workspaceId=$proj&environment=$envSlug&secretPath=/&recursive=true" -Headers $h
$all.secrets | Group-Object secretPath | ForEach-Object { "{0} ({1} claves)" -f $_.Name, $_.Count }   # SOLO conteo

# 2b) DETALLE de UNA carpeta — BAJO DEMANDA (cuando el usuario pregunta "¿qué hay en X?"):
$all.secrets | Where-Object { $_.secretPath -eq '<PATH>' } | ForEach-Object { $_.secretKey }   # NOMBRES, nunca valores

# 3) BUSCAR un secreto por nombre sin saber su path (cuando no sabés dónde está):
$all.secrets | Where-Object { $_.secretKey -eq 'NOMBRE_QUE_BUSCO' } | ForEach-Object { "está en $($_.secretPath)" }
```
```bash
# equivalentes CLI:
infisical secrets folders --projectId "$INFISICAL_PROJECT_ID" --env "$envSlug" --path /     # carpetas de un nivel
infisical secrets --projectId "$INFISICAL_PROJECT_ID" --env "$envSlug" --recursive          # árbol (key/estado, sin valores en claro)
```

> **Convención observada (NO autoritativa — un servicio por carpeta).** Los despliegues gestionados por
> Coolify suelen vivir en `/<proyecto>/<app>` y el entorno Coolify espeja el de Infisical (dev→Development…).
> Servicios/integraciones transversales suelen ir en `/integrations/<servicio>` o carpetas por área.
> **Esto es un patrón, no una verdad fija: descubrí el árbol real (paso 2) antes de actuar.**

## §Fetch puntual (a variable, jamás a pantalla)

```powershell
# una vez ubicado el path (por descubrimiento), traé el valor a una variable:
$val = (Invoke-RestMethod -TimeoutSec 20 -Uri "$base/api/v3/secrets/raw/NOMBRE?workspaceId=$proj&environment=$envSlug&secretPath=<PATH_DESCUBIERTO>" -Headers $h).secret.secretValue
# NO hacer Write-Output $val. TLS lo valida la CA del sistema.
```
```bash
TOK=$(infisical secrets get NOMBRE --projectId "$INFISICAL_PROJECT_ID" --env "$envSlug" --path <PATH> --plain --silent)
```

## §Rotar / Shred (ciclo de seguridad)

- **Rotar:** actualizar el valor en Infisical (PATCH `/api/v3/secrets/raw/NOMBRE`). Si el secreto se consume
  por un servicio con copia local (ej. un `.env` en el host), actualizar AMBOS y redeployar.
- **Shred:** todo archivo de bootstrap/dump en disco (`Infiscal-bootstrap.txt`, `ALL-SECRETS-*.md`) →
  `shred -u <archivo>` (Linux) · Windows: sobrescribir y borrar, o eliminarlo desde el VPS.
- **Rotar** cualquier credencial que haya transitado el contexto del modelo o un dump.

---

## Ejes

- **CONFIABLE:** la estructura se **descubre** (§Descubrir), nunca se afirma de memoria; bootstrap mínimo es el único ancla; `env`/`projectId` explícitos, jamás hardcode de paths.
- **ESTABLE:** tokens efímeros; `-TimeoutSec`/timeouts en REST; sin estado mutable; funciona en cualquier entorno con solo las `.env` mínimas.
- **SEGURO:** valores solo en Infisical; nunca a stdout/log/git/chat; bootstrap NUNCA embebido en la capa; lectura de disco marcada DEPRECATED → shred; rotación documentada.
