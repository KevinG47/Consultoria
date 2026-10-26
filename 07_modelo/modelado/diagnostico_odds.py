#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
diagnostico_odds.py
===================

Ajuste 1 del diseno: diagnostico POST-AJUSTE de odds proporcionales.

Compara el modelo ordinal de odds proporcionales (trace principal) con un
modelo relajado que permite cortes desplazados por categoria de origen:

    κ_{k,c} = κ_k + δ_{k,c},   δ ~ Normal(0, 0.5),  δ_{k,IJ} = 0

Si las posteriores de β cambian poco, la hipotesis de odds proporcionales es
plausible; si cambian mucho, se declara como limitacion medida.

Muestreo corto: 1 cadena x 500 (nutpie). Solo train/val; test no se toca.

Uso:
    <python 07_modelo/.venv-bayes> 07_modelo/modelado/diagnostico_odds.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

CLASES = ("baja", "se_mantiene", "sube")


def _probs_masked(p, mask_ij, mask_ie):
    import pytensor.tensor as pt
    p_baja = pt.where(mask_ij, 0.0, p[:, 0])
    p_sube = pt.where(mask_ie, 0.0, p[:, 2])
    total = p_baja + p[:, 1] + p_sube
    return pt.stack([p_baja / total, p[:, 1] / total, p_sube / total], axis=-1)


def main() -> int:
    try:
        import arviz as az
        import numpy as np
        import pandas as pd
        import pymc as pm
        import pytensor.tensor as pt
        import entrenar_bayesiano as eb
    except ImportError as exc:
        print("ERROR: falta dependencia:", exc)
        return 2

    trace = SCRIPT_DIR / "modelos" / "trace_bayesiano.nc"
    if not trace.exists():
        print(f"ERROR: no existe {trace}")
        return 2

    df = pd.read_parquet(SCRIPT_DIR.parent / "datos" / "derivados" /
                         "modelo_dataset_ventana_contiguo.parquet")
    censo = eb.cargar_censo(pd)
    datos = eb.construir_features(df, censo, pd, np)
    X = datos["X_train"]
    y = datos["y_train"]
    cat = datos["cat_train"]

    # delta con columna 0 = 0 (IJ como referencia)
    with pm.Model() as modelo:
        beta = pm.Normal("beta", 0.0, 1.0, shape=(X.shape[1],))
        pi = pm.Dirichlet("pi", a=np.ones(3))
        k1 = pm.Deterministic("kappa1", pt.log(pi[0]) - pt.log1p(-pi[0]))
        k2 = pm.Deterministic("kappa2", pt.log(pi[0] + pi[1]) - pt.log1p(-(pi[0] + pi[1])))
        sigma_u = pm.HalfNormal("sigma_u", 1.0)
        sigma_v = pm.HalfNormal("sigma_v", 1.0)
        z_u = pm.Normal("z_u", 0.0, 1.0, shape=(4,))
        z_v = pm.Normal("z_v", 0.0, 1.0, shape=(3,))
        u = pm.Deterministic("u", sigma_u * z_u)
        v = pm.Deterministic("v", sigma_v * z_v)
        delta = pm.Normal("delta", 0.0, 0.5, shape=(2, 3))  # k x categorias I, IS, IE
        delta_ext = pt.concatenate([pt.zeros((2, 1)), delta], axis=1)  # 2 x 4
        eta = X @ beta + u[cat] + v[datos["per_train"]]
        p1 = pm.math.sigmoid(k1 + delta_ext[0, cat] - eta)
        p2 = pm.math.sigmoid(k2 + delta_ext[1, cat] - eta)
        p = pt.stack([p1, p2 - p1, 1.0 - p2], axis=-1)
        p = pt.clip(p, 1e-9, 1.0)
        p_masked = _probs_masked(p, datos["mask_ij_train"], datos["mask_ie_train"])
        pm.Categorical("y", p=p_masked, observed=y)

    with modelo:
        idata = pm.sample(draws=500, tune=500, chains=1, cores=1, target_accept=0.9,
                          nuts_sampler="nutpie", return_inferencedata=True,
                          progressbar=True)

    base = az.from_netcdf(trace)
    b_base = base.posterior["beta"].values.reshape(-1, X.shape[1])
    b_rel = idata.posterior["beta"].values.reshape(-1, X.shape[1])
    media_base, media_rel = b_base.mean(axis=0), b_rel.mean(axis=0)
    sd_base, sd_rel = b_base.std(axis=0), b_rel.std(axis=0)
    dif = np.abs(media_rel - media_base)

    rhat = az.rhat(idata)
    ess = az.ess(idata, method="bulk")
    max_rhat = float(np.nanmax([float(np.nanmax(rhat[v].values)) for v in rhat.data_vars])) if idata.posterior.chain.size > 1 else None
    min_ess = float(np.nanmin([float(np.nanmin(ess[v].values)) for v in ess.data_vars]))
    div = int(idata.sample_stats["diverging"].values.sum())
    n = int(idata.sample_stats["diverging"].values.size)

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "modelo": "relajado con delta_{k,c} ~ Normal(0, 0.5), delta_{k,IJ}=0",
        "sampler": "nutpie", "chains": 1, "tune": 500, "draws": 500,
        "diagnosticos": {"r_hat_max": max_rhat, "ess_min": min_ess,
                         "divergencias": div, "iteraciones": n},
        "beta": {
            "max_abs_delta_media": float(dif.max()),
            "media_abs_delta_media": float(dif.mean()),
            "correlacion_medias": float(np.corrcoef(media_base, media_rel)[0, 1]),
            "max_abs_delta_sd": float(np.abs(sd_rel - sd_base).max()),
            "cambio_de_signo": int(np.sum(np.sign(media_base) != np.sign(media_rel))),
            "predictores": eb.PREDICTORES,
            "media_base": media_base.tolist(),
            "media_relajada": media_rel.tolist(),
        },
    }
    salida = SCRIPT_DIR / "resultados" / f"odds_diagnostico_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"delta media max={dif.max():.3f} | media={dif.mean():.3f} | "
          f"corr={resumen['beta']['correlacion_medias']:.3f} | "
          f"cambios de signo={resumen['beta']['cambio_de_signo']} | "
          f"ESS_min={min_ess:.0f} | div={div}/{n}")
    print(f"Guardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
