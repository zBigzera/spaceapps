from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

API_DECAY = 0.85
EXTREME_Q = 0.95
WET_SOIL_Q = 0.90


@dataclass
class TrendResult:
    variable: str
    period: str
    n: int
    slope_per_year: float
    r2: float
    ols_p: float
    mk_s: float
    mk_z: float
    mk_p: float
    mk_label: str
    significant: bool

    def as_dict(self) -> dict:
        return {
            "variável": self.variable,
            "série": self.period,
            "n": self.n,
            "tendência (unid./ano)": round(self.slope_per_year, 4),
            "R²": round(self.r2, 3),
            "p (OLS)": round(self.ols_p, 4),
            "p (Mann-Kendall)": round(self.mk_p, 4),
            "Mann-Kendall": self.mk_label,
            "significativo (α=0.05)": "sim" if self.significant else "não",
        }


@dataclass
class DetectiveReport:
    start: str
    end: str
    n_days: int
    n_compound: int
    critical_days: pd.DataFrame
    trends: list[TrendResult]
    correlations: dict[str, float]
    notes: list[str] = field(default_factory=list)


def _mann_kendall(values: np.ndarray) -> tuple[float, float, float, str, bool]:
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 8:
        return (np.nan, np.nan, np.nan, "série curta demais", False)

    s = 0.0
    for i in range(n - 1):
        s += float(np.sign(x[i + 1 :] - x[i]).sum())

    _, counts = np.unique(x, return_counts=True)
    tie_term = float(np.sum(counts * (counts - 1) * (2 * counts + 5)))
    var_s = (n * (n - 1) * (2 * n + 5) - tie_term) / 18.0
    if var_s <= 0:
        z = 0.0
    elif s > 0:
        z = (s - 1) / np.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / np.sqrt(var_s)
    else:
        z = 0.0
    p = float(2 * (1 - stats.norm.cdf(abs(z))))
    if p < 0.05:
        label = "crescente" if s > 0 else "decrescente"
        significant = True
    else:
        label = "sem tendência significativa"
        significant = False
    return s, z, p, label, significant


def linear_trend(values: pd.Series, variable: str, period: str) -> TrendResult:
    y = values.astype(float)
    y = y[np.isfinite(y)]
    if isinstance(y.index, pd.DatetimeIndex):
        t = y.index.year + (y.index.dayofyear - 1) / 365.25
    else:
        t = y.index.astype(float)
    if len(y) < 4:
        return TrendResult(variable, period, len(y), np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, "série curta demais", False)

    ols = stats.linregress(t, y.to_numpy())
    mk_s, mk_z, mk_p, mk_label, mk_sig = _mann_kendall(y.to_numpy())
    significant = bool((ols.pvalue < 0.05) or mk_sig)
    return TrendResult(
        variable=variable,
        period=period,
        n=len(y),
        slope_per_year=float(ols.slope),
        r2=float(ols.rvalue**2),
        ols_p=float(ols.pvalue),
        mk_s=float(mk_s),
        mk_z=float(mk_z),
        mk_p=float(mk_p),
        mk_label=mk_label,
        significant=significant,
    )


