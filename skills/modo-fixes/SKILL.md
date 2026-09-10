---
name: modo-fixes
description: Diferir el portón (mutantes, CI, aceptación) a la autorización del humano, con el pendiente a la vista. Usar cuando REGLAS.md diga PORTON=bajo-autorizacion o el humano pida modo fixes.
---

# Modo fixes

Que el portón del repo — mutantes, la suite en contenedor, el build del CI,
la aceptación contra un servicio real — corra cuando el humano lo autoriza
y no por cada cambio; que mientras tanto se mida con lo barato; y que lo que
no corrió quede escrito y a la vista, nunca supuesto.

Nació de dos frases del humano. La regla, en `REGLAS.md` de lucky-tool-mtk-chr
(2026-09-08): *"no correr portón ni mutantes mientras aplicamos cambios. se
aplican solo en casos grandes y bajo mi autorización"*. Y el pedido de la
skill (2026-09-09): *"desabilitarlos a voluntad para acelerar el proceso de
desarrollo, por fixes o cambios o test de features: no hace falta correr
toda la guarda ni la automática del harness ni las que correspondan"*. La
frontera es la suya: caso grande, portón; lo demás, barato. Medido el
2026-09-08 en ese repo: en una sesión el portón corrió seis veces — unos 50
minutos de espera — y ninguna de las tres fallas que encontró lo necesitaba:
dos las daba un pytest del archivo tocado, la tercera una reversión a mano.

## Declaración

El modo se declara por repo en `REGLAS.md`, bajo la órbita de
`cargar-reglas`, con una línea `PORTON=bajo-autorizacion` y un bloque al
lado que dice, con comandos literales, qué es el portón y qué es lo barato
en ese repo. Sin la línea, el modo está apagado y el portón corre como cada
skill manda.

```markdown
## Cuándo se corre el portón

PORTON=bajo-autorizacion
- Declarado por el humano el <fecha>: "<sus palabras>".
- PORTON= <comandos caros, literales, con su costo medido>
- BARATO= <comandos que dan la señal en segundos, literales; corren en el
  TARGET declarado, no donde caiga>
- CI= <rama que el workflow escucha, o NINGUNA>
```

En caliente, en la sesión: "modo fixes on" / "modo fixes off". Lo dicho en
la sesión vale más que el archivo; un "off" sostenido de forma estable
propone actualizar la línea, para que la regla no se pierda. En un repo sin
la línea y con el pedido en caliente, la sesión nombra en una línea lo que
hace de portón en ese repo, leyéndolo de su CI y su Dockerfile, y espera:
no escribe `REGLAS.md` por su cuenta.

Antes de diferir un portón, conviene medirlo: el costo de un arnés de
mutación es por proceso (arrancar el intérprete e importar), no por test;
si el import domina, se paraleliza con una copia del árbol por trabajador
(ficha del saber CAP-d74a57d6a39c). Es recomendación, no requisito: en
mtk-chr se paralelizó y el portón sigue costando ocho minutos.

## Invariantes

- **Cadencia, no contrato.** El modo cambia CUÁNDO se invoca el portón; no
  afloja ninguna compuerta. Humano, 2026-09-08: *"esto NO afloja las dos
  compuertas del Dockerfile, que siguen rigiendo: si la suite o los
  mutantes no crean su marcador, no hay imagen. Lo que cambia es la
  CADENCIA con la que la sesión las invoca, no el contrato"*. Nada se toca
  en código para que el modo "pase".
- **Declarado, no silencioso.** El modo existe porque está escrito en
  `REGLAS.md` o porque el humano lo pidió en esta sesión, y se ve en cada
  cierre de tramo. Apagar el portón sin declararlo es rebajar un gate, y
  eso lo prohíbe `cambio`. La diferencia entre las dos cosas es la línea
  escrita.
- **Lo barato no es portón, y no se difiere.** Un CI que corre la suite y el
  linter en segundos, sin servidor ni credenciales, es lo barato aunque
  viva en un workflow: sigue corriendo en cada push y sigue frenando.
  Humano, 2026-09-10: *"esas suites ayudan al desarrollo y cuestan menos que
  un portón"*. El portón es lo caro que el repo declara en `PORTON=`
  (mutantes, build de imagen, aceptación contra un servicio real). Medido:
  en gns3 el modo neutralizó el CI barato (los jobs corrían sin tumbar el
  run) por leer "guardas y portones" como si fueran lo mismo; no lo son, y
  el bloque de `REGLAS.md` los separa a propósito.
- **Se difiere, no se recorta.** El portón corre entero cuando corre.
  Recortar cobertura para ganar minutos paga con lo único que el portón
  aporta. Acelerarlo es otro trabajo, con su propio cambio.
- **Lo barato es obligatorio.** Mientras el portón espera, cada cambio se
  mide con lo que el repo declaró como barato: el test dirigido al archivo
  tocado y la suite local, siempre; y la reversión a mano cuando el cambio
  agrega o toca una guarda — humano: *"reversión a mano de la guarda
  nueva"* —, quitarla y ver que el test falla. Sin eso no hay `TESTS=PASS`,
  y sin `TESTS=PASS` no hay cierre de una fase escritora.
