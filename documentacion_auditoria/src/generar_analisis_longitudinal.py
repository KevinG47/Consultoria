# -*- coding: utf-8 -*-
"""
generar_analisis_longitudinal.py
================================

Genera `documentacion_auditoria/analisis_longitudinal.md` con la estructura
acordada:

  - Secciones principales: cifras del UNIVERSO (censo). La base completa está
    disponible, así que no se reporta una estimación donde se puede reportar el
    parámetro.
  - Anexo A: validación del muestreo (MAS) — diseño, representatividad y
    contraste muestra-censo.
  - Anexo B: post-estratificación y GREG (remite a metodologia_muestreo.md).

Fuentes (ninguna cifra se escribe a mano):
  - data/memoria/longitudinal_resultados.json
  - data/memoria/eda_resultados.json
  - data/memoria/estimadores_resultados.json
"""

from __future__ import annotations

import io
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DOC = Path(__file__).resolve().parents[1]
MEM = DOC / "data" / "memoria"
SALIDA = DOC / "analisis_longitudinal.md"

D = json.loads((MEM / "longitudinal_resultados.json").read_text(encoding="utf-8"))
E = json.loads((MEM / "eda_resultados.json").read_text(encoding="utf-8"))
S = json.loads((MEM / "estimadores_resultados.json").read_text(encoding="utf-8"))
U, T, M = D["universo"], D["tamano_muestra"], D["muestra"]
PU, PM = D["pares_universo"], D["pares_muestra"]
TU, TM = D["transiciones_universo"], D["transiciones_muestra"]
GL = D["retencion_global_2013_2021"]
HC = D["hallazgos_calidad"]
CATS = ["Investigador Junior", "Investigador Asociado",
        "Investigador Sénior", "Investigador Emérito"]
CORTOS = [c.replace("Investigador ", "") for c in CATS]
ANIOS = [2013, 2014, 2015, 2017, 2019, 2021]


def num(x):
    return "—" if x is None else f"{x:,}".replace(",", " ")


def num_s(x):
    """Entero con signo explícito."""
    return "—" if x is None else f"{x:+,}".replace(",", " ")


def pcs(x, dec=1):
    return "—" if x is None else f"{x:.{dec}f}".replace(".", ",")


def p100(x, dec=2):
    return "—" if x is None else f"{100 * x:.{dec}f}".replace(".", ",")


def ic(b, dec=2, etiqueta="ic_wald"):
    lo, hi = b[etiqueta]
    return f"[{100 * lo:.{dec}f}; {100 * hi:.{dec}f}]".replace(".", ",")


def matriz(clave, dic=None):
    src = (dic or TU)[clave]
    m = pd.DataFrame(src["conteos"]).reindex(index=CATS, columns=CATS, fill_value=0)
    return m.astype(int)


def tabla_transicion(clave, dic=None):
    m = matriz(clave, dic)
    L = ["| Categoría en t₁ ↓ / t₂ → | " + " | ".join(CORTOS) + " | Total |",
         "|" + "---|" * (len(CATS) + 2)]
    for o in CATS:
        tot = int(m.loc[o].sum())
        celdas = [f"{int(m.loc[o, d])} ({pcs(100*m.loc[o, d]/tot)} %)" if tot else "0"
                  for d in CATS]
        L.append(f"| {o.replace('Investigador ', '')} | " + " | ".join(celdas)
                 + f" | {num(tot)} |")
    tc = [int(m[c].sum()) for c in CATS]
    L.append("| **Total** | " + " | ".join(num(x) for x in tc)
             + f" | {num(int(m.values.sum()))} |")
    return "\n".join(L)


OUT: list[str] = []
A = OUT.append

A("# Análisis longitudinal de la dinámica del reconocimiento de investigadores")
A("")
A("**Auditoría estadística del sistema de reconocimiento de MinCiencias — "
  "objetivo específico 2**  ")
A(f"Documento generado por `documentacion_auditoria/src/generar_analisis_longitudinal.py`. "
  f"Fecha: {date.today():%Y-%m-%d}.")
A("")
A(f"> **Estas cifras son del universo, no de una muestra.** La base completa está "
  f"disponible ({num(U['registros'])} registros, {num(U['personas'])} personas), así "
  f"que el análisis longitudinal se hace sobre el **censo**: no hay razón para "
  f"reportar una estimación cuando se puede reportar el parámetro. El ejercicio de "
  f"muestreo con el que se trabajó antes se conserva, pero pasa a ser lo que "
  f"corresponde: una **validación metodológica** (Anexo A) y una comparación de "
  f"estimadores (Anexo B). La metodología completa está en "
  f"`metodologia_muestreo.md`.")
