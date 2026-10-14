# -*- coding: utf-8 -*-
"""
genero_comun.py
===============

Colapso de las categorías de género no representadas en la muestra.

Motivo
------
El registro reconoce cuatro categorías de género. Dos de ellas, *Intersexual*
(5 personas en el censo) y *No disponible* (4), tienen **cero observaciones** en
la muestra MAS de 2 224 personas. Una categoría auxiliar sin observaciones no es
calibrable: el GREG no puede reproducir su total poblacional porque ninguna
observación lo representa, y eso deja una dirección singular en la matriz de
calibración.

Decisión
--------
En **todos los análisis desagregados por género** las dos categorías se colapsan
en una sola, `Otro / No especificado`. La columna original `NME_GENERO_PR` se
conserva intacta para:

  - el visor de trayectorias (`construir_herramienta.py`), que reproduce el
    registro censal tal como está y no calcula estadísticos por género;
  - el control de calidad de género inconsistente
    (`analisis_longitudinal.py::genero_inconsistente`), que cuenta categorías
    distintas por persona y por tanto debe ver el registro crudo.

Advertencia honesta
-------------------
El colapso **no** devuelve la calibrabilidad a esa categoría: la causa es la
ausencia en la muestra, no la granularidad excesiva. Lo que consigue es
(i) eliminar una columna duplicada, (ii) reducir de dos a una las columnas no
calibrables, y (iii) dejar un hueco único y rotulado en lugar de dos. Los
estimadores no cambian, porque en la muestra ambas columnas eran constantes
cero y su coeficiente ya era nulo.

Uso
---
    from genero_comun import COL_GENERO_COL, agregar_genero_colapsado
    df = agregar_genero_colapsado(cargar())
    ...
    auxiliares = ["NME_GRAN_AREA_PR", COL_GENERO_COL, "NME_REGION_RES_PR"]
"""

from __future__ import annotations

import pandas as pd

# --------------------------------------------------------------------------
# Nombres y etiquetas
# --------------------------------------------------------------------------
COL_GENERO = "NME_GENERO_PR"          # columna original del registro (cruda)
COL_GENERO_COL = "NME_GENERO_COL"     # columna derivada, ya colapsada
ETIQUETA_OTRO = "Otro / No especificado"

CATEGORIAS_RARAS = ("Intersexual", "No disponible")
CATEGORIAS_COLAPSADAS = ("Femenino", "Masculino", ETIQUETA_OTRO)

MOTIVO = (
    "Las categorías 'Intersexual' y 'No disponible' tienen cero observaciones en "
    "la muestra MAS (2 224 personas), así que su total poblacional no es calibrable. "
    "Se colapsan en 'Otro / No especificado' en todos los análisis desagregados por "
    "género. El colapso no restaura la calibrabilidad —la causa es la ausencia en la "
    "muestra, no la granularidad— pero reduce de dos a una las columnas no calibrables "
    "y deja un hueco único y rotulado."
)


# --------------------------------------------------------------------------
# Operaciones
# --------------------------------------------------------------------------
def colapsar_genero(serie: pd.Series) -> pd.Series:
    """Devuelve la serie de género con Intersexual y No disponible fusionadas."""
    return serie.where(~serie.isin(CATEGORIAS_RARAS), ETIQUETA_OTRO)


def agregar_genero_colapsado(df: pd.DataFrame, col: str = COL_GENERO) -> pd.DataFrame:
    """Añade `NME_GENERO_COL` al DataFrame (in situ) y lo devuelve."""
    df[COL_GENERO_COL] = colapsar_genero(df[col])
    return df


def resumen_colapso(df: pd.DataFrame, col: str = COL_GENERO,
                    ids_muestra: set | None = None,
                    col_persona: str = "ID_PERSONA_PR") -> dict:
    """
    Frecuencias que documentan la decisión: censo a nivel de persona (última
    convocatoria observada), muestra y detalle de las categorías colapsadas.
    """
    ult = df.sort_values("ID_CONVOCATORIA").groupby(col_persona, observed=True).last()
    vc = ult[col].value_counts()
    if ids_muestra is None:
        mu = ult.iloc[0:0]
    else:
        mu = ult.loc[ult.index.isin(ids_muestra)]
    vcm = mu[col].value_counts()

    detalle = {}
    for c in CATEGORIAS_RARAS:
        if c in vc.index:
            personas = ult.index[ult[col] == c]
            # OJO: la etiqueta solo aparece en la convocatoria 2021 en TODO el
            # registro. Las personas, en cambio, figuran en varias convocatorias
            # con otra etiqueta; por eso se cuenta la etiqueta, no a la persona.
            con_etiqueta = sorted(
                {int(c_) for c_ in
                 df.loc[df[col] == c, "ID_CONVOCATORIA"].astype(int)})
            detalle[c] = {
                "personas_censo": int(vc[c]),
                "pct_censo": float(100 * vc[c] / len(ult)),
                "personas_muestra": int(vcm.get(c, 0)),
                "registros_censo": int((df[col] == c).sum()),
                "convocatorias_con_la_etiqueta": con_etiqueta,
                "convocatorias_de_esas_personas": sorted(
                    {int(c_) for c_ in
                     df.loc[df[col_persona].isin(personas), "ID_CONVOCATORIA"].astype(int)}),
            }
    tot_otro = sum(d["personas_censo"] for d in detalle.values())
    solo_2021 = all(d["convocatorias_con_la_etiqueta"] == [21] for d in detalle.values())
    return {
        "columna_original": col,
        "columna_analisis": COL_GENERO_COL,
        "etiqueta_colapsada": ETIQUETA_OTRO,
        "motivo": MOTIVO,
        "categorias_originales": [str(k) for k in vc.index],
        "distribucion_censo": {str(k): {"n": int(v), "pct": float(100 * v / len(ult))}
                               for k, v in vc.items()},
        "distribucion_muestra": {str(k): int(vcm.get(k, 0)) for k in vc.index},
        "distribucion_censo_colapsada": {
            str(k): {"n": int(v), "pct": float(100 * v / len(ult))}
            for k, v in colapsar_genero(ult[col]).value_counts().items()},
        "categorias_colapsadas": detalle,
        "personas_colapsadas_censo": int(tot_otro),
        "pct_colapsado_censo": float(100 * tot_otro / len(ult)),
        "observaciones_en_muestra": int(vcm.reindex(CATEGORIAS_RARAS).fillna(0).sum()),
        "etiquetas_solo_en_2021": bool(solo_2021),
        "nota_2021": (
            "Las etiquetas 'Intersexual' y 'No disponible' no aparecen en ninguna "
            "convocatoria anterior a 2021 (31 registros en total, todos de 2021). "
            "Por eso ninguna tabla de retención o transición por género cambia: la "
            "convocatoria base de cada par es siempre anterior a 2021."
            if solo_2021 else ""),
        "calibrable": False,
        "nota": ("El colapso no restaura la calibrabilidad: la categoría resultante "
                 "sigue teniendo cero observaciones en la muestra."),
    }


def auxiliares_con_genero_colapsado(auxiliares: list[str],
                                    col: str = COL_GENERO) -> list[str]:
    """Sustituye la columna de género cruda por la colapsada en una lista de auxiliares."""
    return [COL_GENERO_COL if a == col else a for a in auxiliares]
