"""Genera la tabla markdown de los 51 artefactos a partir de los dos informes.

Uso: python _archivo/scripts_oneoff/tabla_51_md.py
"""

from __future__ import annotations

import csv
from pathlib import Path

BASE = Path("04_auditoria")
SALIDA = Path("_archivo/scripts_oneoff/tabla_51.md")

CORTO = {
    "CORRE": "CORRE",
    "CORRE (sin datos de entrada)": "CORRE (3)",
    "IMPORTA OK": "IMPORTA",
    "TEST PASA": "TEST PASA",
    "N/A (sin pruebas)": "N/A",
    "FALLA": "**FALLA**",
    "LEGACY (no migrado)": "LEGACY",
}


def leer(ruta: Path) -> list[dict]:
    with ruta.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


poetry = leer(BASE / "reporte_ejecucion_51_poetry.csv")
moderno = {r["ruta"]: r for r in leer(BASE / "reporte_ejecucion_51_moderno.csv")}

lineas = [
    "| # | Artefacto del inventario | Líneas | Con el lock | Con versiones modernas |",
    "|---:|---|---:|---|---|",
]
for a in poetry:
    b = moderno[a["ruta"]]
    est_a = CORTO.get(a["estado"], a["estado"])
    est_b = CORTO.get(b["estado"], b["estado"])
    ruta = a["ruta"].replace("\\", "/")
    lineas.append(f"| {a['n']} | `{ruta}` | {a['lineas']} | {est_a} | {est_b} |")

SALIDA.write_text("\n".join(lineas) + "\n", encoding="utf-8")
print(f"escrito {SALIDA} ({len(lineas)} lineas)")

# Recuentos para el texto del CHANGELOG
from collections import Counter  # noqa: E402

for etiqueta, filas in (("lock", poetry), ("moderno", list(moderno.values()))):
    activos = [r for r in filas if r["ubicacion"] == "activo"]
    cuenta = Counter(r["estado"] for r in activos)
    print(f"\n{etiqueta}: activos={len(activos)}")
    for k, v in cuenta.most_common():
        print(f"   {v:>3}  {k}")
    cats = Counter(r["categoria"] for r in activos if r["categoria"])
    for k, v in cats.most_common():
        print(f"   {v:>3}  {k}")
