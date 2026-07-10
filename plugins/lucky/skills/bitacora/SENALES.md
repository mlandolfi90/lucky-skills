# SEÑALES — señales débiles / near-miss log (no es el catálogo)

> Linaje industrial: *hiyari-hatto* (Toyota, near-miss log) + *weak signals*.
> Ley de Heinrich: la FRECUENCIA del casi-incidente predice el incidente —
> por eso una sospecha sin evidencia no se tira: se acumula y SE CUENTA.
>
> Regla del operador (2026-07-03): un patrón sospechado pero NO probado no entra
> al INDEX (un catálogo que miente causa incidentes), pero tampoco se pierde:
> queda acá con contador de avistamientos, para detectar si "pasa más seguido
> de lo que se imagina".
>
> Reglas duras:
> - Este archivo JAMÁS se consulta para decidir una acción (eso es del INDEX).
> - Cada avistamiento suma `visto: N` + fecha + una línea de contexto.
> - **`visto ≥ 2` → se investiga activamente** en la próxima corrida que lo roce:
>   o gana evidencia real (→ entrada CANDIDATE con validated_on) o se refuta
>   (→ se borra con una línea de por qué era falso).
> - Cero secretos, igual que el catálogo.

| SEÑAL (lo que parece pasar) | visto | avistamientos (fecha · contexto 1 línea) |
|---|---|---|
| winget se cuelga en "DeliveryOptimization downloading" con instaladores grandes (~600MB); dos instancias winget se bloquean mutuamente sin error visible | 1 | 2026-07-03 · upgrade Docker Desktop; workaround: descarga directa del vendor + Get-AuthenticodeSignature Valid antes de ejecutar |
| Endurecer la PROSA de una skill no cambia la conducta de subagentes DENTRO de la misma sesión — parecen actuar sobre la description del listing congelado al session-start, no sobre el cuerpo refrescado en disco | 1 | 2026-07-09 · corrida idea-fallback: 2 retests con cache refrescado repitieron la conducta vieja; el fix se movió a la description; re-verificar en sesión FRESCA |
| Un gate/lint corrido con pipe (`lint \| tail`) dentro de una cadena `&&` queda ENMASCARADO: el exit del pipeline es el de tail (0), no el del gate → el paso "verde" deja pasar un FAIL real | 1 | 2026-07-09 · promoción de CANDIDATEs: lint gritó incoherencia (DRIFT-007 >35 líneas) pero el push salió igual; ventana de catálogo-que-miente en main hasta el fix. Antídoto: gate SIN pipe, capturar `$?` explícito (como hace la forja) |
