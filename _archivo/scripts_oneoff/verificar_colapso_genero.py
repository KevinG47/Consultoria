# -*- coding: utf-8 -*-
"""
Verificacion del colapso de genero: que cambia y que NO cambia.

Comprueba, con las funciones reales del pipeline:
  1. frecuencias censo/muestra antes y despues;
  2. calibrabilidad de los g-weights: columnas no calibrables y cond(M);
  3. si el estimador GREG de la edad cambia (no deberia, ni en el ultimo decimal);
  4. el chi-cuadrado de representatividad del genero (gl y p);
  5. si las tablas de retencion/transicion por genero contienen las categorias raras.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
sys.path.insert(0, str(DOC / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from analisis_longitudinal import comparar_poblacion            # noqa: E402
from diagnosticos_greg import g_weights                        # noqa: E402
from estimadores_longitudinal import (AUX_EDAD, AUX_RET, IDS,  # noqa: E402
                                      cargar, greg_lineal, matriz_aux)
from genero_comun import (CATEGORIAS_RARAS, COL_GENERO, COL_GENERO_COL,  # noqa: E402
                          ETIQUETA_OTRO, agregar_genero_colapsado, resumen_colapso)

AUX_EDAD_CRUDA = list(AUX_EDAD)

print("=" * 78)
print("1. FRECUENCIAS")
print("=" * 78)
ids = set(pd.read_csv(IDS, dtype=str, keep_default_na=False)["ID_PERSONA_PR"])
df = agregar_genero_colapsado(cargar())
R = resumen_colapso(df, ids_muestra=ids)
print(f"categorias originales: {R['categorias_originales']}")
print(f"-> colapsada          : {R['distribucion_censo_colapsada']}")
for c, d in R["categorias_colapsadas"].items():
    print(f"   {c:16s} censo={d['personas_censo']}  muestra={d['personas_muestra']}"
          f"  registros={d['registros_censo']}"
          f"  etiqueta_en={d['convocatorias_con_la_etiqueta']}"
          f"  personas_en={d['convocatorias_de_esas_personas']}")
print(f"personas colapsadas: {R['personas_colapsadas_censo']} "
      f"({R['pct_colapsado_censo']:.4f} %) · observaciones en muestra: "
      f"{R['observaciones_en_muestra']}")

# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("2-3. CALIBRABILIDAD Y ESTIMADOR GREG (edad media, nivel persona)")
print("=" * 78)

ult = df.sort_values("conv_i").groupby("ID_PERSONA_PR", observed=True).last()
edad = pd.to_numeric(ult["EDAD_ANOS_PR"].str.replace(",", ".", regex=False),
                     errors="coerce")
ok = edad.notna()
pop = ult.loc[ok]
y_U = edad[ok].to_numpy()
samp = pop.loc[pop.index.isin(ids)]
y_s = pd.to_numeric(samp["EDAD_ANOS_PR"].str.replace(",", ".", regex=False),
                    errors="coerce").to_numpy()
N = len(pop)


def diagnostico(aux, etiqueta, excluir=()):
    X_U, X_s = matriz_aux(pop, samp, aux)
    nombres = list(pd.get_dummies(
        pd.concat([pop[aux].reset_index(drop=True),
                   samp[aux].reset_index(drop=True)], ignore_index=True),
        drop_first=True, dtype=float).columns)
    if excluir:
        # tercera via: sacar del vector auxiliar la columna que no se puede
        # calibrar, en lugar de dejarla dentro con su total sin reproducir.
        fuera = [i for i, n in enumerate(nombres) if n in excluir]
        X_U = np.delete(X_U, fuera, axis=1)
        X_s = np.delete(X_s, fuera, axis=1)
        nombres = [n for i, n in enumerate(nombres) if i not in fuera]
    g, X_U_tot, X_ht, lam, w, cond = g_weights(X_s, X_U, N)
    Xs = np.hstack([np.ones((len(X_s), 1)), X_s])
    columnas = ["(intercepto)"] + nombres
    tot_cal = (w * (Xs * g[:, None])).sum(axis=0)
    desv = X_U_tot - tot_cal
    fallan = {columnas[i]: float(desv[i]) for i in range(len(desv))
              if abs(desv[i]) > 1e-6}
    rango = int(np.linalg.matrix_rank(w * (Xs.T @ Xs)))
    gl = greg_lineal(y_s, X_s, X_U, N)
    print(f"\n-- {etiqueta}")
    print(f"   columnas auxiliares : {len(columnas)}")
    print(f"   rango(M)            : {rango} de {len(columnas)}")
    print(f"   cond(M)             : {cond:.6e}")
    print(f"   columnas NO calibrables ({len(fallan)}): "
          f"{ {k: round(v, 6) for k, v in fallan.items()} }")
    print(f"   max |desviacion| en las calibrables: "
          f"{max([abs(v) for k, v in {c: desv[i] for i, c in enumerate(columnas)}.items() if k not in fallan] or [0.0]):.3e}")
    print(f"   GREG-lineal edad    : {gl['estimador']:.12f}   "
          f"var={gl['varianza']:.12e}  r2={gl['r2_en_la_muestra']:.6f}")
    print(f"   SUMA w*g            : {(w * g).sum():.10f}   (N = {N})")
    return {"etiqueta": etiqueta, "n_columnas": len(columnas), "rango_M": rango,
            "cond_M": cond, "no_calibrables": fallan, "greg": gl["estimador"],
            "var": gl["varianza"], "r2": gl["r2_en_la_muestra"]}


AUX_COL = [COL_GENERO_COL if a == COL_GENERO else a for a in AUX_EDAD]
A = diagnostico(AUX_EDAD_CRUDA, "SIN colapsar (Intersexual + No disponible por separado)")
B = diagnostico(AUX_COL, "COLAPSADO (Otro / No especificado)")
C = diagnostico(AUX_COL, "COLAPSADO + columna 'Otro' excluida del vector auxiliar",
                excluir=(f"{COL_GENERO_COL}_{ETIQUETA_OTRO}",))

print("\n-- DIFERENCIAS")
print(f"   GREG      : {A['greg']:.12f} -> {B['greg']:.12f}   "
      f"diff = {B['greg'] - A['greg']:.3e} años")
print(f"   varianza  : diff relativa = "
      f"{abs(B['var'] - A['var']) / A['var']:.3e}")
print(f"   cond(M)   : {A['cond_M']:.3e} -> {B['cond_M']:.3e}   (C: {C['cond_M']:.3e})")
print(f"   rango(M)  : {A['rango_M']} -> {B['rango_M']} de {B['n_columnas']}"
      f"   (C: {C['rango_M']} de {C['n_columnas']})")
print(f"   columnas no calibrables: {len(A['no_calibrables'])} -> "
      f"{len(B['no_calibrables'])}   (C: {len(C['no_calibrables'])})")
print(f"   masa no calibrada: {sum(A['no_calibrables'].values()):.0f} personas -> "
      f"{sum(B['no_calibrables'].values()):.0f} personas   "
      f"(C: {sum(C['no_calibrables'].values()):.0f})")

# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("4. REPRESENTATIVIDAD DEL GENERO (chi2 poblacion vs muestra)")
print("=" * 78)
perfil_pob = ult
perfil_mue = ult.loc[ult.index.isin(ids)]
for col, etq in [(COL_GENERO, "sin colapsar"), (COL_GENERO_COL, "colapsado")]:
    r = comparar_poblacion(perfil_pob[col], perfil_mue[col])
    print(f"\n-- {etq}: categorias={list(r['categorias'])}")
    print(f"   chi2={r['chi2']:.6f}  gl={r['gl']}  p={r['p_valor']:.6f}  "
          f"min_esperado={r['min_esperado']:.4f}  supuesto_ok={r['supuesto_frecuencias_ok']}")
    print(f"   max dif = {r['max_diferencia_pp']:.4f} pp")

# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("5. TABLAS DE RETENCION / TRANSICION POR GENERO: aparecen las raras?")
print("=" * 78)
L = json.loads((DOC / "data" / "memoria" / "longitudinal_resultados.json")
               .read_text(encoding="utf-8"))
E = json.loads((DOC / "data" / "memoria" / "eda_resultados.json")
               .read_text(encoding="utf-8"))


def buscar(o, ruta=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(k, str) and any(r in k for r in CATEGORIAS_RARAS):
                yield f"{ruta}.{k}"
            yield from buscar(v, f"{ruta}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from buscar(v, f"{ruta}[{i}]")


for nombre, d in (("longitudinal_resultados.json", L), ("eda_resultados.json", E)):
    hits = [h for h in buscar(d)]
    print(f"\n{nombre}: {len(hits)} apariciones de categorias raras")
    for h in hits:
        if "GENERO" in h.upper() or "genero" in h:
            print(f"   [GENERO] {h}")
