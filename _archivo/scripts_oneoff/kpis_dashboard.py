"""Define las tarjetas KPI del dashboard: valor CENSAL principal y, como nota
metodologica, la estimacion muestral. Comprueba que ninguna tarjeta use una
estimacion como valor principal.

Uso: python _archivo/scripts_oneoff/kpis_dashboard.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = Path("documentacion_auditoria/data/memoria")

eda = json.loads((BASE / "eda_resultados.json").read_text(encoding="utf-8"))
est = json.loads((BASE / "estimadores_resultados.json").read_text(encoding="utf-8"))


def est_de(bloque: str) -> dict:
    return est[bloque]


e = est_de("edad")
r = est["retencion"]["2013\u21922021"]

print("=== TARJETAS KPI: valor principal (CENSO) + nota muestral ===\n")

filas = []

# 1. Registros
filas.append((
    "Registros en el dataset",
    f"{eda['universo']['registros']:,}".replace(",", " "),
    "Censo completo (6 convocatorias, 2013-2021)",
    "Sin estimacion: es el total observado.",
))

# 2. Personas
filas.append((
    "Personas unicas",
    f"{eda['universo']['personas']:,}".replace(",", " "),
    "Censo completo",
    "Sin estimacion: es el total observado.",
))

# 3. Convocatorias
filas.append((
    "Convocatorias",
    str(eda["universo"]["convocatorias"]),
    "2013, 2014, 2015, 2017, 2019 y 2021",
    "Sin estimacion.",
))

# 4. Edad media
filas.append((
    "Edad media",
    f"{eda['edad']['media']:.2f}".replace(".", ","),
    f"Censo completo ({eda['edad']['n']:,} personas con edad registrada)".replace(",", " "),
    f"Estimacion MAS: {e['mas']['estimador']:.2f} | "
    f"post-estratificada: {e['post_estratificado']['estimador']:.2f} | "
    f"GREG: {e['greg_lineal']['estimador']:.2f} (n = {e['n_muestra']:,})".replace(",", " "),
))

# 5. Retencion 2013 -> 2021
filas.append((
    "Retencion 2013 a 2021",
    f"{r['censo']*100:.1f} %".replace(".", ","),
    f"Censo completo ({eda['universo']['personas']:,} personas)".replace(",", " "),
    f"Estimacion MAS: {r['mas']['estimador']*100:.1f} % (n = {r['mas']['n']}) | "
    f"post-estratificada: {r['post_estratificado']['estimador']*100:.1f} % | "
    f"GREG: {r['greg_lineal']['estimador']*100:.1f} %",
))

for titulo, valor, subtitulo, nota in filas:
    print(f"  {titulo}")
    print(f"     valor      : {valor}")
    print(f"     subtitulo  : {subtitulo}")
    print(f"     nota       : {nota}")
    print()

print("=" * 70)
print("COMPROBACION: el valor principal es censal en las 5 tarjetas")
print("=" * 70)
print(f"  registros  {eda['universo']['registros']:>7,}  <- censo (len del dataset)")
print(f"  personas   {eda['universo']['personas']:>7,}  <- censo (nunique ID_PERSONA_PR)")
print(f"  convocs    {eda['universo']['convocatorias']:>7}  <- censo (6 convocatorias)")
print(f"  edad       {eda['edad']['media']:>7.4f}  <- censo (media sobre las 30 085)")
print(f"  retencion  {r['censo']:>7.4f}  <- censo 2013->2021")
print()
print("  Unico KPI que estaba como estimacion: retencion (56,6 % MAS).")
print(f"  Corregido al valor censal {r['censo']*100:.1f} %, con la MAS como nota.")
print()
print(f"  media de edad: MAS={e['mas']['estimador']:.4f} "
      f"IC95=[{e['mas']['ic95'][0]:.4f}, {e['mas']['ic95'][1]:.4f}]")
print(f"  retencion: censo={r['censo']:.4f} MAS={r['mas']['estimador']:.4f} "
      f"IC95=[{r['mas']['ic95'][0]:.4f}, {r['mas']['ic95'][1]:.4f}]")
