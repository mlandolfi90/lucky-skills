# Esqueleto parametrizable (copiar al adoptar)

> **Esto NO es un mapa: son ROLES arquitectónicos.** Los nombres entre `<…>` los
> DESCUBRÍS o PARAMETRIZÁS por proyecto. Las carpetas son roles, no nombres
> obligatorios literales. El sufijo de tipo (`.ts`/`.py`/`_test`/`Impl`) lo pone
> tu lenguaje. Lo innegociable es la **dirección de la dependencia** y la
> **separación de capas**, no este árbol al pie de la letra. Antes de crear nada:
> corré la **regla de tier** (`references/migracion.md`) — si da MVC plano, NO
> uses este árbol completo.

```
<raiz-del-proyecto>/
├─ <src>/                       # (o app/ lib/ internal/ cmd/ — lo que tu lenguaje use)
│  ├─ <dominio>/                # NÚCLEO — un bounded context por dominio. PURO.
│  │  ├─ dominio/               # entidades, value-objects, eventos, reglas
│  │  ├─ aplicacion/            # casos de uso (1 archivo = 1 caso de uso) + dto
│  │  └─ puertos/
│  │      ├─ entrada/           # driving — interfaces que el mundo invoca
│  │      └─ salida/            # driven — <Entidad>Repositorio, Reloj, Notificador
│  ├─ <adaptadores>/            # TODO lo sucio. El núcleo NO conoce esta carpeta.
│  │  ├─ entrada/               # driving adapters
│  │  │   ├─ http/              # ← MVC ENTRA ACÁ: controllers, routes, presenters, middlewares
│  │  │   ├─ cli/               # comandos
│  │  │   └─ eventos/           # consumers de cola/bus
│  │  └─ salida/                # driven adapters — IMPLEMENTAN un puerto de salida
│  │      ├─ persistencia/<tecnologia>/   # mappers + migraciones (gate DDL del Crisol)
│  │      ├─ gateways/<proveedor>/         # cliente de SDK/API externa
│  │      └─ mensajeria/<tecnologia>/      # publisher/notifier concreto
│  ├─ <composition-root>/       # único que conoce concretos: wiring + config (12-factor)
│  └─ <shared>/                 # cross-cutting NEUTRAL: errors, result, logger, tipos base
│
├─ <frontend>/                  # si hay UI propia — ATOMIC DESIGN (omitir si API-only/CLI/worker)
│  └─ <src>/
│     ├─ components/ atoms/ molecules/ organisms/
│     ├─ templates/             # esqueleto de layout, sin datos
│     ├─ pages/                 # template + datos reales (responsive: criterio Crisol §2)
│     └─ api/                   # cliente HTTP hacia el backend (la costura)
│
├─ tests/                       # ESPEJA src/: unit (núcleo puro) · integration (adapters) · e2e
└─ docs/
   ├─ decisions/                # ADR NNNN-titulo.md (gate de crédito técnico del Crisol)
   └─ architecture/             # diagrama de contexto, mapa de puertos
```

## La regla del árbol (una sola)

Las flechas de dependencia apuntan SIEMPRE hacia adentro:
`adaptadores → puertos → aplicacion → dominio`. `dominio` no importa a nadie. Si
una carpeta de `adaptadores/` aparece importada desde `<dominio>/` → violación
→ `FAIL` del Verificador.

## Convención de nombres por capa

| Capa | Patrón | Ejemplo (placeholder) | Regla |
|---|---|---|---|
| entidad | `<Sustantivo>` | `<Pedido>`, `<Cliente>` | sustantivo del negocio, sin sufijo técnico |
| value-object | `<Sustantivo>` | `<Dinero>`, `<Email>` | inmutable; nombre = el concepto |
| evento | `<Sustantivo><ParticipioPasado>` | `<Pedido>Pagado` | hecho consumado, en pasado |
| caso de uso | `<verbo>-<sustantivo>` | `confirmar-<pedido>` | imperativo; 1 archivo = 1 caso de uso |
| puerto salida | `<Sustantivo><Rol>` | `<Pedido>Repositorio`, `<Pago>Gateway` | nombre por lo que HACE, NO la tecnología |
| puerto entrada | `Para<Accion>` | `Para<Confirmar><Pedido>` | el contrato que el mundo invoca (interfaz, distinta del caso de uso que la implementa) |
| adaptador salida | `<Sustantivo>.<tecnologia>.<rol>` | `<Pedido>.sql.repositorio` | la TECNOLOGÍA va en el adapter, NUNCA en el puerto |
| adaptador entrada http | `<recurso>.controller` | `<pedido>.controller` | controller delgado, sin lógica de negocio |
| composition | `container`, `config` | — | único con permiso de conocer concretos |
| componente UI | `<Componente>` + carpeta por nivel | `<Boton>`, `<TablaPedidos>` | el NIVEL lo da la carpeta, no el nombre |
| test | `<unidad>.<spec\|test>` | `confirmar-<pedido>.spec` | espeja la ruta de lo que prueba |

**Lo no negociable del naming:** (1) la tecnología SOLO aparece en
`adaptadores/` y en el nombre del adapter — jamás en núcleo, puerto, dominio ni
caso de uso; (2) usá el idioma del negocio (ubiquitous language) para dominio/
casos de uso, no jerga de framework; (3) el sufijo de tipo lo pone tu lenguaje
— adaptá los ejemplos, no copies la extensión; (4) el puerto de entrada es la
interfaz; el caso de uso es su implementación — en proyectos chicos se colapsan.

## Notas de adaptación

- **Monorepo vs multi-repo:** esta es la estructura POR unidad desplegable. Si
  back y front viven en repos separados, aplicá `<src>/` en uno y `<frontend>/`
  en el otro — no impone monorepo.
- **Lenguajes sin interfaces explícitas** (C, Go, JS sin tipos): un "puerto" se
  expresa con punteros a función, structs o duck typing. Adaptá el mecanismo;
  el invariante es la dirección de la dependencia, no el keyword.
- **Proyecto chico:** colapsá `puertos/entrada` cuando no hay variación (eco del
  criterio del Crisol "donde no hay variación, código simple"). Ver
  `references/migracion.md` (MVH). Los puertos de **salida** del núcleo NO se
  colapsan: los exige la testabilidad.
- **DDL:** las migraciones viven en `adaptadores/salida/persistencia/<tec>/
  migraciones/` — ahí aplica el `MIGRATION_STRATEGY` del Crisol.
