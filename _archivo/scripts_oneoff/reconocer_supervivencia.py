# -*- coding: utf-8 -*-
"""
Reconocimiento para F2-10: dependencias disponibles y estructura de la
supervivencia (entradas, salidas, censura y tamaños de grupo).
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]

print("=== dependencias ===")
for mod in ("lifelines", "statsmodels", "scipy", "numpy", "sklearn"):
    try:
        m = __import__(mod)
        print(f"  {mod:14s} OK  {getattr(m, '__version__', '?')}")
    except Exception as e:                                  # noqa: BLE001
        print(f"  {mod:14s} FALTA ({type(e).__name__})")

FUENTE = (RAIZ / "datos_originales" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR", "ANO_CONVO",
                          "NME_CLASIFICACION_PR", "NME_GENERO_PR",
                          "NME_GRAN_AREA_PR", "NME_DEPARTAMENTO_RES_PR"])
df["conv"] = df["ID_CONVOCATORIA"].astype(int)
df["fecha"] = pd.to_datetime(df["ANO_CONVO"], format="%d/%m/%Y")
print(f"\nregistros: {len(df):,} · personas: {df['ID_PERSONA_PR'].nunique():,}"
      .replace(",", " "))

fechas = df.groupby("conv")["fecha"].first().sort_index()
t0, t1 = fechas.iloc[0], fechas.iloc[-1]
print(f"ventana de observación: {t0.date()} → {t1.date()} "
      f"({(t1 - t0).days / 365.25:.3f} años)")

# --- entrada y última observación de cada persona ---
g = df.sort_values("conv").groupby("ID_PERSONA_PR")
primera = g["conv"].min()
ultima = g["conv"].max()
entrada = df.drop_duplicates("ID_PERSONA_PR").set_index("ID_PERSONA_PR")["fecha"]
entrada = df.sort_values("conv").drop_duplicates("ID_PERSONA_PR", keep="first") \
    .set_index("ID_PERSONA_PR")["fecha"]
salida_fecha = df.sort_values("conv").drop_duplicates("ID_PERSONA_PR", keep="last") \
    .set_index("ID_PERSONA_PR")["fecha"]

print("\n=== convocatoria de entrada ===")
print(primera.value_counts().sort_index().to_string())
print("\n=== convocatoria de última observación ===")
print(ultima.value_counts().sort_index().to_string())

# Censura: la última convocatoria observada es la última del estudio
en_el_final = int((ultima == fechas.index[-1]).sum())
print(f"\npersonas cuya última observación es 2021 (CENSURADAS): "
      f"{en_el_final:,} de {len(ultima):,} ({100*en_el_final/len(ultima):.1f} %)"
      .replace(",", " "))

print("\n=== cohorte de 2013 (diseño sin truncamiento) ===")
c2013 = set(df.loc[df["conv"] == 16, "ID_PERSONA_PR"])
sigue = c2013 & set(df.loc[df["conv"] == 21, "ID_PERSONA_PR"])
print(f"  presentes en 2013: {len(c2013):,} · siguen en 2021: {len(sigue):,} "
      f"({100*len(sigue)/len(c2013):.2f} %)".replace(",", " "))
print(f"  -> la mediana de supervivencia {'SÍ' if len(sigue)/len(c2013) < 0.5 else 'NO'} "
      f"se alcanza dentro de la ventana")

print("\n=== tamaños de grupo (personas distintas) ===")
ult = df.sort_values("conv").drop_duplicates("ID_PERSONA_PR", keep="last")
for col, etq in (("NME_CLASIFICACION_PR", "categoría"),
                 ("NME_GENERO_PR", "género"),
                 ("NME_GRAN_AREA_PR", "gran área")):
    print(f"\n  {etq}:")
    for k, v in ult[col].value_counts().items():
        print(f"    {k[:40]:42s} {v:6,d} {100*v/len(ult):5.2f}%".replace(",", " "))

print("\n  departamento (top 8) — personas en su última observación:")
for k, v in ult["NME_DEPARTAMENTO_RES_PR"].value_counts().head(8).items():
    print(f"    {k[:40]:42s} {v:6,d} {100*v/len(ult):5.2f}%".replace(",", " "))

# --- Emérito: ¿cuántos y en qué convocatorias? ---
eme = df[df["NME_CLASIFICACION_PR"] == "Investigador Emérito"]
print(f"\n=== Emérito ===")
print(f"  registros: {len(eme)} · personas: {eme['ID_PERSONA_PR'].nunique()}")
print(f"  convocatorias en que aparece: "
      f"{sorted(eme['conv'].unique().tolist())}")
print(f"  personas Emérito presentes en 2021: "
      f"{eme[eme['conv'] == 21]['ID_PERSONA_PR'].nunique()}")
