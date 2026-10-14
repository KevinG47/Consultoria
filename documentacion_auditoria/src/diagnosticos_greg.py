# -*- coding: utf-8 -*-
"""
diagnosticos_greg.py
====================

Diagnósticos de supuestos y calidad del modelo GREG, siguiendo la recomendación de
Hedlin et al. (2001): analizar **g-weights, residuos y diagnósticos de regresión**
antes de dar por buena una estimación asistida por modelo.

Produce:
  - data/memoria/diagnosticos_greg.json
  - data/memoria/eda/07..10*.png

Todo se implementa directamente (no hay statsmodels en el entorno):
  - Lilliefors por Monte Carlo para el KS con parámetros estimados
  - Breusch-Pagan y versión de White recortada
  - Levene y Bartlett por celdas del modelo
  - errores estándar robustos HC3 (sándwich)
  - g-weights, leverage y distancia de Cook

Uso:  python diagnosticos_greg.py
"""

from __future__ import annotations

import io
import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from estimadores_longitudinal import (  # noqa: E402
    AUX_EDAD, AUX_RET, CONV_ORDEN, IDS, cargar, matriz_aux)

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
DIR_EDA = DOC / "data" / "memoria" / "eda"
SALIDA = DOC / "data" / "memoria" / "diagnosticos_greg.json"
SEMILLA = 2026

AZUL, DORADO, VERDE, ROJO, GRIS = "#1E3780", "#B7871E", "#15803D", "#B91C1C", "#64748B"
FUENTE = ("Fuente: base completa de investigadores reconocidos (datos.gov.co, "
          "bqtm-4y2h). Muestra MAS n = 2 224, semilla 2026.")
plt.rcParams.update({"figure.dpi": 130, "font.size": 10, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.spines.top": False,
                     "axes.spines.right": False})


def _fuente(ax):
    ax.figure.text(0.01, 0.005, FUENTE, fontsize=6.4, color="#555555",
                   ha="left", va="bottom")


# --------------------------------------------------------------------------
# 1. Normalidad
# --------------------------------------------------------------------------
def ks_normal(x: np.ndarray) -> float:
    """Estadístico KS contra la normal con media y desviación estimadas."""
    z = np.sort((x - x.mean()) / x.std(ddof=1))
    n = len(z)
    ecdf = np.arange(1, n + 1) / n
    prev = np.concatenate([[0.0], ecdf[:-1]])
    cdf = stats.norm.cdf(z)
    return float(np.max(np.maximum(np.abs(ecdf - cdf), np.abs(prev - cdf))))


def lilliefors(x: np.ndarray, n_sim: int = 500, semilla: int = SEMILLA) -> dict:
    """
    KS con parámetros estimados (Lilliefors) por Monte Carlo.

    `kstest` con media y desviación estimadas de los propios datos NO es válido:
    los parámetros se ajustan a la muestra, lo que hace que el estadístico sea
    menor de lo que sería bajo la hipótesis nula y el p-valor quede inflado. La
    corrección de Lilliefors obtiene la distribución nula por simulación.
    """
    D = ks_normal(x)
    rng = np.random.default_rng(semilla)
    n = len(x)
    sims = np.empty(n_sim)
    for i in range(n_sim):
        sims[i] = ks_normal(rng.standard_normal(n))
    return {"estadistico_D": D, "p_valor_montecarlo": float((sims >= D).mean()),
            "n_simulaciones": n_sim,
            "D_critico_5pct": float(np.quantile(sims, 0.95))}


