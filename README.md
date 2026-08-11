# Electricity Demand Growth and Power-Sector Emissions Intensity
## A cross-country analysis of the world's largest electricity markets, 2015–2025

Five of the ten largest electricity markets increased electricity demand while lowering power-sector emissions intensity between 2015 and 2025.

However, lower emissions intensity did not always mean lower total emissions: China and India both saw total power-sector emissions rise substantially as electricity demand and absolute coal generation continued to grow.

![Demand change vs. emissions-intensity change, 2015-2025](figures/fig1_demand_vs_intensity_quadrant.png)

The x-axis is each country's electricity-demand change, 2015–2025 (%); the y-axis is its power-sector emissions-intensity change over the same period (%). Each point is one of the ten largest electricity markets by 2025 demand.

## Research question

Among the world's ten largest electricity markets, which countries increased electricity demand while reducing the carbon intensity of power generation between 2015 and 2025 — and which did not?

This is a descriptive comparison. It does not attempt to estimate the causal effect of any particular technology or policy.

## Key findings

**1. Five of the ten markets grew demand while lowering emissions intensity.** China (demand +81.98%, intensity −21.22%), the United States (+9.28%, −23.87%), India (+58.92%, −10.69%), Brazil (+24.06%, −41.78%), and South Korea (+14.03%, −14.46%) all fall in this quadrant. The other five either grew demand while intensity also rose (Russia and Canada), or had lower/roughly flat demand alongside falling intensity (Japan, Germany and France).

