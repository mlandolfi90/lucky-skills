# install-trust.ps1 — empotra la publica minisign del loader `cargar` FUERA del
# repo (ancla TOFU install-only) y fija el estado del install (tag/commit/registry-url)
# que el fetcher lee sin depender del env que el modelo controla. Idempotente, ROTATE.
#
# Uso:
#   pwsh ./install-trust.ps1 -Src "C:\ruta\cargar-release.pub" -Tag v1.9.0 `
#        [-Commit <sha40>] [-RegistryUrl <BASE>] [-Rotate]
#
# RegistryUrl es el unico ancla; si no se pasa, se toma de $env:SKILLS_REGISTRY_URL.
param(
  [Parameter(Mandatory)][string]$Src,
  [Parameter(Mandatory)][string]$Tag,
  [string]$Commit = "",
  [string]$RegistryUrl = $env:SKILLS_REGISTRY_URL,
  [switch]$Rotate
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path $Src)) { throw "No existe: $Src" }
if ([string]::IsNullOrWhiteSpace($RegistryUrl)) {
  throw "Falta el ancla: pasá -RegistryUrl o exportá SKILLS_REGISTRY_URL"
}

$stateDir = Join-Path $env:LOCALAPPDATA 'lucky\cargar'
$trustDir = Join-Path $stateDir 'trust'
$dest     = Join-Path $trustDir 'cargar-release.pub'
$state    = Join-Path $stateDir 'state.env'

$txt = Get-Content -Raw $Src
if ($txt -notmatch '(?m)^untrusted comment:') { throw "No parece una clave minisign." }
if ($txt -notmatch '(?m)^RW')                 { throw "No hallé la linea publica (RW...)." }
if ($txt -match '(?i)secret key')             { throw "¡Esto es una clave PRIVADA! Abortá." }

# CRLF->LF y UTF-8 sin BOM (minisign no tolera BOM ni CR en la publica).
$norm = ($txt -replace "`r`n", "`n")
New-Item -ItemType Directory -Force -Path $trustDir | Out-Null

if ((Test-Path $dest) -and ((Get-Content -Raw $dest) -ne $norm)) {
  if (-not $Rotate) {
    Write-Host "Ya hay una clave anclada DISTINTA. Si es rotacion legitima, agregá -Rotate." -ForegroundColor Yellow
    exit 2
  }
  Copy-Item $dest "$dest.prev.$((Get-Date).ToString('yyyyMMddHHmmss'))"
}
$utf8NoBom = [Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText($dest, $norm, $utf8NoBom)

# Estado del install: LF puro, sin BOM.
$lines = @("SKILLS_REGISTRY_URL=$RegistryUrl", "CARGAR_TAG=$Tag")
if (-not [string]::IsNullOrWhiteSpace($Commit)) { $lines += "CARGAR_COMMIT=$Commit" }
[IO.File]::WriteAllText($state, ($lines -join "`n") + "`n", $utf8NoBom)

Write-Host "Clave publica anclada (TOFU) en: $dest"
(Select-String -Path $dest -Pattern '^untrusted comment:').Line | ForEach-Object { "   $_" }
Write-Host "Estado del install fijado en: $state"
$commitShown = if ([string]::IsNullOrWhiteSpace($Commit)) { "" } else { " commit=$Commit" }
Write-Host "   tag=$Tag$commitShown"
Write-Host "   cotejá el key-id de arriba contra el que anotaste al generar la clave."