def diagnostico_normalidad(x: np.ndarray, etiqueta: str) -> dict:
    x = np.asarray(x, dtype=float)
    n = len(x)
    sk = float(stats.skew(x, bias=False))
    ku = float(stats.kurtosis(x, fisher=True, bias=False))   # exceso de curtosis
    out = {"etiqueta": etiqueta, "n": n, "media": float(x.mean()),
           "desv": float(x.std(ddof=1)), "asimetria": sk, "curtosis_exceso": ku,
           "min": float(x.min()), "max": float(x.max())}
    if n <= 5000:
        w, p = stats.shapiro(x)
        out["shapiro"] = {"W": float(w), "p_valor": float(p),
                          "aplica": True, "n": n}
    else:
        sub = np.random.default_rng(SEMILLA).choice(x, 5000, replace=False)
        w, p = stats.shapiro(sub)
        out["shapiro"] = {"W": float(w), "p_valor": float(p), "aplica": True,
                          "n": 5000,
                          "nota": (f"Shapiro-Wilk no es fiable con n={n}: se aplica "
                                   f"sobre una submuestra aleatoria de 5000")}
    out["ks_ingenua"] = {"estadistico_D": ks_normal(x),
                         "nota": ("KS con parámetros estimados de los datos: "
                                  "p-valor no válido (conservador), se reporta solo "
                                  "como referencia")}
    out["lilliefors"] = lilliefors(x, n_sim=500 if n <= 5000 else 300)
    out["lectura"] = {
        "asimetria_interpretacion": (
            "aceptable (|asimetría| < 1)" if abs(sk) < 1 else
            "moderada (1 ≤ |asimetría| < 2)" if abs(sk) < 2 else
            "severa (|asimetría| ≥ 2)"),
        "curtosis_interpretacion": (
            "aceptable (|curtosis| < 7)" if abs(ku) < 7 else
            "problemática (|curtosis| ≥ 7)"),
    }
    return out


# --------------------------------------------------------------------------
# 2. Heterocedasticidad
# --------------------------------------------------------------------------
def breusch_pagan(e: np.ndarray, X: np.ndarray) -> dict:
    """LM = n·R² de regresar e² sobre las auxiliares (Koenker studentizado)."""
    n = len(e)
    u2 = e ** 2
    Xb = np.hstack([np.ones((n, 1)), X])
    beta, *_ = np.linalg.lstsq(Xb, u2, rcond=None)
    ajust = Xb @ beta
    ss_tot = float(((u2 - u2.mean()) ** 2).sum())
    r2 = 1 - float(((u2 - ajust) ** 2).sum()) / ss_tot if ss_tot else 0.0
    lm = n * r2
    gl = Xb.shape[1] - 1
    return {"LM": float(lm), "R2": float(r2), "gl": int(gl),
            "p_valor": float(stats.chi2.sf(lm, gl))}


def white_recortada(e: np.ndarray, X: np.ndarray) -> dict:
    """
    Versión de White sobre los términos no redundantes.

    Con regresores SOLO dicotómicos el test de White es degenerado: el cuadrado de
    una dummy es la propia dummy y el producto cruzado de dos dummies es otra
    dummy, así que los términos adicionales son colineales con los niveles y la
    matriz de diseño queda singular. Se construyen únicamente los productos
    cruzados distintos (no los cuadrados) y se reporta la limitación.
    """
    n, k = X.shape
    terminos = [X]
    cruces = []
    for i in range(k):
        for j in range(i + 1, k):
            if not np.array_equal(X[:, i], X[:, j]):
                cruces.append((X[:, i] * X[:, j]).reshape(-1, 1))
    if cruces:
        terminos.append(np.hstack(cruces))
    Xw = np.hstack([np.ones((n, 1))] + terminos)
    u2 = e ** 2
    beta, *_ = np.linalg.lstsq(Xw, u2, rcond=None)
    ajust = Xw @ beta
    ss_tot = float(((u2 - u2.mean()) ** 2).sum())
    r2 = 1 - float(((u2 - ajust) ** 2).sum()) / ss_tot if ss_tot else 0.0
    lm = n * r2
    gl = Xw.shape[1] - 1
    return {"LM": float(lm), "R2": float(r2), "gl": int(gl),
            "p_valor": float(stats.chi2.sf(lm, gl)),
            "terminos_cruzados": len(cruces),
            "nota": ("degenerado con regresores solo dicotómicos: los cuadrados "
                     "coinciden con las dummies y se omiten; se usan solo los "
                     "productos cruzados distintos")}


