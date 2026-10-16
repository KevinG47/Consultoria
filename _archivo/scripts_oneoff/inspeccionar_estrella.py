"""Inspecciona el esquema del modelo estrella del repositorio auditado.

Comprueba el objetivo especifico 4: "esquema estrella con nueve dimensiones y una
tabla de hechos".

Uso: python _archivo/scripts_oneoff/inspeccionar_estrella.py [ruta.duckdb]
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RUTA = Path(sys.argv[1] if len(sys.argv) > 1 else
            "Observatorio_Ministerio_de_Ciencias_Grupo8/datos/processed/observatorio.duckdb")
print(f"archivo: {RUTA}  ({RUTA.stat().st_size / 1e6:.2f} MB)\n")

con = duckdb.connect(str(RUTA), read_only=True)

rel = con.execute("""
    SELECT table_name, table_type
    FROM information_schema.tables
    ORDER BY table_type, table_name
""").fetchall()

tablas = [n for n, t in rel if t == "BASE TABLE"]
vistas = [n for n, t in rel if t != "BASE TABLE"]

print(f"TABLAS ({len(tablas)}):")
for n in tablas:
    filas = con.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0]
    cols = [c[0] for c in con.execute(f'DESCRIBE "{n}"').fetchall()]
    print(f"  {n:28} {filas:>9,} filas  {len(cols):>2} columnas")

print(f"\nVISTAS ({len(vistas)}):")
for n in vistas:
    cols = [c[0] for c in con.execute(f'DESCRIBE "{n}"').fetchall()]
    print(f"  {n:28} {len(cols):>2} columnas")

# Clasificacion dim_* / fact_* : es lo que distingue un esquema estrella.
dims = [n for n in tablas if n.lower().startswith("dim")]
facts = [n for n in tablas if n.lower().startswith("fact")]
otros = [n for n in tablas if n not in dims + facts]
print(f"\ndimensiones (dim_*): {len(dims)} -> {dims}")
print(f"tablas de hechos (fact_*): {len(facts)} -> {facts}")
print(f"otras tablas: {len(otros)} -> {otros}")

print("\n--- columnas de cada dimension ---")
for n in dims:
    cols = [c[0] for c in con.execute(f'DESCRIBE "{n}"').fetchall()]
    print(f"  {n}: {', '.join(cols)}")
for n in facts:
    cols = [c[0] for c in con.execute(f'DESCRIBE "{n}"').fetchall()]
    print(f"  {n}: {', '.join(cols)}")

con.close()

print("\n" + "=" * 70)
print(f"El objetivo pedia NUEVE dimensiones y UNA tabla de hechos.")
print(f"Encontradas: {len(dims)} dimensiones y {len(facts)} tabla(s) de hechos.")
