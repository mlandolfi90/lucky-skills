---
name: arquitectura-configuracion
description: Ningún valor de configuración en el código; cada uno llega por un contrato declarado. Usar al crear o revisar la configuración de un servicio, o ante un literal de host, puerto, ruta o tiempo.
---

# Arquitectura: configuración

Ningún valor de configuración vive en el código. Cada uno llega al proceso
por un contrato declarado, y una guarda impide que vuelvan a entrar.

Un literal de configuración no es un atajo: es deuda que crece con el
desarrollo. El primero se justifica ("es solo para probar"), el décimo ya
nadie lo ve, y un repo copiado apunta al servidor de otro. Las tres skills
de arquitectura juzgan estructura; esta juzga cómo llegan los valores.
Frontera con custodiar-secretos: allá los valores son secretos y nunca se
ven; acá son configuración y se ven, pero no en el código.

## Invariantes

- **Qué es configuración**: hosts, puertos, URLs, rutas, tiempos y topes,
  nombres de recursos (proyectos, colas, buckets, tablas), identidades de
  entorno, interruptores. Si cambia entre máquinas, entornos o copias del
  repo, es configuración. Un secreto es configuración que además rige
  custodiar-secretos.
- **`config/` guarda la forma, nunca un valor**: por cada archivo de
  configuración, su `.example` con todas las claves, su tipo y su
  propósito, y el archivo real ignorado por git. Un `.example` que
  contiene un valor real es un hardcode con otro nombre.
- **Un solo cargador**: un módulo de settings por servicio, con
  precedencia declarada y en ese orden: entorno del proceso → archivo
  local ignorado por git → default declarado en el cargador. Ningún otro
  código lee `os.environ` ni abre archivos de configuración. Un default es
  una decisión escrita en el cargador, no un literal en el sitio de uso.
- **Falla cerrado**: una clave requerida que no llega detiene el arranque
  con su nombre; una clave desconocida se rechaza, no se ignora. El
  descarte silencioso (`extra="ignore"`) es la forma más cara de un
  hardcode: el valor está escrito y no gobierna nada.
- **Prueba de llegada**: por cada clave, una prueba que la pone por el
  canal declarado y mide que el proceso la ve. Un `.env` que un cargador
  no exporta, o una variable que el arnés no hereda, se descubren ahí y
  no en producción. Se mide por dónde llega en este repo; no se
  generaliza de otro.
- **Interruptores locales declarados**: los que no salen del gestor de
  secretos (auditoría, depuración, banderas de desarrollo) van en una
  lista `LOCALES` que quien regenera el archivo preserva. Un interruptor
  que se apaga solo porque un script reescribió el archivo es peor que no
  tenerlo.
- **Dependencias en la versión exacta donde se probaron**: una
  dependencia se declara con la versión con la que se probó, evaluó y
  desplegó (`==`), nunca con un rango. Un rango (`>=4`, `^1.2`) afirma
  compatibilidad con versiones que nadie midió, y el día que el gestor
  resuelve otra, el mismo código corre sobre otro contrato sin que nada
  falle. Medido: un `fastmcp>=4` probado con 4.0.2 resolvía a 4.0.3 la
  semana siguiente. Subir de versión es un cambio: se mide y se pinea
  la nueva. Vale para runtime, desarrollo y CI por igual — también para
  las herramientas de la suite: `ruff` cambia su selección por defecto
  entre versiones, así que "ruff limpio" con un rango quiere decir cosas
  distintas según quién lo corra. Y vale para el intérprete: la versión
  de Python (o Node) que corrió la suite se declara por nombre, y las
  demás del rango soportado se declaran sin medir hasta que un CI las
  corra de verdad — y se lea. Medido: un paquete declaraba 3.10–3.13,
  la suite había corrido a mano solo en 3.12.10, y el CI que cubría
  3.10 había corrido en rojo tres veces sin que nadie lo mirara (el
  piso declarado importaba un módulo que en 3.10 no existe). Decir
  "medido en 3.10 y 3.13" habría sido el mismo defecto una capa más
  arriba; decir "el CI nunca corrió" fue el mismo defecto en la otra
  dirección.
- **Guarda contra literales**: una comprobación mecánica (AST o patrones)
  sobre el código fuente que detecta IPs, puertos, URLs, rutas absolutas
  y tiempos mágicos fuera del cargador. Corre en cada cierre y en
  arquitectura-verificar, como el cero-fuga de secretos. Cada excepción
  lleva su motivo escrito al lado; sin motivo, es un hallazgo. La guarda
  pide FORMA y POSICIÓN, no forma sola: el literal cuenta cuando está
  donde un valor gobierna algo (defecto de parámetro, constante
  asignada, argumento nombrado como configuración, espera, defecto de un
  `.get()`, clave de configuración en un dict). Medido: por forma sola
  daba 52, y veinte no eran configuración (`"=" * 80` y `data[-80:]`
  contaban como el puerto 80; `radius = 300` como un timeout de cinco
  minutos); la cuenta honesta era 30. Una guarda que mide por forma sola
  no subestima la deuda: la INVENTA — el defecto que la skill persigue,
  cometido por su propia herramienta.
