---
name: red-de-desarrollo
description: Tender la red de comprobación de un repo: lo barato en cada push, lo caro con disparador escrito, lo manual declarado, el resultado leído. Usar en un repo nuevo o ante una suite que solo corre a mano.
---

# Red de desarrollo

Que cada comprobación del repo corra sola, en el momento que le toca, y que
alguien lea el resultado. "Una suite que solo corre cuando alguien se acuerda
no es una red" (lucky-tool-gns3, 2026-09-06: 1021 tests y el linter no los
corría nadie salvo a mano, mientras el único workflow construía una imagen).

La red tiene tres hilos, y cada comprobación del repo cae en uno:

- **Barato**: da la señal en segundos, sin servidor ni secretos. Corre en
  cada push y frena. Es lo que ayuda a desarrollar: cuesta menos que un
  portón y se corre cien veces por día.
- **Portón**: lo caro — mutantes, build de imagen, suite en contenedor,
  aceptación contra un servicio desechable. Corre con disparador escrito
  (push a la rama de integración, dispatch, tag) y es lo que `modo-fixes`
  difiere bajo autorización.
- **Manual**: lo que no puede ir al CI porque necesita un servicio vivo con
  estado o credenciales reales. Se declara con su comando y se corre a mano,
  avisado.

Humano, 2026-09-10: *"esas suites ayudan al desarrollo y cuestan menos que un
portón"*. Confundir los hilos cuesta caro en las dos direcciones: un barato
tratado como portón deja de frenar (medido en gns3, `mcp-tests` neutralizado
bajo modo fixes); un portón metido en el hilo barato hace esperar ocho
minutos por cada cambio (medido en mtk-chr). Y una suite que solo vive
dentro del build de la imagen es portón aunque corra en cada push: cuesta
el build entero, y el día que `modo-fixes` difiere el build no frena nada
(medido el 2026-09-10: siete repos de la casa tienen ese dibujo, ver "La
red por stack").

La red es la misma en cualquier lenguaje: tres hilos y las invariantes de
abajo. Lo que cambia por stack es con qué se teje cada hilo — el comando
que da la señal barata, qué archivo es el lock y cómo se lo exige, qué
versiones forman la matriz, dónde suele vivir el portón — y eso está en
"La red por stack", con cada fila marcada medida o hipótesis.

## Invariantes

- **Todo repo tiene su hilo barato, y frena.** Workflow en cada push y PR a
  las ramas de trabajo: formateo y linter, suite con dobles, guardas
  (configuración, fuga), en la matriz de versiones declaradas del
  intérprete o toolchain. Sin secretos, sin servidores: la suite trata a
  `127.0.0.1` como texto. Un job rojo tumba el run; un hilo barato que no
  frena no es red, y un workflow que solo escucha `pull_request` deja cada
  push de la rama de trabajo sin señal. Medido: gns3 `mcp-tests.yml` (push
  y PR a `main` y `dev`, 3.10 y 3.13, ruff + pytest + guarda de
  configuración), netbox `verificar.yml` job `offline` (segundos, sin red).
- **El portón va aparte y con disparador escrito.** Otro workflow, otro job
  o un stage del build, con su costo medido al lado y la rama o el evento
  que lo dispara. Es la línea `PORTON=` del bloque de `REGLAS.md` que
  `modo-fixes` lee; su cadencia la decide ese modo, no esta skill. Una
  suite que corre dentro del build de la imagen (stage `test` del
  Dockerfile) es portón por costo aunque sea barata por contenido: se la
  deja como compuerta del build y se la repite en el hilo barato, en el
  runner, antes del build. Medido: mtk-chr stages `test` y `mutantes` del
  Dockerfile en push a `dev` (~8 min); netbox job `contra-netbox` (levanta
  un NetBox desechable, ~10 min, `timeout-minutes: 30`); gns3 build de la
  imagen del ssh-proxy sin publicar.
- **Lo manual se declara, no se olvida.** Lo que necesita un servicio vivo
  con estado o secretos reales no va al CI: se escribe su comando, qué
  crea y qué borra, y a quién se avisa antes. Medido: gns3
  `scripts/aceptacion_mcp.py` contra GNS3 real, "a mano y avisada"; netbox
  aceptación contra el lab con `NETBOX_ALLOW_WRITES`.
- **El resultado se lee, nunca se supone.** Después de cada disparo, el run
  se lee con el comando (`gh run list`, `gh run view`) antes de afirmar
  nada; tag y deploy solo después de verde leído. Medido: un CI corrió doce
  veces con las tres últimas en rojo mientras dos sesiones escribían "nunca
  corrió"; un `success` con el stage de tests CACHED no ejecutó ningún test
  (saber FALSO-VERDE-006).
- **Versiones exactas; la matriz prueba los extremos, no tu PC.** Pines
  `==` en dependencias y herramientas (arquitectura-configuracion); la
  matriz corre la versión mínima y la máxima declaradas del intérprete o
  toolchain (`requires-python`, `engines.node`, `rust-version`, la etiqueta
  de la imagen base), y cada celda tiene que quedar verde. Sin declaración
  no hay matriz posible: declarar es el primer paso (medido: los dos repos
  Node de la casa no declaran `engines`). Medido: un piso declarado en 3.10
  importaba un módulo que en 3.10 no existe y nadie lo vio hasta que la
  matriz lo corrió; el paquete de auditoría corre 3.10, 3.12 y 3.13 en
  ubuntu y windows, `fail-fast: false`.
- **El lock manda en cada paso.** Donde hay lockfile — `uv.lock`,
  `package-lock.json`, `Cargo.lock`, `go.sum`, el digest de cada imagen en
  un compose — todo comando del CI falla si el lock no corresponde al
  manifiesto, no solo el `sync` donde alguien se acordó de escribir
  `--locked`. El mecanismo es del stack (tabla): una variable del workflow
  entero, un instalador que lo exige solo, o el flag en cada invocación.
  Medido: netbox `UV_LOCKED="1"` como variable del workflow entero.
- **Nombres fijos y un mapa en `config/README.md`.** Los workflows se
  llaman `barato.yml` y `porton.yml`; lo manual se lista en
  `config/README.md` con su comando. El README dice cuál es cada hilo, qué
  dispara cada uno y con qué comando se lee. Un repo donde hay que abrir
  cada workflow para saber qué corre no tiene red tendida: tiene archivos.
  En retrofit, renombrar; la historia de runs queda bajo el nombre viejo, y
  se dice.
- **`modo-fixes` consume esta red, no la arma.** `BARATO=`, `PORTON=` y
  `CI=` del bloque `PORTON=bajo-autorizacion` salen de acá; sin red tendida
  ese bloque se escribe a ciegas.

## La red por stack

Cada fila dice con qué se teje cada hilo en ese stack y si está **medida**
en un repo de la casa (repo y commit) o es **hipótesis**. Una hipótesis se
vuelve medida la primera vez que se tiende en un repo de la casa, y la fila
se corrige con lo que se encontró: la receta no se inventa dos veces. Lo
que no cambia por stack: los tres hilos, el push como disparador del
barato, el run leído, los nombres fijos y el mapa.

- **Python con uv** (`pyproject.toml` + `uv.lock`) — MEDIDO. Barato:
  `uv sync`, `ruff check`, `pytest` con dobles, guarda de configuración.
  Lock: `uv.lock`, exigido con `UV_LOCKED="1"` en el `env:` del workflow
  entero. Matriz: los extremos de `requires-python` en ubuntu; windows
  además cuando el paquete se instala ahí. Portón: aceptación contra un
  servicio desechable, build de imagen. Medido: gns3 `mcp-tests.yml`
  (`ada3c15`), netbox `verificar.yml` (`4672442`), lucky-skills
  `auditoria-mcp.yml` (`44d289c`, 3.10/3.12/3.13 × ubuntu/windows).
- **Python con `requirements.txt` y Dockerfile** — PORTÓN MEDIDO, BARATO
  AUSENTE. Hoy la suite vive dentro del build: el stage `test` corre
  pytest y un test roto rompe la imagen. Eso es portón: cuesta el build
  entero por cambio y, diferido, no deja nada que frene. Barato a tender:
  un job en el runner, antes del build, con `pip install -r
  requirements.txt` (pines `==`), `pip check`, linter y pytest con dobles.
  Lock: el `requirements.txt` pinneado es el lock; `pip check` acusa lo que
  no cierra. Matriz: los extremos de `requires-python`; si no está
  declarado, la versión de la imagen base sola, y declararlo. Portón: los
  stages `test` y `mutantes` del build, con su disparador (mtk-chr: push a
  `dev`, ~8 min). Medido: mtk-chr `build.yml` + Dockerfile (`45809c1`); el
  mismo dibujo, sin hilo barato, en Auth-Plane, Rag, tool-design,
  tool-image, tool-saber y blob-store (inventario del 2026-09-10).
- **Node / TypeScript** — HIPÓTESIS, parcial en la casa. Barato: `npm ci`
  (falla solo si `package-lock.json` no corresponde a `package.json`),
  `npm test`, linter, `tsc --noEmit` si hay TypeScript, y las guardas que
  el repo ya tenga como scripts. Lock: `package-lock.json`, exigido por
  `npm ci`; nunca `npm install` en el CI. Matriz: los extremos de
  `engines.node` con `actions/setup-node`. Portón: build de imagen, e2e con
  navegador. En la casa: Lucky-Estilo `build-tokens.yml` corre `npm ci` y
  `npm run build` en Node 20 y deja fuera `gate:no-break` y
  `check:contrast`, que ya existen como scripts; lucky-tool-debug-feedback
  tiene `"test": "node --test"` y su único workflow construye la imagen.
  Ninguno declara `engines`: sin eso no hay matriz.
- **Rust** — HIPÓTESIS, leída en copia ajena. Barato: `cargo fmt --all --
  --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test
  --locked`. Lock: `Cargo.lock`, con `--locked` en cada `cargo` del CI.
  Matriz: `rust-version` de `Cargo.toml` (el piso) y `stable`, fijados con
  `rust-toolchain.toml`. Portón: benchmarks, build de release,
  cross-compile. Leído en rtkAI (`ci.yml`, copia de `rtk-ai/rtk`): fmt,
  clippy, test, security, semgrep, benchmark y doc-review en un solo
  workflow, pero solo en `pull_request` a `develop` y `master` (un push a
  la rama de trabajo no corre nada), toolchain `stable` sin pin y sin
  `--locked` aunque declara `rust-version = "1.91"`. No medido en un repo
  de la casa.
- **Compose sin código propio** — PARCIAL. Barato: `docker compose config`
  valida el archivo sin levantar nada, más guardas de texto sobre lo que
  el compose no valida. Lock: el digest de cada imagen (`image:
  x@sha256:...`); una etiqueta móvil (`latest`, `1`) es un rango y
  arquitectura-configuracion lo bloquea al integrar. Matriz: no hay
  intérprete; cada servicio es una celda. Portón: build y deploy. Medido:
  Auth-Plane `compose-guard.yml` (guarda: `traefik.docker.network` debe
  ser literal, no `${...}`); LLMS y TDU solo tienen build y deploy: portón
  sin barato.
- **Go y todo lo que no está arriba** — SIN RECETA. Lo esperable en Go:
  `go vet`, `go test ./...`, `golangci-lint`; lock `go.sum` con
  `-mod=readonly`; matriz entre la directiva `go` del `go.mod` y la última
  estable. No hay repo Go en la casa (2026-09-10): la fila se escribe con
  repo y commit la primera vez que se tienda.

## Flujo

1. Inventariar: qué workflows, stages y scripts de comprobación tiene el
   repo, qué dispara cada uno, y qué corre solo a mano. Con `gh run list`,
   cuándo corrió cada uno por última vez y cómo terminó. Anotar el stack:
   qué fila de "La red por stack" aplica y si está medida o es hipótesis.
2. Clasificar cada comprobación en barato, portón o manual por dos
   preguntas: ¿da la señal en segundos? ¿necesita servidor, estado o
   secretos reales? Anotar el costo medido de lo caro. Una suite dentro
   del build cae en portón.
3. Tender el hilo barato con la receta del stack: `barato.yml` en push y
   PR a las ramas de trabajo, con matriz de extremos, pines exactos, lock
   exigido y guardas. Sin `continue-on-error`.
4. Aislar el portón en `porton.yml` (o en el stage del build que ya lo sea),
   con su disparador y su costo escritos en la cabecera.
5. Declarar lo manual en `config/README.md`: comando, qué toca, a quién se
   avisa.
6. Escribir el mapa en `config/README.md` y, si el repo usa `modo-fixes`,
   las líneas `BARATO=`, `PORTON=` y `CI=` de `REGLAS.md`.
7. Disparar la primera corrida, leerla con el comando, y anotar el
   resultado. La primera corrida siempre encuentra algo (medido en gns3:
   `scripts/` nunca se había lintado, diez errores y tres scripts muertos
   del upstream). Si la fila del stack era hipótesis, corregirla acá con
   repo y commit.

## Salida

```text
RED=TENDIDA|PARCIAL|AUSENTE
STACK=<fila de la tabla · MEDIDO|HIPOTESIS>
BARATO=<workflow · disparador · jobs · matriz|NINGUNO>
PORTON=<workflow o stage · disparador · costo medido|NINGUNO>
MANUAL=<comando · aviso|NINGUNO>
FRENA=SI|NO
LECTURA=<comando y último run leído|SIN_LEER>
MAPA=config/README.md|AUSENTE
RECEIPT=...
```

`RED=TENDIDA` exige `FRENA=SI`, `LECTURA` con un run leído y `MAPA`
presente. Sin hilo barato, `AUSENTE` aunque haya un portón: un repo con
mutantes y sin linter en cada push no tiene red, tiene un portón solo; y
un repo cuya única suite corre dentro del build tampoco.

## Referencia viva

Medido, anclado en commits: lucky-tool-gns3 `mcp-tests.yml` (`ada3c15`,
barato con matriz y guarda; aceptación manual declarada); Lucky-tool-NetBox
`verificar.yml` (`4672442`, dos jobs: `offline` barato y `contra-netbox`
portón con servicio desechable, `UV_LOCKED`); lucky-tool-mtk-chr
`build.yml` + Dockerfile (`45809c1`, portón como stages del build);
lucky-skills `auditoria-mcp.yml` (`44d289c`, matriz 3.10/3.12/3.13 ×
ubuntu/windows scopeada a `packages/`); Lucky-Auth-Plane
`compose-guard.yml` (guarda barata sobre el compose). Inventario del
2026-09-10 sobre los repos de la casa: hilo barato ausente con el portón
dentro del build en mtk-chr, Auth-Plane, Rag, tool-design, tool-image,
tool-saber y blob-store; solo build en debug-feedback, LLMS y TDU; Node
sin suite ni guardas en el hilo en Lucky-Estilo; Rust leído en rtkAI
(copia ajena). Ninguno usa todavía los nombres fijos: es el primer retrofit
de esta skill.
