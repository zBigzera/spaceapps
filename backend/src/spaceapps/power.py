from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from spaceapps.regions import Region

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETERS = [
    "PRECTOTCORR",
    "GWETTOP",
    "GWETROOT",
    "T2M",
    "EVPTRNS",
    "RH2M",
]
FILL_VALUE = -999.0
LATENT_HEAT_MJ_PER_KG = 2.45


def cache_path(region: Region, start: str, end: str, cache_dir: Path) -> Path:
    start_tag = start.replace("-", "")
    end_tag = end.replace("-", "")
    lat = f"{region.latitude:.2f}"
    lon = f"{region.longitude:.2f}"
    return cache_dir / f"power_{region.slug}_{lat}_{lon}_{start_tag}_{end_tag}.csv"


def _request_power(region: Region, start: str, end: str) -> pd.DataFrame:
    query = urllib.parse.urlencode(
        {
            "parameters": ",".join(PARAMETERS),
            "community": "AG",
            "longitude": f"{region.longitude:.4f}",
            "latitude": f"{region.latitude:.4f}",
            "start": start.replace("-", ""),
            "end": end.replace("-", ""),
            "format": "JSON",
        }
    )
    url = f"{POWER_URL}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "spaceapps-trend-detective/0.1"})
    with urllib.request.urlopen(request, timeout=180) as response:
        payload = json.loads(response.read().decode("utf-8"))

    params = payload["properties"]["parameter"]
    series: dict[str, pd.Series] = {}
    for name, values in params.items():
        parsed = pd.Series({pd.to_datetime(k): v for k, v in values.items()}, name=name)
        parsed = parsed.where(parsed != FILL_VALUE)
        series[name] = parsed

    df = pd.concat(series.values(), axis=1).sort_index()
    df.index.name = "date"
    return df.rename(
        columns={
            "PRECTOTCORR": "precip_mm",
            "GWETTOP": "soil_surface",
            "GWETROOT": "soil_root",
            "T2M": "temp_c",
            "EVPTRNS": "et_mj",
            "RH2M": "rh_pct",
        }
    )


def _year_windows(start: str, end: str) -> list[tuple[str, str]]:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    windows: list[tuple[str, str]] = []
    cursor = start_ts
    while cursor <= end_ts:
        year_end = min(pd.Timestamp(year=cursor.year, month=12, day=31), end_ts)
        windows.append((cursor.strftime("%Y-%m-%d"), year_end.strftime("%Y-%m-%d")))
        cursor = year_end + pd.Timedelta(days=1)
    return windows


def fetch_nasa_power(region: Region, start: str, end: str, cache_dir: Path) -> pd.DataFrame:
    """Baixa série diária pontual da NASA POWER (MERRA-2), com cache local."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_path(region, start, end, cache_dir)
    if cached.exists():
        print(f"Using NASA POWER cache: {cached}")
        df = pd.read_csv(cached, parse_dates=["date"], index_col="date")
        return df.sort_index()

    print(f"Requesting NASA POWER (MERRA-2) for {region.name}")
    print(f"    {start} to {end} | point ({region.latitude}, {region.longitude})")

    frames = []
    for window_start, window_end in _year_windows(start, end):
        print(f"    {window_start} to {window_end}")
        frames.append(_request_power(region, window_start, window_end))

    df = pd.concat(frames).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    df["et_mm"] = df["et_mj"] / LATENT_HEAT_MJ_PER_KG
    df["soil_surface_pct"] = df["soil_surface"] * 100.0
    df["soil_root_pct"] = df["soil_root"] * 100.0
    df["precip_mm"] = df["precip_mm"].clip(lower=0)
    df.to_csv(cached)
    print(f"Saved {len(df)} days to {cached}")
    return df