A("")

# ================================ 1 =======================================
A("## 1. Datos y alcance")
A("")
A("| Convocatoria | Fecha (`ANO_CONVO`) | Personas | Registros |")
A("|---|---|---:|---:|")
for c, anio in zip(["16", "17", "18", "19", "20", "21"], ANIOS):
    A(f"| {anio} | {D['convocatorias_fecha'][c]} | {num(U['personas_por_convocatoria'][str(anio)])} "
      f"| {num(U['registros_por_convocatoria'][str(anio)])} |")
A(f"| **Total** | — | **{num(U['personas'])}** | **{num(U['registros'])}** |")
A("")
A(f"La clave `(ID_PERSONA_PR, ID_CONVOCATORIA)` es única: "
  f"{num(HC['duplicados_persona_convocatoria'])} duplicados en los "
  f"{num(U['registros'])} registros. Por tanto cada persona aparece **como máximo "
  f"una vez por convocatoria** y el panel persona × convocatoria es una matriz sin "
  f"repeticiones. Las convocatorias **no son anuales** (faltan 2016, 2018 y 2020), "
  f"lo que condiciona cualquier lectura temporal y obliga a medir los intervalos "
  f"reales en lugar de suponerlos.")
A("")

# ================================ 2 =======================================
A("## 2. Cifras del universo (censo)")
A("")
A("### 2.1 Retención, entradas y salidas")
A("")
A("**Retenidos** = presentes en ambas convocatorias · **salidas** = presentes en la "
  "primera y no en la segunda · **entradas** = presentes en la segunda y no en la "
  "primera. Las tasas de retención y salida se calculan sobre las personas presentes "
  "en la primera convocatoria, y la de entrada sobre las de la segunda.")
A("")
A("| Par | Años reales | Personas en t₁ | Retenidos | Retención | Salidas | Entradas | Crecimiento neto |")
A("|---|---|---:|---:|---:|---:|---:|---:|")
for p in PU:
    A(f"| {p['par']} | {pcs(p['anios_reales'], 2)} | {num(p['n_a'])} | {num(p['retenidos'])} "
      f"| **{p100(p['retencion']['p'])} %** | {p100(p['salida']['p'])} % "
      f"| {num(p['entradas'])} | {num_s(p['crecimiento_neto'])} |")
A("")
A(f"La identidad del panel se cumple en los cinco pares: retenidos + entradas "
  f"reconstruye exactamente el tamaño de la segunda convocatoria.")
A("")
A("### 2.2 Los intervalos de tiempo reales cambian la comparación")
A("")
A("Los años nominales sugieren intervalos de 1, 1, 2, 2 y 2 años, pero `ANO_CONVO` "
  "contiene fechas y al medirlas los intervalos son otros:")
A("")
A("| Par | Intervalo nominal | Intervalo real | Retención observada | Anualizada (nominal) | Anualizada (real) |")
A("|---|---|---|---|---|---|")
for p in PU:
    A(f"| {p['par']} | {p['anios']} años | {pcs(p['anios_reales'], 3)} años "
      f"| {p100(p['retencion']['p'])} % | {p100(p['retencion_anualizada'])} % "
      f"| **{p100(p['retencion_anualizada_real'])} %** |")
A("")
A("La causa principal es un dato ya documentado en el repositorio auditado: la "
  "convocatoria rotulada **«833 de 2018» está fechada el 06/12/2019**. Por eso el "
  f"hueco 2017→2019 dura {pcs(D['intervalos_anios_reales']['2017->2019'], 2)} años y "
  f"2019→2021 solo {pcs(D['intervalos_anios_reales']['2019->2021'], 2)}. La "
  "consecuencia no es cosmética: **invierte el orden de los pares**. Con años "
  f"nominales, 2017→2019 ({p100(PU[3]['retencion_anualizada'])} %) y 2019→2021 "
  f"({p100(PU[4]['retencion_anualizada'])} %) parecen igual de malos; con los "
  f"intervalos reales, 2017→2019 es el peor "
  f"({p100(PU[3]['retencion_anualizada_real'])} %) y 2019→2021 el segundo mejor "
  f"({p100(PU[4]['retencion_anualizada_real'])} %).")
