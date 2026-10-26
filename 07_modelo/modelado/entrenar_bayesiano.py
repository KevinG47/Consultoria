#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
entrenar_bayesiano.py
=====================

Fase 5: modelo bayesiano jerárquico ordinal (cumulative link) para la
transicion de categoria. Solo train/val; test no se toca.

Modelo (ver diseno_bayesiano.md):
    y_i ~ Categorical(p_i)   con p_i derivada de un logit acumulativo
    η_i = x_i'β + u_{c(i)} + v_{t(i)}
    P(y ≤ k) = sigmoid(κ_k − η),  κ_1 < κ_2
    u_c = σ_u z_c, v_t = σ_v w_t   (non-centered)
    β ~ N(0,1), π_ref ~ Dirichlet(1,1,1) -> κ, σ ~ HalfNormal(1)
    Máscaras: IJ no puede "baja"; IE no puede "sube".

Incluye el TEST UNITARIO de renormalizacion de mascaras ANTES de NUTS.

Requisitos: pymc, arviz, pandas, numpy, pyarrow (venv 07_modelo/.venv-bayes).

Uso:
    <python> 07_modelo/modelado/entrenar_bayesiano.py --smoke
    <python> 07_modelo/modelado/entrenar_bayesiano.py --chains 4 --tune 2000 --draws 2000

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

# Sin compilador C en esta maquina: PyTensor en modo Python.
# Cache en TEMP (ruta corta: la de OneDrive supera MAX_PATH con numba).
_TMP_CACHE = Path(os.environ.get("TEMP", ".")) / "dsh_bayes"
_TMP_CACHE.mkdir(parents=True, exist_ok=True)
_BASE_PYT = str(_TMP_CACHE / "pytensor").replace("\\", "/")
os.environ["PYTENSOR_FLAGS"] = f"cxx=,base_compiledir={_BASE_PYT}"
os.environ["NUMBA_CACHE_DIR"] = str(_TMP_CACHE / "numba")
(_TMP_CACHE / "numba").mkdir(exist_ok=True)

SCRIPT_DIR = Path(__file__).resolve().parent
# El sandbox no permite escribir en %LOCALAPPDATA% real: ArviZ/Matplotlib cachean ahi.
_CACHE_DIR = SCRIPT_DIR.parent / ".cache"
_CACHE_DIR.mkdir(exist_ok=True)
os.environ["LOCALAPPDATA"] = str(_CACHE_DIR)
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_DIR / "matplotlib"))

try:  # redirigir la cache de ArviZ (usa platformdirs, no la env var)
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
CATS = ("IJ", "I", "IS", "IE")
PERIODOS = ("17", "18", "19")
CAT_MAP = {12: 0, 13: 1, 14: 2, 15: 3}
PER_MAP = {17: 0, 18: 1, 19: 2}

# Predictores (25). Ver §3 del diseno.
CLASE_COLS = [
    "n_clase_APROPIACI_N_SOCIAL_DEL_CONOCIMIENTO",
    "n_clase_DESARROLLO_TECNOL_GICO_E_INNOVACI_N",
    "n_clase_FORMACI_N_DE_RECURSO_HUMANO",
    "n_clase_NO_CATEGORIZADO",
    "n_clase_NUEVO_CONOCIMIENTO",
]
TIP_COLS = [
    "n_tipologia_ART_CULOS_DE_INVESTIGACI_N",
    "n_tipologia_TESIS_DE_PREGRADO",
    "n_tipologia_EVENTO_CIENT_FICO",
    "n_tipologia_ART_CULOS",
]
CAT_COLS = [
    "n_categoria_ART_CULOS_DE_GENERACI_N_DE_CONTENIDO",
    "n_categoria_TESIS_DE_PREGRADO_CON_CALIDAD_B",
    "n_categoria_EVENTO_CIENT_FICO_CON_CALIDAD_A",
]
PREDICTORES = (
    ["log_filas", "log_productos", "log_grupos", "dias", "sin_produccion"]
    + [f"share_clase_{i}" for i in range(5)]
    + ["share_clase_otras"]
    + [f"share_tip_{i}" for i in range(4)]
    + [f"share_cat_{i}" for i in range(3)]
    + ["share_cat_otras"]
    + ["genero_masculino", "genero_desconocido", "edad", "edad_faltante",
       "depto_bogota", "depto_antioquia"]
)


