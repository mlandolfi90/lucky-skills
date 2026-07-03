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
