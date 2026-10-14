# -*- coding: utf-8 -*-
"""
eda_longitudinal.py
===================

EDA formal ANTES del muestreo (Parte 1 de la metodología).

Fundamento: "Exploratory data analysis (EDA), including the production of simple
data summaries, tabulations and graphs, is typically the first stage of any such
analysis" (StatsRef.com, sobre Cochran 1977). El EDA aquí no es decorativo: sus
resultados son los que justifican (o no) las decisiones de muestreo y de
estimación que vienen después.

Produce:
  - data/memoria/eda/*.png          gráficas del EDA
  - data/memoria/eda_resultados.json  todas las cifras citadas en el documento

Uso:  python eda_longitudinal.py
"""

from __future__ import annotations

import io
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# El genero se analiza con la columna COLAPSADA (Intersexual + No disponible ->
# "Otro / No especificado"); ver genero_comun.py.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from genero_comun import (  # noqa: E402
    COL_GENERO_COL, agregar_genero_colapsado, resumen_colapso)

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
CSV = RAIZ / "Datos" / "Investigadores_Reconocidos_por_convocatoria_20261006.csv"
DIR_EDA = DOC / "data" / "memoria" / "eda"
SALIDA = DOC / "data" / "memoria" / "eda_resultados.json"

CONV_ORDEN = [16, 17, 18, 19, 20, 21]
ANIOS = {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021}
CATEGORIAS = ["Investigador Junior", "Investigador Asociado",
              "Investigador Sénior", "Investigador Emérito"]
AZUL, DORADO, VERDE, ROJO, GRIS, MORADO = ("#1E3780", "#B7871E", "#15803D",
                                           "#B91C1C", "#64748B", "#7C3AED")
FUENTE = ("Fuente: datos.gov.co, dataset bqtm-4y2h — 77 237 registros, "
          "30 086 personas, convocatorias 2013-2021.")
plt.rcParams.update({"figure.dpi": 130, "font.size": 10, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.spines.top": False,
                     "axes.spines.right": False})


def _fuente(ax, extra: str = "") -> None:
    ax.figure.text(0.01, 0.005, FUENTE + ((" " + extra) if extra else ""),
                   fontsize=6.4, color="#555555", ha="left", va="bottom")


def cargar() -> pd.DataFrame:
    partes = [t for t in pd.read_csv(CSV, dtype=str, keep_default_na=False,
                                     chunksize=50_000, encoding="utf-8")]
    df = pd.concat(partes, ignore_index=True)
    df["conv_i"] = df["ID_CONVOCATORIA"].astype(int)
    return agregar_genero_colapsado(df)


