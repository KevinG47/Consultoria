# -*- coding: utf-8 -*-
"""
diversidad_inferencia.py
========================

F2-5 — Diversidad con intervalos de confianza y cobertura por convocatoria.

Qué añade sobre lo que ya existía
---------------------------------
El repositorio auditado publica la subrepresentación de cada grupo con
`comparar_dane()`, que devuelve un número puntual redondeado a un decimal
(«afro 3,0×»). Con 453 personas afro sobre 20 423 respuestas conocidas, ese 3,0×
tiene un intervalo que nadie había calculado. Aquí se calcula en dos niveles:

1. **Wilson** (analítico) sobre las respuestas conocidas de 2021. Es el intervalo
   correcto para una proporción con denominador fijo y se porta bien con
   proporciones pequeñas, donde el de Wald se sale de [0, 1].
2. **Bootstrap de diseño** sobre la muestra MAS (n = 2 224) con la
   post-estratificación por categoría que usa todo el proyecto. Responde a la
   pregunta honesta: «¿qué podría afirmarse si solo tuviéramos la muestra?».

El **IC del cociente de subrepresentación** r = DANE / p se obtiene transformando
los extremos del IC de p: como la referencia es fija, r es monótona decreciente
en p, así que [d/p_sup, d/p_inf].

La cobertura por convocatoria
-----------------------------
Las tres variables de diversidad **solo existen en 2021**. No es un defecto de
este análisis: es una restricción del registro. La comparación con DANE es una
**fotografía de 2021**, no una serie temporal; el género, en cambio, sí está
capturado en las seis convocatorias y sí admite serie.

Cómo se distingue «conocido» de «no registrado»
-----------------------------------------------
Se usa la semántica del propio código del auditado (`VALORES_NULOS`):
`TXT_GRUPO_ETNICO` y `TXT_POBLACION_DISCA` usan 'No disponible';
`ID_VICTIMA_CONFLICTO` usa 'No registra'. **'No registra' no es «no es víctima»**:
es que el campo no se capturó. Contarlo como respuesta conocida convertiría un
0 % de cobertura en un 100 % falso.

Produce:
    data/memoria/diversidad_inferencia.json
    data/memoria/graficas_diversidad/*.png

Uso:
    python documentacion_auditoria/src/diversidad_inferencia.py
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
FUENTE = (RAIZ / "datos_originales" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
MUESTRA = DOC / "data" / "memoria" / "muestra_ids.csv"
REPO = RAIZ / "datos_originales" / "repo_auditado" / "evidencias"
SALIDA = DOC / "data" / "memoria" / "diversidad_inferencia.json"
GRAF = DOC / "data" / "memoria" / "graficas_diversidad"

CONV = {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021}
SEMILLA = 20260217
B = 2000
Z = 1.959963984540054

AZUL, AZUL_SEC, AZUL_CLARO = "#1E3780", "#4A6BA8", "#7BA7D0"
DORADO, DORADO_CLARO = "#B7871E", "#D4A84A"
GRIS_OSC, GRIS, GRIS_CLARO = "#334155", "#64748B", "#CBD5E1"
FONDO, TEXTO, ALERTA = "#F8FAFC", "#1E293B", "#B91C1C"

VALORES_NULOS = {
    "ID_VICTIMA_CONFLICTO": "NO REGISTRA",
    "TXT_GRUPO_ETNICO": "NO DISPONIBLE",
    "TXT_POBLACION_DISCA": "NO DISPONIBLE",
}

# Referencias copiadas de repo_mejorado/src/analisis/diversidad.py.
# La columna de salida se llama `pct_dane_2018`, pero las víctimas son del
# RUV 2021 y NO del censo 2018 (parche E3 del CHANGELOG).
DANE_REFERENCIA = {
    "afro": (6.7, "Censo DANE 2018"),
    "indigena": (4.4, "Censo DANE 2018"),
    "raizal": (0.06, "Censo DANE 2018"),
    "palenquero": (0.014, "Censo DANE 2018"),
    "rrom": (0.005, "Censo DANE 2018"),
    "discapacidad": (7.1, "Censo DANE 2018"),
    "victima": (17.7, "RUV 2021 sobre población 2021"),
}
PATRONES_ETNIA = {
    "afro": "AFRO|NEGRA",
    "indigena": "INDIGENA|IND.GENA",
    "raizal": "RAIZAL",
    "palenquero": "PALENQUERO",
    "rrom": "RROM|GITANO",
}
DISCAPACIDADES = ["VISUAL", "FÍSICA", "FISICA", "AUDITIVA", "PSICOSOCIAL",
                  "INTELECTUAL", "MÚLTIPLE", "MULTIPLE"]
SIN_ETNIA = ["NINGÚN GRUPO ÉTNICO", "NINGUN GRUPO ETNICO", "BLANCO O MESTIZO"]
ETIQUETAS = {"afro": "Afrocolombiano", "indigena": "Indígena",
             "raizal": "Raizal", "palenquero": "Palenquero",
             "rrom": "Rrom (gitano)", "discapacidad": "Discapacidad (cualquiera)",
             "victima": "Víctima del conflicto"}


# ==========================================================================
# 1. Intervalos
# ==========================================================================
def wilson(k: int, n: int, z: float = Z) -> tuple[float, float]:
    """Intervalo de Wilson al 95 % para una proporción."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1.0 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    semi = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, float(centro - semi)), min(1.0, float(centro + semi)))