def homocedasticidad_por_celdas(e: np.ndarray, etiquetas: np.ndarray) -> dict:
    """Levene y Bartlett entre las celdas del modelo (el test apropiado aquí)."""
    grupos = [e[etiquetas == g] for g in np.unique(etiquetas)]
    grupos = [g for g in grupos if len(g) >= 5]
    if len(grupos) < 2:
        return {"aplica": False}
    lev = stats.levene(*grupos, center="median")
    bar = stats.bartlett(*grupos) if min(len(g) for g in grupos) > 2 else None
    return {"aplica": True, "n_celdas": len(grupos),
            "levene": {"estadistico": float(lev.statistic), "p_valor": float(lev.pvalue)},
            "bartlett": ({"estadistico": float(bar.statistic),
                          "p_valor": float(bar.pvalue)} if bar else None),
            "varianza_min": float(min(np.var(g, ddof=1) for g in grupos)),
            "varianza_max": float(max(np.var(g, ddof=1) for g in grupos)),
            "celda_mas_pequena": int(min(len(g) for g in grupos))}


def errores_robustos(e: np.ndarray, X: np.ndarray) -> dict:
    """Compara la varianza clásica con HC3 (sándwich) para el coeficiente de interés."""
    n, k = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    # leverage
    h = np.einsum("ij,jk,ik->i", X, XtX_inv, X)
    omega = (e / np.clip(1 - h, 1e-8, None)) ** 2
    V_hc3 = XtX_inv @ (X.T @ (omega[:, None] * X)) @ XtX_inv
    s2 = float((e ** 2).sum() / (n - k))
    V_clas = s2 * XtX_inv
    return {"se_clasico_media": float(np.sqrt(V_clas[0, 0])),
            "se_hc3_media": float(np.sqrt(V_hc3[0, 0])),
            "ratio_hc3_clasico": float(np.sqrt(V_hc3[0, 0] / V_clas[0, 0])),
            "leverage_medio": float(h.mean()), "leverage_max": float(h.max())}


# --------------------------------------------------------------------------
# 3. g-weights e influencia
# --------------------------------------------------------------------------
def g_weights(X_s: np.ndarray, X_U: np.ndarray, N: int) -> tuple:
    """
    Pesos implícitos del GREG: g_i = 1 + lambda' x_i, con
    lambda = (SUM_s w x x')^{-1} (X_U - X_hat_HT) y w_i = N/n.

    Propiedades que deben cumplirse y se comprueban: SUM_s w_i g_i x_i = X_U y,
    como el intercepto está entre las auxiliares, SUM_s w_i g_i = N.
    """
    n = X_s.shape[0]
    w = N / n
    Xs = np.hstack([np.ones((n, 1)), X_s])
    Xu = np.hstack([np.ones((len(X_U), 1)), X_U])
    X_U_tot = Xu.sum(axis=0)
    X_ht = w * Xs.sum(axis=0)
    M = w * (Xs.T @ Xs)
    # lstsq con rcond=None resuelve con precisión de máquina; pinv truncaría
    # valores singulares pequeños (M está mal condicionada con dummies) y los
    # totales auxiliares no se reproducirían.
    lam = np.linalg.lstsq(M, X_U_tot - X_ht, rcond=None)[0]
    return 1.0 + Xs @ lam, X_U_tot, X_ht, lam, w, float(np.linalg.cond(M))