def _probs_masked(p, mask_ij, mask_ie):
    """p: tensor (N,3); pone a 0 las clases imposibles y renormaliza por fila."""
    import pytensor.tensor as pt
    p_baja = pt.where(mask_ij, 0.0, p[:, 0])
    p_sube = pt.where(mask_ie, 0.0, p[:, 2])
    p_mant = p[:, 1]
    total = p_baja + p_mant + p_sube
    return pt.stack([p_baja / total, p_mant / total, p_sube / total], axis=-1)


def _test_mascaras() -> None:
    """Test unitario (ajuste 2): sum(p_masked)==1 para filas IJ e IE."""
    import numpy as np
    import pytensor
    import pytensor.tensor as pt

    p = pt.as_tensor_variable(np.array([[0.3, 0.4, 0.3],
                                        [0.3, 0.4, 0.3],
                                        [0.3, 0.4, 0.3]], dtype="float64"))
    mask_ij = pt.as_tensor_variable(np.array([True, False, False]))
    mask_ie = pt.as_tensor_variable(np.array([False, True, False]))
    f = pytensor.function([], _probs_masked(p, mask_ij, mask_ie))
    q = f()
    assert np.allclose(q.sum(axis=1), 1.0), f"sumas: {q.sum(axis=1)}"
    assert abs(q[0, 0]) < 1e-12, "IJ sigue con p(baja)>0"
    assert abs(q[1, 2]) < 1e-12, "IE sigue con p(sube)>0"
    print("   [OK] test de renormalizacion de mascaras (IJ e IE)")


def cargar_censo(pd) -> "pd.DataFrame":
    cols = ["ID_PERSONA_PR", "ID_CONVOCATORIA", "NME_GENERO_PR",
            "EDAD_ANOS_PR", "NME_DEPARTAMENTO_RES_PR"]
    c = pd.read_csv(CENSO, usecols=cols, dtype=str, encoding="utf-8-sig",
                    keep_default_na=False)
    c["ID_PERSONA_PR"] = c["ID_PERSONA_PR"].str.strip().str.zfill(10)
    c["ID_CONVOCATORIA"] = pd.to_numeric(c["ID_CONVOCATORIA"], errors="coerce").astype("Int64")
    c = c.rename(columns={"NME_GENERO_PR": "genero",
                          "EDAD_ANOS_PR": "edad_raw",
                          "NME_DEPARTAMENTO_RES_PR": "depto"})
    return c


