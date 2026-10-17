# -*- coding: utf-8 -*-
"""
Reconocimiento para F2-7: cuántos IDs se repiten, cómo se comporta la diferencia de
edad frente al lapso real entre convocatorias, y cuántas violaciones hay bajo la
regla DOCUMENTADA frente a la IMPLEMENTADA en R.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
FUENTE = (RAIZ / "datos_originales" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")

df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR", "NME_GENERO_PR",
                          "EDAD_ANOS_PR", "ANO_CONVO"])
df["conv"] = df["ID_CONVOCATORIA"].astype(int)
df["edad"] = pd.to_numeric(df["EDAD_ANOS_PR"].str.replace(",", ".", regex=False),
                           errors="coerce")
df["fecha"] = pd.to_datetime(df["ANO_CONVO"], format="%d/%m/%Y")
print(f"registros: {len(df):,} · personas: {df['ID_PERSONA_PR'].nunique():,}"
      .replace(",", " "))

print("\n=== fechas de convocatoria (de ANO_CONVO) ===")
fechas = df.groupby("conv")["fecha"].first().sort_index()
for c, f in fechas.items():
    print(f"  {c}: {f.date()}")
anios = (fechas - fechas.min()).dt.days.to_numpy() / 365.25
print(f"\n  lapso desde la primera (años): "
      f"{dict(zip(fechas.index, anios.round(3)))}")

print("\n=== IDs repetidos ===")
cuenta = df.groupby("ID_PERSONA_PR").size()
print(f"  IDs con más de un registro: {int((cuenta > 1).sum()):,}".replace(",", " "))
print(f"  distribución del nº de registros por ID: "
      f"{cuenta.value_counts().sort_index().to_dict()}")

# --- pares CONSECUTIVOS del mismo ID ---
orden = df.sort_values(["ID_PERSONA_PR", "conv"])
g = orden.groupby("ID_PERSONA_PR")
pares = orden.assign(
    edad_prev=g["edad"].shift(1), conv_prev=g["conv"].shift(1),
    genero_prev=g["NME_GENERO_PR"].shift(1),
).dropna(subset=["edad_prev"])
pares = pares[pares["conv"] != pares["conv"].shift(1).where(
    pares["ID_PERSONA_PR"] == pares["ID_PERSONA_PR"].shift(1))]
pares["lapso"] = pares.apply(
    lambda r: (fechas[r["conv"]] - fechas[int(r["conv_prev"])]).days / 365.25, axis=1)
pares["dif_edad"] = pares["edad"] - pares["edad_prev"]
pares["residuo"] = pares["dif_edad"] - pares["lapso"]
pares["genero_igual"] = pares["NME_GENERO_PR"] == pares["genero_prev"]

print(f"\n=== pares consecutivos del mismo ID: {len(pares):,} ===".replace(",", " "))
print(f"  residuo (Δedad − lapso): media={pares['residuo'].mean():.4f} "
      f"sd={pares['residuo'].std():.4f} "
      f"min={pares['residuo'].min():.2f} max={pares['residuo'].max():.2f}")
print(f"  |residuo| > 4 (regla DOCUMENTADA, simétrica): "
      f"{int((pares['residuo'].abs() > 4).sum())}")
print(f"  dif_edad > 4.1 (regla IMPLEMENTADA en R, una cola): "
      f"{int((pares['dif_edad'] > 4.1).sum())}")
print(f"  género distinto entre los dos registros: "
      f"{int((~pares['genero_igual']).sum())}")
print(f"  simultáneamente |residuo|>4 y género distinto: "
      f"{int(((pares['residuo'].abs() > 4) & (~pares['genero_igual'])).sum())}")

print("\n=== los 10 residuos más extremos ===")
top = pares.reindex(pares["residuo"].abs().sort_values(ascending=False).index)
for _, r in top.head(10).iterrows():
    print(f"  ID {r['ID_PERSONA_PR']} {int(r['conv_prev'])}→{int(r['conv'])}: "
          f"edad {r['edad_prev']:.2f}→{r['edad']:.2f} (Δ {r['dif_edad']:+.2f}) "
          f"lapso {r['lapso']:.2f} residuo {r['residuo']:+.2f} "
          f"género {'=' if r['genero_igual'] else '≠'}")

print("\n=== ¿la regla implementada ve los descensos? ===")
bajadas = pares[pares["dif_edad"] < -4]
print(f"  pares con dif_edad < -4 (la edad DECRECE más de 4 años): {len(bajadas)}")
for _, r in bajadas.head(6).iterrows():
    print(f"    ID {r['ID_PERSONA_PR']} {int(r['conv_prev'])}→{int(r['conv'])}: "
          f"{r['edad_prev']:.2f}→{r['edad']:.2f} "
          f"(el filtro dif_edad>4.1 NO lo detecta)")