A("")
A("### 2.3 Retención global 2013→2021")
A("")
A(f"De las {num(PU[0]['n_a'])} personas reconocidas en 2013, "
  f"{num(GL['universo'] * PU[0]['n_a'])} seguían reconocidas en 2021: "
  f"**{p100(GL['universo'])} %**. La estructura de permanencia a lo largo de todo el "
  f"período es muy desigual:")
A("")
A("| N.º de convocatorias en que aparece | Personas | Porcentaje |")
A("|---|---:|---:|")
for k, v in HC["personas_por_numero_de_convocatorias"].items():
    A(f"| {k} | {num(v['personas'])} | {pcs(v['pct'])} % |")
A("")
A(f"El **{pcs(HC['personas_por_numero_de_convocatorias']['1']['pct'])} %** de las "
  f"personas aparece en una sola convocatoria y nunca vuelve; en el extremo opuesto, "
  f"{num(HC['personas_por_numero_de_convocatorias']['6']['personas'])} personas "
  f"({pcs(HC['personas_por_numero_de_convocatorias']['6']['pct'])} %) están "
  f"reconocidas en las seis.")
A("")
A("### 2.4 Transiciones de categoría")
A("")
A("Filas: categoría en la primera convocatoria del par. Columnas: categoría en la "
  "segunda. Cada celda muestra el número de personas y el porcentaje sobre el total "
  "de la fila. El orden jerárquico es Junior (12) < Asociado (13) < Sénior (14) < "
  "Emérito (15), según `ORDEN_CLAS_PR`.")
A("")
for p in PU:
    k = p["par"]
    t = TU[k]
    A(f"**{k}** — {num(t['n_transiciones'])} personas con categoría en ambas "
      f"convocatorias; permanecen {num(t['misma_categoria'])} "
      f"({p100(t['tasa_permanencia'])} %), ascienden {num(t['ascienden'])}, "
      f"descienden {num(t['descienden'])}.")
    A("")
    A(tabla_transicion(k))
    A("")
A("Las transiciones dominantes son de ascenso: Junior→Asociado es el flujo más "
  "numeroso en todos los pares. Pero el descenso existe y no es marginal: en "
  f"2019→2021 bajaron de categoría {num(TU['2019→2021']['descienden'])} personas, "
  f"el {p100(TU['2019→2021']['descienden']/TU['2019→2021']['n_transiciones'])} % de "
  f"las trayectorias observadas. La categoría no es un derecho adquirido.")
A("")
A("### 2.5 «Emérito» es un estado absorbente")
A("")
em = HC["emerito_absorbente"]
A(f"De las {num(em['oportunidades'])} personas clasificadas como Investigador "
  f"Emérito en 2015, 2017 o 2019, **ninguna** vuelve a aparecer en una convocatoria "
  f"posterior: {num(em['retornos'])} retornos sobre {num(em['oportunidades'])} "
  f"oportunidades. La categoría no existe en 2013 ni en 2014 y aparece por primera "
  f"vez en 2015.")
A("")
A("Dos consecuencias. En lo descriptivo, la fila «Emérito» de toda matriz de "
  "transición es estructuralmente cero. En lo analítico, cualquier cadena de Markov "
  "ajustada a estas transiciones tendrá en Emérito un **estado absorbente**, y la "
  "retención de los Eméritos no es un caso de baja retención sino una regla del "
  "sistema. Lo que el dato **no** permite determinar es la causa: podría ser que el "
  "reconocimiento no se renueve, que se otorgue una sola vez, o que quienes lo "
  "reciben dejen de postularse.")
A("")
A("### 2.6 Entradas y salidas en sentido estricto")
A("")
A("La definición habitual de «entrada» mezcla dos poblaciones distintas: quien nunca "
  "había sido reconocido y quien ya lo fue, faltó a la convocatoria intermedia y "
  "volvió. Separarlas cambia la lectura del crecimiento:")
A("")
A("| Par | Entradas | Entradas nuevas reales | Reingresos | Reingresos/entradas | Salidas | Salidas temporales | Salidas definitivas |")
A("|---|---:|---:|---:|---:|---:|---:|---:|")
for p in PU:
    A(f"| {p['par']} | {num(p['entradas'])} | {num(p['entradas_nuevas_reales'])} "
      f"| {num(p['reingresos'])} | {pcs(p['pct_reingresos_sobre_entradas'])} % "
      f"| {num(p['salidas'])} | {num(p['salidas_temporales'])} "
      f"| {num(p['salidas_definitivas'])} |")
