# -*- coding: utf-8 -*-
"""
Diagnostica por qué `transformar()` del auditado falla con el CSV fuente.

Sospecha: `EDAD_ANOS_PR` viene con COMA decimal ('956,25'), así que pandas la
infiere como texto y `tratar_faltantes()` revienta en `.median()` con
"TypeError: Cannot perform reduction 'median' with string dtype".
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
FUENTE = (RAIZ / "01_datos" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
CONSOLIDADO = (RAIZ / "04_auditoria" / "repo_original" / "datos"
               / "tarea_join" / "investigadores_consolidado.csv")
NUMERICAS = ["NRO_ORDEN_FORM_PR", "ORDEN_CLAS_PR", "EDAD_ANOS_PR"]

for nombre, ruta in (("fuente 6 conv (CSV de Socrata)", FUENTE),
                     ("consolidado 3 conv (CSV)", CONSOLIDADO)):
    print("=" * 88)
    print(f"{nombre}\n  {ruta.name}")
    df = pd.read_csv(ruta, low_memory=False, encoding="utf-8")
    print(f"  shape: {df.shape}")
    for col in NUMERICAS:
        if col not in df.columns:
            print(f"  {col}: NO ESTÁ")
            continue
        s = df[col]
        print(f"  {col}: dtype pandas = {s.dtype}")
        # ¿cuántos valores son texto con coma?
        como_texto = s.astype(str)
        con_coma = como_texto.str.contains(",", regex=False).sum()
        como_num = pd.to_numeric(como_texto.str.replace(",", ".", regex=False),
                                 errors="coerce")
        print(f"      valores con coma decimal : {con_coma}")
        print(f"      convertibles a numérico   : {como_num.notna().sum()}"
              f" de {len(s)}")
        print(f"      ejemplos                  : "
              f"{[v for v in como_texto.unique()[:6]]}")
    print()

print("=" * 88)
print("¿Falla .median() en la columna tal como la lee pandas?")
for nombre, ruta in (("fuente 6 conv", FUENTE), ("consolidado 3 conv", CONSOLIDADO)):
    df = pd.read_csv(ruta, low_memory=False, encoding="utf-8")
    for col in NUMERICAS:
        try:
            m = df[col].median()
            print(f"  {nombre:20s} {col:20s} median() OK -> {m}")
        except Exception as e:                              # noqa: BLE001
            print(f"  {nombre:20s} {col:20s} median() FALLA -> "
                  f"{type(e).__name__}: {str(e)[:70]}")
