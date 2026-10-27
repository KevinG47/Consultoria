#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
auditoria_eda.py
================

Los siete analisis que faltaban en el EDA (ver documentacion/auditoria_base_datos.md).
NO reentrena el modelo operativo y NO toca el test.

  a. chi2 de homogeneidad de target_class entre train/val/test (+ V de Cramer)
  b. PSI y KS por feature: train vs test
  c. atipicos de n_productos: IQR, winsorizacion al p99 (calibrada en train)
  d. VIF iterativo sobre las 172 features, eliminando la de mayor VIF hasta <= 10
  e. features muertas: >90 % y >99 % ceros; propuesta de poda
  f. fechas post-convocatoria: productos con fcreacion_pd posterior al ano_convo

Uso:
    python auditoria_eda.py [--saltar-fechas]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import opt_comun as oc  # noqa: E402

RESULTADOS = SCRIPT_DIR / "resultados"
PRODUCCION = Path(r"C:\datos_externos\minciencias\33dq-ab5a\2026-10-25\produccion_grupos.csv")
CONV_ANO = {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021}


# ---------------------------------------------------------------- a) chi2
def chi2_homogeneidad(df):
    from scipy.stats import chi2_contingency
    tabla = pd.crosstab(df["split"], df["target_class"])
    chi2, p, gl, esp = chi2_contingency(tabla)
    n = tabla.to_numpy().sum()
    v = float(np.sqrt(chi2 / (n * (min(tabla.shape) - 1))))
    pares = {}
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        t2 = pd.crosstab(df.loc[df["split"].isin([a, b]), "split"],
                         df.loc[df["split"].isin([a, b]), "target_class"])
        c2, p2, _, _ = chi2_contingency(t2)
        n2 = t2.to_numpy().sum()
        pares[f"{a}_vs_{b}"] = {"chi2": round(float(c2), 2), "p": float(p2),
                                "v_cramer": round(float(np.sqrt(c2 / (n2 * (min(t2.shape) - 1)))), 4)}
    return {"tabla": tabla.to_dict(), "chi2": round(float(chi2), 2), "gl": int(gl),
            "p": float(p), "v_cramer": round(v, 4),
            "esperados_min": round(float(esp.min()), 2), "pares": pares}


# ---------------------------------------------------------- b) PSI y KS
def psi(base, comp, bins=10):
    qs = np.unique(np.quantile(base, np.linspace(0, 1, bins + 1)))
    if len(qs) < 3:
        return float("nan")
    qs[0], qs[-1] = -np.inf, np.inf
    b = np.histogram(base, bins=qs)[0] / len(base)
    c = np.histogram(comp, bins=qs)[0] / len(comp)
    eps = 1e-6
    b = np.clip(b, eps, None)
    c = np.clip(c, eps, None)
    return float(np.sum((c - b) * np.log(c / b)))


def psi_ks(X, feats, tr, te):
    from scipy.stats import ks_2samp
    A, B = X[tr], X[te]
    filas = []
    for j, f in enumerate(feats):
        a, b = A[:, j], B[:, j]
        p = psi(a, b)
        ks = ks_2samp(a, b)
        filas.append({"feature": f, "psi": round(float(p), 4),
                      "ks": round(float(ks.statistic), 4),
                      "ks_p": float(ks.pvalue),
                      "media_train": round(float(a.mean()), 3),
                      "media_test": round(float(b.mean()), 3)})
    filas.sort(key=lambda r: (-(r["psi"] if np.isfinite(r["psi"]) else -1)))
    return filas


