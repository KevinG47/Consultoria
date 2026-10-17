# -*- coding: utf-8 -*-
"""
¿Cuánto pesa el GeoJSON una vez limpio? y ¿coinciden los códigos DIVIPOLA con
los del DANE que ya usa F2-2?

Se prueban tres niveles de detalle (decimales de redondeo) sobre una COPIA
temporal. No escribe nada en el repositorio.
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
DANE = (RAIZ / "01_datos" / "datos_fuente"
        / "dane_cnpv2018_poblacion_departamental.csv")
URL = ("https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/"
       "be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json")

tmp = Path(tempfile.mkdtemp(prefix="geojson_medir_"))
req = urllib.request.Request(URL, headers={"User-Agent": "estudio-viabilidad"})
with urllib.request.urlopen(req, timeout=60) as r:
    crudo = r.read()
gj = json.loads(crudo.decode("utf-8"))
print(f"original: {len(crudo):,} B ({len(crudo)/1024:.0f} KB)".replace(",", " "))


def podar(geo: dict, nd: int) -> dict:
    """Quita propiedades sobrantes y redondea coordenadas a nd decimales."""
    salida = {"type": "FeatureCollection", "features": []}
    for f in geo["features"]:
        p = f["properties"]
        geom = f["geometry"]

        def ronda(c):
            if isinstance(c, list):
                if c and isinstance(c[0], (int, float)):
                    return [round(float(x), nd) for x in c]
                return [ronda(x) for x in c]
            return c

        salida["features"].append({
            "type": "Feature",
            "properties": {"codigo_dane": str(p["DPTO"]).zfill(2),
                           "departamento": str(p["NOMBRE_DPT"]).title()},
            "geometry": {"type": geom["type"], "coordinates": ronda(geom["coordinates"])},
        })
    return salida


def n_vertices(geo: dict) -> int:
    def cuenta(c):
        if isinstance(c, list):
            if c and isinstance(c[0], (int, float)):
                return 1
            return sum(cuenta(x) for x in c)
        return 0
    return sum(cuenta(f["geometry"]["coordinates"]) for f in geo["features"])


print(f"vértices: {n_vertices(gj):,}".replace(",", " "))
print()
for nd in (2, 3, 4, 6):
    g = podar(gj, nd)
    t = json.dumps(g, ensure_ascii=False, separators=(",", ":"))
    print(f"  redondeo a {nd} decimales: {len(t.encode()):,} B "
          f"({len(t.encode())/1024:.0f} KB)".replace(",", " "))

print("\n=== ¿coinciden los 33 códigos con los del DANE que usa F2-2? ===")
dane = pd.read_csv(DANE, dtype={"codigo_dane": str})
cod_dane = set(dane["codigo_dane"].str.zfill(2))
cod_geo = {str(f["properties"]["DPTO"]).zfill(2) for f in gj["features"]}
print(f"  códigos DANE: {len(cod_dane)} · códigos GeoJSON: {len(cod_geo)}")
print(f"  en DANE y no en GeoJSON: {sorted(cod_dane - cod_geo)}")
print(f"  en GeoJSON y no en DANE: {sorted(cod_geo - cod_dane)}")
print(f"  intersección: {len(cod_dane & cod_geo)}")

print("\n=== nombres del GeoJSON (para ver la trampa de San Andrés) ===")
for f in gj["features"]:
    n = str(f["properties"]["NOMBRE_DPT"])
    if "SAN" in n or "BOGOT" in n:
        print(f"  {f['properties']['DPTO']}: {n}")
