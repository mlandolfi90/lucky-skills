# Catálogo de anti-patrones (transversal, una sola vez)

> Leé esta capa cuando dudes si algo es un smell. Catálogo único de los
> anti-patrones estructurales que el Verificador rechaza, agnóstico de lenguaje:
> **síntoma → por qué rompe → veredicto.** Las capas referencian acá por nombre;
> no duplican. Open/Closed de la propia skill: sumar un anti-patrón = una fila,
> sin tocar el SKILL.md.

## Núcleo y puertos (hexagonal)

| Anti-patrón | Síntoma | Por qué rompe | Veredicto |
|---|---|---|---|
| Núcleo enchufado | el núcleo importa el ORM/driver/SDK/framework | DIP invertida: la flecha sale del núcleo | `REJECT` |
| Modelo anémico mal ubicado | "entidad" sin reglas que extiende la clase base del ORM | es persistencia disfrazada, no dominio | `REJECT` |
| Switch que crece en lo estable | `if tipo=="A"... elif "B"...` que se amplía en una unidad estable para sumar comportamiento | modificás lo cerrado (OCP) | `REJECT` (→ polimorfismo/registro) |
| `new` adentro del núcleo | `new RepoSql()` instanciado DENTRO del núcleo | el núcleo elige la impl concreta | `REJECT` (→ inyectar en composition root) |
| Puerto que filtra tecnología | el puerto devuelve un `Row` del ORM o recibe una `connection` | el detalle se cuela al núcleo | `REJECT` |
| Puerto que nombra infra | `GuardarEnPostgres` en vez de `RepoPedidos` | la flecha apunta para afuera | `REJECT` |
| Puerto-Dios | una interfaz con 12 métodos que nadie implementa entera | ISP roto — instancia hexagonal de `INTERFACE_SEGREGATION` (Crisol §2/§5) | `REJECT` (→ partir por capacidad) |
| Generalidad especulativa | puerto con 1 implementación y cero variación prevista (que NO es salida del núcleo) | abstracción sin demanda = deuda | `FAIL` salvo justificación |
| Estado global mutable nuevo | singleton/variable de módulo que muta entre capas | rompe inyección y testeo aislado | `REJECT` |

## MVC / adaptador de entrada

| Anti-patrón | Síntoma | Por qué rompe | Veredicto |
|---|---|---|---|
| Controller gordo | el controller valida reglas, arma queries o decide flujo de dominio | lógica de negocio atrapada en el adaptador | `REJECT` |
| Entidad cruda en la vista | la vista serializa la entidad de dominio directo | filtra el dominio al transporte; acopla | `REJECT` (→ DTO/view-model) |
| "Tengo MVC = soy hexagonal" | hay controllers/models/views pero el Model está soldado al ORM | falta partir el Model y meter puertos | `REJECT` |

## Frontend (atomic)

| Anti-patrón | Síntoma | Por qué rompe | Veredicto |
|---|---|---|---|
| Dependencia al revés | un átomo importa una molécula/organismo | dirección de dependencia rota | `FAIL` |
| Fetch bajo la página | un organismo/molécula llama a `api/` o hace fetch | rompe el aislamiento del backend | `FAIL` |
| Estado de dominio en organismo | el store global vive dentro de un organismo | reintroduce el acoplamiento que el árbol evita | `REJECT` |
| Design-system upfront | librería de componentes para un front chico sin demanda | generalidad especulativa | `FAIL` salvo justificación |
| URL real hardcodeada | dominio/endpoint fijo en vez de `API_BASE_URL` | zero-leak + 12-factor | `FAIL` |

## 12-factor (transversal)

| Anti-patrón | Síntoma | Por qué rompe | Veredicto |
|---|---|---|---|
| Valor de entorno hardcodeado | IP/dominio/puerto productivo en el código | F-1 | `REJECT` |
| Secreto en el repo | token/password/connection-string con valor | F-2 + zero-leak | `FAIL` |
| Estado de proceso persistente | asume "el mismo proceso atiende la próxima request" | F-4 (no sobrevive a `kill -9`) | `REJECT` |
| Log a path fijo | la app abre/rota su propio archivo de log | F-5 | `REJECT` |
| Rebuild para promover | se recompila código distinto del que pasó testing | F-3 (se promueve lo que se probó) | `REJECT` |

> Excepción legal (igual que Crisol §2): tocar lo estable vale SOLO si es (a)
> bug, (b) refactor de costura en corrida propia, o (c) cambio de contrato con
> ADR + tier completo. Fuera de esos 3 casos, los veredictos de arriba mandan.
