# -*- coding: utf-8 -*-
"""
streamlit_app.py

Dashboard del Observatorio MinCiencias.

Estructura: 6 secciones tipo capitulos del informe critico final.
Cada seccion sigue el patron pregunta -> evidencia -> takeaway -> caveat.

Ejecucion:
    streamlit run streamlit_app.py
"""

import pathlib
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from ingesta import cargar_consolidado, cargar_produccion  # noqa: E402
from Transformacion import transformar  # noqa: E402
from analisis.longitudinal import construir_panel, comparar_periodo, matriz_transicion  # noqa: E402
from analisis.territorial import hhi_por_convocatoria  # noqa: E402
from analisis.genero import tabla_pivot_pct_femenino  # noqa: E402
from analisis.diversidad import (  # noqa: E402
    cobertura_por_convocatoria,
    distribucion_categoria,
    comparar_dane,
)
from analisis.redes import normalizar_institucion  # noqa: E402
from analisis.produccion import (  # noqa: E402
    normalizar_produccion,
    cobertura_reconocidos,
    cobertura_autores_unicos,
    productividad_por_categoria,
    brecha_productividad_genero,
    productividad_territorial,
    mix_tipologias,
    reconocidos_sin_produccion,
)

# ---------------------------------------------------------------------------
# Configuracion de pagina
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Observatorio MinCiencias — Informe critico",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
COORDENADAS_DEPTO = {
    "AMAZONAS": (-1.44, -71.57), "ANTIOQUIA": (7.19, -75.34),
    "ARAUCA": (6.54, -71.00),
    "ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA": (12.53, -81.72),
    "ATLÁNTICO": (10.69, -74.87), "BOGOTÁ, D. C.": (4.71, -74.07),
    "BOLÍVAR": (8.67, -74.03), "BOYACÁ": (5.45, -73.36),
    "CALDAS": (5.30, -75.27), "CAQUETÁ": (1.61, -75.61),
    "CASANARE": (5.75, -71.57), "CAUCA": (2.53, -76.62),
    "CESAR": (9.33, -73.50), "CHOCÓ": (5.69, -76.66),
    "CÓRDOBA": (8.39, -75.51), "CUNDINAMARCA": (5.03, -74.01),
    "GUAINÍA": (2.58, -68.53), "GUAVIARE": (2.57, -72.67),
    "HUILA": (2.53, -75.52), "LA GUAJIRA": (11.35, -72.48),
    "MAGDALENA": (10.41, -74.41), "META": (3.99, -73.56),
    "NARIÑO": (1.28, -77.35), "NORTE DE SANTANDER": (7.94, -72.50),
    "PUTUMAYO": (0.44, -76.64), "QUINDÍO": (4.46, -75.67),
    "RISARALDA": (5.31, -75.98), "SANTANDER": (6.64, -73.65),
    "SUCRE": (9.30, -75.40), "TOLIMA": (4.09, -75.15),
    "VALLE DEL CAUCA": (3.80, -76.51), "VAUPÉS": (0.86, -70.81),
    "VICHADA": (4.42, -69.59),
}

# Poblacion DANE 2018 por departamento (miles de habitantes)
POBLACION_DANE_2018 = {
    "BOGOTÁ, D. C.": 7181, "ANTIOQUIA": 6407, "VALLE DEL CAUCA": 4476,
    "CUNDINAMARCA": 2919, "ATLÁNTICO": 2536, "SANTANDER": 2101,
    "BOLÍVAR": 2070, "CÓRDOBA": 1763, "NARIÑO": 1631, "TOLIMA": 1331,
    "MAGDALENA": 1342, "BOYACÁ": 1217, "NORTE DE SANTANDER": 1346,
    "HUILA": 1100, "CAUCA": 1244, "CESAR": 1099, "META": 1040,
    "CALDAS": 998, "RISARALDA": 943, "SUCRE": 904, "LA GUAJIRA": 880,
    "QUINDÍO": 539, "CHOCÓ": 535, "CASANARE": 380, "CAQUETÁ": 401,
    "PUTUMAYO": 350, "ARAUCA": 263, "AMAZONAS": 76, "GUAVIARE": 82,
    "VICHADA": 76, "GUAINÍA": 48, "VAUPÉS": 37,
    "ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA": 61,
}

CAT_CORTA = {
    "INVESTIGADOR JUNIOR": "Junior",
    "INVESTIGADOR ASOCIADO": "Asociado",
    "INVESTIGADOR SÉNIOR": "Sénior",
    "INVESTIGADOR EMÉRITO": "Emérito",
}

# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Cargando 77.237 registros…")
def cargar_datos() -> pd.DataFrame:
    df = transformar(cargar_consolidado())
    df["edad_valida"] = (df["EDAD_ANOS_PR"] <= 100) | df["EDAD_ANOS_PR"].isna()
    return df


# normalizar_institucion ahora vive en src/analisis/redes.py — se importa arriba


