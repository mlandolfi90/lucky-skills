## [DRIFT-009] Arreglás "X sigue activo al apagar Y" y anda por el control que probaste, pero el MISMO síntoma reaparece al apagar por OTRO control que parece "lo mismo"

- **TIPO:** DRIFT
- **SÍNTOMA (lo observable, NO la causa):** el usuario reporta "al apagar/parar Y, X sigue activo" (ej. "al detener la grabación sigue activa la transcripción"). Arreglás el gate, probás por UN control y anda. Pero el mismo síntoma REAPARECE —o aparece el inverso "efecto activo SIN indicador"— cuando se apaga/prende por OTRO control que el usuario percibe como equivalente. Un verificador fresco (o el usuario) lo caza por ese segundo camino.
- **CAUSA-RAÍZ (1 línea):** DOS señales/toggles INDEPENDIENTES gobiernan lo que el usuario percibe como UN solo estado (caso real: "grabando" = toggle popover `SET_RECORDING` **vs** la pastilla REC = `etch-mode`, que era otra captura de mutaciones del DOM). El fix/gate se ató a UNA sola señal; el otro camino queda roto.
- **ACCIÓN (pasos):**
  1. **Enumerá TODOS los controles** que el usuario cree que gobiernan ese estado (toggle, botón, atajo, pastilla) ANTES de cerrar el fix. Preguntate: "¿de cuántas formas se prende/apaga esto?".
  2. Definí el **estado EFECTIVO unificado** y gateá/fixeá por él, no por la señal que testeaste. Si la UI refleja un subsistema, hacé que la ESPEJE por la fuente real (caso: la caja de transcripción espeja el mic = `narración AND grabación`, NO la pastilla que se ve).
  3. Verificá los DOS invariantes: nunca el efecto activo sin indicador (mic caliente sin caja), ni el indicador sin el efecto.
- **ANTI-ACCIÓN (camino muerto):** NO asumas "1 toggle = 1 estado". NO des el fix por cerrado probando UN solo camino de apagado — el segundo camino es exactamente donde reaparece. NO gatees la UI por la señal que se PARECE (la pastilla visible) en vez de por la que dispara el efecto (el gate real del subsistema).
- **PREVENCIÓN:** al tocar un estado con múltiples disparadores, mapealos primero; verificador fresco que pruebe CADA camino. **META — cuando "cada fix rompe otra cosa" (whack-a-mole): PARÁ de parchar. Acordá con el humano UN modelo mental único (quién MANDA vs quién es CONFIG), alineá TODO a ese modelo, y recién ahí fixeá.** Parchar sin modelo acordado garantiza el ciclo de choques (caso HOT-MIC: pastilla-vs-toggles se destrabó recién al fijar "pastilla=maestro, toggles=config").
- **validated_on:** `dev · 2026-07-10 · 634fd79 (checkpoint HOT-MIC, Lucky-Debugger)`
- **stale_si:** >90 días sin re-validar
- **origen:** RUN HOT-MIC ITER 4→5 (arco micrófono de narración): gateé la caja por `etch-mode` en vez del gate del mic → el bug reportado reaparecía por la pastilla REC; lo cazó el verificador fresco opus (2 lentes independientes) tras yo darlo por cerrado · **usos:** 1
- **REFS:** primo de [[GREP-004]] (2 strikes ⇒ instrumentá) y del catch por verificador fresco · **NEXT:** cualquier fix de "estado X sigue activo/encendido" en UI con más de un control para el mismo estado
- **estado:** CANDIDATE