def _autotest_wilson() -> dict:
    """
    Casos de solución conocida, incluidos los extremos que Wald rompe.

    Se compara con tolerancia y no con `==`: en k = n el extremo superior vale
    1 menos un error de redondeo (~1e-17), así que una igualdad exacta falla por
    coma flotante y no por un defecto del cálculo.
    """
    casos = {
        "mitad_n1000": wilson(500, 1000),
        "cero_n100": wilson(0, 100),
        "todos_n100": wilson(100, 100),
        "seis_de_20423": wilson(6, 20423),
    }
    lo, hi = casos["mitad_n1000"]
    casos["todas_ok"] = bool(
        abs(lo - 0.4691) < 1e-3 and abs(hi - 0.5309) < 1e-3
        and abs(casos["cero_n100"][0] - 0.0) < 1e-9
        and abs(casos["todos_n100"][1] - 1.0) < 1e-9
        and 0 <= casos["seis_de_20423"][0] <= casos["seis_de_20423"][1] <= 1)
    return casos


def ic_cociente(dane_pct: float, lo: float, hi: float) -> list:
    """
    IC del cociente r = (dane/100) / p, transformando los extremos de p.

    r decrece con p, así que el extremo alto de r sale del extremo bajo de p.
    """
    if not (lo > 0 and hi > 0):
        return [float("nan"), float("nan")]
    d = dane_pct / 100.0
    return [float(d / hi), float(d / lo)]


# ==========================================================================
# 2. Bootstrap de diseño (MAS + post-estratificación)
# ==========================================================================
def boot_ratio(estrato: np.ndarray, en_grupo: np.ndarray,
               conocido: np.ndarray, N_h: np.ndarray, rng,
               reps: int = B) -> np.ndarray:
    """
    Bootstrap del cociente «proporción del grupo entre las respuestas conocidas».

        p = SUM_h N_h * a_h  /  SUM_h N_h * b_h

    con a_h = casos del grupo en el estrato h de la muestra / n_h y b_h = lo
    mismo para las respuestas conocidas. Se remuestrea DENTRO de cada
    post-estrato con n_h fijo.

    Se remuestrea el universo COMPLETO de 2021 (conocidas y no conocidas), no
    solo las conocidas: el denominador «respuestas conocidas» también se estima,
    y fijarlo subestimaría la incertidumbre.
    """
    H = N_h.size
    pos = [np.where(estrato == h)[0] for h in range(H)]
    out = np.full(reps, np.nan)
    for b in range(reps):
        num = den = 0.0
        for h, p in enumerate(pos):
            if p.size == 0 or N_h[h] <= 0:
                continue
            draw = p[rng.integers(0, p.size, p.size)]
            w = N_h[h] / p.size
            num += w * en_grupo[draw].sum()
            den += w * conocido[draw].sum()
        if den > 0:
            out[b] = num / den
    return out[~np.isnan(out)]


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


