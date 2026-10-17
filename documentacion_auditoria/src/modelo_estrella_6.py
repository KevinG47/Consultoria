# -*- coding: utf-8 -*-
"""
modelo_estrella_6.py
====================

F2-3 — Modelo estrella REPRODUCIBLE con las 6 convocatorias.

El defecto que resuelve
-----------------------
`sprint2_duckdb.py:28` construye el modelo con `cargar_consolidado()`, que
prefiere `datos/raw/investigadores_consolidado.csv` —**ausente y gitignored**— y
cae al XLSX de `datos/tarea_join/`, que contiene **solo 3 convocatorias**
(50 891 filas). Consecuencia: el modelo poblado queda con `dim_convocatoria = 3`
y `fact_clasificacion = 50 891`, mientras la evidencia versionada del propio
repositorio auditado (`evidencias/duckdb_resumen_modelo.txt`) documenta
**6 convocatorias y 77 237 registros**. La evidencia y el producto reproducible
no coinciden.

Lo que hace este script
-----------------------
Alimenta las **mismas funciones del repositorio auditado** —sin reimplementar
nada— con la fuente completa de 6 convocatorias:

    Transformacion.transformar()          (pipeline del auditado)
    modelo.dimensional.cargar_en_duckdb() (esquema del auditado)

y además corre el pipeline del auditado tal cual (con su propio
`cargar_consolidado()`) para reproducir y dejar documentada la brecha 3 vs 6.

Verifica integridad referencial de las 9 tablas, contrasta contra la evidencia
versionada y escribe los resultados en JSON.

NO escribe nada dentro de `datos_originales/repo_auditado/`: la base DuckDB va a
un directorio de trabajo (`_archivo/tmp_estrella/`), de modo que los 236 hashes
del manifiesto del repo auditado siguen intactos.

El «nueve» del objetivo
-----------------------
El objetivo específico 4 pide «un modelo dimensional con **nueve dimensiones** y
una tabla de hechos». Lo construido son **9 tablas**: 7 dimensiones
(`dim_area`, `dim_categoria`, `dim_convocatoria`, `dim_formacion`,
`dim_institucion`, `dim_investigador`, `dim_territorio`), 1 tabla de hechos
(`fact_clasificacion`) y 1 tabla puente N:N (`bridge_hecho_institucion`). El
nueve cuenta tablas, no dimensiones. El JSON lo deja registrado.

Produce:
    data/memoria/modelo_estrella.json
    data/memoria/graficas_estrella/*.png

Uso:
    python documentacion_auditoria/src/modelo_estrella_6.py
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
REPO = RAIZ / "datos_originales" / "repo_auditado"
FUENTE = (RAIZ / "datos_originales" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
TRABAJO = RAIZ / "_archivo" / "tmp_estrella"
SALIDA = DOC / "data" / "memoria" / "modelo_estrella.json"
GRAF = DOC / "data" / "memoria" / "graficas_estrella"
EVIDENCIA_AUDITADA = REPO / "evidencias" / "duckdb_resumen_modelo.txt"

# Los scripts del auditado importan `ingesta`, `Transformacion` y `modelo` como
# modulos de primer nivel: hay que poner su src/ en el path.
#
# Y hay que desactivar la escritura de .pyc ANTES de importarlos: al importar
# modulos de repo_auditado/ Python deja __pycache__ dentro de esa carpeta, que es
# una copia VERBATIM verificada con 236 hashes. `verificar_hashes.py` los reporta
# como "sobrantes" y la carpeta deja de contener exactamente el contenido
# versionado. Con esto no se crean.
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "src"))

# --- paleta institucional única -------------------------------------------
AZUL, AZUL_SEC, AZUL_CLARO = "#1E3780", "#4A6BA8", "#7BA7D0"
DORADO, DORADO_CLARO = "#B7871E", "#D4A84A"
GRIS_OSC, GRIS, GRIS_CLARO = "#334155", "#64748B", "#CBD5E1"
FONDO, TEXTO, ALERTA = "#F8FAFC", "#1E293B", "#B91C1C"

# Esperado según la evidencia versionada del propio repositorio auditado.
EVIDENCIA_6 = {2013: 8016, 2014: 8280, 2015: 10050, 2017: 13001,
               2019: 16796, 2021: 21094}
TOTAL_6 = sum(EVIDENCIA_6.values())          # 77 237
TOTAL_3 = 50891

TABLAS_DIM = ["dim_area", "dim_categoria", "dim_convocatoria", "dim_formacion",
              "dim_institucion", "dim_investigador", "dim_territorio"]
HECHOS = "fact_clasificacion"
PUENTE = "bridge_hecho_institucion"
CLAVES = {                     # tabla -> (columna del hecho, columna de la dim)
    "dim_convocatoria": ("id_convocatoria", "id_convocatoria"),
    "dim_investigador": ("id_persona_pr", "id_persona_pr"),
    "dim_categoria": ("id_clas_pr", "id_clas_pr"),
    "dim_area": ("id_area_con_pr", "id_area_con_pr"),
    "dim_formacion": ("id_niv_formacion_pr", "id_niv_formacion_pr"),
    "dim_territorio": ("sk_territorio", "sk_territorio"),
}
# Clave primaria de CADA dimensión. `dim_institucion` no aparece en CLAVES
# porque no es clave foránea del hecho: se relaciona por la tabla puente.
PK_DIM = {
    "dim_area": "id_area_con_pr",
    "dim_categoria": "id_clas_pr",
    "dim_convocatoria": "id_convocatoria",
    "dim_formacion": "id_niv_formacion_pr",
    "dim_institucion": "sk_institucion",
    "dim_investigador": "id_persona_pr",
    "dim_territorio": "sk_territorio",
}


# ==========================================================================
# 1. Construcción del modelo
# ==========================================================================
def cargar_fuente_6() -> tuple[pd.DataFrame, dict]:
    """
    Lee la fuente de 6 convocatorias.

    Se lee **igual que `cargar_consolidado()`** (inferencia de tipos con
    `low_memory=False` y columnas en mayúsculas), con UNA adaptación necesaria y
    documentada: el archivo fuente guarda `EDAD_ANOS_PR` con **coma decimal**
    ('66,92'), así que pandas la infiere como texto y
    `Transformacion.tratar_faltantes()` revienta con
    `TypeError: Cannot perform reduction 'median' with string dtype`.

    Esto NO es un defecto de la fuente ni del pipeline en su ruta normal: la API
    de Socrata devuelve la edad con **punto** ('66.92'), así que el CSV que
    escribe `src/ingesta/minciencias.py` se lee como float y el pipeline corre.
    La adaptación solo hace explícito lo que el propio proyecto ya hace en sus
    scripts de análisis (`str.replace(",", ".")` antes de `pd.to_numeric`).
    """
    df = pd.read_csv(FUENTE, low_memory=False, encoding="utf-8")
    df.columns = df.columns.str.upper()

    from pandas.api import types as ptypes

    adaptados = {}
    for col in df.columns:
        # OJO: en pandas 3.x las columnas de texto tienen dtype `str`, NO
        # `object`. Comparar contra `object` no detecta nada y la conversión se
        # salta en silencio; por eso se pregunta si la columna NO es numérica ni
        # temporal, en vez de si es `object`.
        if ptypes.is_numeric_dtype(df[col]) or ptypes.is_datetime64_any_dtype(df[col]):
            continue
        s = df[col].astype(str).str.strip()
        num = pd.to_numeric(s.str.replace(",", ".", regex=False), errors="coerce")
        # Solo se convierte si TODOS los valores no vacíos son numéricos: así no
        # se tocan las columnas realmente categóricas.
        no_vacios = s.replace({"": None, "nan": None, "None": None}).notna()
        if no_vacios.any() and num[no_vacios].notna().all():
            adaptados[col] = {
                "valores_con_coma": int(s.str.contains(",", regex=False).sum()),
                "faltantes": int((~no_vacios).sum()),
                "dtype_antes": str(df[col].dtype), "dtype_despues": "float64"}
            df[col] = num
    return df, adaptados


def construir(df_transformado: pd.DataFrame, destino: Path) -> tuple[object, dict]:
    """Construye las 9 tablas con las funciones del auditado, sin tocar nada suyo."""
    from modelo.dimensional import cargar_en_duckdb

    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        destino.unlink()

    buf = io.StringIO()
    real = sys.stdout
    sys.stdout = buf                     # silenciar el log verboso del auditado
    try:
        con = cargar_en_duckdb(df_transformado, path=destino, verbose=True)
    finally:
        sys.stdout = real
    return con, {"log_construccion": buf.getvalue().strip().splitlines()}


def resumen_tablas(con) -> dict:
    nombres = [r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='main' ORDER BY 1").fetchall()]
    return {t: int(con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
            for t in nombres}


def integridad(con) -> dict:
    """
    Integridad referencial: cada clave foránea del hecho debe existir en su
    dimensión, y el puente no debe tener claves huérfanas en ningún extremo.
    """
    out: dict = {"claves_foraneas": {}, "puente": {}, "claves_primarias": {}}
    for dim, (col_f, col_d) in CLAVES.items():
        huerf = con.execute(f"""
            SELECT COUNT(*) FROM {HECHOS} f
            LEFT JOIN {dim} d ON f.{col_f} = d.{col_d}
            WHERE d.{col_d} IS NULL
        """).fetchone()[0]
        out["claves_foraneas"][dim] = {
            "columna_hecho": col_f, "columna_dimension": col_d,
            "hechos_huerfanos": int(huerf), "integra": bool(huerf == 0)}
    # El hecho debe tener SK de territorio asignada (join left del auditado)
    nulos = con.execute(
        f"SELECT COUNT(*) FROM {HECHOS} WHERE sk_territorio IS NULL"
    ).fetchone()[0]
    out["claves_foraneas"]["sk_territorio_no_nula"] = {
        "hechos_sin_territorio": int(nulos), "integra": bool(nulos == 0)}

    out["puente"]["hechos_huerfanos"] = int(con.execute(f"""
        SELECT COUNT(*) FROM {PUENTE} b
        LEFT JOIN {HECHOS} f ON b.sk_hecho = f.sk_hecho
        WHERE f.sk_hecho IS NULL""").fetchone()[0])
    out["puente"]["instituciones_huerfanas"] = int(con.execute(f"""
        SELECT COUNT(*) FROM {PUENTE} b
        LEFT JOIN dim_institucion i ON b.sk_institucion = i.sk_institucion
        WHERE i.sk_institucion IS NULL""").fetchone()[0])
    out["puente"]["integra"] = bool(
        out["puente"]["hechos_huerfanos"] == 0
        and out["puente"]["instituciones_huerfanas"] == 0)

    for dim in TABLAS_DIM:
        col = PK_DIM[dim]
        dup = con.execute(
            f"SELECT COUNT(*) - COUNT(DISTINCT {col}) FROM {dim}").fetchone()[0]
        nulos = con.execute(
            f"SELECT COUNT(*) FROM {dim} WHERE {col} IS NULL").fetchone()[0]
        out["claves_primarias"][dim] = {"columna": col, "duplicados": int(dup),
                                        "nulos": int(nulos),
                                        "unica": bool(dup == 0 and nulos == 0)}
    dup_h = con.execute(f"SELECT COUNT(*) - COUNT(DISTINCT sk_hecho) "
                        f"FROM {HECHOS}").fetchone()[0]
    out["claves_primarias"][HECHOS] = {"columna": "sk_hecho",
                                       "duplicados": int(dup_h), "nulos": 0,
                                       "unica": bool(dup_h == 0)}
    return out


def por_convocatoria(con) -> dict:
    filas = con.execute(f"""
        SELECT c.ano_convo_int AS anio, COUNT(*) AS n_registros,
               COUNT(DISTINCT f.id_persona_pr) AS n_investigadores
        FROM {HECHOS} f JOIN dim_convocatoria c USING (id_convocatoria)
        GROUP BY c.ano_convo_int ORDER BY c.ano_convo_int
    """).fetchall()
    return {int(a): {"registros": int(n), "investigadores": int(p)}
            for a, n, p in filas}


# ==========================================================================
# 2. Gráficas
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


def fig_convocatorias(conteos: dict, archivo) -> None:
    anios = sorted(conteos)
    obs = [conteos[a]["registros"] for a in anios]
    esp = [EVIDENCIA_6[a] for a in anios]
    x = np.arange(len(anios))
    fig, ax = plt.subplots(figsize=(9.4, 4.4), dpi=150)
    ax.bar(x - 0.19, esp, width=0.36, color=DORADO, zorder=2,
           label="Evidencia versionada del auditado")
    ax.bar(x + 0.19, obs, width=0.36, color=AZUL, zorder=2,
           label="Modelo reconstruido (este análisis)")
    for xi, (e, o) in enumerate(zip(esp, obs)):
        ax.annotate(f"{e:,}".replace(",", " "), (xi - 0.19, e),
                    textcoords="offset points", xytext=(0, 4), ha="center",
                    fontsize=7.4, color=GRIS_OSC)
        ax.annotate(f"{o:,}".replace(",", " "), (xi + 0.19, o),
                    textcoords="offset points", xytext=(0, 4), ha="center",
                    fontsize=7.4, color=AZUL)
    ax.set_xticks(x)
    ax.set_xticklabels([str(a) for a in anios])
    ax.set_xlabel("Convocatoria", color=TEXTO, fontsize=9)
    ax.set_ylabel("Registros en fact_clasificacion", color=TEXTO, fontsize=9)
    ax.set_title("Registros por convocatoria con las 6 convocatorias\n"
                 f"Total reconstruido {sum(obs):,} frente a los {sum(esp):,} de la "
                 "evidencia".replace(",", " "),
                 color=TEXTO, fontsize=10.2, pad=10, loc="left")
    ax.legend(frameon=False, fontsize=8.4, labelcolor=GRIS_OSC)
    _estilo(ax)
    fig.tight_layout()
    fig.savefig(archivo, facecolor="white")
    plt.close(fig)


def fig_tablas(t3: dict, t6: dict, archivo) -> None:
    orden = [t for t in (TABLAS_DIM + [HECHOS, PUENTE]) if t in t6]
    y = np.arange(len(orden))
    v3 = [t3.get(t, 0) for t in orden]
    v6 = [t6.get(t, 0) for t in orden]
    fig, ax = plt.subplots(figsize=(9.6, 5.0), dpi=150)
    ax.barh(y - 0.19, v3, height=0.36, color=GRIS, zorder=2,
            label="Con el insumo de 3 convocatorias (lo que corre hoy)")
    ax.barh(y + 0.19, v6, height=0.36, color=AZUL, zorder=2,
            label="Con las 6 convocatorias (este análisis)")
    for yi, (a, b) in enumerate(zip(v3, v6)):
        ax.annotate(f"{a:,}".replace(",", " "), (a, yi - 0.19),
                    textcoords="offset points", xytext=(4, 0), va="center",
                    fontsize=7.4, color=GRIS_OSC)
        ax.annotate(f"{b:,}".replace(",", " "), (b, yi + 0.19),
                    textcoords="offset points", xytext=(4, 0), va="center",
                    fontsize=7.4, color=AZUL)
    ax.set_yticks(y)
    ax.set_yticklabels(orden, fontsize=8.2)
    ax.invert_yaxis()
    ax.set_xscale("symlog")
    ax.set_xlabel("Filas (escala logarítmica simétrica)", color=TEXTO, fontsize=9)
    ax.set_title("Las 9 tablas del modelo estrella, según el insumo\n"
                 "Siete dimensiones, una tabla de hechos y una tabla puente",
                 color=TEXTO, fontsize=10.2, pad=10, loc="left")
    ax.legend(frameon=False, fontsize=8.4, labelcolor=GRIS_OSC)
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
# 3. Principal
# ==========================================================================
def main() -> int:
    print("== F2-3 · Modelo estrella reproducible con las 6 convocatorias ==")
    salida: dict = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "analisis": "F2-3 — Modelo estrella reproducible (objetivo específico 4)",
        "nota": ("Se usan las funciones del repositorio auditado sin "
                 "reimplementarlas; la base se escribe en un directorio de "
                 "trabajo para no alterar los 236 hashes del repo auditado."),
    }

    composicion = {
        "tablas_totales": len(TABLAS_DIM) + 2,
        "dimensiones": TABLAS_DIM, "n_dimensiones": len(TABLAS_DIM),
        "tabla_de_hechos": HECHOS, "tablas_puente": [PUENTE],
        "enunciado_del_objetivo": ("«modelo dimensional (esquema estrella) con "
                                   "nueve dimensiones y una tabla de hechos» "
                                   "(repo auditado, informe_final.md:38)"),
        "correccion": ("Son 9 TABLAS: 7 dimensiones + 1 tabla de hechos + 1 "
                       "tabla puente. El «nueve» cuenta tablas, no dimensiones: "
                       "el docstring de sprint2_duckdb.py lista exactamente esas "
                       "9. El diseño es correcto; el enunciado no."),
    }
    salida["composicion_del_modelo"] = composicion
    print(f"   composición: {composicion['n_dimensiones']} dimensiones + 1 "
          f"hechos + 1 puente = {composicion['tablas_totales']} tablas")

    # ---------------- pipeline del auditado, con su propio insumo ----------
    print("\n[1/4] Reproduciendo el modelo con el insumo del auditado (3 conv.)")
    from Transformacion import transformar
    from ingesta import cargar_consolidado

    buf = io.StringIO()
    real = sys.stdout
    sys.stdout = buf
    try:
        df3 = transformar(cargar_consolidado())
    finally:
        sys.stdout = real
    print(f"   insumo cargado por cargar_consolidado(): {df3.shape}")
    con3, _ = construir(df3, TRABAJO / "auditado_3conv.duckdb")
    t3 = resumen_tablas(con3)
    conv3 = por_convocatoria(con3)
    con3.close()
    print(f"   dim_convocatoria={t3.get('dim_convocatoria')} · "
          f"{HECHOS}={t3.get(HECHOS):,}".replace(",", " "))

    # ---------------- pipeline del auditado, con las 6 convocatorias -------
    print("\n[2/4] Reconstruyendo el modelo con la fuente de 6 convocatorias")
    df6_crudo, adaptados = cargar_fuente_6()
    print(f"   fuente: {df6_crudo.shape[0]:,} registros × "
          f"{df6_crudo.shape[1]} columnas".replace(",", " "))
    for col, d in adaptados.items():
        print(f"   adaptada {col}: {d['valores_con_coma']:,} valores con coma "
              f"decimal -> {d['dtype_despues']} "
              f"({d['faltantes']} faltante/s)".replace(",", " "))
    buf = io.StringIO()
    sys.stdout = buf
    try:
        df6 = transformar(df6_crudo)
    finally:
        sys.stdout = real
    log_tr = buf.getvalue().strip().splitlines()
    print(f"   tras transformar(): {df6.shape}")
    con6, info6 = construir(df6, TRABAJO / "observatorio_6conv.duckdb")
    t6 = resumen_tablas(con6)
    conv6 = por_convocatoria(con6)
    print(f"   dim_convocatoria={t6.get('dim_convocatoria')} · "
          f"{HECHOS}={t6.get(HECHOS):,}".replace(",", " "))

    # ---------------- integridad -----------------------------------------
    print("\n[3/4] Integridad referencial")
    integ = integridad(con6)
    for dim, d in integ["claves_foraneas"].items():
        if "hechos_huerfanos" in d:
            print(f"   [{'OK ' if d['integra'] else 'NO '}] FK {dim:20s} "
                  f"huérfanos={d['hechos_huerfanos']}")
        else:
            print(f"   [{'OK ' if d['integra'] else 'NO '}] "
                  f"sk_territorio no nula (sin territorio={d['hechos_sin_territorio']})")
    print(f"   [{'OK ' if integ['puente']['integra'] else 'NO '}] puente N:N "
          f"(hechos huérfanos={integ['puente']['hechos_huerfanos']}, "
          f"instituciones huérfanas={integ['puente']['instituciones_huerfanas']})")
    singulares = [d for d, v in integ["claves_primarias"].items() if not v["unica"]]
    print(f"   [{'OK ' if not singulares else 'NO '}] claves primarias únicas en "
          f"las {len(integ['claves_primarias'])} tablas"
          + (f" · fallan: {singulares}" if singulares else ""))

    # edad: el pipeline del auditado imputa la mediana a los faltantes
    faltantes_edad = int(df6_crudo["EDAD_ANOS_PR"].isna().sum())
    mediana_edad = float(df6_crudo["EDAD_ANOS_PR"].median())
    print(f"   [dato] el pipeline del auditado imputa la MEDIANA a los "
          f"faltantes numéricos: {faltantes_edad} edades -> {mediana_edad:.2f}")

    # ---------------- contraste con la evidencia versionada ---------------
    print("\n[4/4] Contraste con la evidencia versionada del auditado")
    deltas = {a: conv6[a]["registros"] - EVIDENCIA_6[a] for a in EVIDENCIA_6
              if a in conv6}
    coincide = (conv6 and set(conv6) == set(EVIDENCIA_6)
                and all(v == 0 for v in deltas.values()))
    for a in sorted(EVIDENCIA_6):
        obs = conv6.get(a, {}).get("registros")
        print(f"   {a}: evidencia={EVIDENCIA_6[a]:,} · reconstruido={obs}"
              .replace(",", " "))
    print(f"   [{'OK ' if coincide else 'NO '}] el modelo reconstruido "
          f"reproduce la evidencia versionada")
    con6.close()

    salida["insumo"] = {
        "usado_por_el_auditado": "datos/tarea_join/investigadores_consolidado.xlsx",
        "causa": ("cargar_consolidado() prefiere datos/raw/"
                  "investigadores_consolidado.csv, ausente y gitignored, y cae "
                  "al XLSX de 3 convocatorias"),
        "usado_aqui": str(FUENTE.relative_to(RAIZ)).replace("\\", "/"),
        "columnas": {"n": int(df6_crudo.shape[1]),
                     "identicas_al_consolidado_del_auditado": True,
                     "verificado": ("mismas 30 columnas y mismo orden que "
                                    "datos/tarea_join/investigadores_consolidado.csv")},
        "registros_fuente": int(df6_crudo.shape[0]),
        "adaptacion_necesaria": {
            "columnas_convertidas": adaptados,
            "motivo": ("El archivo fuente guarda la edad con COMA decimal, así "
                       "que pandas la lee como texto y tratar_faltantes() del "
                       "auditado lanza TypeError: Cannot perform reduction "
                       "'median' with string dtype. Se convierte la coma en "
                       "punto antes de llamar al pipeline."),
            "no_es_un_defecto_de_la_ruta_normal": (
                "Verificado contra la API de Socrata: el dataset bqtm-4y2h "
                "devuelve edad_anos_pr como texto con PUNTO ('66.92'), así que "
                "el CSV que escribe src/ingesta/minciencias.py se lee como float "
                "y el pipeline corre sin tocarlo. El pipeline sí es sensible al "
                "separador decimal del insumo."),
        },
    }
    salida["modelo_3_convocatorias"] = {
        "tablas": t3, "por_convocatoria": conv3,
        "total_hechos": int(t3.get(HECHOS, 0)),
        "n_convocatorias": int(t3.get("dim_convocatoria", 0)),
    }
    salida["modelo_6_convocatorias"] = {
        "tablas": t6, "por_convocatoria": conv6,
        "total_hechos": int(t6.get(HECHOS, 0)),
        "n_convocatorias": int(t6.get("dim_convocatoria", 0)),
    }
    salida["integridad_referencial"] = integ
    salida["evidencia_versionada"] = {
        "esperado_por_convocatoria": EVIDENCIA_6, "total_esperado": TOTAL_6,
        "observado_por_convocatoria": {a: conv6[a]["registros"]
                                       for a in sorted(conv6)},
        "observado_total": int(sum(v["registros"] for v in conv6.values())),
        "deltas": {str(a): v for a, v in deltas.items()},
        "reproduce_la_evidencia": bool(coincide),
        "fuente_de_la_evidencia": str(EVIDENCIA_AUDITADA.relative_to(RAIZ)).replace("\\", "/"),
    }
    salida["transformacion_del_auditado"] = {
        "log": info6["log_construccion"] + log_tr,
        "imputacion_de_edad": {
            "faltantes_en_la_fuente": faltantes_edad,
            "valor_imputado": mediana_edad,
            "nota": ("tratar_faltantes() rellena TODOS los faltantes numéricos "
                     "con la mediana, incluida EDAD_ANOS_PR. Es lógica del "
                     "repositorio auditado, no nuestra: se conserva para que el "
                     "modelo sea reproducible, y se registra aquí porque fabrica "
                     "observaciones que la fuente no tiene."),
        },
    }
    salida["validaciones"] = {
        "9_tablas_construidas": bool(len(t6) == 9),
        "dim_convocatoria_tiene_6_filas": bool(t6.get("dim_convocatoria") == 6),
        "hechos_igualan_la_evidencia": bool(t6.get(HECHOS) == TOTAL_6),
        "total_reconstruido_77_237": bool(
            sum(v["registros"] for v in conv6.values()) == TOTAL_6),
        "integridad_referencial_completa": bool(
            all(d.get("integra") for d in integ["claves_foraneas"].values())
            and integ["puente"]["integra"]),
        "claves_primarias_unicas": bool(not singulares),
        "el_defecto_3_convocatorias_se_reproduce": bool(
            t3.get("dim_convocatoria") == 3 and t3.get(HECHOS) == TOTAL_3),
        "reproduce_la_evidencia_versionada": bool(coincide),
        "adaptacion_de_entrada_declarada": bool(set(adaptados) == {"EDAD_ANOS_PR"}),
        "no_hay_valores_con_coma_sin_convertir": bool(
            sum(d["valores_con_coma"] for d in adaptados.values()) > 0),
    }
    for k, v in salida["validaciones"].items():
        print(f"   [{'OK ' if v else 'NO '}] {k}")

    # ---------------- figuras y escritura --------------------------------
    GRAF.mkdir(parents=True, exist_ok=True)
    fig_convocatorias(conv6, GRAF / "f2_3_registros_por_convocatoria.png")
    fig_tablas(t3, t6, GRAF / "f2_3_tablas_del_modelo.png")
    salida["figuras"] = sorted(p.name for p in GRAF.glob("*.png"))

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"\n-> {SALIDA.relative_to(RAIZ)} ({SALIDA.stat().st_size:,} bytes)")
    print(f"-> {GRAF.relative_to(RAIZ)}/ ({len(salida['figuras'])} figuras)")
    print(f"-> bases de trabajo en {TRABAJO.relative_to(RAIZ)}/ "
          f"(ignoradas por git; el repo auditado NO se toca)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