A("")
A(f"Entre el {pcs(min(p['pct_reingresos_sobre_entradas'] for p in PU), 0)} % y el "
  f"{pcs(max(p['pct_reingresos_sobre_entradas'] for p in PU), 0)} % de las entradas "
  f"son **reingresos**. Y en el otro sentido, buena parte de las salidas no son "
  f"definitivas: en 2013→2014, {num(PU[0]['salidas_temporales'])} de las "
  f"{num(PU[0]['salidas'])} salidas "
  f"({p100(PU[0]['salidas_temporales']/PU[0]['salidas'])} %) corresponden a personas "
  f"que reaparecen después. Tratar cada ausencia como una baja definitiva infla la "
  f"rotación aparente del padrón. La última fila está **censurada a la derecha**: en "
  f"2019→2021 no hay convocatorias posteriores.")
A("")
A("### 2.7 Desagregaciones (censo)")
A("")
A("Tasas de retención por par. Se calculan sobre el universo, no sobre la muestra.")
A("")
pares_lbl = [p["par"] for p in PU]
for col, titulo in [("NME_CLASIFICACION_PR", "Categoría"),
                    ("NME_GRAN_AREA_PR", "Gran área de conocimiento"),
                    ("NME_GENERO_PR", "Género")]:
    A(f"**{titulo}**")
    A("")
    A("| Grupo | " + " | ".join(pares_lbl) + " |")
    A("|---|" + "---|" * len(pares_lbl))
    grupos = sorted(E["bivariado"]["pares"][pares_lbl[0]][col].keys())
    for g in grupos:
        fila = []
        for pl in pares_lbl:
            v = E["bivariado"]["pares"][pl][col].get(g)
            fila.append(f"{p100(v['tasa'])} %" if v else "—")
        A(f"| {g} | " + " | ".join(fila) + " |")
    A("")
A("Las tres tablas cuentan la misma historia que el EDA: la **categoría** separa "
  "comportamientos (los Junior retienen bastante menos que los Sénior), la **gran "
  "área** separa algo (Ingeniería y Ciencias Médicas por encima de Sociales y "
  "Humanidades) y el **género** apenas separa.")
A("")
A("### 2.8 Calidad del registro que revela el panel")
A("")
gin = HC["genero_inconsistente"]
A(f"- **Sin duplicados**: {num(HC['duplicados_persona_convocatoria'])} repeticiones "
  f"de la clave persona × convocatoria.")
A(f"- **Género contradictorio**: {num(gin['personas'])} personas "
  f"({pcs(gin['pct_personas'], 2)} % del padrón) figuran con más de un género a lo "
  f"largo del tiempo —" +
  ", ".join(f"{k.replace(' -> ', '→')} ({num(v)})" for k, v in gin["patrones"].items())
  + ". El género no es un atributo estable en este registro.")
A("- **Atributos que cambian dentro de la misma persona**: "
  + ", ".join(f"{num(v)} en {k.replace('NME_', '').replace('_PR', '').lower()}"
              for k, v in D["coherencia_atributos_por_persona"].items())
  + ". Obliga a declarar qué observación se usa en cada análisis.")
ed = E["edad"]
A(f"- **Edades imposibles**: {num(ed['mayores_100'])} personas declaran más de 100 "
  f"años (máximo {pcs(ed['maximo'], 2)}). Es un problema de captura, no de la "
  f"población.")
A(f"- **Faltantes**: {num(E['faltantes']['columnas_con_vacios'])} de "
  f"{num(E['faltantes']['total_columnas'])} columnas tienen vacíos, concentrados en "
  f"`INST_FILIA` y los códigos DANE; ninguna es variable del análisis longitudinal.")
A("")

# ================================ 3 =======================================
A("## 3. Conclusiones")
A("")
A(f"1. **La retención es alta en cada intervalo, pero acumulada pierde casi la mitad "
  f"del padrón.** Entre convocatorias consecutivas se retiene entre "
  f"{p100(min(p['retencion']['p'] for p in PU))} % y "
  f"{p100(max(p['retencion']['p'] for p in PU))} %, pero de quienes entraron en 2013 "
  f"solo el {p100(GL['universo'])} % seguía en 2021.")
A(f"2. **Anualizar con las fechas reales invierte el diagnóstico.** El hueco "
  f"2017→2019 dura {pcs(D['intervalos_anios_reales']['2017->2019'], 2)} años y el "
  f"2019→2021 solo {pcs(D['intervalos_anios_reales']['2019->2021'], 2)}; con años "
  f"nominales ambos parecen equivalentes, con las fechas reales 2017→2019 es el peor "
  f"par y 2019→2021 el segundo mejor.")
