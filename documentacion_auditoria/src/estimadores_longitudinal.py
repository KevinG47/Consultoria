# -*- coding: utf-8 -*-
"""
estimadores_longitudinal.py
===========================

Partes 2 y 3 de la metodología: post-estratificación y estimador GREG, comparados
con el MAS puro y con el valor censal (que en este proyecto se conoce, porque la
base completa está disponible).

Fundamento
----------
- Post-estratificación: Cochran (1977, §5A) y Lohr (2010, §7.6). Cochran (1977,
  pp. 132-134) recomienda entre cuatro y seis estratos con un tamaño razonable
  (~20) en cada uno. La varianza post-estratificada se estima con
  v = SUM_h W_h^2 (1 - n_h/N_h) s_h^2 / n_h.
- GREG (model-assisted): Särndal, Swensson & Wretman (1992, §6.4-6.5) y FCSM
  (2003). Se usa la forma de diferencia
      Y_GREG = media_U(y_hat) + media_s(y - y_hat)
  que es consistente por diseño aunque el modelo no sea correcto (Kalton, 2002).
- Con un modelo LINEAL y auxiliares conocidos en toda la población, GREG adopta
  la forma clásica  Y_GREG = ybar_s + (Xbar_U - xbar_s)' beta_s.
- Comprobación interna: con un modelo SATURADO en los post-estratos, GREG y la
  post-estratificación coinciden exactamente. Se verifica numéricamente.

Produce: data/memoria/estimadores_resultados.json

Uso:  python estimadores_longitudinal.py
"""

from __future__ import annotations

import io
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize
from sklearn.linear_model import LogisticRegression

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Colapso de las categorias de genero no representadas en la muestra (ver
# genero_comun.py). El genero entra en los auxiliares por la columna COLAPSADA;
# la columna cruda se conserva para el control de calidad.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from genero_comun import (  # noqa: E402
    COL_GENERO, COL_GENERO_COL, agregar_genero_colapsado, resumen_colapso)

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
CSV = RAIZ / "01_datos" / "datos_fuente" / "Investigadores_Reconocidos_por_convocatoria_20261006.csv"
IDS = DOC / "data" / "memoria" / "muestra_ids.csv"
SALIDA = DOC / "data" / "memoria" / "estimadores_resultados.json"

CONV_ORDEN = [16, 17, 18, 19, 20, 21]
ANIOS = {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021}
CATEGORIAS = ["Investigador Junior", "Investigador Asociado",
              "Investigador Sénior", "Investigador Emérito"]
RANGO = {c: i for i, c in enumerate(CATEGORIAS)}

AUX_RET = ["NME_CLASIFICACION_PR", COL_GENERO_COL, "NME_GRAN_AREA_PR",
           "NME_DEPARTAMENTO_RES_PR"]
AUX_EDAD = [COL_GENERO_COL, "NME_GRAN_AREA_PR", "NME_REGION_RES_PR"]


def cargar() -> pd.DataFrame:
    partes = [t for t in pd.read_csv(CSV, dtype=str, keep_default_na=False,
                                     chunksize=50_000, encoding="utf-8")]
    df = pd.concat(partes, ignore_index=True)
    df["conv_i"] = df["ID_CONVOCATORIA"].astype(int)
    return agregar_genero_colapsado(df)