def fig_cobertura(cob: dict, archivo) -> None:
    anios = sorted(cob)
    variables = ["TXT_GRUPO_ETNICO", "TXT_POBLACION_DISCA",
                 "ID_VICTIMA_CONFLICTO", "NME_GENERO_PR"]
    etiquetas = ["Grupo étnico", "Discapacidad", "Víctima del conflicto", "Género"]
    colores = [AZUL, AZUL_SEC, AZUL_CLARO, DORADO]
    fig, ax = plt.subplots(figsize=(9.6, 4.5), dpi=150)
    ancho = 0.8 / len(variables)
    x = np.arange(len(anios))
    for i, (v, etq, col) in enumerate(zip(variables, etiquetas, colores)):
        vals = [cob[a][v]["pct_cobertura"] for a in anios]
        ax.bar(x + (i - (len(variables) - 1) / 2) * ancho, vals, width=ancho,
               color=col, zorder=2, label=etq)
    ax.set_xticks(x)
    ax.set_xticklabels([str(a) for a in anios])
    ax.set_ylim(0, 112)
    ax.set_xlabel("Convocatoria", color=TEXTO, fontsize=9)
    ax.set_ylabel("% de registros con el dato capturado", color=TEXTO, fontsize=9)
    ax.set_title("Cobertura de las variables de diversidad por convocatoria\n"
                 "Las tres variables de diversidad solo existen en 2021; el "
                 "género sí está en las seis",
                 color=TEXTO, fontsize=10.2, pad=10, loc="left")
    ax.legend(frameon=False, fontsize=8.2, labelcolor=GRIS_OSC, ncols=2)
    _estilo(ax)
    fig.tight_layout()
    fig.savefig(archivo, facecolor="white")
    plt.close(fig)


def fig_cocientes(res: dict, archivo) -> None:
    grupos = [g for g in ETIQUETAS if g in res
              and np.isfinite(res[g]["razon"])]
    fig, ax = plt.subplots(figsize=(9.8, 5.0), dpi=150)
    for i, g in enumerate(grupos):
        d = res[g]
        w_lo, w_hi = d["razon_ic_wilson"]
        ax.plot([w_lo, w_hi], [i - 0.16, i - 0.16], color=AZUL, linewidth=4.2,
                solid_capstyle="round", zorder=3,
                label="IC 95 % de Wilson (censo)" if i == 0 else None)
        ax.plot([d["razon"]], [i - 0.16], marker="o", color=AZUL, markersize=6,
                zorder=4)
        b = d.get("razon_ic_diseno")
        if b and np.isfinite(b[0]) and np.isfinite(b[1]):
            ax.plot([b[0], b[1]], [i + 0.16, i + 0.16], color=GRIS, linewidth=4.2,
                    solid_capstyle="round", zorder=2,
                    label="IC 95 % de diseño (muestra)" if i == 0 else None)
            ax.plot([d["razon"]], [i + 0.16], marker="o", color=GRIS_OSC,
                    markersize=5.4, zorder=4)
        else:
            ax.annotate("no estimable con la muestra", (d["razon"], i + 0.16),
                        textcoords="offset points", xytext=(8, 0), va="center",
                        fontsize=7.6, color=ALERTA)
        ax.annotate(f"{d['razon']:.1f}×", (d["razon"], i - 0.16),
                    textcoords="offset points", xytext=(0, 8), ha="center",
                    fontsize=8, color=AZUL)
    ax.axvline(1.0, color=DORADO, linewidth=1.6, zorder=1)
    ax.set_yticks(range(len(grupos)))
    ax.set_yticklabels([res[g]["etiqueta"] for g in grupos], fontsize=8.6)
    ax.set_xscale("log")
    ax.set_xlabel("Cociente de subrepresentación (DANE / MinCiencias), escala "
                  "logarítmica · 1 = representación igual a la poblacional",
                  color=TEXTO, fontsize=8.8)
    ax.set_title("Subrepresentación con su incertidumbre\n"
                 "El intervalo gris es el único que se puede sostener con la "
                 "muestra", color=TEXTO, fontsize=10.2, pad=10, loc="left")
    ax.legend(frameon=False, fontsize=8.2, labelcolor=GRIS_OSC, loc="lower right")
    _estilo(ax)
    ax.grid(axis="x", color=GRIS_CLARO, linewidth=0.6, alpha=0.9)
    fig.tight_layout()
    fig.savefig(archivo, facecolor="white")
    plt.close(fig)