def add_hydrology_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["precip_7d"] = out["precip_mm"].rolling(7, min_periods=1).sum()
    out["precip_30d"] = out["precip_mm"].rolling(30, min_periods=1).sum()

    api = np.zeros(len(out), dtype=float)
    precip = out["precip_mm"].fillna(0).to_numpy()
    for i, p in enumerate(precip):
        api[i] = precip[i] if i == 0 else API_DECAY * api[i - 1] + p
    out["api"] = api

    month = out.index.month
    climatology = out.groupby(month)["precip_mm"].transform("mean")
    out["precip_anomaly"] = out["precip_mm"] - climatology
    out["precip_deseason"] = out["precip_anomaly"]

    soil_clim = out.groupby(month)["soil_root_pct"].transform("mean")
    out["soil_root_anomaly"] = out["soil_root_pct"] - soil_clim

    # Balanço hídrico simples: chuva menos evapotranspiração (mm)
    out["water_balance_mm"] = out["precip_mm"] - out["et_mm"]

    precip_q = out["precip_mm"].quantile(EXTREME_Q)
    soil_q = out["soil_root_pct"].quantile(WET_SOIL_Q)
    accum_q = out["precip_7d"].quantile(0.90)
    out["extreme_rain"] = out["precip_mm"] >= precip_q
    out["wet_soil"] = out["soil_root_pct"] >= soil_q
    out["compound_flood"] = (out["precip_7d"] >= accum_q) & out["wet_soil"]

    # Índice 0–100: gatilho (chuva 7d) + memória do solo + anomalia + API
    rain_term = np.clip(out["precip_7d"] / max(out["precip_7d"].quantile(0.98), 1) * 100, 0, 100)
    soil_term = np.clip(out["soil_root_pct"], 0, 100)
    api_term = np.clip(out["api"] / max(out["api"].quantile(0.98), 1) * 100, 0, 100)
    anomaly_term = np.clip((out["precip_anomaly"] + 20) / 40 * 100, 0, 100)
    out["rain_contribution"] = 0.35 * rain_term
    out["soil_contribution"] = 0.30 * soil_term
    out["api_contribution"] = 0.20 * api_term
    out["anomaly_contribution"] = 0.15 * anomaly_term
    out["flood_risk"] = 0.35 * rain_term + 0.30 * soil_term + 0.20 * api_term + 0.15 * anomaly_term
    out["flood_risk"] = np.clip(out["flood_risk"], 0, 100)
    out["alert"] = pd.cut(
        out["flood_risk"],
        bins=[-0.1, 40, 60, 75, 100],
        labels=["baixo", "moderado", "alto", "crítico"],
    )
    return out


def analyze(df: pd.DataFrame) -> DetectiveReport:
    work = add_hydrology_features(df)
    monthly = work.resample("MS").agg(
        {
            "precip_mm": "sum",
            "soil_root_pct": "mean",
            "flood_risk": "mean",
            "water_balance_mm": "sum",
            "precip_deseason": "mean",
        }
    )
    annual = work.resample("YE").agg(
        {
            "precip_mm": "sum",
            "soil_root_pct": "mean",
            "flood_risk": "mean",
            "compound_flood": "sum",
            "extreme_rain": "sum",
        }
    )

    trends = [
        linear_trend(monthly["precip_mm"], "Precipitação mensal (mm)", "mensal"),
        linear_trend(monthly["precip_deseason"], "Precipitação dessazonalizada (mm/dia)", "mensal"),
        linear_trend(monthly["soil_root_pct"], "Saturação da zona radicular (%)", "mensal"),
        linear_trend(monthly["flood_risk"], "Índice de risco de enchente", "mensal"),
        linear_trend(annual["precip_mm"], "Precipitação anual (mm)", "anual"),
        linear_trend(annual["compound_flood"], "Dias compostos chuva+solo/ano", "anual"),
        linear_trend(annual["extreme_rain"], "Dias de chuva extrema/ano", "anual"),
    ]

    lagged_soil = work["soil_root_pct"].shift(-1)
    correlations = {
        "chuva vs solo no mesmo dia": float(work["precip_mm"].corr(work["soil_root_pct"])),
        "chuva vs solo no dia seguinte": float(work["precip_mm"].corr(lagged_soil)),
        "acúmulo 7d vs saturação": float(work["precip_7d"].corr(work["soil_root_pct"])),
        "saturação vs índice de risco": float(work["soil_root_pct"].corr(work["flood_risk"])),
    }

    critical = work.loc[work["flood_risk"] >= 75, ["precip_mm", "precip_7d", "soil_root_pct", "api", "flood_risk"]]
    critical = critical.sort_values("flood_risk", ascending=False)

    notes = [
        "O índice não prevê enchente hidrológica de rio (não usa vazão observada); estima a coincidência de gatilho (chuva) e condição de terreno (solo saturado).",
        "Sazonalidade removida subtraindo a média do mês civil na série completa, para o teste de tendência não confundir verão chuvoso com mudança de longo prazo.",
        "Dias compostos = acúmulo de 7 dias acima do percentil 90 e solo na zona radicular acima do percentil 90.",
    ]
    return DetectiveReport(
        start=str(work.index.min().date()),
        end=str(work.index.max().date()),
        n_days=len(work),
        n_compound=int(work["compound_flood"].sum()),
        critical_days=critical,
        trends=trends,
        correlations=correlations,
        notes=notes,
    )
