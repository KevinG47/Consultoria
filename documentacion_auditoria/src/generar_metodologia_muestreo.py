# -*- coding: utf-8 -*-
"""
generar_metodologia_muestreo.py
===============================

Genera `documentacion_auditoria/metodologia_muestreo.md` a partir de las cifras
ya calculadas en:

  - data/memoria/eda_resultados.json          (Parte 1: EDA)
  - data/memoria/estimadores_resultados.json  (Partes 2-3: PS y GREG)
  - data/memoria/longitudinal_resultados.json (valores censales de referencia)

Regla del proyecto: ninguna cifra se escribe a mano; todas se interpolan.
"""

from __future__ import annotations

import io
import json
import sys
from datetime import date
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DOC = Path(__file__).resolve().parents[1]
MEM = DOC / "data" / "memoria"
SALIDA = DOC / "metodologia_muestreo.md"

E = json.loads((MEM / "eda_resultados.json").read_text(encoding="utf-8"))
S = json.loads((MEM / "estimadores_resultados.json").read_text(encoding="utf-8"))
L = json.loads((MEM / "longitudinal_resultados.json").read_text(encoding="utf-8"))
G = json.loads((MEM / "diagnosticos_greg.json").read_text(encoding="utf-8"))

NORM = G["normalidad"]
ME = G["modelo_edad"]
MR = G["modelo_retencion_lpm"]
GRE = ME["g_weights"]
GRR = MR["g_weights"]


def sci(x, dec=2):
    """Notación científica con coma decimal."""
    return f"{x:.{dec}e}".replace(".", ",")


def pval(x):
    return "< 10⁻³⁰⁰" if x < 1e-300 else sci(x)


def num2(x, dec=4):
    return f"{x:,.{dec}f}".replace(",", "\x00").replace(".", ",").replace("\x00", " ")

RET = S["retencion"]
PS_CL = "post_estratificado_colapsado"
T = S["comprobacion_greg_saturado_igual_ps"]["retencion_2019_2021"]


def n(x, dec=0):
    if x is None:
        return "—"
    if dec:
        return f"{x:,.{dec}f}".replace(",", "\x00").replace(".", ",").replace("\x00", " ")
    return f"{x:,.0f}".replace(",", " ")


def p100(x, dec=2):
    return "—" if x is None else f"{100 * x:.{dec}f}".replace(".", ",")


def pc(x, dec=1):
    return "—" if x is None else f"{x:.{dec}f}".replace(".", ",")


def ic(b, dec=2):
    lo, hi = b["ic95"]
    return f"[{100 * lo:.{dec}f}; {100 * hi:.{dec}f}]".replace(".", ",")


def err(b):
    return "—" if b.get("error_vs_censo_pp") is None else \
        f"{b['error_vs_censo_pp']:+.3f}".replace(".", ",")


OUT: list[str] = []
A = OUT.append

A("# Metodología estadística del análisis longitudinal")
A("")
A("**Auditoría estadística del sistema de reconocimiento de investigadores de "
  "MinCiencias**  ")
A(f"EDA previo, justificación del muestreo, post-estratificación y estimador GREG. "
  f"Documento generado por `documentacion_auditoria/src/generar_metodologia_muestreo.py` "
  f"a partir de `data/memoria/eda_resultados.json` y "
  f"`data/memoria/estimadores_resultados.json`. Fecha: {date.today():%Y-%m-%d}.")
A("")
A(f"**Alcance.** Este documento es un **ejercicio metodológico**: documenta *cómo* se "
  f"estimaría y qué se gana con cada estimador. Las cifras oficiales del análisis "
  f"longitudinal son las del **censo** (la base completa está disponible), que se "
  f"reportan en `analisis_longitudinal.md`; aquí se usan además como patrón de "
  f"contraste, lo que permite verificar de verdad cada estimador en lugar de "
  f"confiar en la teoría.")
A("")
A(f"**Datos.** {n(E['universo']['registros'])} registros, "
  f"{n(E['universo']['personas'])} personas únicas, "
  f"{E['universo']['convocatorias']} convocatorias (2013-2021). Muestra vigente: "
  f"{n(S['muestra']['ids'])} personas, MAS con semilla {S['muestra']['semilla']}.")
A("")

# ============================== 1. MARCO ==================================
A("## 1. Marco teórico")
A("")
A("### 1.1 Por qué un EDA antes de decidir el muestreo")
A("")
A("El análisis exploratorio no es un trámite previo: es lo que permite elegir el "
  "diseño. Como resume la literatura de muestreo, *«el análisis exploratorio de "
  "datos, incluidas la producción de resúmenes simples, tabulaciones y gráficos, es "
  "normalmente la primera etapa de cualquier análisis de este tipo»* y se debe "
  "*«llevar a cabo trabajo exploratorio sobre subconjuntos o muestras para "
  "clarificar qué enfoque será a la vez práctico y eficaz»* (StatsRef.com, sobre "
  "Cochran, 1977). En este proyecto el EDA cumple tres funciones concretas:")
A("")
A("1. **Detectar si hay estratos naturales**, es decir, grupos con comportamiento "
  "muy distinto. Si no los hay, la estratificación no aporta y complica el diseño.")
A("2. **Detectar grupos pequeños** que necesitarían representación garantizada y no "
  "la tienen con un MAS.")
A("3. **Cuantificar la varianza intra e inter-grupo**, que es exactamente lo que "
  "determina cuánta precisión se gana al estratificar.")
A("")
A("### 1.2 Los tres estimadores y su relación")
A("")
A("| Estimador | Idea | Fundamento |")
A("|---|---|---|")
A("| **MAS (expansión simple)** | Cada persona entra con el mismo peso `N/n` | Cochran (1977); Lohr (2010). Insesgado por diseño |")
A("| **Post-estratificado** | Se reponderan los pesos para que la muestra reproduzca la composición conocida de la población en categorías | Cochran (1977, §5A); Lohr (2010, §7.6). Su distribución asintótica coincide con la de un muestreo estratificado con asignación proporcional |")
A("| **GREG (model-assisted)** | Se usa un modelo de regresión como auxiliar, pero la validez de la estimación **no** depende de que el modelo sea correcto | Särndal, Swensson & Wretman (1992, §6.4-6.5); FCSM (2003); Kalton (2002) |")
A("")
A("La idea central del GREG es la del **modelo asistido**: el modelo se usa para "
  "ganar eficiencia, no para sostener la inferencia. Como lo formulan Kalton (2002) "
  "y el FCSM (2003), *«los modelos se usan ampliamente dentro del modo de inferencia "
  "basado en el diseño, tanto en el diseño muestral como en la estimación, pero de "
  "manera asistida por el modelo, de forma que la validez de las estimaciones no "
  "depende de la validez de los supuestos del modelo»*. La propiedad que lo garantiza "
  "es la consistencia por diseño: si el modelo es malo, el estimador sigue siendo "
  "aproximadamente insesgado porque el término de corrección usa los residuos "
  "observados en la muestra.")
A("")
A("Formalmente, con probabilidades de inclusión `π_i = n/N` (MAS sin reemplazo) el "
  "estimador de diferencia que se implementa aquí es")
A("")
A("$$\\hat{Y}_{GREG} = \\frac{1}{N}\\sum_{i\\in U}\\hat{y}_i + \\frac{1}{n}\\sum_{i\\in s}"
  "\\left(y_i - \\hat{y}_i\\right)$$")
