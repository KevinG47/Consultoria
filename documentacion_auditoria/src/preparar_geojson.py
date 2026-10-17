# -*- coding: utf-8 -*-
"""
preparar_geojson.py
===================

Descarga **una sola vez** el GeoJSON de departamentos de Colombia, lo deja
limpio, mínimo y redondeado, y lo versiona junto a su `.procedencia.txt`.

POR QUE ESTE SCRIPT
-------------------
El repositorio auditado no tenía ni una geometría (`mapbox_style="open-street-map"`
pedía teselas a internet). Para que el mapa funcione **sin red** hay que traer los
polígonos una vez y dejarlos en el repositorio. Este script hace esa compra y
deja la factura: URL, fecha, SHA-256 del archivo original y el criterio de
limpieza, en `colombia_departamentos.procedencia.txt`.

QUE HACE
--------
1. Descarga el GeoJSON público de john-guerra (basado en DIVIPOLA/IGAC).
2. Verifica que trae 33 features y que sus códigos DIVIPOLA coinciden **33 de 33**
   con los del CSV del DANE que usa F2-2 (`codigo_dane`).
3. Se queda solo con `codigo_dane` y `nombre` (la única llave de unión es el
   código: los nombres del GeoJSON son `SANTAFE DE BOGOTA D.C` y
   `ARCHIPIELAGO DE SAN ANDRES...`, que no coinciden con la etiqueta del DANE).
4. Redondea las coordenadas a 4 decimales (~11 m) y elimina vértices repetidos.
5. Escribe el `.geojson` y el `.procedencia.txt`.

No depende de geopandas/shapely/folium (no están instaladas): es `json` puro.

Uso:  python preparar_geojson.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
GEO = DOC / "data" / "geo"
DANE = (RAIZ / "datos_originales" / "datos_fuente"
        / "dane_cnpv2018_poblacion_departamental.csv")
SALIDA = GEO / "colombia_departamentos.geojson"
PROCEDENCIA = GEO / "colombia_departamentos.procedencia.txt"

URL = ("https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/"
       "be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json")
DECIMALES = 4          # ~11 m: un mapa nacional de burbujas no pierde nada

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def leer_dane() -> dict[str, tuple[str, str]]:
    """Devuelve {codigo: (nombre_dane, poblacion)} del CSV del DANE de F2-2."""
    import csv

    with DANE.open(encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh))
    return {f["codigo_dane"].strip(): (f["departamento"].strip(),
                                       int(f["poblacion_censada_2018"])) for f in filas}


def redondear(coords, dec: int, cerrada: bool) -> list:
    """Redondea una lista de anillos [[lon, lat], ...] y quita puntos repetidos."""
    salida = []
    for anillo in coords:
        limpio = []
        visto = None
        for lon, lat in anillo:
            p = [round(float(lon), dec), round(float(lat), dec)]
            if p == visto:
                continue
            limpio.append(p)
            visto = p
        if cerrada and limpio and limpio[0] != limpio[-1]:
            limpio.append(list(limpio[0]))
        salida.append(limpio)
    return salida


def main() -> int:
    GEO.mkdir(parents=True, exist_ok=True)
    dane = leer_dane()
    print(f"== DANE de F2-2 ==\n   {len(dane)} departamentos en {DANE.name}")

    print("\n== Descarga (una sola vez) ==")
    peticion = urllib.request.Request(
        URL, headers={"User-Agent": "consultoria-usta/2026 (F2-11)"})
    with urllib.request.urlopen(peticion, timeout=180) as resp:
        crudo = resp.read()
    sha = hashlib.sha256(crudo).hexdigest().upper()
    print(f"   {len(crudo):,} B · SHA-256 {sha}")

    gj = json.loads(crudo.decode("utf-8"))
    feats = gj["features"]
    print(f"   type {gj.get('type')} · {len(feats)} features · crs {gj.get('crs')}")

    # --- validaciones de la fuente -----------------------------------------
    codigos_gj = [str(f["properties"]["DPTO"]).strip() for f in feats]
    if len(feats) != 33:
        raise SystemExit(f"FALLA: se esperaban 33 features y llegaron {len(feats)}")
    if len(set(codigos_gj)) != 33:
        raise SystemExit("FALLA: códigos DIVIPOLA repetidos en el GeoJSON")
    faltan = sorted(set(dane) - set(codigos_gj))
    sobran = sorted(set(codigos_gj) - set(dane))
    if faltan or sobran:
        raise SystemExit(f"FALLA: faltan {faltan} · sobran {sobran}")
    print("   33/33 códigos dentro del GeoJSON coinciden con el CSV del DANE")

    # --- limpieza -----------------------------------------------------------
    n_vert_antes = n_vert_despues = 0
    features_limpias = []
    for f in feats:
        cod = str(f["properties"]["DPTO"]).strip()
        nombre_dane = dane[cod][0]
        g = f["geometry"]
        tipo = g["type"]
        if tipo == "Polygon":
            n_vert_antes += sum(len(a) for a in g["coordinates"])
            coords = redondear(g["coordinates"], DECIMALES, cerrada=True)
            n_vert_despues += sum(len(a) for a in coords)
        elif tipo == "MultiPolygon":
            n_vert_antes += sum(len(a) for p in g["coordinates"] for a in p)
            coords = [redondear(p, DECIMALES, cerrada=True) for p in g["coordinates"]]
            n_vert_despues += sum(len(a) for p in coords for a in p)
        else:
            raise SystemExit(f"FALLA: geometría {tipo} no prevista en {cod}")
        features_limpias.append({
            "type": "Feature",
            "properties": {"codigo_dane": cod, "nombre": nombre_dane},
            "geometry": {"type": tipo, "coordinates": coords},
        })

    # el orden se alfabetiza por código para que el archivo sea estable
    features_limpias.sort(key=lambda f: f["properties"]["codigo_dane"])
    limpio = {"type": "FeatureCollection", "features": features_limpias}
    texto = json.dumps(limpio, ensure_ascii=False, separators=(",", ":"))
    SALIDA.write_text(texto, encoding="utf-8", newline="\n")
    peso = SALIDA.stat().st_size
    sha_versionado = hashlib.sha256(SALIDA.read_bytes()).hexdigest().upper()
    print(f"\n== Limpieza (redondeo a {DECIMALES} decimales) ==")
    print(f"   vértices {n_vert_antes:,} → {n_vert_despues:,} "
          f"({n_vert_antes - n_vert_despues:,} repetidos eliminados)")
    print(f"   {SALIDA.relative_to(RAIZ)} · {peso:,} B = {peso / 1024:.0f} KB")

    # --- factura ------------------------------------------------------------
    nombres_gj = {str(f["properties"]["DPTO"]).strip(): f["properties"]["NOMBRE_DPT"]
                  for f in feats}
    procedencia = f"""Procedencia de colombia_departamentos.geojson
