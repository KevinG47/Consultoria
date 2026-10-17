# -*- coding: utf-8 -*-
"""Corre las 17 reglas y resume el estado (sin compilar LaTeX)."""
from __future__ import annotations
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "documentacion_auditoria" / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from memoria import reglas  # noqa: E402

informe = reglas.antes_de_compilar(forzar=True)
print("\n=== ESTADO DE LAS 17 REGLAS ===")
for r in informe["reglas"]:
    print(f"  {r['id']:4} {r['estado']:12} {r['descripcion'][:78]}")
print(f"\n  resumen: {informe['resumen']}")
print(f"  abortar: {informe['abortar']}")
raise SystemExit(0 if not informe["abortar"] else 1)