- **Retrofit por inventario**: en un repo ya nacido, primero se cuenta
  (la guarda en modo informe da el número), después se mueve al contrato,
  y la guarda queda permanente con la cuenta en cero. El número de
  literales es la medida de la deuda; se declara, no se estima.

## Receta: la forma fija de centralizar la configuración

Los invariantes dicen qué; esto dice cómo, con valores fijos, para que
todos los repos de la casa se vean igual. Regla del humano, textual y
cerrada: **toda configuración (= settings) va en la raíz del repo, en
`/config/`; todo apunta allí; nada de configuración — ni siquiera la de
prueba, dev o test — va fuera.** Lo técnico se resuelve adentro de esa
regla.

- **C1 — Un solo lugar: `/config/`.** Todo archivo de configuración del
  servicio vive ahí, incluidos los de dev y test (`config/dev.*`,
  `config/test.*`): la configuración de prueba es configuración. Por
  cada archivo, su `.example` versionado con todas las claves (tipo,
  default, propósito, si es secreto, si es LOCAL) y el archivo real
  ignorado por git. Un archivo de configuración fuera de `/config/` es
  un hallazgo de la guarda, igual que un literal.
- **C1-bis — Cuando el archivo no se puede mover, `/config/` igual lo
  explica.** Regla del humano, textual: si el contrato o el software no
  puede mover el archivo de configuración a `/config/`, igual se coloca
  en `/config/` su `.example` y su explicación — en `/config/` se tiene
  que encontrar, sí o sí, cómo configurar (settings) un proyecto. La
  excepción exime al archivo de mudarse; no exime a `/config/` de ser el
  único lugar donde se entiende la configuración entera: el `.example`
  dice qué claves tiene el archivo, y la explicación dice dónde vive de
  verdad, por qué no puede moverse (quién lo lee ahí: la herramienta, el
  framework, el runtime) y cómo se genera o se copia desde `/config/`.
  La regla nació corrigiendo el razonamiento "mover no agrega nada, la
  forma ya está versionada y los valores ya ignorados": el invariante no
  protege dónde vive el valor, protege DÓNDE SE ENCUENTRA LA
  EXPLICACIÓN — un repo nuevo no sabe que tiene que mirar la raíz. Cómo
  se cumple, medido (lucky-tool-netbox, 78fa493):
  - "No se puede mover" son dos casos con textos distintos en la
    excepción: IMPOSIBLE (el cliente MCP descubre `.mcp.json` en la raíz
    por convención suya; no hay flag) y POSIBLE PERO CARO (`.env` lo
    nombra por ruta absoluta el `.mcp.json` de cada máquina, ignorado
    por git: moverlo rompe en silencio registros que nadie ve). El
    segundo es reversible y queda como pendiente que exige avisar
    antes; el primero no.
  - El molde se MUEVE a `/config/`, no se copia: dos copias del mismo
    contrato es peor que ninguna — se edita una, la otra sigue diciendo
    lo de antes, y las dos son texto válido, así que nada falla.
  - Sin punto adelante: `config/env.example`, no `config/.env.example`
    — un archivo oculto dentro de un directorio cuya razón de ser es que
    se encuentre.
  - `config/README.md` obligatorio: tabla molde → archivo real → quién
    lo escribe; por qué el real no está acá, un párrafo por archivo; los
    comandos para poner en marcha; y las reglas (precedencia, defaults en
    el cargador, falla cerrado, moldes sin valores, `LOCALES`). Un
    `/config/` sin README es un cajón: alguien encuentra el molde y no
    sabe adónde copiarlo.
  - Puntero en los dos sentidos: cada molde abre diciendo adónde va el
    archivo real y por qué; el README de la raíz dice que la explicación
    está en `/config/`.
