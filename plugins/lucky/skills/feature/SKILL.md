---
name: feature
description: >-
  Feature — lo que el proyecto DEBE TENER, como registro de primera clase
  (ADR 0020). Disparar con "/feature", "quiero que el proyecto tenga X",
  "agreguemos una sección/capacidad X", o al PROMOVER una idea madura del
  parking. Una feature tiene nacimiento, funcionalidad, de qué evolucionó,
  qué se intentó y qué funcionó — y NUNCA "cierra": crece por sub-features
  (padre:). Gate de doc: no llega a VIVA sin su documentación. NO usar para
  ideas volátiles (eso es /idea — el parking) ni para bugs (eso es la
  escalera diagnostico→microfix→hotfix→crisol).
allowed-tools: Read, Grep, Glob, Bash, Agent, Write, Edit
---

# Feature — lo que el proyecto debe tener

Una idea es una línea que espera; una **feature** es un compromiso con
historia: qué es, de dónde vino, qué se intentó, qué funcionó, y qué le
crece adentro. El operador la definió así: *"debe tener su nacimiento, su
funcionalidad, si evolucionó de otra cosa, qué se hizo o se intentó y qué
funcionó — y no necesariamente cierra: también puede crecer"*.

**Ejes:** primera clase (fila, no línea de parking) · genealógica (origen y
descendencia trazados) · honesta (los intentos fallidos se registran) ·
viva (crece por sub-features, jamás "termina") · documentada (sin doc no
está VIVA).

**Ramas de esta skill** (ADR 0018 — aprendizaje condicional, se carga SOLO si
el gatillo matchea; el bloque lo regenera `scripts/proyectar.py`):

<!-- RAMAS:BEGIN (generado por scripts/proyectar.py — propuesta = cuarentena, no rutea; ADR 0018) -->
| # | gatillo (si tu situación matchea → abrí SOLO esa rama) | rama |
|---|---|---|
| 001 | una feature transiciona a VIVA y el gate de doc muerde (autor↔lector, veredicto, desempate) | ramas/001-gate-de-doc.md |
<!-- RAMAS:END -->

## La fila (tabla `feature`, registros.yaml — `docs/features/`)

```
---
id: <slug>                    # ej: settings, settings-dark-mode
schema: feature/1
tipo: feature
estado: PROPUESTA             # PROPUESTA → EN-DISENIO → EN-CONSTRUCCION → VIVA | DESCARTADA
creado: <YYYY-MM-DD>
padre: null                   # sub-feature → feature:<id-del-padre>
origen: <idea:I-nnn | operador | diagnostico:...>
audiencia: user               # user → docs/manual/ (tutorial+how-to) | dev → docs/sistema/ (reference+explanation)
doc: null                     # → docs/manual/ (user) | docs/sistema/ (dev) — OBLIGATORIO para VIVA; lo escribe el FLUJO tras PASA
doc_veredicto: {estado: PENDIENTE, ronda: 0, ref: null}   # estado: PENDIENTE|PASA|FALLA
intentos: []                  # [{que: "...", resultado: funcionó|descartado, ref: corrida:...}]
refs: []
---
<funcionalidad: QUÉ hace, observable, ≤15 líneas>
```

## Reglas duras

1. **Promoción desde idea**: si la feature nace de una línea de `docs/IDEAS.md`,
   esa línea cambia su estado inline a `PROMOVIDA` (+ el id de la feature) —
   la idea no se borra ni se duplica: se gradúa. Se acaba el abuso del parking.
2. **Gate de doc (jidoka)**: `estado: VIVA` exige DOS cosas, no una: (i) `doc:`
   apuntando a un archivo REAL (`docs/manual/` si `audiencia: user`,
   `docs/sistema/` si `dev`) Y (ii) `doc_veredicto.estado: PASA`. Sin veredicto
   = PENDIENTE = NO pasa (la ausencia BLOQUEA, jamás habilita). Lo valida
   `registros-lint.py`, no la prosa. Sin ambas → se queda `EN-CONSTRUCCION`.
3. **Nunca cierra**: agregarle algo a una feature VIVA = sub-feature nueva con
   `padre:` — jamás reabrir ni reescribir la fila del padre (el árbol, otra
   vez). `DESCARTADA` es el único terminal, con el porqué en el cuerpo.
4. **Los intentos se registran**: cada camino probado (funcionó o no) suma a
   `intentos:` con su ref — la feature es memoria, no solo estado.
5. **La construcción va por la escalera/crisol**: esta skill REGISTRA y traza;
   el código de la feature entra por corridas normales que la citan en `refs:`.

## Flujo

1. **Nace**: fila `PROPUESTA` (+ graduación de la idea si aplica).
2. **Se diseña/construye**: transiciones + `intentos:` + refs a corridas.
3. **VIVA**: el gate de doc muerde → bucle autor↔lector con `manualizador-2`
   (agente canónico; el `manualizador` está SUPERSEDED — el nombre del llamador
   es el único de-ruteo) → ver rama `001-gate-de-doc` → recién con
   `doc_veredicto.estado: PASA` la transición es legal. Regenerar proyecciones
   en el mismo paso.
4. **Crece**: sub-features con `padre:` repiten el ciclo.

---
**Fuente: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.7.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene tag
mayor, seguir la del repo. Caso skill nueva: si el tag mayor no incluye
`feature/`, tratar como sin-red y registrar `LEY: <tag> (local, skill nueva)`.
