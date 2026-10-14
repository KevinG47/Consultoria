# -*- coding: utf-8 -*-
"""
resumen_fichas.py
=================

Resume las 51 fichas de `documentacion_auditoria/data/analisis_codigo/` para
planificar los arreglos de `datos_originales/repo_mejorado/`: qué archivos NO
son ejecutables, por qué, y qué bugs declara cada ficha.

Uso:  python _archivo/scripts_oneoff/resumen_fichas.py [--bugs]
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
FICHAS = RAIZ / "documentacion_auditoria" / "data" / "analisis_codigo"

filas = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(FICHAS.glob("*.json"))]
print(f"fichas leidas: {len(filas)}\n")

print("=" * 100)
print("1. EJECUTABILIDAD DECLARADA EN LA FICHA")
print("=" * 100)
no_ejec = [f for f in filas
           if str(f.get("ejecutabilidad", "")).strip().upper().startswith("NO")]
print(f"  NO ejecutables  : {len(no_ejec)}")
print(f"  Si (con matices): {len(filas) - len(no_ejec)}\n")
for f in no_ejec:
    print(f"  [{f['rol']:14s}] {f['archivo']}")
    print(f"      {(f.get('ejecutabilidad') or '')[:200]}")

print("\n" + "=" * 100)
print("2. BUGS DECLARADOS")
print("=" * 100)
total = 0
for f in filas:
    b = f.get("bugs") or []
    total += len(b)
    if b:
        print(f"\n  {f['archivo']}  ({len(b)})")
        for x in b:
            print(f"     - {x[:190]}")
print(f"\n  TOTAL de bugs declarados: {total}")

print("\n" + "=" * 100)
print("3. CAUSAS RECURRENTES")
print("=" * 100)
claves = {
    "ruta /content de Colab": ["/content"],
    "display() o magia de notebook": ["display(", "!pip"],
    "input ausente o no versionado": ["no existe", "falta el input", "no esta en el clon",
                                      "gitignored", "no encontrado"],
    "dependencia no declarada": ["kaleido", "openpyxl", "nbformat", "pyvis",
                                 "scikit-posthocs", "duckdb"],
    "encoding / consola Windows": ["unicodeencodeerror", "cp1252", "charmap"],
    "cwd / resolucion de rutas": ["cwd", "modulenotfounderror", "resolve()"],
    "tipos / dtype": ["typeerror", "dtype", "int64", "tuplas"],
    "supuestos estadisticos": ["frecuencia esperada", "supuesto", "pearson"],
}
for etq, pats in claves.items():
    hits = [f["archivo"] for f in filas
            if any(p in json.dumps(f, ensure_ascii=False).lower() for p in pats)]
    print(f"\n  {etq}: {len(hits)}")
    for h in hits:
        print(f"      {h}")
