# -*- coding: utf-8 -*-
"""Extrae mensajes de error de los scripts fallidos del log de ejecución."""
import re
import sys

p = sys.argv[1] if len(sys.argv) > 1 else r".\documentacion_auditoria\data\ejecucion_log.txt"
salida = sys.argv[2] if len(sys.argv) > 2 else r".\documentacion_auditoria\data\errores_ejecucion.txt"

b = open(p, "rb").read()
t8 = b.decode("utf-8", errors="replace")
t16 = b.decode("utf-16-le", errors="replace")
txt = t16 if t16.count("EXIT=") > t8.count("EXIT=") else t8

fallidos = [
    "sprint6_ocde_composicion.py",
    "sprint6_sankey_categoria.py",
    "sprint6_geografia_institucional.py",
    "sprint6_sankey_territorial.py",
    "sprint5_produccion.py",
    "sprint5_duckdb.py",
]

out = []
for s in fallidos:
    m = re.search(r"=== " + re.escape(s) + r" ===(.*?)EXIT=-?\d+", txt, re.S)
    if not m:
        out.append(f"### {s}: no encontrado en log")
        continue
    body = m.group(1)
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    out.append(f"### {s}")
    # últimas líneas del cuerpo (suelen contener el traceback)
    for l in lines[-6:]:
        out.append("   " + l[:200])
    out.append("")

open(salida, "w", encoding="utf-8").write("\n".join(out))
print(f"escrito: {salida}")
