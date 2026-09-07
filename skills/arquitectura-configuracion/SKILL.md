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
  lleva su motivo escrito al lado; sin motivo, es un hallazgo.
- **Retrofit por inventario**: en un repo ya nacido, primero se cuenta
  (la guarda en modo informe da el número), después se mueve al contrato,
  y la guarda queda permanente con la cuenta en cero. El número de
  literales es la medida de la deuda; se declara, no se estima.

## Flujo

1. Inventariar: correr la guarda en modo informe y listar cada literal
   con archivo:línea.
2. Declarar el contrato: `config/` con `.example`, cargador único con
   precedencia y defaults, lista `LOCALES`.
3. Mover cada literal al contrato; la clave se nombra por lo que
   gobierna, no por dónde estaba.
4. Probar la llegada de cada clave por su canal real.
5. Dejar la guarda permanente en el portón (cierre, arquitectura-verificar)
   con la cuenta en cero y las excepciones motivadas.

## Referencia viva

Primer caso de la casa: el directorio `config/` con sus `.example` en el
repo OptimizacionMikrotik, creado para que ningún valor quede en el
código. Pendiente de medir contra estos invariantes; cuando se mida, el
resultado va a ficha del saber y a la siguiente versión de esta skill.

## Salida

```text
LITERALES=<cuenta actual> (archivo:línea por cada uno, o NINGUNO)
CONTRATO=DECLARADO|AUSENTE
CARGADOR=UNICO|DISPERSO
PRECEDENCIA=<entorno > local > default | NO_DECLARADA>
LLEGADA=PASS|FAIL (<claves probadas>/<claves declaradas>)
LOCALES=<lista o NINGUNO>
GUARDA=PERMANENTE|INFORME|AUSENTE
EXCEPCIONES=<cuenta, con motivo cada una>
```
