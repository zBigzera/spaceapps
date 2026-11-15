from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from spaceapps.analysis import DetectiveReport
from spaceapps.regions import Region

VARIABLE_GLOSSARY = [
    ("Precipitação (PRECTOTCORR)", "Chuva diária corrigida, NASA POWER / MERRA-2, em mm/dia. É o gatilho meteorológico da enchente."),
    ("Saturação superficial (GWETTOP)", "Umidade da camada 0–5 cm (0–1). Responde rápido à chuva; indica encharcamento raso e escoamento imediato."),
    ("Saturação radicular (GWETROOT)", "Umidade de 0–100 cm (0–1). Memória hídrica do solo: se já está alto, chuva nova vira escoamento."),
    ("Evapotranspiração (EVPTRNS)", "Energia usada para evaporar água. Convertida em mm para um balanço chuva − ET."),
    ("API", "Índice de precipitação antecedente: memória exponencial da chuva (k=0,85). Captura solo ‘já molhado’."),
    ("Índice de risco", "Combinação 0–100 de chuva em 7 dias, saturação do solo, API e anomalia mensal. Crítico ≥ 75."),
]


def _trend_table(report: DetectiveReport) -> go.Table:
    rows = [t.as_dict() for t in report.trends]
    frame = pd.DataFrame(rows)
    return go.Table(
        header=dict(values=list(frame.columns), fill_color="#0f172a", font=dict(color="white", size=12), align="left"),
        cells=dict(
            values=[frame[c] for c in frame.columns],
            fill_color="#1e293b",
            font=dict(color="#e2e8f0", size=11),
            align="left",
            height=28,
        ),
    )


