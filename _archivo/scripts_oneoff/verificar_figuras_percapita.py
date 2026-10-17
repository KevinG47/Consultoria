# -*- coding: utf-8 -*-
"""Verifica las figuras de F2-2: validez PNG, tamaño y uso de la paleta."""
from __future__ import annotations

import io
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
GRAF = RAIZ / "documentacion_auditoria" / "data" / "memoria" / "graficas_percapita"

PERMITIDOS = {"#1E3780", "#4A6BA8", "#7BA7D0", "#B7871E", "#D4A84A",
              "#334155", "#64748B", "#CBD5E1", "#F8FAFC", "#1E293B"}
PROHIBIDOS = {"#B91C1C", "#15803D", "#7C3AED", "#FF0000", "#00FF00",
              "#15803d", "#7c3aed"}

try:
    from PIL import Image
    hay_pil = True
except Exception:                                     # noqa: BLE001
    hay_pil = False
print(f"PIL disponible: {hay_pil}")

for p in sorted(GRAF.glob("*.png")):
    print(f"\n=== {p.name} · {p.stat().st_size:,} bytes ===")
    if not hay_pil:
        continue
    with Image.open(p) as im:
        im = im.convert("RGB")
        print(f"    tamaño: {im.width} x {im.height}")
        colores = Counter(im.getdata())
    total = sum(colores.values())
    print(f"    colores distintos: {len(colores)}")
    print("    colores dominantes (hex, % del área):")
    for c, n in colores.most_common(9):
        hexa = "#{:02X}{:02X}{:02X}".format(*c)
        etiqueta = ""
        if hexa in PERMITIDOS:
            etiqueta = " [paleta]"
        elif hexa in PROHIBIDOS:
            etiqueta = " [PROHIBIDO]"
        elif hexa in ("#FFFFFF", "#000000"):
            etiqueta = " [blanco/negro]"
        print(f"      {hexa}  {100*n/total:6.2f} %{etiqueta}")
    # comprobación de colores prohibidos con tolerancia (antialias)
    mallos = []
    for c, n in colores.items():
        hexa = "#{:02X}{:02X}{:02X}".format(*c)
        for proh in ("B91C1C", "15803D", "7C3AED"):
            pr, pg, pb = (int(proh[i:i+2], 16) for i in (0, 2, 4))
            if abs(c[0]-pr) <= 12 and abs(c[1]-pg) <= 12 and abs(c[2]-pb) <= 12:
                mallos.append((hexa, n))
                break
    print(f"    píxeles de color prohibido (rojo/verde/morado): "
          f"{sum(n for _, n in mallos)} "
          f"({100*sum(n for _, n in mallos)/total:.4f} % del área)")
