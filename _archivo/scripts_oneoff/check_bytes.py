# -*- coding: utf-8 -*-
"""Verifica los bytes del fragmento 'SÍ' en los .tex generados."""
from pathlib import Path

for ruta in [
    r".\documentacion_auditoria\latex\objetivo_3\secciones\03_codigo.tex",
    r".\documentacion_auditoria\latex\maestro_auditoria\secciones\05_codigo.tex",
]:
    b = Path(ruta).read_bytes()
    hay = b.decode("utf-8", errors="replace")
    i = hay.find('ID_VICTIMA_CONFLICTO"] == "')
    if i < 0:
        print(f"{ruta}: patrón no encontrado")
        continue
    # encontrar la posición en bytes del inicio del patrón dentro de hay
    inicio = i + hay[i:i + 40].find('== "') + 4
    seg = hay[inicio:inicio + 8]
    print(f"{Path(ruta).name}: después de == \" -> {seg!r}")
    # bytes reales: localizar por búsqueda de bytes
    bpat = b'ID_VICTIMA_CONFLICTO"] == "'
    j = b.find(bpat)
    if j >= 0:
        raw = b[j + len(bpat):j + len(bpat) + 6]
        print("   bytes crudos:", " ".join(f"{x:02X}" for x in raw))