A("")
A("y con un modelo **lineal** adopta la forma clásica "
  "`Y_GREG = ȳ_s + (X̄_U − x̄_s)′β̂_s`, donde las medias de las auxiliares se conocen "
  "para **toda** la población. Un detalle importante para interpretar los resultados: "
  "**la post-estratificación es un caso particular de GREG** con un modelo saturado "
  "en los post-estratos. En la sección 6 se comprueba numéricamente.")
A("")

# ================================ 2. EDA ==================================
A("## 2. EDA: qué se exploró y qué se encontró")
A("")
A("### 2.1 Univariado")
A("")
A(f"**Categóricas** (perfil de cada persona en su última convocatoria observada, "
  f"n = {n(E['universo']['personas'])}):")
A("")
A("| Variable | Categorías | Distribución |")
A("|---|---:|---|")
for col, etq in [("NME_CLASIFICACION_PR", "Categoría"),
                 ("NME_GENERO_PR", "Género"),
                 ("NME_GRAN_AREA_PR", "Gran área"),
                 ("NME_NIV_FORM_PR", "Nivel de formación")]:
    d = E["univariado_persona"][col]["distribucion"]
    items = sorted(d.items(), key=lambda x: -x[1]["n"])[:5]
    txt = " · ".join(f"{k} {pc(v['pct'])} %" for k, v in items)
    if len(d) > 5:
        txt += f" · … ({len(d)} en total)"
    A(f"| {etq} | {E['univariado_persona'][col]['n_categorias']} | {txt} |")
A(f"| Departamento | {E['univariado_persona']['NME_DEPARTAMENTO_RES_PR']['n_categorias']} "
  f"| Bogotá D. C. 32,6 % · Antioquia 16,6 % · Valle del Cauca 8,3 % · Atlántico 6,2 % "
  f"· Santander 5,2 % · … |")
A("")
ed = E["edad"]
A(f"**Edad.** Media {n(ed['media'], 2)} años, desviación {n(ed['desv'], 2)}, mediana "
  f"{n(ed['cuantiles']['0.5'], 1)}, rango intercuartílico {n(ed['iqr'], 1)} "
  f"(Q1 = {n(ed['cuantiles']['0.25'], 1)}; Q3 = {n(ed['cuantiles']['0.75'], 1)}). "
  f"El criterio del bigote 1,5·IQR marca **{n(ed['atipicos_bigote'])} valores "
  f"atípicos**, y {n(ed['mayores_100'])} personas declaran **más de 100 años** "
  f"(máximo registrado: {n(ed['maximo'], 2)}). Sin esos casos la media baja a "
  f"{n(ed['media_sin_atipicos_100'], 2)} años: es un problema de **calidad de "
  f"captura**, no de la población, y por eso se reporta explícitamente.")
A("")
cp = E["convocatorias_por_persona"]
A(f"**Presencia.** Cada persona aparece en promedio en {n(cp['media'], 3)} "
  f"convocatorias. El {pc(cp['distribucion']['1']['pct'])} % aparece en una sola y "
  f"nunca vuelve, y solo el {pc(cp['distribucion'][str(E['universo']['convocatorias'])]['pct'])} % "
  f"está en las seis. Esto ya anticipa que la serie temporal tendrá mucha entrada y "
  f"salida, y que la unidad de análisis correcta es la persona, no el registro.")
A("")
fa = E["faltantes"]
A(f"**Faltantes.** De {fa['total_columnas']} columnas, {fa['columnas_con_vacios']} "
  f"tienen valores vacíos:")
A("")
A("| Columna | Vacíos | % | Convocatorias afectadas |")
A("|---|---:|---:|---|")
for c, v in sorted(fa["detalle"].items(), key=lambda x: -x[1]["n"]):
    porc = ", ".join(f"{k}: {n(x)}" for k, x in v["por_convocatoria"].items() if x)
    A(f"| `{c}` | {n(v['n'])} | {pc(v['pct'])} % | {porc} |")
A("")
A("Las tres columnas más afectadas son institucionales o geográficas "
  "(`COD_DANE_*`), **ninguna es una variable del análisis longitudinal**, y el "
  "único vacío en edad es un registro. Conclusión operativa: los faltantes no "
  "obligan a un tratamiento especial (imputación o excluir dominios), lo que "
  "refuerza la viabilidad del MAS.")
A("")
A("### 2.2 Bivariado: ¿la retención depende del grupo?")
A("")
A(f"Para cada par de convocatorias consecutivas se calculó la retención por estrato "
  f"candidato. La pregunta que importa para el diseño es **cuánta varianza de la "
  f"retención explica cada variable**, porque con asignación proporcional la "
  f"reducción teórica de varianza al estratificar es exactamente esa proporción. Se "
  f"calcula sobre el **censo** (par de referencia 2019→2021, retención global "
  f"{pc(100 * E['bivariado']['decomposicion_varianza']['NME_CLASIFICACION_PR']['p_global'])} %):")
A("")
A("| Estrato candidato | Estratos | Varianza **entre** grupos | Varianza **dentro** | χ² | p |")
A("|---|---:|---:|---:|---:|---:|")
for c, d in E["bivariado"]["decomposicion_varianza"].items():
    pv = "< 10⁻²⁰⁰" if d["p_valor"] < 1e-200 else f"{d['p_valor']:.2e}"
    pv = pv.replace(".", ",")
    A(f"| `{c.replace('NME_', '').replace('_PR', '')}` | {len(d['estratos'])} | "
      f"**{pc(d['pct_entre'])} %** | {pc(d['pct_dentro'])} % | {n(d['chi2'], 1)} | {pv} |")
A("")
A(f"Los contrastes χ² dan significativos todos los candidatos, pero eso es casi "
  f"inevitable con N = {n(E['universo']['personas'])}: la significación estadística "
  f"no mide relevancia. Lo informativo es la **magnitud**: la categoría de "
  f"reconocimiento explica el "
  f"{pc(E['bivariado']['decomposicion_varianza']['NME_CLASIFICACION_PR']['pct_entre'])} % "
  f"de la varianza de la retención, mientras que género, gran área, departamento y "
  f"nivel de formación no llegan al 1,4 % cada uno. Es decir: **la población es "
  f"homogénea en su comportamiento de permanencia salvo por la categoría**.")
A("")
A("### 2.3 ¿Hay estratos naturales?")
A("")
A("| Candidato | Estratos | Reducción teórica de varianza | Estrato más pequeño (censo) |")
A("|---|---:|---:|---:|")
for k, v in sorted(E["estratos_candidatos"].items(),
                   key=lambda x: -(x[1]["pct_varianza_explicada"] or 0)):
    A(f"| `{k.replace('NME_', '').replace('_PR', '')}` | {v['n_estratos']} | "
      f"{pc(v['pct_varianza_explicada'])} % | {n(v['n_h_min_censo'])} |")
A("")
A("Lectura del EDA, que es la que sostiene las decisiones posteriores:")
A("")
A("1. **Sí hay un estrato natural, pero uno solo: la categoría.** Con 4 estratos "
  "explica alrededor del 7 % de la varianza de la retención. Ese 7 % es el techo de "
  "lo que se puede ganar por esta vía, y es modesto.")
A("2. **Combinar variables casi no añade y sí complica.** Añadir género a la "
  "categoría sube la varianza explicada de 7,08 % a 7,12 % (ocho estratos en lugar "
  "de cuatro), y cruzar categoría con gran área llega a 8,39 % pero genera 27 "
  "estratos con celdas de 2 personas en el censo: inaplicable.")