# ==========================================================================
# 4. Principal
# ==========================================================================
def main() -> int:
    print("== F2-5 · Diversidad con IC y cobertura por convocatoria ==")
    salida: dict = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "analisis": "F2-5 — Diversidad con intervalos de confianza (Q5/Q6)",
        "semilla": SEMILLA, "replicas_bootstrap": B,
        "autotest_wilson": _autotest_wilson(),
    }
    if not salida["autotest_wilson"]["todas_ok"]:
        print("   [ABORTA] el autotest de Wilson falló")
        return 2
    print("   [OK] autotest de Wilson: casos conocidos y extremos")

    cols = ["ID_CONVOCATORIA", "ID_PERSONA_PR", "TXT_GRUPO_ETNICO",
            "TXT_POBLACION_DISCA", "ID_VICTIMA_CONFLICTO",
            "NME_CLASIFICACION_PR", "NME_GENERO_PR"]
    df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                     usecols=cols)
    for c in cols[2:]:
        df[c] = df[c].str.strip()
    df["conv_i"] = df["ID_CONVOCATORIA"].astype(int)
    df["anio"] = df["conv_i"].map(CONV)
    print(f"   fuente: {len(df):,} registros · {df['ID_PERSONA_PR'].nunique():,} "
          f"personas".replace(",", " "))

    # ---------------- cobertura por convocatoria ----------------
    cob: dict = {}
    for anio, g in df.groupby("anio"):
        fila: dict = {"n": int(len(g))}
        for col, nulo in VALORES_NULOS.items():
            conocido = g[col].str.upper() != nulo.upper()
            fila[col] = {"pct_cobertura": float(100 * conocido.mean()),
                         "pct_no_registra": float(100 * (1 - conocido.mean()))}
        fila["NME_GENERO_PR"] = {
            "pct_cobertura": 100.0, "pct_no_registra": 0.0,
            "nota": ("'No disponible' es una categoría observada del registro, "
                     "no un dato ausente: el género está capturado siempre.")}
        cob[str(int(anio))] = fila
    salida["cobertura_por_convocatoria"] = cob
    print("\n   cobertura (dato capturado) por convocatoria:")
    for a in sorted(cob):
        print(f"      {a}: etnia {cob[a]['TXT_GRUPO_ETNICO']['pct_cobertura']:6.2f} %"
              f" · discapacidad {cob[a]['TXT_POBLACION_DISCA']['pct_cobertura']:6.2f} %"
              f" · víctima {cob[a]['ID_VICTIMA_CONFLICTO']['pct_cobertura']:6.2f} %")

    aud_cob = pd.read_csv(REPO / "diversidad_cobertura_por_convocatoria.csv",
                          encoding="utf-8-sig")
    dif_cob = 0.0
    for _, r in aud_cob.iterrows():
        a = str(int(r["ANO_CONVO_INT"]))
        for col in VALORES_NULOS:
            dif_cob = max(dif_cob, abs(cob[a][col]["pct_no_registra"]
                                       - float(r[f"{col}_pct_no_registra"])))
    print(f"   [{'OK ' if dif_cob < 0.02 else 'NO '}] cobertura reproducida "
          f"(diferencia máxima {dif_cob:.4f} pp)")

    # ---------------- universo 2021 ----------------
    d21 = df[df["anio"] == 2021].copy()
    ids = set(pd.read_csv(MUESTRA, dtype=str, keep_default_na=False)
              ["ID_PERSONA_PR"])
    d21["en_muestra"] = d21["ID_PERSONA_PR"].isin(ids)

    VARIABLES = {
        "etnia": ("TXT_GRUPO_ETNICO", ["afro", "indigena", "raizal",
                                       "palenquero", "rrom"]),
        "discapacidad": ("TXT_POBLACION_DISCA", ["discapacidad"]),
        "victima": ("ID_VICTIMA_CONFLICTO", ["victima"]),
    }
    cats = sorted(d21["NME_CLASIFICACION_PR"].unique())
    mapa_cat = {k: i for i, k in enumerate(cats)}
    estrato = d21["NME_CLASIFICACION_PR"].map(mapa_cat).to_numpy()
    N_h = d21["NME_CLASIFICACION_PR"].value_counts().reindex(cats).to_numpy(float)
    sel = d21["en_muestra"].to_numpy()
    print(f"\n   universo 2021: {len(d21):,} registros · muestra {int(sel.sum()):,}"
          f" · post-estratos {len(cats)}".replace(",", " "))

    rng = np.random.default_rng(SEMILLA)
    res: dict = {}
    for _clave_var, (col, grupos) in VARIABLES.items():
        s = d21[col].str.upper()
        conocido = (s != VALORES_NULOS[col].upper()).to_numpy()
        N_conv = int(conocido.sum())
        for g in grupos:
            if _clave_var == "etnia":
                en_grupo = s.str.contains(PATRONES_ETNIA[g], regex=True,
                                          na=False).to_numpy()
            elif g == "discapacidad":
                en_grupo = s.isin(DISCAPACIDADES).to_numpy()
            else:
                en_grupo = s.isin(["SÍ", "SI"]).to_numpy()
            en_grupo = en_grupo & conocido

            n = int(en_grupo.sum())
            p = n / N_conv if N_conv else float("nan")
            lo_w, hi_w = wilson(n, N_conv)
            dane, fuente_dane = DANE_REFERENCIA[g]
            razon = (dane / 100) / p if p > 0 else float("inf")

            # --- bootstrap de diseño sobre la muestra de 2021 ---
            reps = boot_ratio(estrato[sel], en_grupo[sel].astype(float),
                              conocido[sel].astype(float), N_h, rng)
            n_muestra_grupo = int((en_grupo & sel).sum())
            pct_ic_diseno = razon_d = None
            if reps.size and n_muestra_grupo > 0:
                b_lo = float(np.percentile(reps, 2.5))
                b_hi = float(np.percentile(reps, 97.5))
                pct_ic_diseno = [float(100 * b_lo), float(100 * b_hi)]
                # Si el IC de la proporción incluye el 0, el cociente DANE/p no
                # está acotado por arriba (dividir por un p que puede ser 0 da
                # infinito). Se declara en vez de inventar un número: para los
                # grupos raros, la muestra no acota la subrepresentación.
                if b_lo > 0 and b_hi > 0:
                    razon_d = [float((dane / 100) / b_hi),
                               float((dane / 100) / b_lo)]

            res[g] = {
                "etiqueta": ETIQUETAS[g],
                "variable": col,
                "n": n, "denominador_respuestas_conocidas": N_conv,
                "pct": float(100 * p),
                "ic95_wilson_pct": [float(100 * lo_w), float(100 * hi_w)],
                "dane_pct": dane, "fuente_dane": fuente_dane,
                "razon": float(razon),
                "razon_ic_wilson": ic_cociente(dane, lo_w, hi_w),
                "n_muestra_grupo": n_muestra_grupo,
                "pct_ic95_diseno": pct_ic_diseno,
                "razon_ic_diseno": razon_d,
                "estimable_con_la_muestra": bool(n_muestra_grupo > 0),
                "cociente_acotado_con_la_muestra": bool(razon_d is not None),
            }
            d = res[g]
            ic_w = d["razon_ic_wilson"]
            ic_d = d["razon_ic_diseno"]
            print(f"   {g:12s} {n:5,d}/{N_conv:,} = {100*p:5.2f} % "
                  f"IC [{100*lo_w:5.2f};{100*hi_w:5.2f}] · razón {razon:5.2f}× "
                  f"IC [{ic_w[0]:5.2f};{ic_w[1]:5.2f}] · muestra n={n_muestra_grupo}"
                  f" · IC diseño "
                  + (f"[{ic_d[0]:5.2f};{ic_d[1]:5.2f}]" if ic_d else
                     "no estimable").replace(",", " "))

    # ---------------- contraste con la evidencia del auditado -------------
    aud = pd.read_csv(REPO / "diversidad_comparacion_dane.csv", encoding="utf-8-sig")
    mapa_aud = {"NEGRO/AFROCOLOMBIANO": "afro", "INDIGENA": "indigena",
                "RAIZAL": "raizal", "PALENQUERO": "palenquero", "RROM": "rrom",
                "DISCAPACIDAD (cualquiera)": "discapacidad",
                "VICTIMA CONFLICTO": "victima"}
    dif_n = 0
    dif_pct = dif_razon = 0.0
    for _, rd in aud.iterrows():
        k = mapa_aud.get(rd["grupo"])
        if not k:
            continue
        dif_n = max(dif_n, abs(int(rd["n_minciencias_2021"]) - res[k]["n"]))
        dif_pct = max(dif_pct, abs(float(rd["pct_minciencias"])
                                   - round(res[k]["pct"], 2)))
        dif_razon = max(dif_razon, abs(float(rd["razon_subrepresentacion"])
                                       - round(res[k]["razon"], 1)))
    print(f"\n   [{'OK ' if dif_n == 0 else 'NO '}] n reproducidos "
          f"(diferencia máxima {dif_n})")
    print(f"   [{'OK ' if dif_pct < 0.005 else 'NO '}] porcentajes reproducidos "
          f"(diferencia máxima {dif_pct:.4f} pp)")
    print(f"   [{'OK ' if dif_razon < 0.05 else 'NO '}] razones reproducidas "
          f"(diferencia máxima {dif_razon:.4f})")

    # ---------------- denominador: la decisión del parche E1 --------------
    s21 = d21["TXT_GRUPO_ETNICO"].str.upper()
    en_etnia = (s21 != VALORES_NULOS["TXT_GRUPO_ETNICO"]).to_numpy()
    mayoria = int((en_etnia & s21.isin(SIN_ETNIA).to_numpy()).sum())
    n_afro = res["afro"]["n"]
    den_equiv = int(en_etnia.sum()) - mayoria
    pct_equiv = 100 * n_afro / den_equiv if den_equiv else None
    salida["denominador_etnia"] = {
        "respuestas_conocidas": int(en_etnia.sum()),
        "mayoria_declarada_incluida": mayoria,
        "n_afro": n_afro,
        "pct_con_denominador_correcto": res["afro"]["pct"],
        "denominador_si_se_excluye_la_mayoria": den_equiv,
        "pct_con_denominador_equivocado": pct_equiv,
        "nota": ("Excluir «Ningún grupo étnico» y «Blanco o mestizo» del "
                 "denominador mezclaría bases: compararía «qué proporción de las "
                 "minorías es afro» con «qué proporción del país es afro». El "
                 "CÓDIGO del auditado no lo hace y es lo correcto; era el "
                 "COMENTARIO el que lo pedía (parche E1 del CHANGELOG)."),
    }
    print(f"\n   denominador: {int(en_etnia.sum())} respuestas conocidas -> afro "
          f"{res['afro']['pct']:.2f} %; excluyendo la mayoría ({den_equiv}) "
          f"daría {pct_equiv:.1f} %")

    # ---------------- alcance temporal -----------------------------------
    salida["alcance_temporal"] = {
        "con_datos": ["2021"],
        "sin_datos": ["2013", "2014", "2015", "2017", "2019"],
        "nota": ("La comparación con DANE es una FOTOGRAFÍA de 2021, no una "
                 "serie: las tres variables de diversidad tienen 0 % de "
                 "cobertura antes de 2021. Con este registro no puede hablarse "
                 "de evolución de la diversidad, solo de su estado en la última "
                 "convocatoria."),
        "genero_si_es_serie": ("NME_GENERO_PR está capturado en las seis "
                               "convocatorias, así que el género sí admite "
                               "análisis temporal."),
    }
    salida["grupos"] = res
    salida["referencias_dane"] = {k: {"pct": v[0], "fuente": v[1]}
                                  for k, v in DANE_REFERENCIA.items()}
    salida["grupos_no_estimables_con_la_muestra"] = [
        g for g, d in res.items() if not d["estimable_con_la_muestra"]]
    salida["grupos_cuyo_cociente_no_queda_acotado"] = [
        g for g, d in res.items() if not d["cociente_acotado_con_la_muestra"]]
    salida["nota_grupos_pequenos"] = (
        "Los grupos pequeños tienen intervalos ANCHOS, y eso es el resultado, no "
        "un fallo del análisis: con 114 indígenas y 6 rrom sobre 20 423 "
        "respuestas, la precisión está limitada por el tamaño del grupo. En la "
        "muestra MAS (n = 2 224) algunos grupos casi desaparecen, y su cociente "
        "deja de ser estimable en términos de diseño: se reporta como tal en vez "
        "de inventar un intervalo.")

    GRAF.mkdir(parents=True, exist_ok=True)
    fig_cobertura(cob, GRAF / "f2_5_cobertura_por_convocatoria.png")
    fig_cocientes(res, GRAF / "f2_5_razones_subrepresentacion.png")
    salida["figuras"] = sorted(p.name for p in GRAF.glob("*.png"))

    salida["validaciones"] = {
        "cobertura_reproducida": bool(dif_cob < 0.02),
        "n_reproducidos": bool(dif_n == 0),
        "porcentajes_reproducidos": bool(dif_pct < 0.005),
        "razones_reproducidas": bool(dif_razon < 0.05),
        "tres_variables_solo_en_2021": bool(
            all(cob[a]["TXT_GRUPO_ETNICO"]["pct_cobertura"] == 0
                for a in ("2013", "2014", "2015", "2017", "2019"))),
        "denominador_equivocado_daria_72_pct": bool(
            pct_equiv is not None and abs(pct_equiv - 72.0) < 1.5),
        "wilson_dentro_de_0_1": bool(all(
            0 <= d["ic95_wilson_pct"][0] <= d["ic95_wilson_pct"][1] <= 100
            for d in res.values())),
    }
    print()
    for k, v in salida["validaciones"].items():
        print(f"   [{'OK ' if v else 'NO '}] {k}")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"\n-> {SALIDA.relative_to(RAIZ)} ({SALIDA.stat().st_size:,} bytes)")
    print(f"-> {GRAF.relative_to(RAIZ)}/ ({len(salida['figuras'])} figuras)")
    print(f"   grupos no estimables con la muestra: "
          f"{salida['grupos_no_estimables_con_la_muestra'] or 'ninguno'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
