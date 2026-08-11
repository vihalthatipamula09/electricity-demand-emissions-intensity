"""
clean_data.py

Reads the cached raw Ember CSV (data/raw/release_generation_yearly_global.csv),
programmatically selects the 10 analysis countries, restricts the dataset to
the years and electricity sources this project actually needs, validates it,
and writes data/processed/clean_annual_country_source.csv.

This script does NOT calculate project metrics, classify countries, or
produce findings -- that happens in analyze.py (Phase 6). Its only job is to
turn the raw Ember file into a small, validated, analysis-ready table, and to
fail loudly if the raw data doesn't support that.

Usage:
    python src/clean_data.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = REPO_ROOT / "data" / "raw" / "release_generation_yearly_global.csv"
OUTPUT_PATH = REPO_ROOT / "data" / "processed" / "clean_annual_country_source.csv"

START_YEAR = 2015
END_YEAR = 2025
N_COUNTRIES = 10

# The exact raw columns this script depends on. Checked before anything else
# runs -- if Ember changes the schema, we want a clear error here, not a
# confusing KeyError three functions later.
REQUIRED_RAW_COLUMNS = [
    "Area",
    "ISO 3 code",
    "Year",
    "Area type",
    "Electricity source",
    "Is aggregated source",
    "Generation (TWh)",
    "Share of generation (%)",
    "Emissions (MtCO2e)",
    "Emissions intensity (gCO2e/kWh)",
]

# The only Electricity source rows this project needs. Deliberately narrow:
# Chart 2 (generation-mix transition) needs Coal, Gas, Other fossil, Nuclear,
# and Renewables; the classification and CAGR/trend work need Demand and
# Total generation. Individual renewable fuel rows (Wind, Solar, Hydro,
# Bioenergy, Other renewables) are dropped -- we use Ember's own validated
# "Renewables" aggregate instead of reconstructing it (see the Phase 5
# report for why).
REQUIRED_SOURCES = [
    "Demand",
    "Total generation",
    "Coal",
    "Gas",
    "Other fossil",
    "Nuclear",
    "Renewables",
]


class DataValidationError(Exception):
    """Raised when the raw or cleaned data fails a required check."""


# ---------------------------------------------------------------------------
# Loading and schema validation
# ---------------------------------------------------------------------------

def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Raw data file not found at {path}. Run src/download_data.py first."
        )

    df = pd.read_csv(path)

    missing_cols = [c for c in REQUIRED_RAW_COLUMNS if c not in df.columns]
    if missing_cols:
        raise DataValidationError(
            "Raw CSV is missing required columns -- Ember's schema may have "
            f"changed. Missing: {missing_cols}. Found columns: {list(df.columns)}"
        )

    return df


# ---------------------------------------------------------------------------
# Country universe and selection
# ---------------------------------------------------------------------------

def country_level_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Restrict to real countries/economies, dropping World, regions (Asia,
    Europe, ...), and economic groupings (EU, G7, G20, OECD, ASEAN, ...).
    No hardcoded exclusion list -- Ember's own "Area type" column already
    distinguishes "Country or economy" from "Region".
    """
    valid_types = set(df["Area type"].unique())
    if "Country or economy" not in valid_types:
        raise DataValidationError(
            f"Expected 'Country or economy' in Area type values, found: {valid_types}"
        )
    return df[df["Area type"] == "Country or economy"].copy()


