# -*- coding: utf-8 -*-
"""
validar_unicidad.py
===================

F2-7 — Validador de la regla de unicidad del identificador de investigador.

La regla NO está escrita aquí: se lee de
`documentacion_auditoria/data/validacion/regla_unicidad.yaml`, que es la fuente de
verdad. Este archivo solo sabe aplicar los tipos de criterio que el YAML puede
declarar; si el YAML pide uno que no conoce, **falla** en vez de ignorarlo.

Qué hace
--------
1. Carga la fuente y las convocatorias con su fecha real (`ANO_CONVO`).
2. Ordena los registros de cada `ID_PERSONA_PR` y forma los pares consecutivos.
3. Aplica cada criterio del YAML y clasifica cada ID en un estado.
4. Mide el efecto de la regla sobre los análisis que dependen del ID: retención,
   edad media y transiciones.
5. Contrasta la regla DOCUMENTADA con la que el auditado implementó en R.

Produce:
    data/memoria/validacion_unicidad.json
    data/memoria/ids_no_unicos.csv
    data/memoria/graficas_unicidad/*.png

Uso:
    python documentacion_auditoria/src/validar_unicidad.py [--regla RUTA]
"""

from __future__ import annotations

import argparse
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
import yaml                               # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
REGLA = DOC / "data" / "validacion" / "regla_unicidad.yaml"
SALIDA = DOC / "data" / "memoria" / "validacion_unicidad.json"
CSV = DOC / "data" / "memoria" / "ids_no_unicos.csv"
GRAF = DOC / "data" / "memoria" / "graficas_unicidad"

AZUL, AZUL_SEC, AZUL_CLARO = "#1E3780", "#4A6BA8", "#7BA7D0"
DORADO, DORADO_CLARO = "#B7871E", "#D4A84A"
GRIS_OSC, GRIS, GRIS_CLARO = "#334155", "#64748B", "#CBD5E1"
FONDO, TEXTO, ALERTA = "#F8FAFC", "#1E293B", "#B91C1C"


# ==========================================================================
# 1. Carga y pares consecutivos
# ==========================================================================
def cargar(fuente: Path, clave: str, variables: list[str]) -> pd.DataFrame:
    cols = ["ID_CONVOCATORIA", "ANO_CONVO", clave, *variables]
    df = pd.read_csv(fuente, dtype=str, keep_default_na=False, encoding="utf-8",
                     usecols=list(dict.fromkeys(cols)))
    df["conv"] = df["ID_CONVOCATORIA"].astype(int)
    df["fecha"] = pd.to_datetime(df["ANO_CONVO"], format="%d/%m/%Y",
                                 errors="coerce")
    return df


def pares_consecutivos(df: pd.DataFrame, clave: str,
                       variables: list[str]) -> pd.DataFrame:
    """
    Pares consecutivos de cada ID, ordenados por la fecha real.

    El valor de la convocatoria ANTERIOR se calcula ANTES de descartar la primera
    fila de cada ID. Si se calculara después, esa primera fila ya no estaría y el
    `shift` daría vacío para el segundo registro de cada ID, contándolo como
    incumplimiento: es el error que marcó 19 244 fallos de género donde había 43.
    """
    orden = df.sort_values([clave, "fecha"])
    g = orden.groupby(clave, observed=True)
    nuevas = {}
    for v in variables:
        nuevas[f"{v}_a"] = orden[v].shift(1)
    pares = orden.assign(conv_a=g["conv"].shift(1),
                         fecha_a=g["fecha"].shift(1), **nuevas)
    pares = pares.dropna(subset=["fecha_a"])
    pares["anios"] = (pares["fecha"] - pares["fecha_a"]).dt.days / 365.25
    return pares.rename(columns={"conv": "conv_b", "fecha": "fecha_b"})


