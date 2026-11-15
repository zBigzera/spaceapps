from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from spaceapps.analysis import add_hydrology_features, analyze
from spaceapps.dashboard import write_dashboard
from spaceapps.power import fetch_nasa_power
from spaceapps.regions import REGIONS, Region, get_region

ROOT = Path.cwd()
CACHE_DIR = ROOT / "data" / "cache"
OUTPUT_DIR = ROOT / "outputs"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="spaceapps",
        description=(
            "Earth System Trend Detective: cruza séries da NASA (chuva, saturação do solo "
            "e evapotranspiração) para diagnosticar risco composto de enchente e tendências."
        ),
    )
    parser.add_argument(
        "--region",
        default="uba",
        choices=sorted(REGIONS),
        help="Estudo de caso predefinido (padrão: Ubá, MG).",
    )
    parser.add_argument("--lat", type=float, help="Latitude (sobrescreve a região).")
    parser.add_argument("--lon", type=float, help="Longitude (sobrescreve a região).")
    parser.add_argument("--name", help="Nome amigável do ponto personalizado.")
    parser.add_argument("--start", default="2026-01-01", help="Início YYYY-MM-DD.")
    parser.add_argument("--end", default=date.today().isoformat(), help="Fim YYYY-MM-DD.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Arquivo HTML do dashboard (padrão: outputs/<regiao>_trend_detective.html).",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Abre o gráfico principal no navegador após gerar o HTML.",
    )
    return parser.parse_args(argv)


def resolve_region(args: argparse.Namespace) -> Region:
    base = get_region(args.region)
    if args.lat is None and args.lon is None:
        return base
    if args.lat is None or args.lon is None:
        raise SystemExit("Informe --lat e --lon juntos para um ponto personalizado.")
    return Region(
        slug="custom",
        name=args.name or f"Ponto ({args.lat:.2f}, {args.lon:.2f})",
        latitude=args.lat,
        longitude=args.lon,
        description="Ponto definido pelo usuário para o diagnóstico céu × solo.",
    )


def print_report(region: Region, report) -> None:
    print("=" * 78)
    print(" NASA SPACE APPS · Earth System Trend Detective")
    print(f" Onde: {region.name}")
    print(f" Período: {report.start} → {report.end}  ({report.n_days} dias)")
    print("=" * 78)
    print("\n O QUE / QUANTO / SIGNIFICATIVO")
    for trend in report.trends:
        flag = "✓" if trend.significant else "·"
        print(
            f"  {flag} {trend.variable}: {trend.slope_per_year:+.4f}/ano | "
            f"R²={trend.r2:.3f} | p_OLS={trend.ols_p:.4f} | "
            f"MK {trend.mk_label} (p={trend.mk_p:.4f})"
        )
    print("\n CORRELAÇÕES CÉU × SOLO")
    for key, value in report.correlations.items():
        print(f"  · {key}: {value:.2f}")
    print(f"\n Eventos compostos (chuva persistente + solo úmido): {report.n_compound}")
    if report.critical_days.empty:
        print(" Nenhum dia com índice de risco ≥ 75.")
    else:
        print("\n Principais dias críticos:")
        for idx, row in report.critical_days.head(8).iterrows():
            print(
                f"  {idx.strftime('%d/%m/%Y')}  chuva {row.precip_mm:5.1f} mm  |  "
                f"7d {row.precip_7d:6.1f} mm  |  solo {row.soil_root_pct:5.1f}%  |  "
                f"risco {row.flood_risk:5.1f}"
            )
    print("=" * 78)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    region = resolve_region(args)
    raw = fetch_nasa_power(region, args.start, args.end, CACHE_DIR)
    featured = add_hydrology_features(raw)
    report = analyze(raw)
    print_report(region, report)

    output = args.output
    if output is None:
        output = OUTPUT_DIR / f"{region.slug}_trend_detective.html"
    path = write_dashboard(featured, report, region, output)
    print(f"\n🌐 Dashboard salvo em: {path}")
    if args.show:
        from spaceapps.dashboard import build_figures

        build_figures(featured, report, region)[0].show()


if __name__ == "__main__":
    main()