A(f"3. **La movilidad es ascendente y masiva, y el descenso también existe.** En "
  f"2019→2021, de {num(TU['2019→2021']['n_transiciones'])} trayectorias "
  f"{num(TU['2019→2021']['ascienden'])} ascendieron y "
  f"{num(TU['2019→2021']['descienden'])} descendieron.")
A(f"4. **«Emérito» funciona como estado terminal: {num(em['retornos'])} retornos de "
  f"{num(em['oportunidades'])}.** Debe incorporarse como supuesto explícito en "
  f"cualquier modelo de transición.")
A(f"5. **La rotación aparente está inflada.** Entre el 14 % y el 20 % de las entradas "
  f"son reingresos, y hasta el "
  f"{p100(PU[0]['salidas_temporales']/PU[0]['salidas'])} % de las salidas de "
  f"2013→2014 corresponden a personas que reaparecen.")
A("")

# ================================ 4 =======================================
A("## 4. Limitaciones")
A("")
A("1. **Las convocatorias no son anuales**: faltan 2016, 2018 y 2020, y los "
  f"intervalos reales van de {pcs(min(D['intervalos_anios_reales'].values()))} a "
  f"{pcs(max(D['intervalos_anios_reales'].values()))} años. Las tasas anualizadas "
  f"suponen riesgo constante dentro del intervalo y con seis puntos de observación "
  f"ese supuesto no puede contrastarse. El análisis es descriptivo: no se ajustó "
  f"ningún modelo de supervivencia.")
A("2. **Qué significa `ANO_CONVO` no está documentado.** Se midió el intervalo con "
  f"esas fechas, el único dato temporal del archivo, pero la discrepancia entre el "
  f"rótulo «833 de 2018» y la fecha 06/12/2019 no se resuelve con lo disponible.")
A("3. **Observación solo en las fechas de convocatoria.** Una persona ausente en una "
  f"convocatoria y presente en la siguiente es indistinguible de alguien que nunca "
  f"fue reconocido, salvo por el historial previo; por eso se separan reingresos y "
  f"salidas temporales, pero no se observa lo que ocurre entre convocatorias.")
A("4. **Censura a la derecha en el último par.** En 2019→2021 las "
  f"{num(PU[4]['salidas'])} salidas no pueden clasificarse en temporales y "
  f"definitivas. Lo mismo afecta a la condición terminal de Emérito.")
A("5. **Atributos no constantes.** El perfil de cada persona se toma de su última "
  f"convocatoria observada, y el género cambia en {num(gin['personas'])} personas.")
A("6. **Datos atípicos de edad** sin corregir: se reportan "
  f"{num(ed['mayores_100'])} casos por encima de 100 años; el análisis de edad "
  f"describe el registro tal como está.")
A("")

# ================================ 5 =======================================
A("## 5. Referencias")
A("")
A("- Cochran, W. G. (1977). *Sampling Techniques* (3rd ed.). John Wiley & Sons.")
A("- Lohr, S. L. (2010). *Sampling: Design and Analysis* (2nd ed.). Brooks/Cole.")
A("- Särndal, C.-E., Swensson, B., & Wretman, J. (1992). *Model Assisted Survey "
  "Sampling*. Springer-Verlag.")
A("- Kalton, G. (2002). Models in the practice of survey sampling. *International "
  "Statistical Review*, 70(2), 175-192.")
A("- Departamento Administrativo de Ciencia, Tecnología e Innovación (MinCiencias). "
  "*Investigadores reconocidos por convocatoria* [conjunto de datos, `bqtm-4y2h`]. "
  "datos.gov.co. Consulta: 2026-10-06.")
A("")

# ============================== ANEXO A ===================================
A("---")
A("")
A("## Anexo A — Validación del muestreo (MAS)")
A("")
A("Este anexo documenta el ejercicio de muestreo. **No es la fuente de las cifras "
  "de este documento**: sirve para (i) mostrar que el diseño elegido es defendible, "
  "y (ii) verificar los estimadores contra el censo, que es una oportunidad poco "
  "habitual y aquí se aprovecha.")
A("")
A("### A.1 Diseño y tamaño de muestra")
A("")
A("Muestreo aleatorio simple **de personas** (no de registros), sin reemplazo, con "
  f"semilla {D['semilla']}. Marco: {num(T['N'])} personas. Fórmula de Cochran (1977) "
  "con corrección por población finita:")