# ---------------------------------------------------------------------------
# Sidebar — filtros
# ---------------------------------------------------------------------------
def sidebar_filtros(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    st.sidebar.title("🔎 Filtros")
    st.sidebar.caption("Los filtros se aplican a todas las secciones.")

    anios = sorted(df["ANO_CONVO_INT"].dropna().unique().tolist())
    anios_sel = st.sidebar.multiselect("Año de convocatoria", anios, default=anios)

    generos = sorted(df["NME_GENERO_PR"].dropna().unique().tolist())
    generos_sel = st.sidebar.multiselect("Género", generos, default=generos)

    areas = sorted(df["NME_GRAN_AREA_PR"].dropna().unique().tolist())
    areas_sel = st.sidebar.multiselect("Gran área OCDE", areas, default=areas)

    deptos_top = df["NME_DEPARTAMENTO_RES_PR"].value_counts().head(15).index.tolist()
    deptos_sel = st.sidebar.multiselect(
        "Departamento (top 15)", deptos_top, default=[],
        help="Vacío = todos los departamentos",
    )

    cats = sorted(df["NME_CLASIFICACION_PR"].dropna().unique().tolist())
    cats_sel = st.sidebar.multiselect("Categoría", cats, default=cats)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Calidad")
    excluir_calidad = st.sidebar.checkbox(
        "Excluir registros con problemas de calidad",
        value=False,
        help="Quita: edad >100, depto NO DISPONIBLE, género NO REPORTADO",
    )

    mascara = (
        df["ANO_CONVO_INT"].isin(anios_sel)
        & df["NME_GENERO_PR"].isin(generos_sel)
        & df["NME_GRAN_AREA_PR"].isin(areas_sel)
        & df["NME_CLASIFICACION_PR"].isin(cats_sel)
    )
    if deptos_sel:
        mascara &= df["NME_DEPARTAMENTO_RES_PR"].isin(deptos_sel)

    if excluir_calidad:
        mascara &= df["edad_valida"]
        mascara &= df["NME_DEPARTAMENTO_RES_PR"] != "NO DISPONIBLE"
        mascara &= df["NME_GENERO_PR"] != "NO REPORTADO"

    metadatos = {
        "n_total": len(df),
        "n_filtrado": int(mascara.sum()),
        "excluir_calidad": excluir_calidad,
    }
    return df[mascara].copy(), metadatos


# ---------------------------------------------------------------------------
# Cabecera + tarjetas de hallazgos criticos
# ---------------------------------------------------------------------------
def cabecera(df_full: pd.DataFrame) -> None:
    st.title("🔬 Observatorio MinCiencias — Investigadores Reconocidos")
    st.caption(
        "Análisis crítico de 6 convocatorias (2013-2021) · 77.237 registros · "
        "30.086 investigadores únicos · Universidad Santo Tomás · Ustadistica 2026-I"
    )

    with st.container():
        st.markdown(
            """
            > **Esta no es una infografía.** Es una herramienta de auditoría sobre
            > el sistema de reconocimiento de investigadores de MinCiencias.
            > Cada sección formula una pregunta y muestra la evidencia,
            > incluyendo las falencias de los datos y los sesgos del sistema.
            """
        )

    st.markdown("### 📌 Hallazgos críticos")
    cols = st.columns(6)
    bog = (df_full["NME_DEPARTAMENTO_RES_PR"] == "BOGOTÁ, D. C.").sum()
    bog_pct = bog / len(df_full) * 100
    cols[0].metric("Concentración Bogotá", f"{bog_pct:.0f}%",
                   help="Proporción de registros en Bogotá D.C.")

    fem = (df_full["NME_GENERO_PR"] == "FEMENINO").sum()
    masc = (df_full["NME_GENERO_PR"] == "MASCULINO").sum()
    cols[1].metric("Mujeres (global)", f"{fem/(fem+masc)*100:.1f}%",
                   help="Excluyendo NO REPORTADO")

    edades_invalidas = (df_full["EDAD_ANOS_PR"] > 100).sum()
    cols[2].metric("Edades imposibles", f"{int(edades_invalidas)}",
                   help="Registros con edad > 100 años")

    cobertura_etnia_global = (df_full["TXT_GRUPO_ETNICO"] != "NO DISPONIBLE").mean() * 100
    cols[3].metric("Cobertura etnia", f"{cobertura_etnia_global:.0f}%",
                   help="Solo capturada desde 2021")

    n_inst = df_full["INST_FILIA"].dropna().str.split("|").explode().str.strip().str.upper().nunique()
    cols[4].metric("Instituciones únicas", f"{n_inst:,}",
                   help="Sin normalizar — incluye sedes y variantes")

    n_unicos = df_full["ID_PERSONA_PR"].nunique()
    cols[5].metric("Investigadores únicos", f"{n_unicos:,}",
                   help="Distintos por ID_PERSONA_PR")


# ---------------------------------------------------------------------------
# Helper de presentacion
# ---------------------------------------------------------------------------
def narrativa(pregunta: str, takeaway: str, caveat: str) -> None:
    st.markdown(f"**Pregunta.** {pregunta}")
    col1, col2 = st.columns([1, 1])
    col1.success(f"**Hallazgo:** {takeaway}")
    col2.warning(f"**Caveat:** {caveat}")


# ---------------------------------------------------------------------------
# Seccion 1: Calidad de los datos
# ---------------------------------------------------------------------------
def seccion_calidad(df: pd.DataFrame) -> None:
    st.header("1️⃣ Calidad de los datos — ¿qué tan confiable es la fuente?")
    narrativa(
        pregunta="¿La información que MinCiencias publica permite analizar el sistema "
                 "de manera confiable y comparable entre convocatorias?",
        takeaway="No. Hay vacíos sistemáticos de captura, etiquetas administrativas "
                 "que no coinciden con la realidad operativa, y una explosión de "
                 "instituciones únicas que en realidad son la misma con varios nombres.",
        caveat="Lo que el dashboard muestra después de este filtro es lo mejor "
               "que se puede inferir; las decisiones de política basadas en estos "
               "datos heredan las falencias del registro.",
    )

    st.subheader("Cobertura de variables clave por convocatoria")
    cob = cobertura_por_convocatoria(df)
    cob_plot = cob.set_index("ANO_CONVO_INT")[
        ["ID_VICTIMA_CONFLICTO_pct_cobertura",
         "TXT_GRUPO_ETNICO_pct_cobertura",
         "TXT_POBLACION_DISCA_pct_cobertura"]
    ]
    cob_plot.columns = ["Víctima conflicto", "Grupo étnico", "Discapacidad"]
    fig = px.imshow(
        cob_plot.T, text_auto=".1f", aspect="auto",
        color_continuous_scale="RdYlGn", zmin=0, zmax=100,
        labels={"x": "Convocatoria", "y": "Variable", "color": "% cobertura"},
        title="% de registros con dato real (verde = cubierto, rojo = NO REGISTRA)",
    )
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Las variables de diversidad son **invisibles antes de 2021**. "
        "Cualquier análisis longitudinal sobre etnia, discapacidad o víctima del "
        "conflicto es estructuralmente imposible."
    )

    st.subheader("Anomalías detectadas")
    anomalias = pd.DataFrame([
        {"Anomalía": "Edad > 100 años",
         "Registros": int((df["EDAD_ANOS_PR"] > 100).sum()),
         "Detalle": f"Máximo: {df['EDAD_ANOS_PR'].max():.0f} años"},
        {"Anomalía": "Departamento NO DISPONIBLE",
         "Registros": int((df["NME_DEPARTAMENTO_RES_PR"] == "NO DISPONIBLE").sum()),
         "Detalle": "Sin geolocalización posible"},
        {"Anomalía": "Género NO REPORTADO",
         "Registros": int((df["NME_GENERO_PR"] == "NO REPORTADO").sum()),
         "Detalle": "No se puede analizar brecha"},
        {"Anomalía": "Departamento EXTERIOR",
         "Registros": int((df["NME_DEPARTAMENTO_RES_PR"] == "EXTERIOR").sum()),
         "Detalle": "Investigadores residentes fuera de Colombia"},
        {"Anomalía": "Convocatoria 833 etiquetada como 2018, fechada 2019",
         "Registros": int((df["ID_CONVOCATORIA"] == 20).sum()) if "ID_CONVOCATORIA" in df.columns else 16796,
         "Detalle": "Etiqueta administrativa ≠ realidad"},
    ])
    st.dataframe(anomalias, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Seccion 2: Trayectoria longitudinal
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Construyendo panel longitudinal…")
def panel_completo(df_hash: int, df: pd.DataFrame) -> dict:
    panel = construir_panel(df)
    anios = sorted(panel["ANO_CONVO_INT"].dropna().unique())
    rows = []
    transiciones = {}
    for a0, a1 in zip(anios, anios[1:]):
        comp = comparar_periodo(panel, a0, a1)
        n0 = len(comp)
        retenidos_mask = comp["resultado"].isin(["Se mantiene", "Sube", "Baja"])
        ret = int(retenidos_mask.sum())
        rows.append({
            "Periodo": f"{int(a0)}→{int(a1)}",
            f"Investigadores iniciales": n0,
            "Retenidos": ret,
            "Tasa retención (%)": round(ret / n0 * 100, 1) if n0 else 0,
        })
        try:
            conteos, _ = matriz_transicion(comp, incluir_desaparece=True)
            transiciones[f"{int(a0)}→{int(a1)}"] = conteos
        except Exception:
            pass
    return {"retencion": pd.DataFrame(rows), "transiciones": transiciones}


def seccion_trayectoria(df: pd.DataFrame) -> None:
    st.header("2️⃣ Trayectoria longitudinal — ¿se quedan o desaparecen?")
    narrativa(
        pregunta="¿El sistema retiene a los investigadores reconocidos entre "
                 "convocatorias? ¿Suben o bajan de categoría?",
        takeaway="La retención global supera el 75%, pero los Eméritos desaparecen "
                 "completamente entre convocatorias y los criterios de clasificación "
                 "cambian de forma que vicia las comparaciones.",
        caveat="Se identifica al investigador por ID_PERSONA_PR. Si MinCiencias "
               "cambió esa llave en alguna convocatoria, parte del 'desaparece' "
               "es ruido administrativo, no realidad.",
    )

    st.subheader("Investigadores por convocatoria")
    conteo = (df.groupby("ANO_CONVO_INT").size()
              .reset_index(name="Investigadores")
              .rename(columns={"ANO_CONVO_INT": "Año"}))
    fig = px.bar(conteo, x="Año", y="Investigadores", text_auto=True,
                 color="Investigadores", color_continuous_scale="Blues",
                 title="Crecimiento del sistema en una década")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        f"De {conteo['Investigadores'].min():,} en {conteo.iloc[0]['Año']} a "
        f"{conteo['Investigadores'].max():,} en {conteo.iloc[-1]['Año']}: "
        "más del doble. Pero buena parte del crecimiento es por relajamiento "
        "de los criterios de Junior, no por capacidad real adicional."
    )

    if len(df) >= 100:
        try:
            datos = panel_completo(len(df), df)
            st.subheader("Tasa de retención entre convocatorias consecutivas")
            ret_df = datos["retencion"]
            if not ret_df.empty:
                fig_ret = px.line(ret_df, x="Periodo", y="Tasa retención (%)", markers=True,
                                  title="Retención (%) — el sistema mantiene 3 de cada 4 investigadores")
                fig_ret.update_yaxes(range=[0, 100])
                st.plotly_chart(fig_ret, use_container_width=True)
                st.dataframe(ret_df, use_container_width=True, hide_index=True)
            else:
                st.info("No hay suficientes convocatorias en el filtro para calcular retención.")

            transiciones = datos["transiciones"]
            if transiciones:
                st.subheader("Matriz de transición de categorías")
                periodo = st.selectbox("Periodo", list(transiciones.keys()))
                m = transiciones[periodo]
                fig_m = px.imshow(
                    m, text_auto=True, aspect="auto",
                    color_continuous_scale="Blues",
                    labels={"x": "Categoría destino", "y": "Categoría origen", "color": "N investigadores"},
                    title=f"Transiciones {periodo}",
                )
                st.plotly_chart(fig_m, use_container_width=True)
                st.caption(
                    "Las casillas de la diagonal muestran quien permanece en la misma categoría. "
                    "La fila Emérito está casi vacía hacia adelante: confirma que **los Eméritos "
                    "no aparecen en la siguiente convocatoria**."
                )
        except Exception as e:
            st.info(f"Análisis longitudinal no disponible para los filtros actuales: {e}")


