# Earth System Trend Detective: Intenção e Objetivos do Projeto

## Visão geral

O **Earth System Trend Detective** diagnostica eventos ambientais extremos a partir de séries temporais da NASA. O caso piloto é a bacia de **Ubá (MG)** e o recorte temático é enchente: relacionar o **gatilho climático** (chuva) com a **resposta do terreno** (saturação do solo, evapotranspiração, memória da chuva antecedente).

A ferramenta não é só um gráfico de precipitação. Ela audita o passado recente para responder, com teste estatístico:

- o que está mudando;
- onde está mudando;
- quanto está mudando;
- se a mudança é significativa (OLS + Mann-Kendall).

## Como a enchente entra no diagnóstico

Enchente urbana/ribeirinha raramente é “só chuva forte num dia”. O motor trata o problema como evento **composto**:

1. **Gatilho:** precipitação diária e acumulados de 7 e 30 dias (`PRECTOTCORR`, NASA POWER / MERRA-2).
2. **Estado do solo:** umidade superficial (`GWETTOP`) e da zona radicular (`GWETROOT`). Solo já saturado transforma chuva nova em escoamento.
3. **Memória:** índice de precipitação antecedente (API) e anomalia em relação ao ciclo sazonal.
4. **Alívio:** evapotranspiração (`EVPTRNS`) no balanço chuva − ET.

Dias em que acúmulo de 7 dias e solo úmido coincidem (percentis altos) são marcados como **eventos compostos**.

## Como rodar

Na raiz do repositório:

```bash
uv sync
uv run spaceapps --region uba
```

O dashboard interativo (Plotly) é gravado em `outputs/`. Detalhes de uso estão no README da raiz do projeto.

## Desafio Space Apps

O desafio *Be An Earth System Trend Detective!* pede selecionar variáveis de missões/modelos da NASA, gerar série longa para uma região, visualizar a evolução e testar se a tendência é significativa. Tendências podem ter sinal oposto em regiões diferentes; por isso a unidade de análise é o **ponto/região**, não o globo.
