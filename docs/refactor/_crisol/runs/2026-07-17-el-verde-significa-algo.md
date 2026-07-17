---
id: 2026-07-17-el-verde-significa-algo
schema: corrida/1
tipo: corrida
estado: ACTIVE
creado: 2026-07-17
branch: main
titulo: "El verde significa algo — CI en runner ajeno + RED_GREEN"
tier: "completo (ID nuevo en el catálogo §5 = contrato; >1 archivo; establece patrón: el primer verificador que NO es un LLM)"
target: "pc-local (donde el líder y el roster verifican). NOTA de bootstrap: esta corrida CONSTRUYE el runner ajeno, así que su propia evidencia de CI se observa en GitHub Actions tras el push de respaldo — el runner no existe hasta que se pushea."
model: "fable (uniforme)"
ley: "v2.5.0 (verificada — git ls-remote: máximo remoto == sello local)"
iteraciones: "0/3"
runState: wip
veredictos: []
refs: [adr:0022, concejo:2026-07-16-equipo-doc, adr:0017, adr:0016]
---
- ORIGEN: el operador mandó analizar 4 repos ajenos (`obra/superpowers`,
  `thedotmack/claude-mem`, `awesome-skills/code-review-skill`, `garrytan/gstack`).
  De 21 borradores cosechados endosó DOS: CI y RED_GREEN ("1+2"). El resto quedó
  descartado o parkeado por él.
  **Los dos saldan el mismo dolor**, y por eso van juntos en una corrida y no en
  dos: hoy la ley verifica que el verde EXISTA, nunca que SIGNIFIQUE algo.
- EVIDENCIA que lo justifica (no es moda — es la propia bitácora del repo):
  - `bitacora/entries/DRIFT-007` documenta que el mismo hook da verde en Windows
    y muere en Linux (`command not found`, exit 127) o falla EN SILENCIO por el
    stub de Microsoft Store (exit 49). **Mordió DOS veces** (`validated_on`: 1ª
    `faa405c` con repro Linux real; 2ª el paso 6b de `/ley`, que usaba
    `command -v` y falló callado en una corrida real).
    Su línea de PREVENCIÓN, escrita por el propio repo: *"la corrida que lo toque
    corre la suite en Linux fiel (REGLA 0 multi-OS)"* — **y no hay con qué**.
  - `crisol/SKILL.md:57-61` (REGLA 0) exige que el Verificador corra los tests
    ÉL MISMO **en el TARGET**, "jamás en la PC local". Hoy eso lo hace cumplir un
    rol-LLM sobre sí mismo, en la máquina del operador. Un runner Linux ajeno
    **es** el target que la regla pide y que nadie provee.
  - `crisol/SKILL.md:65-68`: `TEST_COVERAGE: NONE` puede emitir `PASS` (solo
    bloquea el tag estable). Es un falso-verde con nombre propio.
  - `registros.yaml:8` prohíbe editar proyecciones a mano **con una frase**. Sin
    CI, "jamás editar a mano" es un pedido.
  - Hallazgo de hoy: `leak-scan.sh:61` tenía la rama Windows muerta vaya a saber
    desde cuándo (saldado por `microfix:2026-07-16-leak-scan-ruta-windows`). El
    scanner solo corre en la forja; con CI corre en cada push.
- Alcance (CERRADO):
  1. **CI en runner ajeno** — `.github/workflows/` que corra en `ubuntu-latest`:
     las suites de `plugins/lucky/skills/*/tests/`, `registros-lint.py`,
     `leak-scan.sh` y `proyectar.py --check` (gate de drift de proyecciones).
  2. **`RED_GREEN`** — ID nuevo en el catálogo §5 + enunciado en §2 + su hogar en
     el `dictamina:` del guardián que corresponda: todo test que sostiene un PASS
     fue VISTO fallar antes; todo test de regresión probó su rojo por revert.
  3. **El falso-verde de `TEST_COVERAGE: NONE`** — revisar que `NONE` no siga
     emitiendo `PASS` sin más.
  4. **ADR 0022** — la decisión y su porqué.
  FUERA DE ALCANCE (el operador descartó explícitamente, hoy): multi-harness
  (verificado: superpowers porta 10 harnesses con UN solo evento `sessionStart`
  y CERO bloqueo — la portabilidad es consecuencia de no tener nada que perder);
  pressure-testing de la prosa (caro, queda para su corrida); gate de mtime
  (necesita diseño); doble voz cross-modelo (no hay 2º proveedor hoy).
- SELLO PENDIENTE (esperado, no es drift): el lint reporta 1 hallazgo —
  `corrida:2026-07-16-leak-scan-puente` CLOSED sin sello. Es la ventana normal
  entre cierre y forja: el sellador es el paso 4c de `forjar-release.sh`. La forja
  de cierre de ESTA corrida lo salda. Gate: lint POST-FORJA == 0.
- MIGRATION_STRATEGY: N/A (sin DDL)
- RETRO: <pendiente al cierre>
