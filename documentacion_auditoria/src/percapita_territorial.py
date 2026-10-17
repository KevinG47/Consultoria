# -*- coding: utf-8 -*-
"""
percapita_territorial.py
========================

F2-2 — Concentración territorial PER CÁPITA (respuesta a la pregunta Q3 del
repositorio auditado).

Problema que resuelve
---------------------
El repositorio auditado mide la concentración territorial con el HHI sobre
CUOTAS DE INVESTIGADORES: qué fracción del total aporta cada departamento. Ese
indicador mezcla dos cosas distintas:

  (a) que un departamento tenga muchos investigadores porque tiene mucha
      población, y
  (b) que tenga muchos investigadores POR HABITANTE.

Que el HHI de cuotas baje (0,1903 en 2013 -> 0,1457 en 2021) solo dice que la
cuota del departamento dominante se diluyó. NO dice si la probabilidad de ser
investigador reconocido por habitante se volvió más parecida entre territorios.
Q3 pide lo segundo —«comparar la concentración territorial frente a la población
departamental»— y nunca se calculó en el repositorio auditado.

Qué hace este script
--------------------
1. Cuenta PERSONAS distintas por departamento y convocatoria.
2. Une por CÓDIGO DIVIPOLA, no por nombre: el nombre de la fuente trae dobles
   espacios ('Bogotá  D. C.') y no es una clave fiable.
3. Divide por la población departamental del CNPV 2018 -> investigadores por
   100 000 habitantes.
4. IC al 95 % por bootstrap en dos niveles:
     - `bootstrap_personas`: remuestreo de los investigadores reconocidos
       (incertidumbre de superpoblación del indicador);
     - `bootstrap_diseno`  : remuestreo dentro de post-estratos por categoría
       sobre la muestra MAS (n = 2 224). Responde a «¿qué podría afirmarse por
       departamento si solo tuviéramos la muestra?».
5. Gini y Theil (T y L) de los conteos y de las TASAS, con descomposición de
   Theil entre y dentro de regiones, por convocatoria.
6. Compara con el HHI del auditado y cuantifica el efecto de tratar «Exterior»
   y «No disponible» como si fueran territorios colombianos.

Denominadores (todos oficiales del DANE; ver *.procedencia.txt junto a cada CSV)
------------------------------------------------------------------------------
- Principal : población CENSADA 2018 (cuadro 1PD; 33 unidades; 44 164 417).
- Robustez 1: población AJUSTADA por omisión 2018 (proyecciones PPED;
              48 258 494).
- Robustez 2: población proyectada 2021 (51 115 637), denominador emparejado
              por año para la convocatoria de 2021.

Produce:
    01_datos/resultados_json/percapita_territorial.json
    data/memoria/graficas_percapita/*.png

Uso:
    python documentacion_auditoria/src/percapita_territorial.py
"""

from __future__ import annotations

import io
import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                        # noqa: E402
import pandas as pd                       # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
FUENTE_DIR = RAIZ / "01_datos" / "datos_fuente"
FUENTE = FUENTE_DIR / "Investigadores_Reconocidos_por_convocatoria_20261006.csv"
POB_CENSADA = FUENTE_DIR / "dane_cnpv2018_poblacion_departamental.csv"
POB_PROYECTADA = FUENTE_DIR / "dane_proyecciones_poblacion_departamental.csv"
MUESTRA = DOC / "data" / "memoria" / "muestra_ids.csv"
AUDITADO = RAIZ / "04_auditoria" / "repo_original" / "evidencias"

SALIDA = RAIZ / "01_datos" / "resultados_json" / "percapita_territorial.json"
GRAF = DOC / "data" / "memoria" / "graficas_percapita"

CONV = {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021}
CONV_ORDEN = [16, 17, 18, 19, 20, 21]
SEMILLA = 20260217
B = 2000                      # réplicas de bootstrap
EXCLUIDOS_DE_TASA = ["Exterior", "No disponible"]

# --- paleta institucional única (la misma del dashboard y del anteproyecto) --
AZUL, AZUL_SEC, AZUL_CLARO = "#1E3780", "#4A6BA8", "#7BA7D0"
DORADO, DORADO_CLARO = "#B7871E", "#D4A84A"
GRIS_OSC, GRIS, GRIS_CLARO = "#334155", "#64748B", "#CBD5E1"
FONDO, TEXTO, ALERTA = "#F8FAFC", "#1E293B", "#B91C1C"


# ==========================================================================
# 0. Índices de desigualdad
# ==========================================================================
def gini(x: np.ndarray) -> float:
    """Coeficiente de Gini (0 = igualdad total; ->1 = toda la masa en uno)."""
    x = np.asarray(x, dtype=float)
    if x.size == 0 or x.sum() <= 0 or (x < 0).any():
        return float("nan")
    n = x.size
    xs = np.sort(x)
    i = np.arange(1, n + 1)
    return float((2.0 * np.sum(i * xs) - (n + 1) * np.sum(xs)) / (n * np.sum(xs)))


def theil_t(x: np.ndarray) -> float:
    """
    Theil T (entropía generalizada con alpha = 1).

    T = (1/n) * SUM (x_i/xbar) * ln(x_i/xbar), con 0*ln0 = 0. Admite ceros: un
    departamento sin investigadores contribuye 0.
    """
    x = np.asarray(x, dtype=float)
    if x.size == 0 or x.sum() <= 0 or (x < 0).any():
        return float("nan")
    r = x / x.mean()
    with np.errstate(divide="ignore", invalid="ignore"):
        term = np.where(r > 0, r * np.log(np.where(r > 0, r, 1.0)), 0.0)
    return float(term.mean())


