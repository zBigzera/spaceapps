# Earth System Trend Detective

Tooling to investigate trends and flood risk through NASA Earht Data this software uses Ordinary Least Squares (OLS), Mann-Kendall, and trend analysis to investigate statistically significant environmental changes that may influence flood occurencies. It integrates NASA Earth science data to analyze long-term trends in precipitation, soil moisture, evapotranspiration, and atmospheric conditions. Rather than examining rainfall independently, the platform evaluates interactions between atmospheric water input and terrestrial water storage to identify changes in flood susceptibility. Historical data are retrieved through NASA POWER, primarily using MERRA-2 reanalysis. The application calculates accumulated rainfall, antecedent precipitation, soil wetness, and compound conditions involving heavy rainfall and elevated soil moisture. By integrating NASA Earth science data, hydrological indicators, and statistical methods, Earth Science Data Analysis transforms complex environmental datasets into accessible scientific information. The platform aims to support researchers, students, environmental professionals, and local decision-makers in understanding regional environmental changes and identifying conditions that may contribute to flood susceptibility.
## running locally

### Web application

Run from the repository root (Python 3.12+):

```bash
uv sync --project backend
uv run --project backend uvicorn spaceapps.api:app --app-dir backend/src --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. FastAPI serves both the frontend and `/api/detective` on the same origin; no separate frontend server is needed. The main page compares the daily risk index with sourced official flood dates. `/methodology` explains the formula, shows the contributing time series, and reports Mann–Kendall and OLS separately. Both pages are in English.

The curated official-event register currently contains the Ubá flood of February 23–24, 2026. It is not exhaustive. A comparison is a threshold check during the documented dates, not a model accuracy score. Add sourced records in `backend/src/spaceapps/validation.py`. Custom coordinates are not automatically matched to named-region events.

NASA data requests are cached in the repository's `data/cache/` directory, independent of the launch directory. The chart library and fonts require internet access. First-time NASA requests may take several minutes.

Run the event-comparison tests:

```bash
uv run --project backend python -m unittest discover -s backend/tests
```

### Frontend on Vercel

Set the Vercel project's Root Directory to `frontend`. The configuration in
`frontend/vercel.json` enables clean URLs so `/methodology` serves
`methodology.html`, preserving the investigation query parameters. Deploy this
file with the frontend to make the methodology links work on Vercel. 

### Command-line reports

```bash
uv sync
uv run spaceapps --region uba --start 2026-01-01 --end 2026-12-31

uv run uvicorn spaceapps.api:app --reload --port 8000
```

```bash
# other regions
uv run spaceapps --region porto-alegre --start 2015-01-01

# coordinates
uv run spaceapps --lat -23.55 --lon -46.63 --name "São Paulo" --start 2012-01-01
```

Uses: Python 3.12+ and internet then `data/cache/`

## Version notes
This pipeline uses long punctual series of NASA POWER not using `earthaccess` database of first version.

## Limitations

Would be increased accuration throught looking for oficial allerts of Civil Deffense and with local data of river level.
