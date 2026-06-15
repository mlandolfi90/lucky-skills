#!/usr/bin/env bash
# leak-scan — gate anti-leak pre-push para la familia lucky-skills (repo PUBLICO).
#
# Cubre los artefactos del loader `cargar`, las 5 skills, references, scripts Y los
# meta-docs (ADR docs/decisions/*.md + RUN-LEDGER + mensajes de commit los revisa
# el humano). Leccion v1.7 (4 IPs reales filtradas -> revert + purga de historia) y
# leccion v1.8.0 (re-leak al DOCUMENTAR un fix): por eso el scan corre TAMBIEN sobre
# los meta-docs, no solo el codigo.
#
# Fail-closed: un solo hit con VALOR -> exit 1 -> NO push. El unico ancla legitimo
# es SKILLS_REGISTRY_URL (parametrizado, runtime). El UNICO literal aceptado es el
# slug del propio repo (auto-referencia del sello/Ley viva), cableado en ALLOW_SLUG.
#
# Entorno: Git-Bash/PowerShell en Windows (usa GNU grep + mapfile). Corre sobre el
# arbol staged o todo el repo.
# Uso:  bash scripts/leak-scan.sh            (todo lo versionado)
#       bash scripts/leak-scan.sh --staged   (solo lo que vas a commitear)
set -uo pipefail
export LC_ALL=C   # regex estables, sin sorpresas de locale

# Slug-aceptado: unica auto-referencia legitima (sello + Ley viva). Se excluye SOLO
# de la regla de dominio/owner real; sigue contando un IP o una ruta aunque esten
# cerca del slug. CABLEADO de verdad mas abajo (regla 4).
ALLOW_SLUG='mlandolfi90/lucky-skills'

# Universo de archivos: staged o todo el repo (incluye .md de docs/ADR/ledger).
if [ "${1:-}" = "--staged" ]; then
  mapfile -t FILES < <(git diff --cached --name-only --diff-filter=ACM)
else
  mapfile -t FILES < <(git ls-files)
fi
if [ "${#FILES[@]}" -eq 0 ]; then
  echo "leak-scan: 0 archivos. OK."; exit 0
fi

fail=0
hit(){ printf 'LEAK [%s] %s\n' "$1" "$2" >&2; fail=1; }

for f in "${FILES[@]}"; do
  [ -f "$f" ] || continue
  # binarios fuera (minisign sig, imagenes, etc.): solo texto.
  # el propio escaner contiene los patrones que detecta (regex de vikingo/PRIVATE
  # KEY) -> se excluye a si mismo para no auto-marcarse (estandar en scanners).
  case "$f" in *.sig|*.minisig|*.png|*.jpg|*.jpeg|*.gif|*.zip|*.bin|*.pdf|*.key|*.pub|*leak-scan.sh) continue;; esac

  # ── 1) IPs no-loopback (el leak de v1.7). Excluye loopback, 0.0.0.0, broadcast,
  #      mascaras y versiones vX.Y.Z (sello). ─────────────────────────────────
  if grep -nE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' "$f" 2>/dev/null \
      | grep -vE '127\.0\.0\.1|0\.0\.0\.0|255\.255|\bv?[0-9]+\.[0-9]+\.[0-9]+\b' \
      | grep -q .; then
    hit "IP" "$f"
  fi

  # ── 2) Atribucion prohibida: el nombre de pila del operador NUNCA en prosa.
  #      Es "MLL" en todo artefacto; el handle local del operador jamas. ──────
  if grep -niE '\bvikingo\b' "$f" 2>/dev/null | grep -q .; then
    hit "ATRIBUCION(Vikingo->MLL)" "$f"
  fi

  # ── 3) Rutas absolutas reales de la maquina del operador. ──────────────────
  if grep -nE 'C:\\\\Users\\\\[^\\\\"]+|/home/[A-Za-z0-9_.-]+/|/Users/[A-Za-z0-9_.-]+/' "$f" 2>/dev/null \
      | grep -q .; then
    hit "RUTA-ABSOLUTA" "$f"
  fi

  # ── 4) VALOR de SKILLS_REGISTRY_URL horneado (debe ser solo el NOMBRE de la var,
  #      el token ${SKILLS_REGISTRY_URL}, o un placeholder). Atrapa asignaciones a
  #      http(s)://... o a un IP. Permite el slug-aceptado (ALLOW_SLUG), example.com,
  #      placeholders y la propia referencia a la var. ─────────────────────────
  if grep -nE 'SKILLS_REGISTRY_URL[[:space:]]*[:=][[:space:]]*["'"'"']?(https?://|[0-9]{1,3}\.[0-9])' "$f" 2>/dev/null \
      | grep -vE 'example\.com|<host>|<inyectado|<REDACTED>|github\.com/'"$ALLOW_SLUG"'|raw\.githubusercontent\.com/'"$ALLOW_SLUG"'|\$\{?SKILLS_REGISTRY_URL' \
      | grep -q .; then
    hit "REGISTRY-URL-HORNEADO" "$f"
  fi

  # ── 5) Clave PRIVADA en el arbol (jamas debe entrar al repo). ──────────────
  if grep -nE 'BEGIN (OPENSSH |RSA |EC |DSA |PGP )?PRIVATE KEY|minisign encrypted secret key|untrusted comment: minisign (encrypted )?secret key' "$f" 2>/dev/null \
      | grep -q .; then
    hit "CLAVE-PRIVADA" "$f"
  fi

  # ── 6) Secretos con VALOR: tokens largos / connection strings con pass /
  #      asignaciones de secreto a un literal. Permite placeholders, refs a env
  #      ($VAR / ${VAR} / env:VAR), <REDACTED>, <inyectado>, ejemplos. ─────────
  if grep -niE '(client[_-]?secret|api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|bearer)[[:space:]]*[:=][[:space:]]*["'"'"']?[A-Za-z0-9/+_.=-]{20,}' "$f" 2>/dev/null \
      | grep -vEi '<REDACTED>|<inyectado|<valor|example|placeholder|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|env:[A-Za-z_]|infisical|NOMBRE_|MINISIGN_(SECRET|PASSWORD|PUBKEY)' \
      | grep -q .; then
    hit "SECRETO-CON-VALOR" "$f"
  fi
done

if [ "$fail" -ne 0 ]; then
  echo >&2
  echo "leak-scan: HALLAZGOS. NO pushear hasta limpiar (artefactos + meta-docs)." >&2
  exit 1
fi
echo "leak-scan: LIMPIO (IP / Vikingo / rutas / registry-url / clave-privada / secreto-valor). OK para push."
exit 0
