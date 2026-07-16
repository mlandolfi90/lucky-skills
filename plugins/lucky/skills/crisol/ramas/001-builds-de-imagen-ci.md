---
id: 001-builds-de-imagen-ci
schema: rama/1
tipo: rama
estado: LIVE
canal: estable
creado: 2026-07-16
skill: crisol
gatillo: "el artefacto del deploy es una IMAGEN (Dockerfile, multi-stage) y hay que satisfacer la REGLA 0"
origen: "extraída del tronco crisol §2 (ley ya endosada que solo se muda — nace estable, ADR 0018 §2)"
ultima_validacion: corrida:2026-07-16-ramas-agentes-canonicos
refs: [adr:0018]
---
# Builds de imagen — el gate-test va HORNEADO en el CI, no en el VPS

Cuando el artefacto es una imagen (Dockerfile multi-stage), la suite de la
REGLA 0 se **hornea en el stage `test`** que corre DURANTE el build del CI
(runner Linux = entorno fiel del TARGET). El build vive en el CI
(build-once-promote — ver `arquitectura:references/deploy-build-once-promote.md`);
**NO se corre en el VPS de deploy ni se duplica con un pre-build local**
(`scp` + `docker build`): es redundante y carga el server.

El Verificador satisface la REGLA 0 así:
1. Observa el stage `test` VERDE en el CI (gate determinista, no reporte ajeno).
2. Verifica la **provenance**: imagen desplegada == `sha-<commit>` del CI.
3. Suma su verificación **funcional/e2e propia** contra el artefacto desplegado.

Único build legal fuera del CI: minutos de CI agotados (fallback declarado).

---
**Fuente: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.4.0` (cache local, NO la ley).**
