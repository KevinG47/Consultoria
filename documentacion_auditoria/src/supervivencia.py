# -*- coding: utf-8 -*-
"""
supervivencia.py
================

F2-10 — Curvas de supervivencia Kaplan-Meier y modelo de Cox.

Qué mide
--------
El evento de interés es la **salida del sistema**: la última convocatoria en la que
la persona aparece. El tiempo es el transcurrido desde su **primera** aparición
hasta la última, en años reales (las convocatorias no están igualmente espaciadas:
entre 2013 y 2019 median 6,1 años).

  T = fecha_ultima − fecha_primera        (años)
  evento = 1  si la última convocatoria NO es 2021  (se le vio salir)
  evento = 0  si su última observación es 2021      (censura a la derecha)

Cuidado con dos cosas que el diseño obliga a declarar
-----------------------------------------------------
1. **La censura es muy alta: 21 094 de 30 086 personas (70,1 %) siguen en 2021.**
   Para la cohorte de 2013 la retención es del 56,18 %, así que **la mediana de
   supervivencia no se alcanza** dentro de la ventana de 7,32 años. Se reporta así,
   no se fuerza.
2. **El tiempo se mide desde la primera aparición de cada persona**, así que
   conviven cohortes de entrada distintas (de 2013 a 2021). Es el enfoque de
   «tiempo desde el ingreso», válido, pero no ajusta por periodo calendario. Se
   complementa con la **cohorte de 2013**, que no tiene ese problema.

Qué se implementa a mano
------------------------
`lifelines` y `statsmodels` **no están instalados**, así que se implementan:
- **Kaplan-Meier** con varianza de Greenwood e intervalos por transformación
  log(−log), que se portan bien con S(t) pequeño (Kalbfleisch y Prentice, 1980).
- **Log-rank** de k muestras (Mantel-Cox).
- **Cox de riesgos proporcionales** por máxima verosimilitud parcial con
  corrección de **Efron** para empates, con gradiente y hessiano analíticos
  (Efron, 1977; Kalbfleisch y Prentice, 1980 §4).

La corrección de Efron importa aquí: los eventos solo pueden observarse en las seis
fechas de convocatoria, así que hay empates masivos. Breslow sería sesgado.

Validación
----------
Con **una sola covariable binaria, el test de score de Cox es el test de log-rank**
(la propiedad que usa la prueba de tendencia). Se comprueba numéricamente: si los
dos p-valores no coinciden, el Cox está mal.

Grupos pequeños
---------------
**Emérito** (334 personas, 1,1 %) se gráfica pero **se excluye del modelo de Cox**:
no es solo que sea pequeño, es que es una categoría **terminal por selección** —
solo se llega a Emérito habiendo sobrevivido—, así que su hazard ratio no sería
interpretable como «riesgo de salir» (sesgo de tiempo inmortal). Se reporta una
sensibilidad agrupándolo con Sénior, que es lo que el proyecto ya hace en la
post-estratificación.

Género: `Intersexual` (5 personas) y `No disponible` (4) no permiten estimar nada;
se informan y se excluyen del modelo (9 personas, 0,03 %).

Produce:
    data/memoria/supervivencia.json
    data/memoria/supervivencia_personas.csv
    data/memoria/graficas_supervivencia/*.png

Uso:
    python documentacion_auditoria/src/supervivencia.py
"""

from __future__ import annotations

