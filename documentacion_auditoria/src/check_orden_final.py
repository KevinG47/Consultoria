# -*- coding: utf-8 -*-
"""Verificación DEFINITIVA del orden canónico (desescapa los nombres del tex)."""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(r".\documentacion_auditoria\src").resolve()))
from generar_documento import capa_de_ruta, _cargar_capas  # noqa: E402

def desescapar(nombre: str) -> str:
    return nombre.replace("\\_", "_").replace("\\textbackslash{}", "\\")

for doc, texp in [
    ("objetivo_3", r".\documentacion_auditoria\latex\objetivo_3\secciones\03_codigo.tex"),
    ("maestro", r".\documentacion_auditoria\latex\maestro_auditoria\secciones\05_codigo.tex"),
    ("objetivo_3_lite", r".\documentacion_auditoria\latex\objetivo_3_lite\secciones\03_codigo.tex"),
]:
    tex = Path(texp).read_text(encoding="utf-8")
    nombres = [desescapar(n) for n in re.findall(r"\\subsubsection\{([^}]+)\}", tex)]
    seq = []
    for n in nombres:
        c = capa_de_ruta(n)
        if not seq or seq[-1] != c:
            seq.append(c)
    canónico = ["ingesta", "transformacion", "modelo", "analisis", "orquestacion",
                "visualizacion", "documentacion", "eda", "testing", "legacy", "otro"]
    esperado = [c for c in canónico if c in seq]
    ok = seq == esperado
    print(f"{doc:16s} fichas={len(nombres):3d} orden={'OK' if ok else 'INCORRECTO'}")
    if not ok:
        print("   real:", " -> ".join(seq))
        print("   esp.:", " -> ".join(esperado))