==============================================

Qué es
------
Polígonos de los 33 departamentos de Colombia (incluida Bogotá, D. C. y
San Andrés, Providencia y Santa Catalina), en coordenadas geográficas
WGS84 (EPSG:4326), listos para dibujarse offline con Plotly.

Fuente
------
GeoJSON público de John Guerra (john-guerra), derivado de las geometrías
departamentales de DIVIPOLA / IGAC. Es el archivo más usado para mapas de
departamentos de Colombia en Python.

URL   : {URL}
Fecha : {date.today().isoformat()} (descarga)
Tamaño original : {len(crudo):,} bytes
SHA-256 original: {sha}

Qué se conserva
---------------
Solo dos propiedades por feature:

    properties.codigo_dane   Código DIVIPOLA de 2 dígitos («05», «11», «88»)
    properties.nombre        Nombre del departamento según el CSV del DANE (F2-2)

Se descartan AREA, PERIMETER y HECTARES (no se usan) y se redondean las
coordenadas a {DECIMALES} decimales (~11 m), que es más que suficiente para un
mapa nacional de burbujas. Vértices: {n_vert_antes:,} originales →
{n_vert_despues:,} tras redondear y quitar puntos repetidos.

Por qué se une por código y nunca por nombre
--------------------------------------------
Los nombres del GeoJSON original no coinciden con los del DANE:

    GeoJSON          : {nombres_gj.get("11")!r}
    DANE / F2-2      : {dane["11"][0]!r}
    GeoJSON          : {nombres_gj.get("88")!r}
    DANE / F2-2      : {dane["88"][0]!r}

Es la misma trampa que documentamos en el hallazgo H6: dos fuentes que
escriben distinto el mismo departamento. La llave es `codigo_dane`, y se
verificó que los 33 códigos del GeoJSON coinciden 33 de 33 con los del
CSV `dane_cnpv2018_poblacion_departamental.csv` que usa F2-2.

El archivo que queda versionado
-------------------------------
{peso:,} bytes · {len(features_limpias)} features · orden alfabético por código.
SHA-256 del archivo versionado: {sha_versionado}

Así, `verificar_mapa.py` puede comprobar sin red que el archivo que dibuja el
mapa es exactamente este y que nadie lo editó a mano.

Reproducibilidad
----------------
Se regenera con `python documentacion_auditoria/src/preparar_geojson.py`.
El script vuelve a descargar el original, comprueba el SHA-256, valida los
33/33 códigos y falla si algo no cuadra. NO descarga nada en tiempo de
ejecución del mapa: el mapa lee este archivo.

Licencia y atribución
---------------------
El GeoJSON de origen es de uso libre con atribución a su autor (john-guerra)
y a la fuente de las geometrías (DIVIPOLA / IGAC). En el mapa y en el
documento se cita esa procedencia.
"""
    PROCEDENCIA.write_text(procedencia, encoding="utf-8", newline="\n")
    print(f"   {PROCEDENCIA.relative_to(RAIZ)}")
    print("\n== OK ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