def matriz_aux(pop: pd.DataFrame, samp: pd.DataFrame, cols: list[str],
               saturado: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """Dummies coherentes entre población y muestra (mismas columnas, mismo orden)."""
    p = pop[cols].reset_index(drop=True)
    s = samp[cols].reset_index(drop=True)
    todo = pd.concat([p, s], ignore_index=True)
    X = pd.get_dummies(todo, drop_first=not saturado, dtype=float)
    return X.iloc[:len(p)].to_numpy(), X.iloc[len(p):].to_numpy()


def var_mas(y: np.ndarray, N: int) -> dict:
    n = len(y)
    f = n / N
    s2 = float(np.var(y, ddof=1))
    return {"estimador": float(np.mean(y)), "varianza": (1 - f) * s2 / n,
            "n": n, "N": N, "s2": s2}


def var_greg(y: np.ndarray, pred: np.ndarray, N: int) -> dict:
    """Varianza linealizada del estimador de diferencia (residuos del modelo)."""
    n = len(y)
    f = n / N
    e = y - pred
    s2e = float(np.var(e, ddof=1))
    return {"varianza": (1 - f) * s2e / n, "s2_residuos": s2e, "n": n, "N": N}


def post_estratificado(y: np.ndarray, estrato_s: pd.Series, estrato_U: pd.Series,
                       N: int) -> dict:
    """Post-estratificación con pesos w_i = (N_h/N)/(n_h/n) y su varianza."""
    n = len(y)
    df = pd.DataFrame({"e": estrato_s.values, "y": y})
    W_h = estrato_U.value_counts(normalize=True)
    detalle, est, var = {}, 0.0, 0.0
    for h, sub in df.groupby("e", observed=True):
        n_h = len(sub)
        p_h = float(sub["y"].mean())
        W = float(W_h.get(h, 0.0))
        s2_h = float(np.var(sub["y"], ddof=1)) if n_h > 1 else 0.0
        N_h = W * N
        est += W * p_h
        var += W ** 2 * (1 - n_h / N_h) * s2_h / n_h if N_h > 0 else 0.0
        detalle[str(h)] = {"W_h": W, "N_h": N_h, "n_h": n_h, "p_h": p_h,
                           "s2_h": s2_h, "peso_w": (W * n) / n_h if n_h else None}
    return {"estimador": float(est), "varianza": float(var), "estratos": detalle,
            "n_estratos": len(detalle), "n_h_min": min(d["n_h"] for d in detalle.values())}


def greg_lineal(y_s: np.ndarray, X_s: np.ndarray, X_U: np.ndarray, N: int) -> dict:
    """
    GREG con modelo lineal: Y = ybar_s + (Xbar_U - xbar_s)' beta_s.

    Se anade el intercepto explicitamente porque `matriz_aux` usa drop_first=True:
    sin el, el grupo de referencia (codificado con todo ceros) quedaria con un
    valor ajustado de 0 y el modelo no representaria ni el nivel medio de y.
    """
    unos_s = np.ones((len(X_s), 1))
    unos_U = np.ones((len(X_U), 1))
    Xs = np.hstack([unos_s, X_s])
    Xu = np.hstack([unos_U, X_U])
    beta, *_ = np.linalg.lstsq(Xs, y_s, rcond=None)
    pred_s = Xs @ beta
    est = float(Xu.mean(axis=0) @ beta + np.mean(y_s - pred_s))
    v = var_greg(y_s, pred_s, N)
    ss_tot = float(np.sum((y_s - y_s.mean()) ** 2))
    r2 = 1 - float(np.sum((y_s - pred_s) ** 2)) / ss_tot if ss_tot else None
    return {"estimador": est, "varianza": v["varianza"],
            "s2_residuos": v["s2_residuos"], "n_coef": int(Xs.shape[1]),
            "r2_en_la_muestra": r2}


def greg_logit(y_s: np.ndarray, X_s: np.ndarray, X_U: np.ndarray, N: int) -> dict:
    modelo = LogisticRegression(max_iter=2000, C=1.0)
    modelo.fit(X_s, y_s)
    p_s = modelo.predict_proba(X_s)[:, 1]
    p_U = modelo.predict_proba(X_U)[:, 1]
    est = float(p_U.mean() + np.mean(y_s - p_s))
    v = var_greg(y_s, p_s, N)
    return {"estimador": est, "varianza": v["varianza"],
            "s2_residuos": v["s2_residuos"], "media_pred_U": float(p_U.mean()),
            "media_pred_s": float(p_s.mean()),
            "auc_aparente": float(_auc(y_s, p_s))}


def _auc(y: np.ndarray, p: np.ndarray) -> float:
    orden = np.argsort(p)
    y_ord = y[orden]
    n1, n0 = int(y_ord.sum()), int(len(y_ord) - y_ord.sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    rangos = np.arange(1, len(y_ord) + 1)
    return float((rangos[y_ord == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def ordinal_proporcional(y_niv: np.ndarray, X: np.ndarray, J: int = 3,
                         lam: float = 1.0) -> dict:
    """
    Modelo de odds proporcionales (ordinal logit) ajustado por máxima verosimilitud
    con penalización L2. P(Y<=j) = logistica(theta_j - x'beta).

    No hay statsmodels en este entorno, así que se implementa el MLE directamente.
    """
    k = X.shape[1]
    theta0 = np.array([-1.0, 1.0])[: J - 1]

    def neg_ll(par: np.ndarray) -> float:
        beta, theta = par[:k], par[k:]
        eta = X @ beta
        # asegura umbrales ordenados con una transformación suave
        th = np.concatenate([[theta[0]], theta[0] + np.cumsum(np.exp(theta[1:]))]) \
            if len(theta) > 1 else theta
        P = np.zeros((len(X), J))
        acum = 1.0 / (1.0 + np.exp(-(th[0] - eta)))
        P[:, 0] = acum
        for j in range(1, J - 1):
            siguiente = 1.0 / (1.0 + np.exp(-(th[j] - eta)))
            P[:, j] = np.maximum(siguiente - acum, 1e-12)
            acum = siguiente
        P[:, J - 1] = np.maximum(1.0 - acum, 1e-12)
        ll = np.log(P[np.arange(len(y_niv)), y_niv]).sum()
        return float(-ll + lam * np.sum(beta ** 2))

    par0 = np.concatenate([np.zeros(k), theta0])
    opt = optimize.minimize(neg_ll, par0, method="L-BFGS-B",
                            options={"maxiter": 2000})
    beta, theta = opt.x[:k], opt.x[k:]
    th = np.concatenate([[theta[0]], theta[0] + np.cumsum(np.exp(theta[1:]))]) \
        if len(theta) > 1 else theta
    return {"beta": beta.tolist(), "umbrales": th.tolist(),
            "neg_ll": float(opt.fun), "convergio": bool(opt.success),
            "_theta": th}


def probs_ordinal(modelo: dict, X: np.ndarray, J: int = 3) -> np.ndarray:
    beta, th = np.array(modelo["beta"]), np.array(modelo["umbrales"])
    eta = X @ beta
    P = np.zeros((len(X), J))
    acum = 1.0 / (1.0 + np.exp(-(th[0] - eta)))
    P[:, 0] = acum
    for j in range(1, J - 1):
        siguiente = 1.0 / (1.0 + np.exp(-(th[j] - eta)))
        P[:, j] = siguiente - acum
        acum = siguiente
    P[:, J - 1] = 1.0 - acum
    return P


def resumen(y_s, X_s, X_U, N, estrato_s, estrato_U, estrato_colapsado_s=None,
            estrato_colapsado_U=None, y_U=None) -> dict:
    """Los seis estimadores de un parámetro, con IC 95% y ganancia de precisión."""
    mas = var_mas(y_s, N)
    ps = post_estratificado(y_s, estrato_s, estrato_U, N)
    glin = greg_lineal(y_s, X_s, X_U, N)
    # el GREG logístico solo tiene sentido con una variable respuesta binaria
    binaria = set(np.unique(y_s)).issubset({0.0, 1.0})
    glog = greg_logit(y_s, X_s, X_U, N) if binaria else None
    out = {
        "censo": float(np.mean(y_U)) if y_U is not None else None,
        "mas": mas,
        "post_estratificado": ps,
        "greg_lineal": glin,
        "greg_logit": glog,
        "respuesta_binaria": binaria,
        "n_muestra": int(len(y_s)), "N_poblacion": int(N),
        "fraccion_muestreo": float(len(y_s) / N),
    }
    if estrato_colapsado_s is not None:
        out["post_estratificado_colapsado"] = post_estratificado(
            y_s, estrato_colapsado_s, estrato_colapsado_U, N)
    # IC 95% y ganancia de precisión frente al MAS
    for k in ("mas", "post_estratificado", "post_estratificado_colapsado",
              "greg_lineal", "greg_logit"):
        if k not in out or out[k] is None:
            continue
        e, v = out[k]["estimador"], out[k]["varianza"]
        ee = float(np.sqrt(max(v, 0)))
        out[k]["ee"] = ee
        out[k]["ic95"] = [e - 1.96 * ee, e + 1.96 * ee]
        out[k]["ganancia_varianza_vs_mas_pct"] = (
            100 * (1 - v / mas["varianza"]) if mas["varianza"] > 0 else None)
        out[k]["error_vs_censo_pp"] = (100 * (e - out["censo"])
                                       if out["censo"] is not None else None)
    return out


def main() -> int:
    print("== Carga ==")
    df = cargar()
    ids = set(pd.read_csv(IDS, dtype=str, keep_default_na=False)["ID_PERSONA_PR"])
    print(f"   {len(df)} registros · muestra de {len(ids)} ids (semilla 2026)")

    res: dict = {"fecha": datetime.now().isoformat(timespec="seconds"),
                 "nota": ("Los tres estimadores se comparan contra el valor censal "
                          "porque la base completa está disponible. La comparación "
                          "del error realizado es UNA realización de la muestra: "
                          "no es criterio para elegir estimador por sí sola."),
                 "muestra": {"ids": len(ids), "semilla": 2026}}

    # ---------------- referencias por convenio ---------------------------
    presentes = {c: set(df.loc[df["conv_i"] == c, "ID_PERSONA_PR"]) for c in CONV_ORDEN}
    ult = df.sort_values("conv_i").groupby("ID_PERSONA_PR", observed=True).last()

    # ------------- colapso de genero (decision documentada) ---------------
    res["genero_colapso"] = resumen_colapso(df, ids_muestra=ids)
    gc = res["genero_colapso"]
    print("\n== Genero: colapso de categorias no representadas ==")
    for c, d in gc["categorias_colapsadas"].items():
        print(f"   {c:16s} censo={d['personas_censo']:2d}  muestra={d['personas_muestra']}"
              f"  etiqueta solo en {d['convocatorias_con_la_etiqueta']}")
    print(f"   -> '{gc['etiqueta_colapsada']}': "
          f"{gc['personas_colapsadas_censo']} personas "
          f"({gc['pct_colapsado_censo']:.4f} % del censo), "
          f"{gc['observaciones_en_muestra']} en la muestra -> no calibrable")

    # ======================= 1) RETENCIÓN =================================
    print("\n== Retención: MAS / post-estratificado / GREG ==")
    ret: dict = {}
    for a, b in zip(CONV_ORDEN[:-1], CONV_ORDEN[1:]):
        pop = (df.loc[df["conv_i"] == a].drop_duplicates("ID_PERSONA_PR")
                 .set_index("ID_PERSONA_PR"))
        y_U = np.array([int(p in presentes[b]) for p in pop.index], dtype=float)
        samp = pop.loc[pop.index.isin(ids)]
        y_s = np.array([int(p in presentes[b]) for p in samp.index], dtype=float)
        X_U, X_s = matriz_aux(pop, samp, AUX_RET)
        cat_s, cat_U = samp["NME_CLASIFICACION_PR"], pop["NME_CLASIFICACION_PR"]
        col_s = cat_s.replace({"Investigador Emérito": "Investigador Sénior"})
        col_U = cat_U.replace({"Investigador Emérito": "Investigador Sénior"})
        r = resumen(y_s, X_s, X_U, len(pop), cat_s, cat_U, col_s, col_U, y_U)
        # reducción de varianza que PREDICE el censo (lo que el EDA justifica)
        p_bar = float(y_U.mean())
        p_h = pd.Series(y_U).groupby(cat_U.values, observed=True).mean()
        W_h = cat_U.value_counts(normalize=True)
        com = p_h.index.intersection(W_h.index)
        entre = float((W_h[com] * (p_h[com] - p_bar) ** 2).sum())
        dentro = float((W_h[com] * p_h[com] * (1 - p_h[com])).sum())
        r["reduccion_varianza_teorica_censo_pct"] = 100 * entre / (entre + dentro)
        ret[f"{ANIOS[a]}→{ANIOS[b]}"] = r
        print(f"   {ANIOS[a]}→{ANIOS[b]} (n={r['n_muestra']}, N={r['N_poblacion']}): "
              f"censo={100*r['censo']:.2f} | MAS={100*r['mas']['estimador']:.2f} "
              f"({r['mas']['ganancia_varianza_vs_mas_pct']:+.1f}%) | "
              f"PS={100*r['post_estratificado']['estimador']:.2f} "
              f"(mejora var {r['post_estratificado']['ganancia_varianza_vs_mas_pct']:+.1f}%) | "
              f"GREG-logit={100*r['greg_logit']['estimador']:.2f} "
              f"(mejora var {r['greg_logit']['ganancia_varianza_vs_mas_pct']:+.1f}%)")
    # retención global 2013 → 2021
    pop = (df.loc[df["conv_i"] == 16].drop_duplicates("ID_PERSONA_PR")
             .set_index("ID_PERSONA_PR"))
    y_U = np.array([int(p in presentes[21]) for p in pop.index], dtype=float)
    samp = pop.loc[pop.index.isin(ids)]
    y_s = np.array([int(p in presentes[21]) for p in samp.index], dtype=float)
    X_U, X_s = matriz_aux(pop, samp, AUX_RET)
    cat_s, cat_U = samp["NME_CLASIFICACION_PR"], pop["NME_CLASIFICACION_PR"]
    ret["2013→2021"] = resumen(
        y_s, X_s, X_U, len(pop), cat_s, cat_U,
        cat_s.replace({"Investigador Emérito": "Investigador Sénior"}),
        cat_U.replace({"Investigador Emérito": "Investigador Sénior"}), y_U)
    p_bar_g = float(y_U.mean())
    p_h_g = pd.Series(y_U).groupby(cat_U.values, observed=True).mean()
    W_h_g = cat_U.value_counts(normalize=True)
    com_g = p_h_g.index.intersection(W_h_g.index)
    entre_g = float((W_h_g[com_g] * (p_h_g[com_g] - p_bar_g) ** 2).sum())
    dentro_g = float((W_h_g[com_g] * p_h_g[com_g] * (1 - p_h_g[com_g])).sum())
    ret["2013→2021"]["reduccion_varianza_teorica_censo_pct"] = 100 * entre_g / (entre_g + dentro_g)
    print(f"   2013→2021 global: censo={100*ret['2013→2021']['censo']:.2f} | "
          f"MAS={100*ret['2013→2021']['mas']['estimador']:.2f} | "
          f"PS={100*ret['2013→2021']['post_estratificado']['estimador']:.2f} | "
          f"GREG-logit={100*ret['2013→2021']['greg_logit']['estimador']:.2f}")
    res["retencion"] = ret

    # ======================= 2) EDAD =======================================
    print("\n== Edad media: MAS / post-estratificado / GREG ==")
    edad_U = pd.to_numeric(ult["EDAD_ANOS_PR"].str.replace(",", ".", regex=False),
                           errors="coerce")
    ok = edad_U.notna()
    pop = ult.loc[ok]
    y_U = edad_U[ok].to_numpy()
    samp = pop.loc[pop.index.isin(ids)]
    y_s = pd.to_numeric(samp["EDAD_ANOS_PR"].str.replace(",", ".", regex=False),
                        errors="coerce").to_numpy()
    X_U, X_s = matriz_aux(pop, samp, AUX_EDAD)
    # post-estratos por categoría (categoría no es auxiliar "natural" de la edad,
    # pero es la variable que el EDA señaló como más heterogénea)
    cat_s, cat_U = samp["NME_CLASIFICACION_PR"], pop["NME_CLASIFICACION_PR"]
    edad_res = resumen(y_s, X_s, X_U, len(pop), cat_s, cat_U,
                       y_U=y_U)
    # variante sin los registros con edad > 100 (calidad del dato)
    m = y_U <= 100
    pop2 = pop.loc[m]
    samp2 = pop2.loc[pop2.index.isin(ids)]
    y_s2 = pd.to_numeric(samp2["EDAD_ANOS_PR"].str.replace(",", ".", regex=False),
                         errors="coerce").to_numpy()
    X_U2, X_s2 = matriz_aux(pop2, samp2, AUX_EDAD)
    res["edad_sin_mayores_100"] = resumen(
        y_s2, X_s2, X_U2, len(pop2), samp2["NME_CLASIFICACION_PR"],
        pop2["NME_CLASIFICACION_PR"], y_U=y_U[m])
    res["edad"] = edad_res
    print(f"   censo={edad_res['censo']:.3f} | MAS={edad_res['mas']['estimador']:.3f} | "
          f"PS={edad_res['post_estratificado']['estimador']:.3f} | "
          f"GREG-lineal={edad_res['greg_lineal']['estimador']:.3f} "
          f"(mejora var {edad_res['greg_lineal']['ganancia_varianza_vs_mas_pct']:+.1f}%) "
          f"[GREG-logit no aplica: la edad no es binaria]")
    print(f"   sin edades >100: censo={res['edad_sin_mayores_100']['censo']:.3f} | "
          f"MAS={res['edad_sin_mayores_100']['mas']['estimador']:.3f} | "
          f"PS={res['edad_sin_mayores_100']['post_estratificado']['estimador']:.3f} | "
          f"GREG-lineal={res['edad_sin_mayores_100']['greg_lineal']['estimador']:.3f}")

    # ======================= 3) ASCENSO DE CATEGORÍA =======================
    print("\n== Ascenso de categoría 2019→2021 ==")
    a, b = 20, 21
    ca = (df.loc[df["conv_i"] == a].drop_duplicates("ID_PERSONA_PR")
            .set_index("ID_PERSONA_PR"))
    cb = (df.loc[df["conv_i"] == b].drop_duplicates("ID_PERSONA_PR")
            .set_index("ID_PERSONA_PR"))
    comunes = ca.index.intersection(cb.index)
    cat_a = ca.loc[comunes, "NME_CLASIFICACION_PR"].map(RANGO)
    cat_b = cb.loc[comunes, "NME_CLASIFICACION_PR"].map(RANGO)
    mov = np.where(cat_b > cat_a, 2, np.where(cat_b == cat_a, 1, 0))
    pop_mov = ca.loc[comunes].copy()
    pop_mov["_nivel"] = mov
    pop_mov["_asciende"] = (mov == 2).astype(float)
    samp_mov = pop_mov.loc[pop_mov.index.isin(ids)]
    y_U = pop_mov["_asciende"].to_numpy()
    y_s = samp_mov["_asciende"].to_numpy()
    X_U, X_s = matriz_aux(pop_mov, samp_mov,
                          ["NME_CLASIFICACION_PR", COL_GENERO_COL,
                           "NME_GRAN_AREA_PR"])
    asc = resumen(y_s, X_s, X_U, len(pop_mov), samp_mov["NME_CLASIFICACION_PR"],
                  pop_mov["NME_CLASIFICACION_PR"], y_U=y_U)
    # modelo ordinal (odds proporcionales) sobre el movimiento de 3 niveles
    modelo_ord = ordinal_proporcional(samp_mov["_nivel"].to_numpy(), X_s, J=3)
    P_U = probs_ordinal(modelo_ord, X_U, J=3)
    p_asc_U = P_U[:, 2]
    p_asc_s = probs_ordinal(modelo_ord, X_s, J=3)[:, 2]
    est_ord = float(p_asc_U.mean() + np.mean(y_s - p_asc_s))
    v_ord = var_greg(y_s, p_asc_s, len(pop_mov))
    asc["greg_ordinal"] = {"estimador": est_ord, "varianza": v_ord["varianza"],
                           "s2_residuos": v_ord["s2_residuos"],
                           "convergio": modelo_ord["convergio"],
                           "beta": modelo_ord["beta"],
                           "umbrales": modelo_ord["umbrales"],
                           "neg_ll": modelo_ord["neg_ll"]}
    e, v = est_ord, v_ord["varianza"]
    asc["greg_ordinal"]["ee"] = float(np.sqrt(max(v, 0)))
    asc["greg_ordinal"]["ic95"] = [e - 1.96 * asc["greg_ordinal"]["ee"],
                                   e + 1.96 * asc["greg_ordinal"]["ee"]]
    asc["greg_ordinal"]["ganancia_varianza_vs_mas_pct"] = (
        100 * (1 - v / asc["mas"]["varianza"]))
    asc["greg_ordinal"]["error_vs_censo_pp"] = 100 * (est_ord - asc["censo"])
    asc["movimiento"] = {
        "permanece": int((mov == 1).sum()), "asciende": int((mov == 2).sum()),
        "desciende": int((mov == 0).sum()), "N": int(len(pop_mov)),
        "prop_asciende_censo": float(y_U.mean()),
        "prop_desciende_censo": float((mov == 0).mean()),
    }
    res["ascenso_2019_2021"] = asc
    print(f"   censo asciende={100*asc['censo']:.2f}% | MAS={100*asc['mas']['estimador']:.2f}% "
          f"| PS={100*asc['post_estratificado']['estimador']:.2f}% "
          f"| GREG-logit={100*asc['greg_logit']['estimador']:.2f}% "
          f"| GREG-ordinal={100*est_ord:.2f}%")

    # ============ 4) COMPROBACIÓN: GREG saturado == post-estratificado =====
    print("\n== Comprobación interna: GREG con modelo saturado == post-estratificado ==")
    comp = {}
    pop = (df.loc[df["conv_i"] == 20].drop_duplicates("ID_PERSONA_PR")
             .set_index("ID_PERSONA_PR"))
    y_U = np.array([int(p in presentes[21]) for p in pop.index], dtype=float)
    samp = pop.loc[pop.index.isin(ids)]
    y_s = np.array([int(p in presentes[21]) for p in samp.index], dtype=float)
    X_U_sat, X_s_sat = matriz_aux(pop, samp, ["NME_CLASIFICACION_PR"], saturado=True)
    g_sat = greg_lineal(y_s, X_s_sat, X_U_sat, len(pop))
    ps = ret["2019→2021"]["post_estratificado"]
    comp["retencion_2019_2021"] = {
        "greg_saturado": g_sat["estimador"],
        "post_estratificado": ps["estimador"],
        "diferencia_absoluta": abs(g_sat["estimador"] - ps["estimador"]),
        "varianza_saturado": g_sat["varianza"], "varianza_ps": ps["varianza"],
    }
    print(f"   GREG saturado ={100*g_sat['estimador']:.6f} %  "
          f"post-estratificado={100*ps['estimador']:.6f} %  "
          f"|dif|={100*comp['retencion_2019_2021']['diferencia_absoluta']:.2e} pp")
    res["comprobacion_greg_saturado_igual_ps"] = comp

    # ============ 5) condición de tamaño mínimo (Cochran) ==================
    cond = {}
    for par, r in ret.items():
        d = r["post_estratificado"]["estratos"]
        chicos = {k: v["n_h"] for k, v in d.items() if v["n_h"] <= 20}
        cond[par] = {"n_h_por_estrato": {k: v["n_h"] for k, v in d.items()},
                     "estratos_con_n_h_menor_igual_20": chicos,
                     "cumple_todos_mayor_20": not chicos,
                     "n_h_min": r["post_estratificado"]["n_h_min"]}
    res["condicion_tamano_minimo"] = cond
    print("\n== Condición n_h > 20 (Cochran 1977, pp. 132-134) ==")
    for par, c in cond.items():
        estado = "cumple" if c["cumple_todos_mayor_20"] else \
                 f"NO cumple: {c['estratos_con_n_h_menor_igual_20']}"
        print(f"   {par:14s} n_h min={c['n_h_min']:5d}  {estado}")

    SALIDA.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {SALIDA.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
