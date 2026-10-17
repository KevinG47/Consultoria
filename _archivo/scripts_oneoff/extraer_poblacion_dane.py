# -*- coding: utf-8 -*-
"""
extraer_poblacion_dane.py
=========================

Extrae del cuaderno OFICIAL del DANE (CNPV 2018, cuadro 1PD) la población total
censada por departamento y la deja versionada como CSV pequeño con procedencia.

El análisis de F2-2 (per cápita) lee ese CSV: así es reproducible sin red.

Validaciones internas (abortan si fallan):
  * la suma de los departamentos debe igualar el "Total Nacional" del cuadro;
  * deben aparecer exactamente 33 unidades (32 departamentos + Bogotá D. C.);
  * la suma de hombres + mujeres debe igualar el total de cada fila.

Uso:
    python _archivo/scripts_oneoff/extraer_poblacion_dane.py
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
XLSX = (RAIZ / "_archivo" / "tmp_dane"
        / "PERSONAS_DEMOGRAFICO_Cuadros_CNPV_2018.xlsx")
SALIDA = (RAIZ / "datos_originales" / "datos_fuente"
          / "dane_cnpv2018_poblacion_departamental.csv")
URL = ("https://www.dane.gov.co/files/censo2018/informacion-tecnica/"
       "PERSONAS_DEMOGRAFICO_Cuadros_CNPV_2018.xlsx")

# El cuaderno etiqueta cada bloque como "<codigo>_<nombre>" (p. ej. "5_Antioquia",
# "88_Archipiélago de San Andrés, ..."). El código es el DIVIPOLA de 2 dígitos y
# es la clave estable; el nombre se normaliza a la forma oficial para que el CSV
# sea legible. `NOMBRE_OFICIAL` solo se usa cuando el nombre del cuaderno difiere.
NOMBRE_OFICIAL = {
    "11": "Bogotá, D. C.",
    "63": "Quindío",
    "88": "San Andrés, Providencia y Santa Catalina",
    "5": "Antioquia",
    "8": "Atlántico",
}
# Orden oficial DIVIPOLA (32 departamentos + Bogotá D. C.)
ORDEN = ["05", "08", "11", "13", "15", "17", "18", "19", "20", "23", "25", "27",
         "41", "44", "47", "50", "52", "54", "63", "66", "68", "70", "73", "76",
         "81", "85", "86", "88", "91", "94", "95", "97", "99"]


def partir_etiqueta(etiqueta: str) -> tuple[str, str]:
    """'5_Antioquia' -> ('05', 'Antioquia'); '11_Bogotá, D.C.' -> ('11', ...)."""
    crudo = etiqueta.strip()
    if "_" not in crudo:
        raise ValueError(f"Etiqueta sin código DIVIPOLA: {etiqueta!r}")
    codigo, nombre = crudo.split("_", 1)
    codigo = codigo.strip().zfill(2)
    nombre = nombre.strip()
    return codigo, NOMBRE_OFICIAL.get(codigo, nombre)


def extraer() -> tuple[list[dict], int]:
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb["1PD"]

    filas: list[dict] = []
    nacional: int | None = None
    depto_actual = ""

    for fila in ws.iter_rows(min_row=12, values_only=True):
        a, b, c, total = fila[0], fila[1], fila[2], fila[3]
        if a is not None and str(a).strip():
            depto_actual = str(a).strip()
        area = "" if b is None else str(b).strip()
        edad = "" if c is None else str(c).strip()
        if area != "Total" or edad != "Total":
            continue
        if not isinstance(total, (int, float)):
            continue
        total = int(total)
        if depto_actual.lower().startswith("total nacional"):
            nacional = total
            continue
        codigo, nombre = partir_etiqueta(depto_actual)
        filas.append({
            "codigo": codigo,
            "departamento": nombre,
            "etiqueta_cuaderno": depto_actual,
            "total": total,
            "hombres": int(fila[4] or 0),
            "mujeres": int(fila[5] or 0),
        })
    wb.close()
    if nacional is None:
        raise SystemExit("ERROR: no se encontró la fila 'Total Nacional'.")
    return filas, nacional


def main() -> int:
    print(f"[1] Leyendo {XLSX.name}")
    filas, nacional = extraer()
    print(f"    unidades departamentales encontradas: {len(filas)}")
    print(f"    Total Nacional (cuadro 1PD)          : {nacional:,}")

    # --- validaciones -----------------------------------------------------
    suma = sum(f["total"] for f in filas)
    print(f"    suma de departamentos                : {suma:,}")
    if len(filas) != 33:
        raise SystemExit(f"ERROR: se esperaban 33 unidades, hay {len(filas)}")
    codigos = {f["codigo"] for f in filas}
    faltan = set(ORDEN) - codigos
    sobran = codigos - set(ORDEN)
    if faltan or sobran:
        raise SystemExit(f"ERROR de códigos. faltan={faltan} sobran={sobran}")
    if suma != nacional:
        raise SystemExit(f"ERROR: suma {suma:,} != nacional {nacional:,}")
    for f in filas:
        if f["hombres"] + f["mujeres"] != f["total"]:
            raise SystemExit(f"ERROR: sexo no cuadra en {f['departamento']}")
    print("    [OK] 33 unidades, códigos DIVIPOLA completos, suma == Total "
          "Nacional, sexo cuadra")

    # --- escritura --------------------------------------------------------
    filas.sort(key=lambda f: f["codigo"])
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["codigo_dane", "departamento", "poblacion_censada_2018",
                    "hombres", "mujeres"])
        for f in filas:
            w.writerow([f["codigo"], f["departamento"], f["total"],
                        f["hombres"], f["mujeres"]])
    print(f"\n[2] Escrito {SALIDA.relative_to(RAIZ)}")
    print(f"    {SALIDA.stat().st_size:,} bytes")

    sha_origen = hashlib.sha256(XLSX.read_bytes()).hexdigest().upper()
    with open(SALIDA.with_suffix(".procedencia.txt"), "w", encoding="utf-8") as fh:
        fh.write(
            "Procedencia de dane_cnpv2018_poblacion_departamental.csv\n"
            "========================================================\n\n"
            "Fuente : DANE — Censo Nacional de Población y Vivienda 2018 (CNPV 2018)\n"
            "Cuadro : 1PD «Población total censada, por sexo e índices de masculinidad\n"
            "         y feminidad, según departamentos, áreas (Total, Cabecera y\n"
            "         Centros poblados y Rural disperso)»\n"
            f"Archivo: {URL.rsplit('/', 1)[-1]}\n"
            f"URL    : {URL}\n"
            f"SHA-256: {sha_origen}\n"
            f"Tamaño : {XLSX.stat().st_size:,} bytes\n\n"
            "Qué se toma\n"
            "------------\n"
            "De cada bloque departamental se toma la fila con área = 'Total' y\n"
            "grupo de edad = 'Total', es decir la POBLACIÓN TOTAL CENSADA del\n"
            "departamento en 2018 (no la ajustada por omisión censal).\n"
            f"Total Nacional del cuadro: {nacional:,}\n"
            f"Suma de los 33 departamentos: {suma:,} (idéntica).\n\n"
            "Advertencia metodológica\n"
            "------------------------\n"
            "La población CENSADA subestima la población real porque el CNPV 2018\n"
            "tuvo omisión. La población oficial ajustada por omisión es superior\n"
            "(48.258.494 a nivel nacional). Se usa la cifra censada porque es la\n"
            "que publica directamente el cuadro oficial descargado y permite que\n"
            "el cálculo sea reproducible sin depender de un modelo de ajuste.\n"
            "El efecto sobre las tasas por 100.000 habitantes se discute en el\n"
            "informe de F2-2.\n"
        )
    print(f"[3] Escrita la procedencia "
          f"{SALIDA.with_suffix('.procedencia.txt').name}")
    print(f"\n    SHA-256 del cuaderno origen: {sha_origen}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