def theil_l(x: np.ndarray) -> float | None:
    """Theil L (desviación media logarítmica). Devuelve None si hay ceros."""
    x = np.asarray(x, dtype=float)
    if x.size == 0 or (x <= 0).any():
        return None
    return float(np.mean(np.log(x.mean() / x)))


def hhi(x: np.ndarray) -> float:
    """Herfindahl-Hirschman sobre la distribución normalizada de x."""
    x = np.asarray(x, dtype=float)
    if x.size == 0 or x.sum() <= 0:
        return float("nan")
    s = x / x.sum()
    return float(np.sum(s ** 2))


def theil_descomposicion(x: np.ndarray, grupos: np.ndarray) -> dict:
    """
    Descompone Theil T en ENTRE y DENTRO de grupos (regiones).

        T = SUM_g s_g * T_g  +  SUM_g s_g * ln(s_g / p_g)
            \\___dentro___/     \\________entre________/

    con s_g = cuota del grupo en la masa total de x y p_g = cuota de unidades.
    """
    x = np.asarray(x, dtype=float)
    grupos = np.asarray(grupos)
    s_tot, n_tot = x.sum(), x.size
    dentro = entre = 0.0
    detalle: dict = {}
    for g in pd.unique(grupos):
        m = grupos == g
        s_g = float(x[m].sum() / s_tot) if s_tot > 0 else 0.0
        p_g = float(m.sum() / n_tot)
        t_g = theil_t(x[m])
        dentro += s_g * (t_g if np.isfinite(t_g) else 0.0)
        if s_g > 0:
            entre += s_g * np.log(s_g / p_g)
        detalle[str(g)] = {"s_g": s_g, "p_g": p_g, "T_g": float(t_g),
                           "n": int(m.sum())}
    return {"total": theil_t(x), "dentro": float(dentro), "entre": float(entre),
            "suma_dentro_entre": float(dentro + entre), "grupos": detalle}


def _autotest_indices() -> dict:
    """
    Comprueba los índices contra casos de solución conocida.

    Evita el error silencioso más caro de este análisis: un Gini o un Theil mal
    implementados que producen cifras plausibles pero falsas.
    """
    n = 33
    casos: dict = {}
    igual = np.full(n, 7.0)
    casos["igualdad_perfecta"] = {"gini": gini(igual), "theil_t": theil_t(igual),
                                  "theil_l": theil_l(igual)}
    concentrado = np.zeros(n)
    concentrado[0] = 1.0
    casos["concentracion_total"] = {
        "gini": gini(concentrado), "gini_esperado": (n - 1) / n,
        "theil_t": theil_t(concentrado), "theil_t_esperado": float(np.log(n)),
    }
    rng = np.random.default_rng(7)
    x = rng.gamma(2.0, 1.0, n)
    g = np.array(["A"] * 11 + ["B"] * 11 + ["C"] * 11)
    d = theil_descomposicion(x, g)
    casos["descomposicion_cierra"] = {
        "total": d["total"], "dentro_mas_entre": d["suma_dentro_entre"],
        "diferencia": abs(d["total"] - d["suma_dentro_entre"]),
    }
    casos["invariancia_escala"] = {
        "gini_original": gini(x), "gini_escalado": gini(x * 1234.5),
        "theil_original": theil_t(x), "theil_escalado": theil_t(x * 1234.5),
    }
    ok = (
        abs(casos["igualdad_perfecta"]["gini"]) < 1e-12
        and abs(casos["igualdad_perfecta"]["theil_t"]) < 1e-12
        and abs(casos["igualdad_perfecta"]["theil_l"]) < 1e-12
        and abs(casos["concentracion_total"]["gini"]
                - casos["concentracion_total"]["gini_esperado"]) < 1e-12
        and abs(casos["concentracion_total"]["theil_t"]
                - casos["concentracion_total"]["theil_t_esperado"]) < 1e-12
        and casos["descomposicion_cierra"]["diferencia"] < 1e-12
        and abs(casos["invariancia_escala"]["gini_original"]
                - casos["invariancia_escala"]["gini_escalado"]) < 1e-12
        and abs(casos["invariancia_escala"]["theil_original"]
                - casos["invariancia_escala"]["theil_escalado"]) < 1e-12
    )
    casos["todas_las_comprobaciones_ok"] = bool(ok)
    return casos


