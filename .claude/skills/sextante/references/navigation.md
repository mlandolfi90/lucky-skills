# Navegación

## Paquete autónomo

El contrato canónico obligatorio viaja dentro de esta skill:

- [Configuración lifecycle v1](lifecycle-config-v1.md): lectura segura,
  defaults, fuentes y estados de componentes.
- [State Map v1](state-map-v1.md): esquema, autoridad y corroboración.
- [Huella local v3](local-fingerprint-v1.md): material exacto y SHA-256.
- [Comprobante y resumen v1](receipt-v1.md): salida, semántica y gates.
- [Vectores de conformidad v1](conformance-v1.json): casos estáticos que todo
  adaptador debe reproducir.

`SKILL.md` y estos cuatro contratos bastan para ejecutar Sextante en nivel
`MANUAL` o `DEGRADED`. Si un harness no puede reproducir una sonda normativa,
debe degradarla a `PARTIAL`; la ausencia del repositorio de desarrollo nunca
autoriza a inventar datos.

Antes de certificar un adaptador o distribución como portable, ejecutar los
vectores estáticos de configuración, State Map y huella local incluidos en
`references/conformance-v1.json`.

## Árbol de desarrollo opcional

Cuando esta skill vive dentro del repositorio completo, puede aprovechar:

- `docs/concepts/INDEX.md` para documentación ampliada.
- `templates/lifecycle/` para una futura adopción explícita.
- `adapters/reference_python/run_sextante.py` como adaptador de referencia.

Son recursos opcionales del árbol de desarrollo, no dependencias del paquete
autónomo. Una copia separada del adaptador recibe `--skill-version` o
`--source-root`; cualquier adaptador de otro harness conserva los cuatro
contratos junto a su manifiesto.