# ---------------------------------------------------------------------------
# Seccion 3: Concentracion territorial
# ---------------------------------------------------------------------------
def seccion_territorial(df: pd.DataFrame) -> None:
    st.header("3️⃣ Concentración territorial — ¿el conocimiento es centralizado?")
    narrativa(
        pregunta="¿La capacidad investigativa de Colombia está distribuida "
                 "equitativamente o concentrada en unas pocas ciudades?",
        takeaway="Bogotá + Antioquia concentran el 51% del país. El HHI muestra "
                 "una concentración moderada-alta sostenida. Hay departamentos "
                 "enteros (Vichada, Vaupés, Guainía) con menos de 10 investigadores.",
        caveat="El conteo es por residencia del investigador, no por sede de la "
               "investigación. Y no se ajusta por población — un análisis per cápita "
               "(abajo) cambia el ranking.",
    )

    col = "NME_DEPARTAMENTO_RES_PR"
    conteo = df[col].value_counts().reset_index()
    conteo.columns = ["Departamento", "Investigadores"]
    conteo_geo = conteo[conteo["Departamento"].isin(COORDENADAS_DEPTO)].copy()
    conteo_geo["lat"] = conteo_geo["Departamento"].map(lambda d: COORDENADAS_DEPTO[d][0])
    conteo_geo["lon"] = conteo_geo["Departamento"].map(lambda d: COORDENADAS_DEPTO[d][1])

    st.subheader("Mapa de investigadores por departamento de residencia")
    fig = px.scatter_mapbox(
        conteo_geo, lat="lat", lon="lon",
        size="Investigadores", color="Investigadores",
        hover_name="Departamento",
        color_continuous_scale="YlOrRd", size_max=60,
        zoom=4.5, center={"lat": 4.5, "lon": -74.0},
        mapbox_style="open-street-map",
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=500)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Investigadores por cada 100 mil habitantes")
        st.caption("Se usa población DANE 2018 para normalizar el ranking territorial.")
        per_capita = conteo_geo.copy()
        per_capita["pob_miles"] = per_capita["Departamento"].map(POBLACION_DANE_2018)
        per_capita = per_capita.dropna(subset=["pob_miles"])
        per_capita["por_100k"] = per_capita["Investigadores"] / per_capita["pob_miles"] * 100
        per_capita = per_capita.sort_values("por_100k", ascending=False)
        fig_pc = px.bar(per_capita.head(15), x="por_100k", y="Departamento",
                        orientation="h", color="por_100k", color_continuous_scale="Greens",
                        labels={"por_100k": "Investigadores / 100k habitantes"},
                        title="Top 15 — densidad de investigadores")
        fig_pc.update_layout(yaxis={"autorange": "reversed"}, height=500)
        st.plotly_chart(fig_pc, use_container_width=True)

    with col2:
        st.subheader("Concentración (HHI) — ¿se concentra más con el tiempo?")
        try:
            hhi_df = hhi_por_convocatoria(df, col_geo=col).reset_index()
            hhi_df.columns = ["Año", "HHI"]
            fig_hhi = px.line(hhi_df, x="Año", y="HHI", markers=True,
                              title="HHI por convocatoria (mayor = más concentrado)")
            fig_hhi.add_hline(y=0.15, line_dash="dash", annotation_text="Umbral concentración moderada")
            fig_hhi.add_hline(y=0.25, line_dash="dash", line_color="red",
                              annotation_text="Umbral concentración alta")
            st.plotly_chart(fig_hhi, use_container_width=True)
        except Exception as e:
            st.info(f"HHI no disponible: {e}")

    top5 = conteo.head(5)["Investigadores"].sum()
    total = conteo["Investigadores"].sum()
    st.metric("Top 5 departamentos", f"{top5/total*100:.1f}% del total", help="Bogotá, Antioquia, Valle, Atlántico, Santander")


