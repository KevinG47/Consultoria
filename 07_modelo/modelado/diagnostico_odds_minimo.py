#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
diagnostico_odds_minimo.py
==========================

Ajuste 1 del diseno, version MINIMA: diagnostico POST-AJUSTE de odds
proporcionales sobre el modelo de 12 predictores (trace_bayesiano_minimo.nc).

Modelo relajado (solo train, sin mascaras, 12 predictores):

    κ_{k,c} = κ_k + δ_{k,c},   δ ~ Normal(0, 0.5),   δ_{k,IJ} = 0

Si las posteriores de β cambian poco (|Δmedia| <= 0.2 y mismos signos), la
hipotesis de odds proporcionales es plausible; si cambian mucho, se declara
como limitacion medida.

Muestreo corto: 1 cadena x 500 (nutpie). Solo train/val; test no se toca.

Uso:
    <python 07_modelo/.venv-bayes> 07_modelo/modelado/diagnostico_odds_minimo.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- Cache y flags ANTES de importar arviz/pymc (ver entrenar_bayesiano_minimo)
_TMP_CACHE = Path(os.environ.get("TEMP", ".")) / "dsh_bayes"
_TMP_CACHE.mkdir(parents=True, exist_ok=True)
os.environ["PYTENSOR_FLAGS"] = (
    "cxx=,base_compiledir=" + str(_TMP_CACHE / "pytensor").replace("\\", "/"))
os.environ["NUMBA_CACHE_DIR"] = str(_TMP_CACHE / "numba")
(_TMP_CACHE / "numba").mkdir(exist_ok=True)

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
_CACHE_DIR = SCRIPT_DIR.parent / ".cache"
_CACHE_DIR.mkdir(exist_ok=True)
os.environ["LOCALAPPDATA"] = str(_CACHE_DIR)
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_DIR / "matplotlib"))
try:
    import platformdirs as _pd
    _orig = _pd.user_cache_dir

    def _uc(appname=None, appauthor=None, version=None, roaming=False):
        if appname == "arviz":
            return str(_CACHE_DIR / "arviz")
        return _orig(appname, appauthor, version, roaming)

    _pd.user_cache_dir = _uc
except Exception:  # pragma: no cover
    pass


def main() -> int:
    try:
        import arviz as az
        import numpy as np
        import pandas as pd
        import pymc as pm
        import pytensor.tensor as pt
        import entrenar_bayesiano_minimo as em
    except ImportError as exc:
        print("ERROR: falta dependencia:", exc)
        return 2

    trace = SCRIPT_DIR / "modelos" / "trace_bayesiano_minimo.nc"
    if not trace.exists():
        print(f"ERROR: no existe {trace}")
        return 2

    ruta = SCRIPT_DIR.parent / "datos" / "derivados" / \
        "modelo_dataset_ventana_contiguo.parquet"
    df = pd.read_parquet(ruta)
    df = df[df["split"].isin(["train", "val"])].copy()   # test nunca se carga
    censo = em.cargar_censo(pd)
    datos = em.construir_features(df, censo, pd, np)
    X = datos["X_train"]
    y = datos["y_train"]
    cat = datos["cat_train"]

    with pm.Model() as modelo:
        beta = pm.Normal("beta", 0.0, 1.0, shape=(X.shape[1],))
        pi = pm.Dirichlet("pi", a=np.ones(3))
        k1 = pm.Deterministic("kappa1", pt.log(pi[0]) - pt.log1p(-pi[0]))
        k2 = pm.Deterministic("kappa2", pt.log(pi[0] + pi[1])
                              - pt.log1p(-(pi[0] + pi[1])))
        sigma_u = pm.HalfNormal("sigma_u", 1.0)
        sigma_v = pm.HalfNormal("sigma_v", 1.0)
        z_u = pm.Normal("z_u", 0.0, 1.0, shape=(em.N_CAT,))
        z_v = pm.Normal("z_v", 0.0, 1.0, shape=(em.N_PER,))
        u = pm.Deterministic("u", sigma_u * z_u)
        v = pm.Deterministic("v", sigma_v * z_v)
        delta = pm.Normal("delta", 0.0, 0.5, shape=(2, 3))   # I, IS, IE
        delta_ext = pt.concatenate([pt.zeros((2, 1)), delta], axis=1)
        eta = X @ beta + u[cat] + v[datos["per_train"]]
        p1 = pm.math.sigmoid(k1 + delta_ext[0, cat] - eta)
        p2 = pm.math.sigmoid(k2 + delta_ext[1, cat] - eta)
        p = pt.stack([p1, p2 - p1, 1.0 - p2], axis=-1)
        p = pt.clip(p, 1e-9, 1.0)
        pm.Categorical("y", p=p, observed=y)

    with modelo:
        idata = pm.sample(draws=500, tune=500, chains=1, cores=1,
                          target_accept=0.9, nuts_sampler="nutpie",
                          return_inferencedata=True, progressbar=True)

    base = az.from_netcdf(trace)
    b_base = base.posterior["beta"].to_numpy().reshape(-1, X.shape[1])
    b_rel = idata.posterior["beta"].to_numpy().reshape(-1, X.shape[1])
    media_base, media_rel = b_base.mean(axis=0), b_rel.mean(axis=0)
    sd_base, sd_rel = b_base.std(axis=0), b_rel.std(axis=0)
    dif = np.abs(media_rel - media_base)

    ess = az.ess(idata, method="bulk")
    min_ess = float(np.nanmin([float(np.nanmin(ess[v].values))
                               for v in ess.data_vars]))
    div = int(idata.sample_stats["diverging"].values.sum())
    n = int(idata.sample_stats["diverging"].values.size)

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "modelo": "minimo relajado: delta_{k,c} ~ Normal(0, 0.5), delta_{k,IJ}=0",
        "sampler": "nutpie", "chains": 1, "tune": 500, "draws": 500,
        "diagnosticos": {"r_hat_max": None, "ess_min": min_ess,
                         "divergencias": div, "iteraciones": n},
        "beta": {
            "max_abs_delta_media": float(dif.max()),
            "media_abs_delta_media": float(dif.mean()),
            "correlacion_medias": float(np.corrcoef(media_base, media_rel)[0, 1]),
            "max_abs_delta_sd": float(np.abs(sd_rel - sd_base).max()),
            "cambio_de_signo": int(np.sum(np.sign(media_base) != np.sign(media_rel))),
            "predictores": em.PREDICTORES,
            "media_base": media_base.tolist(),
            "media_relajada": media_rel.tolist(),
            "sd_base": sd_base.tolist(),
            "sd_relajada": sd_rel.tolist(),
        },
        "veredicto": {
            "odds_proporcionales_plausibles": bool(
                dif.max() <= 0.2
                and np.sum(np.sign(media_base) != np.sign(media_rel)) == 0),
            "umbral_delta_media": 0.2,
        },
    }
    salida = SCRIPT_DIR / "resultados" / (
        "odds_diagnostico_minimo_"
        + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"delta media max={dif.max():.3f} | media={dif.mean():.3f} | "
          f"corr={resumen['beta']['correlacion_medias']:.3f} | "
          f"cambios de signo={resumen['beta']['cambio_de_signo']} | "
          f"ESS_min={min_ess:.0f} | div={div}/{n}")
    print("odds proporcionales plausibles: "
          + ("SI" if resumen["veredicto"]["odds_proporcionales_plausibles"] else "NO"))
    print(f"Guardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
