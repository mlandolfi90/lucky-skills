# TypeScript / JavaScript — reglas idiomáticas

> Curado y traducido de ECC `rules/typescript/` (github.com/affaan-m/ECC, MIT)
> — 2026-07-09. **Extiende `reglas-comunes.md`**: acá SOLO lo idiomático de
> TS/JS; lo transversal vive allá. Toolchain = recomendación, no ley.

## Tipado

- **Tipar las APIs públicas** (funciones exportadas, utils compartidas, métodos
  públicos); dejar que TS INFIERA los locales obvios (tipar `const x: number =
  2` es ruido). Shapes inline repetidos → tipo nombrado.
- **`interface` vs `type`:** `interface` para shapes extensibles/implementables;
  `type` para uniones, intersecciones, tuplas, mapped/utility types.
- **Uniones de string literales > `enum`** (salvo interop que lo exija):
  ```ts
  type Estado = 'pendiente' | 'activo' | 'cerrado';  // BIEN
  enum EstadoEnum { Pendiente, Activo, Cerrado }     // solo si el interop lo pide
  ```
- **`any` está prohibido como salida fácil.** Input externo/no confiable →
  `unknown` + narrowing:
  ```ts
  function getErrorMessage(error: unknown): string {
    if (error instanceof Error) return error.message;
    return String(error);
  }
  ```
  Si el tipo depende del caller → generics, no `any`.

## Validación en el boundary

- **Zod** (o equivalente) en cada entrada externa, e **inferir el tipo del
  schema** — una sola fuente de verdad:
  ```ts
  const UserSchema = z.object({ id: z.string(), email: z.string().email() });
  type User = z.infer<typeof UserSchema>;   // el tipo NACE del validador
  ```

## Inmutabilidad idiomática

- Spread para actualizar (`{ ...user, name }`, `[...items, nuevo]`);
  `Readonly<T>` / `readonly` para congelar contratos.

## React (si aplica)

- Props con `interface`/`type` NOMBRADO; **no usar `React.FC`** salvo razón
  concreta; callbacks tipados explícitos (`onSave: (id: string) => void`).

## Patrones

- **`ApiResponse<T>`** genérico (success + data | error + meta) — la versión
  tipada del envelope de `reglas-comunes.md`.
- **`Repository<T>`** genérico tipado — el puerto de persistencia hexagonal.

## Higiene

- **Cero `console.log` en producción** → logging library (niveles/contexto).
- Secretos: `process.env.API_KEY` con guard de arranque
  (`if (!apiKey) throw new Error('API_KEY faltante')`) — fail-fast, jamás
  hardcodear.
- En `.js`/`.jsx` sin migración práctica a TS: **JSDoc** donde el tipo aporte
  claridad real.

## Testing

- **Playwright** para E2E de los flujos críticos (login, checkout, el camino
  que factura). Unit/integración: heredan `reglas-comunes.md` (AAA, nombres
  conductuales, 80% recomendado).
