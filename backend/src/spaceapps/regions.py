from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    slug: str
    name: str
    latitude: float
    longitude: float
    description: str


REGIONS: dict[str, Region] = {
    "uba": Region(
        slug="uba",
        name="Ubá, Minas Gerais",
        latitude=-21.12,
        longitude=-42.94,
        description=(
            "Bacia piloto do projeto. Região serrana da Zona da Mata mineira, "
            "com histórico de enxurradas urbanas quando chuva intensa encontra solo já saturado."
        ),
    ),
    "petropolis": Region(
        slug="petropolis",
        name="Petrópolis, Rio de Janeiro",
        latitude=-22.51,
        longitude=-43.18,
        description="Encostas da Serra dos Órgãos, altamente sensíveis a chuva acumulada e saturação do solo.",
    ),
    "porto-alegre": Region(
        slug="porto-alegre",
        name="Porto Alegre, Rio Grande do Sul",
        latitude=-30.03,
        longitude=-51.23,
        description="Planície do Guaíba. Enchentes associadas a chuva persistente e solo/planície já encharcados.",
    ),
    "recife": Region(
        slug="recife",
        name="Recife, Pernambuco",
        latitude=-8.05,
        longitude=-34.88,
        description="Planície costeira com drenagem limitada; picos de chuva sobre solo úmido agravam alagamentos.",
    ),
}


def get_region(slug: str) -> Region:
    try:
        return REGIONS[slug]
    except KeyError as exc:
        known = ", ".join(sorted(REGIONS))
        raise SystemExit(f"Região desconhecida: {slug}. Opções: {known}") from exc
