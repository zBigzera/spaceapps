# Earth System Trend Detective

Tooling to investigate trends and flood risk through NASA Earht Data this software uses Ordinary Least Squares (OLS), Mann-Kendall, and trend analysis to investigate statistically significant environmental changes that may influence flood occurencies. It integrates NASA Earth science data to analyze long-term trends in precipitation, soil moisture, evapotranspiration, and atmospheric conditions. Rather than examining rainfall independently, the platform evaluates interactions between atmospheric water input and terrestrial water storage to identify changes in flood susceptibility. Historical data are retrieved through NASA POWER, primarily using MERRA-2 reanalysis. The application calculates accumulated rainfall, antecedent precipitation, soil wetness, and compound conditions involving heavy rainfall and elevated soil moisture. By integrating NASA Earth science data, hydrological indicators, and statistical methods, Earth Science Data Analysis transforms complex environmental datasets into accessible scientific information. The platform aims to support researchers, students, environmental professionals, and local decision-makers in understanding regional environmental changes and identifying conditions that may contribute to flood susceptibility.
## running locally

```bash
uv sync
uv run spaceapps --region uba --start 2026-01-01 --end 2026-12-31
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