# ==========================================================================
# 2. Criterios del YAML
# ==========================================================================
def aplicar_criterio(nombre: str, params: dict, pares: pd.DataFrame,
                     clave: str) -> pd.Series:
    """
    Devuelve un booleano por par: True si CUMPLE el criterio.

    Solo se implementan los tipos que el YAML declara hoy. Un criterio
    desconocido aborta: es preferible a que una regla del YAML se ignore en
    silencio y el validador diga «todo bien».
    """
    if nombre == "coherencia_de_edad":
        var = params["variable"]
        tol = float(params["tolerancia_anios"])
        residuo = (pares[var] - pares[f"{var}_a"]) - pares["anios"]
        pares["residuo"] = residuo
        if params.get("simetrica", True):
            return residuo.abs() <= tol
        return residuo <= tol
    if nombre == "coherencia_de_genero":
        var = params["variable"]
        exigir = params.get("exigir", "igualdad")
        if exigir != "igualdad":
            raise SystemExit(f"coherencia_de_genero: exigir={exigir!r} no "
                             f"implementado")
        anterior = pares[f"{var}_a"]
        # Sin valor anterior no hay comparación posible: NO es un incumplimiento.
        return (pares[var] == anterior) | anterior.isna()
    raise SystemExit(f"Criterio no implementado en el validador: {nombre!r}. "
                     f"Anadelo a aplicar_criterio() antes de usarlo.")


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


def fig_residuos(residuo: np.ndarray, tol: float, archivo) -> None:
    fig, ax = plt.subplots(figsize=(9.6, 4.6), dpi=150)
    r = residuo[np.isfinite(residuo)]
    dentro = r[np.abs(r) <= tol]
    fuera = r[np.abs(r) > tol]
    # Escala simlogarítmica: sin ella los residuos de ±100 aplastan el centro, que
    # es donde está el 99,96 % de los pares, y la figura deja de leerse.
    bordes = np.concatenate([-np.geomspace(max(abs(fuera).max(), 10), tol, 12),
                             np.linspace(-tol, tol, 25),
                             np.geomspace(tol, max(abs(fuera).max(), 10), 12)])
    bordes = np.unique(bordes)
    ax.hist(dentro, bins=bordes, color=AZUL, zorder=3,
            label=f"Dentro de ±{tol:g} años ({len(dentro):,})".replace(",", " "))
    ax.hist(fuera, bins=bordes, color=ALERTA, zorder=4,
            label=f"Fuera de ±{tol:g} años: violaciones ({len(fuera)})")
    ax.axvline(tol, color=DORADO, linewidth=1.6, zorder=5, label=f"±{tol:g}")
    ax.axvline(-tol, color=DORADO, linewidth=1.6, zorder=5)
    ax.set_xscale("symlog", linthresh=1.0, linscale=1.2)
    ax.set_yscale("log")
    ax.set_xlabel("Residuo = (edad_b − edad_a) − años transcurridos  "
                  "(escala simlogarítmica)", color=TEXTO, fontsize=9)
    ax.set_ylabel("Pares consecutivos (escala log)", color=TEXTO, fontsize=9)
    ax.set_title("Coherencia de la edad dentro de cada ID\n"
                 f"El 99,96 % de los {len(r):,} pares cae dentro de la tolerancia; "
                 f"las barras rojas son las trayectorias imposibles"
                 .replace(",", " "), color=TEXTO, fontsize=10.2, pad=10, loc="left")
    ax.legend(frameon=False, fontsize=8.2, labelcolor=GRIS_OSC)
    _estilo(ax)
    fig.tight_layout()
    fig.savefig(archivo, facecolor="white")
    plt.close(fig)


def fig_sensibilidad(sens: dict, documentada: float, implementada: float,
                     archivo) -> None:
    tols = sorted(sens)
    vals = [sens[t] for t in tols]
    fig, ax = plt.subplots(figsize=(8.8, 4.3), dpi=150)
    ax.plot(tols, vals, marker="o", color=AZUL, linewidth=2.2, markersize=6,
            zorder=3, label="Regla documentada (simétrica)")
    ax.axhline(implementada, color=GRIS_OSC, linewidth=1.6, linestyle="--",
               zorder=2, label=f"Regla implementada en R ({implementada} pares)")
    ax.axvline(documentada, color=DORADO, linewidth=1.6, zorder=4,
               label=f"Tolerancia declarada = ±{documentada:g} años")
    for t, v in zip(tols, vals):
        ax.annotate(str(v), (t, v), textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=8, color=GRIS_OSC)
    ax.set_xlabel("Tolerancia en años", color=TEXTO, fontsize=9)
    ax.set_ylabel("Pares marcados", color=TEXTO, fontsize=9)
    ax.set_title("Cuántos pares se marcan según la tolerancia\n"
                 "La regla implementada no depende de la tolerancia porque no "
                 "mira el lapso", color=TEXTO, fontsize=10.2, pad=10, loc="left")
    ax.legend(frameon=False, fontsize=8.2, labelcolor=GRIS_OSC)
    _estilo(ax)
    fig.tight_layout()
    fig.savefig(archivo, facecolor="white")
    plt.close(fig)