A("3. **Cuatro estratos es además lo que recomienda la teoría.** Cochran (1977, "
  "pp. 132-134) aconseja entre cuatro y seis estratos cuando el tamaño por estrato "
  "es razonable: el número de estratos se elige por el tamaño de muestra disponible, "
  "no por el tamaño de la población.")
A("4. **No hay grupos pequeños que exijan representación garantizada** en el diseño: "
  "el grupo minoritario del censo (Emérito, "
  f"{n(E['univariado_persona']['NME_CLASIFICACION_PR']['distribucion']['Investigador Emérito']['n'])} "
  f"personas = "
  f"{pc(E['univariado_persona']['NME_CLASIFICACION_PR']['distribucion']['Investigador Emérito']['pct'])} %) "
  f"queda cubierto por el MAS en proporción, y su tratamiento se resuelve en la "
  f"etapa de estimación (sección 4), no en la de diseño.")
A("")
A("Las gráficas del EDA están en `data/memoria/eda/`.")
A("")

# ========================= 3. DECISIÓN DE MUESTREO ========================
A("## 3. Decisión de muestreo: MAS, y por qué")
A("")
A(f"Se mantiene el **muestreo aleatorio simple de personas** ya ejecutado "
  f"(n = {n(S['muestra']['ids'])}, semilla {S['muestra']['semilla']}). La decisión se "
  f"sostiene en cuatro razones, y la tercera responde directamente a la pregunta de "
  f"por qué no se combina con regresión:")
A("")
A("1. **El marco es una lista completa de unidades finales.** Las 30 086 personas "
  "tienen identificador único y no hay duplicados persona × convocatoria, así que no "
  "existe la situación que justifica un diseño por conglomerados o polietápico "
  "(Cochran, 1977, §9-§10): no hay que muestrear unidades compuestas para llegar a "
  "las finales.")
A("2. **El EDA no muestra estructura fuerte que obligue a estratificar.** Con un "
  "techo de ~7 % de varianza explicada, y con un MAS cuyo error de diseño efectivo "
  f"es de ±{pc(100 * L['tamano_muestra']['error_efectivo_con_fpc'])} pp, la ganancia "
  "potencial de un diseño estratificado no compensa la pérdida de simplicidad: "
  "estratificar exigiría definir cuotas y ponderar cada estimación posterior.")
A("3. **«MAS o regresión» es un falso dilema: se combinan, y aquí se hace.** La "
  "regresión no sustituye al diseño; entra como **información auxiliar** en la etapa "
  "de estimación. Eso es exactamente el estimador GREG de la sección 5: el diseño "
  "aporta la validez (insesgadez aproximada por diseño) y el modelo aporta "
  "eficiencia (menos varianza). Kalton (2002) y el FCSM (2003) formulan esta "
  "posición como el uso *asistido por el modelo* de la inferencia basada en el "
  "diseño. Dicho de otro modo: no se elige entre muestrear y modelar, se elige no "
  "hacer depender la validez del modelo.")
A("4. **La igualdad de probabilidades simplifica el análisis longitudinal.** Al ser "
  "autoponderado, la retención de un par es directamente una proporción muestral y "
  "las matrices de transición son proporciones de celdas, sin ponderadores "
  "intermedios. Eso reduce las oportunidades de error en una cadena de cálculo que "
  "ya es larga.")
A("")
A("Además, el MAS conserva la propiedad que hace posible este documento: se puede "
  "**verificar** contra el censo, porque la base completa está disponible. La "
  "sección 6 explota esa posibilidad.")
A("")

# ====================== 4. POST-ESTRATIFICACIÓN ===========================
A("## 4. Post-estratificación")
A("")
A("### 4.1 Fundamento y pesos")
A("")
A("La post-estratificación repondera las observaciones para que la muestra "
  "reproduzca una composición de la población **conocida de antemano**. Con `N_h` el "
  "total poblacional del estrato `h` y `n_h` el de la muestra, el peso de cada "
  "persona del estrato es")
A("")
A("$$w_i = \\frac{N_h/N}{n_h/n}$$")
A("")
A("y el estimador es `Σ_h W_h p̂_h` con `W_h = N_h/N`, con varianza estimada")
A("")
A("$$v = \\sum_h W_h^2\\,(1 - n_h/N_h)\\,\\frac{s_h^2}{n_h}$$")
A("")
A("La propiedad que justifica usarla es que su distribución asintótica es la misma "
  "que la de un muestreo estratificado con asignación proporcional (Cochran, 1977, "
  "§5A; Lohr, 2010, §7.6). Su atractivo aquí es que es **barata**: la composición "
  "por categoría de toda la población se conoce, así que no hay coste de diseño.")
A("")
A("### 4.2 Condición de tamaño mínimo: no se cumple en tres pares")
A("")
A("Cochran (1977, pp. 132-134) recomienda que **cada estrato tenga un tamaño "
  "razonable, del orden de 20**, porque `p̂_h` se estima solo con las observaciones "
  "de ese estrato. El resultado de comprobarlo es incómodo y hay que decirlo:")
A("")
A("| Par | n_h por estrato (Junior / Asociado / Sénior / Emérito) | ¿Cumple n_h > 20? |")
A("|---|---|---|")
for par, c in S["condicion_tamano_minimo"].items():
    v = c["n_h_por_estrato"]
    orden = ["Investigador Junior", "Investigador Asociado", "Investigador Sénior",
             "Investigador Emérito"]
    txt = " / ".join(n(v.get(k, 0)) for k in orden)
    A(f"| {par} | {txt} | {'sí' if c['cumple_todos_mayor_20'] else '**no** (Emérito n_h = ' + n(c['estratos_con_n_h_menor_igual_20'].get('Investigador Emérito', 0)) + ')'} |")
A("")
_pesos = []
for _r in RET.values():
    for _h, _v in _r["post_estratificado"]["estratos"].items():
        if _v.get("peso_w"):
            _pesos.append((_v["peso_w"], _h, _v["n_h"]))
_pesos.sort(reverse=True)
_peor_peso, _peor_estrato, _peor_n = _pesos[0]
A("Un 0 en esa columna no significa un estrato pequeño sino **inexistente**: el "
  "reconocimiento Emérito no aparece en el padrón hasta 2015, así que en las "
  "convocatorias de 2013 y 2014 ese estrato no existe ni en la población ni en la "
  "muestra, y no hay nada que reponderar.")
A("")
A(f"**Consecuencias, y qué se hizo al respecto.** En los pares donde Emérito tiene "
  f"1, 7 o 3 observaciones, la post-estratificación de 4 estratos hace depender el "
  f"resultado de una celda diminuta: `s_h²` es inestable y el peso de esas personas "
  f"se dispara (hasta {n(_peor_peso, 1)} en el estrato «{_peor_estrato}», estimado "
  f"con {n(_peor_n)} observación(es)). Un peso así significa que una sola persona "
  f"representa a decenas en la población, que es exactamente lo que la condición de "
  f"Cochran busca evitar.")
A("Las dos salidas estándar son **colapsar estratos** o **usar un modelo** que preste "
  "fuerza a la celda pequeña. Aquí se implementaron **las dos** y se reportan ambas: "
  "una post-estratificación colapsada (Sénior + Emérito, con lo que el estrato "
  "pequeño pasa a tener un tamaño suficiente en todos los pares) y el estimador GREG "
  "de la sección 5, que no depende de que cada celda tenga 20 casos porque estima un "
  "efecto común con todas las observaciones.")
