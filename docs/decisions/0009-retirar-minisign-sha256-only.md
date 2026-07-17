# 0009 — retirar minisign: integridad sha256-only + pin por commit (dueño único)

- estado: aceptado
- fecha: 2026-07-09
- decide: MLL (operador)
- tags de la familia al sellar: v1.29.0
- relacionado: ADR 0001 (loader `cargar` — este ADR SUPERSEDE su §2 «ancla TOFU
  con minisign» y su §3 «firma del registry»; el resto del diseño del loader
  sigue vigente); RUN-LEDGER corrida `main — 2026-07-09`
- supersede: la cadena de firma minisign de ADR 0001 (§2 y la firma de §3)

## Contexto

ADR 0001 estableció la cadena: registry firmado con minisign (Ed25519, TOFU
install-only) + sha256 por archivo + pin por commit, todo verificado por código
externo. En la práctica la firma nunca llegó a operar de forma sostenida:

- El schema del registry ya la declaraba **"DIFERIDA/dormida"** — el registry se
  generaba sin firmar (v1.28.0 se forjó con `--no-sign`).
- El repo no comitea ningún `.minisig`.
- Pero `cargar-fetch-verify.sh` EXIGÍA el `.minisig` y su validación → la
  vía-dato del loader estaba **estructuralmente rota**: todo fetch terminaba en
  reject (fail-closed correcto, pero inútil).
- Costo operativo real: clave privada custodiada (Infisical), passphrase,
  `minisign` en PATH en cada máquina, pública baked por install, rotación —
  para un repo con UN solo dueño.

Decisión del operador (2026-07-09): *"soy el único dueño del repo — eliminar
minisign, sacar definitivamente; en algún momento se volverá pero no quiero más
fastidio con eso."*

## Decisión

1. **Se retira minisign de toda la cadena activa** (fetch-verify, install,
   forja, tests, prosa). No queda paso de firma ni clave que gestionar.
2. **La integridad que QUEDA** (toda por código externo, fail-closed):
   - fetch de bytes crudos `raw@REF` vía HTTPS (`curl --proto '=https'`);
   - la REF la fija el **install** en `state.env`, fuera del alcance del modelo
     y del payload — v1 pinea por TAG (el campo `commit` del registry es
     informativo: la forja corre pre-commit; pin-por-commit real = v2);
   - pin `registry.tag == CARGAR_TAG` (+ commit, si el install lo fijó);
   - `sha256 -c` de cada cuerpo contra el hash que el CÓDIGO extrae del
     registry, con normalización CRLF→LF antes de hashear;
   - `exit ≠ 0` → nada entra al contexto (invariante intacto).
3. **El resto de ADR 0001 sigue vigente:** skill-como-datos, capability-gate
   (jamás versión castrada), nonce de sesión del entorno, payload = dato no
   confiable, MODO MANUAL sin fetcher, carga progresiva, idempotencia activa.
4. **La forja ya no firma:** `forjar-release.sh` pierde el paso de firma y las
   variables `MINISIGN_*`; `--no-sign` queda como no-op con aviso y el script
   limpia `.minisig` residuales.
5. **install-trust** deja de anclar clave pública: solo fija el pin
   (`state.env`: registry-url, tag, commit).

## Modelo de amenaza (delta vs ADR 0001)

| Amenaza | Antes (con firma, si hubiera operado) | Ahora (sha256-only) |
|---|---|---|
| CDN/red adultera bytes | firma + sha no matchean → reject | sha del registry@commit no matchea → reject (HTTPS + pin por commit) |
| Tag movido (`git -f`) | la firma del registry del commit no valida → cazado | cae en el bucket repo-comprometido ACEPTADO (mover un tag exige escritura en el repo); pin-por-commit (v2) lo re-cerraría sin firma |
| **Repo / cuenta GitHub comprometida** | la firma no valida sin la privada → cazado | **NO se caza**: el atacante regenera registry+cuerpos consistentes. RIESGO ACEPTADO (dueño único, 2FA) |
| Clave privada filtrada | firma falsa que SÍ valida (riesgo TOFU de 0001) | N/A — no hay clave que filtrar |
| Payload malicioso (prompt-injection) | aislamiento nonce/código | igual (sin cambios) |

Neto honesto: se pierde el segundo factor anti-repo-comprometido; desaparece
entera la superficie de gestión de claves (que además cargaba el riesgo TOFU de
privada filtrada). Para un operador único con 2FA, el trade-off favorece la
simplicidad — y des-rompe el loader.

## Criterio de reversa (cuándo VUELVE la firma)

Se re-introduce si CUALQUIERA de estas condiciones cambia:

- más de un operador con acceso de escritura al repo;
- distribución del catálogo a terceros (consumidores fuera del control del
  operador);
- señal de compromiso de la cuenta GitHub;
- el catálogo empieza a servir contenido ejecutable (hooks/binarios) por la
  vía-dato, además de prosa-método.

La reversa es barata: git history conserva la implementación completa
(fetch-verify con `minisign -V`, forja con firma, install-trust con pública
baked, test-verify con par throwaway) al alcance de un revert.

## Consecuencias

- (+) La vía-dato del loader **vuelve a funcionar** (exigía una firma que el
  release no producía).
- (+) Cero fastidio de claves: sin `minisign` en PATH, sin privada en Infisical
  para releases, sin baked keys por máquina, sin rotación.
- (+) Forja e install más simples y honestos: el código dice lo que el sistema
  hace (antes la prosa prometía una firma que no existía).
- (−) Sin segundo factor anti-repo-comprometido (aceptado y documentado arriba).
- (=) Fail-closed, nonce, capability-gate, zero-leak, pin por commit: intactos.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.6.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.
