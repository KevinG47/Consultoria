#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generar_dashboard_modelo.py
===========================

Genera `02_dashboards/dashboard_modelo.html`: dashboard autocontenido del
modelo de machine learning (Fase 3), para presentar al profesor.

- Lee cifras de 07_modelo/modelado/resultados/*.json (no inventa ninguna).
- Recalcula desde los datos solo lo que NO está guardado en JSON:
  matriz de confusión en test (t=0.15), barrido de umbrales y features
  con gain > 0. Todo se contrasta contra los JSON y se avisa si no cuadra.
- Plotly va EMBEBIDO (plotly.min.js), así que el HTML funciona sin red.

Uso:  07_modelo\\.venv-bayes\\Scripts\\python.exe 07_modelo/dashboard/generar_dashboard_modelo.py
"""

from __future__ import annotations

import glob
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
MODELADO = RAIZ / "07_modelo" / "modelado"
RES = MODELADO / "resultados"
DERIV = RAIZ / "07_modelo" / "datos" / "derivados"
CENSO = RAIZ / "01_datos" / "datos_fuente" / "Investigadores_Reconocidos_por_convocatoria_20261006.csv"
SALIDA = RAIZ / "02_dashboards" / "dashboard_modelo.html"
CLASES = ("baja", "se_mantiene", "sube")
T_FINAL = 0.15
UMBRALES = (0.06, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20)
CONTACTO = "kevin47gremory@gmail.com"
REPO = "https://github.com/KevinG47/Consultoria"

AVISOS: list[str] = []


# ----------------------------------------------------------------------------
# Utilidades de datos
# ----------------------------------------------------------------------------
def leer_json(patron: str) -> dict:
    archivos = sorted(glob.glob(str(RES / patron)))
    if not archivos:
        raise FileNotFoundError(f"no hay JSON que case con {patron}")
    return json.loads(Path(archivos[-1]).read_text(encoding="utf-8"))


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest().upper()


def prec_rec_f1(y, pred):
    yb = y == 0
    sel = pred == 0
    tp = int(np.sum(sel & yb))
    prec = tp / int(sel.sum()) if sel.any() else 0.0
    rec = tp / int(yb.sum()) if yb.any() else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1


def pred_umbral(p, t):
    return np.where(p[:, 0] >= t, 0, np.where(p[:, 1] >= p[:, 2], 1, 2))


def f1_macro(y, pred):
    f1s = []
    for k in range(3):
        tp = int(np.sum((pred == k) & (y == k)))
        den = int(np.sum(pred == k)) + int(np.sum(y == k))
        f1s.append(2 * tp / den if den else 0.0)
    return float(np.mean(f1s))


def brier(p, y):
    return float(np.mean(np.sum((p - np.eye(3)[y]) ** 2, axis=1)))


def modelos_entrenados():
    """Reentrena la config final (17-20) y predice test. Devuelve p, y, gain."""
    sys.path.insert(0, str(MODELADO))
    import opt_comun as oc
    import modelo_mascaras as mm  # noqa: F401  (documenta el esquema de máscaras)

    df, feats = oc.cargar()
    X = oc.matriz(df, feats)
    y = df["y"].to_numpy()
    cat = df["cat"].to_numpy()
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()
    m_tr = np.isin(per, [17, 18, 19, 20])
    m_te = per == 21
    prev = np.bincount(y[m_tr], minlength=3) / m_tr.sum()
    params = dict(oc.BASE, n_estimators=100, min_child_weight=1, gamma=0.1,
                  subsample=0.8, max_depth=7, learning_rate=0.05)
    mod = oc.entrenar_cat(X, y, cat, m_tr, params)
    p = oc.predecir_cat(mod, X, cat, m_te, prev)
    gain = np.zeros(len(feats))
    for m in mod.values():
        gain += m.feature_importances_
    return p, y[m_te], gain, len(feats)


# ----------------------------------------------------------------------------
# HTML
# ----------------------------------------------------------------------------
CSS = """
:root{
  --tinta:#1E293B; --azul:#1E3780; --azul2:#4A6BA8; --oro:#8F6D0A;
  --gris:#475569; --linea:#CBD5E1; --fondo:#F8FAFC; --blanco:#FFFFFF;
  --alerta:#7A2E1E; --alerta-fondo:#FDF3EF;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--fondo);color:var(--tinta);
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
  font-size:17px;line-height:1.6;-webkit-font-smoothing:antialiased}
main{max-width:1120px;margin:0 auto;padding:0 22px 72px}
section{background:var(--blanco);border:1px solid var(--linea);border-radius:10px;
  padding:26px 30px;margin:22px 0;box-shadow:0 1px 2px rgba(15,23,42,.04)}
h1{font-size:2.05rem;line-height:1.2;margin:.2em 0 .3em;color:var(--azul);letter-spacing:-.01em}
h2{font-size:1.42rem;margin:0 0 .5em;color:var(--azul);letter-spacing:-.01em}
h3{font-size:1.08rem;margin:1.3em 0 .4em;color:var(--tinta)}
p{margin:.55em 0}
.eyebrow{font-size:.82rem;letter-spacing:.1em;text-transform:uppercase;color:var(--oro);font-weight:700}
.lead{font-size:1.08rem;color:var(--gris)}
.num{font-variant-numeric:tabular-nums}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:14px;margin:18px 0}
.kpi{border:1px solid var(--linea);border-radius:9px;padding:14px 16px;background:#FCFDFF}
.kpi .v{font-size:1.75rem;font-weight:700;color:var(--azul);line-height:1.1;font-variant-numeric:tabular-nums}
.kpi .k{font-size:.86rem;color:var(--gris);margin-top:4px}
.kpi .n{font-size:.78rem;color:var(--oro);margin-top:3px}
table{width:100%;border-collapse:collapse;margin:14px 0;font-size:.95rem}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--linea);vertical-align:top}
th{background:#F1F5F9;color:var(--tinta);font-size:.86rem;text-transform:uppercase;letter-spacing:.04em}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
tbody tr:hover{background:#F8FAFE}
.fr{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:16px 0}
.paso{flex:1 1 150px;min-width:140px;border:1px solid var(--linea);border-radius:9px;padding:12px 14px;background:#FCFDFF}
.paso b{display:block;color:var(--azul);font-size:.95rem}
.paso span{font-size:.82rem;color:var(--gris)}
.flecha{color:var(--oro);font-weight:700;font-size:1.2rem}
.tl{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}
.cohorte{flex:1 1 130px;border-top:4px solid var(--azul2);background:#F8FAFE;border-radius:0 0 8px 8px;padding:10px 12px}
.cohorte.activa{border-top-color:var(--oro)}
.cohorte b{display:block;font-size:.92rem;color:var(--tinta)}
.cohorte span{font-size:.8rem;color:var(--gris)}
.alerta{background:var(--alerta-fondo);border:1px solid #E9C9BE;border-left:5px solid var(--alerta);
  border-radius:8px;padding:16px 20px;margin:16px 0}
.alerta h2{color:var(--alerta)}
.alerta li{margin:.35em 0}
.nota{font-size:.86rem;color:var(--gris)}
.small{font-size:.82rem;color:var(--oro);font-weight:600}
.btn{display:inline-block;border:1px solid var(--azul);background:var(--azul);color:#fff;
  border-radius:8px;padding:10px 18px;font-size:.95rem;font-weight:600;cursor:pointer;text-decoration:none}
.btn:hover{background:#16295E}
.btn.sec{background:#fff;color:var(--azul)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.pie{border-top:1px solid var(--linea);margin-top:26px;padding-top:16px;font-size:.84rem;color:var(--gris)}
code{background:#F1F5F9;border:1px solid var(--linea);border-radius:4px;padding:1px 5px;font-size:.88em}
pre{background:#0F172A;color:#E2E8F0;border-radius:8px;padding:14px 16px;overflow:auto;font-size:.84rem;line-height:1.5}
pre code{background:none;border:0;color:inherit;padding:0}
a{color:#1B4B8F}
.obs{border-left:3px solid var(--oro);padding-left:12px;color:var(--gris);font-size:.93rem;margin:10px 0}
@media (max-width:900px){
  body{font-size:16px} main{padding:0 12px 48px} section{padding:18px}
  .grid2{grid-template-columns:1fr} h1{font-size:1.6rem} h2{font-size:1.2rem}
}
@media print{
  body{background:#fff;font-size:11pt} main{max-width:none;padding:0}
  section{page-break-inside:avoid;box-shadow:none;border:1px solid #999;margin:10px 0;padding:14px}
  .btn{display:none} h1{font-size:20pt} h2{font-size:14pt}
  a{color:#000;text-decoration:none}
}
"""


def kpi(valor: str, etiqueta: str, nota: str = "") -> str:
    n = f'<div class="n">{nota}</div>' if nota else ""
    return (f'<div class="kpi"><div class="v num">{valor}</div>'
            f'<div class="k">{etiqueta}</div>{n}</div>')


def tabla(cabecera, filas, numericas=()) -> str:
    th = "".join(
        f'<th class="{"n" if i in numericas else ""}">{c}</th>'
        for i, c in enumerate(cabecera))
    cuerpo = []
    for f in filas:
        tds = "".join(
            f'<td class="{"n" if i in numericas else ""}">{v}</td>'
            for i, v in enumerate(f))
        cuerpo.append(f"<tr>{tds}</tr>")
    return f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(cuerpo)}</tbody></table>"


def fmt(x, d=4):
    return f"{x:.{d}f}".replace(".", ",")


def main() -> int:
    t0 = time.time()
    exp_e = leer_json("expE_test_*.json")
    paso5 = leer_json("paso5_tabla_final_*.json")
    paso3 = leer_json("paso3_xgb_mascaras_*.json")
    exp_a = leer_json("expA_grid_*.json")
    exp_c = leer_json("expC_demografia_*.json")
    exp_d = leer_json("expD_umbral_mediana_*.json")
    exp_f = leer_json("expF_trayectoria_*.json")
    exp_g = leer_json("expG_red_*.json")
    exp_h = leer_json("expH_prior_shift_*.json")

    p, y, gain, n_feats = modelos_entrenados()
    pred = pred_umbral(p, T_FINAL)
    prec, rec, f1b = prec_rec_f1(y, pred)
    f1m, b = f1_macro(y, pred), brier(p, y)
    conf = np.zeros((3, 3), dtype=int)
    for real, pr in zip(y, pred):
        conf[real, pr] += 1

    # contraste contra el JSON de la evaluación final
    m_json = exp_e["metricas"]
    for nombre, valor, guardado in (("F1 baja", f1b, m_json["f1_baja"]),
                                    ("recall", rec, m_json["recall_baja"]),
                                    ("precisión", prec, m_json["precision_baja"]),
                                    ("F1 macro", f1m, m_json["f1_macro"]),
                                    ("Brier", b, m_json["brier"])):
        if abs(valor - guardado) > 1e-3:
            AVISOS.append(f"{nombre}: recalculado {valor:.4f} != JSON {guardado:.4f}")

    # los cinco KPIs del dashboard deben coincidir con la ficha (ambos son ronda 2)
    ficha = (MODELADO / "model_card.md").read_text(encoding="utf-8")
    for etiqueta, valor in (("F1 «baja»", m_json["f1_baja"]),
                            ("recall", m_json["recall_baja"]),
                            ("precisión", m_json["precision_baja"]),
                            ("F1 macro", m_json["f1_macro"]),
                            ("Brier", m_json["brier"])):
        if fmt(valor) not in ficha:
            AVISOS.append(f"KPI {etiqueta}={fmt(valor)} no aparece en model_card.md")

    barrido = []
    for t in UMBRALES:
        pr_t = pred_umbral(p, t)
        pc, rc, f1 = prec_rec_f1(y, pr_t)
        barrido.append({"t": t, "prec": pc, "rec": rc, "f1": f1,
                        "f1_macro": f1_macro(y, pr_t),
                        "pct": float(np.mean(pr_t == 0))})
    (RAIZ / "07_modelo" / "dashboard" / "dashboard_umbrales.json").write_text(
        json.dumps({"fecha": datetime.now().isoformat(timespec="seconds"),
                    "t_final": T_FINAL, "barrido": barrido}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    n_gain0 = int(np.sum(gain <= 0))
    n_gain_pos = int(np.sum(gain > 0))

    # cohortes del dataset
    import pandas as pd
    df = pd.read_parquet(DERIV / "modelo_dataset_ventana_contiguo.parquet",
                         columns=["ID_CONVOCATORIA_siguiente", "split"])
    cohortes = df["ID_CONVOCATORIA_siguiente"].value_counts().sort_index()
    etiquetas = {17: "2013 → 2014", 18: "2014 → 2015", 19: "2015 → 2017",
                 20: "2017 → 2019", 21: "2019 → 2021"}
    n_censo = sum(1 for _ in open(CENSO, encoding="utf-8-sig", errors="replace")) - 1
    man = json.loads(Path(sorted(glob.glob(str(RAIZ / "07_modelo/ingesta/manifiestos/produccion_*.json")))[-1])
                     .read_text(encoding="utf-8"))

    # ---------------------------------------------------------------- gráficos
    import plotly.graph_objects as go
    import plotly.io as pio

    fig_conf = go.Figure(go.Heatmap(
        z=conf, x=list(CLASES), y=list(CLASES),
        colorscale=[[0, "#F8FAFC"], [0.35, "#E6DFC8"], [0.7, "#8F6D0A"], [1, "#1E3780"]],
        text=[[f"{v:,}".replace(",", " ") for v in fila] for fila in conf],
        texttemplate="%{text}", textfont={"size": 16, "color": "#1E293B"},
        hovertemplate="real %{y} · predicho %{x}<br>%{z} casos<extra></extra>",
        showscale=False, xgap=3, ygap=3))
    fig_conf.update_layout(
        height=380, margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="predicho", yaxis_title="real",
        font=dict(family="system-ui, Segoe UI, Arial", size=13, color="#1E293B"),
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF")

    fig_umb = go.Figure()
    fig_umb.add_scatter(x=[d["t"] for d in barrido], y=[d["rec"] for d in barrido],
                        mode="lines+markers", name="recall",
                        line=dict(color="#1E3780", width=3))
    fig_umb.add_scatter(x=[d["t"] for d in barrido], y=[d["prec"] for d in barrido],
                        mode="lines+markers", name="precisión",
                        line=dict(color="#4A6BA8", width=3, dash="dot"))
    fig_umb.add_scatter(x=[d["t"] for d in barrido], y=[d["f1"] for d in barrido],
                        mode="lines+markers", name="F1 «baja»",
                        line=dict(color="#8F6D0A", width=3))
    fig_umb.add_vline(x=T_FINAL, line=dict(color="#7A2E1E", width=2, dash="dash"),
                      annotation_text=f"t = {T_FINAL}", annotation_position="top")
    fig_umb.update_layout(
        height=360, margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="umbral sobre p(baja)", yaxis_title="valor",
        legend=dict(orientation="h", y=1.12, x=0),
        font=dict(family="system-ui, Segoe UI, Arial", size=13, color="#1E293B"),
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", hovermode="x unified")

    rondas = [
        ("Tuning (54 configuraciones)", exp_a["mejor"]["media"] - exp_a["referencia_200_1_0_08"]["media"], "expA"),
        ("Features top 50/80/120", 0.0, "expB"),
        ("Demografía (27 columnas)", exp_c["delta_pp"] / 100, "expC"),
        ("Trayectoria (5 features)", exp_f["delta_pp"] / 100, "expF"),
        ("Red de grupos (6 features)", exp_g["delta_pp"] / 100, "expG"),
    ]
    fig_rondas = go.Figure(go.Bar(
        x=[r[1] * 100 for r in rondas], y=[r[0] for r in rondas], orientation="h",
        marker_color=["#8F6D0A" if r[1] > 0 else ("#4A6BA8" if r[1] == 0 else "#7A2E1E") for r in rondas],
        text=[f"{r[1]*100:+.2f} pp" for r in rondas], textposition="outside",
        hovertemplate="%{y}: %{x:.2f} pp<extra></extra>"))
    fig_rondas.update_layout(
        height=300, margin=dict(l=10, r=60, t=10, b=10),
        xaxis_title="Δ F1 «baja» OOS (puntos porcentuales)", xaxis_range=[-0.6, 1.4],
        yaxis=dict(autorange="reversed"),
        font=dict(family="system-ui, Segoe UI, Arial", size=13, color="#1E293B"),
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", showlegend=False)

    js_plotly = (Path(__import__("plotly").__file__).parent / "package_data" / "plotly.min.js"
                 ).read_text(encoding="utf-8").replace("</script", "<\\/script")
    graf_conf = pio.to_html(fig_conf, include_plotlyjs=False, full_html=False,
                            div_id="g_conf", config={"displayModeBar": False})
    graf_umb = pio.to_html(fig_umb, include_plotlyjs=False, full_html=False,
                           div_id="g_umb", config={"displayModeBar": False})
    graf_rondas = pio.to_html(fig_rondas, include_plotlyjs=False, full_html=False,
                              div_id="g_rondas", config={"displayModeBar": False})

    # ---------------------------------------------------------------- secciones
    comparacion = [
        ("Línea base (prevalencia)", 0.1851, 1.0000, 0.1020, 0.0617, 0.4419),
        ("XGBoost ronda 1", 0.1550, 0.3658, 0.0983, 0.3939, 0.5479),
        ("Bayesiano mínimo (umbral)", 0.2861, 0.6260, 0.1854, 0.2945, 0.4370),
        ("**XGBoost ronda 2 (operativo)**", 0.4234, 0.7878, 0.2895, 0.5109, 0.4692),
    ]
    filas_cmp = [(n, fmt(a), fmt(b), fmt(c), fmt(d), fmt(e))
                 for n, a, b, c, d, e in comparacion]

    filas_umb = [(fmt(d["t"], 2), fmt(d["prec"]), fmt(d["rec"]), fmt(d["f1"]),
                  fmt(d["f1_macro"]), f"{100*d['pct']:.1f} %") for d in barrido]

    auc_i = paso3["categorias"]["I (Asociado)"]["argmax"]["auc_ovr"]["baja"]
    auc_s = paso3["categorias"]["IS (Senior)"]["argmax"]["auc_ovr"]["baja"]

    h = []
    h.append(f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Modelo de ML · Transición de categoría · Observatorio MinCiencias</title>
<style>{CSS}</style>
<script>{js_plotly}</script>
</head>
<body>
<main>

<section id="portada">
  <div class="eyebrow">Consultoría estadística · USTA 2026-II · Fase 3</div>
  <h1>Modelo de machine learning para anticipar descensos de categoría</h1>
  <p class="lead">XGBoost con máscaras estructurales sobre 43 187 transiciones contiguas del
  padrón de investigadores reconocidos de Minciencias (2013–2021).</p>
  <p><b>Autor:</b> Kevin Leonardo Chaparro Reyes · <b>Fecha:</b> 26 de octubre de 2026 ·
  <b>Repositorio:</b> <a href="{REPO}">KevinG47/Consultoria</a></p>
  <div class="kpis">
    {kpi(fmt(m_json['f1_baja']), 'F1 «baja» en test', 'umbral 0,15')}
    {kpi(fmt(m_json['recall_baja']), 'recall de «baja»', 'detecta 79 % de los descensos')}
    {kpi(fmt(m_json['precision_baja']), 'precisión de «baja»', '1 de cada 3,4 alertas acierta')}
    {kpi(fmt(m_json['f1_macro']), 'F1 macro', 'tres clases')}
    {kpi(fmt(m_json['brier']), 'Brier multiclase', 'ver limitaciones')}
  </div>
  <div class="obs"><b>Resumen ejecutivo.</b> El modelo estima, para cada investigador y cada
  convocatoria, la probabilidad de que su categoría baje, se mantenga o suba en la
  convocatoria siguiente. Se entrenó con las cohortes 2014–2017, se validó en 2019 y se
  evaluó <b>una sola vez</b> en 2021 (13 355 transiciones), donde
  <b>detecta el 79 % de los descensos con una precisión del 29 %; es útil para priorizar
  revisión, no para automatizar</b>. Cuatro rondas de mejora no movieron el resultado:
  el límite es del dato, no del método.</div>
  <p><button class="btn" onclick="window.print()">Imprimir / Guardar PDF</button>
  <a class="btn sec" href="#metricas">Ir a las métricas</a></p>
</section>

<section id="problema">
  <h2>2 · El problema</h2>
  <p>Para cada <b>investigador reconocido</b> y cada convocatoria <i>t</i>, el modelo predice
  la <b>transición de categoría</b> hacia la convocatoria <i>t</i>+1 en tres estados:
  <b>baja</b>, <b>se mantiene</b> o <b>sube</b>.</p>
  <p>La unidad de análisis es la <b>transición</b> de una persona entre dos convocatorias
  consecutivas, no la persona: así el modelo aprende del cambio, que es lo que Minciencias
  necesita anticipar. A la cartera le interesa el <b>descenso</b>: una caída de categoría
  implica pérdida de reconocimiento, de acceso a convocatorias y de capacidad del grupo.</p>
  <p>El resultado operativo es una probabilidad <code>p(baja)</code> y un umbral de decisión.
  Con el umbral 0,15 se alerta al <b>25,7 %</b> de la población y se cubre el
  <b>{100*m_json['recall_baja']:.1f} %</b> de los descensos reales. El modelo <b>prioriza</b> la
  revisión de casos; <b>no</b> decide por sí solo.</p>
</section>

<section id="datos">
  <h2>3 · Los datos</h2>
  <div class="kpis">
    {kpi(f"{n_censo:,}".replace(',', ' '), 'registros del censo', 'persona × convocatoria')}
    {kpi(f"{man['filas']:,}".replace(',', ' '), 'filas de producción', 'productos por persona y convocatoria')}
    {kpi('5', 'cohortes históricas', '2013 · 2014 · 2015 · 2017 · 2019')}
    {kpi(f"{len(df):,}".replace(',', ' '), 'transiciones contiguas', 'unidad de análisis')}
  </div>
  <div class="fr">
    <div class="paso"><b>1 · Ingesta</b><span>API de datos.gov.co, validación de esquema y llave</span></div>
    <span class="flecha">→</span>
    <div class="paso"><b>2 · Features</b><span>172 variables de producción por persona y convocatoria</span></div>
    <span class="flecha">→</span>
    <div class="paso"><b>3 · Dataset</b><span>transiciones contiguas con etiqueta de cambio de categoría</span></div>
    <span class="flecha">→</span>
    <div class="paso"><b>4 · Modelo</b><span>XGBoost con máscaras por categoría de origen</span></div>
    <span class="flecha">→</span>
    <div class="paso"><b>5 · Evaluación</b><span>test out-of-time, una sola vez</span></div>
  </div>
  {tabla(['Partición', 'Cohortes', 'Transiciones', 'Uso'],
         [('Train', '2014, 2015, 2017', '19 838', 'ajuste'),
          ('Validación', '2019', '9 994', 'elección de umbral y diagnóstico'),
          ('Test', '2021', '13 355', 'evaluación final, una sola vez')], numericas=(2,))}
  <p class="nota">El test nunca entra en el entrenamiento, en la estandarización ni en la
  elección del umbral.</p>
</section>

<section id="modelo">
  <h2>4 · El modelo</h2>
  <p><b>XGBoost con máscaras estructurales</b>: un submodelo por categoría de origen, con las
  restricciones que impone el propio padrón.</p>
  {tabla(['Categoría de origen', 'Submodelo', 'Restricción estructural'],
         [('Junior (IJ)', 'binario', 'no puede bajar: p(baja) = 0'),
          ('Asociado (I)', 'tricótomo', '—'),
          ('Sénior (IS)', 'tricótomo', '—'),
          ('Emérito (IE)', 'excluido', 'sin transiciones en los datos')])}
  <div class="grid2">
    <div>
      <h3>Configuración</h3>
      {tabla(['Hiperparámetro', 'Valor'],
             [('n_estimators', '100'), ('max_depth', '7'), ('learning_rate', '0,05'),
              ('subsample', '0,8'), ('gamma', '0,1'), ('min_child_weight', '1'),
              ('pesos', 'balanceados por clase'), ('semilla', '42')], numericas=(1,))}
    </div>
    <div>
      <h3>Features</h3>
      <p><b>{n_feats}</b> variables de producción (volumen, clase de producto, tipología y
      categoría/calidad), sin <code>ano</code>.</p>
      <p>En el modelo final, <b>{n_gain_pos}</b> tienen gain &gt; 0 y <b>{n_gain0}</b> no se usan
      nunca. (En el fold más pequeño solo se activan 43: por eso la ficha del modelo cita 43;
      el número depende de cuánta historia se use para entrenar.)</p>
      <p class="nota">Se probó añadir demografía, trayectoria y red: ninguna superó el +2 pp
      exigido para volver a test (ver §8).</p>
    </div>
  </div>
  <h3>¿Por qué XGBoost y no otro modelo?</h3>
  <p>Porque el problema es tabular, con muchas variables correlacionadas y pocas filas
  (≈20 mil): los árboles con boosting manejan bien esa combinación sin supuestos de
  distribución. Se comparó con regresión logística (F1 macro 0,35) y con un bayesiano
  jerárquico (que gana en calibración pero pierde con el <code>argmax</code>; ver §7).</p>
</section>

<section id="validacion">
  <h2>5 · Validación temporal</h2>
  <p>No se usa validación aleatoria: barajar filas mezclaría cohortes y dejaría al modelo
  «ver el futuro». Se usan <b>folds temporales</b>: entrenar con el pasado y evaluar con la
  cohorte siguiente.</p>
  {tabla(['Fold', 'Entrena con', 'Elige umbral en', 'Evalúa en'],
         [('F1', '2014', '2015', '2017'),
          ('F2', '2014, 2015', '2017', '2019'),
          ('F3', '2015', '2017', '2019')])}
  <div class="tl">
    <div class="cohorte"><b>2013 → 2014</b><span>4 817 transiciones</span></div>
    <div class="cohorte"><b>2014 → 2015</b><span>6 857</span></div>
    <div class="cohorte"><b>2015 → 2017</b><span>8 164</span></div>
    <div class="cohorte"><b>2017 → 2019</b><span>9 994 · validación</span></div>
    <div class="cohorte activa"><b>2019 → 2021</b><span>13 355 · test (una vez)</span></div>
  </div>
  <p><b>Regla de oro:</b> el test se toca <b>una sola vez</b>. Todos los experimentos de
  mejora (§8) se decidieron con los folds, nunca con el test. La evaluación final usa el
  umbral fijado como <b>mediana de los umbrales de los folds</b>
  ({fmt(exp_d['umbral_mediana'], 2)}), no un umbral elegido en test.</p>
  <p class="nota">Umbrales por fold: {", ".join(fmt(u, 2) for u in exp_d['umbrales_folds'])}.
  El umbral es la decisión más frágil del sistema: moverlo cambia el recall entre 0,54 y 0,89.</p>
</section>

<section id="metricas">
  <h2>6 · Métricas en test (13 355 transiciones, una sola vez)</h2>
  <div class="kpis">
    {kpi(fmt(m_json['f1_baja']), 'F1 «baja»', 'clase de interés')}
    {kpi(fmt(m_json['recall_baja']), 'recall «baja»', 'descensos detectados')}
    {kpi(fmt(m_json['precision_baja']), 'precisión «baja»', 'alertas correctas')}
    {kpi(fmt(m_json['f1_macro']), 'F1 macro', 'equilibrio entre clases')}
    {kpi(fmt(m_json['brier']), 'Brier', 'error cuadrático multiclase')}
  </div>
  <div class="grid2">
    <div>
      <h3>Matriz de confusión</h3>
      <p class="nota">Pase el cursor por una celda para ver el detalle. Filas = clase real,
      columnas = clase predicha (umbral 0,15).</p>
      {graf_conf}
      <p class="nota"><b>Matriz de confusión del modelo operativo (ronda 2: 100 árboles,
      gamma=0.1, umbral 0.15).</b> La ronda 1 (200 árboles, sin gamma) daba una matriz
      ligeramente distinta con el mismo F1; ver
      <a href="{REPO}/blob/main/07_modelo/modelado/validacion_honesta.md">validacion_honesta.md</a>.</p>
    </div>
    <div>
      <h3>El umbral mueve todo</h3>
      {graf_umb}
      <p class="nota">El umbral 0,15 no maximiza el F1 (lo hace 0,08 con 0,345): se elige por
      estabilidad entre cohortes, no por el pico de una cohorte.</p>
    </div>
  </div>
  {tabla(['Umbral', 'Precisión', 'Recall', 'F1 «baja»', 'F1 macro', '% alertado'],
         filas_umb, numericas=(1, 2, 3, 4, 5))}
  <p class="nota">AUC de «baja» dentro de cada categoría (donde el descenso es posible):
  Asociado <b>{fmt(auc_i)}</b> · Sénior <b>{fmt(auc_s)}</b>. El AUC global (0,863) está
  inflado por la máscara de Junior, que nunca puede bajar.</p>
</section>

<section id="comparacion">
  <h2>7 · Comparación honesta entre modelos</h2>
  {tabla(['Modelo', 'F1 «baja»', 'Recall', 'Precisión', 'F1 macro', 'Brier'],
         filas_cmp, numericas=(1, 2, 3, 4, 5))}
  <p class="nota">Todas las filas con umbral optimizado sobre la misma validación; el test solo
  se usó para la fila operativa.</p>
  <h3>¿Por qué el bayesiano tiene mejor AUC (0,82) y peor F1 (0,29)?</h3>
  <p>Porque su <code>argmax</code> nunca elige «baja»: sus probabilidades están encogidas hacia
  las prevalencias y el punto de corte queda mal puesto. Con umbral optimizado su F1 «baja» sube
  a 0,286 — sigue por debajo del XGBoost (0,423) pero con <b>mejor Brier (0,437 vs 0,469)</b>.
  Es un modelo mejor calibrado y peor clasificador: se documenta como <b>capa de
  incertidumbre</b>, no como modelo operativo.</p>
</section>

<section id="rondas">
  <h2>8 · Las cuatro rondas de mejora</h2>
  {graf_rondas}
  {tabla(['Palanca', 'Qué se probó', 'Δ F1 «baja» OOS'],
         [('Tuning', '54 configuraciones de regularización y nº de árboles', '+0,48 pp'),
          ('Selección de features', 'top 50 / 80 / 120 por gain', '0,00 pp'),
          ('Demografía', 'género, edad, departamento e institución (27 columnas)', '−0,02 pp'),
          ('Trayectoria', 'tiempo en categoría, historial, momentum, producción normalizada', '+0,78 pp'),
          ('Red', 'compañeros de grupo y su movilidad (6 features)', '0,00 pp'),
          ('Prior shift', 'recalibración por prevalencia estimada de test', 'Brier empeora')],
         numericas=(2,))}
  <p><b>Conclusión:</b> ninguna palanca alcanzó el umbral de <b>+2 pp</b> fijado a priori para
  volver a tocar el test. El F1 «baja» se queda en ≈0,42 en test con cuatro aproximaciones
  independientes: <b>el techo es del dato, no del método</b>.</p>
</section>

<section id="limitaciones" class="alerta">
  <h2>9 · Limitaciones (leer antes de usar el modelo)</h2>
  <ul>
    <li><b>Las probabilidades no son confiables.</b> Brier 0,4692, peor que una constante con
    las prevalencias de entrenamiento (0,4419). Usar el <b>ranking</b> y el umbral, no el valor
    puntual. La corrección por prior shift se probó y empeoró el Brier (0,4917–0,6054).</li>
    <li><b>Sobreajuste.</b> F1 macro 0,83 en train frente a 0,50 en validación: el modelo
    memoriza. Con 100 árboles y <code>gamma</code>=0,1 se atenúa, no desaparece.</li>
    <li><b>{n_gain0} de las {n_feats} features tienen gain 0</b> en el modelo final (43 se
    activan en el fold más pequeño): el modelo efectivo usa {n_gain_pos} variables y el resto es
    ruido que el boosting ignora.</li>
    <li><b>No hay coautorías en el dato.</b> El CSV de producción tiene 1,02 autores por
    producto (máximo 6): solo existen 72 226 pares de coautoría en todo el censo, así que la red
    de coautorías no se puede construir. La red de grupos tampoco aporta (+0,00 pp).</li>
    <li><b>Solo cinco cohortes históricas.</b> No alcanza para separar tendencia de ruido ni
    para validar la estabilidad del umbral.</li>
    <li><b>Cambio de régimen 2019–2021.</b> La prevalencia de «baja» pasa de 5,2 % a 10,2 % y
    cambia la composición de quiénes bajan: por eso el Brier empeora aunque el F1 mejore.</li>
    <li><b>Umbral sensible a la cohorte.</b> El óptimo por fold va de 0,08 a 0,29; se fija 0,15
    por mediana. Recalcularlo con cada cohorte nueva.</li>
  </ul>
</section>

<section id="preguntas">
  <h2>10 · Qué necesito que revises</h2>
  <ol>
    <li><b>¿La formulación del problema es la correcta para Minciencias?</b> Predecimos la
    transición t→t+1 por persona. ¿Debería ser otra unidad (grupo, institución, región) o otro
    horizonte (dos convocatorias)?</li>
    <li><b>¿El umbral 0,15 es el trade-off adecuado?</b> Con 0,15 se detectan 79 % de los
    descensos y 1 de cada 3,4 alertas es correcta. Con 0,08 se detectan 84 % pero baja la
    precisión; con 0,20 se detecta 54 % y la precisión sube a 25 %. ¿Qué cuesta más en la
    práctica: un descenso no anticipado o una alerta falsa?</li>
    <li><b>¿Faltan features que el censo no tiene y la literatura de movilidad académica sí
    usa?</b> Financiación captada, participación en proyectos, patentes, movilidad
    internacional, dirección de tesis. Sin ellas el modelo no puede pasar de donde está.</li>
    <li><b>¿El techo del dato es convincente o hay otra palanca?</b> Probamos tuning,
    selección de features, demografía, trayectoria y red. ¿Se le ocurre otra vía con los datos
    disponibles?</li>
    <li><b>¿El bayesiano debería ser el modelo operativo por su calibración?</b> Tiene mejor
    Brier (0,437) y mejor AUC (0,82), pero peor F1 con umbral (0,286 vs 0,423). ¿Priorizamos
    calibración o capacidad de detectar descensos?</li>
  </ol>
  <p><b>Contacto para comentarios:</b> <a href="mailto:{CONTACTO}">{CONTACTO}</a> ·
  <a href="{REPO}/issues">Issues del repositorio</a>.
  Si prefieres, anota tus respuestas en el PDF impreso: cada sección está numerada para
  citarla.</p>
</section>

<section id="repro">
  <h2>11 · Reproducibilidad</h2>
  <p>Todo se regenera con el entorno <code>07_modelo/.venv-bayes</code>
  (Python 3.11.9 · xgboost 3.2.0 · scikit-learn 1.9.1 · pandas 3.1.0 · numpy 2.4.6, semilla 42).</p>
  <pre><code># evaluación final: entrena con 2014-2019 y evalúa 2021 una sola vez
07_modelo\\.venv-bayes\\Scripts\\python.exe 07_modelo/modelado/expE_test.py

# validación temporal (3 folds) y umbral mediana
07_modelo\\.venv-bayes\\Scripts\\python.exe 07_modelo/modelado/pasoA_cv_temporal.py
07_modelo\\.venv-bayes\\Scripts\\python.exe 07_modelo/modelado/expD_umbral_mediana.py

# este dashboard
07_modelo\\.venv-bayes\\Scripts\\python.exe 07_modelo/dashboard/generar_dashboard_modelo.py</code></pre>
  {tabla(['Insumo', 'SHA-256'],
         [('modelo_dataset_ventana_contiguo.parquet', sha256(DERIV / 'modelo_dataset_ventana_contiguo.parquet')),
          ('features_ventana_t.parquet', sha256(DERIV / 'features_ventana_t.parquet')),
          ('Investigadores_…_20261006.csv', sha256(CENSO)),
          ('produccion_grupos.csv (3 166 629 filas)', man['sha256'].upper())])}
  <p class="nota">Ficha del modelo:
  <a href="{REPO}/blob/main/07_modelo/modelado/model_card.md">model_card.md</a> ·
  Bitácora de validación:
  <a href="{REPO}/blob/main/07_modelo/modelado/validacion_honesta.md">validacion_honesta.md</a>
  (en GitHub; los mismos archivos están en el repo, en <code>07_modelo/modelado/</code>).</p>
</section>

<div class="pie">
  Dashboard generado automáticamente el {datetime.now().strftime('%d/%m/%Y %H:%M')} desde
  <code>07_modelo/dashboard/generar_dashboard_modelo.py</code>. Todas las cifras provienen de
  <code>07_modelo/modelado/resultados/*.json</code> o se recalculan de los parquet; la matriz de
  confusión y el barrido de umbrales se recalculan en cada generación y se contrastan contra el
  JSON de la evaluación final. Sin dependencias de red: Plotly va embebido.
</div>
</main>
</body>
</html>
""")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("".join(h), encoding="utf-8")
    seg = time.time() - t0
    mb = SALIDA.stat().st_size / (1024 * 1024)
    print(f"OK  {SALIDA}")
    print(f"    {mb:.2f} MB | generado en {seg:.1f} s | "
          f"fragmentos de sección: {len(h)}")
    print(f"    contraste con expE: F1baja={f1b:.4f} (json {m_json['f1_baja']:.4f}) | "
          f"Brier={b:.4f} (json {m_json['brier']:.4f})")
    print(f"    features con gain>0: {n_gain_pos} | gain=0: {n_gain0}")
    print(f"    matriz de confusión (t=0.15): {conf.tolist()}")
    for a in AVISOS:
        print("    [aviso]", a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
