---
name: ley-viva
description: Comprobar al inicio de sesión que las skills adoptadas siguen vigentes contra el catálogo publicado, y avisar antes de trabajar si hay versión nueva. Nunca actualiza por su cuenta.
---

# Ley viva

Que ningún repo trabaje con gobernanza vencida sin saberlo.

## Fuente

```text
CATALOG_SOURCE=github.com/mlandolfi90/lucky-skills
REF=último tag skill-<id>-v* publicado; sin tags, el manifiesto en la rama default
```

La fuente es una línea mutable: cuando el catálogo migre de repo, cambiarla
es un PATCH de esta skill.

## Invariantes

- Se ejecuta al inicio de sesión en un repo adoptante, antes del trabajo:
  la invoca `cargar-reglas` como segundo acto de su orden de arranque.
  El hook lifecycle del repo (`configurar-hooks`, evento `SESSION_START`)
  la recuerda; el hook global de `scripts/` la ejecuta (ver Hook).
- Lo que esta skill avisa lo ejecuta `adopcion` (una skill por transacción,
  con sus dependencias) o el comando `actualizar-skills` del repo; nunca
  esta skill. Una skill del catálogo que el repo nunca adoptó no aparece
  como atrasada: se ofrece aparte, como disponible.
- Compara lo adoptado (`.lifecycle/state/skills/*.env`) contra lo publicado
  en el catálogo, con la semántica SemVer de la casa: PATCH/MINOR nuevo →
  actualización fluida disponible; MAJOR nuevo → adaptación requerida.
- Solo avisa: la transición la ejecutan sincronizar y adopción con sus
  propias compuertas. Avisar no es actualizar.
- Sin acceso al catálogo, la vigencia es `UNKNOWN` y se declara: se trabaja
  con lo adoptado (que está instalado y verificado por huella), pero jamás
  se afirma "al día" sin haber comprobado.
- El aviso es corto: una línea por skill desactualizada, con su salto.

## Hook

La comprobación corre sola, sin que nadie se acuerde, desde
`scripts/ley-viva-aviso.py`: advisory puro, `exit 0` siempre, sin escritura
fuera de su propia marca de tiempo, sin secretos. En Claude Code se instala
como hook global del usuario, no del repo: copia byte a byte en
`~/.claude/hooks/ley-viva-aviso.py` y dos entradas en `~/.claude/settings.json`,
`SessionStart` (siempre) y `UserPromptSubmit` con `--throttle 900` (una vez
cada quince minutos por workspace). La copia instalada se compara por hash
contra la de la skill adoptada; si difiere, se reinstala desde la skill, no se
edita en disco. Hasta el 2026-09-10 el hook vivió solo en `~/.claude/hooks/`,
sin historial (lo midió lucky-tool-netbox); `~/.claude` no puede ser repo
porque guarda credenciales, por eso la fuente de verdad es esta skill.

Tres estados, no dos: atrás del catálogo (`UPDATE_AVAILABLE`,
`ADAPTATION_REQUIRED`) y adelante (`ADOPTED_AHEAD`: una versión adoptada que
ningún tag publica; sale de adoptar una fuente sin sellar o de un registro
escrito a mano, y no es estar al día). Lo nunca adoptado se cuenta
(`NOT_ADOPTED=n`), no se lista. Un aviso largo se recorta a seis líneas y el
recorte se declara. Pruebas: `python scripts/test_ley_viva_aviso.py` contra
el catálogo real, y `tests/conformance/test_hooks_globales.py` sin red.

## Flujo

1. Enumerar las skills adoptadas del repo y sus versiones.
2. Resolver el catálogo a su referencia vigente.
3. Comparar versión por versión y clasificar cada salto.
4. Avisar antes de que el trabajo empiece; registrar la comprobación.

## Salida

```text
CATALOG=<repo@ref|UNREACHABLE>
ADOPTED=n
CURRENT=n
UPDATE_AVAILABLE=<skill@salto,...|NONE>
ADAPTATION_REQUIRED=<skill@salto,...|NONE>
ADOPTED_AHEAD=<skill@versión sin tag,...|NONE>
NOT_ADOPTED=n
CURRENCY=VERIFIED|UNKNOWN
```