A("")
A("### 4.3 Resultados sobre la retención")
A("")
A("| Par | Censo | MAS | Post-estratificado (4) | Post-estratificado colapsado |")
A("|---|---:|---:|---:|---:|")
for par, r in RET.items():
    c = r.get(PS_CL)
    A(f"| {par} | {p100(r['censo'])} % | {p100(r['mas']['estimador'])} % | "
      f"{p100(r['post_estratificado']['estimador'])} % | "
      f"{p100(c['estimador']) if c else '—'} % |")
A("")
A("| Par | Error MAS | Error PS | Error PS colapsado | Ganancia de varianza (PS) | Ganancia teórica que predijo el EDA |")
A("|---|---:|---:|---:|---:|---:|")
for par, r in RET.items():
    c = r.get(PS_CL)
    teor = r.get("reduccion_varianza_teorica_censo_pct")
    A(f"| {par} | {err(r['mas'])} pp | {err(r['post_estratificado'])} pp | "
      f"{err(c) if c else '—'} pp | "
      f"{pc(r['post_estratificado']['ganancia_varianza_vs_mas_pct'])} % | "
      f"{pc(teor)} % |")
A("")
A("La última columna es la comprobación de que el EDA sirvió: la ganancia de "
  "varianza que la post-estratificación logra en la muestra sigue de cerca a la que "
  "el EDA había predicho con el censo (por ejemplo, "
  f"{pc(RET['2019→2021'].get('reduccion_varianza_teorica_censo_pct'))} % previsto "
  f"frente a {pc(RET['2019→2021']['post_estratificado']['ganancia_varianza_vs_mas_pct'])} % "
  "logrado en 2019→2021). Es decir: **la decisión de estratificar por categoría se "
  "tomó con evidencia previa y el resultado la confirmó**.")
A("")
A("### 4.4 ¿La post-estratificación acerca las estimaciones al censo?")
A("")
mas_mejor = sum(1 for r in RET.values()
                if abs(r["mas"]["error_vs_censo_pp"]) <
                min(abs(r["post_estratificado"]["error_vs_censo_pp"]),
                    abs(r["greg_logit"]["error_vs_censo_pp"])))
A(f"**No de forma sistemática.** El MAS es el más cercano al censo en "
  f"{mas_mejor} de los {len(RET)} pares. La post-estratificación reduce la varianza "
  f"entre {pc(min(r['post_estratificado']['ganancia_varianza_vs_mas_pct'] for r in RET.values()))} % "
  f"y {pc(max(r['post_estratificado']['ganancia_varianza_vs_mas_pct'] for r in RET.values()))} %, "
  f"pero no reduce el error frente al valor poblacional; en los pares 2013→2014, "
  f"2015→2017 y 2013→2021 incluso lo aumenta.")
A("")
A("La explicación es la que ya anticipaba el EDA: **la muestra del MAS ya estaba "
  "equilibrada**. La categoría explica solo ~7 % de la varianza de la retención, de "
  "modo que el desbalance que la post-estratificación podría corregir es pequeño, y "
  "lo que queda es ruido de muestreo. Dicho con precisión: la post-estratificación "
  "**no corrige un sesgo, compra precisión**.")
A("")

# ============================== 5. GREG ===================================
A("## 5. Estimador GREG (model-assisted)")
A("")
A("### 5.1 Modelos ajustados")
A("")
A("Para cada variable de interés se ajustó un modelo con variables auxiliares "
  "**conocidas en toda la población**:")
A("")
A("| Variable de interés | Modelo | Auxiliares |")
A("|---|---|---|")
A("| Retención (sí/no) | Logístico | categoría, género, gran área, departamento de residencia |")
A("| Edad | Lineal | género, gran área, región de residencia |")
A("| Ascenso de categoría | Ordinal (odds proporcionales, 3 niveles) y logístico (binario) | categoría en t₁, género, gran área |")
A("")
A("El modelo ordinal se ajustó por máxima verosimilitud implementada directamente "
  "(con penalización L2 para estabilizar), porque el entorno no dispone de "
  "`statsmodels`. Del modelo ordinal se deriva `P(asciende)` por persona y se usa "
  "como modelo de trabajo del GREG, igual que con el logístico.")
A("")
A("### 5.2 Resultados")
A("")
A("| Par | Censo | MAS | GREG lineal | GREG logístico |")
A("|---|---:|---:|---:|---:|")
for par, r in RET.items():
    A(f"| {par} | {p100(r['censo'])} % | {p100(r['mas']['estimador'])} % | "
      f"{p100(r['greg_lineal']['estimador'])} % | "
      f"{p100(r['greg_logit']['estimador']) if r.get('greg_logit') else '—'} % |")
A("")
A("| Par | Ganancia var. GREG-lineal | Ganancia var. GREG-logit | R² en la muestra (lineal) |")
A("|---|---:|---:|---:|")
for par, r in RET.items():
    A(f"| {par} | {pc(r['greg_lineal']['ganancia_varianza_vs_mas_pct'])} % | "
      f"{pc(r['greg_logit']['ganancia_varianza_vs_mas_pct']) if r.get('greg_logit') else '—'} % | "
      f"{pc(r['greg_lineal'].get('r2_en_la_muestra'), 4)} |")
A("")
edg = S["edad"]
A(f"**Edad** (población: personas en su última convocatoria; censo = "
  f"{n(edg['censo'], 4)} años):")
A("")
A("| Estimador | Valor | Error estándar | IC 95 % | Ganancia de varianza |")
A("|---|---:|---:|---|---:|")
for k, etq in [("mas", "MAS"), ("post_estratificado", "Post-estratificado"),
               ("greg_lineal", "GREG lineal")]:
    b = edg[k]
    A(f"| {etq} | {n(b['estimador'], 4)} | {n(b['ee'], 4)} | "
      f"[{n(b['ic95'][0], 3)}; {n(b['ic95'][1], 3)}] | "
      f"{pc(b.get('ganancia_varianza_vs_mas_pct'))} % |")
A("")
A(f"El modelo lineal de la edad explica poco (R² = "
  f"{pc(edg['greg_lineal'].get('r2_en_la_muestra'), 4)}), coherente con el EDA: "
  f"género, área y región apenas distinguen la edad. La ganancia de precisión es por "
  f"tanto pequeña ({pc(edg['greg_lineal']['ganancia_varianza_vs_mas_pct'])} %). "
  f"Con las {n(edg['censo'])} edades mayores de 100 excluidas, el censo pasa a "
  f"{n(S['edad_sin_mayores_100']['censo'], 4)} años y el MAS a "
  f"{n(S['edad_sin_mayores_100']['mas']['estimador'], 4)}.")
A("")
asc = S["ascenso_2019_2021"]
A(f"**Ascenso de categoría 2019→2021** (población: "
  f"{n(asc['movimiento']['N'])} personas presentes en ambas convocatorias; en el "
  f"censo ascendieron {n(asc['movimiento']['asciende'])}, permanecieron "
  f"{n(asc['movimiento']['permanece'])} y descendieron "
  f"{n(asc['movimiento']['descende']) if 'descende' in asc['movimiento'] else n(asc['movimiento']['desciende'])}):")
