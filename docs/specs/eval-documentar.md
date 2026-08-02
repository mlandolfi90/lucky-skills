# Spec — Arnés de evaluación de conducta para `documentar`

Aprobado en conversación el 2026-08-02. Este archivo es la fuente; el código
de `evals/documentar/` es su artefacto.

## Qué mide

La conducta de un agente siguiendo `skills/documentar/SKILL.md` sobre un
fixture con drifts sembrados: ¿encuentra los drifts reales, cita
`archivo:línea` que resuelve, declara `UNVERIFIED` lo incomprobable, y
reporta contadores que coinciden con la realidad?

Es un termómetro. No publica, no edita skills, no reemplaza el endoso.

## Las cuatro reglas de la casa (anti-Goodhart)

Derivadas de los fallos documentados de microsoft/SkillOpt (issues #174 y
#175) y de fichas del saber propio:

1. **El juez mide el síntoma, no el formato.** Valida que la cita
   `archivo:línea` exista y contenga la afirmación — no exige headings ni
   formato de prosa. Tolerancia: ±2 líneas y ancla de texto (DRIFT-014).
2. **Canario para el juez.** El juez se calibra contra salidas buenas
   conocidas (deben dar PASS, incluso con formato distinto) y salidas malas
   sembradas (deben dar FAIL). Si el juez reprueba un caso bueno, el roto es
   el juez. (FALSO-VERDE-012/-015.)
3. **El que mide no edita.** El juez solo lee fixture + salida y emite
   reporte. Todo cambio de skill sigue entrando por madrina →
   publicar-skill → autorización humana.
4. **Nada de promedios que esconden.** Reporte por caso; una regresión de
   caso (PASS → FAIL contra el baseline) es VERDICT=FAIL aunque el agregado
   mejore. (Issue #174 de SkillOpt.)

## Contrato de salida del evaluado

El agente evaluado emite el bloque `## Salida` de `documentar`
(`AUDIT_SCOPE`, `DOCS_REVIEWED`, `DRIFT_FOUND`, `DRIFT_FIXED`, `UNVERIFIED`,
`MAP_UPDATED`) más una línea por hallazgo:

```text
HALLAZGO=<DRIFT|UNVERIFIED>|<doc_ruta>:<línea>|<cita textual>|<code_ruta>:<línea>|NONE
```

Rutas relativas a la raíz del fixture, formato POSIX. La cita no contiene
`|`. Un `DRIFT` exige referencia de código; un `UNVERIFIED` lleva `NONE`.

## Gold del fixture

`fixture/` contiene `src/calculadora.py` + `docs/MANUAL.md` con 6
afirmaciones etiquetadas en `gold.json`: 3 `DRIFT`, 2 `OK`, 1 `UNVERIFIED`
(la disciplina de no adivinar se mide: marcar la inverificable como OK o
DRIFT penaliza).

## Veredicto

`VERDICT=PASS` exige: recall 1.0 sobre los DRIFT sembrados, precisión 1.0
(cero falsos positivos), todas las citas válidas, contadores coherentes con
los hallazgos listados, disciplina UNVERIFIED respetada y cero regresiones
contra baseline. Exit code 0/1, estilo de la casa.

## Fuera de alcance (por ahora)

Optimización automática de la skill a partir del score. El score avisa; el
humano decide.