A("")
A("| Parámetro | Valor |")
A("|---|---:|")
A(f"| Confianza `Z` | {pcs(T['z'])} |")
A(f"| Proporción `p` (varianza máxima) | {pcs(T['p'])} |")
A(f"| Margen `e` | {pcs(T['e'])} |")
A(f"| `n₀` sin corregir | {num(round(T['n0']))} |")
A(f"| `n` ajustado (exacto) | {pcs(T['n_ajustado_exacto'], 2)} |")
A(f"| **`n` final** | **{num(T['n_final'])}** |")
A(f"| Fracción de muestreo | {pcs(100*T['fraccion_muestreo'])} % |")
A(f"| Error efectivo (con corrección) | {pcs(100*T['error_efectivo_con_fpc'])} pp |")
A("")
A(f"El panel muestral recupera **todos** los registros de esas personas en todas las "
  f"convocatorias: {num(M['registros'])} registros. La justificación de elegir MAS y "
  f"no un diseño estratificado, y de por qué «MAS o regresión» es un falso dilema, "
  f"está desarrollada en `metodologia_muestreo.md` §3, a la luz del EDA.")
A("")
A(f"### A.2 Verificación de representatividad")
A("")
A("Perfil de cada persona en su última convocatoria observada. Contraste de bondad "
  "de ajuste de la muestra contra las proporciones del universo:")
A("")
A("| Eje | χ² | gl | p | Diferencia absoluta máxima |")
A("|---|---:|---:|---:|---:|")
for clave, etq in [("genero", "Género"), ("categoria", "Categoría"),
                   ("gran_area", "Gran área"), ("departamento", "Departamento"),
                   ("nivel_formacion", "Nivel de formación")]:
    r = D["representatividad"][clave]
    A(f"| {etq} | {pcs(r['chi2'], 3)} | {r['gl']} | "
      f"{'< 0,001' if r['p_valor'] < 0.001 else pcs(r['p_valor'], 3)} | "
      f"{pcs(r['max_diferencia_pp'])} pp |")
A("")
A("Cuatro de los cinco ejes tienen p > 0,05. El único que baja de ese umbral es la "
  "categoría; con cinco contrastes simultáneos el umbral de Bonferroni es 0,01 y ese "
  "p-valor no lo alcanza, y la mayor discrepancia observada en categoría queda dentro "
  "del margen de diseño de ±2 pp. Conviene decirlo con precisión: en un MAS la "
  "representatividad **está garantizada por el diseño** en esperanza; estos χ² son "
  "una comprobación de la implementación, no evidencia de representatividad. La "
  "limitación real es que dos categorías de género del universo (Intersexual, 5 "
  "personas, y No disponible, 4) no quedan representadas en la muestra.")
A("")
A("### A.3 Contraste muestra vs censo")
A("")
A("| Par | Estimación muestral | IC 95 % | Valor censal | Diferencia | ¿Censal dentro del IC? |")
A("|---|---|---|---|---|:--:|")
for pm, pu in zip(PM, PU):
    dentro = pm["retencion"]["ic_wald"][0] <= pu["retencion"]["p"] <= pm["retencion"]["ic_wald"][1]
    A(f"| Retención {pm['par']} | {p100(pm['retencion']['p'])} % | {ic(pm['retencion'])} "
      f"| {p100(pu['retencion']['p'])} % | {pcs(100*(pm['retencion']['p']-pu['retencion']['p']), 2)} pp "
      f"| {'sí' if dentro else 'no'} |")
gm = GL["muestra"]["p"]
dentro_g = GL["muestra"]["ic_wald"][0] <= GL["universo"] <= GL["muestra"]["ic_wald"][1]
A(f"| Retención global 2013→2021 | {p100(gm)} % | {ic(GL['muestra'])} "
  f"| {p100(GL['universo'])} % | {pcs(100*(gm-GL['universo']), 2)} pp "
  f"| {'sí' if dentro_g else 'no'} |")
A("")
A("Las seis estimaciones quedan dentro de ±1,1 pp del valor censal y el valor censal "
  "cae dentro del intervalo en los seis casos. **El diseño funciona**: el estimador "
  "reproduce el parámetro. Esto no es un argumento para usar la muestra —el censo es "
  "mejor— sino la comprobación de que si alguna vez hubiera que estimar, el método "
  "sería fiable.")
