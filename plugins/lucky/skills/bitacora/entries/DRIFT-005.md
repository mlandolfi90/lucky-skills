## [DRIFT-005] Tests verdes en local pero el stage `test` del CI muere en collection con ModuleNotFoundError de un módulo NUEVO

- **TIPO:** DRIFT (Dockerfile ↔ código: el COPY enumerado no conoce el archivo nuevo)
- **SÍNTOMA (lo observable, NO la causa):** Agregaste un módulo `.py` nuevo al servicio; la suite
  pasa completa en local, pero el build del CI falla en el stage `test` con
  `ModuleNotFoundError: No module named '<módulo_nuevo>'` en TODOS los test modules
  (interrupted during collection).
- **CAUSA-RAÍZ (1 línea):** el Dockerfile copia los archivos sueltos ENUMERADOS uno a uno
  (`COPY a.py b.py c.py ./`) — el módulo nuevo existe en el repo pero jamás entra a la imagen;
  local funciona porque corre sobre el working tree.
- **ACCIÓN (pasos, máx 7):**
  1. Andá al Dockerfile del servicio y buscá el `COPY` de archivos sueltos.
  2. Sumá el módulo nuevo a esa línea (o migrá a COPY por paquete/directorio si ya son muchos).
  3. Re-push: el stage `test` del CI es el verificador real (REGLA 0) — verde ahí = probado.
- **ANTI-ACCIÓN (el camino muerto — evita re-derivar):** NO toques sys.path, imports diferidos ni
  conftest para "arreglar" el import: el módulo NO ESTÁ en la imagen; ninguna gimnasia de import
  lo va a encontrar. NO debuggees los tests: fallan TODOS a la vez, eso ya te dice que es el
  entorno, no el código.
- **PREVENCIÓN (cómo evitar reincidencia):** al crear cualquier archivo nuevo importado por el
  servicio, el checklist mental incluye "¿el Dockerfile lo copia?"; los COPY enumerados son una
  lista de allowlist — cada módulo nuevo requiere tocarla.
- **validated_on:** `dev` · 2026-07-03 · `16b33c4` (fix del COPY; CI verde en `fa3127a`, deploy verificado en vivo)
- **stale_si:** >90 días, o si el Dockerfile pasa a COPY de directorio completo
- **origen:** Lucky-Auth-Plane RUN-LEDGER (handlers-provider-limits, run CI 28638932678 failure)   ·   **usos:** 1
- **REFS:** keyring/Dockerfile:93   ·   **NEXT:** si se repite, migrar a `COPY *.py ./` con .dockerignore
- **estado:** CANDIDATE
