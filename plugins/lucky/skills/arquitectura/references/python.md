# Python — reglas idiomáticas

> Curado y traducido de ECC `rules/python/` + el oro portable de
> `rules/python/fastapi.md` (github.com/affaan-m/ECC, MIT) — 2026-07-09.
> **Extiende `reglas-comunes.md`**: acá SOLO lo idiomático de Python; lo
> transversal (inmutabilidad, boundaries, TDD, review) vive allá.
> Toolchain = recomendación (estándar de facto), no ley.

## Estilo

- **PEP 8** + **type annotations en TODAS las firmas** de función pública.
- **Inmutabilidad idiomática:**
  ```python
  from dataclasses import dataclass

  @dataclass(frozen=True)
  class Config:
      host: str
      port: int
  # MAL: config.port = 8080  (FrozenInstanceError — y eso es el punto)
  # BIEN: nueva = dataclasses.replace(config, port=8080)
  ```
  `NamedTuple` para records chicos inmutables.
- **Toolchain recomendado:** `black` (formato) · `isort` (imports) · `ruff`
  (lint). Una config, cero debates de estilo.
- **`logging`, JAMÁS `print()`** en código de producción (niveles, contexto,
  y se puede redirigir/silenciar).

## Patrones

- **`Protocol` para duck typing estructural** (el "puerto" hexagonal sin
  herencia):
  ```python
  from typing import Protocol

  class Repository(Protocol):
      def find_by_id(self, id: str) -> Entity | None: ...
      def save(self, e: Entity) -> None: ...
  # el núcleo tipa contra Repository; el adaptador lo implementa sin heredar
  ```
- **Dataclasses como DTOs** en los boundaries (`CreateUserRequest`), separados
  del modelo de dominio.
- **Context managers (`with`)** para TODO recurso (archivos, conexiones,
  locks); **generators** para colecciones grandes/lazy (memoria O(1)).

## Testing

- **pytest** · cobertura: `pytest --cov=src --cov-report=term-missing`.
- Categorizar: `@pytest.mark.unit` / `@pytest.mark.integration` (el CI puede
  correr capas separadas).

## Seguridad

- Secretos: `os.environ["API_KEY"]` (revienta con `KeyError` si falta — eso es
  fail-fast, no un bug) + `.env` SOLO en dev vía `dotenv`.
- **`bandit -r src/`** en el CI: análisis estático de seguridad.

## Diseño de API (oro portable, nacido en su regla de FastAPI)

- **JAMÁS incluir en un response model:** passwords, hashes, access/refresh
  tokens, ni estado interno de auth. El schema de SALIDA es una allow-list.
- **Schemas separados** para create / update / response (nunca reusar el de
  entrada como salida).
- **Handlers/routers DELGADOS:** el negocio y la persistencia viven en
  services/CRUD; el handler solo orquesta (es el "C" de `mvc-adaptador.md`).
- **CORS:** jamás wildcard de origins con credenciales activas.
- **JWT:** validar expiry + issuer + audience + algoritmo (los cuatro).
- **Logs:** redactar credenciales, cookies y headers de authorization SIEMPRE.
- Rate-limit en auth y en todo endpoint de escritura.