def build_eligibility_audit(countries: pd.DataFrame) -> pd.DataFrame:
    """
    Rank country-level entities by END_YEAR electricity demand, and check
    each one for valid START_YEAR and END_YEAR Demand and Total-generation
    emissions-intensity observations. Returns a full audit table (not just
    the selected 10) so the selection is inspectable, not a black box.
    """
    demand = countries[countries["Electricity source"] == "Demand"]
    total_gen = countries[countries["Electricity source"] == "Total generation"]

    demand_end = demand[demand["Year"] == END_YEAR][["Area", "ISO 3 code", "Generation (TWh)"]]
    demand_end = demand_end.rename(columns={"Generation (TWh)": "demand_end"})

    ranked = demand_end.sort_values("demand_end", ascending=False).reset_index(drop=True)
    ranked.insert(0, "rank", ranked.index + 1)

    def lookup(source_df: pd.DataFrame, area: str, year: int, value_col: str):
        row = source_df[(source_df["Area"] == area) & (source_df["Year"] == year)]
        if len(row) == 0:
            return None
        val = row[value_col].values[0]
        return None if pd.isna(val) else val

    records = []
    for _, r in ranked.iterrows():
        area = r["Area"]
        d_start = lookup(demand, area, START_YEAR, "Generation (TWh)")
        d_end = r["demand_end"]
        i_start = lookup(total_gen, area, START_YEAR, "Emissions intensity (gCO2e/kWh)")
        i_end = lookup(total_gen, area, END_YEAR, "Emissions intensity (gCO2e/kWh)")

        missing = []
        if d_start is None:
            missing.append(f"missing {START_YEAR} demand")
        if d_end is None:
            missing.append(f"missing {END_YEAR} demand")
        if i_start is None:
            missing.append(f"missing {START_YEAR} emissions intensity")
        if i_end is None:
            missing.append(f"missing {END_YEAR} emissions intensity")

        eligible = len(missing) == 0
        records.append(
            {
                "rank": int(r["rank"]),
                "country": area,
                "iso3": r["ISO 3 code"],
                f"demand_{END_YEAR}_twh": round(d_end, 2) if d_end is not None else None,
                "eligible": eligible,
                "exclusion_reason": "; ".join(missing) if missing else "",
            }
        )

    return pd.DataFrame(records)


def select_countries(audit: pd.DataFrame, n: int = N_COUNTRIES) -> pd.DataFrame:
    eligible = audit[audit["eligible"]].sort_values("rank")
    if len(eligible) < n:
        raise DataValidationError(
            f"Only {len(eligible)} eligible countries found; need {n}. "
            "Cannot proceed with country selection."
        )
    selected = eligible.head(n).copy()

    excluded_from_top_n = audit[(audit["rank"] <= selected["rank"].max()) & (~audit["eligible"])]
    if len(excluded_from_top_n):
        print("Countries excluded from the nominal top-N window for missing endpoint data:")
        for _, row in excluded_from_top_n.iterrows():
            print(f"  - {row['country']} (rank {row['rank']}): {row['exclusion_reason']}")
    else:
        print(f"No nominal top-{n} country was excluded -- all top-{n}-by-rank countries are eligible.")

    return selected


def print_eligibility_audit(audit: pd.DataFrame, top_n: int = 15) -> None:
    print(f"\n=== Eligibility audit: top {top_n} countries by {END_YEAR} electricity demand ===")
    display_cols = ["rank", "country", "iso3", f"demand_{END_YEAR}_twh", "eligible", "exclusion_reason"]
    with pd.option_context("display.max_rows", None, "display.width", 140):
        print(audit[display_cols].head(top_n).to_string(index=False))


# ---------------------------------------------------------------------------
# Germany "Other renewables" residual audit (required by Phase 5 review)
# ---------------------------------------------------------------------------

def audit_germany_renewables_residual(countries: pd.DataFrame) -> None:
    print("\n=== Audit: Germany 2025 negative 'Other renewables' residual ===")
    g = countries[(countries["Area"] == "Germany") & (countries["Year"] == 2025)]

    if g.empty:
        print("Germany/2025 rows not found in this file -- skipping (nothing to audit).")
        return

    def val(source: str, col: str = "Generation (TWh)"):
        row = g[g["Electricity source"] == source]
        return None if row.empty else row[col].values[0]

    total_gen = val("Total generation")
    other_ren = val("Other renewables")
    renewables_native = val("Renewables")
    fuel_components = ["Wind", "Solar", "Hydro", "Bioenergy", "Other renewables"]
    manual_sum = sum(v for v in (val(f) for f in fuel_components) if v is not None)

    print(f"Germany 2025 'Other renewables' (TWh):        {other_ren}")
    print(f"Germany 2025 Total generation (TWh):          {total_gen}")
    print(f"  -> as % of total generation:                {other_ren/total_gen*100:.4f}%")
    print(f"Germany 2025 native 'Renewables' aggregate:   {renewables_native}")
    print(f"  -> 'Other renewables' as % of that aggregate: {other_ren/renewables_native*100:.4f}%")
    print(f"Manual sum of Wind+Solar+Hydro+Bioenergy+Other renewables: {manual_sum}")
    diff = manual_sum - renewables_native
    print(f"Difference vs. Ember's native 'Renewables' aggregate: {diff}")
    if abs(diff) < 1e-6:
        print(
            "-> Native aggregate is internally coherent: it already includes this "
            "residual and matches the manual sum exactly. The residual is <0.2% of "
            "the Renewables total and <0.12% of total generation -- immaterial to "
            "every metric this project computes, and NOT clipped or altered, "
            "consistent with Ember's own published methodology (which documents "
            "this kind of small reconciliation residual, not row-level cleaning)."
        )
    else:
        print(
            "-> WARNING: native aggregate does NOT match the manual sum. "
            "This needs investigation before proceeding -- do not silently trust "
            "either value."
        )


