# Base mismatch

- **Qué es:** trabajo paralelo solapado planificado sobre bases distintas: cada
  claim registra la huella sobre la que razonó su plan, y las huellas no
  coinciden.
- **Cuándo:** al consultar el Collision Map con claims activos que se solapan
  con el alcance propio y declaran una base comparable.
- **Cómo:** bloquear la escritura, advertir, y proponer en corto la salida: el
  resultado nombra a cada actor en conflicto, su base y el claim donde está
  declarada (`CONFLICT=actor|base|fuente`), y la acción que destraba
  (`PROPOSAL=replanificar sobre la base actual y revalidar el alcance`).
  Coordinar turnos no alcanza: un plan razonado sobre una foto vieja del
  repositorio debe replanificarse, no ejecutarse después.
- **Sin base comparable:** `UNKNOWN`, nunca `NO`. `NO` afirma que la
  comparación ocurrió y no encontró diferencia.
- **No es:** un lock global ni un veto permanente; se disuelve replanificando.
- **Ejemplo:** otra sesión declaró `PATHS="core/api.py"` con base `1111…`; la
  consulta llega con base `2222…` sobre la misma ruta. Sale
  `BASE_MISMATCH=YES`, `RECOMMENDATION=BLOCK`, el `CONFLICT` con el actor y su
  claim, y la proposición de replanificar.
