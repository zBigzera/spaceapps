# Earth System Trend Detective

Ferramenta do [NASA Space Apps Challenge](https://www.spaceappschallenge.org/) para investigar **se enchentes em uma região estão ligadas a tendências reais** de chuva, saturação do solo e outras variáveis da NASA — e se essas mudanças são estatisticamente significativas.

Estudo de caso padrão: **Ubá, Minas Gerais**. Também há presets para Petrópolis, Porto Alegre e Recife, ou qualquer ponto (`--lat` / `--lon`).

## O que a ferramenta responde

1. **O que** está mudando (chuva, solo, eventos compostos chuva+solo, índice de risco).
2. **Onde** (região ou coordenada escolhida).
3. **Quanto** (inclinação linear por ano e R²).
4. **Se é significativo** (regressão OLS e teste de Mann-Kendall, α = 0,05).

Além das tendências, o motor cruza **céu × solo**: chuva diária e acumulada, umidade superficial e da zona radicular, evapotranspiração, índice de precipitação antecedente (API) e um índice de risco 0–100.

## Dados

Fonte padrão: **[NASA POWER](https://power.larc.nasa.gov/)** (reanálise **MERRA-2**), série diária pontual — adequada para décadas de análise sem baixar milhares de granules.

| Variável | Código | Papel na enchente |
| --- | --- | --- |
| Precipitação corrigida | `PRECTOTCORR` | Gatilho (o que vem do céu) |
| Umidade 0–5 cm | `GWETTOP` | Encharcamento raso / escoamento imediato |
| Umidade 0–100 cm | `GWETROOT` | Memória hídrica do terreno |
| Evapotranspiração | `EVPTRNS` | Quanto o solo/vegetação devolve à atmosfera |
| Temperatura e UR | `T2M`, `RH2M` | Contexto atmosférico |

## Como rodar

```bash
uv sync
uv run spaceapps --region uba --start 2026-01-01 --end 2026-12-31
```

Isso baixa (ou relê o cache) 2010 → hoje para Ubá e grava `outputs/uba_trend_detective.html`.

```bash
# Outra cidade
uv run spaceapps --region porto-alegre --start 2015-01-01

# Ponto qualquer
uv run spaceapps --lat -23.55 --lon -46.63 --name "São Paulo" --start 2012-01-01
```

Requisitos: Python 3.12+ e internet na primeira execução (depois usa `data/cache/`).

## Por que não só GPM/GLDAS granule a granule

A versão anterior consultava `GPM_3IMERGDL` e `GLDAS` via `earthaccess`, mas media o **arquivo inteiro** em vez do polígono de Ubá, normalizava o solo pelo máximo da própria série (sempre “100%” no período) e usava **um único ano** como se fosse climatologia. Sem recorte espacial e sem décadas de dados, tendência e risco ficam errados.

O pipeline atual usa séries pontuais longas da NASA POWER. `earthaccess` permanece nas dependências para uma evolução futura com GPM IMERG recortado na bbox.

## Limitações

O índice de risco estima a **coincidência** de chuva persistente e solo já úmido. Não é vazão de rio, nem aviso oficial de defesa civil.