def influencia(e: np.ndarray, X: np.ndarray, y: np.ndarray) -> dict:
    """Leverage, residuos estudentizados y distancia de Cook."""
    n, k = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    h = np.einsum("ij,jk,ik->i", X, XtX_inv, X)
    resid = y - X @ beta
    s2 = float((resid ** 2).sum() / (n - k))
    r_est = resid / np.sqrt(np.clip(s2 * (1 - h), 1e-12, None))
    cook = (r_est ** 2 / k) * (h / np.clip(1 - h, 1e-12, None))
    umbral_h = 2 * k / n
    umbral_cook = 4 / n
    return {"leverage": h, "residuo_estudentizado": r_est, "cook": cook,
            "beta": beta, "resid": resid, "s2": s2,
            "umbral_leverage": float(umbral_h),
            "umbral_cook": float(umbral_cook),
            "n_sobre_umbral_leverage": int((h > umbral_h).sum()),
            "n_sobre_umbral_cook": int((cook > umbral_cook).sum()),
            "cook_max": float(cook.max()),
            "leverage_max": float(h.max())}


def resumen_g(g: np.ndarray) -> dict:
    q = np.quantile(g, [0, .01, .05, .25, .5, .75, .95, .99, 1])
    return {"min": float(g.min()), "max": float(g.max()),
            "media": float(g.mean()),
            "cuantiles": {str(k): float(v) for k, v in
                          zip([0, 1, 5, 25, 50, 75, 95, 99, 100], q)},
            "n_sobre_5": int((g > 5).sum()), "n_sobre_10": int((g > 10).sum()),
            "pct_sobre_5": float(100 * (g > 5).mean()),
            "pct_sobre_10": float(100 * (g > 10).mean())}


