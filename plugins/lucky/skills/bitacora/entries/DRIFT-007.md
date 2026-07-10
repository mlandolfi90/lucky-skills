## [DRIFT-007] Un hook/gate que anda perfecto en una máquina tira "python: command not found" (o "Python was not found" del stub de Store) en otra sesión/OS

- **TIPO:** DRIFT
- **SÍNTOMA (lo observable, NO la causa):** el mismo hook que corre verde en
  Windows/Git-Bash falla en una sesión Linux con `python: command not found`
  (exit 127) o con ruta inexistente estilo `C:\Users\...`; o al revés: en
  Windows imprime `Python was not found; run without arguments to install
  from the Microsoft Store` (exit 49) aunque "python3 está en PATH".
- **CAUSA-RAÍZ (1 línea):** el cableado hornea valores de UNA máquina (ruta
  absoluta con backslashes, binario `python` pelado) y confía en `command -v`
  — pero Linux moderno solo trae `python3`, y el stub de Microsoft Store
  EXISTE en PATH sin funcionar: existir ≠ correr.
- **ACCIÓN (pasos, máx 7, copy-paste si aplica):**
  1. Cablear SIEMPRE portable: `$HOME` (jamás ruta absoluta horneada) +
     PROBAR el intérprete en vez de confiar en PATH:
     `for PY in python3 python; do "$PY" -c "" >/dev/null 2>&1 && exec "$PY" "$GATE"; done; exit 0`
  2. Fail-open explícito si el artefacto no está instalado en esa máquina:
     `[ -f "$GATE" ] || exit 0` (una sandbox fresca jamás se rompe por el hook).
  3. Verificar en el OTRO OS antes de forjar (WSL/docker-local): correr la
     suite completa ahí, no asumir que "bash es bash".
- **ANTI-ACCIÓN (el camino muerto):** "arreglarlo" instalando python/alias en
  la máquina que falla (parche por máquina = el drift vuelve en la próxima);
  confiar en `command -v python3` sin probarlo (el stub de Store pasa ese check).
- **PREVENCIÓN (cómo evitar reincidencia):** todo cableado que escriba un
  instalador lleva las 3 patas (portable + probar-intérprete + fail-open) y la
  corrida que lo toque corre la suite en Linux fiel (REGLA 0 multi-OS).
- **validated_on:** `main` · 2026-07-10 · 1ª: `faa405c` (repro Linux real + WSL
  python3-only: 127→fix→batería verde ambos OS; stub de Store cazado: exit 49) ·
  2ª: el 6b de /ley usaba `command -v` y falló EN SILENCIO por el stub en una
  corrida real — la entrada lo diagnosticó al toque; corregido a sonda (v1.36.0)
- **stale_si:** >90 días sin re-validar, O el cableado migra a un launcher que
  ya resuelva intérprete/OS por sí mismo
- **origen:** RUN-LEDGER main 2026-07-09 (portabilidad multi-OS) · reporte del operador   ·   **usos:** 2
- **REFS:** scripts/instalar-gate.sh · GUIA-SKILLS (hooks de flota)   ·   **NEXT:** n/a
- **estado:** LIVE  <!-- endoso MLL 2026-07-09, promovida de CANDIDATE -->
