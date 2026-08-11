"""
analyze.py

Reads data/processed/clean_annual_country_source.csv and computes every metric
this project reports, writing outputs/country_summary.csv as the single source
of truth for charts, README numbers, and interpretation.

Usage:
    python src/analyze.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
CLEAN_PATH = REPO_ROOT / "data" / "processed" / "clean_annual_country_source.csv"
OUTPUT_PATH = REPO_ROOT / "outputs" / "country_summary.csv"

START_YEAR = 2015
END_YEAR = 2025
YEARS_INTERVAL = END_YEAR - START_YEAR  # 10 annual intervals between 2015 and 2025

MIX_SOURCES = ["Coal", "Gas", "Other fossil", "Nuclear", "Renewables"]

# Threshold (in percentage points of relative % change) below which a
# demand or intensity endpoint change is flagged as "near zero" for
# reporting before classification -- not auto-hidden.
NEAR_ZERO_THRESHOLD_PCT = 1.0

# Threshold for flagging a generation-mix share-sum residual as worth
# investigating (Coal+Gas+Other fossil+Nuclear+Renewables vs. 100%).
SHARE_RESIDUAL_INVESTIGATE_THRESHOLD = 1.0  # percentage points

REQUIRED_CLEAN_COLUMNS = [
    "country",
    "iso3",
    "year",
    "electricity_source",
    "generation_twh",
    "share_generation_pct",
    "emissions_intensity_gco2e_kwh",
]


class AnalysisError(Exception):
    """Raised when the cleaned data can't support a required calculation."""


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_clean(path: Path = CLEAN_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {path}. Run src/clean_data.py first.")
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_CLEAN_COLUMNS if c not in df.columns]
    if missing:
        raise AnalysisError(f"Cleaned CSV is missing required columns: {missing}")
    return df


def get_value(df: pd.DataFrame, iso3: str, year: int, source: str, col: str) -> float:
    row = df[(df["iso3"] == iso3) & (df["year"] == year) & (df["electricity_source"] == source)]
    if len(row) != 1:
        raise AnalysisError(
            f"Expected exactly 1 row for iso3={iso3}, year={year}, source={source!r}; found {len(row)}."
        )
    return row[col].values[0]


# ---------------------------------------------------------------------------
# Metric calculation, per country
# ---------------------------------------------------------------------------

def compute_demand_metrics(df: pd.DataFrame, iso3: str) -> dict:
    d15 = get_value(df, iso3, START_YEAR, "Demand", "generation_twh")
    d25 = get_value(df, iso3, END_YEAR, "Demand", "generation_twh")
    if pd.isna(d15) or pd.isna(d25):
        raise AnalysisError(f"{iso3}: missing demand value(s).")
    if d15 <= 0:
        raise AnalysisError(f"{iso3}: non-positive {START_YEAR} demand ({d15}) -- cannot compute CAGR.")

    pct_change = ((d25 / d15) - 1) * 100
    cagr = ((d25 / d15) ** (1 / YEARS_INTERVAL) - 1) * 100

    return {
        "demand_2015_twh": d15,
        "demand_2025_twh": d25,
        "demand_pct_change": pct_change,
        "demand_cagr_pct": cagr,
    }


