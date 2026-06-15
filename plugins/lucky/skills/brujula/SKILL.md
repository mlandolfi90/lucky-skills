---
name: brujula
description: >-
  Brújula — ancla la sesión al estado REAL del repo y el deploy para
  evitar alucinar contexto ya superado. Usar AL EMPEZAR a trabajar en un repo,
  al retomar una sesión, o cuando dudes en qué branch/estado estás
  ("¿dónde estoy?", "ubicame", "/brujula"). Lee 4 fuentes reales (git,
  docker, ADR/RUN-LEDGER y, si hay token, la topología del PaaS read-only) y
  devuelve un snapshot objetivo. REGLA DE ORO: si una
  fuente no se puede leer, dice "N/D" — JAMÁS infiere. Solo lectura, no modifica.
allowed-tools: Bash, Read, Glob, Grep
---

# Brújula — ¿dónde estoy parado?

Antes de tocar nada, anclá la sesión a la **verdad del terreno**. El enemigo es
arrancar con suposiciones; esta skill las reemplaza por hechos.

**Ejes:** óptima (ataca la causa, no el síntoma) · compacta · dura (branch
inesperado = bandera roja) · sencilla (invocás y leés) · confiable (fail-closed).

## Uso

Ejecutá el script y mostrale al usuario su salida tal cual:

```bash
bash scripts/brujula.sh
```

## Las 4 fuentes (todas read-only)

1. **Repo** — branch actual, archivos sin commitear, adelanto/atraso vs remote,
   y **último tag** (en promoción-por-tags, el tag ES el estado de release).
   **Trunk-based: lo esperado es `main`**, salvo que el RUN-LEDGER tenga una
   entrada `STATUS: ACTIVE` para otro branch — esa entrada **manda**.
2. **Deploy** — `docker ps` y, si hay compose en el repo, `docker compose ps`.
3. **Decisiones** — último ADR en `docs/decisions/` + estado del Crisol. Si hay
   entrada `ACTIVE` y commits `wip: crisol iter N` recientes → reporta
   **corrida a medias respaldada** (la sesión anterior murió; el trabajo está
   en los WIP-commits).
4. **Topología (PaaS)** — con token disponible, consulta la API del control
   plane (read-only) y reporta SOLO el triplete relevante a esta sesión:
   `<proyecto>/<app>@<env>` (el que matchea el repo en curso), con esta gramática
   canónica del **TARGET**: `paas:<proyecto>/<app>@<env>` | `docker-local` |
   `pc-local` (`<env>` ∈ {`dev`, `testing`, `production`}; **dev** = mesa caliente,
   default de desarrollo). Es *sugerencia*: prefillea el `TARGET:` que el Crisol
   confirma con el humano en su Paso 0. **Nunca lista el inventario completo,
   nunca imprime el token ni dominios/IPs reales: el token se usa, no se vuelca.**
   Sin token, o si la API no responde / no parsea → `N/D` (REGLA DE ORO, igual que
   cualquier fuente).

## Reglas duras

- **Branch ≠ esperado / detached HEAD → bandera roja ARRIBA DE TODO.**
  En trunk-based `main` es lo NORMAL — la anomalía es estar FUERA de `main`
  sin entrada ACTIVE que lo justifique.
- **Fail-closed:** fuente ilegible (sin git, sin docker, sin ADRs, o API del
  PaaS sin token / sin respuesta) → `N/D`.
  Nunca rellena, nunca infiere. Esa es la diferencia entre ubicarse y alucinar.
- **Veredicto de branch binario:** coincide con el esperado, o no. Sin "casi".
- **No modifica nada:** es una brújula, no un timón.

Tras leer el snapshot, NO sigas con suposiciones sobre lo que muestre `N/D`:
pedí el dato o decláralo desconocido.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v1.10.1` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags`), seguir la del repo e informar al humano.