def pct(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


def main() -> int:
    DIR_EDA.mkdir(parents=True, exist_ok=True)
    print("== Carga ==")
    df = cargar()
    N_PERSONAS = df["ID_PERSONA_PR"].nunique()
    N_REGISTROS = len(df)
    print(f"   {N_REGISTROS} registros, {N_PERSONAS} personas")

    res: dict = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "fuente": FUENTE,
        "universo": {"registros": int(N_REGISTROS), "personas": int(N_PERSONAS),
                     "convocatorias": len(CONV_ORDEN)},
    }

    # ------------------------------------------------------------------ 1.1
    # Univariado: categóricas a nivel de PERSONA (última convocatoria observada,
    # misma regla que el resto del análisis, para que todo sea comparable).
    ult = (df.sort_values("conv_i").groupby("ID_PERSONA_PR", observed=True).last())
    # OJO: el genero se analiza con la columna COLAPSADA. La columna cruda
    # (NME_GENERO_PR) se conserva en el DataFrame para el control de calidad.
    CATS = ["NME_CLASIFICACION_PR", COL_GENERO_COL, "NME_GRAN_AREA_PR",
            "NME_DEPARTAMENTO_RES_PR", "NME_NIV_FORM_PR"]
    univ: dict = {}
    for c in CATS:
        vc = ult[c].value_counts()
        univ[c] = {"n_categorias": int(vc.size),
                   "distribucion": {str(k): {"n": int(v), "pct": 100 * v / len(ult)}
                                    for k, v in vc.items()}}
    res["univariado_persona"] = univ
    print("\n== 1.1 Univariado (nivel persona) ==")
    for c in CATS:
        print(f"   {c:26s} {univ[c]['n_categorias']:3d} categorías")

    # ---- edad -------------------------------------------------------------
    edad = pd.to_numeric(ult["EDAD_ANOS_PR"].str.replace(",", ".", regex=False),
                         errors="coerce")
    q = edad.quantile([0, .01, .05, .25, .5, .75, .95, .99, 1]).to_dict()
    iqr = q[0.75] - q[0.25]
    atip_bigote = int(((edad < q[0.25] - 1.5 * iqr) |
                       (edad > q[0.75] + 1.5 * iqr)).sum())
    res["edad"] = {
        "n": int(edad.notna().sum()), "faltantes": int(edad.isna().sum()),
        "media": float(edad.mean()), "desv": float(edad.std()),
        "cuantiles": {str(k): float(v) for k, v in q.items()},
        "iqr": float(iqr), "atipicos_bigote": atip_bigote,
        "mayores_100": int((edad > 100).sum()),
        "maximo": float(edad.max()), "minimo": float(edad.min()),
        "media_sin_atipicos_100": float(edad[edad <= 100].mean()),
    }
    print(f"   edad: media={res['edad']['media']:.2f} desv={res['edad']['desv']:.2f} "
          f"mediana={q[0.5]:.1f} bigote={atip_bigote} >100={res['edad']['mayores_100']} "
          f"max={res['edad']['maximo']}")

    # ---- genero: colapso de las categorias no representadas ---------------
    res["genero_colapso"] = resumen_colapso(df)
    gc = res["genero_colapso"]
    print(f"\n== Género: colapso en '{gc['etiqueta_colapsada']}' ==")
    for k, d in gc["categorias_colapsadas"].items():
        print(f"   {k:16s} censo={d['personas_censo']:2d} "
              f"etiqueta_en={d['convocatorias_con_la_etiqueta']}")
    print(f"   -> {gc['distribucion_censo_colapsada']}")

    # ---- convocatorias por persona ---------------------------------------
    nconv = df.groupby("ID_PERSONA_PR", observed=True)["conv_i"].nunique()
    dist_n = nconv.value_counts().sort_index()
    res["convocatorias_por_persona"] = {
        "distribucion": {str(int(k)): {"n": int(v), "pct": 100 * v / N_PERSONAS}
                         for k, v in dist_n.items()},
        "media": float(nconv.mean()), "max": int(nconv.max()),
        "una_sola": int((nconv == 1).sum()),
        "todas": int((nconv == len(CONV_ORDEN)).sum()),
    }
    print(f"   convocatorias por persona: media={nconv.mean():.3f} "
          f"una_sola={(nconv==1).sum()} todas={(nconv==6).sum()}")

    # ---- faltantes por variable y por convocatoria ------------------------
    # Solo cuentan las columnas del FUENTE: `conv_i` y la columna derivada de
    # genero colapsado no son variables del registro y contarlas inflaria el
    # total (30 -> 31) falseando el hallazgo.
    cols = [c for c in df.columns if c not in ("conv_i", COL_GENERO_COL)]
    falt: dict = {}
    for c in cols:
        vacio = (df[c].astype(str).str.strip() == "")
        if vacio.any():
            falt[c] = {
                "n": int(vacio.sum()), "pct": float(100 * vacio.mean()),
                "por_convocatoria": {str(ANIOS[k]): int(vacio[df["conv_i"] == k].sum())
                                     for k in CONV_ORDEN},
            }
    res["faltantes"] = {"total_columnas": len(cols),
                        "columnas_con_vacios": len(falt), "detalle": falt}
    print(f"\n== 1.1 Faltantes: {len(falt)} de {len(cols)} columnas tienen vacíos ==")
    for c, v in sorted(falt.items(), key=lambda x: -x[1]["n"])[:8]:
        print(f"   {c:26s} {v['n']:6d} ({pct(v['pct'])} %)")

    # ------------------------------------------------------------------ 1.2
    # Bivariado: retención por estrato candidato, en cada par de convocatorias.
    filas = ult.index  # personas
    cats_por_conv = {c: df.loc[df["conv_i"] == c].set_index("ID_PERSONA_PR")[CATS[0]]
                     for c in CONV_ORDEN}
    presentes = {c: set(df.loc[df["conv_i"] == c, "ID_PERSONA_PR"]) for c in CONV_ORDEN}

    def retencion_por(estrato_serie: pd.Series, ret_serie: pd.Series) -> dict:
        g = pd.DataFrame({"e": estrato_serie, "r": ret_serie}).dropna()
        out = {}
        for k, sub in g.groupby("e", observed=True):
            out[str(k)] = {"n": int(len(sub)), "retenidos": int(sub["r"].sum()),
                           "tasa": float(sub["r"].mean())}
        return out

    biv: dict = {"pares": {}, "decomposicion_varianza": {}}
    print("\n== 1.2 Bivariado: retención por estrato ==")
    for a, b in zip(CONV_ORDEN[:-1], CONV_ORDEN[1:]):
        A_, B_ = presentes[a], presentes[b]
        base = df.loc[df["conv_i"] == a].drop_duplicates("ID_PERSONA_PR")
        base = base.set_index("ID_PERSONA_PR")
        y = pd.Series({p: int(p in B_) for p in A_})
        par = {}
        for c in CATS:
            par[c] = retencion_por(base.loc[list(A_), c], base.loc[list(A_)].index.map(y))
        biv["pares"][f"{ANIOS[a]}→{ANIOS[b]}"] = par

    # Descomposición de la varianza para el par de referencia 2019→2021 usando
    # el CENSO (población completa), no la muestra.
    a, b = 20, 21
    base = df.loc[df["conv_i"] == a].drop_duplicates("ID_PERSONA_PR").set_index("ID_PERSONA_PR")
    y = pd.Series({p: int(p in presentes[b]) for p in presentes[a]})
    p_bar = float(y.mean())
    for c in CATS:
        estratos = base[c]
        p_h = y.groupby(estratos, observed=True).mean()
        W_h = estratos.value_counts(normalize=True)
        comunes = p_h.index.intersection(W_h.index)
        p_h, W_h = p_h[comunes], W_h[comunes]
        entre = float((W_h * (p_h - p_bar) ** 2).sum())
        dentro = float((W_h * p_h * (1 - p_h)).sum())
        total = entre + dentro
        ret_por_h = y.groupby(estratos, observed=True).agg(["sum", "size"])
        ret_por_h = ret_por_h.loc[comunes]
        if len(ret_por_h) >= 2:
            tabla = np.array([[int(r["sum"]), int(r["size"] - r["sum"])]
                              for _, r in ret_por_h.iterrows()])
            try:
                chi2, pval, gl, _ = stats.chi2_contingency(tabla, correction=False)
            except Exception:
                chi2, pval, gl = float("nan"), float("nan"), 0
        else:
            chi2 = pval = float("nan"); gl = 0
        biv["decomposicion_varianza"][c] = {
            "referencia": "2019→2021 (censo)",
            "p_global": p_bar,
            "estratos": {str(k): {"W_h": float(W_h[k]), "p_h": float(p_h[k]),
                                  "n_h_censo": int(ret_por_h.loc[k, "size"])}
                         for k in comunes},
            "varianza_entre": entre, "varianza_dentro": dentro,
            "varianza_total": total,
            "pct_entre": 100 * entre / total if total else None,
            "pct_dentro": 100 * dentro / total if total else None,
            "chi2": float(chi2), "gl": int(gl), "p_valor": float(pval),
            "min_n_h_censo": int(ret_por_h["size"].min()),
        }
        d = biv["decomposicion_varianza"][c]
        print(f"   {c:26s} entre={d['pct_entre']:5.2f} % dentro={d['pct_dentro']:5.2f} % "
              f"chi2={chi2:8.1f} p={pval:.3g}")
    res["bivariado"] = biv

    # ------------------------------------------------------------------ 1.3
    # Estratos naturales: comparar candidatos por ganancia teórica (asignación
    # proporcional => Var(estrat)/Var(MAS) = varianza_dentro/varianza_total).
    cand: dict = {}
    for c, d in biv["decomposicion_varianza"].items():
        cand[c] = {"pct_varianza_explicada": d["pct_entre"],
                   "reduccion_varianza_teorica_pct": d["pct_entre"],
                   "n_estratos": len(d["estratos"]),
                   "n_h_min_censo": d["min_n_h_censo"],
                   "p_valor": d["p_valor"]}
    # combinaciones de dos vías
    for c1, c2 in [("NME_CLASIFICACION_PR", COL_GENERO_COL),
                   ("NME_CLASIFICACION_PR", "NME_GRAN_AREA_PR")]:
        comb = base[c1].astype(str) + " | " + base[c2].astype(str)
        p_h = y.groupby(comb, observed=True).mean()
        W_h = comb.value_counts(normalize=True)
        comunes = p_h.index.intersection(W_h.index)
        p_h, W_h = p_h[comunes], W_h[comunes]
        entre = float((W_h * (p_h - p_bar) ** 2).sum())
        dentro = float((W_h * p_h * (1 - p_h)).sum())
        tot = entre + dentro
        cand[f"{c1} × {c2}"] = {
            "pct_varianza_explicada": 100 * entre / tot if tot else None,
            "reduccion_varianza_teorica_pct": 100 * entre / tot if tot else None,
            "n_estratos": int(len(comunes)),
            "n_h_min_censo": int(comb.value_counts()[comunes].min()),
            "p_valor": None,
        }
    res["estratos_candidatos"] = cand
    print("\n== 1.3 Estratos candidatos (reducción teórica de varianza) ==")
    for k, v in sorted(cand.items(), key=lambda x: -(x[1]["pct_varianza_explicada"] or 0)):
        print(f"   {k:44s} estratos={v['n_estratos']:3d} "
              f"minN_h={v['n_h_min_censo']:5d} "
              f"reduce={v['reduccion_varianza_teorica_pct']:5.2f} %")

    # =============================== GRÁFICAS ==============================
    print("\n== Gráficas ==")

    # --- 01 univariado categóricas
    fig, axes = plt.subplots(2, 2, figsize=(12.4, 8.4))
    for ax, col, titulo in zip(axes.ravel(),
                               ["NME_CLASIFICACION_PR", COL_GENERO_COL,
                                "NME_GRAN_AREA_PR", "NME_NIV_FORM_PR"],
                               ["Categoría de reconocimiento",
                                "Género (colapsado en “Otro / No especificado”)",
                                "Gran área de conocimiento", "Nivel de formación"]):
        vc = ult[col].value_counts().head(11)[::-1]
        etiquetas = [str(i)[:34] for i in vc.index]
        colores = [DORADO if i == 0 else AZUL for i in range(len(vc))]
        ax.barh(etiquetas, vc.values, color=colores[::-1])
        for i, v in enumerate(vc.values):
            ax.text(v + max(vc.values) * 0.01, i, f"{v} ({pct(100*v/len(ult))} %)",
                    va="center", fontsize=7.4)
        ax.set_title(titulo, fontsize=10)
        ax.set_xlim(0, max(vc.values) * 1.42)
        ax.tick_params(labelsize=7.6)
        ax.grid(axis="y", visible=False)
    fig.suptitle("Análisis univariado a nivel de persona (última convocatoria observada, "
                 f"n = {N_PERSONAS})", fontsize=11)
    _fuente(axes[1][0])
    fig.tight_layout(rect=(0, 0.035, 1, 0.95))
    fig.savefig(DIR_EDA / "01_univariado_categoricas.png", bbox_inches="tight")
    plt.close(fig)

    # --- 02 edad
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.4))
    e = edad.dropna()
    axes[0].hist(e, bins=60, color=AZUL, edgecolor="white", linewidth=0.3)
    axes[0].set_title("Distribución de la edad", fontsize=10)
    axes[0].set_xlabel("años"); axes[0].set_ylabel("personas")
    axes[1].boxplot(e, vert=True, widths=0.5, patch_artist=True,
                    boxprops=dict(facecolor="#D6E0F2", color=AZUL),
                    medianprops=dict(color=DORADO, linewidth=2),
                    flierprops=dict(marker="o", markersize=2.4, alpha=0.4,
                                    markerfacecolor=ROJO, markeredgecolor=ROJO))
    axes[1].set_title("Diagrama de caja (atípicos en rojo)", fontsize=10)
    axes[1].set_ylabel("años"); axes[1].set_xticks([])
    etiquetas_q = ["mín", "1 %", "5 %", "Q1", "mediana", "Q3", "95 %", "99 %", "máx"]
    valores_q = [q[0], q[.01], q[.05], q[.25], q[.5], q[.75], q[.95], q[.99], q[1]]
    axes[2].barh(etiquetas_q[::-1], valores_q[::-1], color=MORADO)
    for i, v in enumerate(valores_q[::-1]):
        axes[2].text(v + 4, i, f"{v:.1f}".replace(".", ","), va="center", fontsize=7.6)
    axes[2].set_title("Cuantiles", fontsize=10)
    axes[2].set_xlabel("años"); axes[2].set_xlim(0, max(valores_q) * 1.22)
    axes[2].grid(axis="y", visible=False)
    fig.suptitle(f"Edad a nivel de persona — media {res['edad']['media']:.1f} años · "
                 f"{atip_bigote} atípicos por bigote 1,5·IQR · "
                 f"{res['edad']['mayores_100']} registros con edad > 100", fontsize=10.5)
    _fuente(axes[0])
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    fig.savefig(DIR_EDA / "02_edad.png", bbox_inches="tight")
    plt.close(fig)

    # --- 03 convocatorias por persona
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    xs = list(dist_n.index)
    ax.bar([str(x) for x in xs], dist_n.values, color=AZUL)
    for i, v in enumerate(dist_n.values):
        ax.text(i, v + N_PERSONAS * 0.008, f"{v}\n({pct(100*v/N_PERSONAS)} %)",
                ha="center", fontsize=8)
    ax.set_xlabel("Número de convocatorias en que aparece la persona")
    ax.set_ylabel("Personas")
    ax.set_title("¿Cuántas veces aparece cada persona? "
                 f"(media {nconv.mean():.2f} convocatorias por persona)", fontsize=10.5)
    ax.set_ylim(0, max(dist_n.values) * 1.22)
    _fuente(ax)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(DIR_EDA / "03_convocatorias_por_persona.png", bbox_inches="tight")
    plt.close(fig)

    # --- 04 faltantes
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0),
                             gridspec_kw={"width_ratios": [1, 1.15]})
    top = sorted(falt.items(), key=lambda x: -x[1]["n"])[:12][::-1]
    axes[0].barh([c[:30] for c, _ in top], [v["n"] for _, v in top], color=ROJO)
    for i, (c, v) in enumerate(top):
        axes[0].text(v["n"] + N_REGISTROS * 0.004, i, f"{v['n']} ({pct(v['pct'])} %)",
                     va="center", fontsize=7.6)
    axes[0].set_xlim(0, max(v["n"] for _, v in top) * 1.4)
    axes[0].set_title("Valores vacíos por columna (total)", fontsize=10)
    axes[0].set_xlabel("registros vacíos de 77 237")
    axes[0].grid(axis="y", visible=False)
    cols_graf = [c for c, _ in top][:6]
    ancho = 0.8 / len(cols_graf)
    for j, c in enumerate(cols_graf):
        vals = [falt[c]["por_convocatoria"][str(ANIOS[k])] for k in CONV_ORDEN]
        axes[1].bar(np.arange(len(CONV_ORDEN)) + j * ancho - 0.4, vals, ancho,
                    label=c[:26])
    axes[1].set_xticks(range(len(CONV_ORDEN)), [str(ANIOS[k]) for k in CONV_ORDEN])
    axes[1].set_title("Vacíos de las 6 columnas más afectadas, por convocatoria",
                      fontsize=10)
    axes[1].set_ylabel("registros vacíos")
    axes[1].legend(fontsize=7, frameon=False)
    fig.suptitle(f"Valores faltantes: {len(falt)} de {len(cols)} columnas tienen vacíos "
                 f"(el resto está completo)", fontsize=10.5)
    _fuente(axes[0])
    fig.tight_layout(rect=(0, 0.045, 1, 0.92))
    fig.savefig(DIR_EDA / "04_faltantes.png", bbox_inches="tight")
    plt.close(fig)

    # --- 05 bivariado: retención por estrato
    fig, axes = plt.subplots(2, 2, figsize=(12.8, 8.6))
    par_ref = biv["pares"]["2019→2021"]
    for ax, col, titulo in zip(axes.ravel(),
                               ["NME_CLASIFICACION_PR", COL_GENERO_COL,
                                "NME_GRAN_AREA_PR", "NME_NIV_FORM_PR"],
                               ["Categoría", "Género", "Gran área", "Nivel de formación"]):
        d = par_ref[col]
        items = sorted(d.items(), key=lambda x: x[1]["tasa"])
        nombres = [k[:30] for k, _ in items]
        tasas = [100 * v["tasa"] for _, v in items]
        ns = [v["n"] for _, v in items]
        ax.barh(nombres, tasas, color=[VERDE if t >= 100*p_bar else ROJO for t in tasas])
        ax.axvline(100 * p_bar, color=GRIS, linestyle="--", linewidth=1.2)
        for i, (t, n) in enumerate(zip(tasas, ns)):
            ax.text(t + 1.0, i, f"{pct(t)} % (n={n})", va="center", fontsize=7.4)
        ax.set_xlim(0, 118)
        ax.set_title(f"Retención 2019→2021 por {titulo.lower()}", fontsize=10)
        ax.tick_params(labelsize=7.6)
        ax.grid(axis="y", visible=False)
    axes[0][0].legend(handles=[plt.Line2D([], [], color=GRIS, linestyle="--",
                                         label=f"retención global {pct(100*p_bar)} %")],
                      fontsize=7.4, frameon=False, loc="lower right")
    fig.suptitle("Análisis bivariado: ¿la retención cambia según el grupo? "
                 "(muestra del censo, 2019→2021)", fontsize=11)
    _fuente(axes[1][0])
    fig.tight_layout(rect=(0, 0.035, 1, 0.94))
    fig.savefig(DIR_EDA / "05_bivariado_retencion.png", bbox_inches="tight")
    plt.close(fig)

    # --- 06 varianza intra vs inter
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.0))
    dc = biv["decomposicion_varianza"]
    nombres = [c.replace("NME_", "").replace("_PR", "") for c in dc]
    entre = [dc[c]["pct_entre"] for c in dc]
    dentro = [dc[c]["pct_dentro"] for c in dc]
    ypos = np.arange(len(dc))
    axes[0].barh(ypos, entre, color=VERDE, label="entre grupos (explicada)")
    axes[0].barh(ypos, dentro, left=entre, color="#D6DEEA", label="dentro (no explicada)")
    for i, e_ in enumerate(entre):
        axes[0].text(e_ + 1.5, i, f"{pct(e_)} %", va="center", fontsize=8)
    axes[0].set_yticks(ypos, nombres, fontsize=8.6)
    axes[0].set_xlim(0, 118)
    axes[0].set_xlabel("Porcentaje de la varianza total de la retención")
    axes[0].set_title("Descomposición de la varianza de la retención (2019→2021)",
                      fontsize=10)
    axes[0].legend(fontsize=8, frameon=False, loc="lower right")
    axes[0].grid(axis="y", visible=False)
    for c, d in dc.items():
        for k, v in d["estratos"].items():
            axes[1].scatter(100 * v["W_h"], 100 * v["p_h"], s=max(18, 2.4 * np.sqrt(v["n_h_censo"])),
                            color=DORADO, alpha=0.75, edgecolor=AZUL, linewidth=0.6)
            if v["W_h"] > 0.02 or v["p_h"] > 0.95:
                axes[1].annotate(k[:22], (100 * v["W_h"], 100 * v["p_h"]),
                                 fontsize=6.6, xytext=(4, 3),
                                 textcoords="offset points")
    axes[1].axhline(100 * p_bar, color=GRIS, linestyle="--", linewidth=1.2)
    axes[1].set_xlabel("peso del estrato en la población (%)")
    axes[1].set_ylabel("retención del estrato (%)")
    axes[1].set_title("Heterogeneidad entre estratos: tamaño del estrato vs su retención",
                      fontsize=10)
    fig.suptitle("¿Hay estratos naturales? Cuanto más separadas estén las retenciones "
                 "y más peso tengan, más ayuda estratificar", fontsize=10.5)
    _fuente(axes[0])
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    fig.savefig(DIR_EDA / "06_varianza_intra_inter.png", bbox_inches="tight")
    plt.close(fig)

    for f in sorted(DIR_EDA.glob("*.png")):
        print(f"   {f.name}  ({f.stat().st_size/1024:.1f} KB)")

    SALIDA.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {SALIDA.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