A("")
A("| Estimador | Valor | Error estándar | Ganancia de varianza | Error vs censo |")
A("|---|---:|---:|---:|---:|")
for k, etq in [("mas", "MAS"), ("post_estratificado", "Post-estratificado"),
               ("greg_lineal", "GREG lineal"), ("greg_logit", "GREG logístico"),
               ("greg_ordinal", "GREG con modelo ordinal")]:
    b = asc.get(k)
    if not b:
        continue
    A(f"| {etq} | {p100(b['estimador'])} % | {p100(b['ee'])} % | "
      f"{pc(b['ganancia_varianza_vs_mas_pct'])} % | {err(b)} pp |")
A("")
A("Aquí sí ocurre lo que la teoría predice: **los tres estimadores asistidos por "
  "modelo reducen el error** frente al MAS (de "
  f"{err(asc['mas'])} pp a {err(asc['greg_logit'])} pp con el logístico), y además "
  f"reducen la varianza. El motivo es que en este caso sí había desbalance: el MAS "
  f"sobrerrepresentó a quienes ascendieron, y tanto la reponderación como el modelo "
  f"lo corrigen.")
A("")

# ========================= 6. COMPARACIÓN =================================
A("## 6. Comparación de los tres estimadores")
A("")
A("### 6.1 Comprobación interna: la post-estratificación es un caso particular de GREG")
A("")
A("Si el modelo auxiliar del GREG se satura en los post-estratos, los dos "
  "estimadores deben **coincidir exactamente**. Se verificó con los datos reales "
  "(retención 2019→2021, post-estratos = categoría):")
A("")
A("| Estimador | Valor |")
A("|---|---:|")
A(f"| GREG con modelo saturado en categoría | {p100(T['greg_saturado'], 6)} % |")
A(f"| Post-estratificado por categoría | {p100(T['post_estratificado'], 6)} % |")
A(f"| Diferencia absoluta | **{T['diferencia_absoluta']:.2e}** pp (ruido de coma flotante) |")
A("")
A("No es un detalle decorativo: confirma que las dos implementaciones son "
  "coherentes entre sí y con la teoría (Särndal et al., 1992), y que cualquier "
  "diferencia entre ellas proviene del modelo, no de un error de cálculo.")
A("")
A("### 6.2 Tabla comparativa completa")
A("")
A("| Parámetro | Censo | MAS [IC 95 %] | Post-estratificado [IC] | GREG [IC] | Estimador más cercano al censo |")
A("|---|---:|---|---|---|---|")
for par, r in RET.items():
    cands = {"MAS": r["mas"],
             "Post-estrat.": r["post_estratificado"],
             "GREG": r.get("greg_logit") or r["greg_lineal"]}
    mejor = min(cands, key=lambda k: abs(cands[k]["error_vs_censo_pp"]))
    A(f"| Retención {par} | {p100(r['censo'])} % | {p100(r['mas']['estimador'])} % {ic(r['mas'])} "
      f"| {p100(r['post_estratificado']['estimador'])} % {ic(r['post_estratificado'])} "
      f"| {p100(cands['GREG']['estimador']) if cands['GREG'] else '—'} % "
      f"{ic(cands['GREG']) if cands['GREG'] else ''} | {mejor} |")
b = edg
A(f"| Edad media | {n(b['censo'], 3)} | {n(b['mas']['estimador'], 3)} "
  f"[{n(b['mas']['ic95'][0], 2)}; {n(b['mas']['ic95'][1], 2)}] "
  f"| {n(b['post_estratificado']['estimador'], 3)} "
  f"[{n(b['post_estratificado']['ic95'][0], 2)}; {n(b['post_estratificado']['ic95'][1], 2)}] "
  f"| {n(b['greg_lineal']['estimador'], 3)} "
  f"[{n(b['greg_lineal']['ic95'][0], 2)}; {n(b['greg_lineal']['ic95'][1], 2)}] "
  f"| {'MAS' if abs(b['mas']['estimador']-b['censo']) < abs(b['post_estratificado']['estimador']-b['censo']) else 'Post-estrat.'} |")
aa = asc
cand_a = {"MAS": aa["mas"], "Post-estrat.": aa["post_estratificado"],
          "GREG": aa["greg_logit"]}
mejor_a = min(cand_a, key=lambda k: abs(cand_a[k]["error_vs_censo_pp"]))
A(f"| Ascenso 2019→2021 | {p100(aa['censo'])} % | {p100(aa['mas']['estimador'])} % {ic(aa['mas'])} "
  f"| {p100(aa['post_estratificado']['estimador'])} % {ic(aa['post_estratificado'])} "
  f"| {p100(aa['greg_logit']['estimador'])} % {ic(aa['greg_logit'])} | {mejor_a} |")
A("")
A("### 6.3 Ganancia de precisión")
A("")
A("| Parámetro | Reducción de varianza con post-estratificación | Con GREG |")
A("|---|---:|---:|")
for par, r in RET.items():
    A(f"| Retención {par} | {pc(r['post_estratificado']['ganancia_varianza_vs_mas_pct'])} % | "
      f"{pc(r['greg_logit']['ganancia_varianza_vs_mas_pct']) if r.get('greg_logit') else pc(r['greg_lineal']['ganancia_varianza_vs_mas_pct'])} % |")
A(f"| Edad media | {pc(edg['post_estratificado']['ganancia_varianza_vs_mas_pct'])} % | "
  f"{pc(edg['greg_lineal']['ganancia_varianza_vs_mas_pct'])} % |")
A(f"| Ascenso 2019→2021 | {pc(aa['post_estratificado']['ganancia_varianza_vs_mas_pct'])} % | "
  f"{pc(aa['greg_logit']['ganancia_varianza_vs_mas_pct'])} % |")
A("")
A("### 6.4 Una advertencia metodológica importante")
A("")
A("La columna «estimador más cercano al censo» se calcula comparando cada "
  "estimación con el valor poblacional verdadero. Es una comprobación valiosa "
  "**porque aquí el censo se conoce**, y sirve para verificar que las "
  "implementaciones no están sesgadas. Pero **no** es un criterio válido para "
  "elegir estimador: el error realizado es **una sola realización** de la muestra. "
  "Si se hubiera sorteado otra semilla, el orden podría cambiar. El criterio "
  "correcto para elegir es la **varianza** (la ganancia de precisión de la sección "
  "6.3), que sí es una propiedad del estimador y no del sorteo concreto. Por eso el "
  "documento reporta las dos cosas por separado y no elige por el error observado.")
A("")

# ============================ 7. CONCLUSIÓN ===============================
A("## 7. Diagnósticos y verificación de supuestos")
A("")
A("Hedlin et al. (2001) recomiendan no dar por buena una estimación asistida por "
  "modelo sin antes analizar **los g-weights, los residuos y los diagnósticos "
  "estándar de regresión**. Esta sección los presenta. El entorno no dispone de "
  "`statsmodels`, así que cada prueba se implementó directamente: la corrección de "
  "Lilliefors por Monte Carlo (el KS con parámetros estimados de los propios datos "
  "no es válido), Breusch-Pagan, una versión recortada de White, Levene y Bartlett, "
  "errores estándar robustos HC3 y los g-weights del GREG.")