- **C1-ter — Las guardas del contrato de `/config/`.** Una excepción
  sin guarda se convierte en dos contratos, y `/config/` es terreno
  versionado (al revés que un `.env`), así que hay que comprobar
  activamente lo que en un directorio ignorado se daba por hecho. Una
  prueba por cada una: cada molde está en `/config/` y su copia NO
  reaparece en la raíz; existe `config/README.md`, nombra cada molde y
  dice adónde va cada archivo real; ningún archivo real se coló en
  `/config/` (con y sin punto: `config/.env` y `config/env`); ningún
  molde trae un valor real — secretos vacíos (`TOKEN=`) y marcadores sin
  resolver (`<RUTA AL REPO>`: una ruta resuelta salió de la máquina de
  alguien); y ningún molde trae un permiso encendido de fábrica — las
  claves peligrosas (escrituras, borrados, auditoría) van en un bloque
  que el cliente NO lee (`_env_opcionales`), para que copiar el molde
  entero no pueda encender nada. Medido por reversión, 7/7 — y dos
  "nada falla" de la primera vuelta eran fallas de la sonda, no de la
  guarda: una prueba de "el README menciona X" es débil por
  construcción, mide presencia de una cadena, no que esté explicado.
- **C2 — Un solo cargador, con el nombre de la industria.** `config/` es
  también el paquete que carga: expone un único objeto de settings
  tipado y validado al arrancar (`from config import settings`; en
  Python, `pydantic-settings` con `class Settings(BaseSettings)`; en
  otros stacks, su equivalente: Spring `@ConfigurationProperties`,
  `viper`, `convict`). Es el ÚNICO código que lee `os.environ` o abre
  archivos de `config/`. El resto del código importa `settings.<clave>`;
  lo que la industria estandariza es exactamente esto — un punto de
  carga, precedencia declarada, fallar al arrancar —, no el nombre.
- **C3 — Precedencia fija, y solo esa:** entorno del proceso →
  `config/<archivo>` local → default declarado en el cargador. Sin cwd,
  sin adivinar, sin un cuarto origen.
- **C4 — Nombres:** toda variable de entorno con prefijo del servicio,
  `<SERVICIO>_<CLAVE>`; cada clave declara tipo, default, si es
  **secreto** (en `config/` va solo su NOMBRE en el gestor; el valor
  llega por entorno — custodiar-secretos, mapear-despliegue) y si es
  **LOCAL** (interruptor del operador que el script que regenera el
  archivo preserva).
- **C5 — Falla cerrado:** clave requerida ausente → el arranque para
  nombrándola; clave desconocida → rechazo (`extra="forbid"`), nunca
  `ignore`.
- **C6 — Prueba de llegada:** un test por clave que la pone por su canal
  real y mide que `settings` la ve; los tests leen su configuración de
  `config/test.*`, no de literales en el código de prueba.
- **C7 — Guarda de literales, por forma Y posición**, en cierre y
  arquitectura-verificar; cuenta declarada, excepciones con motivo al
  lado.
- **C8 — Retrofit:** inventario (guarda en modo informe) → mover cada
  archivo y cada literal a `/config/` + `settings` → cuenta en cero →
  guarda permanente. Si una herramienta obliga a un archivo en otro
  lugar por convención propia, se declara como excepción con su motivo
  escrito, no se calla.

## Flujo

1. Inventariar: correr la guarda en modo informe y listar cada literal
   con archivo:línea, y cada archivo de configuración fuera de
   `/config/`.
2. Declarar el contrato: `/config/` con los `.example` de todos los
   archivos (dev y test incluidos), el cargador único `settings` con
   precedencia y defaults, lista `LOCALES`.
3. Mover cada literal al contrato; la clave se nombra por lo que
   gobierna, no por dónde estaba.
4. Probar la llegada de cada clave por su canal real.
5. Dejar la guarda permanente en el portón (cierre, arquitectura-verificar)
   con la cuenta en cero y las excepciones motivadas.

## Referencia viva

Dos casos de la casa. Medido: `lucky-tool-netbox`, commit `78fa493` —
`config/env.example`, `config/mcp.json.example`, `config/README.md` con la
tabla molde → archivo real → quién lo escribe, y
`tests/test_contrato_de_configuracion.py` con las guardas de C1-ter (7
decisiones probadas por reversión); es la implementación de referencia
de C1-bis. Y la guarda de literales por forma y posición de
`lucky-tool-gns3` (`scripts/guarda_configuracion.py`, `2da6a3f`, 30
literales declarados). Pendiente de medir: el `config/` de
OptimizacionMikrotik, el primero que se pidió. Anclar en commits, no en
rutas.

## Salida

```text
LITERALES=<cuenta actual> (archivo:línea por cada uno, o NINGUNO)
FUERA_DE_CONFIG=<archivos de configuración fuera de /config/, o NINGUNO>
CONTRATO=DECLARADO|AUSENTE
CARGADOR=UNICO|DISPERSO
PRECEDENCIA=<entorno > local > default | NO_DECLARADA>
LLEGADA=PASS|FAIL (<claves probadas>/<claves declaradas>)
LOCALES=<lista o NINGUNO>
GUARDA=PERMANENTE|INFORME|AUSENTE
EXCEPCIONES=<cuenta, con motivo cada una>
```
