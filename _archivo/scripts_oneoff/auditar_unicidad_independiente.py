# -*- coding: utf-8 -*-
"""
Auditoría independiente de la regla de unicidad (F2-7).

Reimplementa la REGLA DOCUMENTADA desde cero, sin usar `validar_unicidad.py`, y
compara el resultado con el JSON publicado. Es la comprobación más exigente que se
puede hacer de la cifra «56 IDs violan la regla».

Regla documentada (informe_final.md:130):
  residuo = (edad_b − edad_a) − años_transcurridos_entre_convocatorias
  incumple si |residuo| > 4  o si el género cambia entre los dos registros.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
MEM = RAIZ / "documentacion_auditoria" / "data" / "memoria"
RESULTADOS = RAIZ / "01_datos" / "resultados_json"
FUENTE = (RAIZ / "01_datos" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
TOL = 4.0

df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=["ID_CONVOCATORIA", "ANO_CONVO", "ID_PERSONA_PR",
                          "EDAD_ANOS_PR", "NME_GENERO_PR"])
df["conv"] = df["ID_CONVOCATORIA"].astype(int)
df["fecha"] = pd.to_datetime(df["ANO_CONVO"], format="%d/%m/%Y", errors="coerce")
df["edad"] = pd.to_numeric(df["EDAD_ANOS_PR"].str.replace(",", ".", regex=False),
                           errors="coerce")
df["genero"] = df["NME_GENERO_PR"].str.strip()
print(f"registros: {len(df):,} · personas: {df['ID_PERSONA_PR'].nunique():,}".replace(",", " "))

df = df.sort_values(["ID_PERSONA_PR", "fecha"])
g = df.groupby("ID_PERSONA_PR", observed=True, sort=False)

pares = pd.DataFrame({
    "id": df["ID_PERSONA_PR"],
    "edad_a": g["edad"].shift(1),
    "edad_b": df["edad"],
    "gen_a": g["genero"].shift(1),
    "gen_b": df["genero"],
    "f_a": g["fecha"].shift(1),
    "f_b": df["fecha"],
}).dropna(subset=["edad_a", "edad_b", "f_a", "f_b"]).copy()

pares["anios"] = (pares["f_b"] - pares["f_a"]).dt.days / 365.25
pares["residuo"] = (pares["edad_b"] - pares["edad_a"]) - pares["anios"]
pares["falla_edad"] = pares["residuo"].abs() > TOL
# Solo se compara el género cuando cambia entre dos registros consecutivos.
pares["falla_genero"] = pares["gen_a"] != pares["gen_b"]

print(f"pares consecutivos: {len(pares):,}".replace(",", " "))
print(f"  pares que incumplen la edad   : {int(pares['falla_edad'].sum()):,}".replace(",", " "))
print(f"  pares que incumplen el género : {int(pares['falla_genero'].sum()):,}".replace(",", " "))

por_id = pares.groupby("id", observed=True).agg(
    fallos_edad=("falla_edad", "sum"), fallos_genero=("falla_genero", "sum"))
violan = por_id[(por_id["fallos_edad"] > 0) | (por_id["fallos_genero"] > 0)]
solo_gen = int(((por_id["fallos_edad"] == 0) & (por_id["fallos_genero"] > 0)).sum())
solo_edad = int(((por_id["fallos_edad"] > 0) & (por_id["fallos_genero"] == 0)).sum())
ambas = int(((por_id["fallos_edad"] > 0) & (por_id["fallos_genero"] > 0)).sum())

u = json.loads((RESULTADOS / "validacion_unicidad.json").read_text(encoding="utf-8"))
i = u["ids_no_unicos"]
print("\n=== comparación con lo publicado ===")
print(f"  IDs evaluados  : recalculado {int(por_id.shape[0]):,} · "
      f"publicado {i['n_ids_evaluados']:,}".replace(",", " "))
print(f"  IDs violadores : recalculado {len(violan):,} · "
      f"publicado {i['n_ids_violadores']:,}".replace(",", " "))
print(f"    solo género  : recalculado {solo_gen} · "
      f"publicado {i['por_estado']['violacion_genero']}")
print(f"    solo edad    : recalculado {solo_edad} · "
      f"publicado {i['por_estado']['violacion_edad']}")
print(f"    ambas        : recalculado {ambas} · "
      f"publicado {i['por_estado']['violacion_ambas']}")
print(f"  suma de estados publicados: "
      f"{sum(i['por_estado'].values())} (debe ser {i['n_ids_violadores']})")

print("\n=== los tres peores casos: ¿coincide el residuo? ===")
for det in i["detalle"][:3]:
    mío = violan.index.to_series().index
    fila = pares[pares["id"] == det["id"]].sort_values("residuo")
    if fila.empty:
        print(f"  {det['id']}: no aparece en el recálculo")
        continue
    peor = fila.iloc[0] if abs(fila.iloc[0]["residuo"]) >= abs(
        fila.iloc[-1]["residuo"]) else fila.iloc[-1]
    print(f"  {det['id']}: publicado residuo {det['peor_residuo']:.5f} · "
          f"recalculado {peor['residuo']:.5f} · "
          f"publicado edad_a {det['peor_edad_a']} / edad_b {det['peor_edad_b']} · "
          f"recalculado {peor['edad_a']:.2f} / {peor['edad_b']:.2f}")

print("\n=== ¿cuántas personas cambian de género en todo el padrón? ===")
cambian = pares.loc[pares["falla_genero"], "id"].nunique()
print(f"  personas con algún cambio de género: {cambian} "
      f"(el EDA reporta 42 personas que cambian de género)")
