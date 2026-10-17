# -*- coding: utf-8 -*-
"""
Sondeo de fuentes de GeoJSON de departamentos de Colombia.

Solo investiga: descarga a una carpeta temporal fuera del repositorio, cuenta
features, comprueba si trae código DIVIPOLA y mide el peso. No escribe nada en
el proyecto.
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FUENTES = [
    ("john-guerra/Colombia.geo.json",
     "https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/"
     "be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json"),
    ("datasketch/municipios (ArcGIS)", None),   # se omite: requiere servicio
    ("geonode Colombia departamentos",
     "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/"
     "colombia/colombia-departamentos.json"),
]

tmp = Path(tempfile.mkdtemp(prefix="geojson_"))
print(f"temporal: {tmp}\n")

for nombre, url in FUENTES:
    if not url:
        print(f"- {nombre}: omitida")
        continue
    print(f"- {nombre}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "estudio-viabilidad"})
        with urllib.request.urlopen(req, timeout=45) as r:
            crudo = r.read()
        print(f"    descargado: {len(crudo):,} B ({len(crudo)/1024:.0f} KB)"
              .replace(",", " "))
        obj = json.loads(crudo.decode("utf-8"))
        tipo = obj.get("type")
        print(f"    tipo: {tipo}")
        if tipo == "Topology":
            objs = obj.get("objects", {})
            print(f"    objetos: {list(objs)}")
            claves = [k for k in objs if "objeto" in k or "dep" in k.lower()
                      or k.lower().startswith("col")]
            print(f"    nombres de objeto candidatos: {claves}")
            geoms = objs[list(objs)[0]].get("geometries", [])
            print(f"    geometrías en «{list(objs)[0]}»: {len(geoms)}")
            props = [g.get("properties", {}) for g in geoms[:3]]
        else:
            feats = obj.get("features", [])
            print(f"    features: {len(feats)}")
            props = [f.get("properties", {}) for f in feats[:3]]
        print(f"    propiedades de las 3 primeras:")
        for p in props:
            print(f"      {p}")
        # ¿Se pueden aplanar y guardar?
        destino = tmp / (nombre.split("/")[-1])
        destino.write_bytes(crudo)
    except Exception as exc:                                   # noqa: BLE001
        print(f"    FALLO: {type(exc).__name__}: {exc}")
    print()