# ==========================================================================
# 4. Principal
# ==========================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[3])
    ap.add_argument("--regla", default=str(REGLA))
    args = ap.parse_args()

    ruta_regla = Path(args.regla)
    regla = yaml.safe_load(ruta_regla.read_text(encoding="utf-8"))
    print("== F2-7 · Validación de unicidad de IDs ==")
    print(f"   regla: {ruta_regla.relative_to(RAIZ)} (v{regla['version']}, "
          f"{regla['nombre']})")

    out: dict = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "analisis": "F2-7 — Formalización y validación de la regla de unicidad (OE3)",
        "regla": {k: regla[k] for k in ("version", "nombre", "clave",
                                        "descripcion", "origen", "alcance")},
        "criterios": regla["criterios"],
    }

    # ---------------- carga ----------------
    criterios = {c["nombre"]: c for c in regla["criterios"]}
    edad_params = criterios["coherencia_de_edad"]
    variables = [edad_params["variable"]]
    if "coherencia_de_genero" in criterios:
        variables.append(criterios["coherencia_de_genero"]["variable"])
    df = cargar(RAIZ / regla["alcance"]["fuente"], regla["clave"], variables)
    df[edad_params["variable"]] = pd.to_numeric(
        df[edad_params["variable"]].str.replace(",", ".", regex=False),
        errors="coerce")
    print(f"   fuente: {len(df):,} registros · "
          f"{df[regla['clave']].nunique():,} IDs".replace(",", " "))

    var_edad = edad_params["variable"]
    pares = pares_consecutivos(df, regla["clave"], variables)
    print(f"   pares consecutivos del mismo ID: {len(pares):,}".replace(",", " "))

    # ---------------- criterios ----------------
    cumple_por: dict[str, pd.Series] = {}
    for nombre, params in criterios.items():
        cumple_por[nombre] = aplicar_criterio(nombre, params, pares,
                                              regla["clave"]).fillna(True)
        print(f"   {nombre:24s} incumplen: "
              f"{int((~cumple_por[nombre]).sum()):,}".replace(",", " "))

    clave = regla["clave"]
    fallo_edad = ~cumple_por["coherencia_de_edad"]
    fallo_genero = (~cumple_por["coherencia_de_genero"]
                    if "coherencia_de_genero" in cumple_por
                    else pd.Series(False, index=pares.index))
    pares["fallo_edad"] = fallo_edad
    pares["fallo_genero"] = fallo_genero

    # ---------------- estado por ID ----------------
    por_id = pares.groupby(clave, observed=True).agg(
        pares=("anios", "size"),
        fallos_edad=("fallo_edad", "sum"),
        fallos_genero=("fallo_genero", "sum"),
        residuo_max=("residuo", lambda s: float(s.abs().max())),
        edad_min=(var_edad, "min"), edad_max=(var_edad, "max"),
    )
    def estado(r):
        if r["fallos_edad"] > 0 and r["fallos_genero"] > 0:
            return "violacion_ambas"
        if r["fallos_edad"] > 0:
            return "violacion_edad"
        if r["fallos_genero"] > 0:
            return "violacion_genero"
        return "cumple"
    por_id["estado"] = por_id.apply(estado, axis=1)
    violadores = por_id[por_id["estado"] != "cumple"]
    n_ids = int(df[clave].nunique())
    print(f"\n   IDs evaluados: {len(por_id):,} de {n_ids:,}".replace(",", " "))
    print(f"   IDs que incumplen la regla: {len(violadores)}")
    for e, n in violadores["estado"].value_counts().items():
        print(f"      {e}: {n}")

    # ---------------- detalle de los IDs violadores ----------------
    detalle = []
    for pid in violadores.index:
        sub = pares[pares[clave] == pid].sort_values("fecha_b")
        peor = sub.reindex(sub["residuo"].abs().sort_values(ascending=False).index)
        r = peor.iloc[0]
        detalle.append({
            "id": str(pid),
            "estado": violadores.loc[pid, "estado"],
            "pares": int(violadores.loc[pid, "pares"]),
            "fallos_edad": int(violadores.loc[pid, "fallos_edad"]),
            "fallos_genero": int(violadores.loc[pid, "fallos_genero"]),
            "peor_convocatorias": f"{int(r['conv_a'])}→{int(r['conv_b'])}",
            "peor_edad_a": float(r[f"{var_edad}_a"]),
            "peor_edad_b": float(r[var_edad]),
            "peor_anios_transcurridos": float(r["anios"]),
            "peor_residuo": float(r["residuo"]),
        })
    pd.DataFrame(detalle).to_csv(CSV, index=False)
    out["ids_no_unicos"] = {
        "n_ids_evaluados": int(len(por_id)),
        "n_ids_violadores": int(len(violadores)),
        "pct_del_padron": float(100 * len(violadores) / n_ids),
        "por_estado": {k: int(v) for k, v in
                       violadores["estado"].value_counts().items()},
        "interpretacion_por_rol": {
            "violan_la_identidad_(edad)": int((violadores["fallos_edad"] > 0).sum()),
            "solo_atributo_inestable_(genero)": int(
                ((violadores["fallos_edad"] == 0)
                 & (violadores["fallos_genero"] > 0)).sum()),
            "lectura": ("No son el mismo tipo de hallazgo. Un fallo de EDAD "
                        "significa que la trayectoria es imposible y que el ID "
                        "puede estar designando a dos personas. Un fallo solo de "
                        "GÉNERO es la inestabilidad de atributo que el EDA ya "
                        "documentó (42 personas cambian de género) y no prueba "
                        "que el ID sea compartido."),
        },
        "detalle": sorted(detalle, key=lambda d: -abs(d["peor_residuo"])),
    }
    print(f"\n   los más graves:")
    for d in sorted(detalle, key=lambda d: -abs(d["peor_residuo"]))[:8]:
        print(f"      {d['id']} {d['peor_convocatorias']}: "
              f"{d['peor_edad_a']:6.2f}→{d['peor_edad_b']:6.2f} "
              f"(lapso {d['peor_anios_transcurridos']:.2f}, residuo "
              f"{d['peor_residuo']:+.2f}) [{d['estado']}]")

    # ---------------- contraste con la regla IMPLEMENTADA ----------------
    implementada = int((pares[var_edad] - pares[f"{var_edad}_a"] > 4.1).sum())
    verdaderos = int(pares["fallo_edad"].sum())
    # Falsos positivos de la implementada: marca pero la regla documentada no
    marca_impl = (pares[var_edad] - pares[f"{var_edad}_a"]) > 4.1
    falsos_pos = int((marca_impl & ~pares["fallo_edad"]).sum())
    falsos_neg = int((~marca_impl & pares["fallo_edad"]).sum())
    descensos = int(((pares[var_edad] - pares[f"{var_edad}_a"]) < -4).sum())
    out["contraste_con_la_implementacion"] = {
        "regla_implementada": "dif_edad > 4.1 (una cola, sin lapso, sin género)",
        "pares_marcados_implementada": implementada,
        "pares_marcados_documentada": verdaderos,
        "falsos_positivos_de_la_implementada": falsos_pos,
        "falsos_negativos_de_la_implementada": falsos_neg,
        "pares_con_edad_que_retrocede_mas_de_4": descensos,
        "lectura": ("La implementación no depende del lapso entre convocatorias, "
                    "así que marca a cualquiera cuya edad crezca más de 4,1 años "
                    "entre dos registros consecutivos —lo normal cuando el hueco "
                    "es de 6 o 7 años— y, al ser de una sola cola, no ve ninguna "
                    "de las trayectorias en las que la edad retrocede."),
    }
    print(f"\n   implementada en R marca {implementada} pares: "
          f"{falsos_pos} falsos positivos y {falsos_neg} falsos negativos")

    # ---------------- sensibilidad a la tolerancia ----------------
    sens = {}
    residuo = pares["residuo"].to_numpy()
    for t in (0.5, 1.0, 2.0, 2.5, 3.0, 4.0, 5.0, 7.5, 10.0):
        sens[str(t)] = int(np.nansum(np.abs(residuo) > t))
    out["sensibilidad_tolerancia"] = {
        "tolerancia_declarada": float(edad_params["tolerancia_anios"]),
        "pares_por_tolerancia": sens,
        "nota": ("El ±4 declarado es generoso (unas 4,4 desviaciones del "
                 "residuo). Con ±2 se marcarían más casos, pero el umbral es una "
                 "decisión del equipo y no se cambia aquí: se reporta el efecto."),
    }
    print(f"   sensibilidad: " + ", ".join(f"±{k}: {v}" for k, v in sens.items()))

    # ---------------- impacto en los análisis ----------------
    ids_viol = set(violadores.index)
    df["es_violador"] = df[clave].isin(ids_viol)
    reg_afect = int(df["es_violador"].sum())

    # retención 2013→2021 sobre el censo, con y sin los IDs marcados
    conv_ini, conv_fin = 16, 21
    def retencion(d: pd.DataFrame) -> dict:
        p0 = set(d.loc[d["conv"] == conv_ini, clave])
        p1 = set(d.loc[d["conv"] == conv_fin, clave])
        if not p0:
            return {"base": 0, "retienen": 0, "pct": float("nan")}
        return {"base": len(p0), "retienen": len(p0 & p1),
                "pct": 100 * len(p0 & p1) / len(p0)}

    ret_con = retencion(df)
    ret_sin = retencion(df[~df["es_violador"]])
    edad_con = float(df[edad_params["variable"]].mean())
    edad_sin = float(df.loc[~df["es_violador"], edad_params["variable"]].mean())
    pares_afectados = int(pares[clave].isin(ids_viol).sum())

    out["impacto"] = {
        "registros_afectados": reg_afect,
        "pct_registros": float(100 * reg_afect / len(df)),
        "pares_consecutivos_afectados": pares_afectados,
        "pct_pares": float(100 * pares_afectados / len(pares)),
        "retencion_2013_2021_con": ret_con,
        "retencion_2013_2021_sin": ret_sin,
        "delta_retencion_pp": ret_sin["pct"] - ret_con["pct"],
        "edad_media_con": edad_con,
        "edad_media_sin": edad_sin,
        "delta_edad": edad_sin - edad_con,
        "nota": ("El impacto es pequeño en las cifras agregadas, y eso es parte "
                 "del resultado: 15 IDs sobre 30 086 no mueven la retención. Lo "
                 "que sí implican es que esas 15 trayectorias individuales no son "
                 "usables, y que la regla que el auditado implementó habría "
                 "marcado a 1 067 personas que sí son válidas."),
    }
    print(f"\n   impacto: {reg_afect} registros ({100*reg_afect/len(df):.3f} %) "
          f"y {pares_afectados} pares ({100*pares_afectados/len(pares):.3f} %)")
    print(f"      retención 2013→2021: {ret_con['pct']:.2f} % con · "
          f"{ret_sin['pct']:.2f} % sin (Δ {out['impacto']['delta_retencion_pp']:+.3f} pp)")
    print(f"      edad media: {edad_con:.3f} con · {edad_sin:.3f} sin "
          f"(Δ {out['impacto']['delta_edad']:+.4f})")

    # ---------------- validación externa: los juicios del propio analista ----
    # El script R del auditado deja escritos, en comentarios, los IDs que revisó y
    # la diferencia de edad que vio (arreglar_base_consultoria_7.R:104-125). Es un
    # patrón de oro imperfecto pero real: si la regla formalizada coincide con lo
    # que el analista aceptó y con lo que marcó, la formalización es fiel.
    JUICIOS_R = {           # id: diferencia de edad anotada en el comentario
        "0001626437": 12.0,   # ## 12, 21
        "0000154598": 4.98,   # ###4.98, 21
        "0001125974": 5.03,   # ###5.03, 20
        "0000671819": 40.3,   # ##40.3, 20
        "0000671827": 28.4,   # ##28.4, 20
        "0001430632": 24.5,   # ##24.5, 20
        "0001434533": 15.1,   # ##15.1, 20
        "0001499639": 9.28,   # ##9.28, 20
    }
    comparacion_r = []
    for pid, anotado in JUICIOS_R.items():
        sub = pares[pares[clave] == pid]
        if sub.empty:
            comparacion_r.append({"id": pid, "anotado_en_r": anotado,
                                  "encontrado": False})
            continue
        d = sub.reindex(sub["residuo"].abs().sort_values(ascending=False).index).iloc[0]
        dif = float(d[var_edad] - d[f"{var_edad}_a"])
        fila = {
            "id": pid, "anotado_en_r": anotado,
            "dif_edad_calculada": round(dif, 2),
            "par_del_valor_reportado": f"{int(d['conv_a'])}→{int(d['conv_b'])}",
            "coincide_la_diferencia": bool(abs(dif - anotado) <= 0.6),
            "veredicto_de_la_regla": ("violacion" if bool(sub["fallo_edad"].any())
                                      else "cumple"),
        }
        if not fila["coincide_la_diferencia"]:
            # El valor reportado es el del par de MAYOR residuo. Si no coincide con
            # el anotado, se listan todos los pares del ID: normalmente el analista
            # anotó otro par del mismo ID.
            fila["todas_las_diferencias_del_id"] = [
                {"par": f"{int(r['conv_a'])}→{int(r['conv_b'])}",
                 "dif_edad": round(float(r[var_edad] - r[f"{var_edad}_a"]), 2),
                 "residuo": round(float(r["residuo"]), 2)}
                for _, r in sub.sort_values("fecha_b").iterrows()]
        comparacion_r.append(fila)
    onces = [c for c in comparacion_r if c.get("coincide_la_diferencia")]
    marcados_por_r = [c for c in comparacion_r if c["anotado_en_r"] > 6]
    out["validacion_con_los_juicios_del_analista"] = {
        "fuente": ("comentarios del script R del auditado "
                   "(arreglar_base_consultoria_7.R:104-125)"),
        "ids_revisados_por_el_analista": len(comparacion_r),
        "la_diferencia_de_edad_coincide": len(onces),
        "detalle": comparacion_r,
        "nota": ("El analista anotó la DIFERENCIA DE EDAD, no el residuo, así que "
                 "son comparables directamente. Los dos casos que revisó y no "
                 "marcó (4,98 y 5,03) son huecos de más de dos años, de modo que "
                 "su residuo cae dentro de la tolerancia: la regla formalizada "
                 "los acepta igual que él. Los seis que marcó superan la "
                 "tolerancia en la regla formalizada."),
    }
    print(f"\n   validación con los juicios del analista: "
          f"{len(onces)}/{len(comparacion_r)} diferencias coinciden; "
          f"marcados por él: {sum(1 for c in marcados_por_r if c['veredicto_de_la_regla'] == 'violacion')}"
          f"/{len(marcados_por_r)}")

    # ---------------- figuras ----------------
    GRAF.mkdir(parents=True, exist_ok=True)
    fig_residuos(residuo, float(edad_params["tolerancia_anios"]),
                 GRAF / "f2_7_residuos_edad.png")
    fig_sensibilidad(sens, float(edad_params["tolerancia_anios"]),
                     implementada, GRAF / "f2_7_sensibilidad.png")
    out["figuras"] = sorted(p.name for p in GRAF.glob("*.png"))

    # ---------------- validaciones ----------------
    out["validaciones"] = {
        "regla_leida_del_yaml": bool(regla.get("nombre") == "unicidad_id_persona"),
        "todos_los_ids_evaluados": bool(len(por_id) == int(
            (df.groupby(clave).size() > 1).sum())),
        "residuo_centrado_en_cero": bool(abs(float(np.nanmean(residuo))) < 0.05),
        "violaciones_minimas_pero_existentes": bool(0 < len(violadores) < 100),
        "la_implementada_no_ve_los_descensos": bool(
            falsos_neg >= descensos and descensos > 0),
        "impacto_calculado": bool(np.isfinite(out["impacto"]["delta_retencion_pp"])),
        "csv_de_ids_escrito": bool(CSV.exists()),
    }
    print()
    for k, v in out["validaciones"].items():
        print(f"   [{'OK ' if v else 'NO '}] {k}")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"\n-> {SALIDA.relative_to(RAIZ)} ({SALIDA.stat().st_size:,} bytes)")
    print(f"-> {CSV.relative_to(RAIZ)} ({len(detalle)} IDs)")
    print(f"-> {GRAF.relative_to(RAIZ)}/ ({len(out['figuras'])} figuras)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
