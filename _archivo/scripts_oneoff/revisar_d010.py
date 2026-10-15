"""Comprueba que decisiones.yaml sigue siendo valido tras corregir D010.

Uso: python _archivo/scripts_oneoff/revisar_d010.py
"""

from __future__ import annotations

from pathlib import Path

import yaml

RUTA = Path("documentacion_auditoria/data/memoria/decisiones.yaml")

datos = yaml.safe_load(RUTA.read_text(encoding="utf-8"))
decisiones = datos["decisiones"]

print(f"YAML valido. decisiones: {len(decisiones)}")
print(f"ids: {[d['id'] for d in decisiones]}")

d10 = next(d for d in decisiones if d["id"] == "D010")
print()
print("Campos que valida R16:")
for campo in ("id", "fecha", "decision", "justificacion", "estado"):
    valor = str(d10.get(campo, "")).strip()
    marca = "PRESENTE" if valor else "*** VACIO ***"
    print(f"  {campo:14} {marca}  ({len(valor)} caracteres)")

permitidos = {"vigente", "superada", "propuesta", "pendiente_implementacion"}
print(f"  estado permitido: {d10.get('estado') in permitidos}")
print(f"  tema: {d10.get('tema')}")
print(f"  marcador_codigo: {d10['implementacion'].get('marcador_codigo')}")
print(f"  archivos: {d10['implementacion'].get('archivos')}")

ids = [d["id"] for d in decisiones]
print(f"  ids unicos: {len(ids) == len(set(ids))}")

print()
print("--- evidencia de D010 (texto interpretado por YAML) ---")
print(d10["evidencia"].strip())