# ==========================================================================
# 1. Carga
# ==========================================================================
def cargar_investigadores() -> tuple[pd.DataFrame, dict]:
    cols = ["ID_CONVOCATORIA", "ID_PERSONA_PR", "COD_DANE_RES_PR",
            "NME_DEPARTAMENTO_RES_PR", "NME_REGION_RES_PR",
            "NME_CLASIFICACION_PR"]
    partes = pd.read_csv(FUENTE, dtype=str, keep_default_na=False,
                         usecols=cols, chunksize=50_000, encoding="utf-8")
    df = pd.concat(partes, ignore_index=True)

    cod = df["COD_DANE_RES_PR"].str.strip()
    # El código DIVIPOLA municipal tiene 5 dígitos y su prefijo de 2 es el
    # departamento; algunas filas traen ya solo el código departamental.
    df["codigo_dane"] = cod.str.slice(0, 2).where(cod.str.len() >= 2, "")
    df["conv"] = df["ID_CONVOCATORIA"].astype(int)
    df["anio"] = df["conv"].map(CONV)
    df["region"] = df["NME_REGION_RES_PR"].str.strip()
    df["categoria"] = df["NME_CLASIFICACION_PR"].str.strip()

    sin_cod = df["codigo_dane"] == ""
    diag = {
        "registros_totales": int(len(df)),
        "personas_distintas": int(df["ID_PERSONA_PR"].nunique()),
        "registros_sin_codigo_dane": int(sin_cod.sum()),
        "registros_sin_codigo_por_etiqueta": {
            k: int(v) for k, v in
            df.loc[sin_cod, "NME_DEPARTAMENTO_RES_PR"].value_counts().items()},
        "personas_excluidas_de_tasa": int(
            df.loc[sin_cod, "ID_PERSONA_PR"].nunique()),
        "duplicados_persona_en_misma_convocatoria": int(
            len(df) - df.drop_duplicates(["conv", "ID_PERSONA_PR"]).shape[0]),
        "convocatorias": {str(CONV[c]): int((df["conv"] == c).sum())
                          for c in CONV_ORDEN},
    }
    return df, diag


# ==========================================================================
# 2. Bootstrap
# ==========================================================================
def _resumen_boot(conteos_rep: np.ndarray, pob: np.ndarray) -> dict:
    """Resume réplicas (B x K) de CONTEOS: tasas, índices e IC percentiles."""
    tasas = conteos_rep / pob * 1e5
    lo = np.percentile(tasas, 2.5, axis=0)
    hi = np.percentile(tasas, 97.5, axis=0)
    ginis = np.array([gini(t) for t in tasas])
    theils = np.array([theil_t(t) for t in tasas])
    hhis = np.array([hhi(t) for t in tasas])
    return {
        "tasa_ic95": {"lo": lo.tolist(), "hi": hi.tolist()},
        "ancho_ic_mediano_por_100000": float(np.median(hi - lo)),
        "gini_ic95": [float(np.percentile(ginis, 2.5)),
                      float(np.percentile(ginis, 97.5))],
        "gini_ee": float(ginis.std(ddof=1)),
        "theil_t_ic95": [float(np.percentile(theils, 2.5)),
                         float(np.percentile(theils, 97.5))],
        "theil_t_ee": float(theils.std(ddof=1)),
        "hhi_tasas_ic95": [float(np.percentile(hhis, 2.5)),
                           float(np.percentile(hhis, 97.5))],
        "replicas": int(conteos_rep.shape[0]),
    }


def boot_personas(k_idx: np.ndarray, pob: np.ndarray, rng) -> np.ndarray:
    """
    Bootstrap de superpoblación: remuestrea los investigadores reconocidos.

    «Si el conjunto de investigadores reconocidos fuese otra realización del
    mismo proceso, ¿cuánto se movería la tasa?» Trata la base como muestra de
    una superpoblación, no como población finita.
    """
    n, K = k_idx.size, pob.size
    out = np.empty((B, K), dtype=np.float64)
    for b in range(B):
        out[b] = np.bincount(k_idx[rng.integers(0, n, n)], minlength=K)
    return out


def boot_diseno(k_s: np.ndarray, cat_s: np.ndarray, N_h: np.ndarray,
                pob: np.ndarray, rng) -> dict:
    """
    Bootstrap de diseño sobre la muestra MAS con post-estratificación.

        N_hat_d = SUM_h N_h * n_{h,d} / n_h

    con N_h = tamaño del post-estrato h en la población y n_h en la muestra. El
    remuestreo se hace DENTRO de cada post-estrato (n_h fijo), que es el
    bootstrap estándar de un estimador post-estratificado.
    """
    K, H = pob.size, N_h.size
    pos = [np.where(cat_s == h)[0] for h in range(H)]
    n_h = np.array([p.size for p in pos])
    out = np.empty((B, K), dtype=np.float64)
    for b in range(B):
        acc = np.zeros(K)
        for h, p in enumerate(pos):
            if p.size == 0 or N_h[h] <= 0:
                continue
            draw = p[rng.integers(0, p.size, p.size)]
            acc += (N_h[h] / p.size) * np.bincount(k_s[draw], minlength=K)
        out[b] = acc
    return {"replicas_conteos": out, "n_h": n_h.tolist(),
            "post_estratos_sin_muestra": int((n_h == 0).sum())}


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


def fig_tasas(etiq, tasa, lo, hi, pob, archivo) -> None:
    orden = np.argsort(tasa)[::-1]
    fig, ax = plt.subplots(figsize=(11.2, 5.4), dpi=150)
    x = np.arange(len(orden))
    y = tasa[orden]
    ax.bar(x, y, color=AZUL, width=0.72, zorder=2)
    ax.errorbar(x, y, yerr=[np.maximum(y - lo[orden], 0),
                            np.maximum(hi[orden] - y, 0)],
                fmt="none", ecolor=GRIS_OSC, elinewidth=0.9, capsize=2.4,
                zorder=3)
    nacional = tasa.sum() / pob.sum() * 1e5
    ax.axhline(nacional, color=DORADO, linewidth=1.6, zorder=4,
               label=f"Promedio nacional = {nacional:,.0f} por 100 000".replace(",", " "))
    ax.set_xticks(x)
    ax.set_xticklabels([etiq[i] for i in orden], rotation=72, ha="right",
                       fontsize=7.4)
    ax.set_ylabel("Investigadores por 100 000 habitantes", color=TEXTO, fontsize=9)
    ax.set_title("Investigadores reconocidos por 100 000 habitantes, por "
                 "departamento\n(stock: cada persona contada en su última "
                 "convocatoria; barras de error = IC 95 % bootstrap)",
                 color=TEXTO, fontsize=10.4, pad=10, loc="left")
    ax.legend(frameon=False, fontsize=8.4, labelcolor=GRIS_OSC)
    _estilo(ax)
    fig.tight_layout()
    fig.savefig(archivo, facecolor="white")
    plt.close(fig)


