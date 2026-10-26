#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
entrenar_bayesiano_minimo.py
============================

Fase 5 — reformulacion MINIMA del modelo bayesiano ordinal jerarquico.

Contexto: el run completo (25 predictores, mascaras IJ/IE, 4 cadenas x
2000+2000, nutpie) no termino en 3 h de computo sin compilador C
(ver diseno_bayesiano.md §7.1). Esta version reduce el orden de magnitud
del COMPUTO, no del diseno:

    12 predictores | 2 cadenas x 1000 tune + 1000 draws | nutpie
    sin mascaras IJ/IE (ordinal puro)
    se conservan u_c y v_t (non-centered) y los priors de §4

Universo: se ajusta SOLO con las 19 838 filas de train y se evalua en las
9 994 de val. Las 43 187 transiciones son el tamano del universo, no filas
de ajuste. El test (13 355) se descarta ANTES de construir features: nunca
se carga ni se usa.

Salidas:
    07_modelo/modelado/modelos/trace_bayesiano_minimo.nc
    07_modelo/modelado/resultados/bayesiano_minimo_<fecha>.json

Codigos: 0 OK | 2 error de datos/dependencias | 3 no convergencia (deuda)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# --- Igual que entrenar_bayesiano.py: sin compilador C, cache en TEMP --------
_TMP_CACHE = Path(os.environ.get("TEMP", ".")) / "dsh_bayes"
_TMP_CACHE.mkdir(parents=True, exist_ok=True)
_BASE_PYT = str(_TMP_CACHE / "pytensor").replace("\\", "/")
os.environ["PYTENSOR_FLAGS"] = f"cxx=,base_compiledir={_BASE_PYT}"
os.environ["NUMBA_CACHE_DIR"] = str(_TMP_CACHE / "numba")
(_TMP_CACHE / "numba").mkdir(exist_ok=True)

SCRIPT_DIR = Path(__file__).resolve().parent
_CACHE_DIR = SCRIPT_DIR.parent / ".cache"
_CACHE_DIR.mkdir(exist_ok=True)
os.environ["LOCALAPPDATA"] = str(_CACHE_DIR)
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_DIR / "matplotlib"))

try:  # ArviZ usa platformdirs, no la variable de entorno
    import platformdirs as _platformdirs
    _orig_user_cache = _platformdirs.user_cache_dir

    def _user_cache_dir(appname=None, appauthor=None, version=None, roaming=False):
        if appname == "arviz":
            return str(_CACHE_DIR / "arviz")
        return _orig_user_cache(appname, appauthor, version, roaming)

    _platformdirs.user_cache_dir = _user_cache_dir
except Exception:  # pragma: no cover
    pass

REPO = SCRIPT_DIR.parents[1]
DERIVADOS = SCRIPT_DIR.parent / "datos" / "derivados"
MODELOS_DIR = SCRIPT_DIR / "modelos"
RESULTADOS_DIR = SCRIPT_DIR / "resultados"
CENSO = REPO / "01_datos" / "datos_fuente" / \
    "Investigadores_Reconocidos_por_convocatoria_20261006.csv"

CLASES = ("baja", "se_mantiene", "sube")
CAT_MAP = {12: 0, 13: 1, 14: 2, 15: 3}       # IJ, I, IS, IE
PER_MAP = {17: 0, 18: 1, 19: 2}
N_CAT, N_PER = 4, 3

XGB_R1 = {"f1_macro": 0.3939, "f1_baja": 0.132, "auc_baja": 0.563,
          "brier": 0.5479}

# Los 12 predictores minimos
PREDICTORES = [
    "log_filas", "log_productos", "n_grupos", "dias", "sin_produccion",
    "share_nuevo_conocimiento", "share_formacion",
    "share_tip_articulos_investigacion", "share_cat_articulos_generacion",
    "genero_masculino", "edad", "depto_bogota",
]
NUM_STD = ["log_filas", "log_productos", "n_grupos", "dias", "edad"]


