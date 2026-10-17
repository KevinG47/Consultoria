# -*- coding: utf-8 -*-
"""
Consulta directa a la API de Socrata (dataset bqtm-4y2h) para saber con qué
separador decimal devuelve `EDAD_ANOS_PR`.

Esto resuelve si el CSV que escribe `src/ingesta/minciencias.py`
(`df.to_csv(SALIDA)`, sin normalizar el separador) alimenta correctamente el
pipeline o lo rompe.
"""
from __future__ import annotations

import io
import json
import ssl
import sys
import urllib.parse
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "https://www.datos.gov.co/resource/bqtm-4y2h.json"
UA = {"User-Agent": "Mozilla/5.0 consultoria-usta/1.0"}


def pedir(params: dict) -> tuple[int, object]:
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60,
                                context=ssl.create_default_context()) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


print("=== 3 registros crudos de la API ===")
try:
    st, datos = pedir({"$limit": 3})
    print(f"status {st}, {len(datos)} registros")
    for i, d in enumerate(datos, 1):
        claves = [k for k in d if "EDAD" in k.upper() or "CONVO" in k.upper()]
        print(f"  registro {i}: { {k: d[k] for k in claves} }")
    print(f"\n  claves del primer registro ({len(datos[0])}):")
    print(f"  {sorted(datos[0].keys())}")
except Exception as e:                                        # noqa: BLE001
    print(f"ERROR: {type(e).__name__}: {e}")

print("\n=== tipos y formato de EDAD_ANOS_PR sobre 200 registros ===")
try:
    st, datos = pedir({"$limit": 200,
                       "$select": "edad_anos_pr,id_convocatoria"})
    edades = [d.get("edad_anos_pr") for d in datos if d.get("edad_anos_pr")]
    tipos = {}
    for v in edades:
        tipos.setdefault(type(v).__name__, 0)
        tipos[type(v).__name__] += 1
    print(f"  tipos Python observados : {tipos}")
    con_coma = sum(1 for v in edades if isinstance(v, str) and "," in v)
    con_punto = sum(1 for v in edades if isinstance(v, str) and "." in v)
    print(f"  con COMA decimal        : {con_coma}")
    print(f"  con PUNTO decimal       : {con_punto}")
    print(f"  ejemplos                : {edades[:8]}")
except Exception as e:                                        # noqa: BLE001
    print(f"ERROR: {type(e).__name__}: {e}")

print("\n=== ¿qué escribiría pandas con to_csv? ===")
try:
    import pandas as pd
    st, datos = pedir({"$limit": 5, "$select": "edad_anos_pr"})
    df = pd.DataFrame.from_records(datos)
    print(f"  dtype tras from_records : {df['edad_anos_pr'].dtype}")
    csv = df.to_csv(index=False)
    print("  primeras líneas del CSV que produciría minciencias.py:")
    for linea in csv.strip().splitlines()[:4]:
        print(f"    {linea}")
except Exception as e:                                        # noqa: BLE001
    print(f"ERROR: {type(e).__name__}: {e}")
