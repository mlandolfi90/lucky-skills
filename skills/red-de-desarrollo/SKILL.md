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
minutos por cada cambio (medido en mtk-chr).

## Invariantes

- **Todo repo tiene su hilo barato, y frena.** Workflow en cada push y PR a
  las ramas de trabajo: linter, suite, guardas (configuración, fuga), en la
  matriz de versiones declaradas. Sin secretos, sin servidores: la suite usa
  dobles y trata a `127.0.0.1` como texto. Un job rojo tumba el run; un hilo
  barato que no frena no es red. Medido: gns3 `mcp-tests.yml` (push y PR a
  `main` y `dev`, 3.10 y 3.13, ruff + pytest + guarda de configuración),
  netbox `verificar.yml` job `offline` (segundos, sin red).
- **El portón va aparte y con disparador escrito.** Otro workflow, otro job
  o un stage del build, con su costo medido al lado y la rama o el evento
  que lo dispara. Es la línea `PORTON=` del bloque de `REGLAS.md` que
  `modo-fixes` lee; su cadencia la decide ese modo, no esta skill. Medido:
  mtk-chr stages `test` y `mutantes` del Dockerfile en push a `dev` (~8
  min); netbox job `contra-netbox` (levanta un NetBox desechable, ~10 min,
  `timeout-minutes: 30`); gns3 build de la imagen del ssh-proxy sin
  publicar.
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
  matriz corre la versión mínima y la máxima declaradas del intérprete, y
  cada celda tiene que quedar verde. Medido: un piso declarado en 3.10
  importaba un módulo que en 3.10 no existe y nadie lo vio hasta que la
  matriz lo corrió; el paquete de auditoría corre 3.10, 3.12 y 3.13 en
  ubuntu y windows, `fail-fast: false`.
- **El lock manda en cada paso.** Donde hay lockfile, todo comando del CI
  falla si el lock no corresponde al manifiesto, no solo el `sync` donde
  alguien se acordó de escribir `--locked`. Medido: netbox `UV_LOCKED="1"`
  como variable del workflow entero.
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

## Flujo

1. Inventariar: qué workflows, stages y scripts de comprobación tiene el
   repo, qué dispara cada uno, y qué corre solo a mano. Con `gh run list`,
   cuándo corrió cada uno por última vez y cómo terminó.
2. Clasificar cada comprobación en barato, portón o manual por dos
   preguntas: ¿da la señal en segundos? ¿necesita servidor, estado o
   secretos reales? Anotar el costo medido de lo caro.
3. Tender el hilo barato: `barato.yml` en push y PR a las ramas de trabajo,
   con matriz de extremos, pines exactos, lock exigido y guardas. Sin
   `continue-on-error`.
4. Aislar el portón en `porton.yml` (o en el stage del build que ya lo sea),
   con su disparador y su costo escritos en la cabecera.
5. Declarar lo manual en `config/README.md`: comando, qué toca, a quién se
   avisa.
6. Escribir el mapa en `config/README.md` y, si el repo usa `modo-fixes`,
   las líneas `BARATO=`, `PORTON=` y `CI=` de `REGLAS.md`.
7. Disparar la primera corrida, leerla con el comando, y anotar el
   resultado. La primera corrida siempre encuentra algo (medido en gns3:
   `scripts/` nunca se había lintado, diez errores y tres scripts muertos
   del upstream).

## Salida

```text
RED=TENDIDA|PARCIAL|AUSENTE
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
mutantes y sin linter en cada push no tiene red, tiene un portón solo.

## Referencia viva

Medido, anclado en commits: lucky-tool-gns3 `mcp-tests.yml` (`ada3c15`,
barato con matriz y guarda; aceptación manual declarada); Lucky-tool-NetBox
`verificar.yml` (`4672442`, dos jobs: `offline` barato y `contra-netbox`
portón con servicio desechable, `UV_LOCKED`); lucky-tool-mtk-chr
`build.yml` + Dockerfile (`45809c1`, portón como stages del build);
lucky-skills `auditoria-mcp.yml` (`44d289c`, matriz 3.10/3.12/3.13 ×
ubuntu/windows scopeada a `packages/`). Ninguno usa todavía los nombres
fijos: es el primer retrofit de esta skill.
