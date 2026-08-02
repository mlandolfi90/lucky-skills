# Arnés de evaluación de conducta — `documentar`

Spec y reglas anti-Goodhart: [docs/specs/eval-documentar.md](../../docs/specs/eval-documentar.md).

## Piezas

- `fixture/` — mini-proyecto con 6 afirmaciones documentales: 3 drift
  sembrados, 2 correctas, 1 incomprobable (mide la disciplina UNVERIFIED).
- `gold.json` — etiquetas por ancla de texto (no por número de línea).
- `juez.py` — juez determinista, solo stdlib. Exit 0/1.
- `canarios/` + `test_juez.py` — calibración del juez: los buenos deben
  PASS (incluso con formato raro), los malos deben FAIL por su razón.
- `baseline.json` — última corrida real aceptada; el juez marca REGRESION
  si un caso que pasaba deja de pasar.

## Correr

Calibración del juez (rápida, sin LLM):

```bash
python -B -m pytest evals -q
```

Juzgar la salida de una corrida real:

```bash
python -B evals/documentar/juez.py --salida <salida.txt> --baseline evals/documentar/baseline.json
```

La corrida real se produce con un agente que sigue
`skills/documentar/SKILL.md` sobre `fixture/`, en solo lectura, emitiendo el
bloque `## Salida` más líneas `HALLAZGO=` (contrato en el spec).

## Primera medición (2026-08-02)

Agente: subagente Claude sobre el fixture, sin conocer el gold.
Resultado: 6/6 casos PASS · precisión 1.00 · recall 1.00 · citas 4/4 ·
VERDICT=PASS. Guardada como `baseline.json`.

El score es termómetro: avisa, no edita. Ningún cambio de skill sale de
acá sin madrina → publicar-skill → autorización humana.
