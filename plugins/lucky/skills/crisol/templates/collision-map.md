# COLLISION-MAP — corrida Crisol `<run-id>`

> Lo emite el **Architecture Steward** (paso Arquitecto) ANTES de que cualquier
> Ingeniero toque código. Previene la colisión cross-carril (poka-yoke).
> Plantilla — copiar a `docs/refactor/_crisol/COLLISION-MAP.md` por corrida.

- **Run-id:** `<YYYYMMDD-HHMM-branch>`
- **Fecha:** `<YYYY-MM-DD>`
- **Carriles activos:** `<dominio-A>`, `<dominio-B>`, ...

## Superficies calientes (tocadas por >1 carril o compartidas)

| Archivo / contrato | Carriles que lo tocan | Tipo | Resolución |
|---|---|---|---|
| `docker-compose.yml` | A, B | COMPARTIDO | Lo administra el team-lead; engineers NO lo tocan directo |
| `docs/contracts/amqp-contracts.md` | B | CONTRATO | Requiere versionado (ADR 0008) |
| `<ruta>` | A, C | SOLAPADO | **Serializar:** C espera a que A cierre carril |
| `<ruta>` | A | AISLADO | Sin conflicto — paralelo OK |

## Orden de serialización impuesto

1. Carriles sin solape → arrancan **en paralelo**.
2. `<carril>` espera a `<carril>` por `<archivo>`.
3. Archivos compartidos → cola administrada por el team-lead.

## Veredicto del Arquitecto

- `APPROVE` / `REJECT`
- Si `REJECT` (= 🚨 VETO): motivo + 1-2 soluciones estructurales concretas.
  No se crea ADR ni se edita ARCHITECTURE.md hasta resolver.
