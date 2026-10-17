# -*- coding: utf-8 -*-
"""Detalle de la comparación con los juicios anotados en el script R del auditado."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
J = json.loads((RAIZ / "documentacion_auditoria" / "data" / "memoria"
                / "validacion_unicidad.json").read_text(encoding="utf-8"))
v = J["validacion_con_los_juicios_del_analista"]
print(f"ids revisados por el analista: {v['ids_revisados_por_el_analista']}")
print(f"diferencias que coinciden    : {v['la_diferencia_de_edad_coincide']}")
print()
print(f"{'id':12s} {'anotado':>8s} {'calculado':>10s} {'coincide':>9s} "
      f"{'veredicto':>12s} {'encontrado':>11s}")
for d in v["detalle"]:
    print(f"{d.get('id', '?'):12s} {d['anotado_en_r']:8.2f} "
          f"{d.get('dif_edad_calculada', float('nan')):10.2f} "
          f"{str(d.get('coincide_la_diferencia')):>9s} "
          f"{str(d.get('veredicto_de_la_regla')):>12s} "
          f"{str(d.get('encontrado', True)):>11s}")
