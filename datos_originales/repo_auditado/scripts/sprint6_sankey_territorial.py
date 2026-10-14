"""
Sprint 6 — Sankey territorial: residencia del investigador → departamento de
la institución.

Materializa el flujo que pidió el director: "los de Vichada estudian en Meta
o Bogotá; eso tiene que verse claramente". El Sankey muestra de dónde sale
cada investigador y hacia qué departamento se afilia.

Salidas:
    artifacts/sprint6_sankey/sankey_territorial.html  (interactivo)
    artifacts/sprint6_sankey/sankey_territorial.png   (estático)

Uso:
    python scripts/sprint6_sankey_territorial.py
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import plotly.graph_objects as go

ARTIFACTS = ROOT / "artifacts" / "sprint6_sankey"
EVIDENCIAS = ROOT / "evidencias"
ARTIFACTS.mkdir(parents=True, exist_ok=True)


# Paleta consistente con la presentación
PALETA = [
    "#1f6feb", "#5b8def", "#f4a261", "#2a9d8f", "#9b5de5",
    "#cf625c", "#3a7ca5", "#f6c453", "#4caf50", "#c084fc",
    "#0ea5e9", "#fb923c", "#10b981", "#a78bfa", "#f87171",
]


def construir_sankey(flujo: pd.DataFrame,
                       top_res: int = 12,
                       top_inst: int = 10,
                       umbral_min: int = 15) -> go.Figure:
    """
    Sankey con los flujos más significativos.

    Para no saturar la figura:
    - Solo top_res departamentos de residencia (por volumen total)
    - Solo top_inst departamentos de institución
    - Solo flujos con n_investigadores >= umbral_min
    """
    top_residencias = (flujo.groupby("DPTO_RESIDENCIA")["n_investigadores"]
                            .sum().nlargest(top_res).index.tolist())
    top_instituciones = (flujo.groupby("DPTO_INSTITUCION")["n_investigadores"]
                              .sum().nlargest(top_inst).index.tolist())

    sub = flujo[flujo["DPTO_RESIDENCIA"].isin(top_residencias) &
                flujo["DPTO_INSTITUCION"].isin(top_instituciones) &
                (flujo["n_investigadores"] >= umbral_min)].copy()

    nodos_res = [f"{d} (res.)" for d in top_residencias]
    nodos_inst = [f"{d} (inst.)" for d in top_instituciones]
    nodos = nodos_res + nodos_inst
    color_map_res = {d: PALETA[i % len(PALETA)] for i, d in enumerate(top_residencias)}
    color_nodes = [color_map_res.get(d, "#888") for d in top_residencias] + \
                  ["#cfd8e3"] * len(top_instituciones)

    sources, targets, values, link_colors = [], [], [], []
    for _, row in sub.iterrows():
        s_idx = top_residencias.index(row["DPTO_RESIDENCIA"])
        t_idx = len(top_residencias) + top_instituciones.index(row["DPTO_INSTITUCION"])
        sources.append(s_idx)
        targets.append(t_idx)
        values.append(int(row["n_investigadores"]))
        link_colors.append(_rgba(color_map_res[row["DPTO_RESIDENCIA"]],
                                 alpha=0.40 if row["DPTO_RESIDENCIA"] == row["DPTO_INSTITUCION"]
                                              else 0.65))

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            label=nodos,
            color=color_nodes,
            pad=14,
            thickness=18,
            line=dict(color="white", width=0.6),
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            hovertemplate="%{source.label} → %{target.label}<br>"
                          "<b>%{value:,}</b> investigadores<extra></extra>",
        ),
    ))

    fig.update_layout(
        title=dict(
            text=f"Flujos residencia → institución (top {top_res} × top {top_inst}, "
                 f"≥ {umbral_min} investigadores)",
            font=dict(size=15),
        ),
        font=dict(family="Inter, sans-serif", size=12),
        margin=dict(l=20, r=20, t=60, b=20),
        height=620,
    )
    return fig


def _rgba(hex_color: str, alpha: float = 0.5) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def main() -> None:
    print("[1/2] Cargando flujos geográficos...")
    flujo = pd.read_csv(EVIDENCIAS / "geografia_flujo_completo.csv")
    print(f"      Pares unicos: {len(flujo):,}")

    print("\n[2/2] Construyendo Sankey territorial...")
    fig = construir_sankey(flujo, top_res=12, top_inst=10, umbral_min=15)
    fig.write_html(ARTIFACTS / "sankey_territorial.html",
                    include_plotlyjs="cdn",
                    full_html=True)
    fig.write_image(ARTIFACTS / "sankey_territorial.png",
                     width=1200, height=620, scale=2)
    print(f"      {ARTIFACTS / 'sankey_territorial.html'}")
    print(f"      {ARTIFACTS / 'sankey_territorial.png'}")


if __name__ == "__main__":
    main()
