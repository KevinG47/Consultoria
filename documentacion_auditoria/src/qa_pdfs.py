# -*- coding: utf-8 -*-
"""QA de los PDFs de auditoría: páginas, glosario, relación, marcadores."""
import io
import sys

import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

docs = [
    "maestro_auditoria", "objetivo_1", "objetivo_2", "objetivo_3",
    "objetivo_4", "objetivo_5", "objetivo_6",
    "objetivo_1_lite", "objetivo_2_lite", "objetivo_3_lite",
    "objetivo_4_lite", "objetivo_5_lite", "objetivo_6_lite",
]
print(f"{'DOC':22s} {'PAGS':>5} {'GLOS':>5} {'REL':>5} {'FICHAS':>6}")
for doc in docs:
    d = pymupdf.open(rf".\documentacion_auditoria\pdf\{doc}.pdf")
    txt = "".join(d[i].get_text() for i in range(d.page_count))
    n_glos = txt.count("Qué significa")
    n_rel = txt.count("Relación con los demás")
    n_fichas = txt.count("Rol:")
    print(f"{doc:22s} {d.page_count:5d} {n_glos:5d} {n_rel:5d} {n_fichas:6d}")
