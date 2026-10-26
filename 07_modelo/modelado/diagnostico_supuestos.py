#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
diagnostico_supuestos.py
========================

Diagnostico B: supuestos de la logistica y autocorrelacion de predicciones.

  1. VIF sobre las features numericas (no one-hot).
  2. Box-Tidwell (linealidad del logit) para "baja" y "sube".
  3. Autocorrelacion de predicciones por persona: se entrena con el split
     por persona (80/20, semilla 42) y se mide el ICC(1) de P(baja) y
     P(sube) entre filas de la misma persona, y el % de personas con clase
     predicha constante.

Solo train/val; test no se toca.

Uso:
    <python con xgboost> 07_modelo/modelado/diagnostico_supuestos.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DERIVADOS = SCRIPT_DIR.parent / "datos" / "derivados"
MODELOS_DIR = SCRIPT_DIR / "modelos"
RESULTADOS_DIR = SCRIPT_DIR / "resultados"

CLASES = ("baja", "se_mantiene", "sube")
NUMERICAS = ["ano", "n_filas", "n_productos", "n_grupos_distintos", "dias_desde_ultimo"]


def icc1(grupos, np):
    k = len(grupos)
    if k < 2:
        return None
    n_i = np.array([len(g) for g in grupos], dtype=float)
    total = n_i.sum()
    grand = sum(g.sum() for g in grupos) / total
    ssb = sum(n_i[j] * (grupos[j].mean() - grand) ** 2 for j in range(k))
    ssw = sum(((grupos[j] - grupos[j].mean()) ** 2).sum() for j in range(k))
    msb = ssb / (k - 1)
    msw = ssw / (total - k)
    if msb + (msw * 0) == 0:
        return None
    n0 = (total - (n_i ** 2).sum() / total) / (k - 1)
    return float((msb - msw) / (msb + (n0 - 1) * msw))


def main() -> int:
    try:
        import numpy as np
        import pandas as pd
        import statsmodels.api as sm
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        import xgboost as xgb
    except ImportError as exc:
        print("ERROR: falta dependencia:", exc)
        print(f"Interprete actual: {sys.executable}")
        return 2

    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Interprete: {sys.executable}")
    print("REGLA: train/val; test no se toca.")

    resultados = {}
    for ds in ("ventana_contiguo", "acumulado_contiguo"):
        cfg = json.loads((MODELOS_DIR / f"config_{ds}.json").read_text(encoding="utf-8"))
        feats = cfg["features"]
        params = cfg["xgboost"]["mejor"]
        df = pd.read_parquet(DERIVADOS / f"modelo_dataset_{ds}.parquet")
        train = df[df["split"] == "train"].copy()
        num = [c for c in NUMERICAS if c in feats]
        X = train[num].fillna(train[num].median())

        print(f"\n== {ds} ==  numericas: {num}")

        # ---- VIF ----
        Xc = sm.add_constant(X)
        vif = {}
        for i, col in enumerate(Xc.columns):
            if col == "const":
                continue
            vif[col] = float(variance_inflation_factor(Xc.values, i))
        print("   VIF: " + " · ".join(f"{k}={v:.2f}" for k, v in vif.items()))

        # ---- Box-Tidwell ----
        def box_tidwell(y_bin):
            base = X - X.min() + 1.0          # todas positivas
            inter = {f"{c}_ln": base[c] * np.log(base[c]) for c in base.columns}
            Xi = pd.concat([X, pd.DataFrame(inter, index=X.index)], axis=1)
            Xi = sm.add_constant(Xi)
            try:
                res = sm.Logit(y_bin, Xi).fit(disp=0, maxiter=300)
                return {c: float(res.pvalues[f"{c}_ln"]) for c in base.columns}
            except Exception as exc:  # noqa: BLE001
                return {"error": str(exc)}

        bt_baja = box_tidwell((train["target_class"] == "baja").astype(int))
        bt_sube = box_tidwell((train["target_class"] == "sube").astype(int))
        print("   Box-Tidwell p-valores (x*ln x) — baja: " +
              " · ".join(f"{k}={v:.4g}" for k, v in bt_baja.items()))
        print("   Box-Tidwell p-valores (x*ln x) — sube: " +
              " · ".join(f"{k}={v:.4g}" for k, v in bt_sube.items()))

        # ---- autocorrelacion de predicciones por persona ----
        ids = df["ID_PERSONA_PR"].unique()
        rng = np.random.default_rng(42)
        perm = rng.permutation(len(ids))
        corte = int(0.8 * len(ids))
        train_ids = set(ids[perm[:corte]])
        val_ids = set(ids[perm[corte:]])
        train_p = df[df["ID_PERSONA_PR"].isin(train_ids)]
        val_p = df[df["ID_PERSONA_PR"].isin(val_ids)].copy()

        yi = np.array([CLASES.index(c) for c in train_p["target_class"]])
        conteo = np.bincount(yi, minlength=3)
        w = (len(yi) / (3.0 * conteo))[yi]
        modelo = xgb.XGBClassifier(objective="multi:softprob", eval_metric="mlogloss",
                                   tree_method="hist", n_jobs=-1, random_state=42,
                                   verbosity=0, **params)
        modelo.fit(train_p[feats], yi, sample_weight=w)
        proba = modelo.predict_proba(val_p[feats])
        val_p["p_baja"] = proba[:, CLASES.index("baja")]
        val_p["p_sube"] = proba[:, CLASES.index("sube")]
        val_p["pred"] = [CLASES[i] for i in proba.argmax(1)]

        grupos_baja, grupos_sube, constantes = [], [], 0
        n_multi = 0
        for _, sub in val_p.groupby("ID_PERSONA_PR"):
            if len(sub) < 2:
                continue
            n_multi += 1
            grupos_baja.append(sub["p_baja"].to_numpy())
            grupos_sube.append(sub["p_sube"].to_numpy())
            if sub["pred"].nunique() == 1:
                constantes += 1
        icc_baja = icc1(grupos_baja, np) if grupos_baja else None
        icc_sube = icc1(grupos_sube, np) if grupos_sube else None
        pct_const = 100.0 * constantes / n_multi if n_multi else None
        print(f"   Autocorrelacion (split por persona): personas con >=2 filas en val={n_multi} | "
              f"ICC P(baja)={icc_baja} | ICC P(sube)={icc_sube} | "
              f"clase constante en {pct_const:.1f} % de esas personas"
              if pct_const is not None else "   Autocorrelacion: sin personas con >=2 filas")

        resultados[ds] = {
            "numericas": num,
            "vif": vif,
            "vif_alto": {k: v for k, v in vif.items() if v > 10},
            "box_tidwell_baja": bt_baja,
            "box_tidwell_sube": bt_sube,
            "autocorrelacion": {
                "personas_val_con_2_o_mas": n_multi,
                "icc_p_baja": icc_baja,
                "icc_p_sube": icc_sube,
                "pct_clase_constante": pct_const,
            },
        }

    print("\nLectura: VIF>10 indica multicolinealidad; Box-Tidwell con p<0.05 indica "
          "no linealidad del logit; ICC alto indica predicciones muy dependientes de la persona.")
    salida = RESULTADOS_DIR / f"diagnostico_supuestos_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    salida.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
