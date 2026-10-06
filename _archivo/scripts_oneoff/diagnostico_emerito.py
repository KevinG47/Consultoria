"""Por que no aparece 'Investigador Emerito' como categoria de origen en la muestra?"""
import sys
from pathlib import Path
import pandas as pd

for _f in (sys.stdout, sys.stderr):
    if hasattr(_f, "reconfigure"):
        _f.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DIR = RAIZ / "documentacion_auditoria" / "data" / "memoria"
CSV = RAIZ / "Datos" / "Investigadores_Reconocidos_por_convocatoria_20261006.csv"
ANIOS = {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021}

cols = ["ID_CONVOCATORIA", "ID_PERSONA_PR", "NME_CLASIFICACION_PR", "ID_CLAS_PR", "ORDEN_CLAS_PR"]
partes = [t for t in pd.read_csv(CSV, dtype=str, keep_default_na=False,
                                 chunksize=50_000, usecols=cols)]
todo = pd.concat(partes, ignore_index=True)
todo["_c"] = todo["ID_CONVOCATORIA"].astype(int)

ids = set(pd.read_csv(DIR / "muestra_ids.csv", dtype=str,
                      keep_default_na=False)["ID_PERSONA_PR"])
mue = todo[todo["ID_PERSONA_PR"].isin(ids)]

print("=== registros con categoria Emerito, por convocatoria ===")
for nombre, d in (("UNIVERSO", todo), ("MUESTRA", mue)):
    e = d[d["NME_CLASIFICACION_PR"] == "Investigador Emérito"]
    print(f"\n{nombre}: {len(e)} registros Emerito, {e['ID_PERSONA_PR'].nunique()} personas")
    print(e.groupby("_c").size().rename(index=ANIOS).to_string())

print("\n=== valores de ID_CLAS_PR / ORDEN_CLAS_PR para Emerito ===")
e = todo[todo["NME_CLASIFICACION_PR"] == "Investigador Emérito"]
print(e.groupby(["ID_CLAS_PR", "ORDEN_CLAS_PR"]).size().to_string())

print("\n=== orden jerarquico declarado (ORDEN_CLAS_PR por categoria) ===")
print(todo.groupby(["NME_CLASIFICACION_PR", "ID_CLAS_PR", "ORDEN_CLAS_PR"],
                   observed=True).size().to_string())

print("\n=== MUESTRA: personas Emerito y en que convocatorias aparecen ===")
ids_e = set(mue.loc[mue["NME_CLASIFICACION_PR"] == "Investigador Emérito", "ID_PERSONA_PR"])
print(f"personas de la muestra con Emerito en alguna convocatoria: {len(ids_e)}")
sub = mue[mue["ID_PERSONA_PR"].isin(ids_e)][
    ["ID_PERSONA_PR", "_c", "NME_CLASIFICACION_PR"]].copy()
sub["_c"] = sub["_c"].map(ANIOS)
piv = sub.pivot_table(index="ID_PERSONA_PR", columns="_c",
                      values="NME_CLASIFICACION_PR", aggfunc="first")
pd.set_option("display.width", 200)
print(piv.to_string())

print("\n=== Contraste: personas Emerito del universo en 2019, cuantas siguen en 2021 ===")
for c in (18, 19, 20):
    e_c = set(todo.loc[(todo["_c"] == c) & (todo["NME_CLASIFICACION_PR"]
                == "Investigador Emérito"), "ID_PERSONA_PR"])
    for c2 in (19, 20, 21):
        if c2 <= c:
            continue
        siguen = set(todo.loc[todo["_c"] == c2, "ID_PERSONA_PR"])
        print(f"  Emerito en {ANIOS[c]} (n={len(e_c)}): presentes en {ANIOS[c2]}: "
              f"{len(e_c & siguen)} ({100*len(e_c & siguen)/len(e_c):.1f}%)")
