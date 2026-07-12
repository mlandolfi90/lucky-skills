# 0014 — Hotfix: anti-círculo (whack-a-mole) + colapso del vault al catálogo `hotfixs/`

- estado: aceptado
- fecha: 2026-07-11
- decide: MLL (operador) — pedido "que no rompa una cosa al arreglar otra bajo
  hotfix" + "estructurar mejor la skill"; diseño perfeccionado por dos paneles
  adversariales (6 diseños en competencia → síntesis; luego autoría + 5 lentes de
  verificación) y decisiones cerradas UNA a una por el operador
- supersede parcialmente: **ADR 0012** — su punto 2 ("vault
  `docs/refactor/_hotfix/<slug>/INTENTOS.md`") queda COLAPSADO a
  `docs/hotfixs/Bug-<frase-corta>.md`. El resto de 0012 sigue vigente.
- tags de la familia al sellar: v1.36.0 (se re-sella en la forja del próximo tag)
- relacionado: skill `hotfix`; bitácora **DRIFT-009** (whack-a-mole, la META que
  esta corrida encarna), DRIFT-008, GREP-004, FALSO-VERDE-003; Crisol §6
  (meta-cambio a la ley); ADR 0012 (el carril original); ADR 0005 (bitácora Capa 4)

## Contexto

El caso fundacional (popover-bleed) y el arco HOT-MIC destaparon un **segundo
enemigo** del hotfix, distinto de la adivinanza serial: el **CÍRCULO**
(whack-a-mole) — arreglás X y se rompe Y, arreglás Y y se rompe X. Cada beta
*pasa* cuando se prueba sola, así que ningún breaker de mismo-síntoma (2-strikes)
salta: los síntomas ALTERNAN. Causa-raíz (DRIFT-009): dos señales INDEPENDIENTES
gobiernan lo que se vive como UN estado; el fix se ata a una, la otra queda rota.
La lección estaba en la Bitácora pero NO en la skill.

Además el vault del carril (ADR 0012 punto 2) era **efímero**: el mapa de
controles —lo caro de descubrir— moría al cerrar el arco, condenando a
re-descubrir la superficie de control en cada sesión.

## Decisión

### A. Anti-círculo — visibilidad + consejo, CERO enforcement
Sobre un estado con **>1 control** (un fix de un solo control no paga nada de
esto), la salida del carril deja de ser "el síntoma que tocaste quedó verde" y
pasa a ser evidencia de una **cura ENTERA** (el estado sostenido por TODOS sus
controles). Piezas:

1. **Regla-5 (§Abrir): mapear los controles.** DESCUBRIR = grep del código (ve la
   señal interna que no se te ocurre nombrar) + elicitación del operador, que
   **DEBEN COINCIDIR** para que el `modelo-estado:` (quién MANDA vs quién es
   CONFIG) cuente como firme.
2. **Verificar splitea por RÉGIMEN** (universal): *ciego* (operador = único
   instrumento de runtime) vs *vidente* (el modelo corre y verifica cada camino,
   cruzado con el entorno real, FALSO-VERDE-003).
3. **Breaker "choque cruzado" (§Ciclo):** hermano ORTOGONAL del 2-strikes.
   2-strikes = mismo síntoma 2 veces → instrumentar. Choque cruzado = un control
   que estaba `✓` vuelve a `✗`/`~` (regresión/alternancia) → parar y re-modelar
   (puntero a DRIFT-009). Dispara al **1er rebote**, con salvaguarda del
   falso-positivo del revert. Es **AVISO, no candado**.
4. El `✓` de síntoma es **PROVISIONAL** (`✓ (una vía)`) hasta pasar por todos los
   caminos; el `✗`/`~` nombra QUÉ camino cayó (sin ese dato el choque cruzado es
   invisible).
5. **TODO NUDGE:** nada bloquea, ni siquiera el cierre. La skill hace VISIBILIDAD
   (el círculo deja de disfrazarse de progreso) + CONSEJO; el humano decide
   siempre. Decisión explícita del operador: manda en su mesa caliente.

### B. Colapso del vault → catálogo `hotfixs/`
El vault efímero desaparece. `docs/hotfixs/Bug-<frase-corta>.md` (per-repo,
persistente, indexado por SÍNTOMA) es el **único** artefacto: borrador vivo
(WIP-commit por beta → `git show`) Y memoria de largo plazo. Es la **3ª capa de
memoria**: entre el arco (ex-vault) y la Bitácora (patrón cross-repo). El
`modelo-estado:` vive en "Invariantes" del `Bug-` → **PERSISTE** (no se
re-descubre la superficie cada vez): ataca el círculo en la raíz. Templates
single-source en el plugin (`skills/hotfix/templates/`); el skill
**auto-bootstrapea** `docs/hotfixs/` on-demand desde ahí (sin duplicar contenido
en `adoptar-crisol.sh`). Consulta por especificidad: `hotfixs/` primero
(instancia, este repo), Bitácora después (patrón). Un `Bug-` que recurre como
CLASE se cosecha a la Bitácora (instancia → patrón).

## Lo que NO es
- **No suspende ni endurece la ley:** sigue siendo ACTIVE+wip; cero candados
  nuevos (todo nudge).
- **No infla el carril barato:** un hotfix de un solo control lee de largo todo
  lo anti-círculo (gateado en ">1 control").
- **No corre solo:** sin operador presente no hay veredictos.

## Consecuencias
- (+) El círculo deja de ser invisible: nombrado en la evidencia, imposible de no
  ver — el lever real contra la frustración de iterar en círculos.
- (+) El mapa de controles persiste por-repo → el próximo hotfix del mismo estado
  arranca con los controles ya enumerados.
- (+) Un solo artefacto (`Bug-`) = borrador + memoria; sin duplicación
  vault↔catálogo; resuelve de paso la colisión de nombres `_hotfix`↔`hotfixs`.
- (−) El `SKILL.md` crece de 175 a 232 líneas (~+33%) — costo real del rediseño;
  aceptado por el operador (la voz "explica el porqué" se preserva; todo lo pesado
  gateado en >1 control).
- (=) Endoso humano intacto: veredicto por beta, "resuelta+verificada" solo con
  confirmación del humano.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v1.41.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.
