# lucky-skills

Marketplace propio de skills de Lucky — **fuente unica**.

Plugin `lucky`:
- **crisol** — loop jidoka de calidad incorporada para cambios de codigo.
- **brujula** — ancla la sesion al estado real del repo/deploy (no alucina contexto).

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

El bump de sellos de version, el `registry.json` (sha256 por archivo + pin por commit) y la
firma `minisign` se forjan en UNA pasada con el script — **nunca a mano**:
```
bash scripts/forjar-release.sh vX.Y.Z             # bump + registry + leak-scan + firma
bash scripts/forjar-release.sh vX.Y.Z --no-sign   # sin firmar (firma diferida)
```
Deja todo en el working tree (no commitea/taggea). Luego, bajo Crisol: review del diff ->
commit -> `git tag -a vX.Y.Z` (anotado) -> push. La firma minisign del registry (ancla commit +
sha256) es la inmutabilidad real.
