# -*- coding: utf-8 -*-
"""Prueba de parametrización: ¿cada PDF incluye solo los términos que usa?"""
import io
import sys

import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TERMINOS = ["HHI", "k-prototypes", "DuckDB", "Mojibake", "Sprint", "CRISP-DM"]
docs = ["objetivo_1", "objetivo_2", "objetivo_4", "objetivo_5", "objetivo_6",
        "objetivo_1_lite", "objetivo_2_lite", "objetivo_4_lite",
        "objetivo_5_lite", "objetivo_6_lite"]
print("Términos encontrados por documento (solo donde el doc los usa en prosa):")
for doc in docs:
    d = pymupdf.open(rf".\documentacion_auditoria\pdf\{doc}.pdf")
    txt = "".join(d[i].get_text() for i in range(d.page_count)).lower()
    presentes = [t for t in TERMINOS if t.lower() in txt]
    # ¿los términos presentes aparecen en el glosario? (buscar la fila del glosario)
    print(f"{doc:18s} usados: {', '.join(presentes) if presentes else 'ninguno'}")