- **Una autorización, una corrida.** El humano autoriza correr el portón
  con palabras, en ese momento, para ese tramo. *"Una autorización no se
  hereda al tramo siguiente"*, ni se infiere de la última vez.
- **El push a la rama del CI es la corrida.** Si el repo declara `CI=<rama>`
  y un push a esa rama construye o prueba en el runner, ese push se
  autoriza como el portón, y su resultado se lee — con el comando, no
  supuesto — antes de seguir. No se corre el portón local además. Un push
  a una rama que ningún workflow escucha no dispara nada. Con `CI=NINGUNA`,
  el portón corre local, con la misma autorización.
- **Pendiente a la vista; la sesión no pregunta.** Un tramo con el portón
  sin correr cierra `CONDITIONAL` con `PORTON=PENDIENTE`, nunca `FINAL`, y
  queda contado en el estado del repo. La sesión no pide permiso al cerrar
  cada tramo: deja el pendiente escrito y espera a que el humano pida
  correrlo. Es su decisión, "a voluntad".
- **`NO_APLICA` solo sin declaración.** `PORTON=NO_APLICA` únicamente cuando
  `REGLAS.md` no declara `PORTON=`. Con portón declarado, todo tramo queda
  `PENDIENTE` hasta que el humano diga: nadie se exime por el contenido
  del diff. Medido: en mtk-chr el portón mide hasta el README.
- **"Off" vuelve la cadencia, no borra el pendiente.** Al apagar el modo,
  el portón vuelve a correr como cada skill manda, y lo acumulado se salda
  en el próximo cierre.
- **El portón como diagnóstico es señal sobre el cambio.** Humano: *"si un
  cambio parece necesitar el portón para saber si está bien, eso es una
  señal sobre el cambio: se parte en tramos que se puedan medir barato"*.
- **La elección es del humano, siempre.** La sesión no propone entrar en
  modo fixes ni escribe `PORTON=` en `REGLAS.md` por su cuenta. Si cree
  que el portón está caro, lo dice en una línea con la medición y espera.
- **Jurisdicción.** Qué se mide lo dice cada repo en su bloque; cómo se
  cierra, `cierre` (el campo `PORTON=` es suyo, acá no se repite). Los
  hooks asesores del harness no son el portón: `configurar-hooks`, sin
  cambio. Un Crisol es el caso grande y cierra igual: `CONDITIONAL` hasta
  que el portón corra. Un deploy pasa por el portón siempre: `desplegar`
  no promueve un `CONDITIONAL` por portón pendiente. `hotfix` no enciende
  este modo: una urgencia trae su propia validación y rollback.

## Estado

El acumulado vive en `.lifecycle/state/modo-fixes.env`, versionado: viaja
con la rama, lo ve la próxima sesión y el humano lo ve en el diff.

```text
FORMAT_VERSION="1"
MODO=ON|OFF
DECLARADO_EN=REGLAS.md|SESION
PENDIENTES=<n>
TRAMO_1="<fecha> <commit> <qué se midió barato>"
ULTIMO_PORTON="<fecha> PASS|FAIL human:<id>"
```

Lo escribe la sesión en cada cierre con `PORTON=PENDIENTE` (suma el tramo)
y en cada corrida del portón (pendientes a cero, `ULTIMO_PORTON`). Es para
el que encendió el modo hace tres días y se olvidó.

## Flujo

1. Resolver el estado: el pedido del humano en la sesión manda; si no hubo,
   la línea `PORTON=` de `REGLAS.md`; si tampoco, `MODO_FIXES=OFF` y esta
   skill no actúa. Leer `.lifecycle/state/modo-fixes.env` si existe.
2. Con el modo encendido, en cada cambio: correr lo barato que el repo
   declaró, y anotar en el recibo qué comandos corrieron y qué portón no
   corrió. No correr `docker build`, mutantes ni el CI por cuenta propia.
3. Al cerrar un tramo: `PORTON=PENDIENTE`, `CLOSURE=CONDITIONAL`, la
   condición en `CONDITIONS` con forma fija `PORTON pendiente: <comando>;
   autoriza human:<id>`, y el tramo sumado a `modo-fixes.env`. No preguntar.
4. Cuando el humano autoriza: correr el portón entero — el push a la rama
   del CI y leer el run, o el comando local con `CI=NINGUNA` — y registrar
   la corrida como un cambio propio: observe → close `FINAL` con
   `PORTON=CORRIDO`, citando los tramos que salda; pendientes a cero. Si
   falla, no hay `FINAL`: se abre el cambio que corresponda.
5. Ante "modo fixes off": confirmar en una línea y decir cuántos tramos
   siguen pendientes. El portón vuelve a correr como cada skill manda y
   salda lo acumulado en el próximo cierre.

## Salida

Se emite sólo cuando la skill actúa: al encender o apagar el modo, al
cerrar un tramo con portón pendiente, y al correr el portón. Al inicio de
sesión se emite sólo si hay pendientes o el estado cambió; bajo un modo
vigente y estable, en medio de un tramo, no se emite nada.

```text
MODO_FIXES=ON|OFF
DECLARADO_EN=REGLAS.md|SESION
PENDIENTES=<n>
MEDIDO_BARATO=<comandos corridos|NONE>
AUTORIZADO_POR=human:<id>|NINGUNO
RECEIPT=...
```
