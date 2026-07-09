# install-trust.ps1 — fija el estado del install del loader `cargar` FUERA del
# repo: el PIN (tag/commit/registry-url) que el fetcher lee sin depender del env
# que el modelo controla. Idempotente.
#
# La clave publica minisign YA NO se ancla: la firma fue RETIRADA (ADR 0009,
# dueño unico del repo; vuelve si el trade-off cambia). El ancla de confianza es
# este pin (TAG hoy; COMMIT cuando se fije — v2) + los sha256 del registry,
# verificados por codigo (cargar-fetch-verify.sh).
#
# Uso:
#   pwsh ./install-trust.ps1 -Tag v1.29.0 [-Commit <sha40>] [-RegistryUrl <BASE>]
#
# RegistryUrl es el unico ancla; si no se pasa, se toma de $env:SKILLS_REGISTRY_URL.
param(
  [Parameter(Mandatory)][string]$Tag,
  [string]$Commit = "",
  [string]$RegistryUrl = $env:SKILLS_REGISTRY_URL
)
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RegistryUrl)) {
  throw "Falta el ancla: pasá -RegistryUrl o exportá SKILLS_REGISTRY_URL"
}
if (-not [string]::IsNullOrWhiteSpace($Commit) -and $Commit -notmatch '^[0-9a-f]{40}$') {
  throw "-Commit debe ser un SHA40 hex minúscula (el pin inmutable)."
}

$stateDir = Join-Path $env:LOCALAPPDATA 'lucky\cargar'
$state    = Join-Path $stateDir 'state.env'
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

# Estado del install: LF puro, sin BOM (el fetcher lo parsea linea a linea).
$lines = @("SKILLS_REGISTRY_URL=$RegistryUrl", "CARGAR_TAG=$Tag")
if (-not [string]::IsNullOrWhiteSpace($Commit)) { $lines += "CARGAR_COMMIT=$Commit" }
$utf8NoBom = [Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText($state, ($lines -join "`n") + "`n", $utf8NoBom)

Write-Host "Estado del install (pin) fijado en: $state"
$commitShown = if ([string]::IsNullOrWhiteSpace($Commit)) { "" } else { " commit=$Commit" }
Write-Host "   tag=$Tag$commitShown"
Write-Host "   sin firma: integridad = sha256 contra el registry del pin (ADR 0009)."