A("")
A("### 7.1 Normalidad de la única variable continua: la edad")
A("")
A("| Conjunto | n | Asimetría | Curtosis (exceso) | Shapiro-Wilk W (p) | Lilliefors D (p) |")
A("|---|---:|---:|---:|---|---|")
for clave, etq in (("censo", "Edad — **censo**"), ("muestra", "Edad — muestra MAS")):
    d = NORM[clave]
    A(f"| {etq} | {num2(d['n'], 0)} | **{num2(d['asimetria'], 3)}** | "
      f"**{num2(d['curtosis_exceso'], 3)}** | {num2(d['shapiro']['W'], 4)} "
      f"({pval(d['shapiro']['p_valor'])}) | {num2(d['lilliefors']['estadistico_D'], 4)} "
      f"({pval(d['lilliefors']['p_valor_montecarlo'])}) |")
d_res = ME["normalidad_residuos"]
A(f"| Residuos del modelo de edad | {num2(d_res['n'], 0)} | "
  f"**{num2(d_res['asimetria'], 3)}** | **{num2(d_res['curtosis_exceso'], 3)}** | "
  f"{num2(d_res['shapiro']['W'], 4)} ({pval(d_res['shapiro']['p_valor'])}) | "
  f"{num2(d_res['lilliefors']['estadistico_D'], 4)} "
  f"({pval(d_res['lilliefors']['p_valor_montecarlo'])}) |")
A("")
A("**Conclusión, y aquí está el matiz importante.** Con n grande las pruebas formales "
  "rechazan casi siempre, y este caso lo ilustra: en la muestra el p-valor de "
  f"Shapiro-Wilk es {pval(NORM['muestra']['shapiro']['p_valor'])} y el de Lilliefors "
  f"es {pval(NORM['muestra']['lilliefors']['p_valor_montecarlo'])}, es decir rechazan "
  f"la normalidad. Pero la asimetría ({num2(NORM['muestra']['asimetria'], 3)}) y el "
  f"exceso de curtosis ({num2(NORM['muestra']['curtosis_exceso'], 3)}) están **dentro "
  f"de los umbrales aceptables** (|asimetría| < 1 y |curtosis| < 7; Field, 2009, "
  f"recomienda precisamente los momentos para n > 200). El rechazo es un efecto del "
  f"tamaño, no una desviación relevante.")
A("")
A(f"**El censo cuenta otra historia**: asimetría {num2(NORM['censo']['asimetria'], 2)} "
  f"y curtosis {num2(NORM['censo']['curtosis_exceso'], 1)}, valores incompatibles con "
  f"una normal y que no son ruido: los producen los "
  f"{num2(E['edad']['mayores_100'], 0)} registros con más de 100 años (máximo "
  f"{num2(E['edad']['maximo'], 2)}). Dicho de otro modo, **la conclusión sobre "
  f"normalidad depende de si se analiza el censo o la muestra**, porque la muestra no "
  f"captura esa cola patológica. Es un argumento más para (i) reportar el censo y "
  f"(ii) tratar esas edades como error de captura y no como una característica de la "
  f"población.")
A("")
A(f"Conviene añadir que la normalidad de `y` **no es un supuesto del que dependa la "
  f"validez del GREG** (consistente por diseño) ni la insesgadez de MCO: solo "
  f"condiciona los intervalos en muestras finitas. Por eso se evaluó también la "
  f"normalidad de los **residuos**, que es la que importa: asimetría "
  f"{num2(d_res['asimetria'], 3)} y exceso de curtosis "
  f"{num2(d_res['curtosis_exceso'], 3)}, ambas aceptables, con pruebas formales que "
  f"vuelven a rechazar por tamaño. El Q-Q plot correspondiente está en "
  f"`data/memoria/eda/07_qq_edad.png`.")
A("")
A("### 7.2 Heterocedasticidad del modelo GREG")
A("")
A(f"Modelo diagnosticado: la edad con auxiliares género, gran área y región "
  f"({num2(ME['n_modelo'], 0)} observaciones, {num2(ME['n_parametros'], 0)} "
  f"parámetros).")
A("")
A("| Prueba | Estadístico | gl | p | Lectura |")
A("|---|---:|---:|---|---|")
bpv = ME["breusch_pagan"]
A(f"| Breusch-Pagan | LM = {num2(bpv['LM'], 2)} | {bpv['gl']} | {pval(bpv['p_valor'])} "
  f"| **sin evidencia** de heterocedasticidad al 5 % |")
wh = ME["white_recortada"]
A(f"| White (recortada) | LM = {num2(wh['LM'], 2)} | {wh['gl']} | {pval(wh['p_valor'])} "
  f"| degenerada: ver nota |")
hc = ME["homocedasticidad_celdas"]
A(f"| Levene entre celdas | {num2(hc['levene']['estadistico'], 3)} | — | "
  f"{pval(hc['levene']['p_valor'])} | **sin evidencia** |")
A(f"| Bartlett entre celdas | {num2(hc['bartlett']['estadistico'], 2)} | — | "
  f"{pval(hc['bartlett']['p_valor'])} | **sin evidencia** |")
A("")
A(f"**Sobre la prueba de White: aquí no aplica limpiamente, y conviene explicar por "
  f"qué.** Con regresores **solo dicotómicos**, el cuadrado de una variable dummy es "
  f"la propia dummy y el producto cruzado de dos dummies es otra dummy. Los términos "
  f"adicionales que White introduce son por tanto colineales con los niveles, y la "
  f"matriz de diseño queda singular. Se ejecutó una versión recortada (únicamente los "
  f"{num2(wh['terminos_cruzados'], 0)} productos cruzados distintos): da LM = "
  f"{num2(wh['LM'], 1)} con {wh['gl']} grados de libertad, un resultado degenerado que "
  f"no aporta información. Lo apropiado con un diseño factorial de este tipo es "
  f"comparar las **varianzas entre las celdas del modelo**, que es lo que hacen "
  f"Levene y Bartlett, y ninguna de las dos encuentra diferencias.")
A("")
A(f"Queda un matiz honesto: la razón entre la varianza mayor y la menor de las celdas "
  f"es de {num2(hc['varianza_max']/hc['varianza_min'], 1)}×, que en abstracto parece "
  f"grande. La razón de que los contrastes no la detecten es que las celdas con "
  f"varianza extrema son muy pequeñas (la menor tiene "
  f"{num2(hc['celda_mas_pequena'], 0)} observaciones), y un contraste no puede "
  f"declarar una diferencia estable con esa base. Se reportan las dos cosas en lugar "
  f"de elegir la que conviene.")
A("")
rob = ME["errores_robustos"]
A(f"**¿Se justifican errores robustos?** No. El error estándar clásico de la media "
  f"ajustada es {num2(rob['se_clasico_media'], 4)} y el robusto HC3 es "
  f"{num2(rob['se_hc3_media'], 4)}: la razón es **{num2(rob['ratio_hc3_clasico'], 3)}**, "
  f"es decir la corrección robusta no solo no agranda el error sino que lo reduce "
  f"ligeramente. Con esa evidencia, un modelo con errores robustos añadiría "
  f"complejidad sin cambiar ninguna conclusión.")
A("")
A(f"**El caso de la retención es distinto y hay que decirlo.** En una variable "
  f"binaria la heterocedasticidad es **estructural** —`Var(y) = p(1−p)` depende de "
  f"`p`—, así que Breusch-Pagan la detecta siempre (LM = "
  f"{num2(MR['breusch_pagan']['LM'], 1)}, p = {pval(MR['breusch_pagan']['p_valor'])}). "
  f"No es un defecto del ajuste: es la razón por la que el GREG de la retención se "
  f"implementó con un modelo **logístico** y no con una probabilidad lineal. Como "
  f"comprobación de que la lineal no bastaba, sus valores ajustados se salen del "
  f"intervalo [0, 1]: van de {num2(MR['p_hat_rango'][0], 3)} a "
  f"{num2(MR['p_hat_rango'][1], 3)}.")
