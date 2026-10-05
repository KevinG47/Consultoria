# -*- coding: utf-8 -*-
"""Corrige referencias cruzadas internas del Estado del Arte tras reordenar secciones."""
import pathlib

base = pathlib.Path(r".\documentacion_auditoria\latex\estado_del_arte\secciones")
reemp = {
    "sección 12.2": "sección 13.2",
    "sección 12.1": "sección 13.1",
    "La sección 11 consolida todo en una matriz": "La sección 12 consolida todo en una matriz",
    "sección 11 consolida todo en una matriz": "sección 12 consolida todo en una matriz",
}
for p in base.glob("*.tex"):
    t = p.read_text(encoding="utf-8")
    orig = t
    for a, b in reemp.items():
        t = t.replace(a, b)
    # referencias simples en visualización
    if p.name == "12_visualizacion.tex":
        t = t.replace("el marco de indicadores de la sección 3",
                      "el marco de indicadores de la sección 2")
        t = t.replace("con el linaje de la sección 5",
                      "con el linaje de la sección 4")
    if t != orig:
        p.write_text(t, encoding="utf-8")
        print("actualizado:", p.name)
print("fin")