def main() -> int:
    DIR_EDA.mkdir(parents=True, exist_ok=True)
    print("== Carga ==")
    df = cargar()
    ids = set(pd.read_csv(IDS, dtype=str, keep_default_na=False)["ID_PERSONA_PR"])
    ult = df.sort_values("conv_i").groupby("ID_PERSONA_PR", observed=True).last()

    res: dict = {"fecha": datetime.now().isoformat(timespec="seconds"),
                 "semilla": SEMILLA,
                 "referencia": ("Hedlin et al. (2001) recomiendan analizar g-weights, "
                                "residuos y diagnósticos de regresión para verificar "
                                "que una estimación GREG es razonable.")}

    # ================= PARTE 1: normalidad de la edad =====================
    print("\n== Parte 1: normalidad de la edad ==")
    edad_U = pd.to_numeric(ult["EDAD_ANOS_PR"].str.replace(",", ".", regex=False),
                           errors="coerce")
    pop = ult.loc[edad_U.notna()]
    y_U = edad_U[edad_U.notna()].to_numpy()
    samp = pop.loc[pop.index.isin(ids)]
    y_s = pd.to_numeric(samp["EDAD_ANOS_PR"].str.replace(",", ".", regex=False),
                        errors="coerce").to_numpy()
    res["normalidad"] = {
        "variable": "EDAD_ANOS_PR (única variable continua del análisis)",
        "censo": diagnostico_normalidad(y_U, "Edad (censo)"),
        "muestra": diagnostico_normalidad(y_s, "Edad (muestra MAS)"),
    }
    for k in ("censo", "muestra"):
        d = res["normalidad"][k]
        print(f"   {d['etiqueta']:22s} n={d['n']:6d} asim={d['asimetria']:+.3f} "
              f"curt={d['curtosis_exceso']:+.3f} shapiro W={d['shapiro']['W']:.4f} "
              f"p={d['shapiro']['p_valor']:.2e} Lilliefors p={d['lilliefors']['p_valor_montecarlo']:.4f}")

    # ================= PARTE 2-3: modelo de EDAD =========================
    print("\n== Partes 2-3: modelo GREG de la edad ==")
    X_U, X_s = matriz_aux(pop, samp, AUX_EDAD)
    Xs = np.hstack([np.ones((len(X_s), 1)), X_s])
    beta, *_ = np.linalg.lstsq(Xs, y_s, rcond=None)
    e = y_s - Xs @ beta
    normal_res = diagnostico_normalidad(e, "Residuos del modelo de edad")
    bp = breusch_pagan(e, X_s)
    wh = white_recortada(e, X_s)
    celdas = (samp[AUX_EDAD].astype(str).agg("|".join, axis=1)).to_numpy()
    hc = homocedasticidad_por_celdas(e, celdas)
    rob = errores_robustos(e, Xs)
    inf = influencia(e, Xs, y_s)
    g, X_U_tot, X_ht, lam, w, cond_M = g_weights(X_s, X_U, len(pop))
    rg = resumen_g(g)
    # ¿Qué columnas auxiliares NO se pueden reproducir? Una categoría con cero
    # observaciones en la muestra no es calibrable: su total poblacional no puede
    # representarse y aparece como desvío exacto igual a su recuento.
    nombres_aux = (["(intercepto)"]
                   + [f"{c}={v}" for c, v in zip(AUX_EDAD * 99,
                                                 [])] if False else
                   [f"col_{i}" for i in range(Xs.shape[1])])
    desv_col = (w * g) @ Xs - X_U_tot
    cols_no_calibrables = [{"columna": int(i), "desvio": float(desv_col[i]),
                            "total_poblacional": float(X_U_tot[i]),
                            "n_muestra_col": int((Xs[:, i] > 0).sum())}
                           for i in np.where(np.abs(desv_col) > 1e-6)[0]]
    res["modelo_edad"] = {
        "auxiliares": AUX_EDAD, "n_modelo": int(len(y_s)), "n_parametros": int(Xs.shape[1]),
        "normalidad_residuos": normal_res,
        "breusch_pagan": bp, "white_recortada": wh, "homocedasticidad_celdas": hc,
        "errores_robustos": rob,
        "influencia": {k: (v.tolist() if isinstance(v, np.ndarray) else v)
                       for k, v in inf.items()},
        "g_weights": rg,
        "g_weights_verificacion": {
            "suma_wg_sobre_N": float((w * g).sum() / len(pop)),
            "max_desvio_totales_auxiliares": float(
                np.max(np.abs((w * g) @ Xs - X_U_tot))),
            "numero_condicion_M": cond_M,
            "columnas_no_calibrables": cols_no_calibrables,
            "nota_no_calibrable": (
                "Una categoría auxiliar con CERO observaciones en la muestra no es "
                "calibrable: el GREG no puede reproducir su total poblacional porque "
                "ninguna observación lo representa. No es un error de cálculo sino un "
                "límite del método, y aquí afecta a las categorías de género "
                "Intersexual y No disponible, ausentes de la muestra (los totales "
                "exactos de cada columna están en `columnas_no_calibrables`)."),
        },
    }
    print(f"   residuos: asim={normal_res['asimetria']:+.3f} "
          f"curt={normal_res['curtosis_exceso']:+.3f} "
          f"Shapiro p={normal_res['shapiro']['p_valor']:.2e} "
          f"Lilliefors p={normal_res['lilliefors']['p_valor_montecarlo']:.4f}")
    print(f"   Breusch-Pagan  LM={bp['LM']:.2f} gl={bp['gl']} p={bp['p_valor']:.3e}")
    print(f"   White (recortada) LM={wh['LM']:.2f} gl={wh['gl']} p={wh['p_valor']:.3e} "
          f"({wh['terminos_cruzados']} cruces)")
    if hc.get("aplica"):
        print(f"   Levene p={hc['levene']['p_valor']:.3e} | Bartlett "
              f"p={hc['bartlett']['p_valor']:.3e} | varianza max/min = "
              f"{hc['varianza_max']/hc['varianza_min']:.2f}")
    print(f"   SE clásico={rob['se_clasico_media']:.4f} vs HC3={rob['se_hc3_media']:.4f} "
          f"(ratio {rob['ratio_hc3_clasico']:.3f})")
    print(f"   g-weights: min={rg['min']:.3f} max={rg['max']:.3f} "
          f">5: {rg['n_sobre_5']} >10: {rg['n_sobre_10']}")
    print(f"   Cook: max={inf['cook_max']:.4f} (umbral {inf['umbral_cook']:.4f}) "
          f"sobre umbral: {inf['n_sobre_umbral_cook']} | leverage sobre umbral: "
          f"{inf['n_sobre_umbral_leverage']}")
    print(f"   número de condición de M = {cond_M:.3e}")
    print(f"   verificación: suma(w·g)/N = "
          f"{res['modelo_edad']['g_weights_verificacion']['suma_wg_sobre_N']:.6f} | "
          f"desvío en totales auxiliares = "
          f"{res['modelo_edad']['g_weights_verificacion']['max_desvio_totales_auxiliares']:.2e}")

    # ---- impacto de las observaciones influyentes sobre el estimador GREG
    orden = np.argsort(-g)
    for k in (0, 5, 10, 25):
        if k and k >= len(orden):
            continue
        quitar = orden[:k] if k else np.array([], dtype=int)
        keep = np.setdiff1d(np.arange(len(y_s)), quitar)
        if len(keep) < 30:
            continue
        gk = g_weights(X_s[keep], X_U, len(pop))[0]
        # estimador de diferencia con el modelo saturado en el subconjunto
        Xs_k = np.hstack([np.ones((len(keep), 1)), X_s[keep]])
        b_k, *_ = np.linalg.lstsq(Xs_k, y_s[keep], rcond=None)
        pred_U = np.hstack([np.ones((len(X_U), 1)), X_U]) @ b_k
        est_k = float(pred_U.mean() + np.mean(y_s[keep] - Xs_k @ b_k))
        res.setdefault("impacto_influyentes", {})[f"sin_los_{k}_con_mayor_g"] = {
            "estimador": est_k,
            "g_max_restante": float(gk.max()),
            "cambio_vs_completo_pp": None,
        }
    # estimador completo con el mismo procedimiento, para comparar
    pred_U = np.hstack([np.ones((len(X_U), 1)), X_U]) @ beta
    est_full = float(pred_U.mean() + np.mean(y_s - Xs @ beta))
    for k, v in res["impacto_influyentes"].items():
        v["cambio_vs_completo_pp"] = v["estimador"] - est_full
    res["impacto_influyentes"]["completo"] = {
        "estimador": est_full, "g_max_restante": float(g.max()),
        "cambio_vs_completo_pp": 0.0}
    print("\n   impacto de quitar las observaciones con mayor g:")
    for k, v in res["impacto_influyentes"].items():
        print(f"      {k:28s} estimador={v['estimador']:.4f} "
              f"cambio={v['cambio_vs_completo_pp']:+.5f}")

    # ================= modelo de RETENCIÓN (probabilidad lineal) ==========
    print("\n== Modelo de retención 2019→2021 (probabilidad lineal) ==")
    presentes = {c: set(df.loc[df["conv_i"] == c, "ID_PERSONA_PR"]) for c in CONV_ORDEN}
    p20 = df.loc[df["conv_i"] == 20].drop_duplicates("ID_PERSONA_PR").set_index("ID_PERSONA_PR")
    yU_r = np.array([int(p in presentes[21]) for p in p20.index], dtype=float)
    samp_r = p20.loc[p20.index.isin(ids)]
    y_s_r = np.array([int(p in presentes[21]) for p in samp_r.index], dtype=float)
    X_U_r, X_s_r = matriz_aux(p20, samp_r, AUX_RET)
    Xs_r = np.hstack([np.ones((len(X_s_r), 1)), X_s_r])
    b_r, *_ = np.linalg.lstsq(Xs_r, y_s_r, rcond=None)
    e_r = y_s_r - Xs_r @ b_r
    bp_r = breusch_pagan(e_r, X_s_r)
    inf_r = influencia(e_r, Xs_r, y_s_r)
    g_r = g_weights(X_s_r, X_U_r, len(p20))[0]
    res["modelo_retencion_lpm"] = {
        "auxiliares": AUX_RET, "n_modelo": int(len(y_s_r)),
        "nota": ("la heterocedasticidad es ESTRUCTURAL en una variable binaria "
                 "(Var(y)=p(1-p) depende de p), no un defecto del modelo; por eso "
                 "el GREG de la retención se implementó con un modelo logístico"),
        "breusch_pagan": bp_r,
        "p_hat_rango": [float((Xs_r @ b_r).min()), float((Xs_r @ b_r).max())],
        "influencia": {k: (v.tolist() if isinstance(v, np.ndarray) else v)
                       for k, v in inf_r.items()},
        "g_weights": resumen_g(g_r),
    }
    print(f"   BP LM={bp_r['LM']:.2f} p={bp_r['p_valor']:.3e} (heterocedasticidad "
          f"estructural: y binaria)")
    print(f"   p̂ ajustada entre {res['modelo_retencion_lpm']['p_hat_rango'][0]:.3f} y "
          f"{res['modelo_retencion_lpm']['p_hat_rango'][1]:.3f}")
    print(f"   g-weights: min={res['modelo_retencion_lpm']['g_weights']['min']:.3f} "
          f"max={res['modelo_retencion_lpm']['g_weights']['max']:.3f} "
          f">5: {res['modelo_retencion_lpm']['g_weights']['n_sobre_5']}")

    # =============================== GRÁFICAS =============================
    print("\n== Gráficas ==")
    # 07 Q-Q
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 5.0))
    for ax, x, t in [(axes[0], y_U, f"Censo (n = {len(y_U)})"),
                     (axes[1], y_s, f"Muestra MAS (n = {len(y_s)})")]:
        (osm, osr), (slope, inter, _) = stats.probplot(x, dist="norm")
        ax.scatter(osm, osr, s=5, color=AZUL, alpha=0.45, edgecolor="none")
        ax.plot(osm, slope * osm + inter, color=ROJO, linewidth=1.6)
        ax.set_title(f"Q-Q normal — Edad, {t}", fontsize=10)
        ax.set_xlabel("cuantiles teóricos (normal estándar)")
        ax.set_ylabel("cuantiles observados (años)")
    axes[0].annotate("cola derecha:\nregistros con edad > 100",
                     xy=(3.6, 130), xytext=(1.4, 500), fontsize=8,
                     arrowprops=dict(arrowstyle="->", color=GRIS))
    fig.suptitle("Normalidad de la edad: la asimetría positiva y el exceso de curtosis "
                 "están en la cola derecha", fontsize=10.5)
    _fuente(axes[0])
    fig.tight_layout(rect=(0, 0.035, 1, 0.93))
    fig.savefig(DIR_EDA / "07_qq_edad.png", bbox_inches="tight")
    plt.close(fig)

    # 08 residuos vs ajustados + scale-location
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.0))
    aj = Xs @ beta
    axes[0].scatter(aj, e, s=6, color=AZUL, alpha=0.4, edgecolor="none")
    axes[0].axhline(0, color=ROJO, linewidth=1.4)
    axes[0].set_xlabel("edad ajustada por el modelo (años)")
    axes[0].set_ylabel("residuo (años)")
    axes[0].set_title("Residuos vs valores ajustados — modelo de edad", fontsize=10)
    raiz = np.sqrt(np.abs(inf["residuo_estudentizado"]))
    axes[1].scatter(aj, raiz, s=6, color=DORADO, alpha=0.4, edgecolor="none")
    med = pd.Series(raiz).groupby(pd.qcut(aj, 12, duplicates="drop"), observed=True).mean()
    centros = [iv.mid for iv in med.index]
    axes[1].plot(centros, med.values, color=ROJO, linewidth=2, marker="o",
                 markersize=4, label="media por doceavo")
    axes[1].set_xlabel("edad ajustada por el modelo (años)")
    axes[1].set_ylabel("√|residuo estudentizado|")
    axes[1].set_title("Scale-location: ¿la dispersión cambia con el nivel?", fontsize=10)
    axes[1].legend(frameon=False, fontsize=8)
    fig.suptitle(f"Breusch-Pagan LM = {bp['LM']:.1f} (gl = {bp['gl']}, "
                 f"p = {bp['p_valor']:.2e}) · Levene entre celdas p = "
                 f"{hc['levene']['p_valor']:.2e}", fontsize=10.5)
    _fuente(axes[0])
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    fig.savefig(DIR_EDA / "08_residuos_vs_ajustados.png", bbox_inches="tight")
    plt.close(fig)

    # 09 g-weights
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.0))
    axes[0].hist(g, bins=60, color=VERDE, edgecolor="white", linewidth=0.3)
    for umbral, color in ((5, DORADO), (10, ROJO)):
        axes[0].axvline(umbral, color=color, linestyle="--", linewidth=1.5,
                        label=f"g = {umbral} ({int((g > umbral).sum())} casos)")
    axes[0].set_xlabel("g-weight del GREG (modelo de edad)")
    axes[0].set_ylabel("personas")
    axes[0].set_title("Distribución de los g-weights", fontsize=10)
    axes[0].legend(frameon=False, fontsize=8)
    axes[1].boxplot([g, g_r], vert=True, widths=0.5, patch_artist=True,
                    tick_labels=["Edad\n(género, área, región)",
                                 "Retención\n(cat., género, área, depto.)"],
                    boxprops=dict(facecolor="#D6E0F2", color=AZUL),
                    medianprops=dict(color=DORADO, linewidth=2),
                    flierprops=dict(marker="o", markersize=3, alpha=0.5,
                                    markerfacecolor=ROJO, markeredgecolor=ROJO))
    axes[1].axhline(1, color=GRIS, linewidth=1.2)
    axes[1].set_ylabel("g-weight")
    axes[1].set_title("Comparación entre los dos modelos", fontsize=10)
    fig.suptitle("Pesos implícitos del GREG: un g-weight grande indica que unas pocas "
                 "observaciones cargan la corrección del modelo", fontsize=10.5)
    _fuente(axes[0])
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    fig.savefig(DIR_EDA / "09_gweights.png", bbox_inches="tight")
    plt.close(fig)

    # 10 influencia
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.0))
    axes[0].scatter(aj, inf["cook"], s=6, color=AZUL, alpha=0.45, edgecolor="none")
    axes[0].axhline(inf["umbral_cook"], color=ROJO, linestyle="--", linewidth=1.4,
                    label=f"umbral 4/n = {inf['umbral_cook']:.4f}")
    axes[0].set_xlabel("edad ajustada (años)")
    axes[0].set_ylabel("distancia de Cook")
    axes[0].set_title("Distancia de Cook — modelo de edad", fontsize=10)
    axes[0].legend(frameon=False, fontsize=8)
    axes[1].scatter(inf["leverage"], inf["residuo_estudentizado"], s=6, color=DORADO,
                    alpha=0.45, edgecolor="none")
    axes[1].axvline(inf["umbral_leverage"], color=ROJO, linestyle="--", linewidth=1.4,
                    label=f"2k/n = {inf['umbral_leverage']:.4f}")
    axes[1].axhline(0, color=GRIS, linewidth=1.0)
    axes[1].set_xlabel("leverage (influencia potencial)")
    axes[1].set_ylabel("residuo estudentizado")
    axes[1].set_title("Leverage vs residuo estudentizado", fontsize=10)
    axes[1].legend(frameon=False, fontsize=8)
    fig.suptitle(f"Observaciones influyentes: {inf['n_sobre_umbral_cook']} superan el "
                 f"umbral de Cook y {inf['n_sobre_umbral_leverage']} el de leverage",
                 fontsize=10.5)
    _fuente(axes[0])
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    fig.savefig(DIR_EDA / "10_influencia.png", bbox_inches="tight")
    plt.close(fig)

    for f in sorted(DIR_EDA.glob("*.png")):
        print(f"   {f.name}  ({f.stat().st_size/1024:.1f} KB)")

    SALIDA.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {SALIDA.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
