#!/usr/bin/env bash
# maquina-scan — auditor de seguridad de la MÁQUINA (~/.claude): el "AgentShield
# hecho en casa". La capacidad se EXTRAJO de la copia auditada de ECC/AgentShield
# (github.com/affaan-m/ECC, MIT) y se forjó propia — CERO ejecución de paquetes
# de terceros (PIN_TOTAL). Hermano del leak-scan (que audita el REPO público);
# éste audita la CONFIG LOCAL del operador: settings, CLAUDE.md global, hooks
# propios, hooks.json de plugins y configs MCP.
#
# Categorías v1 (100% deterministas, sin juicio LLM):
#   CRITICAL: SECRETO-CON-VALOR · CLAVE-PRIVADA · HOOK-PELIGROSO (curl|sh,
#             base64|sh, eval de red, rm -rf raíz/HOME) · BYPASS-PERMISOS
#   HIGH:     PERMISO-ANCHO (Bash sin acotar / "*") · HOOK-NO-PORTABLE
#             (DRIFT-007 ascendida a regla: ruta Windows horneada o `python`
#             pelado en un command)
#   INFO:     MCP-SUPERFICIE (config MCP presente — revisar a mano)
#
# ZERO-LEAK del reporte: JAMÁS imprime el valor hallado — solo severidad +
# categoría + archivo:línea(s), con paths relativos al dir escaneado.
# Exit: 2 si hay CRITICAL · 1 si hay HIGH (sin CRITICAL) · 0 limpio. Gate-able.
#
# Uso:  bash maquina-scan.sh                       (escanea ~/.claude)
#       MAQUINA_SCAN_DIR=<dir> bash maquina-scan.sh  (override; tests/fixtures)
set -uo pipefail
export LC_ALL=C

DIR="${MAQUINA_SCAN_DIR:-$HOME/.claude}"
[ -d "$DIR" ] || { echo "maquina-scan: no existe $DIR — nada que auditar."; exit 0; }

CRIT=0; HIGH=0; INF=0
rep(){ # sev · categoria · relpath · lineas
  case "$1" in CRITICAL) CRIT=$((CRIT+1)) ;; HIGH) HIGH=$((HIGH+1)) ;; *) INF=$((INF+1)) ;; esac
  printf '  %s · %s · %s%s\n' "$1" "$2" "$3" "${4:+ (línea(s) $4)}"
}
lines_of(){ cut -d: -f1 | tr '\n' ',' | sed 's/,$//'; }

# ── universos por tipo (cada check corre SOLO donde tiene sentido: CLAUDE.md es
#    prosa y puede MENCIONAR patrones peligrosos sin serlos) ────────────────────
CONFIGS=(); PROSAS=(); HOOKSRC=(); HOOKJSON=()
for f in "$DIR"/settings.json "$DIR"/settings.local.json; do [ -f "$f" ] && CONFIGS+=("$f"); done
for f in "$DIR"/CLAUDE.md "$DIR"/.mcp.json "$DIR"/mcp.json; do [ -f "$f" ] && PROSAS+=("$f"); done
while IFS= read -r f; do [ -n "$f" ] && HOOKSRC+=("$f"); done < <(find "$DIR/hooks" -maxdepth 1 -type f \( -name '*.sh' -o -name '*.py' \) 2>/dev/null | sort)
while IFS= read -r f; do [ -n "$f" ] && HOOKJSON+=("$f"); done < <(find "$DIR/plugins" -maxdepth 5 -type f -name 'hooks.json' 2>/dev/null | sort)

relp(){ printf '%s' "${1#"$DIR"/}"; }

# ── 1) SECRETO-CON-VALOR + CLAVE-PRIVADA (mismos patrones del leak-scan) ──────
# En TODO el universo: un secreto con valor no es legítimo en ningún lado.
for f in ${CONFIGS[@]+"${CONFIGS[@]}"} ${PROSAS[@]+"${PROSAS[@]}"} ${HOOKSRC[@]+"${HOOKSRC[@]}"} ${HOOKJSON[@]+"${HOOKJSON[@]}"}; do
  case "$f" in *maquina-scan.sh) continue ;; esac
  # ["']? tras el nombre = comilla de cierre de la CLAVE JSON ("API_KEY": ...);
  # sin ella no se detectaría ningún secreto en settings.json (bug cazado por el fixture).
  L="$(grep -niE '(client[_-]?secret|api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|bearer)["'"'"']?[[:space:]]*[:=][[:space:]]*["'"'"']?[A-Za-z0-9/+_.=-]{20,}' "$f" 2>/dev/null \
      | grep -vEi '<REDACTED>|<inyectado|<valor|example|placeholder|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|env:[A-Za-z_]|infisical|NOMBRE_' | lines_of)"
  [ -n "$L" ] && rep CRITICAL SECRETO-CON-VALOR "$(relp "$f")" "$L"
  L="$(grep -nE 'BEGIN (OPENSSH |RSA |EC |DSA |PGP )?PRIVATE KEY' "$f" 2>/dev/null | lines_of)"
  [ -n "$L" ] && rep CRITICAL CLAVE-PRIVADA "$(relp "$f")" "$L"