def cargar_censo(pd) -> "pd.DataFrame":
    cols = ["ID_PERSONA_PR", "ID_CONVOCATORIA", "NME_GENERO_PR",
            "EDAD_ANOS_PR", "NME_DEPARTAMENTO_RES_PR"]
    c = pd.read_csv(CENSO, usecols=cols, dtype=str, encoding="utf-8-sig",
                    keep_default_na=False)
    c["ID_PERSONA_PR"] = c["ID_PERSONA_PR"].str.strip().str.zfill(10)
    c["ID_CONVOCATORIA"] = pd.to_numeric(c["ID_CONVOCATORIA"],
                                         errors="coerce").astype("Int64")
    c = c.rename(columns={"NME_GENERO_PR": "genero",
                          "EDAD_ANOS_PR": "edad_raw",
                          "NME_DEPARTAMENTO_RES_PR": "depto"})
    return c


def construir_features(df, censo, pd, np):
    """Solo train/val. El test fue descartado aguas arriba."""
    df = df.merge(censo, on=["ID_PERSONA_PR", "ID_CONVOCATORIA"], how="left",
                  validate="many_to_one")
    prod = df["n_productos"].to_numpy(dtype=float)
    denom = np.maximum(prod, 1.0)

    def share(col):
        return np.clip(df[col].to_numpy(dtype=float) / denom, 0.0, 1.0)

    X = {}
    X["log_filas"] = np.log1p(df["n_filas"].to_numpy(dtype=float))
    X["log_productos"] = np.log1p(prod)
    X["n_grupos"] = df["n_grupos_distintos"].to_numpy(dtype=float)
    X["dias"] = df["dias_desde_ultimo"].to_numpy(dtype=float)
    X["sin_produccion"] = df["sin_produccion"].astype(float).to_numpy()
    X["share_nuevo_conocimiento"] = share("n_clase_NUEVO_CONOCIMIENTO")
    X["share_formacion"] = share("n_clase_FORMACI_N_DE_RECURSO_HUMANO")
    X["share_tip_articulos_investigacion"] = share(
        "n_tipologia_ART_CULOS_DE_INVESTIGACI_N")
    X["share_cat_articulos_generacion"] = share(
        "n_categoria_ART_CULOS_DE_GENERACI_N_DE_CONTENIDO")

    genero = df["genero"].fillna("").str.strip()
    X["genero_masculino"] = (genero == "Masculino").astype(float).to_numpy()
    edad = pd.to_numeric(df["edad_raw"].fillna("").str.replace(",", "."),
                         errors="coerce")
    X["edad"] = edad.to_numpy(dtype=float)
    depto = df["depto"].fillna("").str.upper().str.strip()
    X["depto_bogota"] = depto.str.startswith("BOGOT").astype(float).to_numpy()

    M = np.column_stack([X[n] for n in PREDICTORES])

    estratos = df["split"].to_numpy()
    idx_tr = np.where(estratos == "train")[0]
    idx_va = np.where(estratos == "val")[0]

    pos = {n: i for i, n in enumerate(PREDICTORES)}
    for n in ("dias", "edad"):            # imputacion con mediana de TRAIN
        col = M[:, pos[n]]
        med = float(np.nanmedian(col[idx_tr]))
        M[:, pos[n]] = np.where(np.isnan(col), med, col)
    media = {n: float(np.mean(M[idx_tr, pos[n]])) for n in NUM_STD}
    desv = {n: (float(np.std(M[idx_tr, pos[n]])) or 1.0) for n in NUM_STD}
    for n in NUM_STD:
        M[:, pos[n]] = (M[:, pos[n]] - media[n]) / desv[n]
    M = np.nan_to_num(M, nan=0.0)

    y = np.array([CLASES.index(c) for c in df["target_class"]])
    cat = np.array([CAT_MAP[int(o)] for o in df["ORDEN_CLAS_PR_actual"]])
    per = np.array([PER_MAP.get(int(c), -1)
                    for c in df["ID_CONVOCATORIA_siguiente"]])

    return {
        "X_train": M[idx_tr], "X_val": M[idx_va],
        "y_train": y[idx_tr], "y_val": y[idx_va],
        "cat_train": cat[idx_tr], "cat_val": cat[idx_va],
        "per_train": per[idx_tr],
        "media": media, "desv": desv,
        "n_train": int(len(idx_tr)), "n_val": int(len(idx_va)),
    }


