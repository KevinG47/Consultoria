"""Analisis longitudinal del padron de investigadores reconocidos (MinCiencias).

Objetivo 2 del anteproyecto: dinamica longitudinal del reconocimiento.

Diseno: Muestreo Aleatorio Simple (MAS) sobre PERSONAS (no registros), sin
reemplazo, con semilla fija 2026. Se recogen despues TODOS los registros de las
personas seleccionadas en TODAS las convocatorias (panel completo).

Fundamento del tamano de muestra: Cochran (1977), formula para proporcion con
p=0.5 y correccion por poblacion finita.

Uso:
    python analisis_longitudinal.py                # solo analisis
    python analisis_longitudinal.py --json out.json

No modifica el archivo de entrada ni el repositorio auditado.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# --------------------------------------------------------------------------
# Rutas y constantes
# --------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parents[2]
CSV = RAIZ / "Datos" / "Investigadores_Reconocidos_por_convocatoria_20261006.csv"
DIR_SALIDA = RAIZ / "documentacion_auditoria" / "data" / "memoria"
DIR_GRAFICAS = DIR_SALIDA / "graficas_longitudinal"

Z = 1.96          # 95% de confianza
P = 0.5           # maxima varianza
E = 0.02          # margen de error +/- 2%
SEMILLA = 2026
CHUNK = 50_000

# Orden cronologico de las convocatorias (ID -> anio del nombre de la convocatoria)
CONV_ANIO = {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021}
CONV_ORDEN = [16, 17, 18, 19, 20, 21]
CATEGORIAS = ["Investigador Junior", "Investigador Asociado",
              "Investigador Sénior", "Investigador Emérito"]
CAT_CORTO = {"Investigador Junior": "Junior", "Investigador Asociado": "Asociado",
             "Investigador Sénior": "Sénior", "Investigador Emérito": "Emérito"}
RANGO_CAT = {c: i for i, c in enumerate(CATEGORIAS)}
TOP5_DEPTO = ["Bogotá, D. C.", "Antioquia", "Valle del Cauca",
              "Atlántico", "Santander"]
FUENTE = ("Fuente: datos.gov.co, dataset bqtm-4y2h — Investigadores reconocidos por "
          "convocatoria (77 237 registros, 30 086 personas).")

COL_PERSONA = "ID_PERSONA_PR"
COL_CAT = "NME_CLASIFICACION_PR"
COL_GENERO = "NME_GENERO_PR"
COL_AREA = "NME_GRAN_AREA_PR"
COL_NIVEL = "NME_NIV_FORM_PR"
COL_DEPTO = "NME_DEPARTAMENTO_RES_PR"

EJE_GENERO = (COL_GENERO, None)
EJE_DEPTO = (COL_DEPTO, TOP5_DEPTO)
EJE_AREA = (COL_AREA, None)
EJE_NIVEL = (COL_NIVEL, None)

# La consola de Windows usa cp1252: sin esto, imprimir "→" o tildes falla.
for _flujo in (sys.stdout, sys.stderr):
    if hasattr(_flujo, "reconfigure"):
        _flujo.reconfigure(encoding="utf-8", errors="replace")

VERDE, AZUL, ROJO, NARANJA, GRIS = "#2E7D5B", "#1F5C99", "#B3382C", "#D98A1F", "#6B6B6B"
plt.rcParams.update({"figure.dpi": 130, "font.size": 10, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.spines.top": False,
                     "axes.spines.right": False})


# --------------------------------------------------------------------------
# 1. Carga
# --------------------------------------------------------------------------

def cargar() -> pd.DataFrame:
    """Lee el CSV completo por trozos, sin coercion silenciosa de tipos."""
    partes = []
    for trozo in pd.read_csv(CSV, dtype=str, keep_default_na=False,
                             chunksize=CHUNK, encoding="utf-8"):
        partes.append(trozo)
    df = pd.concat(partes, ignore_index=True)
    df["_conv"] = df["ID_CONVOCATORIA"].astype(int)
    df["_anio"] = df["_conv"].map(CONV_ANIO)
    return df


# --------------------------------------------------------------------------
# 2. Tamano de muestra (Cochran 1977) con ajuste por poblacion finita
# --------------------------------------------------------------------------

def tamano_muestra(N: int, z: float = Z, p: float = P, e: float = E) -> dict:
    n0 = z ** 2 * p * (1 - p) / e ** 2
    n_aj = n0 / (1 + (n0 - 1) / N)
    return {
        "N": N, "z": z, "p": p, "e": e,
        "n0": n0,
        "n_ajustado_exacto": n_aj,
        "n_final": math.ceil(n_aj),
        "fraccion_muestreo": math.ceil(n_aj) / N,
        "error_efectivo_sin_fpc": z * math.sqrt(p * (1 - p) / math.ceil(n_aj)),
        "error_efectivo_con_fpc": z * math.sqrt(p * (1 - p) / math.ceil(n_aj))
                                  * math.sqrt((N - math.ceil(n_aj)) / (N - 1)),
    }


def seleccionar(ids: list[str], n: int, semilla: int) -> list[str]:
    """MAS sin reemplazo sobre el marco ordenado (reproducible bit a bit)."""
    marco = sorted(ids)
    rng = np.random.default_rng(semilla)
    posiciones = np.sort(rng.choice(len(marco), size=n, replace=False))
    return [marco[i] for i in posiciones]


# --------------------------------------------------------------------------
# 3. Estimadores
# --------------------------------------------------------------------------

def ic_proporcion(x: int, n: int, N: int | None = None,
                  z: float = Z) -> dict:
    """IC 95% de una proporcion.

    Metodo principal: Wald (el solicitado). Se anade Wilson (mas estable cerca
    de 0 y 1) y, si se conoce N, la version con correccion por poblacion finita.
    """
    if n == 0:
        return {"n": 0, "p": None, "ic_wald": (None, None),
                "ic_wilson": (None, None), "ic_wald_fpc": (None, None)}
    p = x / n
    se = math.sqrt(p * (1 - p) / n)
    wald = (max(0.0, p - z * se), min(1.0, p + z * se))
    # Wilson (score)
    den = 1 + z ** 2 / n
    centro = (p + z ** 2 / (2 * n)) / den
    mitad = z * math.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / den
    wilson = (max(0.0, centro - mitad), min(1.0, centro + mitad))
    if N:
        se_fpc = se * math.sqrt((N - n) / (N - 1))
        wald_fpc = (max(0.0, p - z * se_fpc), min(1.0, p + z * se_fpc))
    else:
        wald_fpc = (None, None)
    return {"n": n, "x": x, "p": p, "ic_wald": wald, "ic_wilson": wilson,
            "ic_wald_fpc": wald_fpc}


def anualizada(p: float, anios: int) -> float | None:
    """Tasa anualizada: 1-(1-p)^(1/anios). Supone riesgo constante."""
    if p is None or p >= 1:
        return None
    return 1 - (1 - p) ** (1 / anios)


# --------------------------------------------------------------------------
# 4. Analisis longitudinal
# --------------------------------------------------------------------------

def presencia(panel: pd.DataFrame) -> dict[int, set[str]]:
    return {c: set(panel.loc[panel["_conv"] == c, COL_PERSONA])
            for c in CONV_ORDEN}


def categoria_por_persona(panel: pd.DataFrame) -> dict[int, pd.Series]:
    """Categoria de cada persona en cada convocatoria (clave unica verificada)."""
    return {c: panel.loc[panel["_conv"] == c]
                   .set_index(COL_PERSONA)[COL_CAT]
            for c in CONV_ORDEN}


def fechas_convocatoria(df: pd.DataFrame) -> tuple[dict, dict]:
    """Fecha unica registrada en ANO_CONVO por convocatoria y intervalos reales.

    Las convocatorias NO distan lo que sugiere su anio nominal: la rotulada
    "833 de 2018" esta fechada el 06/12/2019, de modo que el hueco 2017->2019
    dura 2.57 anios y el 2019->2021 solo 1.22. Se mide, no se supone.
    """
    f = {}
    for c in CONV_ORDEN:
        vals = df.loc[df["_conv"] == c, "ANO_CONVO"].unique()
        assert len(vals) == 1, f"convocatoria {c}: {len(vals)} fechas distintas"
        f[c] = datetime.strptime(str(vals[0]), "%d/%m/%Y").date()
    inter = {a: (f[b] - f[a]).days / 365.25
             for a, b in zip(CONV_ORDEN[:-1], CONV_ORDEN[1:])}
    return f, inter


def pares(panel: pd.DataFrame, N: int | None,
          anios_reales: dict | None = None) -> list[dict]:
    pres = presencia(panel)
    res = []
    for a, b in zip(CONV_ORDEN[:-1], CONV_ORDEN[1:]):
        A, B = pres[a], pres[b]
        ret, sal, ent = A & B, A - B, B - A
        # Reingresos: personas de B que ya estaban en alguna convocatoria ANTERIOR
        # a 'a'. No son entradas nuevas en sentido estricto.
        previos: set = set()
        for c in CONV_ORDEN:
            if c < a:
                previos |= pres[c]
        reingresos = len(ent & previos)
        # Salidas: temporal = reaparece despues de t2; definitiva = no reaparece.
        posteriores: set = set()
        for c in CONV_ORDEN:
            if c > b:
                posteriores |= pres[c]
        sal_temporal = len(sal & posteriores)
        anios = CONV_ANIO[b] - CONV_ANIO[a]
        ar = float((anios_reales or {}).get(a, anios))
        r = ic_proporcion(len(ret), len(A), N)
        s = ic_proporcion(len(sal), len(A), N)
        e_ = ic_proporcion(len(ent), len(B), N)
        res.append({
            "par": f"{CONV_ANIO[a]}→{CONV_ANIO[b]}",
            "conv_a": a, "conv_b": b, "anios": anios,
            "anios_reales": round(ar, 4),
            "n_a": len(A), "n_b": len(B),
            "retenidos": len(ret), "salidas": len(sal), "entradas": len(ent),
            "entradas_nuevas_reales": len(ent) - reingresos,
            "reingresos": reingresos,
            "pct_reingresos_sobre_entradas": (100 * reingresos / len(ent)) if ent else None,
            "salidas_temporales": sal_temporal,
            "salidas_definitivas": len(sal) - sal_temporal,
            "ventana_posterior_convocatorias": [CONV_ANIO[c] for c in CONV_ORDEN
                                                if c > b],
            "salidas_censuradas_derecha": not posteriores,
            # la suma de retenidos y entradas reconstruye el tamano de B
            "cierre": len(ret) + len(ent) == len(B),
            "retencion": r, "salida": s, "entrada": e_,
            "crecimiento_neto": len(ent) - len(sal),
            "retencion_anualizada": anualizada(r["p"], anios),
            "retencion_anualizada_real": anualizada(r["p"], ar),
            "salida_anualizada": anualizada(s["p"], anios),
            "salida_anualizada_real": anualizada(s["p"], ar),
        })
    return res


def matrices_transicion(panel: pd.DataFrame) -> dict[str, dict]:
    cats = categoria_por_persona(panel)
    out = {}
    for a, b in zip(CONV_ORDEN[:-1], CONV_ORDEN[1:]):
        comunes = sorted(set(cats[a].index) & set(cats[b].index))
        m = pd.DataFrame(0, index=CATEGORIAS, columns=CATEGORIAS, dtype=int)
        if comunes:
            pares_cat = pd.DataFrame({
                "origen": cats[a].loc[comunes].values,
                "destino": cats[b].loc[comunes].values,
            })
            conteo = pares_cat.groupby(["origen", "destino"], observed=True).size()
            for (o, d), v in conteo.items():
                m.loc[o, d] = int(v)
        filas = m.sum(axis=1)
        pct = m.div(filas.replace(0, np.nan), axis=0) * 100
        diag = int(np.trace(m.values))
        # CATEGORIAS esta ordenada de menor a mayor jerarquia (Junior -> Emerito)
        ascend = int(sum(m.values[i, j] for i in range(4) for j in range(i + 1, 4)))
        descen = int(sum(m.values[i, j] for i in range(4) for j in range(i)))
        out[f"{CONV_ANIO[a]}→{CONV_ANIO[b]}"] = {
            "conteos": m.to_dict(),
            "porcentajes_fila": pct.round(2).to_dict(),
            "totales_fila": filas.to_dict(),
            "n_transiciones": int(filas.sum()),
            "misma_categoria": diag,
            "ascienden": ascend,
            "descienden": descen,
            "tasa_permanencia": diag / int(filas.sum()) if filas.sum() else None,
        }
    return out


def retencion_por_grupo(panel: pd.DataFrame, col: str, a: int, b: int,
                        top: int | None = None,
                        solo: list | None = None) -> dict:
    """Retencion por grupo + chi-cuadrado de homogeneidad.

    `top` conserva los k grupos mas numerosos; `solo` fija una lista de grupos
    (necesario para comparar el MISMO conjunto de grupos entre pares).
    """
    ca = panel.loc[panel["_conv"] == a, [COL_PERSONA, col]]
    cb = panel.loc[panel["_conv"] == b, [COL_PERSONA, col]]
    universo = set(ca[COL_PERSONA])
    base = ca[ca[COL_PERSONA].isin(universo)].copy()
    base["ret"] = base[COL_PERSONA].isin(set(cb[COL_PERSONA])).astype(int)
    if solo is not None:
        base = base[base[col].isin(solo)]
    elif top:
        keep = base[col].value_counts().head(top).index.tolist()
        base = base[base[col].isin(keep)]
    g = base.groupby(col, observed=True)["ret"].agg(["sum", "size"])
    g = g[g["size"] > 0].sort_values("size", ascending=False)
    detalle = {}
    for k, fila in g.iterrows():
        ic = ic_proporcion(int(fila["sum"]), int(fila["size"]))
        detalle[str(k)] = {"n": int(fila["size"]), "retenidos": int(fila["sum"]),
                           "tasa": ic["p"], "ic_wald": ic["ic_wald"]}
    # chi-cuadrado de homogeneidad sobre la tabla 2 x k
    tabla = np.array([[int(f["sum"]), int(f["size"] - f["sum"])]
                      for _, f in g.iterrows()])
    chi2 = pval = gl = None
    min_esp = None
    if tabla.shape[0] >= 2:
        chi2, pval, gl, esp = stats.chi2_contingency(tabla, correction=False)
        chi2, pval, gl = float(chi2), float(pval), int(gl)
        min_esp = float(esp.min())
    return {"variable": col, "convocatorias": f"{CONV_ANIO[a]}→{CONV_ANIO[b]}",
            "grupos": detalle, "chi2": chi2, "p_valor": pval, "gl": gl,
            "min_esperado": min_esp,
            "supuesto_frecuencias_ok": (min_esp is not None and min_esp >= 5)}


def tabla_desagregada(panel: pd.DataFrame, col: str, solo: list | None = None) -> dict:
    """Retencion por grupo para TODOS los pares de convocatorias consecutivas."""
    return {f"{CONV_ANIO[a]}→{CONV_ANIO[b]}": retencion_por_grupo(panel, col, a, b, solo=solo)
            for a, b in zip(CONV_ORDEN[:-1], CONV_ORDEN[1:])}


def transiciones_por_grupo(panel: pd.DataFrame, col: str, a: int, b: int,
                           solo: list | None = None) -> dict:
    """Composicion de las transiciones (permanece/asciende/desciende) por grupo."""
    ca = panel.loc[panel["_conv"] == a].set_index(COL_PERSONA)[[COL_CAT, col]]
    cb = panel.loc[panel["_conv"] == b].set_index(COL_PERSONA)[COL_CAT]
    comunes = ca.index.intersection(cb.index)
    d = pd.DataFrame({"origen": ca.loc[comunes, COL_CAT].values,
                      "destino": cb.loc[comunes].values,
                      "grupo": ca.loc[comunes, col].values})
    ro, rd = d["origen"].map(RANGO_CAT), d["destino"].map(RANGO_CAT)
    d["mov"] = np.where(ro == rd, "permanece",
                        np.where(ro < rd, "asciende", "desciende"))
    if solo is not None:
        d = d[d["grupo"].isin(solo)]
    g = (d.groupby(["grupo", "mov"], observed=True).size()
          .unstack(fill_value=0)
          .reindex(columns=["permanece", "asciende", "desciende"], fill_value=0))
    g["n"] = g.sum(axis=1)
    detalle = {}
    for k, fila in g.iterrows():
        n = int(fila["n"])
        detalle[str(k)] = {c: int(fila[c]) for c in ["permanece", "asciende", "desciende"]}
        detalle[str(k)]["n"] = n
        for c in ["permanece", "asciende", "desciende"]:
            detalle[str(k)][f"pct_{c}"] = (100 * fila[c] / n) if n else None
    chi2 = pval = gl = min_esp = None
    tabla = g[["permanece", "asciende", "desciende"]].values
    if tabla.shape[0] >= 2 and tabla.sum() > 0:
        chi2, pval, gl, esp = stats.chi2_contingency(tabla, correction=False)
        chi2, pval, gl, min_esp = float(chi2), float(pval), int(gl), float(esp.min())
    return {"variable": col, "convocatorias": f"{CONV_ANIO[a]}→{CONV_ANIO[b]}",
            "grupos": detalle, "chi2": chi2, "p_valor": pval, "gl": gl,
            "min_esperado": min_esp,
            "supuesto_frecuencias_ok": (min_esp is not None and min_esp >= 5)}


def emerito_absorbente(panel: pd.DataFrame) -> dict:
    """Verifica si 'Investigador Emérito' es un estado terminal.

    Para cada par consecutivo se cuenta cuantas personas clasificadas como
    Emerito en t1 vuelven a aparecer en t2. Si el total es 0, la categoria es
    absorbente: nadie sale de ella porque nadie vuelve.
    """
    pres = presencia(panel)
    cat = categoria_por_persona(panel)
    detalle = []
    for a, b in zip(CONV_ORDEN[:-1], CONV_ORDEN[1:]):
        em = {i for i, c in cat[a].items() if c == "Investigador Emérito"}
        vuelven = len(em & pres[b])
        detalle.append({"par": f"{CONV_ANIO[a]}→{CONV_ANIO[b]}",
                        "emeritos_t1": len(em), "vuelven_t2": vuelven,
                        "retorno": vuelven / len(em) if em else None})
    tot = sum(x["emeritos_t1"] for x in detalle)
    vue = sum(x["vuelven_t2"] for x in detalle)
    return {"detalle": detalle, "oportunidades": tot, "retornos": vue,
            "tasa_retorno": vue / tot if tot else None,
            "absorbente": vue == 0}


def presencia_personas(panel: pd.DataFrame) -> dict:
    """En cuantas convocatorias aparece cada persona."""
    n = panel.groupby(COL_PERSONA, observed=True)["_conv"].nunique().value_counts()
    tot = int(n.sum())
    return {str(int(k)): {"personas": int(v), "pct": 100 * v / tot}
            for k, v in sorted(n.items())}


def genero_inconsistente(panel: pd.DataFrame) -> dict:
    """Personas cuyo genero declarado cambia entre convocatorias."""
    g = panel.groupby(COL_PERSONA, observed=True)[COL_GENERO].nunique()
    ids = set(g[g > 1].index)
    sub = panel[panel[COL_PERSONA].isin(ids)].sort_values("_conv")
    combos = (sub.groupby(COL_PERSONA, observed=True)[COL_GENERO]
                 .apply(lambda x: " -> ".join(dict.fromkeys(x))))
    return {"personas": len(ids),
            "pct_personas": 100 * len(ids) / panel[COL_PERSONA].nunique(),
            "patrones": combos.value_counts().to_dict()}


def comparar_poblacion(pob: pd.Series, mue: pd.Series) -> dict:
    """Distribucion poblacion vs muestra + chi-cuadrado de bondad de ajuste."""
    pp = pob.value_counts(normalize=True)
    mp = mue.value_counts(normalize=True)
    categorias = sorted(set(pp.index) | set(mp.index))
    obs = np.array([int((mue == c).sum()) for c in categorias], dtype=float)
    esp = np.array([pp.get(c, 0.0) * len(mue) for c in categorias], dtype=float)
    # Se descartan categorias con esperado nulo y se renormaliza el esperado al
    # total observado: la muestra puede no contener categorias muy raras.
    ok = esp > 1e-9
    chi2 = pval = min_esp = None
    if ok.sum() >= 2:
        esp_ok = esp[ok] * (obs[ok].sum() / esp[ok].sum())
        chi2, pval = stats.chisquare(obs[ok], esp_ok)
        chi2, pval, min_esp = float(chi2), float(pval), float(esp_ok.min())
    dif = {str(c): {"poblacion_pct": 100 * pp.get(c, 0.0),
                    "muestra_pct": 100 * mp.get(c, 0.0),
                    "diferencia_pp": 100 * (mp.get(c, 0.0) - pp.get(c, 0.0))}
           for c in categorias}
    return {"categorias": dif, "chi2": chi2, "p_valor": pval,
            "gl": int(ok.sum() - 1) if ok.sum() >= 2 else None,
            "min_esperado": min_esp,
            "supuesto_frecuencias_ok": (min_esp is not None and min_esp >= 5),
            "max_diferencia_pp": max(abs(v["diferencia_pp"]) for v in dif.values())}


# --------------------------------------------------------------------------
# 5. Graficas
# --------------------------------------------------------------------------

def _fuente(ax, extra: str = "") -> None:
    ax.figure.text(0.01, 0.005, FUENTE + ((" " + extra) if extra else ""),
                   fontsize=6.6, color="#555555", ha="left", va="bottom")


def graf_barras_pares(pares_s: list[dict], ruta: Path) -> None:
    etiquetas = [f"{p['par']}\n({p['anios']} año{'s' if p['anios'] > 1 else ''})"
                 for p in pares_s]
    x = np.arange(len(pares_s))
    ancho = 0.26
    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    for i, (clave, color, titulo) in enumerate([
            ("retencion", VERDE, "Retenidos"),
            ("salida", ROJO, "Salidas"),
            ("entrada", AZUL, "Entradas nuevas")]):
        vals = [100 * pr[clave]["p"] for pr in pares_s]
        ax.bar(x + (i - 1) * ancho, vals, ancho, label=titulo, color=color)
        for xi, v in zip(x + (i - 1) * ancho, vals):
            ax.text(xi, v + 0.6, f"{v:.1f}", ha="center", fontsize=7.6)
    ax.set_xticks(x)
    ax.set_xticklabels(etiquetas)
    ax.set_ylabel("Porcentaje (%)")
    n2013 = pares_s[0]["n_a"]
    ax.set_title("Retención, salidas y entradas nuevas por par de convocatorias\n"
                 f"Muestra aleatoria simple de personas (n = {n2013} en 2013)")
    ax.legend(frameon=False, ncol=3)
    _fuente(ax)
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.savefig(ruta, bbox_inches="tight")
    plt.close(fig)


def graf_heatmaps(tm: dict, claves: list[str], ruta: Path) -> None:
    cortos = [CAT_CORTO[c] for c in CATEGORIAS]
    fig, axes = plt.subplots(1, len(claves), figsize=(6.0 * len(claves), 5.2))
    if len(claves) == 1:
        axes = [axes]
    for ax, k in zip(axes, claves):
        m = pd.DataFrame(tm[k]["conteos"]).reindex(index=CATEGORIAS,
                                                   columns=CATEGORIAS).fillna(0)
        pct = pd.DataFrame(tm[k]["porcentajes_fila"]).reindex(
            index=CATEGORIAS, columns=CATEGORIAS)
        im = ax.imshow(m.values, cmap="Blues", vmin=0, vmax=m.values.max())
        ax.set_xticks(range(4), cortos, rotation=30, ha="right")
        ax.set_yticks(range(4), cortos)
        ax.set_xlabel("Categoría en la 2.ª convocatoria")
        ax.set_ylabel("Categoría en la 1.ª convocatoria")
        ax.set_title(f"Transiciones de categoría {k}")
        ax.grid(False)
        for i in range(4):
            for j in range(4):
                v = int(m.values[i, j])
                p = pct.values[i, j]
                txt = f"{v}\n({p:.1f}%)" if not np.isnan(p) else f"{v}\n(—)"
                ax.text(j, i, txt, ha="center", va="center", fontsize=8.4,
                        color="white" if v > 0.6 * m.values.max() else "#1a1a1a")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03, label="Personas")
    fig.suptitle("Matriz de transición de categorías — número de personas y "
                 "% sobre el total de la categoría de origen", fontsize=11)
    _fuente(axes[0])
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(ruta, bbox_inches="tight")
    plt.close(fig)


def graf_poblacion(serie: dict[int, int], ruta: Path, unidad: str) -> None:
    x = [CONV_ANIO[c] for c in CONV_ORDEN]
    y = [serie[c] for c in CONV_ORDEN]
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    ax.plot(x, y, marker="o", color=AZUL, linewidth=2, markersize=7)
    for xi, yi in zip(x, y):
        ax.annotate(f"{yi:,}".replace(",", " "), (xi, yi), textcoords="offset points",
                    xytext=(0, 9), ha="center", fontsize=8.6)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{a}\nconv. {c}" for a, c in zip(x, CONV_ORDEN)])
    ax.set_ylabel(f"Personas reconocidas ({unidad})")
    ax.set_xlabel("Convocatoria (fecha de la convocatoria)")
    ax.set_title("Evolución del número de personas reconocidas por convocatoria\n"
                 "Las convocatorias no son anuales (intervalos de 1 y 2 años)")
    ax.set_ylim(0, max(y) * 1.15)
    _fuente(ax)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(ruta, bbox_inches="tight")
    plt.close(fig)


def graf_retencion_grupos(gen: dict, area: dict, ruta: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.0))
    for ax, datos, titulo in [
            (axes[0], gen, "Retención por género (2019→2021)"),
            (axes[1], area, "Retención por gran área de conocimiento (2019→2021)")]:
        nombres = list(datos["grupos"].keys())
        tasas = [100 * datos["grupos"][k]["tasa"] for k in nombres]
        ns = [datos["grupos"][k]["n"] for k in nombres]
        err = []
        for k in nombres:
            lo, hi = datos["grupos"][k]["ic_wald"]
            err.append(100 * (hi - datos["grupos"][k]["tasa"]))
        y = np.arange(len(nombres))
        colores = [VERDE if i % 2 == 0 else AZUL for i in range(len(nombres))]
        ax.barh(y, tasas, xerr=err, color=colores, capsize=3)
        ax.set_yticks(y, [f"{n}\n(n={v})" for n, v in zip(nombres, ns)], fontsize=8.2)
        ax.invert_yaxis()
        ax.set_xlabel("Tasa de retención (%) con IC 95%")
        ax.set_xlim(0, 100)
        ax.set_title(titulo, fontsize=10)
        for yi, t in zip(y, tasas):
            ax.text(t + 1.4, yi, f"{t:.1f}", va="center", fontsize=8)
    fig.suptitle("Retención por subgrupos — muestra MAS de personas", fontsize=11)
    _fuente(axes[0])
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    fig.savefig(ruta, bbox_inches="tight")
    plt.close(fig)


def graf_anualizada(pares_s: list[dict], ruta: Path) -> None:
    etiquetas = [f"{p['par']}\n{p['anios_reales']:.2f} años reales"
                 for p in pares_s]
    crudas = [100 * p["retencion"]["p"] for p in pares_s]
    an_nom = [100 * p["retencion_anualizada"] for p in pares_s]
    an_real = [100 * p["retencion_anualizada_real"] for p in pares_s]
    x = np.arange(len(pares_s))
    fig, ax = plt.subplots(figsize=(10.2, 5.2))
    ax.bar(x - 0.27, crudas, 0.27, label="Retención observada en el intervalo",
           color=GRIS)
    ax.bar(x, an_nom, 0.27, label="Anualizada con años nominales (1, 1, 2, 2, 2)",
           color=NARANJA)
    ax.bar(x + 0.27, an_real, 0.27,
           label="Anualizada con años reales medidos en ANO_CONVO", color=ROJO)
    for xi, v in zip(x - 0.27, crudas):
        ax.text(xi, v + 0.7, f"{v:.1f}", ha="center", fontsize=7.4)
    for xi, v in zip(x, an_nom):
        ax.text(xi, v + 0.7, f"{v:.1f}", ha="center", fontsize=7.4)
    for xi, v in zip(x + 0.27, an_real):
        ax.text(xi, v + 0.7, f"{v:.1f}", ha="center", fontsize=7.4)
    ax.set_xticks(x, etiquetas, fontsize=8)
    ax.set_ylabel("Porcentaje (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Retención observada vs. tasa anualizada de retención\n"
                 "Anualizar con las fechas reales de ANO_CONVO cambia el orden de los pares")
    ax.legend(frameon=False, fontsize=8)
    _fuente(ax)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(ruta, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# 6. Principal
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=str(DIR_SALIDA / "longitudinal_resultados.json"))
    args = ap.parse_args()

    DIR_GRAFICAS.mkdir(parents=True, exist_ok=True)
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)

    print("== Carga ==")
    df = cargar()
    print(f"   registros={len(df):,}  personas={df[COL_PERSONA].nunique():,}"
          .replace(",", " "))

    ids_unicos = sorted(df[COL_PERSONA].unique())
    N = len(ids_unicos)

    # ---- Tarea 1 -------------------------------------------------------
    tm = tamano_muestra(N)
    print("\n== Tarea 1: tamano de muestra (Cochran 1977) ==")
    print(f"   N={N}  Z={Z}  p={P}  e={E}")
    print(f"   n0={tm['n0']:.4f}   n ajustado={tm['n_ajustado_exacto']:.4f}"
          f"   n final={tm['n_final']}")
    print(f"   fraccion de muestreo={100*tm['fraccion_muestreo']:.2f}%"
          f"   error efectivo (con fpc)={100*tm['error_efectivo_con_fpc']:.2f} pp")

    # ---- Tarea 2 -------------------------------------------------------
    muestra_ids = seleccionar(ids_unicos, tm["n_final"], SEMILLA)
    muestra_set = set(muestra_ids)
    mues = df[df[COL_PERSONA].isin(muestra_set)].copy()
    print("\n== Tarea 2: muestreo MAS ==")
    print(f"   personas en la muestra={len(muestra_ids)}"
          f"   registros={len(mues)}  media registros/persona={len(mues)/len(muestra_ids):.3f}")
    dist_conv = {int(c): int((mues["_conv"] == c).sum()) for c in CONV_ORDEN}

    # personas por convocatoria
    pers_conv_pob = {c: int(df.loc[df['_conv'] == c, COL_PERSONA].nunique())
                     for c in CONV_ORDEN}
    pers_conv_mue = {c: int(mues.loc[mues['_conv'] == c, COL_PERSONA].nunique())
                     for c in CONV_ORDEN}
    print("   personas por convocatoria (muestra):",
          {CONV_ANIO[c]: pers_conv_mue[c] for c in CONV_ORDEN})

    # ---- Perfil a nivel persona (regla: ultima convocatoria observada) --
    def perfil(d: pd.DataFrame) -> pd.DataFrame:
        return (d.sort_values("_conv")
                 .groupby(COL_PERSONA, observed=True)
                 .last()[[COL_GENERO, COL_CAT, COL_AREA, COL_NIVEL, COL_DEPTO]])

    perfil_pob = perfil(df)
    perfil_mue = perfil(mues)

    print("\n== Hallazgos de calidad del registro ==")
    abs_eme = emerito_absorbente(df)
    print(f"   Emerito como estado absorbente: {abs_eme['retornos']}/"
          f"{abs_eme['oportunidades']} retornos -> absorbente={abs_eme['absorbente']}")
    pres_pers = presencia_personas(df)
    print("   personas por numero de convocatorias: "
          + ", ".join(f"{k}:{v['personas']}" for k, v in pres_pers.items()))
    gin = genero_inconsistente(df)
    print(f"   genero inconsistente: {gin['personas']} personas "
          f"({gin['pct_personas']:.2f}%) patrones={gin['patrones']}")
    eme_conv = {str(CONV_ANIO[c]): int(((df["_conv"] == c)
                 & (df[COL_CAT] == "Investigador Emérito")).sum()) for c in CONV_ORDEN}

    # ---- Tarea 3 -------------------------------------------------------
    print("\n== Tarea 3: representatividad ==")
    rep = {}
    for nombre, col in [("genero", COL_GENERO), ("categoria", COL_CAT),
                        ("gran_area", COL_AREA), ("departamento", COL_DEPTO),
                        ("nivel_formacion", COL_NIVEL)]:
        rep[nombre] = comparar_poblacion(perfil_pob[col], perfil_mue[col])
        r = rep[nombre]
        print(f"   {nombre:16s} chi2={r['chi2']:.3f}  gl={r['gl']}  p={r['p_valor']:.4f}"
              f"  max dif={r['max_diferencia_pp']:.3f} pp")

    # ---- Tarea 4 -------------------------------------------------------
    print("\n== Tarea 4: retencion, entradas y salidas ==")
    fechas_conv, inter_reales = fechas_convocatoria(df)
    for c in CONV_ORDEN:
        print(f"   conv {c}: fecha unica ANO_CONVO={fechas_conv[c]}")
    for a, v in inter_reales.items():
        print(f"   intervalo {CONV_ANIO[a]}->{CONV_ANIO[a + 1]}: {v:.4f} anios reales "
              f"(nominal {CONV_ANIO[a + 1] - CONV_ANIO[a]})")
    pares_mue = pares(mues, N, inter_reales)
    pares_pob = pares(df, None, inter_reales)
    for pm, pp_ in zip(pares_mue, pares_pob):
        print(f"   {pm['par']} ({pm['anios']} años, muestra n={pm['n_a']}): "
              f"retención={100*pm['retencion']['p']:.2f}% "
              f"IC[{100*pm['retencion']['ic_wald'][0]:.2f},{100*pm['retencion']['ic_wald'][1]:.2f}]"
              f" | universo={100*pp_['retencion']['p']:.2f}%"
              f" | anualizada nominal={100*pm['retencion_anualizada']:.2f}%"
              f" | anualizada real={100*pm['retencion_anualizada_real']:.2f}%")
    # retencion global 2013->2021
    A = set(mues.loc[mues["_conv"] == 16, COL_PERSONA])
    B = set(mues.loc[mues["_conv"] == 21, COL_PERSONA])
    glob = ic_proporcion(len(A & B), len(A), N)
    A0 = set(df.loc[df["_conv"] == 16, COL_PERSONA])
    B0 = set(df.loc[df["_conv"] == 21, COL_PERSONA])
    glob_pob = len(A0 & B0) / len(A0)
    print(f"   retención global 2013→2021 (muestra): {100*glob['p']:.2f}% "
          f"IC[{100*glob['ic_wald'][0]:.2f},{100*glob['ic_wald'][1]:.2f}]"
          f"  | universo={100*glob_pob:.2f}%")

    # ---- Tarea 5 -------------------------------------------------------
    print("\n== Tarea 5: transiciones de categoria ==")
    tm_mue = matrices_transicion(mues)
    tm_pob = matrices_transicion(df)
    for k, v in tm_mue.items():
        print(f"   {k}: n={v['n_transiciones']}  permanecen={v['misma_categoria']}"
              f" ({100*v['tasa_permanencia']:.1f}%)  suben={v['ascienden']}"
              f"  bajan={v['descienden']}  | universo permanecen="
              f"{100*tm_pob[k]['tasa_permanencia']:.1f}%")

    # ---- Tarea 6 -------------------------------------------------------
    print("\n== Tarea 6: desagregacion (retencion 2019→2021) ==")
    des = {}
    for nombre, (col, solo) in [("genero", EJE_GENERO),
                                ("departamento", EJE_DEPTO),
                                ("gran_area", EJE_AREA),
                                ("nivel_formacion", EJE_NIVEL)]:
        des[nombre] = retencion_por_grupo(mues, col, 20, 21, solo=solo)
        d = des[nombre]
        print(f"   {nombre}: chi2={d['chi2']:.3f} gl={d['gl']} "
              f"p={d['p_valor']:.4f} min_esperado={d['min_esperado']:.2f} "
              f"supuesto_ok={d['supuesto_frecuencias_ok']}")

    print("\n== Tarea 6b: retencion desagregada en TODOS los pares ==")
    des_todos = {}
    for nombre, (col, solo) in [("genero", EJE_GENERO),
                                ("departamento", EJE_DEPTO),
                                ("gran_area", EJE_AREA),
                                ("nivel_formacion", EJE_NIVEL)]:
        des_todos[nombre] = tabla_desagregada(mues, col, solo=solo)
        print(f"\n  --- {nombre} (tasa de retencion % por par) ---")
        pares_lbl = list(des_todos[nombre].keys())
        print("      " + "".join(f"{p:>10s}" for p in pares_lbl))
        grupos = list(des_todos[nombre][pares_lbl[-1]]["grupos"].keys())
        for g in grupos:
            fila = []
            for p in pares_lbl:
                v = des_todos[nombre][p]["grupos"].get(g)
                fila.append(f"{100*v['tasa']:9.1f}" if v else "        -")
            n_ult = des_todos[nombre][pares_lbl[-1]]["grupos"][g]["n"]
            print(f"      {g[:30]:30s}" + "".join(fila) + f"   n(2021)={n_ult}")
        print("      p-valor chi2: " + "".join(
            f"{des_todos[nombre][p]['p_valor']:10.4f}" for p in pares_lbl))

    print("\n== Tarea 6c: transiciones desagregadas (2019->2021) ==")
    des_trans = {}
    for nombre, (col, solo) in [("genero", EJE_GENERO),
                                ("departamento", EJE_DEPTO),
                                ("gran_area", EJE_AREA),
                                ("nivel_formacion", EJE_NIVEL)]:
        des_trans[nombre] = transiciones_por_grupo(mues, col, 20, 21, solo=solo)
        d = des_trans[nombre]
        print(f"\n  --- {nombre} ---  chi2={d['chi2']:.3f} gl={d['gl']} "
              f"p={d['p_valor']:.4f} min_esp={d['min_esperado']:.2f} "
              f"ok={d['supuesto_frecuencias_ok']}")
        for k, v in d["grupos"].items():
            print(f"      {k[:30]:30s} n={v['n']:5d} permanece={v['permanece']:5d}"
                  f"({v['pct_permanece']:5.1f}%) asciende={v['asciende']:4d}"
                  f"({v['pct_asciende']:5.1f}%) desciende={v['desciende']:4d}"
                  f"({v['pct_desciende']:5.1f}%)")

    # ---- Tarea 7 -------------------------------------------------------
    print("\n== Tarea 7: graficas ==")
    graf_barras_pares(pares_mue, DIR_GRAFICAS / "01_retencion_entradas_salidas.png")
    graf_heatmaps(tm_mue, ["2017→2019", "2019→2021"],
                  DIR_GRAFICAS / "02_heatmap_transiciones.png")
    graf_poblacion(pers_conv_mue, DIR_GRAFICAS / "03_poblacion_por_convocatoria.png",
                   "muestra MAS")
    graf_retencion_grupos(des["genero"], des["gran_area"],
                          DIR_GRAFICAS / "04_retencion_genero_area.png")
    graf_anualizada(pares_mue, DIR_GRAFICAS / "05_retencion_anualizada.png")
    for f in sorted(DIR_GRAFICAS.glob("*.png")):
        print(f"   {f.name}  ({f.stat().st_size/1024:.1f} KB)")

    # ---- Salidas -------------------------------------------------------
    pd.DataFrame({COL_PERSONA: muestra_ids}).to_csv(
        DIR_SALIDA / "muestra_ids.csv", index=False, encoding="utf-8")
    mues.to_csv(DIR_SALIDA / "muestra_registros.csv", index=False, encoding="utf-8")
    print(f"\n   muestra_ids.csv ({len(muestra_ids)} ids)")
    print(f"   muestra_registros.csv ({len(mues)} registros)")

    # consistencia de atributos dentro de la persona (calidad)
    inc = {}
    for col in [COL_GENERO, COL_DEPTO, COL_AREA, COL_NIVEL, COL_CAT]:
        n = df.groupby(COL_PERSONA, observed=True)[col].nunique()
        inc[col] = int((n > 1).sum())

    res = {
        "fuente": FUENTE,
        "universo": {"registros": int(len(df)), "personas": int(N),
                     "convocatorias": len(CONV_ORDEN),
                     "personas_por_convocatoria": {str(CONV_ANIO[c]): pers_conv_pob[c]
                                                   for c in CONV_ORDEN},
                     "registros_por_convocatoria": {
                         str(CONV_ANIO[c]): int((df["_conv"] == c).sum())
                         for c in CONV_ORDEN}},
        "tamano_muestra": tm,
        "semilla": SEMILLA,
        "muestra": {"personas": len(muestra_ids), "registros": int(len(mues)),
                    "registros_por_convocatoria": {str(CONV_ANIO[c]): dist_conv[c]
                                                   for c in CONV_ORDEN},
                    "personas_por_convocatoria": {str(CONV_ANIO[c]): pers_conv_mue[c]
                                                  for c in CONV_ORDEN},
                    "media_registros_por_persona": len(mues) / len(muestra_ids)},
        "perfil_poblacion": {c: perfil_pob[c].value_counts().to_dict()
                             for c in [COL_GENERO, COL_CAT, COL_AREA, COL_NIVEL]},
        "perfil_muestra": {c: perfil_mue[c].value_counts().to_dict()
                           for c in [COL_GENERO, COL_CAT, COL_AREA, COL_NIVEL]},
        "representatividad": rep,
        "convocatorias_fecha": {str(c): str(fechas_conv[c]) for c in CONV_ORDEN},
        "intervalos_anios_reales": {f"{CONV_ANIO[a]}->{CONV_ANIO[a + 1]}": round(v, 4)
                                    for a, v in inter_reales.items()},
        "pares_muestra": pares_mue,
        "pares_universo": pares_pob,
        "transiciones_muestra": tm_mue,
        "transiciones_universo": tm_pob,
        "retencion_global_2013_2021": {"muestra": glob, "universo": glob_pob},
        "desagregacion_2019_2021": des,
        "desagregacion_todos_los_pares": des_todos,
        "transiciones_por_grupo_2019_2021": des_trans,
        "top5_departamento": TOP5_DEPTO,
        "coherencia_atributos_por_persona": inc,
        "hallazgos_calidad": {
            "emerito_absorbente": abs_eme,
            "emerito_por_convocatoria": eme_conv,
            "personas_por_numero_de_convocatorias": pres_pers,
            "genero_inconsistente": gin,
            "duplicados_persona_convocatoria": int(
                df.duplicated(subset=[COL_PERSONA, "_conv"]).sum()),
        },
    }

    def limpiar(o):
        if isinstance(o, dict):
            return {str(k): limpiar(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [limpiar(v) for v in o]
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        return o

    Path(args.json).write_text(
        json.dumps(limpiar(res), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"   {Path(args.json).name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
