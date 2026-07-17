---
id: PLAN-verde-significa-algo-contratos
schema: plan/1
tipo: plan
estado: VIGENTE
creado: 2026-07-17
refs: [corrida:2026-07-17-el-verde-significa-algo, adr:0022, adr:0018]
nota: "FASE PIN — aplicada ANTES de planificar, por el RETRO de equipo-doc-v1 (que gastó 2 de 3 iteraciones descubriendo un ciclo de contratos con el primer REJECT del Steward)"
---
# PIN de contratos — corrida `2026-07-17-el-verde-significa-algo`

Esto es **la lección de ayer aplicada hoy**. El RETRO de
`corrida:2026-07-16-equipo-doc-v1` dice, textual: *"la FASE PIN debería ser el
paso 0 de todo tier completo con >1 carril — fijar los contratos cross-carril
ANTES de mandar a planificar, en vez de descubrir el ciclo con el primer
REJECT"*. Aquella corrida quemó 2 de 3 iteraciones en eso y murió ESCALATED.

Dos carriles: **A (CI)** y **B (RED_GREEN)**. Sus sets de archivos son disjuntos
—`.github/` vs `crisol/SKILL.md` + `agents/`— pero eso NO garantiza nada: el
COLLISION-MAP caza colisiones de ARCHIVO, no de CONTRATO. Los contratos que sí
se tocan, pineados acá:

## PIN 1 — El workflow descubre los tests por GLOB, no por lista · dueño: A

```yaml
# el workflow corre TODO lo que matchee, sin enumerar:
plugins/lucky/skills/*/tests/test-*.sh
```

- **Por qué es contrato:** si A enumera los 13 runners a mano, B (o cualquier
  corrida futura) agrega un test y el CI **no lo corre** — y nadie se entera. Un
  test que el CI no corre es un test que no existe, y habríamos construido el
  runner ajeno para que mienta.
- **B queda libre** de agregar fixtures sin tocar `.github/`. Sin este pin, cada
  test nuevo es una edición cross-carril.
- Corolario para A: si el glob no matchea NADA, el job **falla** — un glob vacío
  que pasa en verde es el falso-verde que esta corrida vino a matar.

## PIN 2 — Quién dictamina `RED_GREEN` · dueño: B

- El ID nuevo vive en el catálogo §5 de `crisol/SKILL.md` (fuente única del
  enunciado, como manda §2/§5) y en el `dictamina:` de **un guardián del roster**.
- **B decide CUÁL guardián y CÓMO se le agrega**, con evidencia: el
  `crisol-quality-auditor` es fila `agente` en estado `LIVE`, y `registros.yaml`
  §6-7 + ADR 0018 §4 dicen que una fila LIVE **no se edita in-place**: evoluciona
  por SUPERSEDE (archivo nuevo + `superseded_by:`). B debe leer el ADR y resolver
  si esto es supersede (`crisol-quality-auditor-2`) o si hay un camino legal más
  barato. **No inventar: citar el ADR.**
- **Si hay supersede → el nombre es contrato**: `crisol/SKILL.md` nombra a los
  guardianes del roster en su tabla §2 y en el paso 6 §4. Igual que ayer con
  `manualizador-2`: el nombre del llamador es el de-ruteo. B toca ambos lados —
  es su carril, no de A.

## PIN 3 — `TEST_COVERAGE: NONE` NO se toca en esta corrida · dueño: B (declarar)

- El alcance ítem 3 dice "revisar". **Revisar ≠ cambiar.** Cambiar la semántica
  de `NONE` altera cuándo una corrida puede emitir PASS: eso es cambio de
  contrato con impacto en toda la flota y **merece su propia decisión del
  operador**, no un arrastre de esta corrida.
- B lo **documenta** en el ADR 0022 como deuda con nombre y lo deja parkeado. Si
  B cree que debe entrar, lo propone al Steward con argumento — no lo hace.

## PIN 4 — El CI NO es un guardián del Crisol · dueño: A

- A construye infraestructura, **no una regla de la matriz**. El CI no dictamina
  ningún ID del catálogo §5 y no escribe líneas `[V]`.
- Relación correcta con la ley: el CI es **el TARGET ajeno que la REGLA 0 ya
  exige** (`crisol/SKILL.md:57-61`), no una regla nueva. A no toca el catálogo.
- Consecuencia: A **no** necesita ADR propio (el 0022 lo cubre), y **no** puede
  reclamar celdas de la matriz.

## PIN 5 — Etiqueta legal de cada carril (para que el Steward no las invente)

- **A = AGREGA sin caso legal.** `.github/` no existe; todo es archivo nuevo.
  Ninguna línea existente cambia de comportamiento.
- **B = (c) cambio de contrato → tier completo + ADR**, ya pagado con el ADR 0022
  depositado al abrir. El ID nuevo en el catálogo ES el cambio de contrato.

## Ratificaciones previas que NO se re-litigan

- **Fuera de alcance heredado y confirmado por el operador hoy:** multi-harness,
  pressure-testing de la prosa, gate de mtime, doble voz cross-modelo. Ningún
  plan los mete.
- **El sello pendiente** de `leak-scan-puente` es la ventana normal cierre→forja,
  no un hallazgo. Ningún carril lo "arregla": lo salda la forja de cierre.
- **Citar por ancla de texto, no por número puro** — la otra lección del RETRO de
  ayer, que mató aquella corrida en el último paso. Vale para los dos carriles.
