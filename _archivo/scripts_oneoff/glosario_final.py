# -*- coding: utf-8 -*-
"""Extrae los glosarios COMPLETOS de criterios 4 y 6 (full + lite)."""
import io
import re
import sys
from pathlib import Path

import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

GLOSARIO_TERMINOS = [
    "HHI (Herfindahl-Hirschman)", "Matriz de transición", "Tasa de retención",
    "Representación relativa", "k-prototypes", "MCA / FAMD", "CRISP-DM",
    "Modelo dimensional (esquema estrella)", "DuckDB", "Mojibake",
    "Contrato de esquema", "ETL", "Pipeline", "CI/CD y Docker", "Sprint",
]

for doc in ["objetivo_4", "objetivo_4_lite", "objetivo_6", "objetivo_6_lite"]:
    d = pymupdf.open(rf".\documentacion_auditoria\pdf\{doc}.pdf")
    txt = "".join(d[i].get_text() for i in range(d.page_count))
    # Sección de glosario: entre 'Glosario (solo los términos' y 'Relación con los demás'
    m = re.search(
        r"Glosario de términos presentes en este documento(.*?)Relación con los demás",
        txt, re.S)
    seg = m.group(1) if m else ""
    presentes = [t for t in GLOSARIO_TERMINOS if t in seg]
    print("=" * 70)
    print(f"{doc} — GLOSARIO FINAL (entradas presentes):")
    print("   " + (" | ".join(presentes) if presentes else "(ninguna)"))
