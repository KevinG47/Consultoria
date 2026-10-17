# -*- coding: utf-8 -*-
from __future__ import annotations
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
M = Path(__file__).resolve().parents[2] / "documentacion_auditoria" / "data" / "memoria"
p = json.loads((M / "percapita_territorial.json").read_text(encoding="utf-8"))

bpa = p["bootstrap_personas"]["por_convocatoria_y_stock"]
bdi = p["bootstrap_diseno_mas_ps"]["por_convocatoria"]
print("ancho mediano (por 100 000) por convocatoria")
print("  año   personas   diseño   razón")
for a in ("2013", "2014", "2015", "2017", "2019", "2021"):
    ap, ad = bpa[a]["ancho_ic_mediano_por_100000"], bdi[a]["ancho_ic_mediano_por_100000"]
    print(f"  {a}  {ap:8.3f}  {ad:8.3f}  {ad / ap:6.2f}")
ap = bpa["stock"]["ancho_ic_mediano_por_100000"]
print(f"  stock {ap:8.3f} (personas)")
d21 = bdi["2021"]
print("\ndiseño 2021: n_poblacion", d21["n_poblacion"], "n_muestra", d21["n_muestra"],
      "fracción", round(d21["fraccion_muestreo"], 5))
print("  cero:", d21["departamentos_estimados_en_cero"])
print("  no difieren del promedio:", d21["departamentos_que_no_difieren_del_promedio"])
print("  gini mediana", d21["gini_tasas_mediana"], "IC", d21["gini_tasas_ic95"])
print("  n_h", d21["n_h"], "post_estratos", d21["post_estratos"])
print("  tasa nacional", d21["tasa_nacional_de_la_convocatoria"])
print("\npersonas 2021 gini ic", bpa["2021"]["gini_ic95"],
      "theil ic", bpa["2021"]["theil_t_ic95"])
