# -*- coding: utf-8 -*-
"""Verifica: (a) orden canónico de capas en objetivo_3; (b) contexto de 'Ã'."""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(r".\documentacion_auditoria\src").resolve()))
from generar_documento import capa_de_ruta  # noqa: E402

# (a) orden canónico real en objetivo_3/03_codigo.tex
tex = Path(r".\documentacion_auditoria\latex\objetivo_3\secciones\03_codigo.tex").read_text(
    encoding="utf-8")
nombres = re.findall(r"\\subsubsection\{([^}]+)\}", tex)
capas, visto = [], set()
for n in nombres:
    c = capa_de_ruta(n)
    if c != capas[-1] if capas else True:
        capas.append(c)
print("objetivo_3 capas en orden:", " -> ".join(capas))
print("fichas:", len(nombres))

# (b) contexto de cada 'Ã' en los tex
for p in Path(r".\documentacion_auditoria\latex").rglob("*.tex"):
    t = p.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"Ã", t):
        s = t[max(0, m.start() - 40):m.end() + 25].replace("\n", " ")
        print(f"{p.parent.parent.name}/{p.name}: ...{s}...")
