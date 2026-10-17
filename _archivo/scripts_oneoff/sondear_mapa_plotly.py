# -*- coding: utf-8 -*-
"""
SONDEO (no entregable): comprobar que Plotly dibuja polígonos + burbujas + líneas
de flujo con un GeoJSON embebido, sin red, y cuánto pesa el HTML resultante.

No es el mapa de F2-11: no lee los datos de F2-2, no calcula flujos y no escribe
en el repositorio. Solo comprueba que la técnica funciona y cuánto ocupa.
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

import plotly
import plotly.graph_objects as go
import plotly.io as pio

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = ("https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/"
       "be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json")
tmp = Path(tempfile.mkdtemp(prefix="sondeo_mapa_"))
req = urllib.request.Request(URL, headers={"User-Agent": "estudio-viabilidad"})
with urllib.request.urlopen(req, timeout=60) as r:
    gj = json.loads(r.read().decode("utf-8"))


def podar(geo, nd=4):
    out = {"type": "FeatureCollection", "features": []}
    def ronda(c):
        if isinstance(c, list):
            if c and isinstance(c[0], (int, float)):
                return [round(float(x), nd) for x in c]
            return [ronda(x) for x in c]
        return c
    for f in geo["features"]:
        out["features"].append({
            "type": "Feature",
            "properties": {"codigo_dane": str(f["properties"]["DPTO"]).zfill(2),
                           "departamento": str(f["properties"]["NOMBRE_DPT"]).title()},
            "geometry": {"type": f["geometry"]["type"],
                         "coordinates": ronda(f["geometry"]["coordinates"])}})
    return out


geo = podar(gj)
codigos = [f["properties"]["codigo_dane"] for f in geo["features"]]
# Valores de juguete: solo para ver que el polígono y los puntos se dibujan.
z = [float(c) for c in codigos]
centros = {"11": (-74.07, 4.71), "05": (-75.34, 7.19), "76": (-76.51, 3.80),
           "08": (-74.87, 10.69)}

fig = go.Figure()
fig.add_trace(go.Choropleth(
    geojson=geo, locations=codigos, z=z, featureidkey="properties.codigo_dane",
    colorscale=[[0, "#EAF0F9"], [1, "#1E3780"]], marker_line_color="#FFFFFF",
    marker_line_width=0.6, showscale=False))
fig.add_trace(go.Scattergeo(
    lon=[v[0] for v in centros.values()], lat=[v[1] for v in centros.values()],
    mode="markers", marker=dict(size=[12, 30, 18, 9], color="#B7871E",
                                line=dict(color="#FFFFFF", width=1)),
    text=["Bogotá", "Antioquia", "Valle", "Atlántico"]))
# Una «línea de flujo»: Antioquia -> Bogotá, con marca en el destino.
fig.add_trace(go.Scattergeo(
    lon=[-75.34, -74.07], lat=[7.19, 4.71], mode="lines+markers",
    line=dict(width=2, color="#4A6BA8"),
    marker=dict(size=[0, 9], symbol=["circle", "triangle-up"], color="#1E3780")))
fig.update_geos(fitbounds="locations", visible=False,
                showcountries=False, showcoastlines=False, showland=False,
                bgcolor="#F8FAFC", projection_type="mercator")
fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=560,
                  paper_bgcolor="#F8FAFC")

bundle = (Path(plotly.__file__).parent / "package_data" / "plotly.min.js").read_text(
    encoding="utf-8").replace("</script>", "<\\/script>")
cuerpo = pio.to_html(fig, include_plotlyjs=False, full_html=False)
html = (f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<script>{bundle}</script></head><body>{cuerpo}</body></html>")
salida = tmp / "sondeo.html"
salida.write_text(html, encoding="utf-8")

print(f"GeoJSON limpio : {len(json.dumps(geo, separators=(',', ':')).encode()):,} B"
      .replace(",", " "))
print(f"HTML del sondeo: {salida.stat().st_size:,} B "
      f"({salida.stat().st_size/1024/1024:.2f} MiB)".replace(",", " "))
print(f"trazas          : {len(fig.data)} "
      f"({[t.type for t in fig.data]})")
sin_bundle = lugar = html.replace(bundle, "")
for aguja in ("src=\"http", "href=\"http", "cdn.", "jsdelivr", "url(http"):
    print(f"  ¿{aguja:12} en el documento? {aguja in lugar}")
print(f"\nsondeo en: {salida}")
