# datos/processed/

Artefactos derivados, **no versionados** (`*.duckdb` esta en `.gitignore`).

| Archivo | Como se obtiene |
|---|---|
| `observatorio.duckdb` | `python scripts/sprint2_duckdb.py` (requiere el consolidado) |

Se regenera de forma determinista a partir del consolidado. `sprint5_duckdb.py`
lo exige como punto de partida y avisa si falta.