# ---------------------------------------------------------------------------
# Building the analytical subset
# ---------------------------------------------------------------------------

def build_analytical_subset(countries: pd.DataFrame, selected: pd.DataFrame) -> pd.DataFrame:
    selected_areas = set(selected["country"])
    years = list(range(START_YEAR, END_YEAR + 1))

    subset = countries[
        countries["Area"].isin(selected_areas)
        & countries["Year"].between(START_YEAR, END_YEAR)
        & countries["Electricity source"].isin(REQUIRED_SOURCES)
    ].copy()

    out = subset[
        [
            "Area",
            "ISO 3 code",
            "Year",
            "Electricity source",
            "Is aggregated source",
            "Generation (TWh)",
            "Share of generation (%)",
            "Emissions (MtCO2e)",
            "Emissions intensity (gCO2e/kWh)",
        ]
    ].rename(
        columns={
            "Area": "country",
            "ISO 3 code": "iso3",
            "Year": "year",
            "Electricity source": "electricity_source",
            "Is aggregated source": "is_aggregated_source",
            "Generation (TWh)": "generation_twh",
            "Share of generation (%)": "share_generation_pct",
            "Emissions (MtCO2e)": "emissions_mtco2e",
            "Emissions intensity (gCO2e/kWh)": "emissions_intensity_gco2e_kwh",
        }
    )

    out = out.sort_values(["iso3", "year", "electricity_source"]).reset_index(drop=True)
    return out


# ---------------------------------------------------------------------------
# Validation of the cleaned subset
# ---------------------------------------------------------------------------

def validate_completeness(clean: pd.DataFrame, selected: pd.DataFrame) -> None:
    years = list(range(START_YEAR, END_YEAR + 1))
    gaps = []

    for iso3 in selected["iso3"]:
        for year in years:
            for source in REQUIRED_SOURCES:
                rows = clean[
                    (clean["iso3"] == iso3) & (clean["year"] == year) & (clean["electricity_source"] == source)
                ]
                if len(rows) == 0:
                    gaps.append((iso3, year, source, "missing"))
                elif len(rows) > 1:
                    gaps.append((iso3, year, source, f"{len(rows)} rows (expected 1)"))

    if gaps:
        msg = "\n".join(f"  {iso3} / {year} / {source}: {issue}" for iso3, year, source, issue in gaps[:50])
        raise DataValidationError(
            f"Completeness check failed -- {len(gaps)} gap(s) found (showing up to 50):\n{msg}"
        )

    print(
        f"Completeness check passed: exactly one row for each of "
        f"{len(selected)} countries x {len(years)} years x {len(REQUIRED_SOURCES)} sources "
        f"= {len(selected) * len(years) * len(REQUIRED_SOURCES)} expected rows."
    )


def check_duplicates(clean: pd.DataFrame) -> None:
    dupes = clean.duplicated(subset=["iso3", "year", "electricity_source"], keep=False)
    if dupes.any():
        raise DataValidationError(
            f"Found {dupes.sum()} duplicate (iso3, year, electricity_source) rows:\n"
            f"{clean[dupes].to_string(index=False)}"
        )
    print("Duplicate check passed: no duplicate (iso3, year, electricity_source) rows.")