# ---------------------------------------------------------------------------
# Seccion 4: Genero y diversidad
# ---------------------------------------------------------------------------
def seccion_diversidad(df: pd.DataFrame) -> None:
    st.header("4️⃣ Brecha de género y diversidad — ¿quién está dentro del sistema?")
    narrativa(
        pregunta="¿La composición de los investigadores reconocidos refleja la "
                 "diversidad poblacional de Colombia?",
        takeaway="No. Las mujeres están en 37% global pero apenas 24% en Ingeniería. "
                 "Las minorías étnicas, las personas con discapacidad y las víctimas "
                 "del conflicto están subrepresentadas entre 3x y 8.6x respecto a su "
                 "peso poblacional según DANE.",
        caveat="Las variables de diversidad solo se capturan desde 2021. Toda la "
               "comparación es una foto fija del último año.",
    )

    st.subheader("Brecha de género por gran área OCDE (% femenino)")
    try:
        pivot = tabla_pivot_pct_femenino(df, col_area="NME_GRAN_AREA_PR")
        if "promedio" in pivot.columns:
            pivot = pivot.drop(columns="promedio")
        pivot = (pivot * 100).round(1)
        # Acortar etiquetas largas para que se lean
        pivot.index = [idx if len(idx) <= 30 else idx[:27] + "…" for idx in pivot.index]
        pivot.columns = [str(c) for c in pivot.columns]

        fig = px.imshow(
            pivot.values,
            x=pivot.columns,
            y=pivot.index,
            text_auto=".1f",
            color_continuous_scale="RdYlGn",
            zmin=0, zmax=60,
            aspect="auto",
            labels={"x": "Convocatoria", "y": "Gran área OCDE", "color": "% femenino"},
        )
        fig.update_layout(
            title="Verde = paridad (50%), rojo = brecha estructural",
            height=480,
            margin=dict(l=240, r=20, t=60, b=40),
            xaxis=dict(side="bottom"),
            yaxis=dict(tickfont=dict(size=11)),
            coloraxis_colorbar=dict(title="% F"),
        )
        fig.update_traces(textfont_size=12)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "**Ciencias Médicas** se acerca a la paridad (~48%). "
            "**Ingeniería y Tecnología** sigue por debajo del 25%, "
            "una brecha estable que no se ha reducido en una década."
        )
    except Exception as e:
        st.info(f"Análisis de género no disponible: {e}")

    st.subheader("Subrepresentación de minorías vs población colombiana")

    with st.expander("📖 Cómo se calcula la subrepresentación — léelo antes del gráfico", expanded=False):
        st.markdown("""
**Paso a paso del cálculo:**

1. Tomamos **solo la convocatoria 2021** (la única con datos de diversidad).
2. Excluimos los registros con `NO DISPONIBLE` (~3.2%, son no-respuesta).
3. De los ~20.420 que sí respondieron, contamos cuántos se autorreconocen
   como Afrocolombiano, Indígena, etc., y calculamos el **% sobre el total**.
4. Comparamos con el **% poblacional** según la fuente oficial correspondiente:
   - Etnia → DANE Censo Nacional de Población y Vivienda (CNPV) 2018
   - Discapacidad → DANE CNPV 2018
   - Víctima del conflicto → Registro Único de Víctimas (RUV), corte 31-dic-2021

5. **Razón de subrepresentación** = `% poblacional / % MinCiencias`.

**Cómo leer la razón:**
- Razón **3.0x** = "para reflejar la composición del país, debería haber 3 veces más
  investigadores afrocolombianos de los que hay".
- Razón **< 1.0** = sobrerrepresentación (hay MÁS proporción que en la población general).

**¿Por qué solo 2018 / por qué no hay cifras DANE 2021?**
DANE actualiza la composición étnica únicamente con cada **censo nacional**
(cada ~10 años). El último es CNPV 2018. La composición se asume estable hasta
el próximo censo. Por eso comparamos investigadores de 2021 contra la fuente más
reciente disponible. RUV sí es un registro continuo y por eso la cifra de
víctimas sí corresponde a 2021.

**Caveats importantes:**
- La comparación correcta no es contra "toda la población" sino contra la
  **población elegible** (con educación superior). Las brechas de acceso a
  posgrado ya filtran a las minorías antes de llegar al sistema MinCiencias.
  Por tanto **parte de la subrepresentación es heredada** de barreras educativas
  previas, no atribuible solo al sistema de reconocimiento.
- El **autorreconocimiento étnico** depende de la voluntad del investigador.
  El 96% que respondió "NINGÚN GRUPO ÉTNICO" puede incluir mestizos que sí
  tienen ascendencia afro o indígena pero no se autorreconocen.
- DANE reconoce un **subregistro** de afrocolombianos en 2018 (CNPV reportó 6.7%,
  pero estimaciones corregidas hablan de ~9.3%). Usamos la cifra oficial del censo.
        """)

    df_2021 = df[df["ANO_CONVO_INT"] == 2021]
    if len(df_2021) > 0:
        try:
            comp = comparar_dane(df_2021)

            # Grafico principal: barras agrupadas
            comp_long = comp.melt(
                id_vars="grupo",
                value_vars=["pct_minciencias", "pct_dane_2018"],
                var_name="Fuente", value_name="%",
            )
            comp_long["Fuente"] = comp_long["Fuente"].map({
                "pct_minciencias": "Investigadores MinCiencias 2021",
                "pct_dane_2018": "Población Colombia (DANE 2018 / RUV 2021)",
            })
            fig = px.bar(
                comp_long, x="grupo", y="%", color="Fuente",
                barmode="group", text_auto=".2f",
                title="¿Hay tantos investigadores de minorías como hay población minoritaria?",
                color_discrete_map={
                    "Investigadores MinCiencias 2021": "#1f77b4",
                    "Población Colombia (DANE 2018 / RUV 2021)": "#d62728",
                },
            )
            fig.update_xaxes(tickangle=20, title="")
            fig.update_yaxes(title="% sobre el total")
            fig.update_layout(height=460, legend=dict(orientation="h", y=-0.25))
            st.plotly_chart(fig, use_container_width=True)

            # Grafico secundario: razon de subrepresentacion
            comp_pos = comp.dropna(subset=["razon_subrepresentacion"]).copy()
            comp_pos["color"] = comp_pos["razon_subrepresentacion"].apply(
                lambda r: "Subrepresentado" if r > 1 else "Sobrerrepresentado"
            )
            fig2 = px.bar(
                comp_pos.sort_values("razon_subrepresentacion"),
                x="razon_subrepresentacion", y="grupo",
                orientation="h", color="color",
                text=comp_pos.sort_values("razon_subrepresentacion")["razon_subrepresentacion"]
                    .apply(lambda r: f"{r:.1f}x"),
                color_discrete_map={"Subrepresentado": "#d62728",
                                    "Sobrerrepresentado": "#2ca02c"},
                title="Razón de (sub/sobre)representación: cuántas veces fuera de proporción",
            )
            fig2.add_vline(x=1.0, line_dash="dash", line_color="black",
                           annotation_text="Equidad (1.0x)")
            fig2.update_layout(height=380, legend_title_text="",
                               xaxis_title="Razón = % población / % investigadores")
            st.plotly_chart(fig2, use_container_width=True)

            with st.expander("📊 Ver tabla detallada con todos los números"):
                tabla_pretty = comp.copy()
                tabla_pretty.columns = [
                    "Grupo", "N en investigadores 2021",
                    "% en MinCiencias", "% en población",
                    "Razón subrepr.",
                ]
                st.dataframe(tabla_pretty, use_container_width=True, hide_index=True)
                st.caption(
                    "**Hallazgo clave para el informe:** Las minorías mayoritarias "
                    "(afros, indígenas) están subrepresentadas 3-8x. Las minorías "
                    "muy pequeñas (Raizales, Palenqueros, Rrom) están "
                    "**sobrerrepresentadas** 3-6x — esto sugiere que los programas "
                    "focalizados a estos grupos sí tienen efecto, mientras que las "
                    "barreras estructurales para afros e indígenas no se han movido."
                )
        except Exception as e:
            st.info(f"Comparación DANE no disponible: {e}")
    else:
        st.info("Selecciona la convocatoria 2021 para ver el análisis de diversidad.")


