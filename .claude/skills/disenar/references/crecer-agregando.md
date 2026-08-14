# Crecer agregando

Cómo se cierra a la edición un eje que va a crecer, y cuándo no corresponde
cerrarlo. Sale de un caso real.

## El caso (Lucky-PizarraEvo, 2026-08-03)

Una pizarra tenía cuatro catálogos —tipos de nodo, capas, relaciones,
estados—. Cada uno era un archivo con todas sus entradas adentro:

```js
const TIPOS = Object.freeze({
  nota: { ... },
  tarea: { ... },
  idea: { ... },
});
```

Y arriba, este comentario:

```js
// Costura de extensión: agregar un tipo = tocar SOLO este archivo.
```

El comentario se leía como una virtud y era el defecto: "tocar solo este
archivo" sigue siendo tocar un archivo compartido. Se escribió cuatro
veces, una por catálogo, lo que confirmó el patrón en vez de delatarlo.

## Por qué el eje estaba mal cerrado

Los tipos de nodo eran un eje declarado de crecimiento: nacían seguido y
seguirían naciendo. Cerrarlo a la edición no era refinamiento, era el
diseño. Crecer editando cuesta tres cosas:

1. Cada edición arriesga lo que ya funcionaba: el archivo compartido es el
   único punto donde una entrada nueva puede romper a las viejas.
2. No escala fuera del equipo: una entrada de un tercero exigiría que
   alguien acepte un parche en un archivo central.
3. Miente sobre el alcance: un cambio que toca un archivo compartido no es
   atómico, aunque el diff se vea chico.

## La forma correcta

Una entrada, un archivo, en una carpeta, detrás de un puerto.

```
catalogos/tipos/nota.js
catalogos/tipos/idea.js
catalogos/tipos/permiso.js   ← agregar es dejar esto
```

El catálogo es el puerto —la pregunta "¿qué entradas hay?"— y la carpeta es
un adaptador que la contesta; mañana la contesta una tabla o un paquete
externo sin que cambie nada más. La entrada declara su propio orden y sus
banderas, así ubicarla o consumirla tampoco exige editar a nadie. Si el
dato lo consumen una pantalla y un agente por API, lo sirve el backend: una
sola fuente.

También se lo conoce como registro con autodescubrimiento, y la parte de
dejar el archivo y listo, como convención sobre configuración.

## Cuándo NO corresponde

- Cuando el eje no va a crecer: abrir un punto de extensión para una
  variación que nadie va a recorrer agrega indirección sin comprador.
- Cuando el cambio mueve el contrato mismo y no agrega una entrada más:
  ahí toca rediseñar, y rediseñar es la respuesta correcta. Un eje se
  cierra contra su propia variación, no contra cualquier cambio futuro.
- Una raíz de composición que solo cablea crece por adición por diseño: que
  crezca no la vuelve defectuosa.

## Las dos fallas del autodescubrimiento no son iguales

Al leer una carpeta hay dos formas de romperse y se tratan distinto. Un
archivo mal formado se saltea con aviso: se pierde a sí mismo y se nota.
Una clave repetida frena el arranque: secuestra a otra entrada.

La segunda apareció al probarla, no al escribirla. Un archivo `_duplicado`
declarando la misma clave le ganó al original porque el listado del
directorio devuelve alfabético y el guión bajo ordena antes: quién ganaba
dependía de cómo se llamara el archivo, y esa clave estaba guardada en la
base. El autodescubrimiento mete el orden del sistema de archivos adentro
del programa; qué pasa ante una colisión se decide a propósito y se prueba.

## Preguntas para el diseño

- Cuando nazca la próxima entrada de este eje, ¿qué archivos hay que abrir?
  Si alguno es compartido, el eje está mal cerrado.
- ¿Podría alguien de afuera agregar una sin pedir permiso?
- ¿Estoy por escribir "agregar acá = tocar solo este archivo"? Eso no es
  costura de extensión: es la confesión de que no la hay.
- ¿Este eje va a crecer de verdad, o lo estoy blindando por las dudas?
