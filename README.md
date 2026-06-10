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
Actualizar: editar aqui -> push -> web agarra lo ultimo en sesion nueva; local `/plugin update` + `reload-skills`.
