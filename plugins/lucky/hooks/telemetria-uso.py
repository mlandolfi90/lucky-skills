#!/usr/bin/env python3
"""telemetria-uso — cuerpo python del hook PostToolUse (ADR 0019 §4).

Lo invoca telemetria-uso.sh con el stdin del hook INTACTO (por eso vive en
archivo propio: un heredoc consumiría el stdin y el JSON jamás llegaría).
Registra la carga de troncos/ramas/skills como JSONL en
$XDG_DATA_HOME/lucky/telemetria/uso.jsonl. FAIL-OPEN: toda excepción → exit 0.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    data = json.loads(sys.stdin.read() or "{}")
    tool = (data.get("tool_name") or "").strip()
    evento = None
    if tool == "Read":
        # Anclado a la ley de lucky (repo `plugins/lucky/skills/` o cache del
        # plugin `.../lucky/skills/`): un path de usuario con forma parecida
        # JAMÁS se loguea (privacidad — hallazgo del design-verifier T3).
        fp = str((data.get("tool_input") or {}).get("file_path", "")).replace("\\", "/")
        m = re.search(r"lucky/skills/([^/]+)/ramas/(\d{3}-[^/]+)\.md$", fp)
        if m:
            evento = {"tipo": "rama", "skill": m.group(1), "rama": m.group(2)}
        else:
            m = re.search(r"lucky/skills/([^/]+)/SKILL\.md$", fp)
            if m:
                evento = {"tipo": "tronco", "skill": m.group(1)}
    elif tool == "Skill":
        sk = str((data.get("tool_input") or {}).get("skill", "")).strip()
        if sk:
            evento = {"tipo": "skill", "skill": sk}
    if evento:
        evento["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        evento["session"] = str(data.get("session_id", ""))[:16]
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        d = Path(base) / "lucky" / "telemetria"
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "uso.jsonl", "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(evento, ensure_ascii=True, sort_keys=True) + "\n")
except Exception:
    pass
sys.exit(0)
