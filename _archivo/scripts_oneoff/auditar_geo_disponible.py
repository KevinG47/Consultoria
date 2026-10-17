# -*- coding: utf-8 -*-
"""Qué hay disponible para mapas: librerías y geometrías."""
from __future__ import annotations

import io
import importlib
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

print("=== librerías geográficas ===")
for m in ("geopandas", "shapely", "pyproj", "folium", "plotly", "pydeck",
          "branca", "fiona", "rasterio", "contextily"):
    try:
        mod = importlib.import_module(m)
        print(f"  {m:12} {getattr(mod, '__version__', '?')}")
    except Exception:
        print(f"  {m:12} NO instalada")

print("\n=== ¿plotly puede dibujar polígonos de un GeoJSON local sin red? ===")
import plotly
import plotly.graph_objects as go
from pathlib import Path
print(f"  plotly {plotly.__version__}")
p = Path(plotly.__file__).parent / "package_data" / "plotly.min.js"
print(f"  bundle: {p.stat().st_size / 1024 / 1024:.2f} MiB")
txt = p.read_text(encoding="utf-8", errors="replace")
for aguja in ("topojson", "geometry", "choropleth", "geojson", "scattergeo",
              "maplibre", "mapbox"):
    print(f"  ¿el bundle menciona {aguja:12}? {aguja in txt}")
