# datos/raw/

Datos crudos, **no versionados** por su tamano. Aqui va lo que el pipeline
espera encontrar:

| Archivo | Como se obtiene | Tamano |
|---|---|---|
| `produccion_grupos.csv` | `python -m src.ingesta.produccion` (API Socrata; requiere red) | ~1,2 GB |
| `investigadores_consolidado.csv` | descarga desde datos.gov.co | ~18 MB |

`cargar_consolidado()` (`src/ingesta/__init__.py`) prioriza
`datos/raw/investigadores_consolidado.csv` y, si no esta, cae al XLSX de
`datos/tarea_join/`, que **si esta versionado**: por eso los analisis de
investigadores funcionan sin descargar nada.

`cargar_produccion()` **no tiene respaldo**: sin `produccion_grupos.csv` los
scripts de produccion (`sprint5_produccion.py`, `sprint5_duckdb.py`,
`sprint6_ocde_composicion.py`) no pueden producir sus salidas. Se comportan como
se documenta en `CHANGELOG.md`: avisan, dicen el comando exacto y salen con
codigo 3 en vez de lanzar un traceback.