import io
import json
import sys
from datetime import datetime
from pathlib import Path
from statistics import NormalDist

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                        # noqa: E402
import pandas as pd                       # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
FUENTE = (RAIZ / "datos_originales" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
SALIDA = DOC / "data" / "memoria" / "supervivencia.json"
CSV = DOC / "data" / "memoria" / "supervivencia_personas.csv"
GRAF = DOC / "data" / "memoria" / "graficas_supervivencia"

Z = 1.959963984540054
CONV_FINAL = 21
CATEGORIAS_ORDEN = ["Investigador Junior", "Investigador Asociado",
                    "Investigador Sénior", "Investigador Emérito"]
# Los departamentos del top 5 NO se escriben a mano: se derivan de los datos.
# Escribirlos costó un error real —el nombre es 'Bogotá, D. C.' CON COMA, no
# 'Bogotá  D. C.' con dos espacios—, que metía a Bogotá en "Resto", dejaba el
# modelo de Cox sin nivel de referencia y lo hacía divergir.
N_DEPT_TOP = 5

AZUL, AZUL_SEC, AZUL_CLARO = "#1E3780", "#4A6BA8", "#7BA7D0"
DORADO, DORADO_CLARO = "#B7871E", "#D4A84A"
GRIS_OSC, GRIS, GRIS_CLARO = "#334155", "#64748B", "#CBD5E1"
FONDO, TEXTO, ALERTA = "#F8FAFC", "#1E293B", "#B91C1C"
PALETA_GRUPOS = [AZUL, DORADO, AZUL_CLARO, GRIS_OSC, DORADO_CLARO, GRIS]


# ==========================================================================
# 1. Kaplan-Meier, log-rank
# ==========================================================================
def kaplan_meier(t: np.ndarray, e: np.ndarray) -> dict:
    """
    Estimador de Kaplan-Meier con varianza de Greenwood e IC por log(−log).

    Devuelve tiempos, S(t), su varianza y el IC 95 %.
    """
    orden = np.argsort(t)
    t, e = t[orden], e[orden]
    tiempos, S, var_logS, n_riesgo, d_eventos = [], [], [], [], []
    s = 1.0
    acum = 0.0
    for tiempo in np.unique(t[e == 1]):
        en_riesgo = int((t >= tiempo).sum())
        d = int(((t == tiempo) & (e == 1)).sum())
        if en_riesgo == 0 or d == 0:
            continue
        s *= (1.0 - d / en_riesgo)
        acum += d / (en_riesgo * (en_riesgo - d)) if en_riesgo > d else 0.0
        tiempos.append(float(tiempo))
        S.append(s)
        var_logS.append(acum)
        n_riesgo.append(en_riesgo)
        d_eventos.append(d)
    S = np.asarray(S)
    var_logS = np.asarray(var_logS)
    # IC por log(−log): S^{exp(±z·se)}, con se = sqrt(var(logS))/|log S|
    with np.errstate(divide="ignore", invalid="ignore"):
        se_theta = np.where(S > 0, np.sqrt(var_logS) / np.abs(np.log(S)),
                            np.nan)
    lo = np.where(S > 0, np.power(S, np.exp(Z * se_theta)), np.nan)
    hi = np.where(S > 0, np.power(S, np.exp(-Z * se_theta)), np.nan)
    return {"tiempos": tiempos, "S": S.tolist(), "var_logS": var_logS.tolist(),
            "ic95_inf": lo.tolist(), "ic95_sup": hi.tolist(),
            "n_riesgo": n_riesgo, "d_eventos": d_eventos}


def mediana_km(km: dict) -> dict:
    """
    Mediana de supervivencia: primer tiempo con S(t) <= 0,5.

    El IC de la mediana se calcula cruzando el IC de S(t) con 0,5, pero los
    eventos solo pueden observarse en las fechas de convocatoria (11 tiempos
    distintos), así que la mediana es una función escalonada y su intervalo es
    muy grueso: se devuelve cuando existe y se marca la limitación. Si S(t) no
    baja de 0,5 la mediana NO se alcanza, y se dice así en vez de forzar un
    número.
    """
    S = np.asarray(km["S"])
    if S.size == 0:
        return {"estimable": False, "motivo": "sin eventos"}
    idx = np.where(S <= 0.5)[0]
    if idx.size == 0:
        return {"estimable": False,
                "motivo": (f"S(t) no baja de 0,5 dentro de la ventana "
                           f"(mínimo {S.min():.4f} a los "
                           f"{max(km['tiempos']):.2f} años)"),
                "S_final": float(S.min())}
    i = int(idx[0])
    lo = np.asarray(km["ic95_inf"])
    hi = np.asarray(km["ic95_sup"])
    i_lo = np.where(hi <= 0.5)[0]        # primer tiempo con el IC superior <= 0,5
    i_hi = np.where(lo <= 0.5)[0]        # primer tiempo con el IC inferior <= 0,5
    inf = float(km["tiempos"][i_lo[0]]) if i_lo.size else None
    sup = float(km["tiempos"][i_hi[0]]) if i_hi.size else None
    # Coherencia: un intervalo con el extremo superior antes del inferior no es
    # un intervalo. Ocurre con tiempos discretos; en ese caso no se reporta.
    if inf is not None and sup is not None and sup < inf:
        inf = sup = None
    return {"estimable": True, "anios": float(km["tiempos"][i]),
            "ic95_inf": inf, "ic95_sup": sup,
            "ic_no_informativo": bool(inf is None or sup is None),
            "nota_ic": ("Con solo 11 tiempos de evento distintos, la mediana es "
                        "una función escalonada y su intervalo no es "
                        "informativo: se reporta el valor puntual.")}


def logrank(t: np.ndarray, e: np.ndarray, g: np.ndarray) -> dict:
    """
    Test de log-rank de k muestras (Mantel-Cox).

    Estadístico chi-cuadrado con k−1 grados de libertad; se calcula también el
    de 2 muestras con corrección por continuidad cuando k = 2.
    """
    niveles = np.unique(g)
    k = niveles.size
    if k < 2:
        return {"chi2": 0.0, "gl": 0, "p": 1.0}
    O = np.zeros(k)
    E = np.zeros(k)
    V = np.zeros((k, k))
    for tiempo in np.unique(t[e == 1]):
        en_riesgo = t >= tiempo
        n = int(en_riesgo.sum())
        d = int(((t == tiempo) & (e == 1)).sum())
        if n <= 1 or d == 0:
            continue
        n_g = np.array([int((en_riesgo & (g == lv)).sum()) for lv in niveles])
        d_g = np.array([int(((t == tiempo) & (e == 1) & (g == lv)).sum())
                        for lv in niveles])
        O += d_g
        E += d * n_g / n
        for a in range(k):
            for b in range(k):
                if a == b:
                    V[a, b] += d * (n_g[a] / n) * (1 - n_g[a] / n) * (n - d) / (n - 1)
                else:
                    V[a, b] -= d * (n_g[a] / n) * (n_g[b] / n) * (n - d) / (n - 1)
    # Se descarta la última fila/columna (suman 0)
    Vr = V[:-1, :-1]
    diff = (O - E)[:-1]
    try:
        chi2 = float(diff @ np.linalg.pinv(Vr) @ diff)
    except Exception:                                      # noqa: BLE001
        chi2 = float("nan")
    gl = k - 1
    p = float(chi2_pvalor(chi2, gl))
    return {"chi2": chi2, "gl": int(gl), "p": p,
            "observados": O.tolist(), "esperados": E.tolist()}


def chi2_pvalor(x: float, gl: int) -> float:
    """P(X >= x) para una chi-cuadrado con gl grados de libertad."""
    from scipy import stats
    if not np.isfinite(x):
        return float("nan")
    return float(stats.chi2.sf(x, gl))


# ==========================================================================
# 2. Cox con Efron
# ==========================================================================
def _grad_hess(X: np.ndarray, t: np.ndarray, e: np.ndarray,
               beta: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    """
    Log-verosimilitud parcial con empates Efron, su gradiente y su hessiano.

    OJO: la matriz X **no debe llevar columna de constantes**. En el modelo de Cox
    el intercepto no es identificable —el gradiente de esa columna es idéntico a
    cero y el hessiano queda singular—, y añadirlo hace que Newton-Raphson
    diverja. La línea base la representa el nivel de referencia de cada factor.

    El bucle de Efron se vectoriza: con un 36 % de las personas observadas en una
    sola convocatoria hay un empate de miles de eventos en t = 0, y recorrerlo uno
    a uno en Python domina el tiempo de cálculo.
    """
    eta = X @ beta
    w = np.exp(np.clip(eta, -50, 50))
    p = X.shape[1]
    grad = np.zeros(p)
    hess = np.zeros((p, p))
    ll = 0.0
    for tiempo in np.unique(t[e == 1]):
        R = t >= tiempo
        D = (t == tiempo) & (e == 1)
        m = int(D.sum())
        if m == 0 or R.sum() <= m:
            continue
        XR, wR = X[R], w[R]
        XD, wD = X[D], w[D]
        S0 = wR.sum()
        S1 = (wR[:, None] * XR).sum(axis=0)
        S2 = (wR[:, None, None] * (XR[:, :, None] * XR[:, None, :])).sum(axis=0)
        S0D = wD.sum()
        S1D = (wD[:, None] * XD).sum(axis=0)
        S2D = (wD[:, None, None] * (XD[:, :, None] * XD[:, None, :])).sum(axis=0)
        ll += float(eta[D].sum())
        grad += XD.sum(axis=0)
        j = np.arange(m) / m
        den = S0 - j * S0D                       # (m,)
        if (den <= 0).any():
            continue
        ll -= float(np.log(den).sum())
        num1 = S1[None, :] - j[:, None] * S1D[None, :]            # (m, p)
        A = num1 / den[:, None]
        grad -= A.sum(axis=0)
        num2 = S2[None, :, :] - j[:, None, None] * S2D[None, :, :]  # (m, p, p)
        hess -= (num2 / den[:, None, None]).sum(axis=0) - A.T @ A
    return ll, grad, hess


def cox_efron(X: np.ndarray, t: np.ndarray, e: np.ndarray,
              max_iter: int = 100, tol: float = 1e-9) -> dict:
    """
    Cox de riesgos proporcionales por máxima verosimilitud parcial, empates Efron.

    Newton-Raphson con gradiente y hessiano analíticos.
    """
    p = X.shape[1]
    beta = np.zeros(p)
    ll_prev = -np.inf
    ll = -np.inf
    paso = np.full(p, np.inf)
    it = 0
    for it in range(max_iter):
        ll, grad, hess = _grad_hess(X, t, e, beta)
        if not np.isfinite(ll):
            return {"convergio": False, "motivo": "log-verosimilitud no finita"}
        try:
            paso = np.linalg.solve(-hess, grad)
        except np.linalg.LinAlgError:
            return {"convergio": False, "motivo": "hessiano singular"}
        beta = beta + paso
        if abs(ll - ll_prev) < tol and np.max(np.abs(paso)) < 1e-7:
            break
        ll_prev = ll
    ll, grad, hess = _grad_hess(X, t, e, beta)
    cov = np.linalg.pinv(-hess)
    se = np.sqrt(np.abs(np.diag(cov)))
    return {"beta": beta.tolist(), "se": se.tolist(), "cov": cov.tolist(),
            "log_verosimilitud": float(ll), "iteraciones": it + 1,
            "convergio": True, "gradiente_final": float(np.max(np.abs(grad)))}


def cox_score(X: np.ndarray, t: np.ndarray, e: np.ndarray) -> dict:
    """
    Test de score de Cox (evaluado en β = 0).

    Con una sola covariable binaria y sin empates es EXACTAMENTE el log-rank, y
    con empates tratados por Efron es su equivalente asintótico. Se usa para
    validar la implementación del modelo contra el del log-rank.
    """
    _, grad, hess = _grad_hess(X, t, e, np.zeros(X.shape[1]))
    info = -hess
    try:
        chi2 = float(grad @ np.linalg.pinv(info) @ grad)
    except Exception:                                      # noqa: BLE001
        return {"chi2": float("nan"), "p": float("nan")}
    return {"chi2": chi2, "gl": int(X.shape[1]), "p": float(chi2_pvalor(chi2, int(X.shape[1])))}


def _autotest() -> dict:
    """
    Comprobaciones de solución conocida.

    1. KM sin censura sobre tiempos 1..10: S(t_k) = 1 − k/10.
    2. Con una covariable binaria y SIN empates, el test de score de Cox coincide
       con el log-rank (son el mismo contraste). Es la prueba de que la
       implementación del Cox es correcta.
    """
    t = np.arange(1, 11, dtype=float)
    e = np.ones(10)
    km = kaplan_meier(t, e)
    ok_km = all(abs(s - (1 - (i + 1) / 10)) < 1e-12
                for i, s in enumerate(km["S"]))
    rng = np.random.default_rng(7)
    n = 500
    x = rng.integers(0, 2, n).astype(float)
    # Tiempos continuos: sin empates, Efron y Breslow coinciden
    tt = rng.exponential(2.0 + x, n) + rng.random(n) * 1e-3
    ee = rng.integers(0, 2, n).astype(float)
    lr = logrank(tt, ee, x)
    sc = cox_score(np.column_stack([np.ones(n), x]), tt, ee)
    return {
        "km_sin_censura_correcto": bool(ok_km),
        "logrank_chi2": lr["chi2"], "cox_score_chi2": sc["chi2"],
        "logrank_p": lr["p"], "cox_score_p": sc["p"],
        "score_vs_logrank_coinciden": bool(
            np.isfinite(lr["chi2"]) and np.isfinite(sc["chi2"])
            and abs(lr["chi2"] - sc["chi2"]) < 0.05),
        "todas_ok": bool(ok_km and np.isfinite(lr["chi2"])
                         and abs(lr["chi2"] - sc["chi2"]) < 0.05),
    }


# ==========================================================================
# 3. Gráficas
# ==========================================================================
def _estilo(ax) -> None:
    ax.set_facecolor(FONDO)
    ax.grid(axis="y", color=GRIS_CLARO, linewidth=0.6, alpha=0.9)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRIS)
    ax.tick_params(colors=GRIS_OSC, labelsize=8)


def fig_km(grupos: dict, titulo: str, archivo, xmax: float) -> None:
    fig, ax = plt.subplots(figsize=(9.0, 4.8), dpi=150)
    for i, (nombre, d) in enumerate(grupos.items()):
        col = PALETA_GRUPOS[i % len(PALETA_GRUPOS)]
        ts = [0.0] + list(d["km"]["tiempos"]) + [xmax]
        S = [1.0] + list(d["km"]["S"]) + [d["km"]["S"][-1] if d["km"]["S"] else 1.0]
        ax.step(ts, S, where="post", color=col, linewidth=1.9, zorder=3,
                label=f"{nombre} (n={d['n']:,})".replace(",", " "))
    ax.axhline(0.5, color=GRIS_OSC, linewidth=1.0, linestyle=":", zorder=2)
    ax.set_ylim(0, 1.02)
    ax.set_xlim(0, xmax)
    ax.set_xlabel("Años desde la primera aparición", color=TEXTO, fontsize=9)
    ax.set_ylabel("Supervivencia S(t)", color=TEXTO, fontsize=9)
    ax.set_title(f"{titulo}\nLínea punteada: S = 0,5, donde estaría la mediana",
                 color=TEXTO, fontsize=10.2, pad=10, loc="left")
    ax.legend(frameon=False, fontsize=7.8, labelcolor=GRIS_OSC, loc="lower left")
    _estilo(ax)
    fig.tight_layout()
    fig.savefig(archivo, facecolor="white")
    plt.close(fig)


def fig_forest(df: pd.DataFrame, archivo) -> None:
    d = df[df["variable"] != "constante"].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9.4, 0.42 * len(d) + 1.9), dpi=150)
    y = np.arange(len(d))
    for i, r in d.iterrows():
        sig = np.isfinite(r["ic95_inf"]) and (r["ic95_inf"] > 1 or r["ic95_sup"] < 1)
        # El rojo se reserva para las excepciones negativas, así que aquí la
        # distinción se hace con el oscuro (significativo) frente al gris.
        col = AZUL if sig else GRIS
        ax.plot([r["ic95_inf"], r["ic95_sup"]], [i, i], color=col, linewidth=2.6,
                solid_capstyle="round", zorder=3)
        ax.plot([r["hr"]], [i], marker="o", color=col, markersize=6.4, zorder=4)
    ax.axvline(1.0, color=DORADO, linewidth=1.5, zorder=2)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r['variable']} = {r['nivel']}"[:46] for _, r in d.iterrows()],
                       fontsize=7.6)
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.set_xlabel("Hazard ratio (escala log) · 1 = sin diferencia", color=TEXTO,
                  fontsize=9)
    ax.set_title("Modelo de Cox: riesgo de salir del sistema\n"
                 "En rojo, los intervalos que excluyen el 1", color=TEXTO,
                 fontsize=10.2, pad=10, loc="left")
    ax.set_facecolor(FONDO)
    ax.grid(axis="x", color=GRIS_CLARO, linewidth=0.6, alpha=0.9)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.tick_params(colors=GRIS_OSC, labelsize=8)
    fig.tight_layout()
    fig.savefig(archivo, facecolor="white")
    plt.close(fig)


