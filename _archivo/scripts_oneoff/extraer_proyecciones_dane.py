# -*- coding: utf-8 -*-
"""
extraer_proyecciones_dane.py
============================

Extrae de las proyecciones departamentales del DANE (PPED-AreaDep-2018-2050_VP)
la población total por departamento para 2018 y 2021, y la versiona como CSV.

Se usa como COMPROBACIÓN DE ROBUSTEZ en F2-2:
  * 2018 -> población AJUSTADA por omisión, comparable con la censada del
    cuadro 1PD (que es la base principal del análisis);
  * 2021 -> denominador emparejado por año para la última convocatoria, porque
    comparar investigadores de 2021 contra población de 2018 es anacrónico.

Uso:
    python _archivo/scripts_oneoff/extraer_proyecciones_dane.py
"""

from __future__ import annotations

import csv
import hashlib
import io
import sys
from pathlib import Path

import openpyxl

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
XLSX = RAIZ / "_archivo" / "tmp_dane" / "PPED-AreaDep-2018-2050_VP.xlsx"
SALIDA = (RAIZ / "01_datos" / "datos_fuente"
          / "dane_proyecciones_poblacion_departamental.csv")
URL = ("https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/"
       "Departamental/PPED-AreaDep-2018-2050_VP.xlsx")
ANIOS = (2018, 2021)

wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
ws = wb["PobDepartamentalxÁrea"]

# Localizar la fila de encabezado (la que contiene 'DP')
cabecera = None
filas_crudas = []
for i, fila in enumerate(ws.iter_rows(values_only=True), start=1):
    if cabecera is None:
        if fila and any(str(c).strip() == "DP" for c in fila if c is not None):
            cabecera = {str(c).strip(): j for j, c in enumerate(fila)
                        if c is not None}
            continue
    elif fila and len(fila) > 4 and fila[0] is not None:
        filas_crudas.append(fila)
wb.close()

print(f"Encabezado en columnas: {cabecera}")
i_dp, i_nom = cabecera["DP"], cabecera["DPNOM"]
i_anio, i_area, i_tot = cabecera["AÑO"], cabecera["ÁREA GEOGRÁFICA"], cabecera["TOTAL"]

anios_presentes = sorted({int(f[i_anio]) for f in filas_crudas if f[i_anio]})
print(f"Filas de datos: {len(filas_crudas)}")
print(f"Años: {anios_presentes[0]}..{anios_presentes[-1]} ({len(anios_presentes)} años)")
print(f"Áreas: {sorted({str(f[i_area]).strip() for f in filas_crudas})}")

# Nacional por año (el cuaderno publica el total nacional como DP = 00 o similar)
nacionales = {int(f[i_anio]): int(f[i_tot]) for f in filas_crudas
              if str(f[i_dp]).strip().zfill(2) not in ("05",)
              and str(f[i_area]).strip().lower() == "total"
              and str(f[i_nom]).strip().lower().startswith("total")}
print(f"Filas 'Total nacional' detectadas: { {k: f'{v:,}' for k, v in nacionales.items()} }")

datos: list[dict] = []
for f in filas_crudas:
    if str(f[i_area]).strip().lower() != "total":
        continue
    anio = int(f[i_anio])
    if anio not in ANIOS:
        continue
    nombre = str(f[i_nom]).strip()
    if nombre.lower().startswith("total"):
        continue
    datos.append({"codigo": str(f[i_dp]).strip().zfill(2), "departamento": nombre,
                  "anio": anio, "poblacion": int(f[i_tot])})

for anio in ANIOS:
    sub = [d for d in datos if d["anio"] == anio]
    suma = sum(d["poblacion"] for d in sub)
    print(f"\n{anio}: {len(sub)} departamentos, suma={suma:,}")

# --- escritura en formato largo ------------------------------------------
SALIDA.parent.mkdir(parents=True, exist_ok=True)
with open(SALIDA, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["codigo_dane", "departamento", "anio", "poblacion_proyectada"])
    for d in sorted(datos, key=lambda x: (x["anio"], x["codigo"])):
        w.writerow([d["codigo"], d["departamento"], d["anio"], d["poblacion"]])
print(f"\nEscrito {SALIDA.relative_to(RAIZ)} ({SALIDA.stat().st_size:,} bytes)")

sha = hashlib.sha256(XLSX.read_bytes()).hexdigest().upper()
with open(SALIDA.with_suffix(".procedencia.txt"), "w", encoding="utf-8") as fh:
    fh.write(
        "Procedencia de dane_proyecciones_poblacion_departamental.csv\n"
        "===========================================================\n\n"
        "Fuente : DANE — Proyecciones de población departamentales, basadas en el\n"
        "         CNPV 2018 (serie actualizada, archivo «VP»).\n"
        f"Archivo: {XLSX.name}\n"
        f"URL    : {URL}\n"
        f"SHA-256: {sha}\n"
        f"Tamaño : {XLSX.stat().st_size:,} bytes\n\n"
        "Qué se toma\n"
        "------------\n"
        "Hoja «PobDepartamentalxÁrea», filas con ÁREA GEOGRÁFICA = 'Total',\n"
        "para los años 2018 y 2021, columna TOTAL.\n\n"
        "Diferencia frente a la población censada\n"
        "---------------------------------------\n"
        "Estas proyecciones incorporan el AJUSTE POR OMISIÓN censal, de modo que\n"
        "son mayores que la población efectivamente censada del cuadro 1PD:\n"
        "Antioquia 6.407.149 (proyectada) frente a 5.974.788 (censada);\n"
        "Bogotá 7.391.056 frente a 7.181.469.\n"
        "La población censada es la base principal de F2-2 por ser la que publica\n"
        "directamente el cuadro oficial; la proyectada se usa como comprobación de\n"
        "robustez y, para 2021, como denominador emparejado por año.\n"
    )
print(f"Escrita la procedencia ({SALIDA.with_suffix('.procedencia.txt').name})")
print(f"SHA-256 del cuaderno: {sha}")
