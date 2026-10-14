# -*- coding: utf-8 -*-
"""
verificar_comparar_dane.py
==========================

Ejecuta las funciones REALES del repositorio auditado
(`src/Transformacion.py` + `src/analisis/diversidad.py`) sobre los datos reales
para determinar si el denominador de `comparar_dane()` es correcto o no.

La contradiccion a resolver:
    # Etnia: excluir "NINGUN GRUPO ETNICO" del denominador para ver minorias
    etnia = df_2021[df_2021["TXT_GRUPO_ETNICO"] != "NO DISPONIBLE"]

Ademas se contrasta el resultado contra la evidencia versionada del propio
repositorio (`evidencias/diversidad_comparacion_dane.csv`), que es la que
respaldan las cifras publicadas en el anteproyecto.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
REPO = RAIZ / "datos_originales" / "repo_auditado"
sys.path.insert(0, str(REPO / "src"))

from analisis.diversidad import DANE_REFERENCIA, comparar_dane  # noqa: E402
from Transformacion import (COLS_NUMERICAS, limpiar_texto,       # noqa: E402
                            tratar_faltantes)

CSV = RAIZ / "datos_originales" / "datos_fuente" / \
    "Investigadores_Reconocidos_por_convocatoria_20261006.csv"

# Nuestro CSV fuente se lee como texto (dtype=str) para no perder IDs con ceros
# a la izquierda; el pipeline real recibe del Excel las numericas ya tipadas.
# Se replican esos tipos antes de llamar a tratar_faltantes, que calcula medianas.
df = pd.read_csv(CSV, dtype=str, keep_default_na=False, encoding="utf-8")
for col in COLS_NUMERICAS:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col].str.replace(",", ".", regex=False),
                                errors="coerce")
d21 = df[df["ID_CONVOCATORIA"] == "21"].copy()

# Se aplican las DOS funciones reales del pipeline que afectan a estas columnas
d21 = tratar_faltantes(limpiar_texto(d21))
d21["ANO_CONVO_INT"] = 2021

print("=== valores de TXT_GRUPO_ETNICO TRAS EL PIPELINE REAL ===")
for k, v in d21["TXT_GRUPO_ETNICO"].value_counts().items():
    print(f"  {k!r:60s} {v:7,d}".replace(",", " "))

print("\n=== salida de comparar_dane() (codigo sin tocar) ===")
res = comparar_dane(d21)
print(res.to_string(index=False))

print("\n=== denominador efectivo que usa el codigo ===")
conocido = d21[d21["TXT_GRUPO_ETNICO"] != "NO DISPONIBLE"]
print(f"  registros 2021                 : {len(d21):,}".replace(",", " "))
print(f"  excluidos por 'NO DISPONIBLE'  : "
      f"{(d21['TXT_GRUPO_ETNICO'] == 'NO DISPONIBLE').sum():,}".replace(",", " "))
print(f"  denominador efectivo           : {len(conocido):,}".replace(",", " "))
print(f"  desglose del denominador: "
      f"{conocido['TXT_GRUPO_ETNICO'].value_counts().to_dict()}")

print("\n=== evidencia VERSIONADA del propio repositorio auditado ===")
ev = REPO / "evidencias" / "diversidad_comparacion_dane.csv"
if ev.exists():
    print(pd.read_csv(ev).to_string(index=False))
    print("\n  -> si coincide con la salida de arriba, el codigo es el que genero")
    print("     la evidencia que respalda las cifras publicadas.")

print("\n=== que pasaria si se aplicara el COMENTARIO ===")
sin_mayoria = conocido[~conocido["TXT_GRUPO_ETNICO"].isin(
    ["NINGÚN GRUPO ÉTNICO", "NINGUN GRUPO ETNICO", "BLANCO O MESTIZO"])]
print(f"  denominador si se excluye la mayoria: {len(sin_mayoria):,}".replace(",", " "))
for grupo, patron, dane in [("NEGRO/AFROCOLOMBIANO", "AFRO|NEGRA", 6.7),
                            ("INDIGENA", "INDIGENA|IND.GENA", 4.4)]:
    n = sin_mayoria["TXT_GRUPO_ETNICO"].str.contains(patron, case=False, na=False).sum()
    pct = n / len(sin_mayoria) * 100
    print(f"  {grupo:22s} pct={pct:6.2f} %  razon={dane / pct:5.1f}x  "
          f"(vs {dane / (n / len(conocido) * 100):4.1f}x con el codigo actual)")
print("\n  La razon BAJA al excluir la mayoria: la referencia DANE es un % de la")
print("  poblacion TOTAL, asi que la base comparable es el total de respuestas")
print("  conocidas. Excluirla mezcla bases y SUBESTIMA la subrepresentacion.")
