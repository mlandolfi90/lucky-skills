---
name: arquitectura-ubicar
description: Decidir dónde debe vivir un archivo, módulo, puerto, adaptador o componente. Usar después de corroborar la arquitectura y antes de crear o mover estructura.
---

# Ubicar cambio

Elegir el destino más pequeño que preserve las fronteras reales.

## Precondiciones

- Usar un mapa vigente de `arquitectura-descubrir`.
- Definir la responsabilidad única del cambio.
- Consultar `mapa-colisiones` para las rutas candidatas.
- Mantener el TARGET de escritura sin confirmar hasta que el humano elija.

## Decidir

1. Aplicar un tier proporcional antes de introducir hexagonal:
   - Preservar una frontera existente cuando ya es coherente.
   - Introducir puertos y adaptadores nuevos solo con evidencia observada de
     canales alternativos, dominio que exige pruebas sin infraestructura,
     cambio de infraestructura previsto o extensión paralela.
   - Sin esa evidencia, preferir la separación plana más pequeña y evitar
     abstracciones especulativas. Con evidencia insuficiente, no emitir `FIT`.
2. Clasificar la responsabilidad:
   - Regla de negocio: dominio.
   - Orquestación: aplicación o caso de uso.
   - Contrato hacia afuera: puerto.
   - Tecnología concreta: adaptador.
   - HTTP, CLI o UI: adaptador de entrada.
   - Persistencia o servicio externo: adaptador de salida.
   - Componente visual: nivel atómico coherente con el frontend real.
3. Reutilizar una frontera existente si su responsabilidad coincide.
4. Crear una unidad nueva cuando ampliar la existente mezcle motivos de cambio.
5. Evitar archivos concentradores y dependencias desde dominio hacia detalles.
6. Elegir un solo destino recomendado y explicar alternativas descartadas.

## Salida

```text
RESPONSIBILITY=...
TIER=PRESERVE|FLAT|HEXAGONAL|UNKNOWN
DESTINATION=...
ALTERNATIVES_DISCARDED=...
BOUNDARY=...
DEPENDENCY_DIRECTION=...
NEW_UNIT=YES|NO
COLLISION=NONE|FOUND|UNKNOWN
TARGET=UNCONFIRMED|<destino-confirmado-por-humano>
HUMAN_DECISION=NONE|REQUIRED:<decisión>
VERDICT=FIT|ADAPT|BLOCK
REASON=...
```

`DESTINATION` es la recomendación; no se convierte en `TARGET` confirmado por
sí sola.

## Delegación

Un subagente solo puede recolectar mapa, tier y colisiones. La sesión madre
elige `DESTINATION`, emite `TIER`, `VERDICT` y `HUMAN_DECISION`, y entrega el
dictamen final. No crear ni mover archivos: el humano confirma el TARGET y la
sesión con autorización de escritura ejecuta. En contexto subagente, devolver
evidencia acotada sin completar `Salida`.