def build_figures(df: pd.DataFrame, report: DetectiveReport, region: Region) -> list[go.Figure]:
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=(
            "Gatilho: chuva diária e acumulados (NASA POWER / MERRA-2)",
            "Resposta do terreno: saturação do solo",
            "Índice composto de risco de enchente",
            "Anomalia de chuva (ciclo sazonal removido)",
        ),
        specs=[[{"secondary_y": True}], [{}], [{}], [{}]],
    )

    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["precip_mm"],
            name="Chuva diária (mm)",
            marker_color="#38bdf8",
            hovertemplate="%{x|%d/%m/%Y}<br>Chuva: %{y:.1f} mm<extra></extra>",
        ),
        row=1,
        col=1,
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["precip_7d"],
            name="Acumulado 7 dias",
            line=dict(color="#fbbf24", width=2),
            hovertemplate="7 dias: %{y:.1f} mm<extra></extra>",
        ),
        row=1,
        col=1,
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["soil_surface_pct"],
            name="Solo 0–5 cm (%)",
            line=dict(color="#fb7185", width=1.6),
            hovertemplate="Superfície: %{y:.1f}%<extra></extra>",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["soil_root_pct"],
            name="Zona radicular 0–100 cm (%)",
            line=dict(color="#e11d48", width=2.4),
            hovertemplate="Raiz: %{y:.1f}%<extra></extra>",
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["flood_risk"],
            name="Índice de risco",
            line=dict(color="#c084fc", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(192,132,252,0.15)",
            hovertemplate="Risco: %{y:.1f}/100<extra></extra>",
        ),
        row=3,
        col=1,
    )
    fig.add_hline(y=75, line_dash="dash", line_color="#f87171", row=3, col=1)

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["precip_anomaly"],
            name="Anomalia de chuva",
            line=dict(color="#34d399", width=1.4),
            hovertemplate="Anomalia: %{y:.2f} mm<extra></extra>",
        ),
        row=4,
        col=1,
    )
    fig.add_hline(y=0, line_color="#64748b", row=4, col=1)

    compound = df[df["compound_flood"]]
    if not compound.empty:
        fig.add_trace(
            go.Scatter(
                x=compound.index,
                y=compound["flood_risk"],
                mode="markers",
                name="Dia composto (chuva + solo)",
                marker=dict(color="#facc15", size=8, symbol="diamond"),
                hovertemplate="Evento composto %{x|%d/%m/%Y}<extra></extra>",
            ),
            row=3,
            col=1,
        )

    fig.update_yaxes(title_text="mm/dia", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="mm / 7d", row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="Saturação (%)", range=[0, 100], row=2, col=1)
    fig.update_yaxes(title_text="Risco (0–100)", range=[0, 100], row=3, col=1)
    fig.update_yaxes(title_text="mm (anomalia)", row=4, col=1)
    fig.update_layout(
        title=f"<b>Earth System Trend Detective</b> — {region.name}<br><sup>NASA POWER / MERRA-2 · {report.start} a {report.end}</sup>",
        template="plotly_dark",
        height=1480,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, x=0),
        margin=dict(t=120, b=120),
    )

    scatter = go.Figure()
    scatter.add_trace(
        go.Scatter(
            x=df["precip_7d"],
            y=df["soil_root_pct"],
            mode="markers",
            marker=dict(
                size=6,
                color=df["flood_risk"],
                colorscale="Turbo",
                showscale=True,
                colorbar=dict(title="Risco"),
            ),
            text=df.index.strftime("%d/%m/%Y"),
            hovertemplate="%{text}<br>7d: %{x:.1f} mm<br>Solo: %{y:.1f}%<extra></extra>",
            name="Dias",
        )
    )
    scatter.update_layout(
        title="Céu × solo: acúmulo de 7 dias versus saturação da zona radicular",
        xaxis_title="Precipitação acumulada em 7 dias (mm)",
        yaxis_title="Saturação da zona radicular (%)",
        template="plotly_dark",
        height=480,
    )

    table_fig = go.Figure(_trend_table(report))
    table_fig.update_layout(
        title="O que muda, quanto muda, e se a mudança é significativa (OLS + Mann-Kendall)",
        template="plotly_dark",
        height=420,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return [fig, scatter, table_fig]


def write_dashboard(
    df: pd.DataFrame,
    report: DetectiveReport,
    region: Region,
    output_file: Path,
) -> Path:
    figures = build_figures(df, report, region)
    glossary = "".join(
        f"<li><strong>{name}:</strong> {text}</li>" for name, text in VARIABLE_GLOSSARY
    )
    trend_lines = "".join(
        f"<li><strong>{t.variable}:</strong> {t.slope_per_year:.4f} / ano · {t.mk_label} · "
        f"p(MK)={t.mk_p:.4f} · R²={t.r2:.3f}</li>"
        for t in report.trends
    )
    corr_lines = "".join(f"<li>{k}: {v:.2f}</li>" for k, v in report.correlations.items())
    top = report.critical_days.head(8)
    if top.empty:
        crit_html = "<p>Nenhum dia acima do limiar 75 no período.</p>"
    else:
        rows = "".join(
            "<tr>"
            f"<td>{idx.strftime('%d/%m/%Y')}</td>"
            f"<td>{row.precip_mm:.1f}</td>"
            f"<td>{row.precip_7d:.1f}</td>"
            f"<td>{row.soil_root_pct:.1f}</td>"
            f"<td>{row.flood_risk:.1f}</td>"
            "</tr>"
            for idx, row in top.iterrows()
        )
        crit_html = (
            "<table><thead><tr><th>Data</th><th>Chuva (mm)</th><th>7 dias (mm)</th>"
            "<th>Solo raiz (%)</th><th>Risco</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )

    parts = [
        "<!DOCTYPE html><html lang='pt-BR'><head><meta charset='utf-8'/>",
        "<title>Earth System Trend Detective</title>",
        "<style>",
        "body{font-family:Segoe UI,system-ui,sans-serif;background:#020617;color:#e2e8f0;margin:0;padding:24px;}",
        "h1,h2{color:#f8fafc;} a{color:#7dd3fc;} .card{background:#0f172a;border:1px solid #1e293b;border-radius:16px;padding:20px;margin:16px 0;}",
        "table{border-collapse:collapse;width:100%;} td,th{border-bottom:1px solid #334155;padding:8px;text-align:left;}",
        "li{margin:6px 0;} .muted{color:#94a3b8;}",
        "</style></head><body>",
        "<h1>Earth System Trend Detective</h1>",
        f"<p class='muted'>{region.name} · lat {region.latitude}, lon {region.longitude} · {report.start} a {report.end} · {report.n_days} dias</p>",
        f"<div class='card'><p>{region.description}</p>",
        "<h2>Os quatro pilares do desafio NASA</h2><ol>",
        f"<li><strong>O que</strong> está mudando: precipitação, saturação do solo, eventos compostos chuva+solo e o índice de risco.</li>",
        f"<li><strong>Onde</strong>: {region.name}.</li>",
        "<li><strong>Quanto</strong> (taxa linear anual) e <strong>se é significativo</strong> (OLS e Mann-Kendall, α=0,05):</li></ol>",
        f"<ul>{trend_lines}</ul></div>",
        f"<div class='card'><h2>Correlação céu × solo</h2><ul>{corr_lines}</ul>",
        f"<p>Dias compostos (chuva persistente sobre solo já úmido): <strong>{report.n_compound}</strong></p></div>",
        f"<div class='card'><h2>Dias críticos (risco ≥ 75)</h2>{crit_html}</div>",
        f"<div class='card'><h2>O que cada variável significa</h2><ul>{glossary}</ul></div>",
    ]
    html_bits = []
    for fig in figures:
        html_bits.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))
    notes = "".join(f"<li>{n}</li>" for n in report.notes)
    footer = (
        f"<div class='card'><h2>Limitações</h2><ul>{notes}</ul>"
        "<p class='muted'>Fonte: NASA POWER API (MERRA-2). Não substitui aviso oficial de defesa civil.</p></div>"
        "</body></html>"
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("".join(parts) + "".join(html_bits) + footer, encoding="utf-8")
    return output_file
