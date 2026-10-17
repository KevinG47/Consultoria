# -*- coding: utf-8 -*-
"""Resume clustering.json, verifica figuras y muestra los perfiles."""
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
J = json.loads((RAIZ / "01_datos" / "resultados_json" / "clustering.json")
               .read_text(encoding="utf-8"))

print("=== veredicto ===")
print(json.dumps(J["veredicto"], ensure_ascii=False, indent=1))

print("\n=== sensibilidad a gamma (ARI frente al ajuste principal) ===")
print(f"  {J['sensibilidad_gamma']}")
print("\n=== sensibilidad a las edades imposibles ===")
print(f"  {J['sensibilidad_edades_imposibles']}")
print("\n=== nivel de persona ===")
print(f"  {J['nivel_persona']}")
print("\n=== prueba de estructura ===")
p = J["prueba_de_estructura"]
for k in ("k_evaluado", "filas", "silhouette_observada", "silhouette_nulo_medio",
          "silhouette_nulo_ic95", "silhouette_p", "calinski_observado",
          "calinski_nulo_medio", "calinski_p"):
    print(f"  {k:26s} {p[k]}")

print("\n=== pérdida de información ===")
pi = J["perdida_de_informacion"]
print(f"  inercia total (k=1): {pi['inercia_total_k1']:.1f}")
print(f"  inercia intra (k=2): {pi['inercia_intra_k']:.1f}")
print(f"  pérdida            : {pi['perdida_pct']:.2f} %")
print(f"  por k: { {k: round(v,2) for k,v in pi['perdida_por_k'].items()} }")

print("\n=== aporte de cada variable (V de Cramér) ===")
for k, v in J["aporte_de_cada_variable"].items():
    print(f"  {k:26s} {v['cramer_v']:.4f}")

print("\n=== edad por cluster ===")
for k, v in J["edad_por_cluster"].items():
    print(f"  cluster {k}: media={v['media']:.2f} mediana={v['mediana']:.2f} n={v['n']:,}".replace(",", " "))

print("\n=== perfiles del k=2 (categorías con más diferencia) ===")
for var, d in J["perfiles"].items():
    cl = d["clusters"]
    etiquetas = list(cl)
    difs = []
    for i, cat in enumerate(d["categorias"]):
        a = cl[etiquetas[0]][i]
        b = cl[etiquetas[1]][i]
        difs.append((abs(a - b), cat, a, b))
    difs.sort(reverse=True)
    print(f"\n  {var}:")
    for dif, cat, a, b in difs[:4]:
        print(f"    {cat[:34]:36s} c1={a:5.1f}% c2={b:5.1f}%  Δ={dif:5.1f}")

print("\n=== figuras ===")
for ruta in sorted(glob.glob(str(DOC / "data" / "memoria" / "graficas_clusters" / "*.png"))):
    from PIL import Image
    with Image.open(ruta) as im:
        sz = im.size
        im = im.convert("RGB")
        c = Counter(im.getdata())
    tot = sum(c.values())
    malos = 0
    for col, n in c.items():
        for proh in ("B91C1C", "15803D", "7C3AED"):
            pr, pg, pb = (int(proh[i:i + 2], 16) for i in (0, 2, 4))
            if abs(col[0] - pr) <= 12 and abs(col[1] - pg) <= 12 and abs(col[2] - pb) <= 12:
                malos += n
                break
    print(f"  {Path(ruta).name:44s} {sz[0]}x{sz[1]}  prohibidos={100*malos/tot:.4f}%")