def fig_evolucion(anios, series, archivo) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), dpi=150)
    espec = [
        ("hhi_cuotas", "HHI sobre cuotas de investigadores\n(la medida del auditado)", GRIS_OSC),
        ("gini_tasas", "Gini de las tasas por 100 000 hab.\n(desigualdad per cápita)", AZUL),
        ("theil_tasas", "Theil T de las tasas por 100 000 hab.", DORADO),
    ]
    for ax, (clave, titulo, color) in zip(axes, espec):
        y = series[clave]
        ax.plot(anios, y, marker="o", color=color, linewidth=2.1, markersize=5.4,
                zorder=3)
        for xi, yi in zip(anios, y):
            ax.annotate(f"{yi:.4f}", (xi, yi), textcoords="offset points",
                        xytext=(0, 8), ha="center", fontsize=7.6, color=GRIS_OSC)
        ax.set_title(titulo, color=TEXTO, fontsize=9.4, pad=9)
        ax.set_xlabel("Convocatoria", color=TEXTO, fontsize=8.6)
        _estilo(ax)
    fig.suptitle("La cuota del departamento dominante se diluye, pero la "
                 "desigualdad por habitante sigue otro camino",
                 color=TEXTO, fontsize=11.2, y=1.02, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(archivo, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def fig_cuota_vs_poblacion(sh_inv, sh_pob, etiq, archivo) -> None:
    fig, ax = plt.subplots(figsize=(7.6, 6.6), dpi=150)
    lim = max(sh_inv.max(), sh_pob.max()) * 1.4
    ax.plot([0, lim], [0, lim], color=GRIS, linewidth=1.3, linestyle="--",
            label="Proporcionalidad estricta")
    ratio = sh_inv / sh_pob
    colores = np.where(ratio >= 1, DORADO, AZUL)
    ax.scatter(sh_pob * 100, sh_inv * 100, s=48, c=colores, edgecolor="white",
               linewidth=0.7, zorder=3)
    for nombre, x0, y0, r in zip(etiq, sh_pob * 100, sh_inv * 100, ratio):
        if r >= 1.25 or r <= 0.55 or x0 > 6 or y0 > 6:
            ax.annotate(nombre, (x0, y0), textcoords="offset points",
                        xytext=(5, 3), fontsize=7.2, color=GRIS_OSC)
    ax.set_xlabel("Cuota de la población censada 2018 (%)", color=TEXTO, fontsize=9)
    ax.set_ylabel("Cuota de los investigadores reconocidos (%)", color=TEXTO,
                  fontsize=9)
    ax.set_title("Cuánta población aporta cada departamento y cuánta "
                 "investigación\nDorado = más investigadores por habitante que "
                 "el promedio nacional", color=TEXTO, fontsize=10.2, pad=10,
                 loc="left")
    ax.legend(frameon=False, fontsize=8.2, labelcolor=GRIS_OSC)
    _estilo(ax)
    ax.grid(axis="x", color=GRIS_CLARO, linewidth=0.6, alpha=0.9)
    fig.tight_layout()
    fig.savefig(archivo, facecolor="white")
    plt.close(fig)


def fig_theil(anios, dentro, entre, archivo) -> None:
    fig, ax = plt.subplots(figsize=(7.8, 4.4), dpi=150)
    x = np.arange(len(anios))
    ax.bar(x, dentro, color=AZUL, width=0.6, label="Dentro de las regiones",
           zorder=2)
    ax.bar(x, entre, bottom=dentro, color=DORADO, width=0.6,
           label="Entre regiones", zorder=2)
    for xi, (d, e) in enumerate(zip(dentro, entre)):
        ax.annotate(f"{d + e:.4f}", (xi, d + e), textcoords="offset points",
                    xytext=(0, 4), ha="center", fontsize=7.8, color=GRIS_OSC)
    ax.set_xticks(x)
    ax.set_xticklabels([str(a) for a in anios])
    ax.set_xlabel("Convocatoria", color=TEXTO, fontsize=9)
    ax.set_ylabel("Theil T de las tasas por 100 000 hab.", color=TEXTO, fontsize=9)
    ax.set_title("Descomposición de Theil de la desigualdad territorial:\n"
                 "cuánta vive entre regiones y cuánta dentro de ellas",
                 color=TEXTO, fontsize=10.2, pad=10, loc="left")
    ax.legend(frameon=False, fontsize=8.4, labelcolor=GRIS_OSC)
    _estilo(ax)
    fig.tight_layout()
    fig.savefig(archivo, facecolor="white")
    plt.close(fig)


# ==========================================================================
# 4. Principal
# ==========================================================================
def main() -> int:
    print("== F2-2 · Concentración territorial per cápita ==")
    salida: dict = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "analisis": "F2-2 — Concentración territorial per cápita (pregunta Q3)",
        "semilla": SEMILLA, "replicas_bootstrap": B,
        "autotest_indices": _autotest_indices(),
    }
    if not salida["autotest_indices"]["todas_las_comprobaciones_ok"]:
        print("   [ABORTA] el autotest de Gini/Theil falló")
        return 2
    print("   [OK] autotest de Gini/Theil: igualdad, concentración total, "
          "descomposición y invariancia de escala")

    df, diag = cargar_investigadores()
    censada = pd.read_csv(POB_CENSADA, dtype={"codigo_dane": str}, encoding="utf-8")
    proy = pd.read_csv(POB_PROYECTADA, dtype={"codigo_dane": str}, encoding="utf-8")
    print(f"   fuente: {diag['registros_totales']:,} registros · "
          f"{diag['personas_distintas']:,} personas".replace(",", " "))
    print(f"   sin código DIVIPOLA (Exterior + No disponible): "
          f"{diag['registros_sin_codigo_dane']:,} registros".replace(",", " "))
    salida["fuente"] = diag

    codigos = censada["codigo_dane"].tolist()
    etiq = censada["departamento"].tolist()
    K = len(codigos)
    pob_censada = censada["poblacion_censada_2018"].to_numpy(float)
    proy_18 = (proy[proy["anio"] == 2018].set_index("codigo_dane")
               ["poblacion_proyectada"].reindex(codigos).to_numpy(float))
    proy_21 = (proy[proy["anio"] == 2021].set_index("codigo_dane")
               ["poblacion_proyectada"].reindex(codigos).to_numpy(float))
    if np.isnan(proy_18).any() or np.isnan(proy_21).any():
        print("   [ABORTA] faltan departamentos en las proyecciones DANE")
        return 2
    print(f"   población censada 2018    : {pob_censada.sum():,}".replace(",", " "))
    print(f"   población ajustada 2018   : {proy_18.sum():,.0f}".replace(",", " "))
    print(f"   población proyectada 2021 : {proy_21.sum():,.0f}".replace(",", " "))
    salida["poblacion"] = {
        "censada_2018_total": int(pob_censada.sum()),
        "ajustada_2018_total": int(proy_18.sum()),
        "proyectada_2021_total": int(proy_21.sum()),
        "criterio": ("Denominador principal = población censada 2018 (cuadro "
                     "1PD). Robustez con la ajustada por omisión y, para 2021, "
                     "con la proyectada de ese año."),
    }

    # ---------------- universo con territorio colombiano ----------------
    idx = {c: i for i, c in enumerate(codigos)}
    val = df[df["codigo_dane"].isin(idx)].copy()
    val["k"] = val["codigo_dane"].map(idx).astype(np.int16)
    salida["universo"] = {
        "registros_con_territorio_colombiano": int(len(val)),
        "registros_excluidos_de_tasa": int(len(df) - len(val)),
        "personas_excluidas_de_tasa": diag["personas_excluidas_de_tasa"],
        "criterio": ("'Exterior' y 'No disponible' se excluyen de las tasas: no "
                     "tienen población colombiana en el denominador. Sí se "
                     "conservan al reproducir el HHI del auditado, que los "
                     "cuenta como territorios."),
    }

    # ---------------- conteos ----------------
    uniq = val.drop_duplicates(["conv", "ID_PERSONA_PR"])
    conteo = np.zeros((len(CONV_ORDEN), K), dtype=np.int64)
    reg_c: dict[int, np.ndarray] = {}
    for j, c in enumerate(CONV_ORDEN):
        sub = uniq[uniq["conv"] == c]
        conteo[j] = np.bincount(sub["k"].to_numpy(), minlength=K)
        reg_c[c] = (sub.groupby("k")["region"].agg(lambda s: s.mode().iat[0])
                    .reindex(range(K)).fillna("No disponible").to_numpy())
    ult = val.sort_values("conv").drop_duplicates("ID_PERSONA_PR", keep="last")
    stock = np.bincount(ult["k"].to_numpy(), minlength=K)
    regiones = (ult.groupby("k")["region"].agg(lambda s: s.mode().iat[0])
                .reindex(range(K)).fillna("No disponible").to_numpy())
    print(f"   stock (última convocatoria de cada persona): "
          f"{stock.sum():,} personas".replace(",", " "))
    salida["conteos"] = {
        "stock_personas": int(stock.sum()),
        "departamentos_sin_investigadores_en_stock": int((stock == 0).sum()),
        "por_convocatoria": {str(CONV[c]): int(conteo[j].sum())
                             for j, c in enumerate(CONV_ORDEN)},
    }

    # ---------------- tasas e índices por convocatoria ----------------
    def tabla(conteos: np.ndarray, pob: np.ndarray) -> dict:
        tasa = conteos / pob * 1e5
        return {etiq[i]: {"investigadores": int(conteos[i]),
                          "poblacion": int(pob[i]),
                          "tasa_por_100000": float(tasa[i])}
                for i in range(K)}

    por_conv: dict = {}
    for j, c in enumerate(CONV_ORDEN):
        tasa = conteo[j] / pob_censada * 1e5
        des = theil_descomposicion(tasa, reg_c[c])
        por_conv[str(CONV[c])] = {
            "total_investigadores": int(conteo[j].sum()),
            "tasa_nacional_por_100000": float(conteo[j].sum()
                                              / pob_censada.sum() * 1e5),
            "gini_tasas": gini(tasa), "theil_t_tasas": theil_t(tasa),
            "hhi_tasas": hhi(tasa),
            "gini_conteos": gini(conteo[j]),
            "theil_t_conteos": theil_t(conteo[j]),
            "hhi_conteos": hhi(conteo[j]),
            "departamentos_sin_investigadores": int((conteo[j] == 0).sum()),
            "theil_tasas_dentro_regiones": des["dentro"],
            "theil_tasas_entre_regiones": des["entre"],
            "detalle": tabla(conteo[j], pob_censada),
        }
    tasa_stock = stock / pob_censada * 1e5
    des_stock = theil_descomposicion(tasa_stock, regiones)
    salida["tasa_por_100000"] = {
        "denominador": "población censada 2018",
        "stock_ultima_convocatoria": tabla(stock, pob_censada),
        "por_convocatoria": por_conv,
    }
    salida["indices_stock"] = {
        "gini_tasas": gini(tasa_stock),
        "theil_t_tasas": theil_t(tasa_stock),
        "theil_l_tasas": theil_l(tasa_stock),
        "hhi_tasas": hhi(tasa_stock),
        "gini_conteos": gini(stock),
        "theil_t_conteos": theil_t(stock),
        "hhi_conteos": hhi(stock),
        "theil_descomposicion_tasas_regiones": des_stock,
        "theil_descomposicion_conteos_regiones":
            theil_descomposicion(stock, regiones),
        "tasa_nacional_por_100000": float(stock.sum() / pob_censada.sum() * 1e5),
    }
    print(f"\n   Gini de tasas (stock) : {salida['indices_stock']['gini_tasas']:.4f}")
    print(f"   Theil T de tasas      : {salida['indices_stock']['theil_t_tasas']:.4f}")
    print(f"   Gini de conteos       : {salida['indices_stock']['gini_conteos']:.4f}")
    print(f"   Theil T: entre regiones={des_stock['entre']:.4f} · "
          f"dentro={des_stock['dentro']:.4f}")

    # ---------------- indicadores clave para el informe ----------------
    sh_inv = stock / stock.sum()
    sh_pob = pob_censada / pob_censada.sum()
    ratio = sh_inv / sh_pob
    orden_tasa = np.argsort(tasa_stock)[::-1]
    salida["indicadores_clave"] = {
        "tasa_nacional_por_100000": salida["indices_stock"]["tasa_nacional_por_100000"],
        "departamento_mayor_tasa": {"departamento": etiq[orden_tasa[0]],
                                    "tasa": float(tasa_stock[orden_tasa[0]])},
        "departamento_menor_tasa": {"departamento": etiq[orden_tasa[-1]],
                                    "tasa": float(tasa_stock[orden_tasa[-1]])},
        "razon_mayor_menor": float(tasa_stock[orden_tasa[0]]
                                   / tasa_stock[orden_tasa[-1]]),
        "sobrerrepresentacion_cuota_vs_poblacion": {
            etiq[i]: float(ratio[i]) for i in np.argsort(ratio)[::-1][:5]},
        "subrrepresentacion_cuota_vs_poblacion": {
            etiq[i]: float(ratio[i]) for i in np.argsort(ratio)[:5]},
        "cuota_bogota_investigadores": float(sh_inv[etiq.index("Bogotá, D. C.")]),
        "cuota_bogota_poblacion": float(sh_pob[etiq.index("Bogotá, D. C.")]),
    }

    # ---------------- bootstrap de personas ----------------
    rng = np.random.default_rng(SEMILLA)
    boot: dict = {}
    for c in CONV_ORDEN:
        sub = val[val["conv"] == c].drop_duplicates("ID_PERSONA_PR")
        m = boot_personas(sub["k"].to_numpy(), pob_censada, rng)
        boot[str(CONV[c])] = _resumen_boot(m, pob_censada)
        print(f"   bootstrap personas {CONV[c]}: n={sub.shape[0]:,} · ancho IC "
              f"mediano={boot[str(CONV[c])]['ancho_ic_mediano_por_100000']:.1f}"
              .replace(",", " "))
    m_stock = boot_personas(ult["k"].to_numpy(), pob_censada, rng)
    boot["stock"] = _resumen_boot(m_stock, pob_censada)
    salida["bootstrap_personas"] = {
        "descripcion": ("Remuestreo de los investigadores reconocidos. Mide la "
                        "incertidumbre de superpoblación del indicador, "
                        "tratando la base como una realización de un proceso."),
        "por_convocatoria_y_stock": boot,
    }

    # ---------------- bootstrap de diseño (MAS + post-estratificación) ----
    ids = set(pd.read_csv(MUESTRA, dtype=str, keep_default_na=False)
              ["ID_PERSONA_PR"])
    val["en_muestra"] = val["ID_PERSONA_PR"].isin(ids)
    diseno: dict = {}
    for j, c in enumerate(CONV_ORDEN):
        sub = val[val["conv"] == c].drop_duplicates("ID_PERSONA_PR")
        cats = sorted(sub["categoria"].unique())
        mapa = {k: i for i, k in enumerate(cats)}
        N_h = (sub["categoria"].value_counts().reindex(cats).to_numpy(float))
        ms = sub[sub["en_muestra"]]
        if ms.shape[0] < 30:
            diseno[str(CONV[c])] = {"error": "muestra insuficiente"}
            continue
        r = boot_diseno(ms["k"].to_numpy(),
                        ms["categoria"].map(mapa).to_numpy(), N_h,
                        pob_censada, rng)
        tasa_rep = r["replicas_conteos"] / pob_censada * 1e5
        lo = np.percentile(tasa_rep, 2.5, axis=0)
        hi = np.percentile(tasa_rep, 97.5, axis=0)
        mediana = np.median(r["replicas_conteos"], axis=0)
        # La referencia debe ser la tasa nacional DE ESA CONVOCATORIA, no la del
        # stock: el número de investigadores por 100 000 habitantes se multiplica
        # por ~2,6 entre 2013 y 2021, así que comparar 2013 contra la tasa del
        # stock marcaría como «distintos» departamentos que no lo son.
        nacional_c = float(conteo[j].sum() / pob_censada.sum() * 1e5)
        diseno[str(CONV[c])] = {
            "n_poblacion": int(sub.shape[0]), "n_muestra": int(ms.shape[0]),
            "fraccion_muestreo": float(ms.shape[0] / sub.shape[0]),
            "post_estratos": cats, "n_h": r["n_h"],
            "post_estratos_sin_muestra": r["post_estratos_sin_muestra"],
            "tasa_ic95": {"departamentos": etiq, "lo": lo.tolist(),
                          "hi": hi.tolist()},
            "ancho_ic_mediano_por_100000": float(np.median(hi - lo)),
            "tasa_nacional_de_la_convocatoria": nacional_c,
            "departamentos_estimados_en_cero": int((mediana == 0).sum()),
            "departamentos_que_no_difieren_del_promedio": int(
                ((lo <= nacional_c) & (hi >= nacional_c)).sum()),
            "gini_tasas_mediana": float(np.median(
                [gini(t) for t in tasa_rep])),
            "gini_tasas_ic95": [
                float(np.percentile([gini(t) for t in tasa_rep], 2.5)),
                float(np.percentile([gini(t) for t in tasa_rep], 97.5))],
        }
        d = diseno[str(CONV[c])]
        print(f"   bootstrap diseño {CONV[c]}: n={d['n_muestra']:,} de "
              f"{d['n_poblacion']:,} · ancho IC mediano="
              f"{d['ancho_ic_mediano_por_100000']:.1f} · deptos en 0="
              f"{d['departamentos_estimados_en_cero']} · sin diferencia del "
              f"promedio={d['departamentos_que_no_difieren_del_promedio']}"
              .replace(",", " "))
    salida["bootstrap_diseno_mas_ps"] = {
        "descripcion": ("Bootstrap dentro de post-estratos por categoría sobre "
                        "la muestra MAS (n = 2 224). Cuantifica qué podría "
                        "afirmarse por departamento contando solo con la "
                        "muestra."),
        "por_convocatoria": diseno,
    }

    # ---------------- robustez de denominador ----------------
    # OJO con dos cosas que NO son lo mismo:
    #   (a) invariancia de ESCALA: multiplicar TODAS las tasas por una misma
    #       constante deja Gini y Theil idénticos. Es una propiedad aritmética
    #       de los índices, y es lo que se comprueba aquí.
    #   (b) pasar de población censada a AJUSTADA por omisión NO es un factor
    #       común: la omisión censal es diferencial por departamento, así que
    #       cambia la desigualdad de verdad. Se reporta como análisis aparte.
    C = 137.0                       # constante común arbitraria
    taux = stock / pob_censada * 1e5
    inv_gini = abs(gini(taux) - gini(taux * C)) < 1e-12
    inv_theil = abs(theil_t(taux) - theil_t(taux * C)) < 1e-12
    tasa_aj18 = stock / proy_18 * 1e5
    j21 = CONV_ORDEN.index(21)
    t21_cens = conteo[j21] / pob_censada * 1e5
    t21_proy = conteo[j21] / proy_21 * 1e5
    salida["robustez_denominador"] = {
        "invariancia_de_escala": {
            "constante_comun": C,
            "gini_original": gini(taux), "gini_escalado": gini(taux * C),
            "theil_original": theil_t(taux), "theil_escalado": theil_t(taux * C),
            "nota": ("Gini y Theil son invariantes de escala. Por eso una "
                     "corrección de omisión UNIFORME (mismo factor para todos "
                     "los departamentos) NO alteraría la desigualdad medida, "
                     "solo el nivel de las tasas."),
        },
        "stock_con_poblacion_ajustada_2018": {
            "gini_tasas": gini(tasa_aj18), "theil_t_tasas": theil_t(tasa_aj18),
            "delta_gini_vs_censada": gini(tasa_aj18)
                                     - salida["indices_stock"]["gini_tasas"],
            "delta_theil_vs_censada": theil_t(tasa_aj18)
                                      - salida["indices_stock"]["theil_t_tasas"],
            "nota": ("La omisión del CNPV 2018 es DIFERENCIAL por departamento "
                     "(mayor en la periferia), así que este cambio no es un "
                     "factor común y sí mueve la desigualdad. Es la cota de "
                     "sensibilidad al denominador."),
        },
        "convocatoria_2021": {
            "tasa_nacional_censada_2018": float(conteo[j21].sum()
                                                / pob_censada.sum() * 1e5),
            "tasa_nacional_proyectada_2021": float(conteo[j21].sum()
                                                   / proy_21.sum() * 1e5),
            "gini_censada_2018": gini(t21_cens),
            "gini_proyectada_2021": gini(t21_proy),
            "theil_censada_2018": theil_t(t21_cens),
            "theil_proyectada_2021": theil_t(t21_proy),
            "nota": ("Denominador emparejado por año para la última "
                     "convocatoria: 2018 queda anacrónico para 2021."),
        },
        "invariancia_gini_verificada": bool(inv_gini),
        "invariancia_theil_verificada": bool(inv_theil),
    }

    # ---------------- comparación con el auditado ----------------
    # El auditado calcula el HHI sobre TODOS los registros, sin excluir
    # 'Exterior' ni 'No disponible': por eso usa `df` completo, no `val`.
    aud = pd.read_csv(AUDITADO / "territorial_hhi_por_convocatoria.csv",
                      encoding="utf-8-sig")
    con_ext, sin_ext, n_terr = [], [], []
    for c in CONV_ORDEN:
        vc = df.loc[df["conv"] == c, "NME_DEPARTAMENTO_RES_PR"].value_counts()
        con_ext.append(hhi(vc.to_numpy(float)))
        n_terr.append(int(vc.size))
        vc2 = vc.drop(labels=[k for k in EXCLUIDOS_DE_TASA if k in vc.index])
        sin_ext.append(hhi(vc2.to_numpy(float)))
    hhi_aud = aud["hhi"].to_numpy(float)
    dif = float(np.max(np.abs(np.array(con_ext) - hhi_aud)))
    salida["comparacion_auditado"] = {
        "hhi_auditado": {str(int(a)): float(v) for a, v in
                         zip(aud["ANO_CONVO_INT"], aud["hhi"])},
        "hhi_reproducido_con_exterior": {str(CONV[c]): float(v)
                                         for c, v in zip(CONV_ORDEN, con_ext)},
        "hhi_sin_exterior": {str(CONV[c]): float(v)
                             for c, v in zip(CONV_ORDEN, sin_ext)},
        "n_territorios_auditado": {str(int(a)): int(v) for a, v in
                                   zip(aud["ANO_CONVO_INT"],
                                       aud["n_territorios"])},
        "n_territorios_reproducido": {str(CONV[c]): n for c, n in
                                      zip(CONV_ORDEN, n_terr)},
        "maxima_diferencia_reproduccion": dif,
        "efecto_exterior_media_pp": float(np.mean(
            (np.array(con_ext) - np.array(sin_ext)) * 100)),
        "nota": ("El auditado llama «territorio» a 'Exterior' (2 132 registros) "
                 "y a 'No disponible' (316). Sus 29-34 «territorios» incluyen "
                 "categorías que no son departamentos de Colombia."),
        "tolerancia_reproduccion": ("El HHI publicado está redondeado a 6 "
                                    "decimales, así que coincidir dentro de 1e-6 "
                                    "es coincidir exactamente. La diferencia "
                                    "medida es la de ese redondeo."),
    }
    print(f"\n   HHI del auditado reproducido, máxima diferencia: {dif:.2e}")
    print(f"   territorios del auditado: "
          f"{[int(v) for v in aud['n_territorios']]} · reproducidos: {n_terr}")
    print(f"   efecto de contar 'Exterior' como territorio: "
          f"{salida['comparacion_auditado']['efecto_exterior_media_pp']:+.3f} pp "
          f"de HHI en promedio")

    # ---------------- validaciones ----------------
    salida["validaciones"] = {
        "suma_stock_igual_personas_con_territorio": bool(stock.sum() == len(ult)),
        "suma_conteos_igual_registros_con_territorio": bool(
            int(conteo.sum()) == len(val)),
        "poblacion_censada_suma_44_164_417": bool(
            int(pob_censada.sum()) == 44164417),
        "poblacion_ajustada_suma_48_258_494": bool(
            int(proy_18.sum()) == 48258494),
        "hhi_auditado_reproducido": bool(dif <= 1e-6),
        "invariancia_escala_gini_theil": bool(inv_gini and inv_theil),
        "todos_los_departamentos_con_poblacion": bool((pob_censada > 0).all()),
        "descomposicion_theil_cierra": bool(abs(
            des_stock["total"] - des_stock["suma_dentro_entre"]) < 1e-12),
    }
    for k, v in salida["validaciones"].items():
        print(f"   [{'OK ' if v else 'NO '}] {k}")

    # ---------------- figuras ----------------
    GRAF.mkdir(parents=True, exist_ok=True)
    bs = boot["stock"]
    fig_tasas(etiq, tasa_stock, np.array(bs["tasa_ic95"]["lo"]),
              np.array(bs["tasa_ic95"]["hi"]), pob_censada,
              GRAF / "f2_2_tasa_por_100000.png")
    anios = [CONV[c] for c in CONV_ORDEN]
    fig_evolucion(anios, {
        "hhi_cuotas": [float(v) for v in sin_ext],
        "gini_tasas": [por_conv[str(a)]["gini_tasas"] for a in anios],
        "theil_tasas": [por_conv[str(a)]["theil_t_tasas"] for a in anios],
    }, GRAF / "f2_2_evolucion_concentracion.png")
    fig_cuota_vs_poblacion(sh_inv, sh_pob, etiq,
                           GRAF / "f2_2_cuota_vs_poblacion.png")
    fig_theil(anios,
              [por_conv[str(a)]["theil_tasas_dentro_regiones"] for a in anios],
              [por_conv[str(a)]["theil_tasas_entre_regiones"] for a in anios],
              GRAF / "f2_2_theil_descomposicion.png")
    salida["figuras"] = sorted(p.name for p in GRAF.glob("*.png"))

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"\n-> {SALIDA.relative_to(RAIZ)} ({SALIDA.stat().st_size:,} bytes)")
    print(f"-> {GRAF.relative_to(RAIZ)}/ ({len(salida['figuras'])} figuras)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
