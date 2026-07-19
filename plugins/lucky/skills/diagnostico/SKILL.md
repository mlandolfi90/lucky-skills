---
name: diagnostico
description: >-
  Diagnóstico — peldaño 0 de la escalera de calidad: evaluador PASIVO
  read-only que investiga un bug SIN tocar nada. Reproduce, localiza (bitácora
  por síntoma + arquitectura por capa + grep dirigido) y dice "más o menos acá
  hay que tocar": zona sospechada archivo:línea + hipótesis + escalón/tope
  recomendado. Disparar con "/diagnostico", "diagnosticá X", "¿por qué falla?",
  "¿qué está pasando acá?", o ante un bug reportado sin causa clara. Cero
  escritura al sistema observado → invocable en CUALQUIER entorno, incluso
  producción. Su fila alimenta al microfix/hotfix/crisol vía refs. NO
  implementa el fix (eso es el peldaño que el operador elija) ni especula sin
  evidencia (fail-closed: lo no reproducible se reporta N/D).
allowed-tools: Read, Grep, Glob, Bash
---

# Diagnóstico — ¿qué está pasando y dónde hay que tocar?

Peldaño **0** de la escalera (ADR 0017): `diagnostico → microfix → hotfix →
crisol`. Es una brújula para bugs: reemplaza suposiciones por evidencia, y su
única escritura es SU PROPIA FILA en el repo del taller.

**Ejes:** pasivo (cero mutación del sistema observado) · localizador (termina
en `archivo:línea`, no en teoría) · honesto (sin reproducción no hay hipótesis
con autoridad) · barato (siempre es legal correrlo, en cualquier entorno).

## Reglas duras

1. **READ-ONLY al mundo.** Comandos de observación solamente (curl GET, logs,
   `docker ps`, lecturas). Nada de restarts, redeploys, writes, DDL, ni "probar
   tocando" — eso es el peldaño 1. Si el diagnóstico exige mutar para observar
   → se reporta y ESCALA, no se muta acá.
2. **La única escritura permitida**: su fila en `docs/diagnosticos/` del repo
   de trabajo (tabla del taller, exenta del gate por ser docs/).
3. **Evidencia o N/D.** Cada hipótesis cita QUÉ observación la sostiene. Lo que
   no se pudo reproducir/observar se registra `N/D` — jamás se rellena
   (REGLA DE ORO de la brújula, aplicada a bugs).
4. **Sin tope propio**: el diagnóstico RECOMIENDA escalón y tope; el que decide
   es el operador (o el flujo que pregunta el tope en el peldaño 1).

## Procedimiento

1. **Síntoma en una línea** (las palabras del operador o del reporte).
2. **Bitácora por síntoma (pull):** grepear el INDEX de la skill `bitacora`
   por las palabras del síntoma; si matchea, traer SOLO esa entrada — su
   línea de acción puede cerrar el diagnóstico en segundos (patrón conocido).
3. **Reproducir observando:** el comando/flujo mínimo que EXHIBE el síntoma
   (curl → código de estado, log → línea exacta, test existente → rojo).
   Registrar el comando y su salida relevante (≤3 líneas, sin secretos).
4. **Localizar:** con la skill `arquitectura` (¿qué capa es esto?) + grep
   dirigido por los términos del error → **zona sospechada** `archivo:línea`
   (o rango). Si hay varias, ordenarlas por probabilidad.
5. **Hipotetizar:** máximo 3 hipótesis, cada una con su evidencia y cómo
   verificarla barato.
6. **Recomendar:** escalón de entrada (`microfix` si hay UN punto claro;
   `hotfix` si exige investigación tocando; `crisol` si ya se sabe la solución
   y toca contrato/multi-archivo) + tope sugerido + env donde sondear.
7. **Registrar la fila** y devolver al operador un resumen de 5 líneas.

## La fila (tabla `diagnostico`, registros.yaml)

```
docs/diagnosticos/<YYYY-MM-DD-slug>.md
---
id: <YYYY-MM-DD-slug>
schema: diagnostico/1
tipo: diagnostico
estado: RESPONDIDO          # ABIERTO | RESPONDIDO | DESCARTADO
creado: <YYYY-MM-DD>
sintoma: "<una línea>"
reproduccion: "<comando → observación>"
zona_sospechada: ["<archivo:línea>", ...]
hipotesis:
  - {h: "<hipótesis>", evidencia: "<qué la sostiene>", verificar: "<cómo barato>"}
bitacora_match: <bitacora:ID | null>
escalon_recomendado: microfix | hotfix | crisol
tope_sugerido: <microfix | hotfix | crisol>
target_observado: "<dónde se observó el síntoma>"
refs: []
---
<notas de observación, sin secretos>
```

El peldaño siguiente la consume vía `refs: [diagnostico:<id>]` — la cadena
completa queda trazada: diagnóstico → microfix → hotfix → corrida.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.8.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo
(`raw.githubusercontent.com/mlandolfi90/lucky-skills/<tag>/plugins/lucky/skills/diagnostico/SKILL.md`)
e informar al humano. **Caso de skill nueva:** si el tag remoto mayor existe
pero NO incluye `diagnostico/` (la skill nació en este bump), tratar como
sin-red — seguir esta copia y registrar `LEY: <tag> (local, skill nueva sin
verificar)`. Sin red: seguir esta copia.
