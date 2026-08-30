# -*- coding: utf-8 -*-
"""Parseador del log de ejecución (maneja codificación mixta UTF-8/UTF-16)."""
import re
import sys

p = sys.argv[1] if len(sys.argv) > 1 else r".\documentacion_auditoria\data\ejecucion_log.txt"
b = open(p, "rb").read()
t8 = b.decode("utf-8", errors="replace")
t16 = b.decode("utf-16-le", errors="replace")
txt = t16 if t16.count("EXIT=") > t8.count("EXIT=") else t8

pares = re.findall(
    r"=== (sprint\w+\.py) ===(.*?)EXIT=(-?\d+) TIEMPO=([\d.]+)s", txt, re.S
)
print(f"{'SCRIPT':45s} {'EXIT':>4} {'TIEMPO':>8}  ESTADO")
for nombre, body, code, t in pares:
    err = "ERROR" in body.upper() or "Traceback" in body
    estado = "ERROR" if (err or int(code) != 0) else "OK"
    print(f"{nombre:45s} {code:>4} {t:>7}s  {estado}")

if not pares:
    print("No se encontraron resultados. Primeros 300 chars del log:")
    print(txt[:300])