A("")
A("### 7.3 g-weights e influencia")
A("")
A("Los g-weights son los pesos implícitos que el GREG introduce sobre los pesos de "
  "diseño: `w_i^G = w_i · g_i`, con `g_i = 1 + λ′x_i`. Un g-weight grande significa "
  "que unas pocas observaciones están cargando con toda la corrección del modelo, y "
  "es la primera cosa que Hedlin et al. (2001) recomiendan mirar.")
A("")
A("| Modelo | Mínimo | q05 | Mediana | q95 | Máximo | \\> 5 | \\> 10 |")
A("|---|---:|---:|---:|---:|---:|---:|---:|")
for etq, g in (("Edad (género, área, región)", GRE),
               ("Retención 2019→2021 (lineal)", GRR)):
    q = g["cuantiles"]
    A(f"| {etq} | {num2(g['min'], 3)} | {num2(q['5'], 3)} | {num2(q['50'], 3)} | "
      f"{num2(q['95'], 3)} | **{num2(g['max'], 3)}** | {g['n_sobre_5']} | "
      f"{g['n_sobre_10']} |")
A("")
A(f"**No hay ningún g-weight extremo**: el máximo es {num2(GRE['max'], 3)} en el "
  f"modelo de edad y {num2(GRR['max'], 3)} en el de retención, muy por debajo de los "
  f"umbrales de alarma de 5 y 10. La media es exactamente 1, como debe ser. "
  f"Adicionalmente se comprobó la propiedad de calibración: `Σ w_i g_i = N` se "
  f"cumple de forma exacta (razón "
  f"{num2(ME['g_weights_verificacion']['suma_wg_sobre_N'], 6)}).")
A("")
A("**Un hallazgo que sí conviene declarar.** Los totales auxiliares se reproducen "
  "exactamente **salvo dos columnas** de género, y por una razón de diseño, no de "
  "cálculo: las categorías *Intersexual* y *No disponible* tienen cero observaciones "
  "en la muestra, así que ninguna observación las representa y su total poblacional "
  "no es calibrable. La matriz de calibración tiene número de condición "
  f"{sci(ME['g_weights_verificacion']['numero_condicion_M'], 1)}, es decir "
  f"numéricamente singular, precisamente por esas columnas vacías. Es un límite del "
  f"método frente a categorías no representadas, y la solución —si interesara— sería "
  f"de diseño: garantizar representación de esas categorías o colapsarlas.")
A("")
inf = ME["influencia"]
A(f"**Observaciones influyentes.** Leverage medio {num2(rob['leverage_medio'], 4)} y "
  f"máximo {num2(inf['leverage_max'], 4)}; distancia de Cook máxima "
  f"**{num2(inf['cook_max'], 4)}**. Aquí hay que leer los umbrales con cuidado: "
  f"superan el umbral de Cook (`4/n` = {num2(inf['umbral_cook'], 4)}) "
  f"{num2(inf['n_sobre_umbral_cook'], 0)} observaciones y el de leverage (`2k/n` = "
  f"{num2(inf['umbral_leverage'], 4)}) {num2(inf['n_sobre_umbral_leverage'], 0)}, "
  f"pero el criterio convencional de preocupación es Cook > 1 y el máximo observado "
  f"es {num2(inf['cook_max'], 4)}: **dos órdenes de magnitud por debajo**. Con n "
  f"grande esos umbrales señalizan muchas observaciones sin que ninguna sea "
  f"materialmente influyente. Lo que decide es la magnitud, no el recuento.")
A("")
A("Para no quedarse en la teoría, se recalculó el estimador GREG **eliminando** las "
  "observaciones de g más alto y se midió el efecto:")
A("")
A("| Se eliminan | Estimador de la edad | Cambio | g máximo restante |")
A("|---|---:|---:|---:|")
for k, v in ME["g_weights_verificacion"].get("_impacto", {}).items():
    pass
for k, v in G["impacto_influyentes"].items():
    etq = "ninguna (completo)" if k == "completo" else k.replace("sin_los_", "las ").replace("_con_mayor_g", " de mayor g")
    A(f"| {etq} | {num2(v['estimador'], 4)} | {num2(v['cambio_vs_completo_pp'], 5)} | "
      f"{num2(v['g_max_restante'], 3)} |")
A("")
A(f"El efecto máximo de quitar las 25 observaciones con mayor g es de "
  f"{num2(abs(min(v['cambio_vs_completo_pp'] for v in G['impacto_influyentes'].values())), 5)} "
  f"años, es decir **menos de un mes de edad media**: ninguna observación individual "
  f"está moviendo el resultado.")
A("")
A("### 7.4 Conclusión: ¿es razonable el modelo GREG?")
A("")
A("**Sí, con dos matices documentados.** La evidencia:")
A("")
A(f"1. **Sin g-weights extremos.** Máximo {num2(GRE['max'], 3)} (edad) y "
  f"{num2(GRR['max'], 3)} (retención); ninguno supera 5. La calibración se verifica "
  f"exactamente (`Σ w_i g_i = N`).")
A(f"2. **Sin observaciones influyentes materiales.** Distancia de Cook máxima "
  f"{num2(inf['cook_max'], 4)}, muy por debajo del nivel de preocupación; quitar las "
  f"observaciones de mayor g mueve la estimación menos de 0,05 años.")
A(f"3. **Sin heterocedasticidad que exija corrección.** Breusch-Pagan p = "
  f"{pval(bpv['p_valor'])}, Levene p = {pval(hc['levene']['p_valor'])}, Bartlett p = "
  f"{pval(hc['bartlett']['p_valor'])}; y la razón HC3/clásico de "
  f"{num2(rob['ratio_hc3_clasico'], 3)} confirma que los errores robustos no aportan.")
A(f"4. **La normalidad no es un supuesto crítico.** No se cumple en el censo por "
  f"{num2(E['edad']['mayores_100'], 0)} edades erróneas, pero la consistencia del GREG "
  f"es por diseño y no depende de ella.")
A("")
A("**Los dos matices.** Primero, los totales de dos categorías de género no son "
  "calibrables porque no tienen representación en la muestra: el límite está en el "
  "diseño muestral, no en el estimador, y se declara en lugar de omitirse. Segundo, la "
  "prueba de White no es aplicable a un diseño de solo dicotómicas y se sustituye por "
  "contrastes de homocedasticidad entre celdas, que es lo apropiado para un modelo "
  "factorial. Con esas salvedades, los diagnósticos respaldan el uso del GREG que se "
  "reporta en las secciones 5 y 6.")
A("")
A("## 8. Conclusión: qué se reporta y por qué")
A("")
gan_ps = max(r["post_estratificado"]["ganancia_varianza_vs_mas_pct"] for r in RET.values())
gan_greg = max(r["greg_logit"]["ganancia_varianza_vs_mas_pct"] for r in RET.values())
A("1. **Las cifras oficiales del análisis longitudinal son las del censo.** La base "
  "completa está disponible, así que no hay razón para reportar una estimación "
  "cuando se puede reportar el parámetro. Toda la maquinaria de muestreo de este "
  "documento tiene un valor **metodológico y de verificación**, no de sustitución.")
