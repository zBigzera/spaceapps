from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from spaceapps.analysis import DetectiveReport
from spaceapps.regions import Region

VARIABLE_GLOSSARY = [
    ("Precipitation (PRECTOTCORR)", "Bias-corrected daily precipitation, NASA POWER / MERRA-2, in mm/day. It is the meteorological trigger for flooding."),
    ("Surface soil saturation (GWETTOP)", "Moisture in the 0–5 cm layer (0–1). It responds quickly to rainfall and indicates shallow waterlogging and immediate runoff."),
    ("Root-zone soil saturation (GWETROOT)", "Moisture at 0–100 cm depth (0–1). It represents soil water memory: when already high, new rainfall is more likely to become runoff."),
    ("Evapotranspiração (EVPTRNS)", "Energy used to evaporate water. Converted to mm for to precipitation − ET water balance."),
    ("API", "Antecedent Precipitation Index: an exponential memory of rainfall (k=0.85). It captures whether the soil is already wet."),
    ("Risk index", "A 0–100 combination of 7-day rainfall, soil saturation, API, and monthly anomaly. Critical threshold ≥ 75."),
]


def _trend_table(report: DetectiveReport) -> go.Table:
    rows = [t.as_dict() for t in report.trends]
    frame = pd.DateFrame(rows)
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


