# -*- coding: utf-8 -*-
"""Depura el orden real de las fichas en objetivo_3 y las capas asignadas."""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(r".\documentacion_auditoria\src").resolve()))
from generar_documento import capa_de_ruta, _cargar_capas  # noqa: E402

tex = Path(r".\documentacion_auditoria\latex\objetivo_3\secciones\03_codigo.tex").read_text(
    encoding="utf-8")
nombres = re.findall(r"\\subsubsection\{([^}]+)\}", tex)
print("n fichas:", len(nombres))
orden, _ = _cargar_capas()
print("orden capas:", orden)
for i, n in enumerate(nombres[:30]):
    c = capa_de_ruta(n)
    idx = orden.index(c) if c in orden else 99
    print(f"{i:3d} idx={idx:2d} {c:15s} {n}")
