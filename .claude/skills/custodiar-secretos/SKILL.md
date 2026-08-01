---
name: custodiar-secretos
description: Manejar credenciales sin que ningún valor toque el chat, los logs ni el código. Usar antes de cualquier comando, request o archivo que involucre claves, tokens o passwords.
---

# Custodiar secretos

Prioridad cero: que el secreto nunca llegue al transcript. Sin disculpas
después — la disculpa no revoca la clave.

## Invariantes

- Por defecto no se imprime ningún valor: se trabaja con nombres de
  secretos. Solo una lista explícita de variables de configuración conocidas
  puede mostrarse.
- Un secreto se consume dentro de un solo proceso: nunca pasa por variable
  de shell ni por argumento — el error de un comando vuelca el comando
  entero, con el secreto adentro.
- Comparar valores: por hash corto del valor, jamás el valor.
- Validar la forma sin imprimir: una línea, sin espacios, largo y prefijo
  esperados → veredicto ok/mal, nunca el contenido.
- Requests con secreto en header: usar una herramienta que no vuelque el
  header en su mensaje de error, y capturar solo el código de estado.
- Nada hardcodeado: un secreto en el código o en un archivo versionado es
  fuga, aunque el repo sea privado.
- Si pese a todo un valor tocó el transcript: cero disculpas — rotar
  primero, purgar después, y capturar la ficha al saber. La acción es la
  única respuesta válida.

## Flujo

1. Nombrar qué secreto necesita la tarea y dónde vive (gestor, env), por
   nombre.
2. Elegir el patrón de uso que no puede transcribir: proceso único,
   validación de forma muda, comparación por hash.
3. Ejecutar. Ninguna rama — éxito o error — imprime ni serializa el valor
   ni su objeto contenedor.
4. Antes de mostrar cualquier salida derivada (logs, diff), barrerla; el
   barrido se valida con un canario que debe matchear.
5. Ante fuga: rotar, purgar, ficha. En ese orden, sin pedir perdón.

## Salida

```text
SECRETS_USED=<nombres|NONE>
VALUES_PRINTED=0
PATTERN=SINGLE_PROCESS|MANAGER|N/A
SWEEP=CLEAN|CANARY_FAILED|LEAK
ACTION=NONE|ROTATED_AND_PURGED
```
