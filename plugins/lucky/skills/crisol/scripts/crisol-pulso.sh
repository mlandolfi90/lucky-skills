#!/usr/bin/env bash
# crisol-pulso — métricas del RUN-LEDGER. Read-only: convierte el archivo
# muerto en instrumento. Si una fuente no se puede leer → N/D, jamás inferir.
set -uo pipefail
L="docs/refactor/_crisol/RUN-LEDGER.md"
[ -f "$L" ] || { echo "N/D — sin ledger ($L)"; exit 0; }

total="$(grep -c '^### ' "$L" || true)"
act="$(grep -c '^- STATUS: ACTIVE' "$L" || true)"
clo="$(grep -c '^- STATUS: CLOSED' "$L" || true)"
esc="$(grep -c '^- STATUS: ESCALATED' "$L" || true)"
fp="$(grep -c '^- Tier: fast-path' "$L" || true)"
co="$(grep -c '^- Tier: completo' "$L" || true)"

echo "📊 PULSO — $L"
echo "  Corridas: $total · ACTIVE: $act · CLOSED: $clo · ESCALATED: $esc"
echo "  Tier: fast-path $fp · completo $co"
echo "  RETROs (fricciones del proceso, últimas 10):"
grep '^- RETRO:' "$L" | tail -10 | sed 's/^/    /' || echo "    (ninguna registrada)"
echo "  → ~3 RETROs sobre la misma regla = corrida Crisol sobre lucky-skills (§6)"