# ------------------------------------------------------------ c) atipicos
def atipicos(df, feats=None):
    x = df["n_productos"].astype(float)
    q1, q3 = float(x.quantile(0.25)), float(x.quantile(0.75))
    iqr = q3 - q1
    lim_inf, lim_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    p99_train = float(x[df["split"] == "train"].quantile(0.99))
    sobre_iqr = int((x > lim_sup).sum())
    sobre_p99 = int((x > p99_train).sum())
    por_split = {s: int((x[df["split"] == s] > p99_train).sum()) for s in ("train", "val", "test")}
    return {"q1": q1, "q3": q3, "iqr": iqr, "limite_superior_iqr": round(lim_sup, 2),
            "max": float(x.max()), "p99_train": round(p99_train, 2),
            "filas_sobre_iqr": sobre_iqr,
            "filas_sobre_p99_train": sobre_p99,
            "filas_sobre_p99_por_split": por_split,
            "pct_sobre_iqr": round(100 * sobre_iqr / len(x), 2),
            "pct_sobre_p99": round(100 * sobre_p99 / len(x), 2),
            "media_antes": round(float(x.mean()), 2),
            "media_winsorizada_p99": round(float(x.clip(upper=p99_train).mean()), 2),
            "std_antes": round(float(x.std()), 2),
            "std_winsorizada": round(float(x.clip(upper=p99_train).std()), 2)}


# ------------------------------------------------------------ d) VIF
def vif_iterativo(X, feats, umbral=10.0, max_iter=200):
    """VIF por pasos: (0) quita constantes, (1) quita duplicados exactos,
    (2) elimina la de mayor VIF hasta que todas queden <= umbral."""
    nombres = list(feats)
    X = np.array(X, dtype="float64")
    # el dataset tiene nulos en algunas filas (dias_desde_ultimo); el VIF exige
    # matriz completa: se imputan a 0 (misma convencion que usa XGBoost al separar)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    eliminadas = []
    t0 = time.time()

    # 0) varianza cero
    var = X.var(axis=0)
    for j in sorted(np.flatnonzero(var <= 0), reverse=True):
        eliminadas.append({"feature": nombres[j], "vif": None, "motivo": "varianza cero"})
        nombres.pop(j)
        X = np.delete(X, j, axis=1)

    # 1) duplicados exactos (|r| >= 0.99999): se conserva la primera
    if X.shape[1] > 1:
        R = np.corrcoef(X.T)
        iu = np.triu_indices_from(R, k=1)
        pares = sorted(zip(iu[0], iu[1], np.abs(R[iu])), key=lambda t: -t[2])
        fuera = set()
        for i, j, r in pares:
            if r < 0.99999:
                break
            if i in fuera or j in fuera:
                continue
            fuera.add(j)
            eliminadas.append({"feature": nombres[j], "vif": None,
                               "motivo": f"duplicado exacto de {nombres[i]} (r={r:.5f})"})
        for j in sorted(fuera, reverse=True):
            nombres.pop(j)
            X = np.delete(X, j, axis=1)

    # 2) VIF iterativo
    metodo = "inv"
    while len(nombres) > 2:
        R = np.corrcoef(X.T)
        if not np.all(np.isfinite(R)):
            R = np.nan_to_num(R, nan=0.0, posinf=0.0, neginf=0.0)
            np.fill_diagonal(R, 1.0)
        try:
            inv = np.linalg.inv(R)
            metodo = "inv"
        except np.linalg.LinAlgError:
            inv = np.linalg.pinv(R)
            metodo = "pinv"
        vif = np.diag(inv)
        j = int(np.nanargmax(vif))
        if not np.isfinite(vif[j]) or vif[j] <= umbral:
            break
        eliminadas.append({"feature": nombres[j], "vif": round(float(vif[j]), 2), "motivo": "VIF"})
        nombres.pop(j)
        X = np.delete(X, j, axis=1)
        if len(eliminadas) >= max_iter:
            break

    R = np.corrcoef(X.T)
    try:
        vif_final = np.diag(np.linalg.inv(R))
        metodo = "inv"
    except np.linalg.LinAlgError:
        vif_final = np.diag(np.linalg.pinv(R))
        metodo = "pinv"
    vif_final = np.where(np.isfinite(vif_final), vif_final, np.nan)
    return {"n_inicial": len(feats), "n_final": len(nombres),
            "n_eliminadas": len(eliminadas), "umbral": umbral,
            "max_vif_final": round(float(np.nanmax(vif_final)), 2) if np.isfinite(np.nanmax(vif_final)) else None,
            "metodo": metodo,
            "eliminadas": eliminadas,
            "segundos": round(time.time() - t0, 1)}


