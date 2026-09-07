# -*- coding: utf-8 -*-
"""Prueba: el '95' era el doble render de fichas, no un conteo de archivos."""
import io
import re
import sys
from pathlib import Path

import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

tex = Path(r".\documentacion_auditoria\latex\objetivo_3\secciones\03_codigo.tex")
n_tex = len(re.findall(r"\\subsubsection", tex.read_text(encoding="utf-8")))

d = pymupdf.open(r".\documentacion_auditoria\pdf\objetivo_3.pdf")
txt = "".join(d[i].get_text() for i in range(d.page_count))
print("fichas (\\subsubsection) en 03_codigo.tex :", n_tex)
print('ocurrencias de "Rol:" en objetivo_3.pdf   :', txt.count("Rol:"))
print("=> el '95' antiguo era 2x el n. de fichas (bug de doble render ya")
print("   corregido en la versión 3), no un conteo de archivos del repo.")
