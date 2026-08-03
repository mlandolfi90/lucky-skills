# Paquetes de adopción

- **Qué es:** perfiles recomendados de skills según el tipo de repo; las
  dependencias del grafo entran solas en cada transacción.
- **Cuándo:** al adoptar la suite en un repo nuevo o ampliar uno adoptado.
- **Cómo:** elegir el perfil, adoptar skill por skill con el runbook; un
  perfil es punto de partida, no límite.
- **Perfiles:**
  - **Base** (todo repo): disenar, cambio, cierre, logalizar,
    custodiar-secretos, cargar-reglas, ley-viva, arquitectura-verificar —
    el gate de arquitectura (SOLID, abierto/cerrado) no puede depender del
    pack Deploy: un repo base sin él construye registros centrales sin que
    nadie lo frene (caso PizarraEvo, 2026-08-03).
  - **UI** (base +): estilar.
  - **Deploy** (base +): crisol, microfix, hotfix, autopsia, desplegar,
    mapear-despliegue — el carril de calidad y el de despliegue que un repo
    con CI activo usa a diario.
  - **Transición v2** (cualquiera +): podar-v2 para las reliquias.
- **No es:** una instalación monolítica; cada repo carga solo los cajones
  que su taller usa.
- **Ejemplo:** Lucky-Auth-Plane (CI+deploy) quedó corto con Base y pidió la
  segunda tanda Deploy — el origen de este concepto.