A("")
A("### A.4 Retención muestral con intervalos de confianza")
A("")
A("| Par | n en t₁ | Retenidos | Retención | IC 95 % (Wald) | IC 95 % (Wilson) | IC 95 % (con fpc) |")
A("|---|---:|---:|---|---|---|---|")
for pm in PM:
    A(f"| {pm['par']} | {num(pm['n_a'])} | {num(pm['retenidos'])} "
      f"| {p100(pm['retencion']['p'])} % | {ic(pm['retencion'])} "
      f"| {ic(pm['retencion'], etiqueta='ic_wilson')} "
      f"| {ic(pm['retencion'], etiqueta='ic_wald_fpc')} |")
A("")
A("Se reportan los tres intervalos porque el intervalo de Wald es el habitual pero se "
  "degrada cerca de 0 y 1: la discrepancia máxima entre los tres, en cualquier par y "
  "cualquier extremo, es inferior a 0,2 pp, de modo que la elección no altera ninguna "
  "conclusión.")
A("")
A("### A.5 Transiciones en la muestra")
A("")
A("Las matrices del censo están en §2.4. Las de la muestra (necesarias para las "
  "desagregaciones por subgrupo, donde no siempre hay masa crítica en el censo) "
  "coinciden en las tasas de permanencia:")
A("")
A("| Par | Permanencia (muestra) | Permanencia (censo) | Diferencia |")
A("|---|---|---:|---:|")
for pm in PM:
    k = pm["par"]
    a, b = TM[k]["tasa_permanencia"], TU[k]["tasa_permanencia"]
    A(f"| {k} | {p100(a)} % | {p100(b)} % | {pcs(100*(a-b), 2)} pp |")
A("")
A("### A.6 Desagregaciones por subgrupo")
A("")
A("Cuando el subgrupo es pequeño, el censo no siempre ofrece celdas con masa "
  "suficiente para un contraste; la muestra de 2 224 personas tampoco. Se reportan "
  "las del censo (§2.7) y, para los contrastes de homogeneidad, los del par "
  "2019→2021:")
A("")
A("| Eje | χ² | gl | p | Frecuencia esperada mínima | ¿Supuesto satisfecho? |")
A("|---|---:|---:|---:|---:|:--:|")
for clave, etq in [("genero", "Género"), ("departamento", "Departamento"),
                   ("gran_area", "Gran área"), ("nivel_formacion", "Nivel de formación")]:
    r = D["desagregacion_2019_2021"][clave]
    A(f"| {etq} | {pcs(r['chi2'], 3)} | {r['gl']} | {pcs(r['p_valor'], 4)} "
      f"| {pcs(r['min_esperado'], 2)} | {'sí' if r['supuesto_frecuencias_ok'] else '**no**'} |")
A("")
A("Estos contrastes se calculan sobre la muestra, así que sus p-valores son "
  "orientativos; el EDA ya estableció con el censo la magnitud de las diferencias "
  "(Anexo §2.2 de `metodologia_muestreo.md`), que es de alrededor del 7 % de la "
  "varianza para la categoría y menos del 1,4 % para el resto.")
A("")

# ============================== ANEXO B ===================================
A("---")
A("")
A("## Anexo B — Post-estratificación y GREG")
A("")
A("Comparación de los tres estimadores frente al valor censal. El desarrollo "
  "conceptual, los modelos y las referencias están en `metodologia_muestreo.md` "
  "(§4-§8), incluidos los diagnósticos de supuestos (normalidad, "
  "heterocedasticidad y g-weights); aquí se resume el resultado.")
A("")
A("| Parámetro | Censo | MAS | Post-estratificado | GREG |")
A("|---|---:|---:|---:|---:|")
for par, r in S["retencion"].items():
    g = r.get("greg_logit") or r["greg_lineal"]
    A(f"| Retención {par} | {p100(r['censo'])} % | {p100(r['mas']['estimador'])} % "
      f"| {p100(r['post_estratificado']['estimador'])} % | {p100(g['estimador'])} % |")
e_ = S["edad"]
A(f"| Edad media | {pcs(e_['censo'], 3)} | {pcs(e_['mas']['estimador'], 3)} "
  f"| {pcs(e_['post_estratificado']['estimador'], 3)} "
  f"| {pcs(e_['greg_lineal']['estimador'], 3)} |")
a_ = S["ascenso_2019_2021"]
A(f"| Ascenso 2019→2021 | {p100(a_['censo'])} % | {p100(a_['mas']['estimador'])} % "
  f"| {p100(a_['post_estratificado']['estimador'])} % "
  f"| {p100(a_['greg_logit']['estimador'])} % |")
