# Hijas como sesión aparte (`hija: sesion`)

Cuándo conviene: tramos largos (más de una hora), trabajo en otra máquina
(una VM, un servidor), o cuando hace falta que la hija sobreviva a un
cierre de la madre. Para lo demás, `subagente` es más simple.

Todo lo de abajo está medido en Windows con la extensión de VS Code
(2026-10). Si algo no coincide con tu entorno, medí antes de confiar.

## Lanzar

Desde el shell de la madre, parada en la `carpeta:` del encargo, en
segundo plano. La salida va a un archivo, no al shell de la madre: si
vuelve al shell le llena el contexto, que es justo lo que la regla 8
protege.

```powershell
claude -p "Ejecutá el encargo <ruta-absoluta>. Es tu única tarea. Sos la implementadora: aplicá .claude/agents/implementadora.md." --model <modelo_trabajo> --effort <esfuerzo_trabajo> --permission-mode <el modo activo de la madre> --output-format json > docs/encargos/salida-NNN.json 2>&1
```

- El prompt va pegado a `-p`, **antes** de cualquier flag que acepte
  varios valores (`--allowedTools` se traga lo que sigue).
- **`--permission-mode` replica el modo de la madre.** Un `claude -p`
  nuevo no hereda nada por sí solo: toma el de la configuración. La madre
  lee el suyo y lo pasa igual. No lo sube ni lo baja por su cuenta.
- Un subagente de `.claude/agents/` no restringe a una sesión `-p`: ahí el
  rol es instrucción («aplicá …»). Para la revisora, el mismo comando con
  `--model <modelo_revision>` y «Revisá el encargo … Sos la revisora:
  aplicá .claude/agents/revisora.md».
- Una sesión lanzada con `-p` desde el shell de la madre aparece en la
  lista «Local» de la extensión; una con `--bg` no. La lista no se
  recarga sola: hay que apretar recargar o reabrir el panel.
- Al lanzar, la madre anota en el frontmatter `sesion_id:` (el id que
  devuelve el harness, o el pid) y `plazo:` (el doble de lo estimado).

## Esperar

`Wait-Process -Id <pid>` en un PowerShell en segundo plano
(`run_in_background`), con `-Timeout` igual al `plazo:`. Desde Git Bash,
`kill -0` no ve procesos de Windows y dice «terminó» al instante.

Al vencer el plazo sin cierre, la madre no espera «un ratito más»: le dice
al humano en una línea y le da dos opciones, esperar otro plazo o parar
(`claude stop <sesion_id>`) y retomar con una hija nueva.

## Retomar

`claude --resume <sesion_id>` con el mensaje fijo de SKILL.md («Vuelta N
del encargo …»). La revisora no se retoma.

## Trampas medidas

- **Los subagentes de una hija `-p` tienen que correr en primer plano.**
  Si la hija lanza un agente de fondo y cierra el turno, el runtime lo
  corta a los 10 minutos y el trabajo se pierde. El encargo lo dice en
  «Alcance → Puede ejecutar», y como red la madre pone en el entorno de la
  hija `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=3600000`. Una hija sesión sí
  puede mandar lecturas largas a un subagente; una hija subagente no.
- **Una sola hija por árbol de trabajo.** Dos sesiones sobre la misma
  carpeta se pisan los cambios. Si hacen falta dos a la vez, van en
  carpetas o worktrees distintos, y cada encargo lo declara en
  `carpeta:`. Antes de lanzar, la madre comprueba que no haya otra hija
  viva sobre esa carpeta (`sesion_id:` de los encargos abiertos).
- **La madre no lee `salida-NNN.json`.** Lee el frontmatter y el informe
  del encargo. El archivo de salida queda para diagnóstico, y no se
  commitea (agregarlo a `.gitignore` la primera vez).
- **Cierre:** la hija llena su informe, actualiza `estado:` y termina el
  turno. Lo que tiene que constar va en el encargo; `SendMessage` a la
  madre es un aviso opcional, no el registro.
- **Los historiales no se borran.** `claude stop <id>` libera el proceso
  y conserva la conversación; `claude rm` sólo si el humano lo pide.
