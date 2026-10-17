# -*- coding: utf-8 -*-
"""Resume validacion_unicidad.json y verifica las figuras de F2-7."""
from __future__ import annotations

import glob
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
J = json.loads((DOC / "data" / "memoria" / "validacion_unicidad.json")
               .read_text(encoding="utf-8"))

print("=== ids_no_unicos ===")
d = J["ids_no_unicos"]
for k in ("n_ids_evaluados", "n_ids_violadores", "pct_del_padron"):
    print(f"  {k:24s} {d[k]}")
print(f"  por_estado: {d['por_estado']}")
print(f"  por_rol   : { {k: v for k, v in d['interpretacion_por_rol'].items() if k != 'lectura'} }")

print("\n=== IDs con violación de EDAD (la que compromete la identidad) ===")
for x in d["detalle"]:
    if x["fallos_edad"] > 0:
        print(f"  {x['id']} {x['peor_convocatorias']:7s} "
              f"{x['peor_edad_a']:7.2f}→{x['peor_edad_b']:7.2f} "
              f"lapso={x['peor_anios_transcurridos']:5.2f} "
              f"residuo={x['peor_residuo']:+8.2f} [{x['estado']}]")

print("\n=== contraste con la implementación ===")
for k, v in J["contraste_con_la_implementacion"].items():
    if k != "lectura":
        print(f"  {k:42s} {v}")

print("\n=== sensibilidad ===")
print(f"  {J['sensibilidad_tolerancia']['pares_por_tolerancia']}")

print("\n=== impacto ===")
im = J["impacto"]
for k, v in im.items():
    if k != "nota":
        print(f"  {k:32s} {v}")

print("\n=== validaciones ===")
for k, v in J["validaciones"].items():
    print(f"  [{'OK ' if v else 'NO '}] {k}")

print("\n=== figuras ===")
for ruta in sorted(glob.glob(str(DOC / "data" / "memoria" / "graficas_unicidad" / "*.png"))):
    from PIL import Image
    with Image.open(ruta) as img:
        sz = img.size
        img = img.convert("RGB")
        c = Counter(img.getdata())
    tot = sum(c.values())
    malos = 0
    for col, n in c.items():
        for proh in ("B91C1C", "15803D", "7C3AED"):
            pr, pg, pb = (int(proh[i:i + 2], 16) for i in (0, 2, 4))
            if abs(col[0] - pr) <= 12 and abs(col[1] - pg) <= 12 and abs(col[2] - pb) <= 12:
                malos += n
                break
    print(f"  {Path(ruta).name:36s} {sz[0]}x{sz[1]}  prohibidos={100*malos/tot:.4f}%")
