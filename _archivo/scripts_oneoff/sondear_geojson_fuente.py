# -*- coding: utf-8 -*-
"""Sondeo del GeoJSON: descarga, estructura, codigos y pesos por redondeo."""
from __future__ import annotations

import io
import json
import sys
import urllib.request
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = ("https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/"
       "be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json")
with urllib.request.urlopen(URL, timeout=120) as r:
    crudo = r.read()
print(f"descargado {len(crudo)} bytes")

gj = json.loads(crudo.decode("utf-8"))
print("claves:", list(gj.keys()), "tipo:", gj.get("type"))
feats = gj["features"]
print(f"features: {len(feats)}")
print("props de la primera:", feats[0]["properties"])
print("geometria de la primera:", feats[0]["geometry"]["type"])

tipos = {}
n_vert = 0
for f in feats:
    g = f["geometry"]
    tipos[g["type"]] = tipos.get(g["type"], 0) + 1
    if g["type"] == "Polygon":
        anillos = g["coordinates"]
    else:
        anillos = [a for poly in g["coordinates"] for a in poly]
    for an in anillos:
        n_vert += len(an)
print("tipos:", tipos, "vertices:", n_vert)

for f in feats[:3]:
    print(" ", f["properties"].get("DPTO"), "·", f["properties"].get("NOMBRE_DPT"))
print("...")
for f in feats[-2:]:
    print(" ", f["properties"].get("DPTO"), "·", f["properties"].get("NOMBRE_DPT"))

codigos = [f["properties"].get("DPTO") for f in feats]
print("codigos:", codigos)
print("uniques:", len(set(codigos)))

# nombres raros
for f in feats:
    n = f["properties"].get("NOMBRE_DPT")
    if "SANTAFE" in str(n).upper() or "ARCHIPIELAGO" in str(n).upper():
        print("nombre especial:", n, "codigo", f["properties"].get("DPTO"))
