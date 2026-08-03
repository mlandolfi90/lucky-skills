# Spec — Sondas de conducta para la flota

Aprobado en conversación el 2026-08-03. Origen: caso PizarraEvo — el
anti-patrón "registro central que crece por edición" (`catalogo-tipos.js`)
vivió 5 días sin que nada lo señalara, y la auditoría mostró la causa de
fondo: 82 commits post-adopción, 23 cambios abiertos, **cero cierres**.
La gobernanza estaba instalada y muda. **Adoptado no es ejercido.**

## Principio rector (pedido explícito del operador)

**El abierto/cerrado no depende de la escalera.** La detección corre por
historia git, que existe siempre — si la sesión no abrió el ciclo de
cambio, la sonda ve el anti-patrón igual. Cazarlo al momento es barato;
cazarlo después es refactor + deuda.

## Pieza 1 — `run_sonda_abierto_cerrado.py`

Detecta archivos vivos cuya historia es la firma del registro central:
ediciones netamente aditivas, chicas y puras (ratio ≥ 0.75), con pista de
nombre (catalog|registr|tipos|index|...) como señal secundaria — sin pista
se exige una edición más. `--ultimos N` = modo hook ("¿esto creció por
edición AHORA?"). `--strict` para CI. Asesora: default exit 0.

La prueba de fuego que cita es la CORREGIDA (saber CAP-2c80bf0aae72: una
entrada = un archivo propio, carpeta detrás de un puerto). La ficha previa
CAP-c32b718f796c prescribe "tocar solo el archivo del catálogo" — nació
auto-capturada del propio diseño defectuoso de PizarraEvo el 2026-07-29 y
lo fosiliza; su supersede/corrección es una decisión de destilación humana
pendiente. Dos fichas LIVE se contradicen hasta que eso se resuelva.

Validación contra el caso real: en PizarraEvo @ pre-refactor caza
`catalogo-tipos.js`, `catalogo-capas.js` y `catalogo-relaciones.js` (los
tres con pista, arriba del ranking); en lucky-skills da 0 candidatos (no
grita en falso).

Límite declarado: mira historia, no semántica. Un archivo que DEJÓ de ser
registro pero sobrevive como shim puede seguir apareciendo con historia
completa — la ventana `--ultimos` es la lectura correcta para "hoy".

## Pieza 2 — `run_auditar_escalera.py`

Mide adoptado-vs-ejercido: commits (totales y desde la adopción) contra
los registros de `.lifecycle/changes/` y su profundidad. Veredictos:
`SIN_ACTIVIDAD` · `ESCALERA_VIVA` · `ESCALERA_PARCIAL` (cierres < 10% de
los commits) · `ESCALERA_MUDA` (commits sin ningún cierre). Asesor.

Medición inaugural (2026-08-03): PizarraEvo → MUDA (82 commits, 23
cambios, 0 cierres). El Taller sobre sí mismo → **también MUDA** (4
commits post-autoadopción, 0 registros). El instrumento no perdona a su
autor; ese es el punto.

## Pieza 3 — Packs corregidos

`arquitectura-verificar` entra al pack Base (docs/concepts/adoption-packs.md):
el único gate de SOLID/abierto-cerrado del catálogo llegaba solo como
dependencia de crisol (pack Deploy). Un repo base+UI —PizarraEvo— no tenía
quién verificara arquitectura, por diseño. Corregido.

## Pieza 4 — Hook asesor opt-in (instalación por repo, con su TARGET)

Para repos adoptados que quieran la sonda "al momento". ADVISORY, timeout
corto, jamás bloquea (la ley de hooks v1). Snippet para
`.claude/settings.json` del repo adoptado:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["-B", "<ruta-al-catalogo>/adapters/reference_python/run_sonda_abierto_cerrado.py", "--repo", ".", "--ultimos", "15"],
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

La instalación es por repo y pasa por `configurar-hooks` con autorización
propia — este spec no instala nada.

## Fuera de alcance

Enforcement. Las tres piezas son termómetros: declaran, no bloquean. Si un
día se quiere gate duro (p. ej. `--strict` en CI), es una decisión humana
por repo, nunca un default.