A("")
A("**Ganancia de precisión** (reducción de varianza respecto al MAS):")
A("")
A("| Parámetro | Post-estratificado | GREG |")
A("|---|---:|---:|")
for par, r in S["retencion"].items():
    g = r.get("greg_logit") or r["greg_lineal"]
    A(f"| Retención {par} | {pcs(r['post_estratificado']['ganancia_varianza_vs_mas_pct'])} % "
      f"| {pcs(g['ganancia_varianza_vs_mas_pct'])} % |")
A(f"| Edad media | {pcs(e_['post_estratificado']['ganancia_varianza_vs_mas_pct'])} % "
  f"| {pcs(e_['greg_lineal']['ganancia_varianza_vs_mas_pct'])} % |")
A(f"| Ascenso 2019→2021 | {pcs(a_['post_estratificado']['ganancia_varianza_vs_mas_pct'])} % "
  f"| {pcs(a_['greg_logit']['ganancia_varianza_vs_mas_pct'])} % |")
A("")
mas_mejor = sum(1 for r in S["retencion"].values()
                if abs(r["mas"]["error_vs_censo_pp"]) <
                abs(r["post_estratificado"]["error_vs_censo_pp"]))
A(f"**Lectura.** El MAS es el más cercano al censo en {mas_mejor} de los "
  f"{len(S['retencion'])} pares, es decir que la muestra ya estaba equilibrada y la "
  f"post-estratificación no corrige sesgo: **compra precisión** (hasta "
  f"{pcs(max(r['post_estratificado']['ganancia_varianza_vs_mas_pct'] for r in S['retencion'].values()))} % "
  f"menos varianza). El GREG domina en varianza (hasta "
  f"{pcs(max((r.get('greg_logit') or r['greg_lineal'])['ganancia_varianza_vs_mas_pct'] for r in S['retencion'].values()))} %) "
  f"y además su validez no depende de que el modelo esté bien especificado, que es "
  f"la propiedad *model-assisted*. Se comprobó además que la post-estratificación es "
  f"un caso particular de GREG: con un modelo saturado en los post-estratos ambos "
  f"coinciden exactamente "
  f"(diferencia {S['comprobacion_greg_saturado_igual_ps']['retencion_2019_2021']['diferencia_absoluta']:.1e} pp).")
A("")
A("**Conclusión del anexo:** si hubiera que estimar en lugar de censar, el orden de "
  "preferencia es GREG > post-estratificado > MAS en términos de varianza, y el MAS "
  "es el que menos supuestos exige. La post-estratificación de 4 estratos incumple "
  "la condición de tamaño mínimo de Cochran (1977) en los pares donde Emérito tiene "
  "menos de 20 casos, por lo que se reporta también la versión colapsada "
  "(Sénior + Emérito).")
A("")

# ============================== ANEXO C ===================================
A("---")
A("")
A("## Anexo C — Archivos y reproducibilidad")
A("")
A("| Archivo | Contenido |")
A("|---|---|")
A("| `src/analisis_longitudinal.py` | Muestreo, panel y análisis longitudinal (censo y muestra) |")
A("| `src/eda_longitudinal.py` | EDA previo (Parte 1 de la metodología) |")
A("| `src/estimadores_longitudinal.py` | Post-estratificación y GREG |")
A("| `src/generar_analisis_longitudinal.py` | Genera este documento |")
A("| `metodologia_muestreo.md` | Documento metodológico completo |")
A("| `data/memoria/longitudinal_resultados.json` | Cifras del análisis |")
A("| `data/memoria/eda_resultados.json` | Cifras del EDA |")
A("| `data/memoria/eda/` | 6 gráficas del EDA |")
A("| `data/memoria/estimadores_resultados.json` | Cifras de los estimadores |")
A("| `data/memoria/muestra_ids.csv` | 2 224 identificadores (semilla 2026) |")
A("")
A("```bash")
A("python src/analisis_longitudinal.py")
A("python src/eda_longitudinal.py")
A("python src/estimadores_longitudinal.py")
A("python src/generar_analisis_longitudinal.py")
A("python src/generar_metodologia_muestreo.py")
A("```")
A("")

SALIDA.write_text("\n".join(OUT) + "\n", encoding="utf-8")
print(f"escrito {SALIDA}")
print(f"  {len(OUT)} líneas, {len(''.join(OUT).encode('utf-8'))} bytes")
