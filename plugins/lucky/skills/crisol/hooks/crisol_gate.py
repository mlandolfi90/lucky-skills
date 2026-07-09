#!/usr/bin/env python3
"""crisol_gate.py - PreToolUse hook que enforza el Crisol SOLO sobre código.

Filosofía de diseño (no negociable):
  - FAIL-OPEN: ante CUALQUIER duda, error o excepción -> exit 0 (permitir).
    Un hook global que brickea el Claude Code del usuario seria el colmo de
    la ironia en un sistema anti-defectos. La seguridad primero.
  - OPT-IN POR REPO: en repos que adoptaron el Crisol (existe
    docs/refactor/_crisol/) se exige el ledger completo (STATUS: ACTIVE +
    Tier + Fecha + TARGET).
  - PISO TARGET GLOBAL: en repos git que NO adoptaron el Crisol, la PRIMERA
    edicion de codigo de la sesion bloquea UNA sola vez para forzar la pregunta
    "¿donde corre este codigo?" (el TARGET). Tras declararlo, todo pasa. El piso
    es per (repo, session_id) via un marcador central en ~/.claude/.target-cache.
    Sigue siendo FAIL-OPEN total: cualquier duda -> permitir, jamas trabar.
  - SOLO CODIGO: nunca toca planificacion, lectura, charla, docs ni .md.
    El gate vive en codigo->commit. Jamas en el acto de planificar.

Contrato Claude Code PreToolUse:
  - stdin: JSON con tool_name, tool_input, cwd, session_id, ...
  - exit 0  -> permitir
  - exit 2  -> BLOQUEAR (stderr se devuelve al modelo)
  - cualquier otro no-cero -> error no bloqueante (lo tratamos como permitir)

CLI auxiliar (NO pasa por el gate; el modelo lo corre para desbloquear el piso):
  python crisol_gate.py --register-target "<TARGET>" --session "<sid>" --repo "<repo-root>"
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Windows: cp1252 no imprime acentos/emojis del mensaje de bloqueo -> stderr utf-8.
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Windows: un stdin con bytes UTF-8 crudos no-ASCII (p.ej. una ruta con acentos en
# el JSON) puede fallar el decode y dejar el gate inerte -> reconfigurar utf-8/replace.
# Fail-open si reconfigure no existe (Python viejo) o falla: no brickear jamas.
if hasattr(sys.stdin, "reconfigure"):
    try:
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# POLITICA DE DETECCION DE CODIGO (allow-list, paridad EXACTA con crisol-enforcer.sh:
# _CODE_EXTS + _CODE_FILENAMES): solo esas extensiones/nombres se gatean; TODO lo
# demas (.json, .gitignore, LICENSE, .png, binarios, ...) pasa -- no es codigo->commit.
# Fail-open por defecto: ante duda, permitir. Las dos listas se prueban identicas
# por tests/test-enforcer.sh (extrae CODE_EXTS/CODE_FILENAMES de ambos guardianes).
_CODE_EXTS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".rb",
    ".php", ".c", ".h", ".hpp", ".cpp", ".cc", ".cs", ".sh", ".bash",
    ".ps1", ".psm1", ".sql", ".yaml", ".yml", ".toml",
}
_CODE_FILENAMES = {"dockerfile", "makefile"}

# Segmentos de ruta / sufijos que NUNCA se gatean (planes, docs, config Claude).
_EXCLUDED_DIR_SEGMENTS = {".git", ".claude"}
_EXCLUDED_SUFFIXES = {".md", ".mdx", ".markdown", ".txt", ".rst"}

# Valores que NO cuentan como TARGET declarado (placeholder = no respondio).
_TARGET_PLACEHOLDERS = {"pendiente", "tbd", "n/d", "na", "<...>", "?"}

# Perfiles del guardian (ADR 0011): estricto = hoy; aviso = mismo diagnostico
# pero SIN bloquear (el mensaje llega, la tool-call pasa); off = inerte.
_GATE_PROFILES = {"estricto", "aviso", "off"}


def _gate_profile() -> str:
    """env CRISOL_GATE_PROFILE -> estricto|aviso|off; invalido/vacio -> estricto.

    Parseo CANONICO espejo de crisol-enforcer.sh:_gate_profile (paridad probada
    por test-enforcer.sh Grupo K): trim de whitespace ASCII de bordes + lower;
    cualquier valor fuera del enum (basura, unicode-ws, mayusculas raras) cae a
    'estricto' — FAIL-CLOSED A DUREZA: un perfil mal tipeado jamas afloja."""
    v = os.environ.get("CRISOL_GATE_PROFILE", "").strip(" \t\n\r\x0b\x0c").lower()
    return v if v in _GATE_PROFILES else "estricto"

# ATOMICIDAD (SRP): aviso NO bloqueante cuando un archivo de codigo supera el
# umbral T de lineas. Es una CITACION al juicio, no un veredicto ni un bloqueo:
# el gate no puede juzgar SRP (eso es un LLM), solo nudgea a mirar. Paridad EXACTA
# con crisol-enforcer.sh (mismo umbral, mismo mensaje) — probada por test-enforcer.sh.
# Umbral: env CRISOL_ATOMICIDAD_T -> docs/refactor/_crisol/atomicidad.conf -> 400.
_ATOMICIDAD_DEFAULT_T = 400
_ATOMICIDAD_MSG = (
    "[CRISOL-ATOMICIDAD] {f}: {n} lineas (umbral {t}) - SRP: parti antes de "
    "extender; citacion al juez, no bloqueo. Ajusta el umbral por chat -> "
    "docs/refactor/_crisol/atomicidad.conf"
)


def _as_int_or_none(s: str):
    """Token entero ASCII tras trim de bordes. Regla de parseo CANONICA que espeja
    crisol-enforcer.sh (_trim + _is_digits + base-10): 'trim, luego TODO el token es
    [0-9]'. Rechaza espacios internos, basura ('200abc'), decimales, unicode-digit;
    normaliza a decimal ('007' -> 7). None si no aplica -> el caller cae al siguiente."""
    s = s.strip(" \t\n\r\x0b\x0c")  # SOLO whitespace ASCII: paridad con bash `[[:space:]]`
    if s and s.isascii() and s.isdigit():  # (NBSP/EM-SPACE u otro Unicode-WS NO se trima → rechaza)
        return int(s)
    return None


def _atomicidad_threshold(repo: Path) -> int:
    """env CRISOL_ATOMICIDAD_T -> atomicidad.conf (1ra línea entera-dígito) -> 400.
    Parseo CANONICO (_as_int_or_none), byte-por-comportamiento con el enforcer;
    test-enforcer.sh Grupo I (I5) prueba la paridad bajo config malformada."""
    v = _as_int_or_none(os.environ.get("CRISOL_ATOMICIDAD_T", ""))
    if v is not None:
        return v
    try:
        conf = repo / "docs" / "refactor" / "_crisol" / "atomicidad.conf"
        if conf.is_file():
            for line in conf.read_text(encoding="utf-8", errors="replace").splitlines():
                v = _as_int_or_none(line)
                if v is not None:
                    return v
    except Exception:
        pass
    return _ATOMICIDAD_DEFAULT_T


def _emit_atomicidad_advisory(raw_fp: str, abs_p: Path, repo: Path) -> None:
    """Aviso a stderr si el archivo de codigo ya tiene >= T lineas. NUNCA bloquea.

    Cuenta newlines (== `wc -l`) para paridad exacta con el enforcer bash.
    Fail-open total: cualquier excepcion -> no emite (jamas rompe el gate).
    """
    try:
        if not abs_p.is_file():
            return
        t = _atomicidad_threshold(repo)
        n = abs_p.read_bytes().count(b"\n")
        if n >= t:
            sys.stderr.write(_ATOMICIDAD_MSG.format(f=raw_fp, n=n, t=t) + "\n")
            sys.stderr.flush()
    except Exception:
        pass


def _allow() -> None:
    sys.exit(0)


def _block(msg: str) -> None:
    # Perfil 'aviso' (ADR 0011): el diagnostico completo llega a stderr con un
    # marcador inequivoco, pero la tool-call PASA. Paridad con el enforcer.
    if _gate_profile() == "aviso":
        sys.stderr.write(
            "[CRISOL-AVISO] (modo aviso: NO bloqueado — el perfil estricto habria bloqueado)\n" + msg
        )
        sys.stderr.flush()
        sys.exit(0)
    sys.stderr.write(msg)
    sys.stderr.flush()
    sys.exit(2)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(repo: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, timeout=8,
        )
        if out.returncode != 0:
            return None
        return out.stdout.strip()
    except Exception:
        return None


def _find_repo_root(start: Path) -> Path | None:
    cur = start if start.is_dir() else start.parent
    for _ in range(40):
        if (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def _is_excluded_path(rel_parts: tuple[str, ...], name: str) -> bool:
    lower_parts = {p.lower() for p in rel_parts}
    if lower_parts & _EXCLUDED_DIR_SEGMENTS:
        return True
    # Todo lo que vive bajo docs/ (incluye ADRs, _crisol, ARCHITECTURE.md).
    if rel_parts and rel_parts[0].lower() == "docs":
        return True
    suffix = Path(name).suffix.lower()
    if suffix in _EXCLUDED_SUFFIXES:
        return True
    return False


def _is_code_file(name: str) -> bool:
    n = name.lower()
    if n in _CODE_FILENAMES:
        return True
    return Path(n).suffix in _CODE_EXTS


def _target_is_declared(raw_val: str) -> bool:
    """True si el valor de TARGET es una respuesta real (no vacio/placeholder)."""
    val = raw_val.strip()
    if not val:
        return False
    if val.startswith("<"):
        return False
    if val.lower() in _TARGET_PLACEHOLDERS:
        return False
    return True


# ── CAMBIO A: estado del ledger para repos adoptados ────────────────────────────
def _ledger_state(repo: Path, branch: str) -> str:
    """'ACTIVE_OK' | 'ACTIVE_NO_TARGET' | 'NONE' para el branch.

    ACTIVE_OK         -> hay bloque ACTIVE valido (legado, o ###+Tier+Fecha+TARGET).
    ACTIVE_NO_TARGET  -> hay bloque ### ACTIVE con Tier+Fecha pero SIN TARGET real.
    NONE              -> no hay ACTIVE utilizable para el branch.
    Fail-open: si el ledger no se puede leer -> 'ACTIVE_OK' (no bloquear).
    TARGET solo se exige en el formato estricto '###'; el legado '## RUN' (pre-v1.0.0)
    no lo exige -> no re-bloquea historia.
    """
    ledger = repo / "docs" / "refactor" / "_crisol" / "RUN-LEDGER.md"
    if not ledger.is_file():
        return "NONE"
    try:
        text = ledger.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return "ACTIVE_OK"  # fail-open: no podemos leer -> no bloqueamos

    block_status = None
    block_branch = None
    block_strict = False
    block_tier = False
    block_fecha = False
    block_target = False
    seen_active_no_target = False

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## RUN "):
            block_status, block_branch = None, None
            block_strict, block_tier, block_fecha, block_target = False, False, False, False
            continue
        if line.startswith("### "):
            block_status = None
            block_strict, block_tier, block_fecha, block_target = True, False, False, False
            head = line[4:].strip()
            for sep in (" — ", " - "):
                if sep in head:
                    head = head.split(sep, 1)[0].strip()
                    break
            block_branch = head or None
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        if line.upper().startswith("STATUS:"):
            block_status = line.split(":", 1)[1].strip().upper()
        elif line.startswith("Branch:"):
            block_branch = line.split(":", 1)[1].strip()
        elif line.startswith("Tier:"):
            block_tier = True
        elif line.startswith("Fecha:"):
            block_fecha = True
        elif line.upper().startswith("TARGET:"):
            if _target_is_declared(line.split(":", 1)[1]):
                block_target = True

        if block_status == "ACTIVE" and block_branch == branch:
            if not block_strict:
                return "ACTIVE_OK"  # legado: no exige TARGET
            if block_tier and block_fecha and block_target:
                return "ACTIVE_OK"
            if block_tier and block_fecha and not block_target:
                seen_active_no_target = True

    return "ACTIVE_NO_TARGET" if seen_active_no_target else "NONE"


# ── CAMBIO COBERTURA: gate de la matriz de veredictos en el commit de cierre ─────
def _coverage_state(repo: Path, branch: str) -> str:
    """'WIP' | 'CLOSING_OK' | 'CLOSING_INCOMPLETE' para la entrada ACTIVE del branch.

    Espejo de _ledger_state: parsea la entrada ACTIVE del branch en RUN-LEDGER.md,
    ubica SU bloque <!-- VEREDICTOS:BEGIN -->..<!-- VEREDICTOS:END -->, lee
    `runState` y las lineas `- [V] <ID> · <VEREDICTO> · ...`.

    Devuelve:
      WIP                 -> runState != closing (o ausente) -> PERMITE (iteracion
                             en curso; los WIP-commits no se rompen).
      CLOSING_OK          -> runState: closing ∧ >=1 linea [V] ∧ TODA linea [V] con
                             veredicto ∈ {PASS, N/A} (case-insensitive) -> PERMITE.
      CLOSING_INCOMPLETE  -> runState: closing ∧ (bloque vacio/ausente OR alguna
                             linea [V] con veredicto ∉ {PASS, N/A}) -> BLOQUEA.

    Gramatica TRIVIAL (condicion 4): green ⟺ veredicto ∈ {PASS, N/A}; cualquier otra
    cosa (FAIL, PENDIENTE, vacio, lo que sea) NO es green. Una matriz `closing`
    vacia-pero-presente -> CLOSING_INCOMPLETE (NO fail-open: ausente=skip se bloquea).

    Fail-open ESTRICTO al borde acotado: ledger ausente/ilegible o cualquier
    excepcion de parseo -> 'WIP' (PERMITE). Solo `runState: closing` con matriz
    realmente incompleta/roja bloquea (condicion 4: ilegible=bug NO brickea).
    """
    ledger = repo / "docs" / "refactor" / "_crisol" / "RUN-LEDGER.md"
    if not ledger.is_file():
        return "WIP"  # fail-open: sin ledger no hay cierre que gatear
    try:
        text = ledger.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return "WIP"  # fail-open: ilegible=bug, no brickear

    in_active = False        # estamos dentro de la entrada ACTIVE de ESTE branch
    block_status = None
    block_branch = None
    in_veredictos = False    # estamos entre BEGIN..END del bloque de la entrada ACTIVE
    run_state = None
    seen_v = False
    all_green = True

    GREEN = {"pass", "n/a"}

    try:
        for raw in text.splitlines():
            stripped = raw.strip()

            # Limites de entrada: un nuevo encabezado cierra la entrada previa.
            if stripped.startswith("## RUN "):
                if in_active:
                    break  # ya recorrimos toda la entrada ACTIVE
                in_active = False
                block_status, block_branch = None, None
                continue
            if stripped.startswith("### "):
                if in_active:
                    break  # nueva entrada -> la ACTIVE ya termino
                block_status = None
                head = stripped[4:].strip()
                for sep in (" — ", " - "):
                    if sep in head:
                        head = head.split(sep, 1)[0].strip()
                        break
                block_branch = head or None
                continue

            field = stripped[2:].strip() if stripped.startswith("- ") else stripped
            if field.upper().startswith("STATUS:"):
                block_status = field.split(":", 1)[1].strip().upper()
                if block_status == "ACTIVE" and block_branch == branch:
                    in_active = True
                continue

            # Solo nos interesan las lineas DENTRO de la entrada ACTIVE del branch.
            if not in_active:
                continue

            if stripped == "<!-- VEREDICTOS:BEGIN -->":
                in_veredictos = True
                continue
            if stripped == "<!-- VEREDICTOS:END -->":
                in_veredictos = False
                continue
            if not in_veredictos:
                continue

            # Dentro del bloque VEREDICTOS de la entrada ACTIVE.
            if field.lower().startswith("runstate:"):
                run_state = field.split(":", 1)[1].strip().lower()
                continue
            if field.startswith("[V]"):
                seen_v = True
                parts = field.split("·")  # separador ` · `
                verdict = parts[1].strip().lower() if len(parts) >= 2 else ""
                if verdict not in GREEN:
                    all_green = False
    except Exception:
        return "WIP"  # fail-open: cualquier sorpresa de parseo no brickea

    if run_state != "closing":
        return "WIP"  # wip (o sin runState) -> permite
    # runState: closing -> exigir matriz completa+verde.
    if seen_v and all_green:
        return "CLOSING_OK"
    return "CLOSING_INCOMPLETE"  # bloque vacio/ausente OR alguna linea no-green


def _staged_has_code(repo: Path) -> bool:
    """Para `git commit`: True si ALGUN archivo staged es codigo fuente."""
    names = _git(repo, "diff", "--cached", "--name-only")
    if not names:
        return False
    for n in names.splitlines():
        n = n.strip()
        if not n:
            continue
        parts = tuple(Path(n).parts)
        if _is_excluded_path(parts, Path(n).name):
            continue
        if _is_code_file(Path(n).name):
            return True
    return False


# ── CAMBIO B: piso TARGET global (marcador per repo+sesion) ─────────────────────
def _cache_dir() -> Path:
    override = os.environ.get("CRISOL_TARGET_CACHE_DIR")
    if override and override.strip():
        return Path(override)
    return Path.home() / ".claude" / ".target-cache"


def _norm_repo(p) -> str:
    return str(Path(p).resolve()).replace("\\", "/").lower()


def _marker_path(repo_norm: str, sid: str) -> Path:
    key = hashlib.sha256((repo_norm + "\x00" + sid).encode("utf-8")).hexdigest()[:32]
    return _cache_dir() / (key + ".json")


def _piso_b(target_path, is_commit, repo: Path, data: dict) -> None:
    """Piso TARGET para repos NO adoptados. Bloquea UNA vez por (repo, sesion).

    FAIL-OPEN: cualquier rama incierta -> _allow(). El unico exit 2 exige:
    sid valido ∧ Edit/Write/MultiEdit ∧ archivo de codigo ∧ marcador inexistente
    ∧ marcador recien escrito con exito. Orden: escribir-marcador, LUEGO bloquear.
    """
    if is_commit:
        _allow(); return                 # FO-15: commit en no-adoptado pasa libre
    if target_path is None:
        _allow(); return
    sid = data.get("session_id")
    if not isinstance(sid, str) or not sid.strip():
        _allow(); return                 # FO-11: sin session_id no hay piso posible
    sid = sid.strip()
    try:
        repo_norm = _norm_repo(repo)
        marker = _marker_path(repo_norm, sid)
    except Exception:
        _allow(); return                 # FO-12
    try:
        if marker.exists():
            _allow(); return             # FO-13: presencia (no contenido) = ya respondio
    except Exception:
        _allow(); return
    # No existe marcador -> escribir PRIMERO (garantiza desbloqueo), bloquear DESPUES.
    tmp = None
    try:
        cache = marker.parent
        cache.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({
            "target": "(pendiente-de-registrar)", "repo": repo_norm,
            "session_id": sid, "ts": _utc_now(), "schema": "target-cache@1",
        }, ensure_ascii=True)
        tmp = cache / (marker.name + "." + str(os.getpid()) + ".tmp")
        tmp.write_text(payload, encoding="utf-8")
        os.replace(str(tmp), str(marker))
    except Exception:
        if tmp is not None:
            try:
                tmp.unlink()
            except Exception:
                pass
        _allow(); return                 # FO-14: no puedo persistir -> no bloqueo
    _block(MENSAJE_B.format(
        repo=repo, session_id=sid, script_path=os.path.abspath(__file__)))


def _handle_register(argv) -> None:
    """CLI: registra el TARGET real declarado por el humano. Jamas falla ruidoso."""
    try:
        target = sid = repo = None
        i = 0
        while i < len(argv):
            a = argv[i]
            if a == "--register-target" and i + 1 < len(argv):
                target = argv[i + 1]; i += 2; continue
            if a == "--session" and i + 1 < len(argv):
                sid = argv[i + 1]; i += 2; continue
            if a == "--repo" and i + 1 < len(argv):
                repo = argv[i + 1]; i += 2; continue
            i += 1
        if not (sid and sid.strip() and repo):
            print("OK (nada que registrar: faltan --session/--repo)")
            sys.exit(0)
        repo_norm = _norm_repo(repo)
        marker = _marker_path(repo_norm, sid.strip())
        cache = marker.parent
        cache.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({
            "target": (target or "").strip() or "(sin-valor)",
            "repo": repo_norm, "session_id": sid.strip(),
            "ts": _utc_now(), "schema": "target-cache@1",
        }, ensure_ascii=True)
        tmp = cache / (marker.name + "." + str(os.getpid()) + ".tmp")
        tmp.write_text(payload, encoding="utf-8")
        os.replace(str(tmp), str(marker))
        print("OK TARGET registrado -> " + str(marker))
    except Exception:
        print("OK (no se pudo persistir el marcador, pero no bloqueo nada)")
    sys.exit(0)


# ── mensajes de bloqueo ─────────────────────────────────────────────────────────
MENSAJE_A = (
    "\n[CRISOL] BLOQUEADO: la corrida ACTIVE no declara TARGET (donde corre/verifica).\n"
    "  Repo: {repo}\n  Branch: {branch}\n"
    "  El bloque ACTIVE en docs/refactor/_crisol/RUN-LEDGER.md no tiene el campo\n"
    "  TARGET (o esta vacio/placeholder). Codear sin TARGET = verificar a ciegas.\n\n"
    "  PREGUNTALE AL HUMANO donde corre este codigo. No lo asumas. Esquema:\n"
    "    - TARGET: paas:<proyecto>/<app>@<env>   (env in dev|testing|production; dev=default)\n"
    "    - TARGET: docker-local                  (contenedor Linux fiel)\n"
    "    - TARGET: pc-local                      (esta PC) -- SOLO si el humano lo pide\n\n"
    "  pc-local NUNCA es el default. Target ambiguo -> preguntar, jamas asumir local.\n"
    "  Que hacer: agrega  - TARGET: <valor real>  al bloque ACTIVE y reintenta.\n"
)

MENSAJE_NO_ACTIVE = (
    "\n[CRISOL] BLOQUEADO: este cambio de codigo no paso por el Crisol.\n"
    "  Repo: {repo}\n  Branch: {branch}\n"
    "  No hay entrada 'STATUS: ACTIVE' (con Tier + Fecha + TARGET) para este branch\n"
    "  en docs/refactor/_crisol/RUN-LEDGER.md.\n\n"
    "  Que hacer:\n"
    "   1) Corre la skill: /crisol  (abre la corrida y el ledger), o\n"
    "   2) Si es un cambio legitimo fuera de flujo, abri manualmente una entrada\n"
    "      ACTIVE (con Tier, Fecha y TARGET) en RUN-LEDGER.md para este branch.\n\n"
    "  (El gate solo aplica a codigo fuente. Planificar, leer y editar docs/.md\n"
    "   NUNCA se bloquea.)\n"
)

MENSAJE_B = (
    "\n[CRISOL - PISO] BLOQUEADO (una sola vez en esta sesion).\n"
    "  Repo: {repo}\n"
    "  Vas a EDITAR CODIGO en un repo que NO declaro donde corre. Antes de tocar\n"
    "  una linea hay que saber el TARGET: donde corre y se verifica este codigo.\n\n"
    "  >> PREGUNTALE AL HUMANO: \"¿Donde corre este codigo?\" <<\n"
    "  NO lo asumas. NO asumas que es esta PC. El default de desarrollo es un VPS\n"
    "  Linux remoto, no Windows.\n\n"
    "  Esquema del TARGET (elegi UNO, te lo dice el humano):\n"
    "    paas:<proyecto>/<app>@<env>   env in dev|testing|production ; dev = default\n"
    "    docker-local                  contenedor Linux fiel en esta maquina\n"
    "    pc-local                      ESTA PC -- SOLO si el humano lo pide EXPLICITO\n\n"
    "  pc-local NUNCA es el default. Si el target es ambiguo o no lo sabes:\n"
    "  PREGUNTA y espera. Jamas degrades a local en silencio.\n\n"
    "  Cuando el humano confirme el TARGET, registralo asi (UNA tool-call Bash) y reintenta:\n"
    "    for PY in python3 python; do \"$PY\" -c \"\" >/dev/null 2>&1 && break; done; \\\n"
    "      \"$PY\" \"{script_path}\" --register-target \"<TARGET>\" --session \"{session_id}\" --repo \"{repo}\"\n\n"
    "  Eso desbloquea TODAS las ediciones de codigo de esta sesion en este repo.\n"
    "  (Piso liviano: bloquea una vez para forzar la pregunta. No vuelve a molestar\n"
    "   en esta sesion. Editar docs/.md o planificar nunca se bloquea.)\n"
)

MENSAJE_COBERTURA = (
    "\n[CRISOL - COBERTURA] BLOQUEADO: el commit de cierre exige la matriz de veredictos COMPLETA y VERDE.\n"
    "  Repo: {repo}\n  Branch: {branch}\n"
    "  La entrada ACTIVE declara `runState: closing` (commit de cierre), pero su\n"
    "  bloque <!-- VEREDICTOS:BEGIN -->..<!-- VEREDICTOS:END --> esta vacio/ausente\n"
    "  o tiene alguna regla SIN veredicto verde (PENDIENTE, FAIL, o vacio).\n\n"
    "  Esto NO es el primer detector: es la RED FINAL. El gate de FORMA (TARGET,\n"
    "  Tier, Fecha) ya paso; lo que falta es la COBERTURA del JUICIO — cada regla\n"
    "  con TRIGGER activo necesita su veredicto binario por el rol que la audita.\n\n"
    "  Green ⟺ veredicto ∈ {{PASS, N/A}}. Cualquier otra cosa NO cierra.\n\n"
    "  Que hacer:\n"
    "   - Si falta un veredicto: completa el roster del Steward — corre el verificador\n"
    "     de esa regla y registra su PASS/N/A (con evidencia archivo:linea o conteo).\n"
    "   - Si hay un FAIL: NO se cierra. Corregi el defecto y volve al Paso\n"
    "     correspondiente (re-itera bajo el techo); el veredicto pasa a PASS recien\n"
    "     cuando el verificador lo confirma sobre el artefacto en disco.\n"
    "   - Si todavia estas iterando: deja `runState: wip` (los WIP-commits pasan); pone\n"
    "     `closing` SOLO en el commit que cierra, con la matriz ya completa+verde.\n"
)


def main() -> None:
    # CLI de registro (no lee stdin, no es una tool-call gateada).
    if len(sys.argv) > 1 and sys.argv[1] == "--register-target":
        _handle_register(sys.argv[1:])
        return
    # Introspeccion del perfil resuelto (fixture de paridad, Grupo K).
    if len(sys.argv) > 1 and sys.argv[1] == "--print-profile":
        print(_gate_profile())
        sys.exit(0)

    # Perfil off (ADR 0011): guardian inerte por eleccion explicita del operador.
    if _gate_profile() == "off":
        _allow()
        return

    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        _allow()
        return
    if not isinstance(data, dict):
        _allow()
        return

    tool = (data.get("tool_name") or "").strip()
    ti = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()

    target_path: Path | None = None
    is_commit = False

    if tool in ("Edit", "Write", "MultiEdit"):
        fp = ti.get("file_path")
        if not fp:
            _allow()
            return
        target_path = Path(fp)
    elif tool == "Bash":
        cmd = ti.get("command") or ""
        norm = " ".join(cmd.split()).lower()
        if "git commit" not in norm and "git -c" not in norm:
            _allow()
            return
        if "commit" not in norm:
            _allow()
            return
        is_commit = True
    else:
        _allow()
        return

    anchor = target_path if target_path is not None else Path(cwd)
    repo = _find_repo_root(anchor if anchor.is_absolute() else (Path(cwd) / anchor))
    if repo is None:
        _allow()  # no es repo git -> inerte (vale para A y B)
        return

    # Filtro de path (exclusiones + es-codigo) — necesario para AMBAS ramas.
    if target_path is not None:
        try:
            abs_p = target_path if target_path.is_absolute() else (Path(cwd) / target_path)
            rel_parts = tuple(abs_p.resolve().relative_to(repo.resolve()).parts)
        except Exception:
            _allow()
            return
        if _is_excluded_path(rel_parts, abs_p.name):
            _allow()
            return
        if not _is_code_file(abs_p.name):
            _allow()  # no es fuente -> fail-open permitir
            return
        # ATOMICIDAD (Cambio 3): citacion NO bloqueante si el archivo >= T lineas.
        # Se emite a stderr y el flujo normal (allow/block) sigue igual. Fail-open.
        _emit_atomicidad_advisory(str(target_path), abs_p, repo)

    adopted = (repo / "docs" / "refactor" / "_crisol").is_dir()

    if not adopted:
        _piso_b(target_path, is_commit, repo, data)
        return

    # ── repo adoptado: flujo del Crisol (con cambio A) ──
    if is_commit and not _staged_has_code(repo):
        _allow()  # commit solo de docs/.md -> no requiere Crisol
        return

    branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    if branch is None:
        _allow()  # no podemos saber el branch -> fail-open
        return

    state = _ledger_state(repo, branch)
    if state == "ACTIVE_OK":
        # CAMBIO COBERTURA: el commit de cierre (runState: closing) exige la matriz
        # completa+verde. WIP-commits y ediciones pasan (cov solo muerde en commit).
        if is_commit:
            cov = _coverage_state(repo, branch)
            if cov == "CLOSING_INCOMPLETE":
                _block(MENSAJE_COBERTURA.format(repo=repo, branch=branch))
                return
        _allow()
        return
    if state == "ACTIVE_NO_TARGET":
        _block(MENSAJE_A.format(repo=repo, branch=branch))
        return
    _block(MENSAJE_NO_ACTIVE.format(repo=repo, branch=branch))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        # Ultima red fail-open: jamas brickear por un bug del propio gate.
        sys.exit(0)
