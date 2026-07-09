# Reglas comunes de código (agnósticas de lenguaje)

> Curado y traducido de ECC `rules/common/` (github.com/affaan-m/ECC, MIT) —
> corrida "absorción ECC lote 1", 2026-07-09. Solo el oro atemporal; lo atado a
> su stack quedó afuera. Las hojas por lenguaje (`python.md`, `typescript.md`)
> EXTIENDEN esta base: acá lo transversal, allá solo lo idiomático.
> **Umbrales numéricos = recomendación del catálogo, no ley** — el veredicto por
> corrida lo da el design-verifier (igual que ATOMICIDAD).

## Estilo

- **Inmutabilidad (CRÍTICO):** crear objetos nuevos, jamás mutar in-place.
  Racional: elimina side-effects ocultos, simplifica el debug, habilita
  concurrencia segura.
  ```js
  // MAL: user.name = 'Nuevo'
  // BIEN: const actualizado = { ...user, name: 'Nuevo' }
  ```
- **KISS · DRY · YAGNI, accionables:** no optimizar prematuro; extraer recién
  ante repetición REAL (no especulativa); no construir lo que nadie pidió.
- **Archivos:** muchos chicos > pocos gigantes. Recomendado 200–400 líneas
  (techo ~800). Organizar por feature/dominio, no por tipo técnico.
- **Funciones:** < 50 líneas recomendado; anidamiento máx ~4 niveles; cero
  números mágicos (constante nombrada o config).
- **Naming:** `camelCase` variables/funciones · booleanos con prefijo
  `is/has/should/can` · `PascalCase` tipos/clases/componentes ·
  `UPPER_SNAKE_CASE` constantes.

## Errores y validación

- **Errores explícitos en cada nivel; JAMÁS tragarlos en silencio.** Mensaje
  amigable hacia la UI; contexto completo hacia el log del server.
- **Validar en los BOUNDARIES del sistema** (entrada de usuario, red, disco),
  con schema; **fail-fast**; nunca confiar en data externa.

## Seguridad (checklist pre-commit)

- [ ] Cero secretos hardcodeados (env vars / secret manager; validar presencia
      al arranque; rotar lo expuesto)
- [ ] Todo input validado
- [ ] SQL SOLO parametrizado (jamás concatenación)
- [ ] XSS: HTML sanitizado · CSRF activo en forms
- [ ] authn/authz verificadas en cada endpoint sensible
- [ ] Rate-limiting en endpoints públicos y de escritura
- [ ] Errores que NO filtran datos sensibles

**Disparadores de review de seguridad:** auth, input de usuario, queries a DB,
filesystem, APIs externas, cripto, pagos.
**Protocolo ante hallazgo:** FRENAR → dimensionar → arreglar CRITICAL primero →
rotar secretos → barrer el codebase por el mismo patrón.

## Testing

- **Cobertura mínima recomendada: 80%** · tres tipos: unit, integración, E2E.
- **Ciclo TDD:** RED → GREEN → REFACTOR (el test primero, verlo fallar).
- **Patrón AAA** (Arrange–Act–Assert) por test.
- **Nombres que describen CONDUCTA:**
  `test('devuelve lista vacía cuando ningún mercado matchea la query')` —
  no `test('funciona')`.

## Git

- **Conventional commits:** `<tipo>: <descripción>` (+ body si aporta). Tipos:
  `feat · fix · refactor · docs · test · chore · perf · ci`.
- PR: analizar TODO el rango (`git diff base...HEAD`), no solo el último
  commit; resumen + plan de prueba.

## Patrones transversales

- **Repository:** el acceso a datos detrás de una interfaz
  (`findAll/findById/create/update/delete`); el negocio depende de la
  abstracción, no del storage → swap y mocking triviales. (Es el puerto/
  adaptador de `hexagonal.md` aplicado a persistencia.)
- **Envelope de respuesta de API:** indicador de éxito + `data` (null en
  error) + `error` (null en éxito) + `meta` (total/página/límite) para
  paginación — una sola forma para todo el sistema.
- **Investigar y reusar ANTES de escribir:** buscar implementación existente →
  docs de la librería → web; revisar el registry del ecosistema (npm/PyPI/
  crates) antes de escribir una utilidad; portar algo probado > net-new.

## Review (para el reviewer)

**Checklist:** legible y bien nombrado · funciones <50 · archivos <800 · sin
anidar >4 · errores explícitos · sin secretos · sin `console.log`/prints de
debug · tests presentes · cobertura ≥80%.

**Severidades:**

| Severidad | Acción |
|---|---|
| CRITICAL | BLOQUEA |
| HIGH | ADVERTIR (no aprueba) |
| MEDIUM | INFO |
| LOW | NOTA |

Aprobar ⟺ cero CRITICAL/HIGH.

**Issues que más se escapan:** credenciales hardcodeadas · SQLi por
concatenación · XSS · path traversal · bypass de auth · N+1 queries · listados
sin paginación/`LIMIT` · falta de caché en lecturas calientes.