# ---------------------------------------------------------------------------
# Seccion 5: Redes y poder institucional
# ---------------------------------------------------------------------------
def seccion_redes(df: pd.DataFrame) -> None:
    st.header("5️⃣ Redes y poder institucional — ¿quién es puente?")
    narrativa(
        pregunta="¿Cómo se conectan las instituciones a través de investigadores "
                 "con doble afiliación? ¿Hay universidades-puente?",
        takeaway="Universidad de Antioquia y UNAL son los hubs centrales. "
                 "Los Andes y Javeriana tienen alta betweenness — son puentes "
                 "entre comunidades. El grafo tiene 61 componentes desconectados.",
        caveat="**Solo la convocatoria 2021 captura doble afiliación** — las "
               "demás registran una sola institución por investigador. Esto NO "
               "significa que antes no existiera co-filiación, sino que la "
               "captura cambió.",
    )

    st.subheader("Grafo interactivo de co-filiación (2021)")
    html_path = ROOT / "hallazgos" / "sprint3_grafo_filtrado.html"
    if html_path.exists():
        with open(html_path, encoding="utf-8") as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=750, scrolling=False)
        st.caption(
            "Tamaño de nodo = grado ponderado. Color = betweenness (rojo = puente). "
            "Grosor de arista = investigadores compartidos. "
            "Filtrado a instituciones con grado ≥ 2 (141 nodos)."
        )
    else:
        st.info("Genera el HTML del grafo con: `python scripts/sprint3_grafo_interactivo.py`")

    st.subheader("Top instituciones por número de reconocimientos")

    aplicar_norm = st.toggle(
        "Normalizar instituciones (consolidar sedes / razones sociales)",
        value=True,
        help="Colapsa 'UNAL Bogotá', 'UNAL Medellín' y similares en una sola entidad",
    )

    inst_raw = (df["INST_FILIA"].dropna().str.split("|").explode().str.strip())
    if aplicar_norm:
        inst_serie = inst_raw.map(normalizar_institucion)
    else:
        inst_serie = inst_raw.str.upper()

    n_unicas = inst_serie.nunique()
    inst = inst_serie.value_counts().head(20).reset_index()
    inst.columns = ["Institución", "Reconocimientos"]

    fig = px.bar(inst, x="Reconocimientos", y="Institución", orientation="h",
                 color="Reconocimientos", color_continuous_scale="Blues",
                 title=f"Top 20 — {n_unicas:,} instituciones únicas tras normalización" if aplicar_norm
                 else f"Top 20 — {n_unicas:,} instituciones sin normalizar")
    fig.update_layout(yaxis={"autorange": "reversed"}, height=550, margin=dict(l=280))
    st.plotly_chart(fig, use_container_width=True)

    if aplicar_norm:
        crudo = inst_raw.str.upper().nunique()
        reduccion = crudo - n_unicas
        st.caption(
            f"**Normalización aplicada**: {crudo:,} → {n_unicas:,} entidades "
            f"(−{reduccion:,}, {reduccion/crudo*100:.1f}%). Se consolidaron sedes "
            "(p.ej. UNAL Bogotá + UNAL Medellín → UNAL) usando reglas de paréntesis "
            "y sufijos 'SEDE X'/'SECCIONAL'. **Caveat:** la normalización es "
            "conservadora — variantes ortográficas (acentos, abreviaturas, '&' vs 'Y') "
            "no se colapsan automáticamente. Una normalización exhaustiva (con fuzzy "
            "matching o tabla maestra manual) reduciría aún más el conteo."
        )
    else:
        st.caption(
            "Vista cruda: cada variante ortográfica cuenta como entidad distinta. "
            "Activa la normalización para ver el conteo real."
        )