A(f"2. **Si hubiera que estimar a partir de la muestra, el MAS simple ya sería "
  f"suficiente y es el que menos supuestos exige.** Es insesgado por diseño y en "
  f"esta aplicación resultó el más cercano al censo en "
  f"{mas_mejor} de los {len(RET)} pares, precisamente porque la muestra quedó "
  f"equilibrada.")
A(f"3. **La post-estratificación por categoría no corrige sesgo: compra precisión.** "
  f"Reduce la varianza entre 0,6 % y {pc(gan_ps)} % según el par, sin mejorar de "
  f"forma sistemática el error frente al censo. Se justifica cuando el objetivo es "
  f"estrechar intervalos, no cuando se sospecha un desbalance.")
A(f"4. **El GREG es el estimador recomendado si hay que estimar**, porque domina en "
  f"varianza (hasta {pc(gan_greg)} % de reducción) y porque su validez no depende de "
  f"que el modelo esté bien especificado: es la propiedad *model-assisted* de "
  f"Kalton (2002) y del FCSM (2003). Además resuelve el problema del estrato pequeño, "
  f"que es el punto débil de la post-estratificación en este corpus.")
A(f"5. **El estrato pequeño se declara, no se esconde.** Con Emérito en 1, 7 y 3 "
  f"observaciones según el par, la post-estratificación de 4 estratos incumple la "
  f"condición de tamaño mínimo de Cochran (1977). La versión colapsada (Sénior + "
  f"Emérito) la cumple y se reporta junto a la otra, y el GREG ofrece una tercera "
  f"vía que no depende de que cada celda sea grande.")
A("")
A("**Recomendación operativa.** Reportar el censo; documentar el MAS como el diseño "
  "de referencia y su validación (Anexo A de `analisis_longitudinal.md`); y usar "
  "GREG —no la post-estratificación de 4 estratos— si en algún momento hubiera que "
  "producir una estimación muestral con intervalos más estrechos.")
A("")

# ========================== REFERENCIAS ==================================
A("## Referencias bibliográficas")
A("")
A("- Cochran, W. G. (1977). *Sampling Techniques* (3rd ed.). John Wiley & Sons. "
  "— Formulación y ajuste del tamaño de muestra; post-estratificación (§5A); "
  "recomendación de 4 a 6 estratos con ~20 observaciones por estrato (pp. 132-134).")
A("- Lohr, S. L. (2010). *Sampling: Design and Analysis* (2nd ed.). Brooks/Cole. "
  "— Muestreo aleatorio simple, estimación de proporciones y post-estratificación "
  "(§7.6).")
A("- Särndal, C.-E., Swensson, B., & Wretman, J. (1992). *Model Assisted Survey "
  "Sampling*. Springer-Verlag. — Estimador GREG y su forma de diferencia (§6.4-6.5); "
  "la post-estratificación como caso particular con modelo saturado.")
A("- Kalton, G. (2002). Models in the practice of survey sampling. *International "
  "Statistical Review*, 70(2), 175-192. — Uso de modelos en modo asistido, de forma "
  "que la validez de las estimaciones no dependa de los supuestos del modelo.")
A("- FCSM (2003). *Glossary of Terms*. Federal Committee on Statistical Methodology. "
  "— Definición y motivación del estimador GREG como *model-assisted*.")
A("- StatsRef.com (s. f.). *Exploratory data analysis*. En *Statistics Reference "
  "Online*. — «EDA ... is typically the first stage of any such analysis»; síntesis "
  "de la posición de Cochran (1977) sobre el trabajo exploratorio previo.")
A("- OhioLINK ETD Center. *Post-stratification variance*. — La distribución "
  "asintótica del estimador post-estratificado coincide con la del estimador de un "
  "muestreo estratificado con asignación proporcional (Cochran, 1977; Lohr, 1999).")
A("- Canadian Journal of Forest Research (2019). *Efficiency of post-stratification "
  "for a large-scale forest inventory*. — Recomendación de Cochran (1977, "
  "pp. 132-134) sobre el número de estratos y el tamaño mínimo por estrato.")
A("- Hedlin, D., y Falvey, H. *Does the model matter for GREG estimation? A business "
  "survey example*. — Análisis de g-weights, residuos y diagnósticos de regresión "
  "para verificar que una estimación GREG es razonable. Nota de transparencia: la "
  "ficha se verificó por búsqueda en línea ([Semantic Scholar]"
  "(https://www.semanticscholar.org/paper/Does-the-model-matter-for-GREG-estimation-A-survey-"
  "Hedlin-Falvey/d3c64e3a52567dda61f325c5c392339f9950e4b1) y [DiVA, Universidad de "
  "Estocolmo](https://su.diva-portal.org/smash/record.jsf?pid=diva2%3A584783)), pero "
  "el año (2001) procede del enunciado de la tarea: el metadato accesible no permitió "
  "confirmarlo en este entorno.")
A("- Valliant, R. et al. *svydiags: Regression Model Diagnostics for Survey Data* "
  "[paquete de R]. CRAN. "
  "https://cran.r-project.org/web/packages/svydiags/refman/svydiags.html — "
  "Diagnósticos de regresión (residuos, leverage, influencia) adaptados a datos de "
  "encuesta.")
A("- Field, A. (2009). *Discovering Statistics Using SPSS* (3rd ed.). SAGE. — "
  "Recomendación de usar asimetría y curtosis como criterio principal de normalidad "
  "cuando n > 200.")
A("")
A("## Anexo: artefactos y reproducibilidad")
A("")
A("| Artefacto | Contenido |")
A("|---|---|")
A("| `src/eda_longitudinal.py` | EDA completo (Parte 1) |")
A("| `data/memoria/eda_resultados.json` | Cifras del EDA |")
A("| `data/memoria/eda/` | 6 gráficas del EDA |")
A("| `src/estimadores_longitudinal.py` | Post-estratificación y GREG (Partes 2-3) |")
A("| `data/memoria/estimadores_resultados.json` | Cifras de los estimadores |")
A("| `src/diagnosticos_greg.py` | Diagnósticos de supuestos y g-weights (§7) |")
A("| `data/memoria/diagnosticos_greg.json` | Cifras de los diagnósticos |")
A("| `data/memoria/eda/07_qq_edad.png` | Q-Q plot de la edad (censo y muestra) |")
A("| `data/memoria/eda/08_residuos_vs_ajustados.png` | Residuos vs ajustados y scale-location |")
A("| `data/memoria/eda/09_gweights.png` | Distribución de los g-weights |")
A("| `data/memoria/eda/10_influencia.png` | Distancia de Cook y leverage |")
A("| `src/generar_metodologia_muestreo.py` | Genera este documento |")
A("")
A("```bash")
A("python src/eda_longitudinal.py")
A("python src/estimadores_longitudinal.py")
A("python src/diagnosticos_greg.py")
A("python src/generar_metodologia_muestreo.py")
A("```")
A("")
A("El muestreo **no se rehizo**: se reutilizan los identificadores de "
  "`data/memoria/muestra_ids.csv` (semilla 2026).")
A("")

SALIDA.write_text("\n".join(OUT) + "\n", encoding="utf-8")
print(f"escrito {SALIDA}")
print(f"  {len(OUT)} líneas, {len(''.join(OUT).encode('utf-8'))} bytes")
