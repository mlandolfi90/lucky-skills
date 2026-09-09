# Portón

- **Qué es:** la comprobación cara que un repo declara como condición de
  su imagen, su deploy o su rama principal: mutantes, la suite entera en
  contenedor, el build del CI, la aceptación contra un servicio real. La
  declara `REGLAS.md` del repo con comandos literales y costo medido.
- **Cuándo:** al cerrar un caso grande y bajo autorización del humano si el
  repo declara `PORTON=bajo-autorizacion` (skill `modo-fixes`); si no lo
  declara, cuando cada skill del repo mande. Siempre antes de un deploy.
- **Cómo:** corre entero o no corre; no se recorta. Si un push a la rama
  que el CI escucha lo dispara, ese push es la corrida y su resultado se
  lee antes de seguir. Su estado por tramo vive en el campo `PORTON=` del
  [cierre](closure.md): `CORRIDO`, `PENDIENTE` o `NO_APLICA`.
- **No es:** los gates 1–12 de `cierre` (esos corren siempre), los hooks
  asesores del harness, ni lo barato (el test dirigido al archivo tocado y
  la suite local, que se corren en cada cambio).
- **Ejemplo:** en `lucky-tool-mtk-chr` el portón es el stage `mutantes` del
  Dockerfile (~8 min) y el push a `dev` que lo construye en CI; lo barato
  es el pytest de los verdugos del archivo tocado y la suite local.
