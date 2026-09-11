---
name: cierre
description: Comprobar si un cambio puede cerrarse y dejar evidencia. Usar tras implementar o recuperar para emitir cierre final, condicional o bloqueado sin ocultar pendientes.
---

# Cierre

Decidir el estado final de una ejecución a partir de evidencia actual.

## Comprobar

1. TARGET y alcance coinciden con lo autorizado.
2. El diff contiene solo rutas esperadas.
3. `mapa-colisiones` no tiene conflictos abiertos (`COLLISION=` es el suyo).
4. Pruebas específicas y regresiones proporcionales pasan: `TESTS=` se toma
   de la salida de `microfix` o `hotfix`, mismo nombre y mismo enum.
5. Arquitectura y contratos tienen veredicto suficiente: `ARCHITECTURE=` es
   el de `arquitectura-verificar`, tal cual.
6. Rollback existe o su ausencia fue aceptada.
7. Deuda, seguimientos y riesgos están registrados.
8. Commit, push o deploy solo ocurrieron si estaban autorizados.
9. Si esta corrida consultó el saber, decir qué pasó con lo consultado:
   citar cada ficha usada con su veredicto —funcionó, parcial o no
   funcionó— anclando en el recibo de esta corrida, en formato
   `receipt:<RECEIPT_HASH>` (el saber acepta ese ancla junto al ledger v2).
   Una ficha que no sirvió vale tanto como una que sirvió: sin citas
   negativas nadie se entera de que una guía enseña algo equivocado. No
   haber consultado nada es una respuesta válida y se declara.
10. Si la corrida dejó un aprendizaje reutilizable (síntoma→acción) o una
    sospecha sin evidencia dura, proponerlo al saber como ficha o señal por
    su herramienta (`saber_proponer_ficha`, `saber_senal`), citando el mismo
    recibo. Sin saber disponible, declararlo.
11. Cero fuga de secretos, sin excepción: el diff, los logs, los recibos y
    el transcript no contienen claves, tokens ni credenciales — ni en claro
    ni hardcodeados. Los secretos viajan por nombre, jamás por valor; para
    comparar un valor se usa su hash, nunca el valor. Un secreto detectado
    bloquea el cierre hasta rotarlo y purgarlo. La evidencia es el `SWEEP=`
    de `custodiar-secretos`; sin barrido, `UNKNOWN`, no `PASS`.
12. Cero literales de configuración nuevos: el diff no introduce hosts,
    puertos, URLs, rutas absolutas ni tiempos mágicos fuera del cargador
    único (guarda de arquitectura-configuracion). Los literales previos
    son deuda con su cuenta declarada, no bloqueo; un literal nuevo sin
    motivo escrito al lado sí bloquea.
13. Si `revisor-seguridad` corrió sobre este cambio, `EXPOSURE=CLEAN`; con
    `FOUND`, el hallazgo va a `FOLLOW_UP` y el cierre no es `FINAL`.

## Estados

- `FINAL`: resultado logrado, sin trabajo obligatorio pendiente.
- `CONDITIONAL`: resultado útil logrado, con una condición explícita y
  comprobable pendiente.
- `BLOCKED`: no puede afirmarse éxito o continuar con seguridad.

`CONDITIONAL`, `BLOCKED` o `ROLLBACK=APPLIED` piden `autopsia`; se anota en
`FOLLOW_UP`.

Un descarte sin fase escritora puede cerrar con
`TESTS=NOT_APPLICABLE`; cualquier ejecución escritora exige `TESTS=PASS` para
un cierre final.

`TESTS=` habla de lo barato (el test dirigido al archivo tocado, la suite
local); el portón del repo — mutantes, CI, aceptación — se declara aparte en
`PORTON=`. Con `PORTON=PENDIENTE` el cierre es `CONDITIONAL` y la condición
es una sola, en `CONDITIONS` con forma fija: `PORTON pendiente: <comando>;
autoriza human:<id>`. No hay `FINAL` con portón pendiente. `PORTON=CORRIDO`
exige su resultado leído en esta corrida, no supuesto. `PORTON=NO_APLICA`
únicamente cuando `REGLAS.md` no declara `PORTON=`: el repo sigue su
cadencia propia y este campo no la juzga. Un `CONDITIONAL` por portón se
salda con un cambio propio que corre el portón y cierra `FINAL` con
`PORTON=CORRIDO`, citando los tramos que salda (skill `modo-fixes`).

## Salida

```text
CHANGE_ID=<el de cambio>
CLOSURE=FINAL|CONDITIONAL|BLOCKED
RESULT=...
TESTS=PASS|FAIL|UNKNOWN|NOT_APPLICABLE
PORTON=CORRIDO|PENDIENTE|NO_APLICA
ARCHITECTURE=PASS|BLOCK|UNKNOWN
COLLISION=NONE|FOUND|UNKNOWN
ROLLBACK=READY|APPLIED|UNAVAILABLE
CONDITIONS=...
FOLLOW_UP=...
DECIDED_BY=...
SABER=<fichas citadas|NONE|UNAVAILABLE>
RECEIPT=...
```

No marcar `FINAL` para terminar una sesión, ahorrar tiempo o esconder
incertidumbre.
