---
name: arquitectura-verificar
description: Verificar un plan o diff contra la arquitectura real, SOLID, atomicidad y factorización. Usar antes del cierre cuando cambien estructura, contratos o varias unidades.
---

# Verificar arquitectura

Dictaminar si un cambio respeta las fronteras corroboradas.

## Invariantes

- Analizar el diff o plan exacto, no todo el proyecto sin alcance.
- Usar un mapa vigente de `arquitectura-descubrir`.
- Permanecer en solo lectura.
- No corregir durante la verificación.
- Distinguir defecto nuevo, deuda previa y evidencia insuficiente.

## Gates

Comprobar:

1. Dirección de dependencias y aislamiento del dominio.
2. Tier proporcional cuando el cambio introduce hexagonal: puertos y
   adaptadores nuevos exigen evidencia de variación, testabilidad sin
   infraestructura, cambio de infraestructura o extensión paralela.
3. Puertos definidos por la necesidad del núcleo, no por la tecnología.
4. Adaptadores reemplazables y entradas separadas de aplicación.
5. Responsabilidad única y motivos de cambio concentrados.
6. Extensión sin condicionales tecnológicos dispersos.
7. Sustitución y contratos respetados.
8. Interfaces pequeñas y dependencias invertidas.
9. Cambio atómico, archivos proporcionados y ausencia de duplicación evitable.
   La proporción se mide por bocas públicas: funciones, clases, métodos de
   clase y rutas declaradas. No cuentan nombres privados, declaraciones de
   tipo, constantes de módulo ni archivos de prueba. Bloquea el diff que suma
   una boca a un archivo que ya llega a doce, o que crea uno con doce o más;
   el archivo tocado que ya estaba en doce y no creció es deuda previa.
   Bloquea también el nombre público nuevo repetido entre archivos hermanos
   sin declararlo como contrato en el índice de su carpeta; lo ya repetido es
   deuda previa. El conteo sale de un comando; sin conteo ejecutado el
   veredicto es `UNKNOWN`, no `BLOCK`.
10. Si existe frontend, solo la frontera de página/API observada en ese repo
    cruza al backend. Átomos, moléculas, organismos, templates o equivalentes
    reales no hacen fetch ni conocen URLs o clientes del backend.
11. Collision Map resuelto para las rutas tocadas.
12. Configuración y dependencias externas compatibles con 12-factor cuando
    aplique.

Un archivo que crece por adición a propósito —raíz de composición, tabla de
ruteo, índice de exports, migraciones— se exime del gate 9 en
`.lifecycle/state/BOCAS-OK`, una línea por archivo con su número y su razón.
El número congela lo que ya hay: si el diff lo supera, vuelve a bloquear. Un
símbolo repetido a propósito se declara contrato en el índice de su carpeta y
deja de contar. No hay excepción por commit: el gate corre antes de que exista.

## Veredicto

```text
ARCHITECTURE_VERDICT=PASS|BLOCK|UNKNOWN
NEW_VIOLATIONS=...
PREEXISTING_DEBT=...
COLLISION=NONE|FOUND|UNKNOWN
REQUIRED_ACTION=NONE|ADAPT|HUMAN_DECISION|ADAPT_AND_HUMAN_DECISION
EVIDENCE=...
```

Usar `UNKNOWN` cuando falte evidencia; no convertir una suposición en `PASS`.
Usar `ADAPT_AND_HUMAN_DECISION` cuando el cambio necesita corrección y además
una decisión de autoridad; no ocultar una condición detrás de la otra.

## Delegación

Un subagente solo puede recolectar evidencia acotada para gates aislados. La
sesión madre decide esos gates y emite `ARCHITECTURE_VERDICT` y
`REQUIRED_ACTION`; un subagente no aprueba ni bloquea el cambio completo.
En contexto subagente, devolver evidencia sin completar `Veredicto`.