# ---------------------------------------------------------------------------
# Seccion 6: Productividad y desempeno
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Cargando producción de grupos (3.2M filas)…")
def cargar_produccion_normalizada() -> pd.DataFrame:
    return normalizar_produccion(cargar_produccion())


def seccion_productividad(df: pd.DataFrame) -> None:
    st.header("6️⃣ Productividad y desempeño — ¿quién produce el conocimiento?")
    narrativa(
        pregunta="¿La producción científica reflejada en MinCiencias es coherente "
                 "con el reconocimiento? ¿Los Senior producen más que los Junior? "
                 "¿La brecha de género se replica en outputs?",
        takeaway="Sí — Senior producen 4× más que Junior. Pero el sistema "
                 "captura productos firmados por miles de autores que NUNCA fueron "
                 "reconocidos: ~37% de los autores únicos NO están en el padrón.",
        caveat="El cruce usa id_persona (id_persona_pd ↔ id_persona_pr). El "
               "dataset de producción 33dq-ab5a tiene la 'ventana de observación' "
               "como referencia temporal — los productos pueden ser anteriores.",
    )

    try:
        prod = cargar_produccion_normalizada()
    except FileNotFoundError:
        st.warning(
            "El dataset de producción no está disponible. Ejecute: "
            "`python -m src.ingesta.produccion`"
        )
        return

    # Métricas globales
    cov_unicos = cobertura_autores_unicos(prod, df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Productos totales", f"{len(prod):,}")
    c2.metric("Autores únicos", f"{cov_unicos['autores_unicos_total']:,}")
    c3.metric("% autores que son reconocidos",
              f"{cov_unicos['pct_autores_reconocidos']:.1f}%")
    c4.metric("Reconocidos sin producción",
              f"{cov_unicos['reconocidos_sin_produccion']:,}",
              help="Investigadores reconocidos que no aparecen en ninguna "
                   "ventana del dataset de producción.")

    # ----------------------------------------------------------------------
    st.subheader("Cobertura de reconocimiento — ¿quién firma los productos?")
    cov = cobertura_reconocidos(prod, df)
    cov_plot = cov.melt(
        id_vars="ANO_CONVO_INT",
        value_vars=["n_reconocidos", "n_no_reconocidos"],
        var_name="tipo", value_name="n",
    )
    cov_plot["tipo"] = cov_plot["tipo"].map({
        "n_reconocidos": "Investigadores reconocidos (cualquier convocatoria)",
        "n_no_reconocidos": "Autores NO reconocidos",
    })
    fig = px.bar(
        cov_plot, x="ANO_CONVO_INT", y="n", color="tipo",
        labels={"n": "# productos", "ANO_CONVO_INT": "Convocatoria", "tipo": ""},
        title="Composición de la producción por estatus de reconocimiento",
        color_discrete_map={
            "Investigadores reconocidos (cualquier convocatoria)": "#1f77b4",
            "Autores NO reconocidos": "#cccccc",
        },
    )
    fig.update_layout(height=420, legend=dict(orientation="h", y=-0.15))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "El % de productos firmados por reconocidos baja con el tiempo "
        f"({cov.iloc[0]['pct_reconocidos']:.1f}% en {int(cov.iloc[0]['ANO_CONVO_INT'])} → "
        f"{cov.iloc[-1]['pct_reconocidos']:.1f}% en {int(cov.iloc[-1]['ANO_CONVO_INT'])}). "
        "Los grupos cada vez incluyen más coautores externos al sistema MinCiencias."
    )

    # ----------------------------------------------------------------------
    st.subheader("Productividad por categoría de reconocimiento")
    prod_cat = productividad_por_categoria(prod, df)
    prod_cat_plot = prod_cat[
        prod_cat["NME_CLASIFICACION_PR"].isin(CAT_CORTA.keys())
    ].copy()
    prod_cat_plot["Categoría"] = prod_cat_plot["NME_CLASIFICACION_PR"].map(CAT_CORTA)

    fig = px.line(
        prod_cat_plot, x="ANO_CONVO_INT", y="productos_promedio",
        color="Categoría", markers=True,
        labels={"productos_promedio": "Productos promedio por investigador",
                "ANO_CONVO_INT": "Convocatoria"},
        title="¿Producen más los Senior que los Junior?",
        category_orders={"Categoría": ["Junior", "Asociado", "Sénior", "Emérito"]},
    )
    fig.update_layout(height=420)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "La productividad escala con la categoría: Senior produce ~4× más que "
        "Junior. Los Eméritos rompen el patrón: producción más baja porque "
        "muchos están al final de su carrera activa (y desaparecen del padrón "
        "en la siguiente convocatoria)."
    )

    # ----------------------------------------------------------------------
    st.subheader("Brecha de género en productividad por gran área OCDE")
    brecha = brecha_productividad_genero(prod, df).dropna()
    brecha_plot = brecha[~brecha["NME_GRAN_AREA_PR"].isin(["NO REGISTRA", "NO REPORTADO"])]
    brecha_long = brecha_plot.melt(
        id_vars="NME_GRAN_AREA_PR",
        value_vars=["prom_femenino", "prom_masculino"],
        var_name="genero", value_name="prom",
    )
    brecha_long["genero"] = brecha_long["genero"].map({
        "prom_femenino": "Mujeres", "prom_masculino": "Hombres",
    })
    fig = px.bar(
        brecha_long, x="NME_GRAN_AREA_PR", y="prom", color="genero",
        barmode="group",
        labels={"prom": "Productos promedio por investigador",
                "NME_GRAN_AREA_PR": "Gran área OCDE", "genero": ""},
        title="Productos promedio por género — gran área OCDE",
        color_discrete_map={"Mujeres": "purple", "Hombres": "darkorange"},
    )
    fig.update_layout(height=460, xaxis_tickangle=-25,
                       legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(fig, use_container_width=True)
    cols = st.columns(2)
    cols[0].dataframe(
        brecha_plot[["NME_GRAN_AREA_PR", "prom_femenino", "prom_masculino",
                     "brecha_abs", "razon_f_m"]].rename(columns={
            "NME_GRAN_AREA_PR": "Área", "prom_femenino": "Prom. ♀",
            "prom_masculino": "Prom. ♂", "brecha_abs": "Brecha (♀−♂)",
            "razon_f_m": "Razón ♀/♂",
        }),
        use_container_width=True, hide_index=True,
    )
    cols[1].info(
        "**Lectura crítica.** La brecha de género no es solo de "
        "**representación** (cuántas mujeres entran), sino también de "
        "**productividad medida** (cuánto se les contabiliza). La brecha "
        "más grande está en **Ciencias Médicas** e **Ingeniería**. "
        "Humanidades es la única área con razón ≥ 1."
    )

    # ----------------------------------------------------------------------
    st.subheader("Concentración territorial: ¿productos vs investigadores?")
    terr = productividad_territorial(prod, df).head(15)
    terr_plot = terr.melt(
        id_vars="NME_DEPARTAMENTO_RES_PR",
        value_vars=["pct_productos", "pct_investigadores"],
        var_name="tipo", value_name="pct",
    )
    terr_plot["tipo"] = terr_plot["tipo"].map({
        "pct_productos": "% de productos",
        "pct_investigadores": "% de investigadores",
    })
    fig = px.bar(
        terr_plot, x="NME_DEPARTAMENTO_RES_PR", y="pct", color="tipo",
        barmode="group",
        labels={"pct": "% del total nacional",
                "NME_DEPARTAMENTO_RES_PR": "Departamento", "tipo": ""},
        title="Top 15 departamentos: ¿concentran más productos que investigadores?",
    )
    fig.update_layout(height=460, xaxis_tickangle=-30,
                      legend=dict(orientation="h", y=-0.30))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "**Ratio > 1** = el departamento produce más de lo que su tamaño de "
        "padrón sugeriría (ej. Bolívar 1.24, Risaralda 1.24). **Ratio < 1** = "
        "produce menos (Boyacá 0.88, EXTERIOR 0.34). EXTERIOR tiene investigadores "
        "que probablemente publican fuera del circuito MinCiencias."
    )

    # ----------------------------------------------------------------------
    st.subheader("Reconocidos sin producción registrada")
    sin_prod = reconocidos_sin_produccion(prod, df)
    fig = px.bar(
        sin_prod, x="ANO_CONVO_INT", y="pct_sin_produccion",
        text="pct_sin_produccion",
        labels={"ANO_CONVO_INT": "Convocatoria",
                "pct_sin_produccion": "% reconocidos sin producción"},
        title="¿Reconocimiento sin obra registrada? Calidad de captura por convocatoria",
        color="pct_sin_produccion", color_continuous_scale="Reds",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(height=400, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "La cifra cae con el tiempo (15.4% en 2013 → 5.5% en 2021). "
        "**No es necesariamente que ahora produzcan más** — es que la captura "
        "del campo de productos mejoró. En 2013 había 1.232 reconocidos sin "
        "ningún producto vinculado en el dataset; en 2021 son 1.157."
    )

    # ----------------------------------------------------------------------
    with st.expander("📚 Mix de tipologías de producto por convocatoria"):
        mix = mix_tipologias(prod)
        fig = px.bar(
            mix, x="ANO_CONVO_INT", y="pct", color="NME_TIPO_MEDICION_PD",
            labels={"pct": "% productos", "ANO_CONVO_INT": "Convocatoria",
                    "NME_TIPO_MEDICION_PD": "Tipo medición MinCiencias"},
            title="Composición de la producción por tipo de medición",
        )
        fig.update_layout(height=520, legend=dict(font=dict(size=10)))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Las tres categorías dominantes son **Formación de recursos humanos** "
            "(33%), **Apropiación social** (30%) y **Nuevo conocimiento Tipo A** "
            "(10%). El sistema MinCiencias premia tanto la docencia/formación "
            "como la generación de nuevo conocimiento."
        )


