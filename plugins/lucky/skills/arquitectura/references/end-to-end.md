# Una feature de punta a punta (las 4 lentes en un solo caso)

> Leé esta capa cuando preguntás "¿dónde va esto?" y querés ver UNA feature
> ubicada en todas las capas a la vez. Caso 100% placeholder y agnóstico de
> lenguaje — adaptá nombres a tu stack. Es el antídoto contra el purismo: muestra
> qué archivo NACE en cada capa y qué NO se toca.

## La feature de ejemplo: `<confirmar-pedido>`

Un usuario aprieta "confirmar" en una pantalla; el sistema confirma el
`<Pedido>`, lo persiste y notifica. Recorré la pieza por capa.

```
[FRONTEND — atomic]                          archivo que NACE
  pages/<confirmar-pedido>/                   ← página: orquesta estado, llama api/
    └─ usa organismo <BotonConfirmar> (ya existe)   NO se toca el organismo
  api/<pedidos>.<cliente>                     ← función nueva confirmarPedido(id)
      │  (base-url por API_BASE_URL — 12-factor, NO hardcode)
      ▼ HTTP
[BACKEND — MVC = adaptador de entrada]
  adaptadores/entrada/http/<pedido>.controller ← traduce request → caso de uso
      │  (cero regla de negocio acá)
      ▼ invoca
[NÚCLEO — puerto de entrada]
  <nucleo>/puertos/entrada/ParaConfirmar<Pedido> ← interfaz (contrato)
      ▼ implementado por
  <nucleo>/aplicacion/casos_de_uso/confirmar-<pedido> ← caso de uso NUEVO
      │  depende SOLO de puertos
      ├─ usa entidad <Pedido>.confirmar()     (núcleo, ya existe)
      ▼ necesita persistir → llama
[NÚCLEO — puerto de salida]
  <nucleo>/puertos/salida/<Pedido>Repositorio ← interfaz (ya existe)
  <nucleo>/puertos/salida/Notificador          ← interfaz (ya existe)
      ▼ implementados por
[BORDE — adaptadores de salida]
  adaptadores/salida/persistencia/<tec>/<pedido>.repositorio  (ya existe)
  adaptadores/salida/mensajeria/<tec>/notificador             (ya existe)
[COMPOSITION ROOT]
  cablea el caso de uso nuevo con los adaptadores existentes; lee config (12-factor)
```

## Qué nace y qué NO se toca (la lectura Open/Closed)

| Capa | NACE en esta feature | NO se toca |
|---|---|---|
| Frontend | página `<confirmar-pedido>`, función `api/` | el organismo `<BotonConfirmar>`, los átomos |
| MVC entrada | método en `<pedido>.controller` | el router base, otros controllers |
| Núcleo | caso de uso `confirmar-<pedido>` (+ puerto de entrada) | entidad `<Pedido>` (si ya tiene `confirmar()`), puertos de salida existentes |
| Borde salida | nada (reusa repos/notificador existentes) | los adaptadores ya escritos |
| Composition root | una línea de wiring del caso nuevo | el wiring existente |

> La feature **agrega** una unidad por capa y **compone**; el corazón estable no
> se edita. Si para confirmar tuvieras que editar la entidad `<Pedido>` estable,
> es uno de los 3 casos legales del Crisol §2 (bug / abrir costura en corrida
> propia / cambio de contrato con ADR) o es `REJECT`.

## Las 4 lentes, vistas en este caso

- **Hexagonal:** el caso de uso depende de puertos; los adaptadores apuntan al
  núcleo; la flecha nunca sale del núcleo.
- **MVC-entrada:** el controller solo traduce; cero regla de negocio en el
  adaptador.
- **Atomic:** solo la página cruza al backend (vía `api/`); el organismo recibe
  datos/callbacks por props.
- **12-factor:** `API_BASE_URL` es un nombre inyectado; cero dominio/valor real
  en el código.

> Proyecto sin frontend propio (API-only/CLI/worker): borrá la franja
> "FRONTEND" — el resto del recorrido es idéntico. Proyecto en tier plano (MVC):
> el controller llama directo a un servicio→DB, sin puertos; ver
> `references/migracion.md`.