def build_figures(df: pd.DateFrame, report: DetectiveReport, region: Region) -> list[go.Figure]:
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=(
            "Trigger: daily precipitation and cumulative totals (NASA POWER / MERRA-2)",
            "Land response: soil saturation",
            "Composite flood risk index",
            "Precipitation anomaly (seasonal cycle removed)",
        ),
        specs=[[{"secondary_y": True}], [{}], [{}], [{}]],
    )

    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["precip_mm"],
            name="Daily precipitation (mm)",
            marker_color="#38bdf8",
            hovertemplate="%{x|%d/%m/%Y}<br>Precipitation: %{y:.1f} mm<extra></extra>",
        ),
        row=1,
        col=1,
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["precip_7d"],
            name="7-day cumulative precipitation",
            line=dict(color="#fbbf24", width=2),
            hovertemplate="7 days: %{y:.1f} mm<extra></extra>",
        ),
        row=1,
        col=1,
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["soil_surface_pct"],
            name="Soil moisture 0–5 cm (%)",
            line=dict(color="#fb7185", width=1.6),
            hovertemplate="Surface: %{y:.1f}%<extra></extra>",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["soil_root_pct"],
            name="Root-zone moisture 0–100 cm (%)",
            line=dict(color="#e11d48", width=2.4),
            hovertemplate="Root zone: %{y:.1f}%<extra></extra>",
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["flood_risk"],
            name="Risk index",
            line=dict(color="#c084fc", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(192,132,252,0.15)",
            hovertemplate="Risk: %{y:.1f}/100<extra></extra>",
        ),
        row=3,
        col=1,
    )
    fig.add_hline(y=75, line_dash="dash", line_color="#f87171", row=3, col=1)

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["precip_anomaly"],
            name="Precipitation anomaly",
            line=dict(color="#34d399", width=1.4),
            hovertemplate="Anomaly: %{y:.2f} mm<extra></extra>",
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
                name="Compound event (precipitation + soil)",
                marker=dict(color="#facc15", size=8, symbol="diamond"),
                hovertemplate="Compound event %{x|%d/%m/%Y}<extra></extra>",
            ),
            row=3,
            col=1,
        )

    fig.update_yaxes(title_text="mm/day", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="mm / 7d", row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="Saturation (%)", range=[0, 100], row=2, col=1)
    fig.update_yaxes(title_text="Risk (0–100)", range=[0, 100], row=3, col=1)
    fig.update_yaxes(title_text="mm (anomaly)", row=4, col=1)
    fig.update_layout(
        title=f"<b>Earth System Trend Detective</b> — {region.name}<br><sup>NASA POWER / MERRA-2 · {report.start} to {report.end}</sup>",
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
                colorbar=dict(title="Risk"),
            ),
            text=df.index.strftime("%d/%m/%Y"),
            hovertemplate="%{text}<br>7d: %{x:.1f} mm<br>Soil: %{y:.1f}%<extra></extra>",
            name="Days",
        )
    )
    scatter.update_layout(
        title="Atmosphere × soil: 7-day cumulative precipitation versus root-zone saturation",
        xaxis_title="7-day cumulative precipitation (mm)",
        yaxis_title="Root-zone saturation (%)",
        template="plotly_dark",
        height=480,
    )

    table_fig = go.Figure(_trend_table(report))
    table_fig.update_layout(
        title="What is changing, by how much, and whether the change is significant (OLS + Mann-Kendall)",
        template="plotly_dark",
        height=420,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return [fig, scatter, table_fig]


def write_dashboard(
    df: pd.DateFrame,
    report: DetectiveReport,
    region: Region,
    output_file: Path,
) -> Path:
    figures = build_figures(df, report, region)
    glossary = "".join(
        f"<li><strong>{name}:</strong> {text}</li>" for name, text in VARIABLE_GLOSSARY
    )
    trend_lines = "".join(
        f"<li><strong>{t.variable}:</strong> {t.slope_per_year:.4f} / year · {t.mk_label} · "
        f"p(MK)={t.mk_p:.4f} · R²={t.r2:.3f}</li>"
        for t in report.trends
    )
    corr_lines = "".join(f"<li>{k}: {v:.2f}</li>" for k, v in report.correlations.items())
    top = report.critical_days.head(8)
    if top.empty:
        crit_html = "<p>No days exceeded the threshold of 75 during this period.</p>"
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
            "<table><thead><tr><th>Date</th><th>Precipitation (mm)</th><th>7 days (mm)</th>"
            "<th>Root-zone soil moisture (%)</th><th>Risk</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )

    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'/>",
        "<title>Earth System Trend Detective</title>",
        "<style>",
        "body{font-family:Segoe UI,system-ui,sans-serif;background:#020617;color:#e2e8f0;margin:0;padding:24px;}",
        "h1,h2{color:#f8fafc;} a{color:#7dd3fc;} .card{background:#0f172a;border:1px solid #1e293b;border-radius:16px;padding:20px;margin:16px 0;}",
        "table{border-collapse:collapse;width:100%;} td,th{border-bottom:1px solid #334155;padding:8px;text-align:left;}",
        "li{margin:6px 0;} .muted{color:#94a3b8;}",
        "</style></head><body>",
        "<h1>Earth System Trend Detective</h1>",
        f"<p class='muted'>{region.name} · lat {region.latitude}, lon {region.longitude} · {report.start} to {report.end} · {report.n_days} days</p>",
        f"<div class='card'><p>{region.description}</p>",
        "<h2>The four pillars of the NASA challenge</h2><ol>",
        f"<li><strong>What</strong> is changing: precipitation, soil saturation, compound precipitation + soil events, and the risk index.</li>",
        f"<li><strong>Where</strong>: {region.name}.</li>",
        "<li><strong>How much</strong> (annual linear rate) and <strong>whether it is significant</strong> (OLS and Mann-Kendall, α=0.05):</li></ol>",
        f"<ul>{trend_lines}</ul></div>",
        f"<div class='card'><h2>Atmosphere × soil correlation</h2><ul>{corr_lines}</ul>",
        f"<p>Compound events (persistent rainfall over already wet soil): <strong>{report.n_compound}</strong></p></div>",
        f"<div class='card'><h2>Critical days (risk ≥ 75)</h2>{crit_html}</div>",
        f"<div class='card'><h2>What each variable means</h2><ul>{glossary}</ul></div>",
    ]
    html_bits = []
    for fig in figures:
        html_bits.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))
    notes = "".join(f"<li>{n}</li>" for n in report.notes)
    footer = (
        f"<div class='card'><h2>Limitations</h2><ul>{notes}</ul>"
        "<p class='muted'>Source: NASA POWER API (MERRA-2). This does not replace official civil defense alerts.</p></div>"
        "</body></html>"
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("".join(parts) + "".join(html_bits) + footer, encoding="utf-8")
    return output_file