def compute_intensity_metrics(df: pd.DataFrame, iso3: str) -> dict:
    i15 = get_value(df, iso3, START_YEAR, "Total generation", "emissions_intensity_gco2e_kwh")
    i25 = get_value(df, iso3, END_YEAR, "Total generation", "emissions_intensity_gco2e_kwh")
    if pd.isna(i15) or pd.isna(i25):
        raise AnalysisError(f"{iso3}: missing Total generation emissions intensity for endpoint year(s).")
    if i15 <= 0:
        raise AnalysisError(f"{iso3}: non-positive {START_YEAR} intensity ({i15}) -- cannot compute CAGR.")

    pct_change = ((i25 / i15) - 1) * 100
    cagr = ((i25 / i15) ** (1 / YEARS_INTERVAL) - 1) * 100

    series = df[(df["iso3"] == iso3) & (df["electricity_source"] == "Total generation")].sort_values("year")
    if len(series) != (END_YEAR - START_YEAR + 1):
        raise AnalysisError(f"{iso3}: expected 11 annual Total generation rows, found {len(series)}.")
    if series["emissions_intensity_gco2e_kwh"].isna().any():
        raise AnalysisError(f"{iso3}: NaN in annual Total generation intensity series -- cannot fit trend.")

    years = series["year"].to_numpy(dtype=float)
    values = series["emissions_intensity_gco2e_kwh"].to_numpy(dtype=float)
    slope, intercept = np.polyfit(years, values, 1)  # intensity = intercept + slope * year

    return {
        "intensity_2015_gco2e_kwh": i15,
        "intensity_2025_gco2e_kwh": i25,
        "intensity_pct_change": pct_change,
        "intensity_cagr_pct": cagr,
        "intensity_trend_slope_gco2e_kwh_per_year": slope,
    }


def compute_mix_metrics(df: pd.DataFrame, iso3: str) -> tuple[dict, float, float]:
    shares = {}
    for src in MIX_SOURCES:
        s15 = get_value(df, iso3, START_YEAR, src, "share_generation_pct")
        s25 = get_value(df, iso3, END_YEAR, src, "share_generation_pct")
        if pd.isna(s15) or pd.isna(s25):
            raise AnalysisError(f"{iso3}: missing share_generation_pct for source {src!r}.")
        shares[src] = (s15, s25)

    gas_of_15 = shares["Gas"][0] + shares["Other fossil"][0]
    gas_of_25 = shares["Gas"][1] + shares["Other fossil"][1]

    result = {
        "coal_share_2015_pct": shares["Coal"][0],
        "coal_share_2025_pct": shares["Coal"][1],
        "coal_pp_change": shares["Coal"][1] - shares["Coal"][0],
        "gas_other_fossil_share_2015_pct": gas_of_15,
        "gas_other_fossil_share_2025_pct": gas_of_25,
        "gas_other_fossil_pp_change": gas_of_25 - gas_of_15,
        "nuclear_share_2015_pct": shares["Nuclear"][0],
        "nuclear_share_2025_pct": shares["Nuclear"][1],
        "nuclear_pp_change": shares["Nuclear"][1] - shares["Nuclear"][0],
        "renewables_share_2015_pct": shares["Renewables"][0],
        "renewables_share_2025_pct": shares["Renewables"][1],
        "renewables_pp_change": shares["Renewables"][1] - shares["Renewables"][0],
    }

    residual_2015 = sum(shares[s][0] for s in MIX_SOURCES) - 100
    residual_2025 = sum(shares[s][1] for s in MIX_SOURCES) - 100
    return result, residual_2015, residual_2025


def classify(demand_pct_change: float, intensity_pct_change: float) -> str:
    """
    demand_pct_change > 0            -> "Up"
    demand_pct_change <= 0 (incl. 0) -> "Down"
    intensity_pct_change < 0         -> "Down"
    intensity_pct_change >= 0 (incl. 0) -> "Up"
    Zero is defined explicitly above; near-zero values are reported
    separately (see check_near_zero_metrics) rather than hidden.
    """
    demand_dir = "Up" if demand_pct_change > 0 else "Down"
    intensity_dir = "Down" if intensity_pct_change < 0 else "Up"
    return f"Demand {demand_dir} / Intensity {intensity_dir}"


def is_endpoint_sensitive(intensity_pct_change: float, slope: float) -> bool:
    endpoint_dir = "down" if intensity_pct_change < 0 else "up"
    trend_dir = "down" if slope < 0 else "up"
    return endpoint_dir != trend_dir


# ---------------------------------------------------------------------------
# Chart 3 country selection (rule-based, no manual override)
# ---------------------------------------------------------------------------

