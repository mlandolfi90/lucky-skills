---
name: microfix
description: >-
  Microfix — peldaño 1 de la escalera de calidad: SONDA mínima que corrige UN
  comportamiento tocando UN punto específico del código para ver si el cambio
  es favorable. Disparar con "/microfix", "probá tocando X", o como entrada
  DEFAULT de toda corrección cuyo tope no fue indicado (el flujo PREGUNTA
  "¿hasta qué escalón llega esto?" antes de tocar). TARGET obligatorio (dev =
  default; pc-local solo caso especial explícito; producción JAMÁS para
  sondar). Veredicto binario favorable/no-favorable; si revela profundidad
  ESCALA a hotfix llevándose sus refs — sin saltos de peldaño. NO usar para
  soluciones ya conocidas multi-archivo o de contrato (eso entra directo por
  crisol) ni para investigación profunda iterativa (eso es hotfix).
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Microfix — ¿tocando acá se corrige?

Peldaño **1** de la escalera (ADR 0017): `diagnostico → microfix → hotfix →
crisol`. La sonda: UN comportamiento objetivo, UN punto tocado, un veredicto.
La ceremonia cara llega recién cuando el camino está claro — nunca antes.

**Ejes:** mínimo (un punto = un archivo/una función) · declarado (target
SIEMPRE, tope SIEMPRE) · binario (favorable o no) · escalable (sube con sus
refs, jamás salta) · sin residuo (sonda no favorable se revierte).

## Reglas duras

1. **El tope se pregunta.** Si el operador no indicó hasta qué escalón llega la
   corrección, PREGUNTAR antes de tocar: *"¿hasta qué escalón? (microfix |
   hotfix | crisol)"*. Con diagnóstico previo, su `tope_sugerido` es el
   default a confirmar. Sin respuesta del operador → no se toca código.
2. **TARGET obligatorio, por peldaño.** La sonda declara DÓNDE corre:
   `dev`/mesa caliente = default; `pc-local` SOLO si el operador lo pide
   explícito para un caso especial; **producción jamás se sondea** (si el
   síntoma es de prod: diagnóstico en prod (read-only) + sonda en dev).
3. **UN punto.** Si la sonda necesita tocar un SEGUNDO lugar para lograr el
   comportamiento → ya no es microfix: registrar NO_FAVORABLE + escalar.
4. **Sin saltos.** Del 1 se pasa al 2 (hotfix), no al 4. ¿Quién tiene piernas
   tan grandes? La única excepción: solución que resulta conocida y toca
   contrato → se cierra el microfix como ESCALADO y se abre crisol directo,
   dejando la cadena de refs.
5. **Sonda sin residuo:** veredicto NO_FAVORABLE → el toque se revierte
   (checkout del archivo); si escala y el intento sirve como beta → viaja como
   contexto en la fila, el código vuelve a limpio salvo que el hotfix lo adopte
   de entrada.
6. **Puente de gate (Fase 1):** si la sonda toca código en un repo adoptado,
   el gate exige corrida — abrir TAMBIÉN una corrida **fast-path mínima** con
   `refs: [microfix:<id>]` (ceremonia de 30 segundos: fila corrida + proyectar)
   y cerrarla con el veredicto. Cuando la Fase 2 enseñe a los guardianes a
   leer peldaños, este puente muere y el microfix será su propio permiso.

## Procedimiento

1. **Tope** (regla 1) + **TARGET** (regla 2). Con diagnóstico previo:
   heredar `zona_sospechada` y refs.
2. **Abrir la fila** en `docs/microfixes/` (tabla del taller) + puente de gate
   si aplica (regla 6).
3. **Tocar el punto** (Edit mínimo) + **observar el comportamiento objetivo**
   (el mismo comando/flujo del diagnóstico o el que exhiba el síntoma).
4. **Veredicto binario:**
   - **FAVORABLE** → cerrar fila + puente; commit del toque (mensaje:
     `microfix: <comportamiento> (<id>)`). Si además amerita formalización
     (patrón/contrato/documentación) → decirlo: el operador decide si va a
     crisol.
   - **NO_FAVORABLE** → revertir (regla 5), cerrar fila con lo aprendido.
   - **Revela profundidad** → estado ESCALADO; abrir hotfix con
     `refs: [microfix:<id>, diagnostico:<id>]` — la investigación sigue en el
     peldaño 2 con todo el contexto a cuestas.

## La fila (tabla `microfix`, registros.yaml)

```
docs/microfixes/<YYYY-MM-DD-slug>.md
---
id: <YYYY-MM-DD-slug>
schema: microfix/1
tipo: microfix
estado: FAVORABLE           # ACTIVE | FAVORABLE | NO_FAVORABLE | ESCALADO
creado: <YYYY-MM-DD>
comportamiento: "<QUÉ se quiere corregir, observable>"
punto_tocado: "<archivo:línea — el ÚNICO punto>"
target: "<dónde corrió la sonda>"
tope: <microfix | hotfix | crisol>   # lo que el operador autorizó
observacion: "<qué pasó al tocar (≤2 líneas, sin secretos)>"
escalado_a: <hotfix:<id> | crisol:<id> | null>
refs: [diagnostico:<id>]
---
<contexto mínimo>
```

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.6.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo
(`raw.githubusercontent.com/mlandolfi90/lucky-skills/<tag>/plugins/lucky/skills/microfix/SKILL.md`)
e informar al humano. **Caso de skill nueva:** si el tag remoto mayor NO
incluye `microfix/` (la skill nació en este bump), tratar como sin-red —
seguir esta copia y registrar `LEY: <tag> (local, skill nueva sin verificar)`.
Sin red: seguir esta copia.