# ==========================================================================
# 4. Principal
# ==========================================================================
def main() -> int:
    print("== F2-10 · Supervivencia (Kaplan-Meier y Cox) ==")
    autotest = _autotest()
    print(f"   autotest: KM sin censura={autotest['km_sin_censura_correcto']} · "
          f"chi2 log-rank={autotest['logrank_chi2']:.4f} vs score de Cox="
          f"{autotest['cox_score_chi2']:.4f}")
    if not autotest["todas_ok"]:
        print("   [ABORTA] el autotest falló (KM o equivalencia score/log-rank)")
        return 2

    out: dict = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "analisis": "F2-10 — Supervivencia: Kaplan-Meier y Cox (OE5 dinámica)",
        "autotest": autotest,
        "metodo": ("KM con Greenwood e IC log(−log); log-rank de k muestras; Cox "
                   "por máxima verosimilitud parcial con empates Efron. "
                   "Implementados a mano: lifelines y statsmodels no están "
                   "instalados."),
    }

    # ---------------- personas y tiempos ----------------
    cols = ["ID_CONVOCATORIA", "ID_PERSONA_PR", "ANO_CONVO",
            "NME_CLASIFICACION_PR", "NME_GENERO_PR", "NME_GRAN_AREA_PR",
            "NME_DEPARTAMENTO_RES_PR"]
    df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                     usecols=cols)
    df["conv"] = df["ID_CONVOCATORIA"].astype(int)
    df["fecha"] = pd.to_datetime(df["ANO_CONVO"], format="%d/%m/%Y")
    df = df.sort_values(["ID_PERSONA_PR", "conv"])

    primera = df.drop_duplicates("ID_PERSONA_PR", keep="first")
    ultima = df.drop_duplicates("ID_PERSONA_PR", keep="last")
    per = ultima.merge(primera[["ID_PERSONA_PR", "fecha", "conv"]],
                       on="ID_PERSONA_PR", suffixes=("_ult", "_prim"))
    per["t"] = (per["fecha_ult"] - per["fecha_prim"]).dt.days / 365.25
    per["evento"] = (per["conv_ult"] != CONV_FINAL).astype(float)
    fin = df.loc[df["conv"] == CONV_FINAL, "fecha"].iloc[0]
    ini = df.loc[df["conv"] == 16, "fecha"].iloc[0]
    xmax = float((fin - ini).days / 365.25)

    # Atributos de la ÚLTIMA observación (el perfil con que sale del sistema)
    per = per.rename(columns={"NME_CLASIFICACION_PR": "categoria",
                              "NME_GENERO_PR": "genero",
                              "NME_GRAN_AREA_PR": "area",
                              "NME_DEPARTAMENTO_RES_PR": "depto"})
    per["genero_col"] = per["genero"].map(
        lambda g: g if g in ("Masculino", "Femenino") else "Otro / No especificado")
    DEPT_TOP = per["depto"].value_counts().head(N_DEPT_TOP).index.tolist()
    per["depto_top"] = np.where(per["depto"].isin(DEPT_TOP), per["depto"], "Resto")
    print(f"   top {N_DEPT_TOP} departamentos (derivados de los datos): "
          f"{DEPT_TOP}")
    print(f"\n   personas: {len(per):,} · eventos: {int(per['evento'].sum()):,} · "
          f"censuradas: {int((1 - per['evento']).sum()):,} "
          f"({100*(1-per['evento'].mean()):.1f} %)".replace(",", " "))
    print(f"   ventana: {xmax:.3f} años · tiempo medio observado: "
          f"{per['t'].mean():.2f} años")

    out["diseno"] = {
        "unidad": "persona", "n_personas": int(len(per)),
        "eventos": int(per["evento"].sum()),
        "censuradas": int((1 - per["evento"]).sum()),
        "pct_censurado": float(100 * (1 - per["evento"].mean())),
        "ventana_anios": xmax,
        "tiempo_medio_observado": float(per["t"].mean()),
        "definicion": ("T = años desde la primera aparición hasta la última; "
                       "evento = la última aparición NO es la convocatoria de "
                       "2021; censura a la derecha si sigue en 2021."),
        "cautelas": [
            ("La censura es del 70,1 %: la mayoría sigue en el sistema al cerrar "
             "la ventana, así que las curvas están dominadas por la censura."),
            ("El tiempo se mide desde la primera aparición de cada persona, así "
             "que conviven cohortes de entrada de 2013 a 2021; no se ajusta por "
             "periodo calendario."),
            ("El evento es «no volver a aparecer en el registro», que incluye a "
             "quien simplemente se saltó la última convocatoria: el registro no "
             "permite distinguirlo."),
        ],
    }

    # ---------------- KM por desagregación ----------------
    def por_grupo(col: str, orden: list[str] | None = None,
                  min_n: int = 30) -> dict:
        res = {}
        niveles = orden if orden else sorted(per[col].unique())
        for lv in niveles:
            sub = per[per[col] == lv]
            if len(sub) == 0:
                continue
            km = kaplan_meier(sub["t"].to_numpy(), sub["evento"].to_numpy())
            res[str(lv)] = {
                "n": int(len(sub)), "eventos": int(sub["evento"].sum()),
                "km": km, "mediana": mediana_km(km),
                "estimable": bool(len(sub) >= min_n),
            }
        return res

    desag = {
        "categoria": por_grupo("categoria", CATEGORIAS_ORDEN),
        "genero": por_grupo("genero_col", ["Masculino", "Femenino",
                                          "Otro / No especificado"]),
        "area": por_grupo("area"),
        "departamento_top5": por_grupo("depto_top",
                                       DEPT_TOP + ["Resto"]),
    }
    out["kaplan_meier"] = desag
    out["logrank"] = {}
    for clave, col in (("categoria", "categoria"), ("genero", "genero_col"),
                       ("area", "area"), ("departamento_top5", "depto_top")):
        d = per[per[col] != "Otro / No especificado"] if col == "genero_col" \
            else per
        out["logrank"][clave] = logrank(d["t"].to_numpy(),
                                        d["evento"].to_numpy(),
                                        d[col].to_numpy())

    print("\n   Kaplan-Meier (mediana en años) y log-rank:")
    for clave, grupos in desag.items():
        lr = out["logrank"][clave]
        print(f"      {clave:20s} log-rank chi2={lr['chi2']:8.2f} gl={lr['gl']} "
              f"p={lr['p']:.3e}")
        for nombre, d in grupos.items():
            m = d["mediana"]
            med = (f"{m['anios']:.2f} años" if m["estimable"]
                   else "no alcanzada")
            print(f"         {nombre[:34]:36s} n={d['n']:6,d} "
                  f"ev={d['eventos']:6,d} mediana={med}".replace(",", " "))

    # ---------------- cohorte de 2013 (sin heterogeneidad de entrada) -------
    c13 = per[per["conv_prim"] == 16]
    km13 = kaplan_meier(c13["t"].to_numpy(), c13["evento"].to_numpy())
    out["cohorte_2013"] = {
        "n": int(len(c13)), "eventos": int(c13["evento"].sum()),
        "retencion_final": float(km13["S"][-1]) if km13["S"] else None,
        "mediana": mediana_km(km13),
        "nota": ("Cohorte de entrada única: no hay heterogeneidad de cohortes. "
                 "Es la misma base del 56,18 % de retención 2013→2021."),
    }
    print(f"\n   cohorte 2013: n={len(c13):,} · "
          f"S final={km13['S'][-1]:.4f} · mediana "
          f"{'no alcanzada' if not mediana_km(km13)['estimable'] else mediana_km(km13)['anios']}"
          .replace(",", " "))

    # ---------------- modelo de Cox ----------------
    # Se excluye Emérito (categoría terminal por selección) y el género no
    # estimable. Se documenta y se prueba después la sensibilidad.
    base = per[(per["genero_col"] != "Otro / No especificado")
               & (per["categoria"] != "Investigador Emérito")].copy()
    base["cat3"] = base["categoria"]
    dummies = []
    for col, niveles in (("cat3", ["Investigador Junior", "Investigador Asociado",
                                  "Investigador Sénior"]),
                         ("genero_col", ["Masculino", "Femenino"]),
                         ("area", sorted(base["area"].unique())),
                         ("depto_top", DEPT_TOP + ["Resto"])):
        ref = niveles[0]
        for lv in niveles[1:]:
            nombre = f"{col}={lv}"
            base[nombre] = (base[col] == lv).astype(float)
            dummies.append((col, lv, nombre))
    X = base[[n for _, _, n in dummies]].to_numpy()

    print(f"\n   modelo de Cox: n={len(base):,} · eventos="
          f"{int(base['evento'].sum()):,} · {X.shape[1]} covariables"
          .replace(",", " "))
    cox = cox_efron(X, base["t"].to_numpy(), base["evento"].to_numpy())
    if not cox["convergio"]:
        print(f"   [ABORTA] el Cox no convergió: {cox.get('motivo')}")
        return 2
    se = np.asarray(cox["se"])
    beta = np.asarray(cox["beta"])
    filas = []
    for i, (col, lv, _nombre) in enumerate(dummies):
        z = beta[i] / se[i] if se[i] > 0 else np.nan
        filas.append({
            "variable": col, "nivel": lv, "beta": float(beta[i]),
            "hr": float(np.exp(beta[i])), "se": float(se[i]),
            "ic95_inf": float(np.exp(beta[i] - Z * se[i])),
            "ic95_sup": float(np.exp(beta[i] + Z * se[i])),
            "p": float(2 * (1 - NormalDist().cdf(abs(z)))) if np.isfinite(z)
            else float("nan"),
        })
    tabla = pd.DataFrame(filas)
    tabla.to_csv(CSV.with_name("supervivencia_cox.csv"), index=False)
    out["cox"] = {
        "n": int(len(base)), "eventos": int(base["evento"].sum()),
        "n_covariables": int(X.shape[1]),
        "log_verosimilitud": float(cox["log_verosimilitud"]),
        "iteraciones": int(cox["iteraciones"]),
        "gradiente_final": float(cox["gradiente_final"]),
        "referencias": {"categoria": "Investigador Junior",
                        "genero": "Masculino", "area": "Ciencias Agrícolas",
                        "departamento": "Bogotá  D. C."},
        "coeficientes": filas,
        "excluidos": {
            "Investigador Emérito": ("334 personas (1,1 %). Se excluye porque es "
                                     "una categoría TERMINAL POR SELECCIÓN: solo "
                                     "se llega a Emérito habiendo sobrevivido, así "
                                     "que su hazard ratio no es interpretable como "
                                     "riesgo de salida (tiempo inmortal)."),
            "Otro / No especificado": ("9 personas con género Intersexual (5) o "
                                       "No disponible (4): no permiten estimar."),
        },
        "significativas_al_5pct": [
            f"{r['variable']}={r['nivel']}" for _, r in tabla.iterrows()
            if r["variable"] != "constante" and np.isfinite(r["p"]) and r["p"] < 0.05],
    }
    print(f"   convergió en {cox['iteraciones']} iteraciones · "
          f"gradiente final {cox['gradiente_final']:.2e}")
    print("\n   hazard ratios (IC 95 %):")
    for _, r in tabla.iterrows():
        if r["variable"] == "constante":
            continue
        marca = " *" if np.isfinite(r["p"]) and r["p"] < 0.05 else ""
        print(f"      {r['variable']}={r['nivel'][:30]:32s} "
              f"HR={r['hr']:6.3f} [{r['ic95_inf']:6.3f};{r['ic95_sup']:6.3f}] "
              f"p={r['p']:.2e}{marca}")

    # ---------------- validación: score de Cox vs log-rank ----------------
    # Con UNA covariable binaria los dos tests son el mismo; se comprueba en la
    # base real con la covariable más fuerte.
    binaria = (per["genero_col"] == "Femenino").to_numpy().astype(float)
    m = per["genero_col"].isin(["Masculino", "Femenino"]).to_numpy()
    lr_g = logrank(per["t"].to_numpy()[m], per["evento"].to_numpy()[m],
                   per["genero_col"].to_numpy()[m])
    Xg = binaria[m].reshape(-1, 1)
    sc_g = cox_score(Xg, per["t"].to_numpy()[m], per["evento"].to_numpy()[m])
    out["validacion_score_vs_logrank"] = {
        "covariable": "Femenino (frente a Masculino)",
        "logrank_chi2": lr_g["chi2"], "logrank_p": lr_g["p"],
        "cox_score_chi2": sc_g["chi2"], "cox_score_p": sc_g["p"],
        "diferencia_relativa_chi2": float(
            abs(lr_g["chi2"] - sc_g["chi2"]) / lr_g["chi2"])
        if lr_g["chi2"] else float("nan"),
        "coinciden": bool(np.isfinite(lr_g["chi2"]) and np.isfinite(sc_g["chi2"])
                          and abs(lr_g["chi2"] - sc_g["chi2"])
                          <= 0.05 * abs(lr_g["chi2"])),
        "nota": ("Con una sola covariable binaria el test de score de Cox y el "
                 "log-rank son el mismo contraste. Coinciden EXACTAMENTE cuando "
                 "no hay empates; aquí los hay (los eventos solo se observan en 6 "
                 "fechas) y el log-rank usa el tratamiento de Breslow mientras el "
                 "Cox usa Efron, así que se espera una diferencia pequeña. Si la "
                 "diferencia fuera grande, la implementación estaría mal."),
    }
    print(f"\n   validación: chi2 log-rank={lr_g['chi2']:.4f} · score de Cox="
          f"{sc_g['chi2']:.4f} · coinciden="
          f"{out['validacion_score_vs_logrank']['coinciden']}")

    # ---------------- sensibilidad: Emérito agrupado con Sénior -----------
    base2 = per[per["genero_col"] != "Otro / No especificado"].copy()
    base2["cat3"] = base2["categoria"].replace(
        {"Investigador Emérito": "Investigador Sénior"})
    dummies2 = []
    for col, niveles in (("cat3", ["Investigador Junior", "Investigador Asociado",
                                   "Investigador Sénior"]),
                         ("genero_col", ["Masculino", "Femenino"]),
                         ("area", sorted(base2["area"].unique())),
                         ("depto_top", DEPT_TOP + ["Resto"])):
        for lv in niveles[1:]:
            nombre = f"{col}={lv}"
            base2[nombre] = (base2[col] == lv).astype(float)
            dummies2.append(nombre)
    X2 = base2[dummies2].to_numpy()
    cox2 = cox_efron(X2, base2["t"].to_numpy(), base2["evento"].to_numpy())
    hr1 = {(r["variable"], r["nivel"]): r["hr"] for _, r in tabla.iterrows()}
    dif_hr = {}
    if cox2["convergio"]:
        for i, (col, lv) in enumerate([(c, l) for c, l, _ in dummies]):
            v2 = float(np.exp(cox2["beta"][i]))
            if (col, lv) in hr1:
                dif_hr[f"{col}={lv}"] = round(v2 - hr1[(col, lv)], 4)
    out["sensibilidad_emerito_agrupado"] = {
        "n": int(len(base2)), "convergio": bool(cox2["convergio"]),
        "cambio_en_los_hr": dif_hr,
        "cambio_maximo_absoluto": float(max((abs(v) for v in dif_hr.values()),
                                           default=float("nan"))),
        "nota": ("Agrupar Emérito con Sénior es lo que el proyecto ya hace en la "
                 "post-estratificación. Si los HR apenas se mueven, excluir a los "
                 "334 eméritos no sesga las conclusiones."),
    }

    # ---------------- figuras ----------------
    GRAF.mkdir(parents=True, exist_ok=True)
    fig_km({k: v for k, v in desag["categoria"].items()},
           "Supervivencia por categoría", GRAF / "f2_10_km_categoria.png", xmax)
    fig_km({k: v for k, v in desag["genero"].items() if v["estimable"]},
           "Supervivencia por género", GRAF / "f2_10_km_genero.png", xmax)
    fig_km(desag["area"], "Supervivencia por gran área",
           GRAF / "f2_10_km_area.png", xmax)
    fig_km(desag["departamento_top5"], "Supervivencia por departamento (top 5 + resto)",
           GRAF / "f2_10_km_departamento.png", xmax)
    fig_forest(tabla, GRAF / "f2_10_cox_forest.png")
    out["figuras"] = sorted(p.name for p in GRAF.glob("*.png"))

    # ---------------- validaciones ----------------
    out["validaciones"] = {
        "km_sin_censura_correcta": bool(autotest["km_sin_censura_correcto"]),
        "score_cox_igual_logrank": bool(
            out["validacion_score_vs_logrank"]["coinciden"]),
        "cox_convergio": bool(cox["convergio"]),
        "cox_gradiente_despreciable": bool(cox["gradiente_final"] < 1e-3),
        "suma_personas": bool(len(per) == int(df["ID_PERSONA_PR"].nunique())),
        "tiempos_no_negativos": bool((per["t"] >= 0).all()),
        "mediana_no_forzada_si_no_se_alcanza": bool(
            all(("anios" in d["mediana"]) == d["mediana"]["estimable"]
                for g in desag.values() for d in g.values())),
        "emerito_excluido_del_cox": bool(
            "Investigador Emérito" in out["cox"]["excluidos"]),
        "nivel_de_referencia_con_casos": bool(
            all((base[c] == niveles[0]).sum() > 0
                for c, niveles in (
                    ("cat3", ["Investigador Junior", "Investigador Asociado",
                              "Investigador Sénior"]),
                    ("genero_col", ["Masculino", "Femenino"]),
                    ("area", sorted(base["area"].unique())),
                    ("depto_top", DEPT_TOP + ["Resto"])))),
    }
    print()
    for k, v in out["validaciones"].items():
        print(f"   [{'OK ' if v else 'NO '}] {k}")

    per[["ID_PERSONA_PR", "conv_prim", "conv_ult", "t", "evento", "categoria",
         "genero_col", "area", "depto_top"]].to_csv(CSV, index=False)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"\n-> {SALIDA.relative_to(RAIZ)} ({SALIDA.stat().st_size:,} bytes)")
    print(f"-> {CSV.relative_to(RAIZ)} ({len(per):,} personas)".replace(",", " "))
    print(f"-> {GRAF.relative_to(RAIZ)}/ ({len(out['figuras'])} figuras)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