def construir_features(df, censo, pd, np):
    """Devuelve X_train, X_val, y_train, y_val, cat/periodo, mascaras y nombres."""
    # Unir demograficas por (persona, convocatoria)
    df = df.merge(censo, on=["ID_PERSONA_PR", "ID_CONVOCATORIA"], how="left",
                  validate="many_to_one")
    prod = df["n_productos"].to_numpy(dtype=float)
    denom = np.maximum(prod, 1.0)

    def share(col):
        return np.clip(df[col].to_numpy(dtype=float) / denom, 0.0, 1.0)

    X = {}
    X["log_filas"] = np.log1p(df["n_filas"].to_numpy(dtype=float))
    X["log_productos"] = np.log1p(prod)
    X["log_grupos"] = np.log1p(df["n_grupos_distintos"].to_numpy(dtype=float))
    X["dias"] = df["dias_desde_ultimo"].to_numpy(dtype=float)
    X["sin_produccion"] = df["sin_produccion"].astype(float).to_numpy()

    for i, col in enumerate(CLASE_COLS):
        X[f"share_clase_{i}"] = share(col)
    X["share_clase_otras"] = np.clip(1.0 - sum(X[f"share_clase_{i}"] for i in range(5)), 0, 1)
    for i, col in enumerate(TIP_COLS):
        X[f"share_tip_{i}"] = share(col)
    for i, col in enumerate(CAT_COLS):
        X[f"share_cat_{i}"] = share(col)
    X["share_cat_otras"] = np.clip(1.0 - sum(X[f"share_cat_{i}"] for i in range(3)), 0, 1)

    genero = df["genero"].fillna("").str.strip()
    X["genero_masculino"] = (genero == "Masculino").astype(float).to_numpy()
    X["genero_desconocido"] = (genero.isin(["", "No disponible"])).astype(float).to_numpy()
    edad = pd.to_numeric(df["edad_raw"].fillna("").str.replace(",", "."), errors="coerce")
    X["edad_faltante"] = edad.isna().astype(float).to_numpy()
    X["edad"] = edad.to_numpy(dtype=float)
    depto = df["depto"].fillna("").str.upper().str.strip()
    X["depto_bogota"] = depto.str.startswith("BOGOT").astype(float).to_numpy()
    X["depto_antioquia"] = (depto == "ANTIOQUIA").astype(float).to_numpy()

    M = np.column_stack([X[n] for n in PREDICTORES])

    estratos = df["split"].to_numpy()
    idx_tr = np.where(estratos == "train")[0]
    idx_va = np.where(estratos == "val")[0]
    # NOTA: se elimino el assert de presencia del split "test" (antes linea 195).
    # Era solo una comprobacion de integridad: no se calculaba idx_te ni se usaba
    # el test en ningun punto. Ver diseno_bayesiano.md §7.1.

    # Estandarizar las numericas con media/desv de TRAIN
    pos = {n: i for i, n in enumerate(PREDICTORES)}
    # Imputar NaN de dias/edad con la mediana de TRAIN (antes de estandarizar)
    for n in ("dias", "edad"):
        col = M[:, pos[n]]
        med = float(np.nanmedian(col[idx_tr]))
        M[:, pos[n]] = np.where(np.isnan(col), med, col)
    num_std = ["log_filas", "log_productos", "log_grupos", "dias", "edad"]
    media = {n: float(np.nanmean(M[idx_tr, pos[n]])) for n in num_std}
    desv = {n: float(np.nanstd(M[idx_tr, pos[n]])) or 1.0 for n in num_std}
    for n in num_std:
        M[:, pos[n]] = (M[:, pos[n]] - media[n]) / desv[n]
    M = np.nan_to_num(M, nan=0.0)

    y = np.array([CLASES.index(c) for c in df["target_class"]])
    cat = np.array([CAT_MAP[int(o)] for o in df["ORDEN_CLAS_PR_actual"]])
    periodo = np.array([PER_MAP.get(int(c), -1) for c in df["ID_CONVOCATORIA_siguiente"]])

    mask_ij = (cat == 0)
    mask_ie = (cat == 3)
    return {
        "X_train": M[idx_tr], "X_val": M[idx_va],
        "y_train": y[idx_tr], "y_val": y[idx_va],
        "cat_train": cat[idx_tr], "cat_val": cat[idx_va],
        "per_train": periodo[idx_tr], "per_val": periodo[idx_va],
        "mask_ij_train": mask_ij[idx_tr], "mask_ie_train": mask_ie[idx_tr],
        "mask_ij_val": mask_ij[idx_va], "mask_ie_val": mask_ie[idx_va],
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
        z_u = pm.Normal("z_u", 0.0, 1.0, shape=(len(CATS),))
        z_v = pm.Normal("z_v", 0.0, 1.0, shape=(len(PERIODOS),))
        u = pm.Deterministic("u", sigma_u * z_u)
        v = pm.Deterministic("v", sigma_v * z_v)
        eta = X @ beta + u[datos["cat_train"]] + v[datos["per_train"]]
        p1 = pm.math.sigmoid(k1 - eta)
        p2 = pm.math.sigmoid(k2 - eta)
        p = pt.stack([p1, p2 - p1, 1.0 - p2], axis=-1)
        p = pt.clip(p, 1e-9, 1.0)
        p_masked = _probs_masked(p, datos["mask_ij_train"], datos["mask_ie_train"])
        pm.Categorical("y", p=p_masked, observed=datos["y_train"])
    return modelo


def main() -> int:
    ap = argparse.ArgumentParser(description="Modelo bayesiano ordinal jerarquico.")
    ap.add_argument("--dataset", default="ventana_contiguo")
    ap.add_argument("--chains", type=int, default=4)
    ap.add_argument("--tune", type=int, default=2000)
    ap.add_argument("--draws", type=int, default=2000)
    ap.add_argument("--target-accept", type=float, default=0.9)
    ap.add_argument("--smoke", action="store_true", help="1 cadena x 500 (prueba de tiempo)")
    ap.add_argument("--sampler", default="pymc", choices=["pymc", "nutpie"],
                    help="backend NUTS: pymc (nativo) o nutpie (Rust, mismo NUTS)")
    ap.add_argument("--output", default=str(MODELOS_DIR / "trace_bayesiano.nc"))
    args = ap.parse_args()

    if args.smoke:
        args.chains, args.tune, args.draws = 1, 500, 500

    try:
        import arviz as az
        import numpy as np
        import pandas as pd
        import pymc as pm
    except ImportError as exc:
        print("ERROR: falta dependencia:", exc)
        print("  Use 07_modelo/.venv-bayes")
        return 2

    print(f"Interprete: {sys.executable}")
    print(f"pymc {pm.__version__} | arviz {az.__version__} | sampler={args.sampler} | "
          f"PYTENSOR_FLAGS={os.environ.get('PYTENSOR_FLAGS')}")

    ruta = DERIVADOS / f"modelo_dataset_{args.dataset}.parquet"
    if not ruta.exists():
        print(f"ERROR: no existe {ruta}")
        return 2

    _test_mascaras()

    df = pd.read_parquet(ruta)
    censo = cargar_censo(pd)
    datos = construir_features(df, censo, pd, np)
    print(f"   train {datos['n_train']:,} | val {datos['n_val']:,} | "
          f"predictores {datos['X_train'].shape[1]}".replace(",", " "))
    print(f"   mascara IJ train: {int(datos['mask_ij_train'].sum()):,} | "
          f"IE train: {int(datos['mask_ie_train'].sum()):,}".replace(",", " "))
    print(f"   periodos train: {sorted(set(datos['per_train'].tolist()))} (0=17,1=18,2=19)")

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
    max_rhat = float(np.nanmax([float(np.nanmax(rhat[v].values)) for v in rhat.data_vars]))
    min_ess = float(np.nanmin([float(np.nanmin(ess[v].values)) for v in ess.data_vars]))
    div = int(idata.sample_stats["diverging"].values.sum())
    n_tot = int(idata.sample_stats["diverging"].values.size)
    pct_div = 100.0 * div / n_tot

    if args.chains < 2:
        print("   [aviso] 1 cadena: r_hat no es calculable; la prueba es solo de TIEMPO")
        convergencia_ok = None
    else:
        convergencia_ok = (max_rhat <= 1.01 and min_ess >= 400 and pct_div <= 0.1)
    print(f"\nDiagnosticos: r_hat_max={max_rhat:.4f} | ESS_min={min_ess:.0f} | "
          f"divergencias={div}/{n_tot} ({pct_div:.3f} %) | tiempo={segundos/60:.2f} min")
    print("CONVERGENCIA: " + ("OK" if convergencia_ok else "FALLA"))

    ruta_salida = Path(args.output)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    idata.to_netcdf(ruta_salida)
    print(f"Trace: {ruta_salida}")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset": args.dataset,
        "interprete": sys.executable,
        "pymc": pm.__version__, "arviz": az.__version__, "sampler": args.sampler,
        "pytensor_flags": os.environ.get("PYTENSOR_FLAGS"),
        "chains": args.chains, "tune": args.tune, "draws": args.draws,
        "target_accept": args.target_accept,
        "n_train": datos["n_train"], "n_val": datos["n_val"],
        "predictores": PREDICTORES,
        "estandarizacion": {"media": datos["media"], "desv": datos["desv"]},
        "diagnosticos": {"r_hat_max": max_rhat, "ess_min": min_ess,
                         "divergencias": div, "iteraciones": n_tot,
                         "pct_divergencias": pct_div},
        "convergencia_ok": convergencia_ok,
        "segundos": round(segundos, 1),
        "trace": str(ruta_salida),
    }
    ruta_json = RESULTADOS_DIR / f"bayesiano_{'smoke' if args.smoke else 'fit'}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    ruta_json.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resumen: {ruta_json}")

    if convergencia_ok is False:
        print("\nNO CONVERGIO: se detiene como deuda tecnica declarada. No se reajusta.")
        return 3
    if args.smoke:
        print("\nPrueba de tiempo terminada (sin veredicto de convergencia).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