# ---------------------------------------------------------------------------
# Seccion 7: Datos crudos
# ---------------------------------------------------------------------------
def seccion_datos(df: pd.DataFrame) -> None:
    st.header("7️⃣ Datos crudos — auditoría directa")
    st.caption(
        f"{len(df):,} registros tras filtros. Use el buscador del DataFrame para "
        "validar casos individuales."
    )
    cols_visibles = [
        "ID_PERSONA_PR", "ANO_CONVO_INT", "NME_CLASIFICACION_PR",
        "NME_GENERO_PR", "EDAD_ANOS_PR", "NME_GRAN_AREA_PR",
        "NME_DEPARTAMENTO_RES_PR", "INST_FILIA",
        "TXT_GRUPO_ETNICO", "TXT_POBLACION_DISCA", "ID_VICTIMA_CONFLICTO",
    ]
    cols_disp = [c for c in cols_visibles if c in df.columns]
    st.dataframe(df[cols_disp].head(1000), use_container_width=True, height=500)
    st.download_button(
        "Descargar muestra (CSV, primeras 5.000 filas)",
        data=df[cols_disp].head(5000).to_csv(index=False).encode("utf-8"),
        file_name="muestra_filtrada.csv",
        mime="text/csv",
    )


# ---------------------------------------------------------------------------
# App principal
# ---------------------------------------------------------------------------
def main() -> None:
    try:
        df_full = cargar_datos()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    df, meta = sidebar_filtros(df_full)

    cabecera(df_full)

    if df.empty:
        st.error("No hay registros para los filtros seleccionados.")
        return

    st.sidebar.markdown("---")
    st.sidebar.metric(
        "Registros tras filtros",
        f"{meta['n_filtrado']:,}",
        delta=f"{meta['n_filtrado'] - meta['n_total']:,}",
    )

    tabs = st.tabs([
        "1️⃣ Calidad",
        "2️⃣ Trayectoria",
        "3️⃣ Territorio",
        "4️⃣ Diversidad",
        "5️⃣ Redes",
        "6️⃣ Productividad",
        "7️⃣ Datos",
    ])
    with tabs[0]:
        seccion_calidad(df)
    with tabs[1]:
        seccion_trayectoria(df)
    with tabs[2]:
        seccion_territorial(df)
    with tabs[3]:
        seccion_diversidad(df)
    with tabs[4]:
        seccion_redes(df)
    with tabs[5]:
        seccion_productividad(df)
    with tabs[6]:
        seccion_datos(df)

    st.markdown("---")
    st.caption(
        "Universidad Santo Tomás · Ustadistica · Consultoría e Investigación 2026-I · "
        "[Repositorio](https://github.com/Victor-Diaz-Usta/Min_ciencias)"
    )


if __name__ == "__main__":
    main()
