# Data provenance

This file records exactly what source data this analysis is built on.
Populated in Phase 4 from the actual downloaded file (verified programmatically,
not assumed from documentation).

| Field | Value |
|---|---|
| Publisher | Ember (Ember Energy Research CIC), London |
| Dataset name | Yearly Electricity Data (global) |
| Official dataset page | https://ember-energy.org/data/yearly-electricity-data/ |
| Direct file URL | https://files.ember-energy.org/public-downloads/generation/outputs/release_generation_yearly_global.csv |
| Access / download date | 2026-08-10 |
| Dataset version / vintage | Yearly Electricity Data release current as of the July 2026 long-format schema update; underlies the Global Electricity Review 2026. Data years 1985–2025. **2025 figures are Ember's provisional estimates**, derived by projecting annual totals from monthly data — this applies uniformly to the 2025 vintage and is not flagged row-by-row in the file (see Notes). |
| License | CC BY 4.0 |
| Methodology reference | https://files.ember-energy.org/public-downloads/ember_electricity_data_methodology.pdf |
| Local cached file | `data/raw/release_generation_yearly_global.csv` (not committed to Git — see `data/README.md`) |
| File size | 16,059,637 bytes (~15.3 MiB) |
| File hash (sha256) | `15c7f9d2e0c209013388d397456b507010743e3d60c52ced0491408e21fb083d` |
| Row count | 104,099 data rows (104,100 lines incl. header) |
| Column count | 24 |

## Schema, as verified directly from the file (not from documentation)

Columns, in order: `Area`, `ISO 3 code`, `Year`, `Area type`, `Electricity source`,
`Is aggregated source`, `Generation (TWh)`, `Generation YoY change (TWh)`,
`Generation YoY change (%)`, `Share of generation (%)`,
`Share of generation YoY change (% points)`, `Capacity (GW)`,
`Emissions (MtCO2e)`, `Emissions YoY change (MtCO2e)`, `Emissions YoY change (%)`,
`Share of emissions (%)`, `Emissions intensity (gCO2e/kWh)`, `Continent`,
`Ember region`, `EU member`, `OECD member`, `G20 member`, `G7 member`,
`ASEAN member`.

- **Country vs. aggregate rows:** `Area type` is `"Country or economy"` (209
  distinct entities, always has an `ISO 3 code`) or `"Region"` (15 entities —
  ASEAN, AU, Africa, Asia, EU, Europe, G20, G7, Latin America and Caribbean,
  MENA, Middle East, North America, OECD, Oceania, World — `ISO 3 code` always
  null). Filtering `Area type == "Country or economy"` is sufficient to drop
  every World/regional/economic-grouping row. Note: `"AU"` here is a Region
  row (not Australia); Australia is its own `"Country or economy"` row with
  `ISO 3 code == "AUS"`.
- **Demand** is a row, not a dedicated column: `Electricity source == "Demand"`
  (an aggregated-source row), with the value in `Generation (TWh)` — that
  column name is reused generically across all 17 `Electricity source`
  values, not just fuel generation. `Emissions`/`Emissions intensity` are
  null on Demand rows, correctly, since demand is not an emitting source.
- **Total power-sector emissions intensity** is stored on the
  `Electricity source == "Total generation"` row, column
  `Emissions intensity (gCO2e/kWh)`. Per-fuel intensities (e.g. Coal, Gas)
  are also populated on their own rows.
- **Generation by fuel**: one row per country/year for each of Bioenergy,
  Coal, Gas, Hydro, Nuclear, Other fossil, Other renewables, Solar, Wind
  (`Is aggregated source == False`).
- **Aggregates present**: `Total generation`, `Fossil` (Coal+Gas+Other
  fossil), `Clean` (Renewables+Nuclear), `Renewables` (Wind+Solar+Hydro+
  Bioenergy+Other renewables), `Wind and solar`, `Hydro, bioenergy and
  other renewables`, all with `Is aggregated source == True`.
- **Net imports** is its own row (`Is aggregated source == False`); it can
  be negative for net-exporting countries — this is expected, not a data
  error.

## Notes

- No column in this file flags a row as "provisional" or "estimated." The
  2025-vintage caveat above comes from Ember's published methodology, not
  from the data itself, and cannot be applied selectively by country/row —
  it applies to the 2025 data year as a whole.
- A handful of small negative values appear in minor fuel categories for a
  few smaller countries' 2025 rows (e.g. Costa Rica's "Other fossil",
  Germany's "Other renewables") — residuals from Ember's monthly-to-annual
  reconciliation method. None of our 10 selected countries are materially
  affected; verified directly (see Phase 4 report).
- Zero duplicate `(Area, Year, Electricity source)` rows in the file.
- The dataset is updated twice monthly by Ember; the version pinned here is
  the one actually used for every number in this repository. If the
  analysis is re-run later against a newer Ember release, this file must be
  updated and any changed figures in the README must be regenerated, not
  hand-edited.
- No other dataset is used in this analysis.
