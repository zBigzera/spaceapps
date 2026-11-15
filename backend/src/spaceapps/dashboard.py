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
