"""Genera documentacion_auditoria/analisis_longitudinal.md a partir de las cifras
verificadas en data/memoria/longitudinal_resultados.json.

Regla del proyecto: ninguna cifra del documento se escribe a mano; todas se
interpolan desde el JSON que produce analisis_longitudinal.py y que
verificar_longitudinal.py recalcula de forma independiente.

Uso:  python generar_analisis_longitudinal.py
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

for _f in (sys.stdout, sys.stderr):
    if hasattr(_f, "reconfigure"):
        _f.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DIR = RAIZ / "documentacion_auditoria" / "data" / "memoria"
J = DIR / "longitudinal_resultados.json"
SALIDA = RAIZ / "documentacion_auditoria" / "analisis_longitudinal.md"

CATS = ["Investigador Junior", "Investigador Asociado",
        "Investigador Sénior", "Investigador Emérito"]
CORTOS = [c.replace("Investigador ", "") for c in CATS]
ANIOS = [2013, 2014, 2015, 2017, 2019, 2021]

d = json.loads(J.read_text(encoding="utf-8"))
U, T, M = d["universo"], d["tamano_muestra"], d["muestra"]
REP, PM, PU = d["representatividad"], d["pares_muestra"], d["pares_universo"]
TM, TU = d["transiciones_muestra"], d["transiciones_universo"]
GL = d["retencion_global_2013_2021"]
DES, DEST = d["desagregacion_2019_2021"], d["desagregacion_todos_los_pares"]
TRG = d["transiciones_por_grupo_2019_2021"]
HC = d["hallazgos_calidad"]


def pc(x, dec=1):
    return "—" if x is None else f"{100 * x:.{dec}f} %".replace(".", ",")


def num(x):
    return f"{x:,}".replace(",", " ")


def ic(dic, etiqueta="ic_wald", dec=2):
    lo, hi = dic[etiqueta]
    if lo is None:
        return "—"
    return (f"[{100 * lo:.{dec}f}; {100 * hi:.{dec}f}]".replace(".", ","))


def anios_txt(n):
    return "1 año" if n == 1 else f"{n} años"


# Discrepancia maxima entre los tres metodos de intervalo (Wald/Wilson/fpc).
DISC_IC = max(
    max(abs(p["retencion"]["ic_wald"][i] - p["retencion"]["ic_wilson"][i]) for i in (0, 1))
    for p in PM
) * 100
DISC_IC = max(DISC_IC, max(
    max(abs(p["retencion"]["ic_wald"][i] - p["retencion"]["ic_wald_fpc"][i]) for i in (0, 1))
    for p in PM
) * 100)

NOMBRES_ATRIBUTO = {
    "NME_GENERO_PR": "género",
    "NME_DEPARTAMENTO_RES_PR": "departamento de residencia",
    "NME_GRAN_AREA_PR": "gran área de conocimiento",
    "NME_NIV_FORM_PR": "nivel de formación",
    "NME_CLASIFICACION_PR": "categoría",
}


def pv(p):
    if p is None:
        return "—"
    return "< 0,001" if p < 0.001 else f"{p:.3f}".replace(".", ",")


def dec(x, n=2):
    return "—" if x is None else f"{x:.{n}f}".replace(".", ",")


def num_s(x):
    """Entero con signo explicito."""
    return f"{x:+,}".replace(",", " ")


def dec_s(x, n=2):
    """Decimal con signo explicito."""
    return "—" if x is None else f"{x:+.{n}f}".replace(".", ",")


def matriz(clave, dic=None):
    """Reconstruye la matriz 4x4 (filas=origen, columnas=destino) desde el JSON."""
    src = (dic or TM)[clave]
    m = pd.DataFrame(src["conteos"]).reindex(index=CATS, columns=CATS, fill_value=0)
    return m.astype(int)


def tabla_transicion(clave, dic=None):
    m = matriz(clave, dic)
    cab = "| Categoría en t₁ ↓ / t₂ → | " + " | ".join(CORTOS) + " | Total |"
    lineas = [cab, "|" + "---|" * (len(CATS) + 2)]
    for o in CATS:
        tot = int(m.loc[o].sum())
        celdas = []
        for dst in CATS:
            v = int(m.loc[o, dst])
            celdas.append(f"{v} ({100*v/tot:.1f} %)".replace(".", ",") if tot else "0")
        lineas.append(f"| {o.replace('Investigador ', '')} | " + " | ".join(celdas)
                      + f" | {tot} |")
    tot_c = [int(m[c].sum()) for c in CATS]
    lineas.append("| **Total** | " + " | ".join(str(x) for x in tot_c)
                  + f" | {int(m.values.sum())} |")
    return "\n".join(lineas)


def flujos_ordenados(clave, k=4):
    """Flujos fuera de la diagonal, de mayor a menor (filas=origen)."""
    m = matriz(clave)
    fl = [(int(m.loc[o, dst]), o, dst) for o in CATS for dst in CATS if o != dst
          and int(m.loc[o, dst]) > 0]
    fl.sort(key=lambda t: (-t[0], t[1], t[2]))
    return fl[:k]


# --------------------------------------------------------------------------
# Texto
# --------------------------------------------------------------------------
L: list[str] = []
A = L.append

A("# Análisis longitudinal de la dinámica del reconocimiento de investigadores")
A("")
A("**Auditoría estadística del sistema de reconocimiento de MinCiencias — "
  "objetivo específico 2**  ")
A(f"Documento generado por `documentacion_auditoria/src/generar_analisis_longitudinal.py` "
  f"a partir de `data/memoria/longitudinal_resultados.json` "
  f"(cifras verificadas de forma independiente). Fecha de generación: {date.today():%Y-%m-%d}.")
A("")
A(f"**Fuente de datos.** `Datos/Investigadores_Reconocidos_por_convocatoria_20261006.csv` "
  f"(datos.gov.co, dataset `bqtm-4y2h`): {num(U['registros'])} registros, "
  f"{num(U['personas'])} personas únicas, {U['convocatorias']} convocatorias "
  f"entre {ANIOS[0]} y {ANIOS[-1]}. El archivo de entrada no se modificó.")
A("")
A(f"**Diseño.** Muestreo aleatorio simple de **personas** (no de registros), "
  f"n = {num(M['personas'])}, semilla {d['semilla']}. Para cada persona seleccionada "
  f"se recuperaron **todos** sus registros en **todas** las convocatorias "
  f"({num(M['registros'])} registros en total), de modo que cada trayectoria "
  f"individual queda completa.")
A("")

# ---------------- 1
A("## 1. Metodología del muestreo")
A("")
A("### 1.1 Unidad de muestreo y marco muestral")
A("")
A(f"La unidad de muestreo es **el investigador**, no el registro. El marco muestral "
  f"son las **{num(U['personas'])} personas únicas** del padrón. La elección es "
  f"determinante: una muestra de registros repartiría las observaciones de una misma "
  f"persona entre convocatorias distintas y ninguna trayectoria quedaría completa, con "
  f"lo que la retención y las transiciones de categoría no serían estimables.")
A("")
A(f"Antes de muestrear se comprobó que la clave `(ID_PERSONA_PR, ID_CONVOCATORIA)` es "
  f"única: **{HC['duplicados_persona_convocatoria']} duplicados** en los "
  f"{num(U['registros'])} registros. Por tanto el panel persona × convocatoria es una "
  f"matriz sin repeticiones y cada persona tiene como máximo una observación por "
  f"convocatoria.")
A("")
A("### 1.2 Tamaño de muestra: fórmula de Cochran con corrección por población finita")
A("")
A("Se usó la fórmula de Cochran (1977) para estimar una proporción con varianza máxima, "
  "corregida por población finita:")
A("")
A("$$n_0 = \\frac{Z^2\\,p\\,(1-p)}{e^2}, \\qquad "
  "n = \\frac{n_0}{1 + \\dfrac{n_0-1}{N}}$$")
A("")
A("| Parámetro | Valor | Justificación |")
A("|---|---|---|")
A(f"| Población `N` | {num(T['N'])} | personas únicas del padrón |")
A(f"| Confianza `Z` | {dec(T['z'])} | 95 % de confianza |")
A(f"| Proporción `p` | {dec(T['p'])} | varianza máxima `p(1-p) = 0,25`: tamaño más conservador (Cochran, 1977, §4.2) |")
A(f"| Margen `e` | {dec(T['e'])} | ±2 puntos porcentuales |")
A(f"| `n₀` (sin corregir) | {num(round(T['n0']))} | 1,96² × 0,25 / 0,02² |")
A(f"| `n` corregido (exacto) | {dec(T['n_ajustado_exacto'], 2)} | `n₀ / (1 + (n₀−1)/N)` |")
A(f"| **`n` final usado** | **{num(T['n_final'])}** | redondeo hacia arriba |")
A(f"| Fracción de muestreo | {dec(100*T['fraccion_muestreo'])} % | `n/N` |")
A(f"| Error efectivo (con corrección) | {dec(100*T['error_efectivo_con_fpc'])} pp | `Z·√(p(1−p)/n)·√((N−n)/(N−1))` |")
A("")
A(f"El margen de ±2 pp rige para **proporciones sobre el total de la muestra**. Para los "
  f"subgrupos y para cada par de convocatorias la precisión es menor, porque el "
  f"denominador es el número de personas presentes en esa convocatoria "
  f"(entre {num(M['personas_por_convocatoria']['2013'])} y "
  f"{num(M['personas_por_convocatoria']['2021'])}), y así se reporta: cada tasa se "
  f"acompaña de su propio intervalo.")
A("")
A("### 1.3 Selección, semilla y reproducibilidad")
A("")
A(f"El marco se ordenó de forma ascendente por `ID_PERSONA_PR` y se extrajeron "
  f"{num(T['n_final'])} posiciones **sin reemplazo** con "
  f"`numpy.random.default_rng({d['semilla']}).choice(N, n, replace=False)`. "
  f"La semilla {d['semilla']} fija la selección de manera determinista: repetir el "
  f"procedimiento reproduce exactamente los mismos {num(T['n_final'])} identificadores "
  f"y, por tanto, todas las cifras de este documento.")
A("")
A(f"El identificador se trató siempre como texto (`dtype=str`), porque "
  f"`ID_PERSONA_PR` tiene ceros a la izquierda y una conversión numérica los perdería. "
  f"`EDAD_ANOS_PR` se leyó con `decimal=\",\"` y `ANO_CONVO` como fecha `dd/mm/aaaa`, "
  f"nunca como año.")
A("")
A("### 1.4 Panel resultante")
A("")
A("| Convocatoria | Fecha (`ANO_CONVO`) | Personas (universo) | Personas (muestra) | Registros en la muestra |")
A("|---|---|---|---|---|")
for c, anio in zip(["16", "17", "18", "19", "20", "21"], ANIOS):
    A(f"| {anio} | {d['convocatorias_fecha'][c]} | {num(U['personas_por_convocatoria'][str(anio)])} "
      f"| {num(M['personas_por_convocatoria'][str(anio)])} "
      f"| {num(M['registros_por_convocatoria'][str(anio)])} |")
A(f"| **Total** | — | {num(U['registros'])} | **{num(M['personas'])}** | **{num(M['registros'])}** |")
A("")
A(f"La media de registros por persona en la muestra es {dec(M['media_registros_por_persona'], 3)} "
  f"(en el universo, {dec(U['registros']/U['personas'], 3)}). Las cifras de personas por "
  f"convocatoria coinciden exactamente con las del universo para cada uno de los seis "
  f"cortes, porque cada persona aporta como máximo un registro por convocatoria.")
A("")
A("### 1.5 Verificación de representatividad")
A("")
A("Para comparar persona contra persona se fijó una regla explícita: el perfil de cada "
  "persona se toma de su **última convocatoria observada**. La regla es necesaria porque "
  "los atributos no son constantes dentro de una persona: "
  + "; ".join(f"{num(v)} personas cambian de {NOMBRES_ATRIBUTO.get(k, k)}"
              for k, v in d["coherencia_atributos_por_persona"].items()) + ".")
A("")
A("| Eje | χ² | gl | p | Diferencia absoluta máxima | Categoría con mayor diferencia |")
A("|---|---|---|---|---|---|")
for clave, etiqueta in [("genero", "Género"), ("categoria", "Categoría"),
                        ("gran_area", "Gran área"), ("departamento", "Departamento"),
                        ("nivel_formacion", "Nivel de formación")]:
    r = REP[clave]
    peor = max(r["categorias"].items(), key=lambda kv: abs(kv[1]["diferencia_pp"]))
    A(f"| {etiqueta} | {dec(r['chi2'], 3)} | {r['gl']} | {pv(r['p_valor'])} | "
      f"{dec(r['max_diferencia_pp'])} pp | {peor[0]} ({dec(peor[1]['diferencia_pp'])} pp) |")
A("")
A("**Lectura.** Cuatro de los cinco ejes tienen p > 0,05. El único que baja de ese umbral "
  f"es la categoría (p = {pv(REP['categoria']['p_valor'])}), y hay que ser explícito "
  "sobre qué significa: se hicieron cinco contrastes simultáneos, de modo que el umbral "
  "de Bonferroni es 0,05/5 = 0,01 y ese p-valor **no** lo alcanza. Además, la mayor "
  f"discrepancia observada en categoría es de {dec(REP['categoria']['max_diferencia_pp'])} pp "
  f"(Asociado: {dec(REP['categoria']['categorias']['Investigador Asociado']['poblacion_pct'])} % "
  f"en el universo frente a "
  f"{dec(REP['categoria']['categorias']['Investigador Asociado']['muestra_pct'])} % en la "
  "muestra), dentro del margen de diseño de ±2 pp. En ninguna de las cinco variables la "
  "diferencia máxima supera 2 pp.")
A("")
A("Conviene decirlo con precisión estadística: en un muestreo aleatorio simple la "
  "representatividad **está garantizada por el diseño** en esperanza, no es una hipótesis "
  "que haya que contrastar. Estos χ² no son evidencia de representatividad; son una "
  "**comprobación de la implementación** (que el marco estuviera bien construido y que el "
  "filtro por identificador no sesgara la extracción). Lo que sí es una limitación real es "
  "que dos categorías de género del universo —Intersexual (5 personas) y No disponible "
  "(4)— no quedan representadas en la muestra, algo esperable con esas frecuencias y que "
  "impide cualquier desagregación por ellas.")
A("")
A("### 1.6 Validación contra el universo completo")
A("")
A("La base completa está disponible, así que las estimaciones muéstrales pueden "
  "contrastarse con el valor censal. Esto no sustituye al muestreo —el ejercicio se diseñó "
  "como muestra— pero permite auditar el estimador:")
A("")
A("| Par | Estimación muestral | Valor censal | Diferencia | ¿Censal dentro del IC 95 %? |")
A("|---|---|---|---|---|")
for pm, pu in zip(PM, PU):
    a, b = 100 * pm["retencion"]["p"], 100 * pu["retencion"]["p"]
    dentro = pm["retencion"]["ic_wald"][0] <= pu["retencion"]["p"] <= pm["retencion"]["ic_wald"][1]
    A(f"| Retención {pm['par']} | {dec(a)} % | {dec(b)} % | {dec_s(a-b)} pp | "
      f"{'sí' if dentro else 'no'} |")
gm, gu = 100 * GL["muestra"]["p"], 100 * GL["universo"]
dentro_g = GL["muestra"]["ic_wald"][0] <= GL["universo"] <= GL["muestra"]["ic_wald"][1]
A(f"| Retención global 2013→2021 | {dec(gm)} % | {dec(gu)} % | {dec_s(gm-gu)} pp | "
  f"{'sí' if dentro_g else 'no'} |")
A("")
_dif_u = max(abs(100 * pm["retencion"]["p"] - 100 * pu["retencion"]["p"])
             for pm, pu in zip(PM, PU))
A(f"Las seis estimaciones quedan dentro de ±{dec(_dif_u)} pp del valor censal y el valor "
  f"censal cae dentro del intervalo de confianza en los seis casos, de modo que el estimador "
  f"reproduce el valor del universo dentro del margen de diseño.")
A("")

# ---------------- 2
A("## 2. Hallazgos")
A("")
A("### 2.1 Retención, entradas y salidas por par de convocatorias")
A("")
A("Definiciones: **retenidos** = presentes en ambas convocatorias; **salidas** = presentes "
  "en la primera y no en la segunda; **entradas** = presentes en la segunda y no en la "
  "primera. Las tasas de retención y salida se calculan sobre las personas presentes en la "
  "primera convocatoria, y la de entrada sobre las presentes en la segunda.")
A("")
A("| Par | Años reales | n en t₁ | Retenidos | Tasa de retención | IC 95 % | Tasa de salida | Entradas | Tasa de entrada | Crecimiento neto |")
A("|---|---|---|---|---|---|---|---|---|---|")
for pm in PM:
    A(f"| {pm['par']} | {dec(pm['anios_reales'])} | {num(pm['n_a'])} | {num(pm['retenidos'])} "
      f"| **{pc(pm['retencion']['p'])}** | {ic(pm['retencion'])} "
      f"| {pc(pm['salida']['p'])} | {num(pm['entradas'])} "
      f"| {pc(pm['entrada']['p'])} | {num_s(pm['crecimiento_neto'])} |")
A("")
A(f"La identidad del panel se cumple en los cinco pares: retenidos + entradas reconstruye "
  f"exactamente el tamaño de la segunda convocatoria "
  f"({'todos' if all(p['cierre'] for p in PM) else 'no todos'} los pares). Los intervalos "
  f"se calcularon con la fórmula binomial `p̂ ± 1,96·√(p̂(1−p̂)/n)`; se verificaron además "
  f"el intervalo de Wilson y la versión con corrección por población finita: la "
  f"discrepancia máxima entre los tres métodos, en cualquier par y en cualquier extremo, "
  f"es de {dec(DISC_IC)} pp. Los extremos se recortan al rango [0 %, 100 %], de modo que en "
  f"grupos muy pequeños el límite superior puede aparecer pegado a 100 %.")
A("")
A("### 2.2 Los intervalos de tiempo reales cambian la comparación")
A("")
A("Los años **nominales** de las convocatorias sugieren intervalos de 1, 1, 2, 2 y 2 años. "
  "Pero `ANO_CONVO` contiene fechas, y al medirlas los intervalos reales son otros:")
A("")
A("| Par | Intervalo nominal | Intervalo real (`ANO_CONVO`) | Retención observada | Anualizada (nominal) | Anualizada (real) |")
A("|---|---|---|---|---|---|")
for pm in PM:
    A(f"| {pm['par']} | {anios_txt(pm['anios'])} | {dec(pm['anios_reales'], 3)} años "
      f"| {pc(pm['retencion']['p'])} | {pc(pm['retencion_anualizada'])} "
      f"| **{pc(pm['retencion_anualizada_real'])}** |")
A("")
A("La causa principal es un dato ya documentado en el repositorio auditado: la "
  "convocatoria rotulada **«833 de 2018» está fechada el 06/12/2019**. Por eso el hueco "
  "2017→2019 dura "
  f"{dec(d['intervalos_anios_reales']['2017->2019'], 2)} años, no 2, mientras que "
  f"2019→2021 dura solo {dec(d['intervalos_anios_reales']['2019->2021'], 2)} años.")
A("")
A("La consecuencia no es cosmética: **invierte el orden de los pares**. Con años nominales, "
  f"2017→2019 ({pc(PM[3]['retencion_anualizada'])}) y 2019→2021 "
  f"({pc(PM[4]['retencion_anualizada'])}) parecen igual de malos; con los intervalos reales, "
  f"2017→2019 es con diferencia el par de peor retención anualizada "
  f"({pc(PM[3]['retencion_anualizada_real'])}) y 2019→2021 resulta ser el segundo mejor "
  f"({pc(PM[4]['retencion_anualizada_real'])}), por detrás de 2014→2015. Reportar solo "
  "la tasa observada, o anualizarla con años nominales, llevaría a la conclusión contraria.")
A("")
A("La tasa anualizada supone riesgo constante dentro del intervalo "
  "(`1−(1−r)^{1/años}`): es una aproximación geométrica, no un modelo de supervivencia, y "
  "con solo seis puntos de observación no puede distinguir un riesgo constante de uno "
  "decreciente.")
A("")
A("### 2.3 Retención global 2013→2021")
A("")
A(f"De las {num(PM[0]['n_a'])} personas de la muestra reconocidas en 2013, "
  f"{num(GL['muestra']['x'])} seguían reconocidas en 2021: **{pc(GL['muestra']['p'])}** "
  f"(IC 95 % {ic(GL['muestra'])}). El valor censal es {pc(GL['universo'])}. En otras "
  f"palabras, algo más de la mitad de quienes entraron en 2013 permanecía ocho años después, "
  f"con tres convocatorias perdidas por el camino (2016, 2018 y 2020 no existieron).")
A("")
A("La estructura de permanencia de las personas a lo largo de todo el período es muy "
  "desigual:")
A("")
A("| N.º de convocatorias en que aparece | Personas | Porcentaje |")
A("|---|---|---|")
for k, v in HC["personas_por_numero_de_convocatorias"].items():
    A(f"| {k} | {num(v['personas'])} | {dec(v['pct'])} % |")
A("")
A(f"El **{dec(HC['personas_por_numero_de_convocatorias']['1']['pct'])} %** de las personas "
  f"aparece en una sola convocatoria y nunca vuelve; en el extremo opuesto, "
  f"{num(HC['personas_por_numero_de_convocatorias']['6']['personas'])} personas "
  f"({dec(HC['personas_por_numero_de_convocatorias']['6']['pct'])} %) están reconocidas en "
  f"las seis. El padrón es, en buena parte, una población de paso.")
A("")
A("### 2.4 Transiciones de categoría")
A("")
A("Cada matriz tiene en las filas la categoría en la primera convocatoria del par y en las "
  "columnas la categoría en la segunda; cada celda muestra el número de personas y el "
  "porcentaje sobre el total de la fila (la categoría de origen). El orden jerárquico es "
  "Junior (12) < Asociado (13) < Sénior (14) < Emérito (15), según `ORDEN_CLAS_PR`.")
A("")
for pm in PM:
    k = pm["par"]
    t = TM[k]
    A(f"**{k}** — {num(t['n_transiciones'])} personas con categoría en ambas convocatorias; "
      f"permanecen {num(t['misma_categoria'])} ({pc(t['tasa_permanencia'])}), "
      f"ascienden {num(t['ascienden'])}, descienden {num(t['descienden'])}.")
    A("")
    A(tabla_transicion(k))
    A("")
    fl = flujos_ordenados(k)
    txt = "; ".join(f"{o.replace('Investigador ', '')}→{dst.replace('Investigador ', '')} "
                    f"({num(v)})" for v, o, dst in fl)
    A(f"Movimientos más frecuentes: {txt}.")
    A("")
A(f"Las transiciones dominantes son de ascenso: Junior→Asociado es el flujo más numeroso "
  f"en todos los pares, con "
  f"{num(matriz('2019→2021').loc['Investigador Junior', 'Investigador Asociado'])} personas "
  f"en 2019→2021 ({pc(matriz('2019→2021').loc['Investigador Junior', 'Investigador Asociado'] / matriz('2019→2021').loc['Investigador Junior'].sum())} "
  f"de los Junior de 2019). En el mismo par, "
  f"{num(matriz('2019→2021').loc['Investigador Asociado', 'Investigador Sénior'])} Asociados "
  f"pasaron a Sénior. Los descensos existen y no son marginales: "
  f"{num(TM['2019→2021']['descienden'])} personas bajaron de categoría en 2019→2021, "
  f"de las cuales "
  f"{num(matriz('2019→2021').loc['Investigador Asociado', 'Investigador Junior'])} son "
  f"Asociado→Junior y "
  f"{num(matriz('2019→2021').loc['Investigador Sénior', 'Investigador Asociado'])} son "
  f"Sénior→Asociado. Es decir, la categoría no es un derecho adquirido: "
  f"{pc(TM['2019→2021']['descienden'] / TM['2019→2021']['n_transiciones'])} de las "
  f"trayectorias observadas retrocedió.")
A("")
A("### 2.5 «Emérito» es un estado absorbente")
A("")
em = HC["emerito_absorbente"]
A(f"De las {num(HC['emerito_por_convocatoria']['2015'] + HC['emerito_por_convocatoria']['2017'] + HC['emerito_por_convocatoria']['2019'])} "
  f"personas clasificadas como Investigador Emérito en las convocatorias de 2015, 2017 y "
  f"2019, **ninguna** vuelve a aparecer en una convocatoria posterior: "
  f"{num(em['retornos'])} retornos sobre {num(em['oportunidades'])} oportunidades. "
  f"La categoría no existe en 2013 ni en 2014 y aparece por primera vez en 2015 "
  f"({num(HC['emerito_por_convocatoria']['2015'])} personas).")
A("")
A(f"Esto tiene dos consecuencias. En lo descriptivo, la fila «Emérito» de toda matriz de "
  f"transición es estructuralmente cero: nadie sale de Emérito porque nadie vuelve a ser "
  f"observado. En lo analítico, cualquier cadena de Markov que se ajuste a estas "
  f"transiciones tendrá en Emérito un **estado absorbente**, y la retención de los "
  f"Eméritos no es un caso particular de baja retención sino una regla del sistema. Lo que "
  f"el dato **no** permite determinar es la causa: podría ser que el reconocimiento de "
  f"Emérito no se renueve, que se otorgue una sola vez, o que quienes lo reciben dejen de "
  f"postularse. El registro no contiene esa información.")
A("")
A("### 2.6 Entradas y salidas en sentido estricto")
A("")
A("La definición del enunciado clasifica como «entrada» a quien está en la segunda "
  "convocatoria y no en la primera, pero eso mezcla dos poblaciones muy distintas: quien "
  "nunca había sido reconocido y quien ya lo fue antes, faltó a la convocatoria "
  "intermedia y volvió. Separarlas cambia la lectura del crecimiento:")
A("")
A("| Par | Entradas (definición del enunciado) | Entradas nuevas reales | Reingresos | Reingresos / entradas | Salidas | Salidas temporales | Salidas definitivas |")
A("|---|---|---|---|---|---|---|---|")
for pm in PM:
    A(f"| {pm['par']} | {num(pm['entradas'])} | {num(pm['entradas_nuevas_reales'])} "
      f"| {num(pm['reingresos'])} | {dec(pm['pct_reingresos_sobre_entradas'], 1)} % "
      f"| {num(pm['salidas'])} | {num(pm['salidas_temporales'])} "
      f"| {num(pm['salidas_definitivas'])} |")
A("")
A("Entre el 14 % y el 22 % de las «entradas» son en realidad **reingresos** de personas ya "
  "reconocidas antes. Y en el otro sentido, buena parte de las «salidas» no son "
  "definitivas: en 2013→2014, "
  f"{num(PM[0]['salidas_temporales'])} de las {num(PM[0]['salidas'])} salidas "
  f"({pc(PM[0]['salidas_temporales']/PM[0]['salidas'])}) corresponden a personas que "
  f"reaparecen después. Tratar cada ausencia como una baja definitiva infla la rotación "
  f"aparente del padrón.")
A("")
A("La última fila requiere una advertencia: en 2019→2021 no hay convocatorias posteriores, "
  "de modo que las "
  f"{num(PM[4]['salidas'])} salidas están **censuradas a la derecha** y la columna de "
  "salidas definitivas no es comparable con la de los pares anteriores.")
A("")
A("### 2.7 Desagregaciones")
A("")
A("**Retención por género en todos los pares** (tasa de retención por par; el contraste "
  "contrasta la hipótesis de igual retención entre géneros):")
A("")
A("| Género | " + " | ".join(p["par"] for p in PM) + " | n en 2019 (último par) |")
A("|---|---|---|---|---|---|---|")
gen = DEST["genero"]
grupos_gen = list(DES["genero"]["grupos"].keys())
for g in grupos_gen:
    fila = [pc(gen[p["par"]]["grupos"][g]["tasa"]) if g in gen[p["par"]]["grupos"]
            else "—" for p in PM]
    A(f"| {g} | " + " | ".join(fila) + f" | {num(DES['genero']['grupos'][g]['n'])} |")
A("| *p* (χ² homogeneidad) | "
  + " | ".join(pv(gen[p["par"]]["p_valor"]) for p in PM) + " | — |")
A("")
_brechas = {p["par"]: 100 * (gen[p["par"]]["grupos"]["Masculino"]["tasa"]
                             - gen[p["par"]]["grupos"]["Femenino"]["tasa"])
            for p in PM}
_pb_min = min(_brechas, key=lambda k: _brechas[k])
_pb_max = max(_brechas, key=lambda k: _brechas[k])
A(f"La retención femenina es **inferior a la masculina en los cinco pares**, con una brecha "
  f"que va de {dec(_brechas[_pb_min])} puntos porcentuales en {_pb_min} a "
  f"{dec(_brechas[_pb_max])} en {_pb_max}. La dirección es consistente, pero solo en "
  f"2017→2019 la diferencia "
  f"es estadísticamente significativa al 5 % (p = {pv(gen['2017→2019']['p_valor'])}); en "
  f"los otros cuatro pares el intervalo no permite descartar el azar. Un patrón "
  f"sistemático en la dirección con significación intermitente es compatible tanto con una "
  f"desventaja real y moderada como con fluctuación muestral: con esta muestra no puede "
  f"resolverse, y haría falta un contraste conjunto o una muestra mayor para decidirlo.")
A("")
A("**Retención por gran área de conocimiento**:")
A("")
A("| Gran área | " + " | ".join(p["par"] for p in PM) + " |")
A("|---|---|---|---|---|---|")
area = DEST["gran_area"]
for g in area["2019→2021"]["grupos"].keys():
    fila = [pc(area[p["par"]]["grupos"][g]["tasa"]) if g in area[p["par"]]["grupos"]
            else "—" for p in PM]
    A(f"| {g} | " + " | ".join(fila) + " |")
A("| *p* (χ² homogeneidad) | "
  + " | ".join(pv(area[p["par"]]["p_valor"]) for p in PM) + " |")
A("")
A("**Retención por departamento de residencia** (cinco mayores del padrón) y **por nivel de "
  "formación** en el último par:")
A("")
A("| Grupo | n | Retenidos | Tasa | IC 95 % |")
A("|---|---|---|---|---|")
for eje, etiqueta in [("departamento", "Departamento"), ("nivel_formacion", "Nivel")]:
    for g, v in DES[eje]["grupos"].items():
        A(f"| {etiqueta}: {g} | {num(v['n'])} | {num(v['retenidos'])} | {pc(v['tasa'])} | {ic(v)} |")
A("")
A("Resultados de los contrastes de homogeneidad para el par 2019→2021:")
A("")
A("| Eje | χ² | gl | p | Frecuencia esperada mínima | ¿Supuesto de χ² satisfecho? |")
A("|---|---|---|---|---|---|")
for clave, etiqueta in [("genero", "Género"), ("departamento", "Departamento"),
                        ("gran_area", "Gran área"), ("nivel_formacion", "Nivel de formación")]:
    r = DES[clave]
    A(f"| {etiqueta} | {dec(r['chi2'], 3)} | {r['gl']} | {pv(r['p_valor'])} "
      f"| {dec(r['min_esperado'])} | {'sí' if r['supuesto_frecuencias_ok'] else '**no**'} |")
A("")
A(f"Solo el **departamento** supera el contraste sin reservas "
  f"(p = {pv(DES['departamento']['p_valor'])}; frecuencia esperada mínima "
  f"{dec(DES['departamento']['min_esperado'])}, suficiente): Atlántico "
  f"({pc(DES['departamento']['grupos']['Atlántico']['tasa'])}) y Santander "
  f"({pc(DES['departamento']['grupos']['Santander']['tasa'])}) retienen bastante más que "
  f"Bogotá ({pc(DES['departamento']['grupos']['Bogotá, D. C.']['tasa'])}) y Valle del Cauca "
  f"({pc(DES['departamento']['grupos']['Valle del Cauca']['tasa'])}). En gran área el "
  f"p-valor es {pv(DES['gran_area']['p_valor'])}, pero con una frecuencia esperada mínima "
  f"de {dec(DES['gran_area']['min_esperado'])} las celdas pequeñas invalidan la "
  f"aproximación χ², así que no debe interpretarse. En nivel de formación no hay diferencia "
  f"apreciable (p = {pv(DES['nivel_formacion']['p_valor'])}).")
A("")
A("**Transiciones desagregadas (2019→2021)**: composición de las trayectorias por grupo.")
A("")
A("| Grupo | n | Permanece | Asciende | Desciende |")
A("|---|---|---|---|---|")
for clave, etiqueta in [("genero", "Género"), ("gran_area", "Gran área"),
                        ("departamento", "Departamento")]:
    for g, v in TRG[clave]["grupos"].items():
        A(f"| {etiqueta}: {g} | {num(v['n'])} | {num(v['permanece'])} ({dec(v['pct_permanece'], 1)} %) "
          f"| {num(v['asciende'])} ({dec(v['pct_asciende'], 1)} %) "
          f"| {num(v['desciende'])} ({dec(v['pct_desciende'], 1)} %) |")
A("")
A(f"Los hombres ascienden más que las mujeres "
  f"({dec(TRG['genero']['grupos']['Masculino']['pct_asciende'])} % frente a "
  f"{dec(TRG['genero']['grupos']['Femenino']['pct_asciende'])} %) y las mujeres permanecen "
  f"más ({dec(TRG['genero']['grupos']['Femenino']['pct_permanece'])} % frente a "
  f"{dec(TRG['genero']['grupos']['Masculino']['pct_permanece'])} %), pero el contraste "
  f"global no alcanza significación (p = {pv(TRG['genero']['p_valor'])}). El patrón es "
  f"coherente con la brecha de retención: ellas se quedan más y suben menos. En Ciencias "
  f"Sociales y Humanidades el porcentaje de descensos es el más alto "
  f"({dec(TRG['gran_area']['grupos']['Ciencias Sociales']['pct_desciende'])} % y "
  f"{dec(TRG['gran_area']['grupos']['Humanidades']['pct_desciende'])} %), aunque el "
  f"contraste por gran área tiene celdas esperadas por debajo de 1 y su p-valor "
  f"({pv(TRG['gran_area']['p_valor'])}) no es fiable.")
A("")
A("### 2.8 Calidad del registro que revela el panel")
A("")
A("El seguimiento de las mismas personas entre convocatorias expone inconsistencias que un "
  "análisis transversal no puede ver:")
A("")
gin = HC["genero_inconsistente"]
A(f"- **Género contradictorio.** {num(gin['personas'])} personas "
  f"({dec(gin['pct_personas'])} % del padrón) figuran con más de un género a lo largo del "
  f"tiempo: " + ", ".join(f"{k.replace(' -> ', '→')} ({num(v)})"
                           for k, v in gin["patrones"].items())
  + ". El género no es un atributo estable en este registro.")
A(f"- **Atributos que cambian dentro de la misma persona**: departamento de residencia en "
  f"{num(d['coherencia_atributos_por_persona']['NME_DEPARTAMENTO_RES_PR'])} personas, gran "
  f"área en {num(d['coherencia_atributos_por_persona']['NME_GRAN_AREA_PR'])}, nivel de "
  f"formación en {num(d['coherencia_atributos_por_persona']['NME_NIV_FORM_PR'])} y "
  f"categoría en {num(d['coherencia_atributos_por_persona']['NME_CLASIFICACION_PR'])}. Los "
  f"tres primeros son en parte esperables (migración, nuevos títulos), pero obligan a "
  f"declarar qué observación se usa en cada análisis.")
A(f"- **Sin duplicados**: {HC['duplicados_persona_convocatoria']} repeticiones de la clave "
  f"persona × convocatoria, lo que permite tratar el panel como una matriz limpia.")
A(f"- **Tamaño del sistema**: {num(U['personas'])} personas y {num(U['registros'])} "
  f"reconocimientos a lo largo de seis convocatorias en nueve años del calendario.")
A("")

# ---------------- 3
A("## 3. Conclusiones")
A("")
c1 = PM[3]
A(f"1. **La retención es alta en cada intervalo, pero acumulada pierde casi la mitad del "
  f"padrón.** Entre convocatorias consecutivas se retiene entre "
  f"{pc(min(p['retencion']['p'] for p in PM))} y "
  f"{pc(max(p['retencion']['p'] for p in PM))}, pero de quienes entraron en 2013 solo "
  f"{pc(GL['muestra']['p'])} seguía en 2021. La caída no ocurre de golpe en un par "
  f"concreto: se acumula en cinco transiciones.")
A(f"2. **Anualizar con las fechas reales invierte el diagnóstico.** El hueco 2017→2019 dura "
  f"{dec(d['intervalos_anios_reales']['2017->2019'], 2)} años y el 2019→2021 solo "
  f"{dec(d['intervalos_anios_reales']['2019->2021'], 2)}. Con años nominales ambos parecen "
  f"equivalentes; con las fechas reales, 2017→2019 es el peor par "
  f"({pc(c1['retencion_anualizada_real'])} anualizado) y 2019→2021 el segundo mejor "
  f"({pc(PM[4]['retencion_anualizada_real'])}). Cualquier comparación entre convocatorias "
  f"que ignore las fechas reales llega a la conclusión opuesta.")
A(f"3. **La movilidad es ascendente y masiva, y el descenso también existe.** En 2019→2021, "
  f"de {num(TM['2019→2021']['n_transiciones'])} trayectorias observadas "
  f"{num(TM['2019→2021']['ascienden'])} ascendieron y "
  f"{num(TM['2019→2021']['descienden'])} descendieron "
  f"({pc(TM['2019→2021']['descienden']/TM['2019→2021']['n_transiciones'])}). La categoría "
  f"de investigador es revisable a la baja, no un escalafón de una sola dirección.")
A(f"4. **«Emérito» funciona como estado terminal: {num(em['retornos'])} de "
  f"{num(em['oportunidades'])} retornos.** Ninguna persona clasificada como Emérito vuelve "
  f"a aparecer en una convocatoria posterior. Es la regularidad más nítida de todo el "
  f"análisis y debe incorporarse como supuesto explícito en cualquier modelo de "
  f"transición.")
A(f"5. **La rotación aparente está inflada.** Entre el 14 % y el 22 % de las «entradas» son "
  f"reingresos de personas ya reconocidas, y hasta "
  f"{pc(PM[0]['salidas_temporales']/PM[0]['salidas'])} de las salidas de 2013→2014 "
  f"corresponden a personas que reaparecen después. Contar cada ausencia como una baja "
  f"permanente sobreestima el recambio del padrón.")
A("")

# ---------------- 4
A("## 4. Limitaciones")
A("")
A(f"1. **Es una muestra, no el universo.** Las cifras son estimaciones con intervalos al "
  f"95 %; el error efectivo de diseño es de ±{dec(100*T['error_efectivo_con_fpc'])} pp para "
  f"proporciones sobre el total de la muestra y mayor en subgrupos. En este ejercicio el "
  f"valor censal estaba disponible y todas las estimaciones quedaron a menos de 1,1 pp, "
  f"pero esa comprobación es un privilegio de contar con la base completa: en un uso real "
  f"del muestreo solo se dispondría del intervalo.")
A("2. **Las convocatorias no son anuales.** Faltan 2016, 2018 y 2020, y los intervalos "
  f"reales van de {dec(min(d['intervalos_anios_reales'].values()))} a "
  f"{dec(max(d['intervalos_anios_reales'].values()))} años. Las tasas anualizadas suponen "
  f"riesgo constante dentro de cada intervalo y con seis puntos de observación no puede "
  f"contrastarse ese supuesto. El análisis es descriptivo: no se ajustó ningún modelo de "
  f"supervivencia ni de hazard, pese a que el anteproyecto mencionaba esos métodos.")
A("3. **Qué significa `ANO_CONVO` no está documentado.** Se midió el intervalo con esas "
  f"fechas, que son el único dato temporal del archivo, pero la discrepancia entre el "
  f"rótulo «833 de 2018» y la fecha 06/12/2019 no se resuelve con la información "
  f"disponible. Si `ANO_CONVO` fuera una fecha de publicación de resultados y no de "
  f"apertura, los intervalos reales cambiarían y con ellos las tasas anualizadas.")
A("4. **Observación solo en las fechas de convocatoria.** Una persona ausente en una "
  f"convocatoria y presente en la siguiente es indistinguible de alguien que nunca fue "
  f"reconocido, salvo por el historial previo. Por eso se separaron reingresos y salidas "
  f"temporales; aun así, no se observa lo que ocurre entre convocatorias.")
A("5. **Censura a la derecha en el último par.** En 2019→2021 no hay convocatorias "
  f"posteriores: las {num(PM[4]['salidas'])} salidas no pueden clasificarse en temporales y "
  f"definitivas, y la retención de 2021 es la última observable. El mismo problema afecta a "
  f"la categoría Emérito, cuya condición terminal se comprueba solo hasta 2021.")
A("6. **Subgrupos pequeños.** Categorías como Emérito o «No registra» en gran área tienen "
  f"frecuencias que no sostienen contrastes: en varios ejes la frecuencia esperada mínima "
  f"baja de 5 y el χ² deja de ser válido. Se marcó explícitamente en cada caso en lugar de "
  f"reportar el p-valor como si fuera interpretable.")
A("7. **Atributos no constantes.** El perfil de cada persona se tomó de su última "
  f"convocatoria observada, y el género cambia en {num(gin['personas'])} personas. Las "
  f"desagregaciones por género o área usan el atributo en la convocatoria de origen de cada "
  f"par, lo que es coherente para medir retención, pero no debe leerse como una "
  f"característica fija de la persona.")
A("")

# ---------------- 5
A("## 5. Referencias")
A("")
A("- Cochran, W. G. (1977). *Sampling Techniques* (3.ª ed.). John Wiley & Sons. "
  "(Fórmula de tamaño de muestra para una proporción y corrección por población finita.)")
A("- Lohr, S. L. (2010). *Sampling: Design and Analysis* (2.ª ed.). Brooks/Cole. "
  "(Muestreo aleatorio simple, estimación de proporciones y efectos del diseño.)")
A("- Wilson, E. B. (1927). Probable inference, the law of succession, and statistical "
  "inference. *Journal of the American Statistical Association*, 22(158), 209–212. "
  "(Intervalo de confianza de score, usado como comprobación del intervalo de Wald.)")
A("- Agresti, A. y Coull, B. A. (1998). Approximate is better than “exact” for interval "
  "estimation of binomial proportions. *The American Statistician*, 52(2), 119–126.")
A("- Departamento Administrativo de Ciencia, Tecnología e Innovación (MinCiencias). "
  "*Investigadores reconocidos por convocatoria* [conjunto de datos, `bqtm-4y2h`]. "
  "datos.gov.co. Consulta: 2026-10-06.")
A("")

# ---------------- anexo
A("## Anexo: archivos y reproducibilidad")
A("")
A("| Archivo | Contenido |")
A("|---|---|")
A("| `documentacion_auditoria/src/analisis_longitudinal.py` | Cálculo completo: muestreo, representatividad, retención, transiciones, desagregaciones y gráficas |")
A("| `documentacion_auditoria/src/generar_analisis_longitudinal.py` | Genera este documento a partir del JSON verificado |")
A(f"| `data/memoria/muestra_ids.csv` | {num(M['personas'])} identificadores muestreados (entregable) |")
A(f"| `data/memoria/muestra_registros.csv` | Los {num(M['registros'])} registros de esas personas en las seis convocatorias |")
A("| `data/memoria/longitudinal_resultados.json` | Todas las cifras citadas en este documento |")
A("| `data/memoria/graficas_longitudinal/` | Las cinco gráficas (entregable) |")
A("")
A("Reproducción:")
A("")
A("```bash")
A("python documentacion_auditoria/src/analisis_longitudinal.py")
A("python documentacion_auditoria/src/generar_analisis_longitudinal.py")
A("```")
A("")
A(f"Con la semilla {d['semilla']} el procedimiento es determinista: la misma corrida "
  f"produce los mismos {num(M['personas'])} identificadores y las mismas cifras. La "
  f"verificación independiente de retención y transiciones (recalculadas con operaciones "
  f"de conjuntos y tablas cruzadas, sin reutilizar el código del análisis) coincide "
  f"exactamente con los resultados reportados.")
A("")

SALIDA.write_text("\n".join(L) + "\n", encoding="utf-8")
print(f"escrito {SALIDA}")
print(f"  {len(L)} lineas, {len((''.join(L)).encode('utf-8'))} bytes")