**2. Emissions intensity is not the same as total emissions — China and India show why.** China's coal share of generation fell 15.02 percentage points (69.6% → 54.6%), but coal generation in absolute terms rose from 4,046 TWh to 5,772 TWh, up 42.66%, and total power-sector emissions rose from 3,884 to 5,566 MtCO2e, up 43.31%. India's coal share fell 5.98pp, but absolute coal generation rose 46.46% (1,007 → 1,474 TWh) and total emissions rose 41.85% (984 → 1,396 MtCO2e). A shrinking fossil-fuel *share* in a rapidly growing electricity system does not necessarily mean fossil generation is shrinking in *absolute* terms. Among the five demand-up/intensity-down markets, three — the United States, Brazil, and South Korea — also reduced total power-sector emissions; China and India did not. Recent year-over-year reporting from [IEA](https://www.iea.org/reports/electricity-2026/supply) and [CREA](https://energyandcleanair.org/publication/india-power-sector-review-2025/) shows coal generation easing in both countries in 2025 specifically — our own data shows the same-direction 2024→2025 moves (China −0.95%, India −2.88%). That single-year signal and this project's decade-scale comparison describe different time horizons; they are not in conflict.

**3. Generation mixes followed very different pathways to a lower intensity.** Germany recorded one of the largest emissions-intensity declines among the ten markets (−34.47%, behind only Brazil's −41.78%), alongside a substantial generation-mix shift: renewables up 29.61pp, coal down 21.95pp, and nuclear down 14.36pp following the country's April 2023 phase-out. Fraunhofer ISE's own one-year-after assessment found that added renewables output alone more than compensated for the lost nuclear generation ([Fraunhofer ISE, 2024](https://www.ise.fraunhofer.de/en/press-media/press-releases/2024/status-quo-one-year-since-germanys-nuclear-exit-renewable-capacity-expands-electricity-from-fossil-fuels-significantly-reduced.html)) — an outside characterization, not a claim this project's data can independently establish. The United States reached a smaller intensity decline (−23.87%) through a different mix: coal down 16.81pp, but gas and other fossil fuels up 6.95pp alongside renewables up 12.01pp. China and India, by contrast, cut coal's *share* by far less (−15.02pp and −5.98pp) while absolute coal generation kept growing (see Finding 2) — the same direction of mix change, at a much smaller scale relative to demand growth.

**4. Russia and Canada were the only two demand-up markets where intensity also rose — through different mix changes.** Canada: demand +7.33%, intensity +3.40%, with coal's share down 5.83pp while gas and other fossil rose 8.00pp and renewables' share was essentially flat (+0.05pp) — in this data, most of the shift away from coal went to gas rather than to clean sources, unlike Germany or the United States in Finding 3. Russia: demand +11.38%, intensity +1.24%, with gas's share down 5.10pp and coal up 3.55pp. These are opposite mix changes producing a similar small intensity increase, so they should not be read as the same story. Both increases are small, and both countries' full 2015–2025 trend direction agrees with the endpoint comparison (neither is flagged as endpoint-sensitive — see Methodology). For Russia, the observed increase in coal share and decline in gas share are consistent with the small increase in emissions intensity, but this analysis does not establish why Russia's generation mix changed; the same caveat applies to Canada's mix shift.

Japan is a shorter note rather than a key finding: its demand changed by only −0.0146% over the decade — close enough to zero that it should be read as roughly flat, not declining, even though the classification rule places it on the "Demand Down" side. Japan's intensity still fell 17.43%, alongside nuclear's share recovering by 8.70pp as reactors gradually restarted.

![Generation-mix transition, 2015-2025](figures/fig2_generation_mix_transition.png)

This chart shows each country's change in generation *share* by fuel category, in percentage points — not a percentage change, and not a change in absolute generation. As Finding 2 shows, a falling coal share (as in China and India) can still coexist with rising coal output in absolute terms; this chart alone cannot distinguish the two.

![Annual demand and emissions-intensity trends for four rule-selected markets, 2015-2025](figures/fig3_selected_country_trends.png)

The four countries shown — China, the United States, Russia, and Japan — were not chosen by hand. The selection rule takes the highest-2025-demand country from each occupied outcome quadrant (three quadrants were occupied among these ten countries), then fills any remaining slot with the next-highest-demand country not already selected. The annual trajectories exist to check whether a two-point (2015 vs. 2025) comparison could be hiding a misleading single-year swing. None of the ten countries was flagged endpoint-sensitive: every country's full 11-year linear trend agrees in direction with its 2015–2025 endpoint comparison.

## Data

**Publisher:** Ember (Ember Energy Research CIC)
**Dataset:** Yearly Electricity Data — [ember-energy.org/data/yearly-electricity-data](https://ember-energy.org/data/yearly-electricity-data/)
**File:** `release_generation_yearly_global.csv`
**Access date:** 10 August 2026
**License:** CC BY 4.0
**Period used:** 2015–2025

**Country selection:** the top ten country-level entities by 2025 electricity demand, among countries with valid (non-missing) 2015 and 2025 demand and Total-generation emissions-intensity observations. Applied mechanically in `src/clean_data.py`, not hand-picked — see [`data/raw/PROVENANCE.md`](data/raw/PROVENANCE.md) for the full source record.

**Countries:** China, United States, India, Russia, Japan, Brazil, Canada, South Korea, Germany, France.

Demand in Ember's data is defined as generation plus net imports (it does not subtract transmission and distribution losses). The headline emissions-intensity figure is taken from the "Total generation" row of the dataset and is a lifecycle gCO2e/kWh average across the full generation mix, not direct combustion emissions alone.

## Methodology

**A. Country selection.** Countries are ranked by 2025 electricity demand; the top 10 with valid 2015-and-2025 demand and intensity data are selected. No country needed to be excluded for missing data in this run (see `src/clean_data.py`'s eligibility audit).

**B. Demand change:** `((Demand_2025 / Demand_2015) - 1) × 100`

**C. Demand CAGR:** `((Demand_2025 / Demand_2015)^(1/10) - 1) × 100`

**D. Emissions-intensity change:** the same relative-change formula, applied to the Total generation row's intensity.

**E. Full-series robustness check.** An OLS-equivalent linear trend (`numpy.polyfit`) is fit across all 11 annual intensity observations (2015–2025) per country. If the trend's sign disagrees with the 2015-vs-2025 endpoint direction, the country is flagged `intensity_endpoint_sensitive`. None were flagged in this analysis.

**F. Generation mix.** Percentage-point changes in each country's share of total generation for Coal, Gas + Other fossil (summed), Nuclear, and Renewables (Ember's own aggregate — not manually reconstructed from individual fuel rows).

**G. Outcome classification.** Each country is placed into one of four categories — Demand Up / Intensity Down, Demand Up / Intensity Up, Demand Down / Intensity Down, Demand Down / Intensity Up — based on the sign of its 2015–2025 endpoint change. This is an operational, descriptive classification for this analysis. It is not a claim of causal or economy-wide "decoupling."

## Reproduce the analysis

```bash
git clone https://github.com/vihalthatipamula09/electricity-demand-emissions-intensity.git
cd electricity-demand-emissions-intensity

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

python src/download_data.py
python src/clean_data.py
python src/analyze.py
python src/visualize.py
```

The pipeline runs in one direction: `download_data.py` fetches and caches the raw Ember file; `clean_data.py` selects the 10 countries and writes `data/processed/clean_annual_country_source.csv`; `analyze.py` computes every metric in this README and writes `outputs/country_summary.csv`; `visualize.py` reads both and produces the three PNGs in `figures/`. `outputs/country_summary.csv` is the canonical analytical output — every number in this README is drawn from it or directly recomputable from `data/processed/clean_annual_country_source.csv`.

## Repository structure

```
electricity-demand-emissions-intensity/
├── README.md
├── requirements.txt
├── LICENSE
├── data/
│   ├── raw/               # cached Ember download + PROVENANCE.md (raw CSV itself is not committed)
│   └── processed/
│       └── clean_annual_country_source.csv
├── src/
│   ├── download_data.py   # fetches and verifies the raw Ember file
│   ├── clean_data.py      # selects countries, validates, writes the processed dataset
│   ├── analyze.py         # computes every metric, writes outputs/country_summary.csv
│   └── visualize.py       # produces the three figures below
├── outputs/
│   └── country_summary.csv
└── figures/
    ├── fig1_demand_vs_intensity_quadrant.png
    ├── fig2_generation_mix_transition.png
    └── fig3_selected_country_trends.png
```

## Limitations

1. **Emissions intensity is not total emissions.** A country can lower intensity while total power-sector emissions still rise, if generation grows fast enough — demonstrated directly by China and India (Finding 2).
2. **Generation share is not absolute generation.** A falling fossil share, in a growing system, can coexist with rising fossil output in absolute terms.
3. **Ember's 2025 values are provisional**, projected from partial-year monthly data at the time of this analysis, and subject to revision in future Ember releases.
4. **Weather, hydrology, and nuclear plant availability can shift a single year's generation mix** independently of any structural or policy change. The 11-year trend check (Methodology, E) reduces but does not eliminate this concern — it confirms direction, not magnitude.
5. **These results describe the power sector only**, not economy-wide emissions from transport, industry, or other sectors.
6. **This is a descriptive analysis.** Generation-mix changes are reported as coinciding with intensity changes, not as their proven cause.

## Contextual sources

A small number of claims in this README rely on outside sources for explanatory context beyond what this project's own data can establish — each is cited inline where it's used, and listed here for reference: [IEA, *Electricity 2026*](https://www.iea.org/reports/electricity-2026/supply); [CREA, *India Power Sector Review 2025*](https://energyandcleanair.org/publication/india-power-sector-review-2025/); [Fraunhofer ISE, on Germany's nuclear exit](https://www.ise.fraunhofer.de/en/press-media/press-releases/2024/status-quo-one-year-since-germanys-nuclear-exit-renewable-capacity-expands-electricity-from-fossil-fuels-significantly-reduced.html). No source is cited for a number this project's own pipeline produced. Both Russia's and Canada's generation-mix shifts are deliberately left uncited beyond our own data: sources reviewed for each (e.g. EIA's Russia brief; Canada Energy Regulator market snapshots) either confirm the same mix percentages our pipeline already produces or describe a different pattern (province-level coal-to-gas transitions in Alberta specifically, versus a national coal-to-low-emissions narrative) than the national aggregate shown here — so no outside source is used to explain either country's shift.

## Development note

This project's data pipeline, analysis, figures, and README were built with substantial use of an AI coding assistant (Claude), working under my direction through a phased, review-gated process: I set the research question, dataset, methodology, and specific corrections at each stage, and reviewed the assistant's output before advancing to the next one. Every quantitative claim in this README was independently verified against the pipeline's own generated data (`outputs/country_summary.csv` and `data/processed/clean_annual_country_source.csv`) before publication, including a full audit pass that caught and corrected a citation error from an earlier draft. The analytical definitions, methodological choices, and conclusions are mine.

## About

Vihal Thatipamula

Independent portfolio analysis demonstrating reproducible energy-data research.
