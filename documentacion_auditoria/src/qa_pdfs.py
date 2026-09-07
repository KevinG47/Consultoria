# -*- coding: utf-8 -*-
"""QA final: páginas, commit, cobertura, fragmentos y glosario por documento."""
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
print(f"{'DOC':22s} {'PAG':>4} {'COMMIT':>7} {'COBERT':>7} {'EVID':>5} {'GLOS':>5}")
for doc in docs:
    d = pymupdf.open(rf".\documentacion_auditoria\pdf\{doc}.pdf")
    txt = "".join(d[i].get_text() for i in range(d.page_count))
    p0 = d[0].get_text()
    commit = "Commit auditado" in p0
    cob = "Cobertura:" in txt
    evid = txt.count("Evidencia en")
    glos = txt.count("Qué significa")
    print(f"{doc:22s} {d.page_count:4d} {str(commit):>7} {str(cob):>7} {evid:5d} {glos:5d}")
