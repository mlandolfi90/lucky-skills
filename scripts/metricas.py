#!/usr/bin/env python3
"""metricas — reporte M1-M9 del programa árbol/registros (ADR 0020 §6).

REPORT-ONLY (exit 0 siempre): los gates duros ya viven en la forja (lint,
--check, ruteo). Esto es el tablero numérico del operador — con baseline del
debate 2026-07-16: crisol 562 líneas, ledger monolito 2.536, huérfanos 4+.

Uso: python scripts/metricas.py [--repo <raiz>]
Dependencia: PyYAML.
"""
from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("XX metricas: falta PyYAML.")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_FRONT = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _lineas(p: Path) -> int:
    return p.read_bytes().count(b"\n")


def _exit_de(cmd: list[str], repo: Path) -> str:
    try:
        r = subprocess.run(cmd, cwd=repo, capture_output=True, timeout=300)
        return "VERDE" if r.returncode == 0 else f"ROJO (exit {r.returncode})"
    except Exception as e:
        return f"N/D ({type(e).__name__})"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    repo = Path(ap.parse_args().repo).resolve()
    skills = repo / "plugins" / "lucky" / "skills"
    py = sys.executable or "python"

    print("MÉTRICAS del programa árbol/registros — baseline debate 2026-07-16")
    print("=" * 68)

    # M1 — troncos ≤400 (citación; baseline: crisol 562)
    gordos = [(d.name, _lineas(d / "SKILL.md")) for d in sorted(skills.iterdir())
              if (d / "SKILL.md").is_file() and _lineas(d / "SKILL.md") > 400]
    print(f"M1 troncos>400 (citación): {len(gordos)} " +
          (f"→ {', '.join(f'{n}:{l}' for n, l in gordos)}" if gordos else "· todos ≤400"))

    # M2 — una corrida = un archivo ≤60 líneas de fila (baseline: monolito 2.536)
    runs = repo / "docs" / "refactor" / "_crisol" / "runs"
    largas = []
    total_runs = 0
    for p in sorted(runs.glob("*.md")) if runs.is_dir() else []:
        if p.name.startswith("_archivo"):
            continue
        total_runs += 1
        if _lineas(p) > 60:
            largas.append(f"{p.stem}:{_lineas(p)}")
    print(f"M2 corridas como filas: {total_runs} archivo(s); >60 líneas: {len(largas)}"
          + (f" → {', '.join(largas)}" if largas else ""))

    # M3+M8 — huérfanos y sellos (el lint es la vara)
    print(f"M3/M8 lint (huérfanos+sellos): {_exit_de([py, 'scripts/registros-lint.py'], repo)}")

    # M4 — tokens de arranque: por sesión, no medible desde script
    print("M4 tokens de arranque: N/D desde script (medir por sesión — no se infiere)")

    # M5 — ruteo
    print(f"M5 evals de ruteo: {_exit_de(['bash', 'plugins/lucky/skills/crisol/tests/test-ruteo.sh'], repo)}")

    # M6 — idempotencia de proyecciones
    print(f"M6 idempotencia (--check): {_exit_de([py, 'scripts/proyectar.py', '--check'], repo)}")

    # M7 — paridad del gate
    print(f"M7 paridad gate: {_exit_de(['bash', 'plugins/lucky/skills/crisol/tests/test-paridad.sh'], repo)}")

    # M9 — presupuesto de contexto por activación (tronco + ramas estables)
    print("M9 presupuesto por activación (líneas tronco + ramas estables):")
    for d in sorted(skills.iterdir()):
        t = d / "SKILL.md"
        if not t.is_file():
            continue
        base = _lineas(t)
        extra = 0
        rdir = d / "ramas"
        for p in sorted(rdir.glob("[0-9][0-9][0-9]-*.md")) if rdir.is_dir() else []:
            m = _FRONT.match(p.read_text(encoding="utf-8-sig", errors="replace"))
            fm = yaml.safe_load(m.group(1)) if m else {}
            if isinstance(fm, dict) and str(fm.get("canal", "")).lower() == "estable":
                extra += _lineas(p)
        marca = " ⚠" if base + extra > 500 else ""
        if extra:
            print(f"   {d.name}: {base} + {extra} de ramas = {base + extra}{marca}")
        else:
            print(f"   {d.name}: {base}{marca}")
    print("=" * 68)
    print("(report-only: los gates duros viven en la forja)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
