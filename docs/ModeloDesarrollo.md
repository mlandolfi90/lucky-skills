# Modelo de desarrollo — lucky-skills

> Vista de conjunto (descriptiva). La LEY normativa vive en
> `plugins/lucky/skills/crisol/SKILL.md`; este doc solo la ata en un cuadro y
> apunta a la sección que manda. **Si algo acá choca con el skill, manda el skill.**

El desarrollo acá NO es un roadmap de tareas: son **dos loops acoplados**. El interno
**forja** un cambio verificado (calidad incorporada); el externo lo **promueve** a
producción (entrega controlada). El empalme entre ambos es el `commit`.

---

## Loop interno — forja (kaizen / jidoka)

Cómo **nace** un cambio, antes de tocar `dev`. Fuente: `crisol/SKILL.md` §1–§4.

1. **brújula** — anclar al estado real del repo/deploy (no alucinar contexto).
2. **TARGET** — declarar/confirmar DÓNDE corre y se verifica (Paso 0). Sin esto el gate
   bloquea. Esquema: `paas:<proyecto>/<app>@<env>` | `docker-local` | `pc-local`
   (`pc-local` solo si el humano lo pide explícito; jamás asumir local).
3. **Tier** — clasificar: `fast-path` (mini) o `completo`.
4. **RUN-LEDGER ACTIVE** — abrir la corrida (campos mínimos: STATUS / Tier / Fecha / TARGET).
5. **Carriles** — Planificador → Architecture Steward (COLLISION-MAP) → Ingeniero →
   **Verificador independiente** (contexto fresco; corre los tests ÉL MISMO, EN el TARGET).
6. **Techo de 3 iteraciones** — `FAIL`/`REJECT` → vuelve a planificar. Al 4º → `ESCALATED`,
   decide el humano. No ciclar infinito, no hot-patch.
7. **PASS → commit → cierre del ledger** (`STATUS: CLOSED` + `RETRO`).

## Loop externo — promoción por environment (CD)

Cómo **viaja** ese commit a producción. Fuente: `crisol/SKILL.md` §Versionado.

- Trunk-based: una sola rama `main`. **El entorno lo decide el TAG, no la rama.**
- `push` = respaldo → cae en **dev** (mesa caliente; se itera en vivo, sin culpa).
- `tag vX.Y.Z-rcN` → **testing** (promoción deliberada; candidato a release).
- `tag vX.Y.Z` → **producción** (release estable; nace SOLO tras una corrida `PASS`).
- Se promueve el **mismo commit** que pasó testing. Tags **inmutables**; `latest` es el
  único puntero móvil. **Rollback** = re-deploy del tag estable anterior.
- testing/prod **no se tocan a mano**: si algo falla ahí → vuelve a dev (corrida nueva,
  fix-forward); la corrida `CLOSED` no se reabre.

---

## El cuadro

```
  LOOP INTERNO — forja (kaizen)                LOOP EXTERNO — promoción (CD)

  brújula → TARGET → Tier → ledger ACTIVE
     → Plan → Steward → Ingeniero
     → Verificador (corre tests EN el TARGET)
            │
            │ PASS                  commit
            ▼               ── push ──►  DEV ──tag -rcN──►  TESTING ──tag vX.Y.Z──►  PROD
        commit + cierre              (mesa caliente)                            (estable)
            ▲                              ▲                                        │
       FAIL/REJECT                         └─────────── rollback = tag anterior ────┘
      (máx 3 → ESCALATED)

  RETRO + PARKED (docs/IDEAS.md)  ───────────►  realimentan corridas futuras
```

El **TARGET** aparece en los dos loops: se declara en la forja y se respeta en cada
promoción (la verificación corre en el entorno fiel, no en la PC local). Desde **v1.11.0**
esto está enforced por el gate global (`crisol_gate.py`), no solo documentado.

---

## Realimentación (de dónde sale el "qué sigue")

No hay backlog separado: el próximo trabajo **emerge** de
- `docs/IDEAS.md` — parking lot de candidatas.
- `docs/refactor/_crisol/RUN-LEDGER.md` — los `RETRO` y `PARKED` de cada corrida.
- Regla kaizen: ~3 `RETRO` apuntando a la misma regla → se abre una corrida sobre la
  **propia ley** (`crisol/SKILL.md` §6: la ley se gobierna a sí misma, vN juzga vN+1).

## Dónde manda cada cosa (fuente de verdad)

| Tema | Archivo |
|---|---|
| Reglas de la forja (loop interno) | `plugins/lucky/skills/crisol/SKILL.md` §1–§4 |
| Promoción por environment (loop externo) | `plugins/lucky/skills/crisol/SKILL.md` §Versionado |
| Estado real del repo/deploy | skill `brujula` |
| Backlog / ideas | `docs/IDEAS.md` |
| Bitácora de corridas | `docs/refactor/_crisol/RUN-LEDGER.md` |
| Decisiones estructurales | `docs/decisions/` (ADR) |