def select_chart3_countries(summary: pd.DataFrame, max_countries: int = 4) -> tuple[list[str], dict[str, str]]:
    selected: list[str] = []
    reasons: dict[str, str] = {}

    # Step 1: highest-2025-demand country in each occupied quadrant.
    for quadrant in sorted(summary["outcome_quadrant"].unique()):
        group = summary[summary["outcome_quadrant"] == quadrant]
        top = group.sort_values("demand_2025_twh", ascending=False).iloc[0]
        if top["iso3"] not in selected:
            selected.append(top["iso3"])
            reasons[top["iso3"]] = f"Highest 2025 demand in occupied quadrant: {quadrant}"

    # Step 2: if fewer than max_countries, add endpoint-sensitive countries
    # (highest demand first) not already selected.
    if len(selected) < max_countries:
        candidates = summary[
            summary["intensity_endpoint_sensitive"] & ~summary["iso3"].isin(selected)
        ].sort_values("demand_2025_twh", ascending=False)
        for _, row in candidates.iterrows():
            if len(selected) >= max_countries:
                break
            selected.append(row["iso3"])
            reasons[row["iso3"]] = "Added: flagged intensity-endpoint-sensitive"

    # Step 3: fill any remaining slots with next-highest-2025-demand countries.
    if len(selected) < max_countries:
        remaining = summary[~summary["iso3"].isin(selected)].sort_values("demand_2025_twh", ascending=False)
        for _, row in remaining.iterrows():
            if len(selected) >= max_countries:
                break
            selected.append(row["iso3"])
            reasons[row["iso3"]] = "Added: next-highest 2025 demand (filling remaining slot)"

    return selected[:max_countries], reasons


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def check_near_zero_metrics(summary: pd.DataFrame) -> None:
    print(f"\n=== Near-zero endpoint changes (|change| < {NEAR_ZERO_THRESHOLD_PCT} pct) -- reported before classification ===")
    near_zero = summary[
        (summary["demand_pct_change"].abs() < NEAR_ZERO_THRESHOLD_PCT)
        | (summary["intensity_pct_change"].abs() < NEAR_ZERO_THRESHOLD_PCT)
    ]
    if near_zero.empty:
        print("None.")
    else:
        for _, r in near_zero.iterrows():
            print(
                f"  {r['country']}: demand_pct_change={r['demand_pct_change']:.4f}%, "
                f"intensity_pct_change={r['intensity_pct_change']:.4f}% "
                f"-> classified as {r['outcome_quadrant']} (rule applied as defined, not overridden)"
            )