def construir_modelo(datos, np):
    import pymc as pm
    import pytensor.tensor as pt

    X = datos["X_train"]
    with pm.Model() as modelo:
        beta = pm.Normal("beta", 0.0, 1.0, shape=(X.shape[1],))
        pi = pm.Dirichlet("pi", a=np.ones(3))
        k1 = pm.Deterministic("kappa1", pt.log(pi[0]) - pt.log1p(-pi[0]))
        k2 = pm.Deterministic("kappa2", pt.log(pi[0] + pi[1])
                              - pt.log1p(-(pi[0] + pi[1])))
        sigma_u = pm.HalfNormal("sigma_u", 1.0)
        sigma_v = pm.HalfNormal("sigma_v", 1.0)
        z_u = pm.Normal("z_u", 0.0, 1.0, shape=(N_CAT,))
        z_v = pm.Normal("z_v", 0.0, 1.0, shape=(N_PER,))
        u = pm.Deterministic("u", sigma_u * z_u)
        v = pm.Deterministic("v", sigma_v * z_v)
        eta = X @ beta + u[datos["cat_train"]] + v[datos["per_train"]]
        p1 = pm.math.sigmoid(k1 - eta)
        p2 = pm.math.sigmoid(k2 - eta)
        p = pt.stack([p1, p2 - p1, 1.0 - p2], axis=-1)
        p = pt.clip(p, 1e-9, 1.0)
        pm.Categorical("y", p=p, observed=datos["y_train"])
    return modelo


