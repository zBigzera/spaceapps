"""Compare historical index values with a curated, non-exhaustive event register."""
from __future__ import annotations

import pandas as pd

OFFICIAL_EVENTS = {
    "uba": [{
        "id": "uba-2026-02-23",
        "start": "2026-02-23",
        "end": "2026-02-24",
        "title": "Ubá flood · February 23–24, 2026",
        "source": "Ubá City Council · official municipal statement",
        "url": "https://www.uba.mg.leg.br/noticias/nota-oficial-2013-enchente-historica-em-uba-mg",
    }],
}


def estimate_signals(frame: pd.DataFrame) -> dict:
    """Exploratory daily proxies, never observations or confirmed event types.

    A high index plus rain marks a candidate. The wet-day 95th percentile
    splits extreme-rain candidates from other rainy high-index days. Daily
    totals cannot establish the rapid onset required to identify a flash flood.
    """
    wet_days = frame.loc[frame["precip_mm"].gt(0), "precip_mm"].dropna()
    threshold = float(wet_days.quantile(.95)) if not wet_days.empty else None
    candidates = frame.loc[frame["flood_risk"].ge(75) & frame["precip_mm"].gt(0)]
    events = []
    for idx, row in candidates.iterrows():
        events.append({
            "date": idx.strftime("%Y-%m-%d"),
            "kind": "flash_flood_proxy" if threshold is not None and row.precip_mm >= threshold else "flood_signal",
            "flood_risk": float(row.flood_risk),
            "precip_mm": float(row.precip_mm),
            "precip_7d": float(row.precip_7d) if pd.notna(row.precip_7d) else None,
        })
    return {"events": events, "risk_threshold": 75, "wet_day_p95_mm": threshold,
            "wet_day_count": len(wet_days), "confirmed": False}


def compare_events(frame: pd.DataFrame, region: str, start: str, end: str) -> dict:
    events = []
    for event in OFFICIAL_EVENTS.get(region, []):
        if event["end"] < start or event["start"] > end:
            continue
        window = frame.loc[event["start"]:event["end"], "flood_risk"].dropna()
        expected = pd.date_range(event["start"], event["end"])
        complete = bool(expected.isin(window.index).all())
        peak = float(window.max()) if not window.empty else None
        # A partial window can confirm a match, but cannot establish a miss.
        result = "matched" if peak is not None and peak >= 75 else "below_threshold" if complete else "insufficient_data"
        events.append({**event, "peak_index": peak, "result": result, "complete_window": complete})
    return {
        "threshold": 75,
        "rule": "At least one daily index ≥ 75 during the official event date range.",
        "catalog_complete": False,
        "events": events,
        "matched": sum(event["result"] == "matched" for event in events),
        "evaluated": sum(event["result"] != "insufficient_data" for event in events),
    }
