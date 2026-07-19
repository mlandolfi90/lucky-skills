---
id: adr:0026
schema: decision/1
tipo: decision
estado: ACEPTADA
creado: 2026-07-19
supersede: null
superseded_by: null
refs: [corrida:2026-07-19-versionado-artefactos]
---

# 0026 — La versión de un artefacto es lectura del proceso

## Contexto

Faltaba una regla para responder "¿qué versión le pongo a esta entrega?" sin
inventar un número en el aire. El operador la fijó (spec 2026-07-19): la versión
de un artefacto de producto NO es un contador que alguien elige, es la **lectura
del proceso** que lo produjo — `generacion.corridas.hotfixes.microfixes`, cuatro
segmentos que cuentan cuántas veces pasó cada engranaje del Crisol por ese
artefacto.

Dos cosas la volvían urgente:

- **Reset a la derecha = colisión.** Si al subir un segmento se resetean los de
  la derecha, dos estados distintos del artefacto quedan con el MISMO string
  (pasó una corrida entera entremedio y el número no lo muestra). Un número que
  colisiona no sirve como lectura del proceso.
- **Conflicto con `hotfix §4`.** El carril hotfix ya numeraba betas `-bN`, y su
  paso de cierre decía "Versión final SIN sufijo beta": la beta **se caía al
  cerrar**. Eso contradice un contador acumulado — había que zanjar qué ES una
  beta.

## Decisión

1. **La versión = `generacion.corridas.hotfixes.microfixes`**, cuatro segmentos,
   cada uno la cuenta ACUMULADA de veces que ese engranaje corrió sobre el
   artefacto. **Sin reset a la derecha**: subir un segmento no toca los de abajo
   (con reset, dos estados distintos se ven iguales — la lectura mentiría).

2. **Commit por entrega NO se re-legisla.** Ya es ley dura en `hotfix §El
   registro` (:119-127: WIP-commit por cada bump, la columna `commit` ata cada
   fila al código exacto). Esta decisión lo REFERENCIA, no lo re-decreta.

3. **La beta es una entrega-para-probar (opción a).** El conflicto con `hotfix
   §4` se resuelve así: la beta no es un sufijo cosmético que se cae, es el
   CUARTO segmento moviéndose (una entrega más al operador para que la pruebe).
   Al cerrar, el contador queda donde la última entrega lo dejó; lo que
   desaparece es el stamp humano `-bN` de la UI (etiqueta de prueba), no la
   cuenta.

4. **Fuente de verdad DERIVABLE por segmento**, no un número tecleado: la cuenta
   de cada engranaje se LEE de sus registros (corridas de `runs/` CLOSED,
   `hotfixs/` CLOSED, sondas `microfixes/` FAVORABLE); los segmentos sin registro
   mecánico (generación, entregas-para-probar) son **disciplina declarada, no
   maquinaria**. El diente mecánico llega cuando un repo real adopte la regla;
   hoy es prosa normativa ("disciplina, no maquinaria prematura").

## Consecuencias

- **`hotfix/SKILL.md §4` deja de DEFINIR el contador** y pasa a puntero: la
  semántica vive en la rama 004; §4 conserva solo el aterrizaje por ecosistema
  (cómo se EXPRESA el número) y el stamp humano `vX.Y.Z-bN`.
- **`hotfix §Cerrar` pierde el "Versión final SIN sufijo beta"**: bajo contadores
  acumulados esa frase era FALSA (la beta no se cae). El cierre lo marca la fila
  del `Bug-` en CLOSED + la corrida de formalización, no un decremento cosmético
  del string.
- **La regla operativa vive en `crisol/ramas/004-versionado-artefactos.md`** (una
  define, las demás apuntan): los 4 segmentos, sus disparadores, las fuentes
  derivables, las ambigüedades cerradas, el mapeo por ecosistema y los deslindes.
- **Rige de acá en adelante**: no se re-numeran artefactos viejos; un artefacto
  nuevo NACE `0.0.0.0`.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.9.0` (cache local, NO la ley).**
