from __future__ import annotations

import math
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from spaceapps.analysis import add_hydrology_features, analyze
from spaceapps.power import fetch_nasa_power
from spaceapps.regions import REGIONS, Region, get_region
from spaceapps.validation import compare_events, estimate_signals

ROOT = Path(__file__).resolve().parents[3]
CACHE_DIR = ROOT / "data" / "cache"

app = FastAPI(
    title="Earth System Trend Detective API",
    description="API REST full JSON para diagnóstico de risco composto de enchente e tendências ambientais.",
    version="1.1.1",
)

# Habilita CORS para o front-end em JS / HTML puro
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def clean_nan(obj: Any) -> Any:
    """Substitui recursivamente valores NaN ou Inf por None (null no JSON)."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    return obj


@app.get("/api/regions")
def list_regions():
    """Retorna as regiões/bacias pré-definidas disponíveis no projeto[cite: 7]."""
    return {
        slug: {
            "name": r.name,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "description": r.description,
        }
        for slug, r in REGIONS.items()
    }


@app.get("/api/detective")
def run_detective(
    region: str = Query("uba", description="Slug da região predefinida (ex: uba, petropolis)[cite: 7]"),
    lat: Optional[float] = Query(None, description="Latitude opcional para ponto personalizado"),
    lon: Optional[float] = Query(None, description="Longitude opcional para ponto personalizado"),
    name: Optional[str] = Query(None, description="Nome opcional para ponto personalizado"),
    start: str = Query("2026-01-01", description="Data inicial no formato YYYY-MM-DD"),
    end: str = Query(default_factory=lambda: date.today().isoformat(), description="Data final no formato YYYY-MM-DD"),
):
    """Executa o pipeline completo da NASA POWER e retorna dados diários e análises em JSON[cite: 2, 5]."""
    try:
        if lat is not None and lon is not None:
            reg = Region(
                slug="custom",
                name=name if name else f"Ponto ({lat:.2f}, {lon:.2f})",
                latitude=lat,
                longitude=lon,
                description="Ponto personalizado definido via parâmetros da API.",
            )
        else:
            if region not in REGIONS:
                raise ValueError("Unknown region. Choose a listed region.")
            reg = get_region(region)

        if (lat is None) != (lon is None):
            raise ValueError("Provide both latitude and longitude.")
        if not -90 <= reg.latitude <= 90 or not -180 <= reg.longitude <= 180:
            raise ValueError("Coordinates are outside the valid range.")
        if date.fromisoformat(start) > date.fromisoformat(end):
            raise ValueError("Start date must be before end date.")
        if date.fromisoformat(end) > date.today():
            raise ValueError("Historical analysis cannot include future dates.")

        # 1. Busca dados da NASA POWER (com cache local)[cite: 5]
        raw = fetch_nasa_power(reg, start, end, CACHE_DIR)
        
        # 2. Adiciona recursos hidrológicos e executa análises[cite: 2]
        featured = add_hydrology_features(raw)
        report = analyze(raw)

        # 3. Serializa a série diária para o front-end
        timeseries = []
        for idx, row in featured.iterrows():
            timeseries.append({
                "date": idx.strftime("%Y-%m-%d"),
                **{key: float(row[key]) if pd.notna(row[key]) else None for key in (
                    "api", "precip_30d", "et_mm", "rain_contribution", "soil_contribution",
                    "api_contribution", "anomaly_contribution",
                )},
                "precip_mm": float(row.precip_mm) if pd.notna(row.precip_mm) else None,
                "precip_7d": float(row.precip_7d) if pd.notna(row.precip_7d) else None,
                "soil_surface_pct": float(row.soil_surface_pct) if pd.notna(row.soil_surface_pct) else None,
                "soil_root_pct": float(row.soil_root_pct) if pd.notna(row.soil_root_pct) else None,
                "flood_risk": float(row.flood_risk) if pd.notna(row.flood_risk) else None,
                "precip_anomaly": float(row.precip_anomaly) if pd.notna(row.precip_anomaly) else None,
                "compound_flood": bool(row.compound_flood),
                "alert": str(row.alert) if pd.notna(row.alert) else "baixo",
            })

        # 4. Formata os dias críticos
        critical_list = []
        if not report.critical_days.empty:
            for idx, row in report.critical_days.iterrows():
                critical_list.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "precip_mm": float(row.precip_mm),
                    "precip_7d": float(row.precip_7d),
                    "soil_root_pct": float(row.soil_root_pct),
                    "api": float(row.api),
                    "flood_risk": float(row.flood_risk),
                })

        # 5. Monta o payload e limpa eventuais NaNs remanescentes
        payload = {
            "estimated_signals": estimate_signals(featured),
            "validation": compare_events(featured, reg.slug, start, end),
            "trend_details": [asdict(t) for t in report.trends],
            "monthly_risk": [
                {"date": idx.strftime("%Y-%m-%d"), "value": float(value)}
                for idx, value in featured["flood_risk"].resample("MS").mean().items()
            ],
            "status": "success",
            "region": {
                "slug": reg.slug,
                "name": reg.name,
                "latitude": reg.latitude,
                "longitude": reg.longitude,
                "description": reg.description,
            },
            "period": {
                "start": report.start,
                "end": report.end,
                "n_days": report.n_days,
            },
            "n_compound_events": report.n_compound,
            "trends": [t.as_dict() for t in report.trends],
            "correlations": report.correlations,
            "critical_days": critical_list,
            "notes": report.notes,
            "timeseries": timeseries,
        }

        return clean_nan(payload)

    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/")
def frontend():
    return FileResponse(ROOT / "frontend" / "index.html")


app.mount("/assets", StaticFiles(directory=ROOT / "frontend" / "assets"), name="assets")


@app.get("/methodology")
def methodology():
    return FileResponse(ROOT / "frontend" / "methodology.html")
