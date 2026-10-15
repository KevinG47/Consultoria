"""Comprueba los KPI del dashboard contra los JSON de entrada."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = Path("documentacion_auditoria/data/memoria")

eda = json.loads((BASE / "eda_resultados.json").read_text(encoding="utf-8"))
est = json.loads((BASE / "estimadores_resultados.json").read_text(encoding="utf-8"))
dg = json.loads((BASE / "diagnosticos_greg.json").read_text(encoding="utf-8"))

print("=== KPI solicitados ===")
u = eda["universo"]
print(f"  total registros      : {u['registros']:,}   (pedido 77 237)")
print(f"  personas unicas      : {u['personas']:,}   (pedido 30 086)")
print(f"  convocatorias        : {u['convocatorias']}   (pedido 6)")
print(f"  edad media (censo)   : {eda['edad']['media']:.4f}   (pedido 45,52)")

r = est["retencion"]["2013\u21922021"]
print(f"  retencion 2013->2021 : censo={r['censo']:.4f} ({r['censo']*100:.1f} %)   (pedido 56,6 %)")
print(f"      mas={r['mas']['estimador']:.4f}  ps={r['post_estratificado']['estimador']:.4f} "
      f"greg={r['greg_lineal']['estimador']:.4f}")

print("\n=== Varianza entre grupos (pestaña 3) ===")
pares = {"NME_CLASIFICACION_PR": "categoria", "NME_GRAN_AREA_PR": "area",
         "NME_DEPARTAMENTO_RES_PR": "departamento", "NME_NIV_FORM_PR": "nivel",
         "NME_GENERO_COL": "genero"}
pedido = {"categoria": 7.08, "area": 1.38, "departamento": 0.99,
          "nivel": 0.30, "genero": 0.11}
for clave, etiqueta in pares.items():
    v = eda["estratos_candidatos"][clave]["pct_varianza_explicada"]
    print(f"  {etiqueta:14} {v:6.2f} %   (pedido {pedido[etiqueta]:.2f} %)  "
          f"{'OK' if abs(v - pedido[etiqueta]) < 0.005 else 'DIFIERE'}")

print("\n=== Edad: que hay y que falta ===")
print(f"  claves de eda['edad']: {list(eda['edad'])}")
print("  -> solo estadisticos resumidos; NO hay vector de edades (hace falta")
print("     para el histograma, el boxplot y el Q-Q)")

print("\n=== Modelo de edad: arrays disponibles ===")
inf = dg["modelo_edad"]["influencia"]
for k, v in inf.items():
    print(f"  {k:24} {'list(%d)' % len(v) if isinstance(v, list) else v}")
print("  -> falta el vector de AJUSTADOS (Xs @ beta) para 'residuos vs ajustados'")
print(f"  g_weights: {list(dg['modelo_edad']['g_weights'])}")
print("  -> solo resumen + cuantiles; NO hay vector de g-weights (hace falta")
print("     para la distribucion)")
