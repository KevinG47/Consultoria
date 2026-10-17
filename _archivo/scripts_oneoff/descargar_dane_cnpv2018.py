# -*- coding: utf-8 -*-
"""
descargar_dane_cnpv2018.py
==========================

Descarga el cuadro oficial del DANE con la población del Censo Nacional de
Población y Vivienda 2018 (CNPV 2018) y localiza la hoja/columnas que contienen
la población total por departamento.

Por qué un script aparte
------------------------
El entorno de calificación puede no tener red. Este script es el paso de
ADQUISICIÓN: se ejecuta una vez, deja la tabla derivada versionada como CSV
pequeño con procedencia, y el análisis de F2-2 lee ese CSV sin red.

Uso:
    python _archivo/scripts_oneoff/descargar_dane_cnpv2018.py

Salida:
    _archivo/tmp_dane/PERSONAS_DEMOGRAFICO_Cuadros_CNPV_2018.xlsx  (original)
    + volcado de estructura de hojas por consola
"""

from __future__ import annotations

import hashlib
import io
import ssl
import sys
import urllib.request
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DESTINO = RAIZ / "_archivo" / "tmp_dane"
DESTINO.mkdir(parents=True, exist_ok=True)

URL = ("https://www.dane.gov.co/files/censo2018/informacion-tecnica/"
       "PERSONAS_DEMOGRAFICO_Cuadros_CNPV_2018.xlsx")
NOMBRE = URL.rsplit("/", 1)[-1]
ARCHIVO = DESTINO / NOMBRE

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) consultoria-usta/1.0"}


def descargar() -> Path:
    if ARCHIVO.exists():
        print(f"[=] Ya existe: {ARCHIVO.name} ({ARCHIVO.stat().st_size:,} B)")
        return ARCHIVO
    print(f"[1] Descargando {URL}")
    ctx = ssl.create_default_context()
    req = urllib.request.Request(URL, headers=UA)
    with urllib.request.urlopen(req, timeout=180, context=ctx) as r:
        crudo = r.read()
    ARCHIVO.write_bytes(crudo)
    print(f"    {len(crudo):,} bytes -> {ARCHIVO}")
    return ARCHIVO


def inspeccionar(ruta: Path) -> None:
    """Lista hojas y, para cada una, sus primeras filas y dimensiones."""
    import openpyxl

    sha = hashlib.sha256(ruta.read_bytes()).hexdigest().upper()
    print(f"\n[2] SHA-256: {sha}")
    print(f"    bytes  : {ruta.stat().st_size:,}")

    wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
    print(f"\n[3] Hojas ({len(wb.sheetnames)}):")
    for nombre in wb.sheetnames:
        ws = wb[nombre]
        print(f"  - {nombre!r}  dims={ws.calculate_dimension()} "
              f"filas={ws.max_row} columnas={ws.max_column}")

    print("\n[4] Primeras 12 filas de cada hoja:")
    for nombre in wb.sheetnames:
        ws = wb[nombre]
        print(f"\n--- {nombre} ---")
        for i, fila in enumerate(ws.iter_rows(values_only=True), start=1):
            if i > 12:
                break
            celdas = ["" if c is None else str(c)[:28] for c in fila[:8]]
            print(f"   {i:3d} | " + " | ".join(celdas))
    wb.close()


if __name__ == "__main__":
    ruta = descargar()
    inspeccionar(ruta)
