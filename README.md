# lucky-skills

Marketplace propio de skills de Lucky — **fuente unica**.

Plugin `lucky`:
- **crisol** — loop jidoka de calidad incorporada para cambios de codigo.
- **brujula** — ancla la sesion al estado real del repo/deploy (no alucina contexto).
- **hotfix** — permiso de trabajo en caliente: iterar betas con el operador en frente, formalizar por Crisol al final.

## Uso
```
/plugin marketplace add mlandolfi90/lucky-skills
/plugin install lucky@lucky-skills
```
En cada repo de trabajo, el puntero va en `.claude/settings.json`:
```json
{ "extraKnownMarketplaces": { "lucky-skills": { "source": { "source": "github", "repo": "mlandolfi90/lucky-skills" } } },
  "enabledPlugins": { "lucky@lucky-skills": true } }
```
Actualizar: editar aqui -> push -> web agarra lo ultimo en sesion nueva; local `/plugin update` + `/reload-plugins`.

## Release (ritual)

El bump de sellos de version y el `registry.json` (sha256 por archivo + pin por commit)
se forjan en UNA pasada con el script — **nunca a mano**:
```
bash scripts/forjar-release.sh vX.Y.Z             # bump + registry + leak-scan
bash scripts/forjar-release.sh vX.Y.Z --dry-run   # solo reporta, no escribe
```
Deja todo en el working tree (no commitea/taggea). Luego, bajo Crisol: review del diff ->
commit -> `git tag -a vX.Y.Z` (anotado) -> push. El ancla inmutable real es el COMMIT
pineado en el registry + los sha256 por archivo (la firma minisign fue retirada — ADR 0009;
vuelve si el trade-off cambia).
