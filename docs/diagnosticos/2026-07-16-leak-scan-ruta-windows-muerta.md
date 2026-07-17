---
id: 2026-07-16-leak-scan-ruta-windows-muerta
schema: diagnostico/1
tipo: diagnostico
estado: ABIERTO
creado: 2026-07-16
sintoma: "leak-scan.sh sale 0 (LIMPIO) sobre un archivo que contiene una ruta absoluta Windows de otro usuario — la regla RUTA-ABSOLUTA no la caza"
reproduccion: "en repo temporal, con el script REAL (no retipeado): archivo con ruta Windows de un usuario ficticio (backslashes SIMPLES) → bash scripts/leak-scan.sh → exit 0. El mismo archivo con una ruta /home/<otro>/ → exit 1."
zona_sospechada: ["scripts/leak-scan.sh:61"]
hipotesis:
  - {h: "La rama Windows del ERE está muerta por doble-escape: el patrón exige DOS backslashes literales donde una ruta real trae UNO", evidencia: "el ERE leído crudo del archivo (sin retipear) exige el doble; el test byte-exacto da 0 matches con backslash simple y 1 con doble", verificar: "extraer el patrón del archivo con Python (sin capa de shell) y correrlo contra ambas formas — 30 segundos"}
  - {h: "El vector solo se atrapa hoy de rebote por la regla 2 (ATRIBUCION), que hardcodea el handle del operador", evidencia: "una ruta con el handle del operador dispara la regla 2 aunque la regla 3 la deje pasar; una ruta de OTRO usuario no dispara ninguna", verificar: "archivo con ruta Windows de usuario ajeno, sin el handle → exit 0"}
bitacora_match: null
escalon_recomendado: microfix
tope_sugerido: microfix
target_observado: "pc-local (Git-Bash) — el gate corre acá y en la forja"
refs: [corrida:2026-07-16-equipo-doc-v1, corrida:2026-07-16-equipo-doc-v1-fix]
---
# leak-scan: la rama de rutas Windows no caza nada

Hallado por el `leak-verifier` FRESCO de la corrida `equipo-doc-v1`, y confirmado
por un segundo verificador en la corrida `-fix`. **Read-only: nada se tocó.**

## Impacto

La regla 3 (`RUTA-ABSOLUTA`) existe para cazar rutas absolutas reales de la
máquina del operador. Hoy **la mitad Windows del patrón no matchea nunca**. Como
el operador trabaja en Windows, es justo la mitad que más importa.

El vector queda cubierto SOLO de rebote por la regla 2, que busca el handle del
operador hardcodeado. Consecuencia concreta: **una ruta absoluta Windows de OTRO
usuario (o de otra máquina) se filtraría en silencio** a un repo público, con el
gate en verde.

## Aviso metodológico (esto costó dos intentos fallidos)

El patrón **no se puede verificar retipeándolo**: el shell come una capa de
backslashes y las conclusiones salen invertidas. Tanto el líder de la corrida
como el propio leak-verifier verificaron MAL en su primer intento y llegaron a
la verdad recién leyendo el ERE **crudo desde el archivo** y pasándoselo al motor
sin retipear. Quien tome este diagnóstico: hacelo así o vas a "confirmar" que la
rama vive.

## Por qué microfix y no algo más grande

Un comportamiento, un punto: el nivel de escape del patrón en una línea. La
solución es conocida (un nivel de escape menos en las tres alternativas). Lo que
lo hace no-trivial es la **prueba negativa obligatoria**: el gate tiene que
VERSE morder — archivo con ruta Windows ajena → rojo; sin ella, el fix es una
edición sin evidencia, que es exactamente el pecado que este diagnóstico
denuncia.

## Riesgo conocido al aplicarlo

Al revivir la rama Windows, el patrón pasa a matchear las rutas de **ejemplo**
que viven en la documentación del propio repo. Si esos ejemplos no usan
placeholders `<asi>`, el fix vuelve a bloquear la forja. Ya pasó una vez en la
corrida `-fix`: la documentación de este mismo defecto disparó el gate y hubo
que saldarlo con una excepción del operador. **Antes de aplicar el fix: barrer
la documentación y dejar todos los ejemplos con placeholders.**

## Deuda de diseño que este diagnóstico expone (no la resuelve)

La regla 3 no tiene válvula para el ejemplo declarado — la regla 4 sí la tiene
(`ALLOW_SLUG`). Un gate que no puede distinguir "documento un patrón" de
"filtro un valor" convierte cada postmortem en un bloqueo. Es la lección v1.8.0
que el propio scanner declara **en prosa, en su cabecera, sin mecanizar**.
Decidir si eso entra al microfix o es corrida aparte: del operador.
