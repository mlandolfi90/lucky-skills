## [GREP-003] Un script ESM ajeno falla en contenedor: "X is required, npm install X" aunque el paquete está en la imagen; o Chrome/puppeteer muere con "No usable sandbox"

- **TIPO:** GREP
- **SÍNTOMA (lo observable, NO la causa):** al correr un script `.mjs` de terceros dentro de
  un contenedor que YA trae la dependencia (p.ej. imagen `ghcr.io/puppeteer/puppeteer`), el
  `import` dinámico falla pidiendo instalarla aunque `NODE_PATH` apunte al `node_modules`
  correcto. Segundo tropiezo típico: Chrome crashea con `FATAL … No usable sandbox!`.
- **CAUSA-RAÍZ (1 línea):** la resolución ESM ignora `NODE_PATH` (resuelve subiendo desde la
  RUTA del script); y el sandbox de Chrome necesita user namespaces que el contenedor no da.
- **ACCIÓN (pasos, máx 7, copy-paste si aplica):**
  1. Copiar el script/kit DENTRO del contenedor junto al `node_modules` de la imagen
     (`cp -r /src/scripts /home/<user>/kit && cd /home/<user> && node kit/x.mjs`).
  2. Para Chrome/puppeteer: `docker run --cap-add=SYS_ADMIN …` (o launch-arg `--no-sandbox`
     si el contenido es confiable).
  3. Servicios del contenedor que binden `127.0.0.1`: publicar puerto NO alcanza — meter un
     mini-proxy TCP interno `0.0.0.0:<pub> → 127.0.0.1:<svc>` y publicar el proxy.
- **ANTI-ACCIÓN (el camino muerto):** insistir con `NODE_PATH`/`--preserve-symlinks`;
  `npm install` de puppeteer en una imagen slim (faltan libs compartidas de Chrome).
- **PREVENCIÓN (cómo evitar reincidencia):** para tooling con navegador usar SIEMPRE la
  imagen oficial de puppeteer (pineada) + los 3 pasos de arriba como receta estándar.
- **validated_on:** `main` · 2026-07-03 · `caaa641` (detect-URL de impeccable y Live Mode
  helper corridos así contra la vista de Lucky-TDU)
- **stale_si:** >90 días sin re-validar, O node cambia la resolución ESM
- **origen:** sesión misión impeccable 2026-07-03 (3 intentos hasta la receta)   ·   **usos:** 1
- **REFS:** Impeccable-Estudio/FASE-B-INFORME.md · docker-compose.eval.yml   ·   **NEXT:** n/a
- **estado:** LIVE
