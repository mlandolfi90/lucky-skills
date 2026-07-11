# hotfixs — Índice Semántico de Fallas

> Mapa de las fallas de este repo por lo que se **OBSERVA**. Es la memoria
> anti-"arreglo 1, rompo 2": ante una falla, primero se consulta acá.
>
> **Regla de oro:** ante una falla nueva, GREP este índice por el síntoma ANTES
> de intentar una cura (C — la instancia de ESTE repo); después el INDEX de la
> bitácora (A — el patrón cross-repo). Si ya existe su `Bug-`, leé "Qué se
> intentó" para no repetir un camino muerto (☠️).
>
> El índice **solo lista**; el detalle vive en cada `Bug-`. Cada fila = una
> falla: lo que ves + una explicación breve y específica + estado + archivo.
>
> - **Indexá por SÍNTOMA OBSERVABLE** ("ESC no cierra"), no por tema ("problema de foco").
> - **Naming:** `Bug-<frase-corta>.md`, kebab-case. Linkeá relacionadas con `[[Bug-...]]`.
> - **Estados:** ✅ resuelta+verificada · 🔧 resuelta (pendiente re-aplicar/verificar) · ⏳ abierta.
> - Una falla que RECURRE como **clase** se cosecha a la Bitácora (instancia → patrón); anotá su ID en la fila.
>
> Agrupá por área. Emojis sugeridos: 🎤 mic · 🖼️ preview · 🧭 barra · 📤 envío (agregá los que el repo pida).

## 🖼️ preview

| falla (lo que ves) | explicación breve | estado | archivo |
|---|---|---|---|
| <ej: el borde del popover se corta> | margen negativo del contenedor | ⏳ | [[Bug-popover-bleed]] |

## 🎤 mic

| falla (lo que ves) | explicación breve | estado | archivo |
|---|---|---|---|
| <ej: al detener la grabación sigue activa la transcripción> | dos controles gobiernan un estado (→ DRIFT-009) | ⏳ | [[Bug-mic-sigue-activo]] |

<!-- Duplicá una sección por área. Borrá las filas de ejemplo al sembrar. -->

---

## Invariantes

> Reglas lockeadas que, respetadas, evitan CLASES enteras de falla. No son bugs:
> son el piso que no se vuelve a discutir. Acá suben los `modelo-estado:` de los
> `Bug-` que se probaron firmes y valen para todo el repo, no para una instancia.

- <ej: la caja de transcripción espeja el mic por su gate real (narración AND grabación), NO por la pastilla visible>.

## No son fallas

> Comportamiento CORRECTO que parece bug — no lo "arregles" (anti-falla). Vive
> acá para que el próximo que lo vea no abra un `Bug-` de más.

- <ej: el popover se cierra al perder foco — es intencional, no un bug de foco>.
