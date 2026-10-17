# -*- coding: utf-8 -*-
"""Resume modelo_estrella.json para redactar el informe de F2-3."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
J = json.loads((RAIZ / "documentacion_auditoria" / "data" / "memoria"
                / "modelo_estrella.json").read_text(encoding="utf-8"))


def n(x):
    return f"{x:,}".replace(",", " ")


print("=== composición del modelo ===")
c = J["composicion_del_modelo"]
print(f"  {c['n_dimensiones']} dimensiones + 1 hechos + 1 puente = "
      f"{c['tablas_totales']} tablas")
print(f"  dimensiones: {c['dimensiones']}")

print("\n=== filas por tabla: 3 conv (lo que corre hoy) vs 6 conv ===")
t3 = J["modelo_3_convocatorias"]["tablas"]
t6 = J["modelo_6_convocatorias"]["tablas"]
for k in sorted(t6):
    d = t6[k] - t3.get(k, 0)
    print(f"  {k:28s} {n(t3.get(k,0)):>10s} -> {n(t6[k]):>10s}  (Δ {d:+,})")

print("\n=== por convocatoria (6 conv) ===")
pc6 = J["modelo_6_convocatorias"]["por_convocatoria"]
ev = J["evidencia_versionada"]
for a in sorted(pc6, key=int):
    d = pc6[a]
    print(f"  {a}: registros={n(d['registros']):>7s} "
          f"investigadores={n(d['investigadores']):>7s} "
          f"(evidencia={n(ev['esperado_por_convocatoria'][a])})")
print(f"  TOTAL: {n(ev['observado_total'])} · evidencia {n(ev['total_esperado'])}")

print("\n=== integridad referencial ===")
for k, v in J["integridad_referencial"]["claves_foraneas"].items():
    print(f"  {k:28s} {v}")
print(f"  puente: {J['integridad_referencial']['puente']}")
print("  claves primarias:")
for k, v in J["integridad_referencial"]["claves_primarias"].items():
    print(f"    {k:28s} {v}")

print("\n=== insumo ===")
ins = J["insumo"]
print(f"  usado por el auditado : {ins['usado_por_el_auditado']}")
print(f"  usado aquí            : {ins['usado_aqui']}")
print(f"  registros fuente      : {n(ins['registros_fuente'])}")
print(f"  columnas              : {ins['columnas']}")
for k, v in ins["adaptacion_necesaria"]["columnas_convertidas"].items():
    print(f"  adaptada {k}: {v}")

print("\n=== imputación de edad ===")
print(f"  {J['transformacion_del_auditado']['imputacion_de_edad']}")

print("\n=== validaciones ===")
for k, v in J["validaciones"].items():
    print(f"  [{'OK ' if v else 'NO '}] {k}")

print(f"\nfiguras: {J['figuras']}")
print(f"fecha: {J['fecha']}")
