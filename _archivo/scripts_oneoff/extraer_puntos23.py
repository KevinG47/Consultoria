# -*- coding: utf-8 -*-
"""Extrae: (2) sección 2 del objetivo_6_lite.pdf y (3) glosarios de criterios 4 y 6."""
import io
import re
import sys
from pathlib import Path

import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
OUT = Path(r".\documentacion_auditoria\data\qa")
OUT.mkdir(parents=True, exist_ok=True)


def texto(doc: str) -> str:
    d = pymupdf.open(rf".\documentacion_auditoria\pdf\{doc}.pdf")
    return "".join(d[i].get_text() for i in range(d.page_count))


# ---------- Punto 2: sección 2 de objetivo_6_lite ----------
t = texto("objetivo_6_lite")
m = re.search(r"2\s+Línea de tiempo de commits(.*?)3\s+Relación con los demás", t, re.S)
seccion2 = m.group(1) if m else "(no se encontró el corte 2->3)"
(OUT / "punto2_seccion2_objetivo6_lite.txt").write_text(seccion2, encoding="utf-8")
print("Punto 2: sección 2 de objetivo_6_lite extraída a punto2_seccion2_objetivo6_lite.txt")
print("=" * 70)
print(seccion2[:3000])

# ---------- Punto 3: glosarios de criterios 4 y 6 ----------
for doc in ["objetivo_4", "objetivo_4_lite", "objetivo_6", "objetivo_6_lite"]:
    t = texto(doc)
    gl = re.search(r"Glosario de términos presentes en este documento(.*?)(?:Relación con los demás|Conclusiones)", t, re.S)
    cuerpo_gl = gl.group(1) if gl else "(sin glosario)"
    tiene_pipeline = "ETL / pipeline" in cuerpo_gl
    usa_pipeline_cuerpo = re.search(r"pipeline|etl", t, re.I) is not None
    print("=" * 70)
    print(f"Punto 3: {doc} | fila 'ETL / pipeline' presente: {tiene_pipeline} | 'pipeline/etl' en el doc: {usa_pipeline_cuerpo}")
    print("--- glosario ---")
    print(cuerpo_gl[:1500])
