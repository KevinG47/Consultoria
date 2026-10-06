"""Verificacion INDEPENDIENTE del analisis longitudinal.

Recalcula todo desde muestra_registros.csv / el CSV original con pd.crosstab y
operaciones de conjuntos, sin reutilizar las funciones de analisis_longitudinal.py,
y compara contra longitudinal_resultados.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

for _f in (sys.stdout, sys.stderr):
    if hasattr(_f, "reconfigure"):
        _f.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DIR = RAIZ / "documentacion_auditoria" / "data" / "memoria"
CSV = RAIZ / "Datos" / "Investigadores_Reconocidos_por_convocatoria_20261006.csv"

CONV_ORDEN = [16, 17, 18, 19, 20, 21]
ANIOS = {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021}
CATS = ["Investigador Junior", "Investigador Asociado",
        "Investigador Sénior", "Investigador Emérito"]

J = json.loads((DIR / "longitudinal_resultados.json").read_text(encoding="utf-8"))

# --- reconstruye el panel muestral desde el archivo guardado ---
mue = pd.read_csv(DIR / "muestra_registros.csv", dtype=str, keep_default_na=False)
mue["_c"] = mue["ID_CONVOCATORIA"].astype(int)
ids_muestra = set(pd.read_csv(DIR / "muestra_ids.csv", dtype=str,
                              keep_default_na=False)["ID_PERSONA_PR"])
print(f"muestra_ids.csv: {len(ids_muestra)} ids")
print(f"muestra_registros.csv: {len(mue)} registros, "
      f"{mue['ID_PERSONA_PR'].nunique()} personas")
assert ids_muestra == set(mue["ID_PERSONA_PR"]), "los IDs no coinciden"

# --- T4: retencion recalculada con conjuntos ---
print("\n=== VERIFICACION T4 (retencion/entradas/salidas) ===")
pres = {c: set(mue.loc[mue['_c'] == c, "ID_PERSONA_PR"]) for c in CONV_ORDEN}
ok = True
for i, (a, b) in enumerate(zip(CONV_ORDEN[:-1], CONV_ORDEN[1:])):
    A, B = pres[a], pres[b]
    ref = J["pares_muestra"][i]
    fila = (len(A), len(B), len(A & B), len(A - B), len(B - A), len(B - A) - len(A - B))
    mia = (ref["n_a"], ref["n_b"], ref["retenidos"], ref["salidas"],
           ref["entradas"], ref["crecimiento_neto"])
    coincide = fila == mia
    ok &= coincide
    print(f"  {ANIOS[a]}->{ANIOS[b]}  recalculado={fila}  json={mia}  "
          f"{'OK' if coincide else 'DIFERENCIA'}")
    assert len(A & B) + len(B - A) == len(B), "identidad de cierre violada"

# --- T5: matrices recalculadas con crosstab (orientacion correcta) ---
print("\n=== VERIFICACION T5 (matrices de transicion) ===")
cat = {c: mue.loc[mue['_c'] == c].set_index("ID_PERSONA_PR")["NME_CLASIFICACION_PR"]
       for c in CONV_ORDEN}
filas_md = []
for i, (a, b) in enumerate(zip(CONV_ORDEN[:-1], CONV_ORDEN[1:])):
    comunes = sorted(set(cat[a].index) & set(cat[b].index))
    df = pd.DataFrame({"origen": cat[a].loc[comunes].values,
                       "destino": cat[b].loc[comunes].values})
    # crosstab: filas = origen, columnas = destino (orden jerarquico)
    ct = pd.crosstab(df["origen"], df["destino"]).reindex(index=CATS, columns=CATS,
                                                          fill_value=0)
    ref = J["transiciones_muestra"][f"{ANIOS[a]}→{ANIOS[b]}"]
    # el json guarda to_dict() orientado por columna: {destino: {origen: n}}
    deljson = pd.DataFrame(ref["conteos"]).reindex(index=CATS, columns=CATS, fill_value=0)
    coincide = ct.equals(deljson.astype(int))
    ok &= coincide
    diag = int(np.trace(ct.values))
    up = int(sum(ct.values[x, y] for x in range(4) for y in range(x + 1, 4)))
    dn = int(sum(ct.values[x, y] for x in range(4) for y in range(x)))
    print(f"\n  {ANIOS[a]}->{ANIOS[b]}  n={int(ct.values.sum())}  "
          f"matriz_igual_al_json={coincide}")
    print(f"    permanecen={diag} (json {ref['misma_categoria']})  "
          f"suben={up} (json {ref['ascienden']})  bajan={dn} (json {ref['descienden']})")
    assert (diag, up, dn) == (ref["misma_categoria"], ref["ascienden"], ref["descienden"])
    print("    filas=origen, columnas=destino:")
    print("      " + " " * 9 + "".join(f"{c[13:][:9]:>12s}" for c in CATS))
    for o in CATS:
        tot = int(ct.loc[o].sum())
        celdas = "".join(
            f"{int(ct.loc[o, d]):5d}({100*ct.loc[o, d]/tot:4.1f}%)" if tot else
            f"{0:5d}(  --  )" for d in CATS)
        print(f"      {o[13:][:9]:>9s}{celdas}   n={tot}")
    filas_md.append((f"{ANIOS[a]}→{ANIOS[b]}", ct))

# --- distribucion de categoria por convocatoria (universo) ---
print("\n=== Categoria por convocatoria (UNIVERSO) ===")
partes = []
for t in pd.read_csv(CSV, dtype=str, keep_default_na=False, chunksize=50_000,
                     usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR", "NME_CLASIFICACION_PR"]):
    partes.append(t)
todo = pd.concat(partes, ignore_index=True)
todo["_c"] = todo["ID_CONVOCATORIA"].astype(int)
tab = pd.crosstab(todo["_c"], todo["NME_CLASIFICACION_PR"]).reindex(
    index=CONV_ORDEN, columns=CATS, fill_value=0)
tab.index = [ANIOS[c] for c in CONV_ORDEN]
print(tab.to_string())
print("\n  % por fila:")
print((100 * tab.div(tab.sum(axis=1), axis=0)).round(2).to_string())

print("\n=== VERIFICACION T3 (muestra) ===")
print(f"  personas en la muestra: {mue['ID_PERSONA_PR'].nunique()} "
      f"(json {J['muestra']['personas']})")
print(f"  registros en la muestra: {len(mue)} (json {J['muestra']['registros']})")
assert mue["ID_PERSONA_PR"].nunique() == J["muestra"]["personas"]
assert len(mue) == J["muestra"]["registros"]

print("\n=== VERIFICACION global 2013->2021 ===")
A, B = pres[16], pres[21]
print(f"  recalculado: {len(A & B)}/{len(A)} = {100*len(A & B)/len(A):.2f}%  "
      f"(json {100*J['retencion_global_2013_2021']['muestra']['p']:.2f}%)")
assert abs(len(A & B) / len(A) - J["retencion_global_2013_2021"]["muestra"]["p"]) < 1e-12

print("\n" + ("TODO COINCIDE" if ok else "HAY DIFERENCIAS"))

# --- tablas markdown de transiciones para el documento ---
print("\n=== MARKDOWN: matrices de transicion (muestra) ===")
for nombre, ct in filas_md:
    print(f"\n**{nombre}**")
    enc = "| Categoría en t₁ \\ t₂ | " + " | ".join(c[13:] for c in CATS) + " | Total |"
    print(enc)
    print("|" + "---|" * 6)
    for o in CATS:
        tot = int(ct.loc[o].sum())
        celdas = []
        for d in CATS:
            if tot == 0:
                celdas.append("0")
            else:
                celdas.append(f"{int(ct.loc[o, d])} ({100*ct.loc[o, d]/tot:.1f}%)")
        print(f"| {o[13:]} | " + " | ".join(celdas) + f" | {tot} |")
    tot_c = [int(ct[c].sum()) for c in CATS]
    print("| **Total** | " + " | ".join(str(t) for t in tot_c)
          + f" | {int(ct.values.sum())} |")