def validate_summary(summary: pd.DataFrame, residuals: dict) -> None:
    print("\n=== VALIDATION ===")

    # A. exactly 10 rows
    assert len(summary) == 10, f"Expected 10 summary rows, got {len(summary)}"
    print(f"A. Row count: {len(summary)} (expected 10) -- OK")

    # B. one row per ISO3
    assert summary["iso3"].nunique() == len(summary), "Duplicate ISO3 rows in summary"
    print(f"B. Unique ISO3 count: {summary['iso3'].nunique()} == row count -- OK")

    # C. no required metric missing
    required_numeric = [
        "demand_2015_twh", "demand_2025_twh", "demand_pct_change", "demand_cagr_pct",
        "intensity_2015_gco2e_kwh", "intensity_2025_gco2e_kwh", "intensity_pct_change",
        "intensity_cagr_pct", "intensity_trend_slope_gco2e_kwh_per_year",
        "coal_pp_change", "gas_other_fossil_pp_change", "nuclear_pp_change", "renewables_pp_change",
    ]
    missing_counts = summary[required_numeric].isna().sum()
    assert missing_counts.sum() == 0, f"Missing required metrics:\n{missing_counts[missing_counts > 0]}"
    print("C. No missing required metrics -- OK")

    # D/E. independent recompute of pct change and CAGR for every country
    print("D/E. Independent recompute of demand & intensity pct-change and CAGR:")
    all_match = True
    for _, r in summary.iterrows():
        recomputed_demand_pct = ((r["demand_2025_twh"] / r["demand_2015_twh"]) - 1) * 100
        recomputed_demand_cagr = ((r["demand_2025_twh"] / r["demand_2015_twh"]) ** (1 / YEARS_INTERVAL) - 1) * 100
        recomputed_int_pct = ((r["intensity_2025_gco2e_kwh"] / r["intensity_2015_gco2e_kwh"]) - 1) * 100
        recomputed_int_cagr = ((r["intensity_2025_gco2e_kwh"] / r["intensity_2015_gco2e_kwh"]) ** (1 / YEARS_INTERVAL) - 1) * 100
        ok = (
            np.isclose(recomputed_demand_pct, r["demand_pct_change"])
            and np.isclose(recomputed_demand_cagr, r["demand_cagr_pct"])
            and np.isclose(recomputed_int_pct, r["intensity_pct_change"])
            and np.isclose(recomputed_int_cagr, r["intensity_cagr_pct"])
        )
        all_match = all_match and ok
        if not ok:
            print(f"  MISMATCH for {r['country']}")
    print(f"  All 10 countries' pct-change/CAGR independently recomputed and matched: {all_match} -- {'OK' if all_match else 'FAIL'}")
    assert all_match, "Independent recomputation mismatch -- do not proceed."

    # F. generation-mix share residuals
    print("F. Generation-mix share residual (Coal+Gas+OtherFossil+Nuclear+Renewables - 100), by country/year:")
    max_abs_residual = 0.0
    for iso3, (res15, res25) in residuals.items():
        max_abs_residual = max(max_abs_residual, abs(res15), abs(res25))
        flag = ""
        if abs(res15) > SHARE_RESIDUAL_INVESTIGATE_THRESHOLD or abs(res25) > SHARE_RESIDUAL_INVESTIGATE_THRESHOLD:
            flag = "  <-- INVESTIGATE"
        print(f"  {iso3}: 2015 residual={res15:+.4f} pp, 2025 residual={res25:+.4f} pp{flag}")
    print(f"  Max absolute residual across all countries/years: {max_abs_residual:.4f} pp")

    # G. implausible percentage-point transitions (sanity band, not a hard error)
    print("G. Percentage-point changes outside a +/-60pp sanity band (flagged for review, not auto-rejected):")
    pp_cols = ["coal_pp_change", "gas_other_fossil_pp_change", "nuclear_pp_change", "renewables_pp_change"]
    flagged_any = False
    for _, r in summary.iterrows():
        for col in pp_cols:
            if abs(r[col]) > 60:
                flagged_any = True
                print(f"  {r['country']} {col} = {r[col]:+.2f} pp")
    if not flagged_any:
        print("  None.")

    # H. exactly-zero / near-zero classification metrics
    exact_zero = summary[(summary["demand_pct_change"] == 0) | (summary["intensity_pct_change"] == 0)]
    print(f"H. Exactly-zero classification metrics: {len(exact_zero)} row(s).")
    if len(exact_zero):
        print(exact_zero[["country", "demand_pct_change", "intensity_pct_change"]].to_string(index=False))

    print("\nAll validation checks passed.")


