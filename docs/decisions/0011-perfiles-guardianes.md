# 0011 — Perfiles de los guardianes: CRISOL_GATE_PROFILE (estricto | aviso | off)

- estado: aceptado
- fecha: 2026-07-09
- decide: MLL (operador) — orden "aplica todo lo que propusiste hasta el final"
- tags de la familia al sellar: v1.30.0
- relacionado: ADR 0002 (gate de cobertura fail-closed); ADR 0008 (citación por
  tamaño — estableció el patrón env→conf→default y la paridad por fixture);
  ECC `run-with-flags.js` / `ECC_HOOK_PROFILE` (github.com/affaan-m/ECC);
  RUN-LEDGER corrida `main — 2026-07-09 (absorción ECC lote 1)`

## Contexto

Los guardianes (`crisol_gate.py` global + `crisol-enforcer.sh` del plugin) eran
binarios: encendidos o desinstalados. Para un spike, un repo de juguete o una
demo, la única forma de aflojarlos era editar hooks/settings a mano — y volver a
armarlos después (fricción + riesgo de olvidarlos apagados). ECC resuelve esto
con perfiles por env (`ECC_HOOK_PROFILE`: minimal/standard/strict +
`ECC_DISABLED_HOOKS` + `ECC_DRY_RUN`). Se absorbe el CONCEPTO reducido a la
superficie mínima que lucky necesita.

## Decisión

**Una sola perilla:** `CRISOL_GATE_PROFILE` (env, 12-factor, jamás persistida en
el repo), con parseo CANÓNICO idéntico en ambos guardianes (trim ASCII de bordes
+ lowercase; paridad probada por `test-enforcer.sh` Grupo K — 17 casos):

| Perfil | Semántica |
|---|---|
| `estricto` (**default**) | comportamiento de siempre: exit 2 en toda violación |
| `aviso` | el diagnóstico COMPLETO llega a stderr con el marcador `[CRISOL-AVISO] (modo aviso: NO bloqueado …)`, pero la tool-call PASA (exit 0). Aplica a TODOS los bloqueos: ledger sin ACTIVE, TARGET faltante, piso B (repos no adoptados) y cobertura de cierre |
| `off` | guardián inerte (exit 0 temprano, sin diagnóstico) |

**Reglas duras:**
- **Inválido/vacío → `estricto`** (fail-closed a DUREZA: un perfil mal tipeado,
  con basura o unicode-whitespace JAMÁS afloja el gate — espejo de la lección
  I5/I5b del umbral de atomicidad).
- **Aflojar el perfil es acto del OPERADOR** (setear el env en su shell/launcher),
  nunca del agente: un modelo que se auto-setea `aviso`/`off` para esquivar un
  bloqueo viola la ley (el marcador en stderr delata el modo en todo transcript
  — y el observador de la bitácora lo registra como señal).
- No se absorben `ECC_DISABLED_HOOKS` ni `ECC_DRY_RUN`: con 2 hooks, `off` cubre
  el primero y `aviso` ES el dry-run (menos superficie, misma capacidad).
- Introspección para el fixture: `--print-profile` en ambos guardianes (mismo
  patrón que `--print-threshold`/`--print-code-policy` del ADR 0008).

## Consecuencias

- (+) Spikes/demos/repos de juguete sin desarmar la ley ni editar hooks.
- (+) `aviso` como modo diagnóstico: se VE qué habría bloqueado el estricto
  (útil para adopciones nuevas y para depurar el propio gate).
- (−/a vigilar) Es la primera perilla que puede aflojar la ley de la flota: el
  default estricto + fail-closed-a-dureza + marcador siempre-visible son las
  tres defensas. El env no viaja por autoUpdate (es por máquina/sesión): no hay
  forma de aflojar la flota entera desde el repo.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.1.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.