def check_numeric_validity(clean: pd.DataFrame) -> None:
    print("\n=== Numeric validity report (informational -- nothing is auto-repaired) ===")

    neg_gen = clean[clean["generation_twh"] < 0]
    print(f"Negative generation_twh rows: {len(neg_gen)}")
    if len(neg_gen):
        print(neg_gen[["country", "year", "electricity_source", "generation_twh"]].to_string(index=False))

    missing_gen = clean["generation_twh"].isna().sum()
    print(f"Missing generation_twh values: {missing_gen}")

    intensity_required = clean[clean["electricity_source"] == "Total generation"]
    missing_intensity = intensity_required["emissions_intensity_gco2e_kwh"].isna().sum()
    print(
        f"Missing emissions_intensity_gco2e_kwh on 'Total generation' rows: "
        f"{missing_intensity} (of {len(intensity_required)})"
    )

    # Share of generation should be within a broad plausible band. We do not
    # clip or fix anything here -- only flag rows outside the band. Demand
    # rows can slightly exceed 100% (generation + net imports), so they're
    # checked against a wider allowance.
    non_demand = clean[clean["electricity_source"] != "Demand"]
    implausible = non_demand[
        (non_demand["share_generation_pct"] < -5) | (non_demand["share_generation_pct"] > 105)
    ]
    print(f"Non-demand rows with share_generation_pct outside [-5, 105]: {len(implausible)}")
    if len(implausible):
        print(implausible[["country", "year", "electricity_source", "share_generation_pct"]].to_string(index=False))

    demand_rows = clean[clean["electricity_source"] == "Demand"]
    implausible_demand = demand_rows[
        (demand_rows["share_generation_pct"] < 50) | (demand_rows["share_generation_pct"] > 150)
    ]
    print(f"Demand rows with share_generation_pct outside [50, 150]: {len(implausible_demand)}")
    if len(implausible_demand):
        print(implausible_demand[["country", "year", "share_generation_pct"]].to_string(index=False))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"Loading raw data from {RAW_PATH} ...")
    raw = load_raw()
    print(f"Raw file loaded: {raw.shape[0]:,} rows, {raw.shape[1]} columns.")

    countries = country_level_rows(raw)
    print(
        f"Restricted to Area type == 'Country or economy': "
        f"{countries['Area'].nunique()} unique countries/economies "
        f"({raw['Area'].nunique() - countries['Area'].nunique()} region/aggregate entities dropped)."
    )

    audit_germany_renewables_residual(countries)

    audit = build_eligibility_audit(countries)
    print_eligibility_audit(audit, top_n=15)

    selected = select_countries(audit, n=N_COUNTRIES)
    print(f"\nSelected {N_COUNTRIES} countries (by {END_YEAR} demand, endpoint-eligible):")
    print(selected[["rank", "country", "iso3", f"demand_{END_YEAR}_twh"]].to_string(index=False))

    clean = build_analytical_subset(countries, selected)

    validate_completeness(clean, selected)
    check_duplicates(clean)
    check_numeric_validity(clean)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(OUTPUT_PATH, index=False)

    print("\n=== FINAL VALIDATION SUMMARY ===")
    print(f"Selected countries: {', '.join(selected['country'])}")
    print(f"Year range: {START_YEAR}-{END_YEAR}")
    expected_rows = N_COUNTRIES * (END_YEAR - START_YEAR + 1) * len(REQUIRED_SOURCES)
    print(f"Expected row count: {expected_rows}")
    print(f"Actual row count:   {len(clean)}")
    print(f"Duplicates: 0 (checked above)")
    print(f"Missing generation_twh: {clean['generation_twh'].isna().sum()}")
    print(
        f"Missing emissions_intensity on Total generation rows: "
        f"{clean[clean['electricity_source']=='Total generation']['emissions_intensity_gco2e_kwh'].isna().sum()}"
    )
    print(f"Negative generation_twh rows: {(clean['generation_twh'] < 0).sum()}")
    print(f"Output written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except (DataValidationError, FileNotFoundError) as exc:
        print(f"\nCLEANING FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