def print_spot_check(summary: pd.DataFrame, iso3: str) -> None:
    r = summary[summary["iso3"] == iso3].iloc[0]
    print(f"\n--- Manual spot check: {r['country']} ({iso3}) ---")
    print(f"Demand {START_YEAR}:  {r['demand_2015_twh']:.2f} TWh")
    print(f"Demand {END_YEAR}:  {r['demand_2025_twh']:.2f} TWh")
    print(
        f"Demand % change = (({r['demand_2025_twh']:.2f} / {r['demand_2015_twh']:.2f}) - 1) * 100 "
        f"= {r['demand_pct_change']:.4f}%"
    )
    print(
        f"Demand CAGR = (({r['demand_2025_twh']:.2f} / {r['demand_2015_twh']:.2f}) ** (1/10) - 1) * 100 "
        f"= {r['demand_cagr_pct']:.4f}%"
    )
    print(f"Intensity {START_YEAR}: {r['intensity_2015_gco2e_kwh']:.3f} gCO2e/kWh")
    print(f"Intensity {END_YEAR}: {r['intensity_2025_gco2e_kwh']:.3f} gCO2e/kWh")
    print(
        f"Intensity % change = (({r['intensity_2025_gco2e_kwh']:.3f} / {r['intensity_2015_gco2e_kwh']:.3f}) - 1) * 100 "
        f"= {r['intensity_pct_change']:.4f}%"
    )
    print(f"Intensity trend slope (OLS, 11 points 2015-2025): {r['intensity_trend_slope_gco2e_kwh_per_year']:.4f} gCO2e/kWh per year")
    print(f"Coal share change: {r['coal_share_2015_pct']:.3f}% -> {r['coal_share_2025_pct']:.3f}% = {r['coal_pp_change']:+.3f} pp")
    print(
        f"Gas+Other fossil share change: {r['gas_other_fossil_share_2015_pct']:.3f}% -> "
        f"{r['gas_other_fossil_share_2025_pct']:.3f}% = {r['gas_other_fossil_pp_change']:+.3f} pp"
    )
    print(f"Nuclear share change: {r['nuclear_share_2015_pct']:.3f}% -> {r['nuclear_share_2025_pct']:.3f}% = {r['nuclear_pp_change']:+.3f} pp")
    print(
        f"Renewables share change: {r['renewables_share_2015_pct']:.3f}% -> "
        f"{r['renewables_share_2025_pct']:.3f}% = {r['renewables_pp_change']:+.3f} pp"
    )
    print(f"Outcome quadrant: {r['outcome_quadrant']}")
    print(f"Endpoint-sensitive (intensity): {r['intensity_endpoint_sensitive']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    df = load_clean()
    print(f"Loaded cleaned dataset: {df.shape[0]} rows, {df['iso3'].nunique()} countries.")

    rows = []
    residuals = {}
    for iso3 in sorted(df["iso3"].unique()):
        country = df[df["iso3"] == iso3]["country"].iloc[0]
        row = {"country": country, "iso3": iso3}
        row.update(compute_demand_metrics(df, iso3))
        row.update(compute_intensity_metrics(df, iso3))
        mix, res15, res25 = compute_mix_metrics(df, iso3)
        row.update(mix)
        residuals[iso3] = (res15, res25)

        row["outcome_quadrant"] = classify(row["demand_pct_change"], row["intensity_pct_change"])
        row["intensity_endpoint_sensitive"] = is_endpoint_sensitive(
            row["intensity_pct_change"], row["intensity_trend_slope_gco2e_kwh_per_year"]
        )
        rows.append(row)

    summary = pd.DataFrame(rows).sort_values("demand_2025_twh", ascending=False).reset_index(drop=True)

    check_near_zero_metrics(summary)
    validate_summary(summary, residuals)

    selected_iso3, reasons = select_chart3_countries(summary)
    summary["selected_for_trend_chart"] = summary["iso3"].isin(selected_iso3)

    print("\n=== Chart 3 country selection (rule-based) ===")
    for iso3 in selected_iso3:
        country = summary[summary["iso3"] == iso3]["country"].iloc[0]
        print(f"  {country} ({iso3}): {reasons[iso3]}")

    print("\n=== Manual spot checks ===")
    for iso3 in ["CHN", "USA", "IND"]:
        print_spot_check(summary, iso3)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_PATH, index=False)

    print("\n=== RESULT TABLE (all 10 countries, sorted by 2025 demand) ===")
    display_cols = [
        "country", "demand_pct_change", "intensity_pct_change",
        "intensity_trend_slope_gco2e_kwh_per_year", "coal_pp_change",
        "gas_other_fossil_pp_change", "nuclear_pp_change", "renewables_pp_change",
        "outcome_quadrant", "intensity_endpoint_sensitive",
    ]
    with pd.option_context("display.max_rows", None, "display.width", 200, "display.float_format", "{:.2f}".format):
        print(summary[display_cols].to_string(index=False))

    print(f"\nOutput written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except (AnalysisError, FileNotFoundError, AssertionError) as exc:
        print(f"\nANALYSIS FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