def predecir_val(idata, datos, np, n_ic=400):
    """Media posterior de p en val, con v_20 ~ N(0, sigma_v) integrado.

    Calculo por bloques de draws para no materializar (9994 x S x 3).
    """
    beta = idata.posterior["beta"].to_numpy().reshape(-1, datos["X_val"].shape[1])
    u = idata.posterior["u"].to_numpy().reshape(-1, N_CAT)
    sv = idata.posterior["sigma_v"].to_numpy().reshape(-1)
    k1 = idata.posterior["kappa1"].to_numpy().reshape(-1)
    k2 = idata.posterior["kappa2"].to_numpy().reshape(-1)

    S = beta.shape[0]
    Xv = datos["X_val"]
    catv = datos["cat_val"]
    rng = np.random.default_rng(42)
    v_new = rng.normal(0.0, sv)          # periodo 20 = nivel nuevo

    p_sum = np.zeros((Xv.shape[0], 3))
    media_draw = np.zeros((S, 3))
    paso = max(1, S // n_ic)
    guardar = list(range(0, S, paso))
    p_ic = np.empty((Xv.shape[0], 3, len(guardar)), dtype="float32")

    for ini in range(0, S, 100):
        fin = min(ini + 100, S)
        b = beta[ini:fin]
        eta = Xv @ b.T
        eta = eta + u[ini:fin][:, catv].T
        eta = eta + v_new[ini:fin][None, :]
        p1 = 1.0 / (1.0 + np.exp(-(k1[ini:fin][None, :] - eta)))
        p2 = 1.0 / (1.0 + np.exp(-(k2[ini:fin][None, :] - eta)))
        p = np.stack([p1, p2 - p1, 1.0 - p2], axis=-1).astype("float32")
        p = np.clip(p, 1e-9, 1.0)
        p = p / p.sum(axis=2, keepdims=True)
        p_sum += p.sum(axis=1, dtype="float64")
        media_draw[ini:fin] = p.mean(axis=0)
        for j, s in enumerate(guardar):
            if ini <= s < fin:
                p_ic[:, :, j] = p[:, s - ini, :]

    p_mean = p_sum / S
    return {"p_mean": p_mean, "p_ic": p_ic, "media_por_draw": media_draw,
            "S": int(S), "draws_ic": len(guardar)}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Bayesiano ordinal jerarquico MINIMO (12 predictores).")
    ap.add_argument("--dataset", default="ventana_contiguo")
    ap.add_argument("--chains", type=int, default=2)
    ap.add_argument("--tune", type=int, default=1000)
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--target-accept", type=float, default=0.95)
    ap.add_argument("--sampler", default="nutpie", choices=["pymc", "nutpie"])
    ap.add_argument("--output",
                    default=str(MODELOS_DIR / "trace_bayesiano_minimo.nc"))
    args = ap.parse_args()

    try:
        import arviz as az
        import numpy as np
        import pandas as pd
        import pymc as pm
        from sklearn.metrics import f1_score, roc_auc_score
    except ImportError as exc:
        print("ERROR: falta dependencia:", exc)
        print("  Use 07_modelo/.venv-bayes")
        return 2

    print(f"Interprete: {sys.executable}")
    print(f"pymc {pm.__version__} | arviz {az.__version__} | sampler={args.sampler}")
    print(f"PYTENSOR_FLAGS={os.environ.get('PYTENSOR_FLAGS')}")

    ruta = DERIVADOS / f"modelo_dataset_{args.dataset}.parquet"
    if not ruta.exists():
        print(f"ERROR: no existe {ruta}")
        return 2

    df = pd.read_parquet(ruta)
    # El test se descarta ANTES de cualquier calculo de features.
    df = df[df["split"].isin(["train", "val"])].copy()
    assert (df["split"] != "test").all(), "el test se colo en el dataframe"

    censo = cargar_censo(pd)
    datos = construir_features(df, censo, pd, np)
    print(f"   train {datos['n_train']:,} | val {datos['n_val']:,} | "
          f"predictores {datos['X_train'].shape[1]}".replace(",", " "))
    print(f"   periodos train: {sorted(set(datos['per_train'].tolist()))} "
          f"(0=17,1=18,2=19) | val = periodo 20 (nivel nuevo)")

    modelo = construir_modelo(datos, np)
    print(f"   muestreo: chains={args.chains} tune={args.tune} draws={args.draws}")
    t0 = time.time()
    with modelo:
        kwargs = dict(draws=args.draws, tune=args.tune, chains=args.chains,
                      cores=min(args.chains, os.cpu_count() or 1),
                      target_accept=args.target_accept,
                      nuts_sampler=args.sampler,
                      return_inferencedata=True, progressbar=True)
        if args.sampler == "pymc":
            kwargs["idata_kwargs"] = {"log_likelihood": False}
        idata = pm.sample(**kwargs)
    segundos = time.time() - t0

    rhat = az.rhat(idata)
    ess = az.ess(idata, method="bulk")
    max_rhat = float(np.nanmax([float(np.nanmax(rhat[v].values))
                                for v in rhat.data_vars]))
    min_ess = float(np.nanmin([float(np.nanmin(ess[v].values))
                               for v in ess.data_vars]))
    div = int(idata.sample_stats["diverging"].values.sum())
    n_tot = int(idata.sample_stats["diverging"].values.size)
    pct_div = 100.0 * div / n_tot
    convergencia_ok = (max_rhat <= 1.01 and min_ess >= 400 and pct_div <= 0.1)

    print(f"\nDiagnosticos: r_hat_max={max_rhat:.4f} | ESS_min={min_ess:.0f} | "
          f"divergencias={div}/{n_tot} ({pct_div:.3f} %) | "
          f"tiempo={segundos/60:.2f} min")
    print("CONVERGENCIA: " + ("OK" if convergencia_ok else "FALLA"))

    ruta_salida = Path(args.output)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    idata.to_netcdf(ruta_salida)
    print(f"Trace: {ruta_salida}")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "modelo": "bayesiano_minimo (12 predictores, ordinal puro, sin mascaras)",
        "dataset": args.dataset,
        "interprete": sys.executable,
        "pymc": pm.__version__, "arviz": az.__version__, "sampler": args.sampler,
        "pytensor_flags": os.environ.get("PYTENSOR_FLAGS"),
        "chains": args.chains, "tune": args.tune, "draws": args.draws,
        "target_accept": args.target_accept,
        "n_train": datos["n_train"], "n_val": datos["n_val"],
        "n_universo_transiciones": 43187,
        "test_usado": False,
        "predictores": PREDICTORES,
        "estandarizacion": {"media": datos["media"], "desv": datos["desv"]},
        "diagnosticos": {"r_hat_max": max_rhat, "ess_min": min_ess,
                         "divergencias": div, "iteraciones": n_tot,
                         "pct_divergencias": pct_div},
        "convergencia_ok": convergencia_ok,
        "segundos": round(segundos, 1),
        "minutos": round(segundos / 60, 2),
        "trace": str(ruta_salida),
    }

    if convergencia_ok:
        pred = predecir_val(idata, datos, np)
        p_mean = pred["p_mean"]
        y_val = datos["y_val"]
        y_str = np.array([CLASES[i] for i in y_val])
        pred_idx = p_mean.argmax(axis=1)
        pred_str = np.array([CLASES[i] for i in pred_idx])

        f1_macro = float(f1_score(y_str, pred_str, labels=list(CLASES),
                                  average="macro", zero_division=0))
        f1_clase = f1_score(y_str, pred_str, labels=list(CLASES),
                            average=None, zero_division=0)
        auc = {}
        for i, c in enumerate(CLASES):
            yb = (y_str == c).astype(int)
            auc[c] = (float(roc_auc_score(yb, p_mean[:, i]))
                      if len(np.unique(yb)) > 1 else None)
        onehot = np.zeros_like(p_mean)
        onehot[np.arange(len(y_val)), y_val] = 1.0
        brier = float(np.mean(np.sum((p_mean - onehot) ** 2, axis=1)))

        ci = {}
        for i, c in enumerate(CLASES):
            md = pred["media_por_draw"][:, i]
            q80 = np.percentile(md, [10, 90])
            q95 = np.percentile(md, [2.5, 97.5])
            obs = pred["p_ic"][:, i, :]
            o80 = np.percentile(obs, [10, 90], axis=1)
            o95 = np.percentile(obs, [2.5, 97.5], axis=1)
            ci[c] = {
                "media": float(md.mean()),
                "ic80_agregado": [float(q80[0]), float(q80[1])],
                "ic95_agregado": [float(q95[0]), float(q95[1])],
                "ancho_medio_ic80_por_obs": float(np.mean(o80[1] - o80[0])),
                "ancho_medio_ic95_por_obs": float(np.mean(o95[1] - o95[0])),
            }

        resumen["metricas"] = {
            "f1_macro": f1_macro,
            "f1_por_clase": {c: float(v) for c, v in zip(CLASES, f1_clase)},
            "auc_ovr": auc, "brier": brier,
        }
        resumen["intervalos"] = ci
        resumen["draws_prediccion"] = {"total": pred["S"],
                                       "usados_para_ic": pred["draws_ic"]}
        resumen["xgboost_r1"] = XGB_R1
        resumen["comparacion"] = {
            "delta_f1_macro_pp": round(100 * (f1_macro - XGB_R1["f1_macro"]), 2),
            "delta_brier": round(brier - XGB_R1["brier"], 4),
            "delta_auc_baja": round((auc["baja"] or 0) - XGB_R1["auc_baja"], 4),
        }

        print(f"\nVAL (n={len(y_val)}) — bayesiano minimo")
        print(f"   F1 macro = {f1_macro:.4f}  (XGBoost r1 {XGB_R1['f1_macro']:.4f}, "
              f"delta {resumen['comparacion']['delta_f1_macro_pp']:+.1f} pp)")
        print(f"   F1 baja={f1_clase[0]:.3f} | F1 se_mantiene={f1_clase[1]:.3f} | "
              f"F1 sube={f1_clase[2]:.3f}")
        print(f"   AUC baja={auc['baja']} | AUC se_mantiene={auc['se_mantiene']} | "
              f"AUC sube={auc['sube']}   (XGBoost r1 AUC baja {XGB_R1['auc_baja']})")
        print(f"   Brier = {brier:.4f}  (XGBoost r1 {XGB_R1['brier']:.4f}, "
              f"delta {resumen['comparacion']['delta_brier']:+.4f})")
        for c in CLASES:
            d = ci[c]
            print(f"   [{c}] prob media {d['media']:.3f} | IC80 "
                  f"[{d['ic80_agregado'][0]:.3f}, {d['ic80_agregado'][1]:.3f}] | "
                  f"IC95 [{d['ic95_agregado'][0]:.3f}, {d['ic95_agregado'][1]:.3f}]")

    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    ruta_json = RESULTADOS_DIR / ("bayesiano_minimo_"
                                  + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                                  + ".json")
    ruta_json.write_text(json.dumps(resumen, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    print(f"Resumen: {ruta_json}")

    if not convergencia_ok:
        print("\nNO CONVERGIO: deuda tecnica declarada. No se reajusta sin OK.")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