done

# ── 2) HOOK-PELIGROSO: SOLO en código de hooks y commands cableados ───────────
for f in ${CONFIGS[@]+"${CONFIGS[@]}"} ${HOOKSRC[@]+"${HOOKSRC[@]}"} ${HOOKJSON[@]+"${HOOKJSON[@]}"}; do
  L="$(grep -nE '(curl|wget)[^|;&]*\|[[:space:]]*(ba)?sh\b|base64[[:space:]]+(-d|--decode)[^|]*\|[[:space:]]*(ba)?sh\b|eval[[:space:]]+["'"'"']?\$\((curl|wget)|rm[[:space:]]+-rf?[[:space:]]+("?/"?|~|\$HOME)([[:space:]"'"'"';]|$)' "$f" 2>/dev/null | lines_of)"
  [ -n "$L" ] && rep CRITICAL HOOK-PELIGROSO "$(relp "$f")" "$L"
done

# ── 3) BYPASS-PERMISOS: solo en configs ejecutables (no prosa) ────────────────
for f in ${CONFIGS[@]+"${CONFIGS[@]}"} ${HOOKJSON[@]+"${HOOKJSON[@]}"}; do
  L="$(grep -nE 'dangerously[-_]?skip[-_]?permissions|bypassPermissions' "$f" 2>/dev/null | lines_of)"
  [ -n "$L" ] && rep CRITICAL BYPASS-PERMISOS "$(relp "$f")" "$L"
done

# ── 4) PERMISO-ANCHO: allowlists sin acotar en settings ───────────────────────
for f in ${CONFIGS[@]+"${CONFIGS[@]}"}; do
  L="$(grep -nE '"Bash\(\*\)"|"Bash\(\*[^)]*\)"|"Bash"[[:space:]]*[,\]]|"\*"[[:space:]]*[,\]]' "$f" 2>/dev/null | lines_of)"
  [ -n "$L" ] && rep HIGH PERMISO-ANCHO "$(relp "$f")" "$L"
done

# ── 5) HOOK-NO-PORTABLE (regla nacida de DRIFT-007): commands con ruta Windows
#      horneada o `python` pelado (el stub de Store / Linux sin `python`) ───────
for f in ${CONFIGS[@]+"${CONFIGS[@]}"} ${HOOKJSON[@]+"${HOOKJSON[@]}"}; do
  L="$(grep -nE '"command"[[:space:]]*:[[:space:]]*"[^"]*([A-Za-z]:\\\\|\bpython[[:space:]])' "$f" 2>/dev/null \
      | grep -vE 'python3|for PY in|command -v' | lines_of)"
  [ -n "$L" ] && rep HIGH HOOK-NO-PORTABLE "$(relp "$f")" "$L"
done

# ── 6) MCP-SUPERFICIE: config presente → revisión humana (informativo) ────────
for f in "$DIR"/.mcp.json "$DIR"/mcp.json; do
  [ -f "$f" ] && grep -q '"mcpServers"' "$f" 2>/dev/null && \
    rep INFO MCP-SUPERFICIE "$(relp "$f")" "" && \
    printf '    → revisá a mano qué servidores MCP hay configurados y si siguen haciendo falta\n'
done

# ── veredicto ──────────────────────────────────────────────────────────────────
echo
if [ "$CRIT" -gt 0 ]; then
  echo "MAQUINA-SCAN: $CRIT CRITICAL · $HIGH HIGH · $INF INFO — HALLAZGOS CRÍTICOS: limpiá antes de seguir."
  exit 2
elif [ "$HIGH" -gt 0 ]; then
  echo "MAQUINA-SCAN: 0 CRITICAL · $HIGH HIGH · $INF INFO — advertencias: revisar."
  exit 1
fi
echo "MAQUINA-SCAN: LIMPIO (secretos / claves / hooks peligrosos / bypass / permisos / portabilidad). $INF INFO."
exit 0
