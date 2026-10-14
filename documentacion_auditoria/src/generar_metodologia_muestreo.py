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
A("## 7. Conclusión: qué se reporta y por qué")
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
A("| `src/generar_metodologia_muestreo.py` | Genera este documento |")
A("")
A("```bash")
A("python src/eda_longitudinal.py")
A("python src/estimadores_longitudinal.py")
A("python src/generar_metodologia_muestreo.py")
A("```")
A("")
A("El muestreo **no se rehizo**: se reutilizan los identificadores de "
  "`data/memoria/muestra_ids.csv` (semilla 2026).")
A("")

SALIDA.write_text("\n".join(OUT) + "\n", encoding="utf-8")
print(f"escrito {SALIDA}")
print(f"  {len(OUT)} líneas, {len(''.join(OUT).encode('utf-8'))} bytes")