# -------------------------------------------------- e) features muertas
def features_muertas(X, feats, ganancias=None):
    ceros = (X == 0).mean(axis=0)
    m90 = [f for f, z in zip(feats, ceros) if z > 0.90]
    m99 = [f for f, z in zip(feats, ceros) if z > 0.99]
    sin_var = [f for f, z in zip(feats, ceros) if z == 1.0]
    g0 = []
    if ganancias:
        g0 = [f for f in feats if ganancias.get(f, 0) == 0]
    fam = lambda f: ("categoria" if f.startswith("n_categoria") else
                     "tipologia" if f.startswith("n_tipologia") else
                     "clase" if f.startswith("n_clase") else "volumen")
    def cuenta(lista):
        d = {}
        for f in lista:
            d[fam(f)] = d.get(fam(f), 0) + 1
        return d
    return {"n_features": len(feats),
            "n_mas_90_ceros": len(m90), "n_mas_99_ceros": len(m99),
            "n_todas_cero": len(sin_var), "n_gain_0": len(g0),
            "por_familia_90": cuenta(m90), "por_familia_99": cuenta(m99),
            "ejemplos_99": m99[:15],
            "propuesta_poda": [f for f in m99],
            "propuesta_poda_n": len(m99)}


# ------------------------------------- f) fechas post-convocatoria (chunks)
def fechas_post_convocatoria(ruta=PRODUCCION, chunksize=250_000):
    acum = {}
    pares = {}
    total = 0
    t0 = time.time()
    lector = pd.read_csv(ruta, usecols=["id_convocatoria", "ano_convo", "fcreacion_pd",
                                        "id_producto_pd", "id_persona_pd"],
                         dtype=str, chunksize=chunksize, encoding="utf-8",
                         on_bad_lines="skip")
    for ch in lector:
        total += len(ch)
        ch["conv"] = pd.to_numeric(ch["id_convocatoria"], errors="coerce").astype("Int64")
        ch = ch[ch["conv"].isin(list(CONV_ANO)).fillna(False)]
        if ch.empty:
            continue
        # comparacion lexicografica de fechas ISO (YYYY-MM-DD) es equivalente a la temporal
        cre = ch["fcreacion_pd"].str.slice(0, 10)
        conv = ch["ano_convo"].str.slice(0, 10)
        valida = cre.str.match(r"^\d{4}-\d{2}-\d{2}$").fillna(False) & conv.str.match(r"^\d{4}-\d{2}-\d{2}$").fillna(False)
        tarde = pd.Series(False, index=ch.index)
        tarde[valida] = cre[valida] > conv[valida]
        ch = ch.assign(tarde=tarde)
        for c, g in ch.groupby("conv"):
            a = acum.setdefault(int(c), {"filas": 0, "tarde": 0,
                                         "productos": set(), "productos_tarde": set(),
                                         "personas": set(), "personas_tarde": set()})
            a["filas"] += len(g)
            a["tarde"] += int(g["tarde"].sum())
            a["productos"].update(g["id_producto_pd"].dropna().unique().tolist())
            a["productos_tarde"].update(g.loc[g["tarde"], "id_producto_pd"].dropna().unique().tolist())
            a["personas"].update(g["id_persona_pd"].dropna().unique().tolist())
            a["personas_tarde"].update(g.loc[g["tarde"], "id_persona_pd"].dropna().unique().tolist())
        agg = (ch.groupby(["id_persona_pd", "conv"])["tarde"]
                 .agg(n="size", t="sum"))
        for (pid, cc), row in agg.iterrows():
            k = (str(pid), int(cc))
            d = pares.setdefault(k, [0, 0])
            d[0] += int(row["n"])
            d[1] += int(row["t"])
    resumen = []
    for c in sorted(acum):
        a = acum[c]
        resumen.append({"convocatoria": c, "ano": CONV_ANO[c], "filas": a["filas"],
                        "filas_tarde": a["tarde"],
                        "pct_filas_tarde": round(100 * a["tarde"] / a["filas"], 4) if a["filas"] else None,
                        "productos": len(a["productos"]),
                        "productos_tarde": len(a["productos_tarde"]),
                        "personas": len(a["personas"]),
                        "personas_con_al_menos_uno_tarde": len(a["personas_tarde"])})
    shares = [t / n for n, t in pares.values() if n > 0 and t > 0]
    todo_tarde = sum(1 for n, t in pares.values() if n > 0 and t == n)
    return {"archivo": str(ruta), "filas_leidas": total,
            "por_convocatoria": resumen,
            "pares_persona_convocatoria": len(pares),
            "pares_con_al_menos_uno_tarde": len(shares),
            "share_medio_de_productos_tarde": round(float(np.mean(shares)), 4) if shares else None,
            "pares_100pct_tarde": int(todo_tarde),
            "segundos": round(time.time() - t0, 1)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--saltar-fechas", action="store_true")
    args = ap.parse_args()

    df, feats = oc.cargar()
    tr = (df["split"] == "train").to_numpy()
    va = (df["split"] == "val").to_numpy()
    te = (df["split"] == "test").to_numpy()
    X = df[feats].to_numpy(dtype="float64")
    print(f"dataset: {len(df)} filas | {len(feats)} features | train {tr.sum()} val {va.sum()} test {te.sum()}")

    print("\n=== a) chi2 de homogeneidad de target_class ===")
    a = chi2_homogeneidad(df)
    print(json.dumps({k: v for k, v in a.items() if k != "tabla"}, ensure_ascii=False, indent=1))
    print("tabla:", json.dumps(a["tabla"], ensure_ascii=False))

    print("\n=== b) PSI / KS por feature (train vs test) ===")
    b = psi_ks(X, feats, tr, te)
    for umbral in (0.25, 0.20, 0.10):
        print(f"  features con PSI > {umbral}: {sum(1 for r in b if r['psi'] > umbral)}")
    print(f"  KS p<0,01: {sum(1 for r in b if r['ks_p'] < 0.01)} de {len(b)}")
    print("  top-10 por PSI:")
    for r in b[:10]:
        print(f"    {r['feature'][:60]:60s} PSI={r['psi']:8.3f} KS={r['ks']:.3f}")

    print("\n=== c) atipicos de n_productos ===")
    c = atipicos(df)
    print(json.dumps(c, ensure_ascii=False, indent=1))

    print("\n=== d) VIF iterativo (172 features, umbral 10) ===")
    d = vif_iterativo(X, feats)
    print(json.dumps({k: v for k, v in d.items() if k != "eliminadas"}, ensure_ascii=False))
    print("  primeras 10 eliminadas:", json.dumps(d["eliminadas"][:10], ensure_ascii=False))

    print("\n=== e) features muertas ===")
    import joblib
    cont = joblib.load(SCRIPT_DIR / "modelos" / "xgb_ventana_contiguo.joblib")
    gain = dict(zip(cont["features"], np.asarray(cont["modelo"].feature_importances_)))
    e = features_muertas(X, feats, gain)
    print(json.dumps({k: v for k, v in e.items() if k not in ("ejemplos_99", "propuesta_poda")},
                     ensure_ascii=False))

    f = None
    if not args.saltar_fechas and PRODUCCION.exists():
        print("\n=== f) fechas post-convocatoria (produccion_grupos.csv, por chunks) ===")
        f = fechas_post_convocatoria()
        print(json.dumps(f, ensure_ascii=False, indent=1))
    else:
        print("\n=== f) fechas post-convocatoria: OMITIDO (archivo no disponible) ===")

    salida = {"fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "a_chi2": a, "b_psi_ks": b, "c_atipicos": c, "d_vif": d, "e_muertas": e,
              "f_fechas": f}
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    p = RESULTADOS / ("auditoria_eda_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    p.write_text(json.dumps(salida, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"\nGuardado: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
