"""
visualize.py

Reads outputs/country_summary.csv and data/processed/clean_annual_country_source.csv
and produces the three final figures.
Recalculates nothing except what's structurally required to plot an annual
series (i.e. pulling the 11-year Demand/Total generation rows for the 4
Chart-3 countries) -- every headline number plotted comes straight from
country_summary.csv, the single source of truth.

Outputs:
    figures/fig1_demand_vs_intensity_quadrant.png
    figures/fig2_generation_mix_transition.png
    figures/fig3_selected_country_trends.png

Usage:
    python src/visualize.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
SUMMARY_PATH = REPO_ROOT / "outputs" / "country_summary.csv"
CLEAN_PATH = REPO_ROOT / "data" / "processed" / "clean_annual_country_source.csv"
FIGURES_DIR = REPO_ROOT / "figures"

START_YEAR = 2015
END_YEAR = 2025

SOURCE_NOTE = "Source: Ember Yearly Electricity Data (CC BY 4.0). Independent analysis by Vihal Thatipamula — not affiliated with or endorsed by Ember or CREA."

# Consistent country ordering used across figures 1 and 2: by 2025 demand,
# descending -- the same rank order the country-selection rule itself used.
DEMAND_RANK_COLOR = "#22313a"


class VizError(Exception):
    pass


# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------

def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#444444",
            "axes.labelcolor": "#222222",
            "text.color": "#222222",
            "xtick.color": "#333333",
            "ytick.color": "#333333",
            "axes.grid": False,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


# ---------------------------------------------------------------------------
# Loading + validation
# ---------------------------------------------------------------------------

def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not SUMMARY_PATH.exists():
        raise FileNotFoundError(f"{SUMMARY_PATH} not found. Run src/analyze.py first.")
    if not CLEAN_PATH.exists():
        raise FileNotFoundError(f"{CLEAN_PATH} not found. Run src/clean_data.py first.")
    summary = pd.read_csv(SUMMARY_PATH)
    clean = pd.read_csv(CLEAN_PATH)

    if len(summary) != 10:
        raise VizError(f"Expected 10 countries in country_summary.csv, found {len(summary)}.")

    return summary, clean


def validate_before_plotting(summary: pd.DataFrame, clean: pd.DataFrame) -> dict:
    """Validate data structures and counts before plotting. Returns quadrant counts."""
    counts = summary["outcome_quadrant"].value_counts().to_dict()
    expected = {
        "Demand Up / Intensity Down": 5,
        "Demand Up / Intensity Up": 2,
        "Demand Down / Intensity Down": 3,
    }
    for quadrant, n in expected.items():
        actual = counts.get(quadrant, 0)
        if actual != n:
            raise VizError(f"Quadrant count mismatch for '{quadrant}': expected {n}, found {actual}.")
    if counts.get("Demand Down / Intensity Up", 0) != 0:
        raise VizError("Expected 0 countries in 'Demand Down / Intensity Up'; found otherwise.")
    print(f"Quadrant counts verified against country_summary.csv: {counts}")

    selected = summary[summary["selected_for_trend_chart"]]
    if len(selected) != 4:
        raise VizError(f"Expected exactly 4 countries flagged selected_for_trend_chart, found {len(selected)}.")
    print(f"Chart 3 countries verified: {sorted(selected['country'].tolist())}")

    years_present = sorted(clean["year"].unique())
    expected_years = list(range(START_YEAR, END_YEAR + 1))
    if years_present != expected_years:
        raise VizError(f"Expected years {expected_years} in clean data, found {years_present}.")
    print(f"Year coverage verified: {years_present}")

    japan_row = summary[summary["country"] == "Japan"].iloc[0]
    print(f"Japan demand_pct_change (must remain data-accurate, ~flat): {japan_row['demand_pct_change']:.4f}%")

    return counts


# ---------------------------------------------------------------------------
# Figure 1 -- primary quadrant scatter
# ---------------------------------------------------------------------------

# Manually tuned per-country label offsets (points) to avoid overlapping text.
FIG1_LABEL_OFFSETS = {
    "China": (10, 6),
    "United States": (10, -12),
    "India": (10, 8),
    "Russia": (10, 8),
    "Japan": (-95, 26),
    "Brazil": (10, -12),
    "Canada": (-46, 8),
    "South Korea": (12, -16),
    "Germany": (-14, -16),
    "France": (10, 10),
}


def make_fig1(summary: pd.DataFrame, counts: dict) -> None:
    up_down_n = counts.get("Demand Up / Intensity Down", 0)

    fig, ax = plt.subplots(figsize=(10, 7.4), dpi=200)
    fig.subplots_adjust(top=0.74, bottom=0.10, left=0.085, right=0.97)

    x = summary["demand_pct_change"].to_numpy()
    y = summary["intensity_pct_change"].to_numpy()

    xpad = (x.max() - x.min()) * 0.15
    ypad = (y.max() - y.min()) * 0.18
    xlim = (x.min() - xpad, x.max() + xpad)
    ylim = (y.min() - ypad, y.max() + ypad)

    ax.axhline(0, color="#888888", linewidth=1, zorder=1)
    ax.axvline(0, color="#888888", linewidth=1, zorder=1)

    ax.scatter(x, y, s=70, color=DEMAND_RANK_COLOR, edgecolor="white", linewidth=1.2, zorder=3)

    for _, row in summary.iterrows():
        label = row["country"]
        if label == "Japan":
            label = "Japan (≈0% demand chg.)"
        dx, dy = FIG1_LABEL_OFFSETS[row["country"]]
        ax.annotate(
            label,
            (row["demand_pct_change"], row["intensity_pct_change"]),
            textcoords="offset points",
            xytext=(dx, dy),
            fontsize=9.5,
            color="#111111",
            zorder=4,
        )

    # Quadrant labels, placed in each corner using axes-fraction coordinates
    # so quadrant membership is legible without relying on color at all.
    quadrant_label_style = dict(fontsize=9.5, color="#555555", style="italic", ha="left")
    ax.text(0.02, 0.03, f"Demand ↓ / Intensity ↓  ({counts.get('Demand Down / Intensity Down', 0)} countries)",
            transform=ax.transAxes, va="bottom", **quadrant_label_style)
    ax.text(0.02, 0.97, f"Demand ↓ / Intensity ↑  ({counts.get('Demand Down / Intensity Up', 0)} countries)",
            transform=ax.transAxes, va="top", **quadrant_label_style)
    ax.text(0.98, 0.97, f"Demand ↑ / Intensity ↑  ({counts.get('Demand Up / Intensity Up', 0)} countries)",
            transform=ax.transAxes, va="top", ha="right",
            fontsize=9.5, color="#555555", style="italic")
    ax.text(0.98, 0.03, f"Demand ↑ / Intensity ↓  ({counts.get('Demand Up / Intensity Down', 0)} countries)",
            transform=ax.transAxes, va="bottom", ha="right",
            fontsize=9.5, color="#555555", style="italic")

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_xlabel("Electricity demand change, 2015–2025 (%)", fontsize=11.5)
    ax.set_ylabel("Power-sector emissions-intensity change, 2015–2025 (%)", fontsize=11.5)

    fig.text(
        0.02, 0.965,
        f"{up_down_n} of the ten largest electricity markets grew demand while lowering",
        fontsize=15, fontweight="bold", ha="left", va="top",
    )
    fig.text(
        0.02, 0.925,
        "power-sector emissions intensity between 2015 and 2025",
        fontsize=15, fontweight="bold", ha="left", va="top",
    )
    fig.text(
        0.02, 0.875,
        "2015–2025 change among the ten largest electricity markets by 2025 electricity demand.",
        fontsize=10.5, color="#444444", ha="left", va="top",
    )
    fig.text(
        0.02, 0.845,
        "Emissions intensity is a power-sector average (gCO2e/kWh); this describes an observed pattern, not a causal effect.",
        fontsize=10.5, color="#444444", ha="left", va="top",
    )

    fig.text(0.02, 0.02, SOURCE_NOTE, fontsize=8, color="#666666", ha="left", va="bottom")
    out_path = FIGURES_DIR / "fig1_demand_vs_intensity_quadrant.png"
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"Saved {out_path}")


# ---------------------------------------------------------------------------
# Figure 2 -- generation-mix transition
# ---------------------------------------------------------------------------

MIX_CATEGORIES = [
    ("coal_pp_change", "Coal", "#3d3d3d", None),
    ("gas_other_fossil_pp_change", "Gas + Other fossil", "#c97a2b", "//"),
    ("nuclear_pp_change", "Nuclear", "#6a51a3", "xx"),
    ("renewables_pp_change", "Renewables", "#2e8b57", ".."),
]


def make_fig2(summary: pd.DataFrame) -> None:
    # Sort by 2025 demand descending -- preserves the project's own selection
    # ranking so the country order is consistent with Figures 1 and the
    # README, rather than introducing a second, unexplained ordering.
    ordered = summary.sort_values("demand_2025_twh", ascending=True).reset_index(drop=True)
    countries = ordered["country"].tolist()
    n = len(countries)

    fig, ax = plt.subplots(figsize=(10, 9), dpi=200)
    fig.subplots_adjust(top=0.78, bottom=0.08, left=0.14, right=0.97)

    bar_height = 0.19
    group_gap = 0.0
    offsets = np.linspace(-1.5, 1.5, len(MIX_CATEGORIES)) * bar_height

    y_base = np.arange(n)

    for (col, label, color, hatch), offset in zip(MIX_CATEGORIES, offsets):
        values = ordered[col].to_numpy()
        ax.barh(
            y_base + offset,
            values,
            height=bar_height,
            color=color,
            hatch=hatch,
            edgecolor="white",
            linewidth=0.6,
            label=label,
            zorder=3,
        )

    ax.axvline(0, color="#444444", linewidth=1.2, zorder=2)
    ax.set_yticks(y_base)
    ax.set_yticklabels(countries, fontsize=11)
    ax.set_ylim(-0.7, n - 0.3)

    all_vals = ordered[[c for c, _, _, _ in MIX_CATEGORIES]].to_numpy().flatten()
    pad = (all_vals.max() - all_vals.min()) * 0.08
    ax.set_xlim(all_vals.min() - pad, all_vals.max() + pad)

    ax.set_xlabel("Change in share of total generation, 2015–2025 (percentage points)", fontsize=11.5)
    ax.xaxis.set_major_formatter(lambda v, pos: f"{v:+.0f}pp" if v != 0 else "0")

    legend_handles = [
        mpatches.Patch(facecolor=color, hatch=hatch, edgecolor="white", label=label)
        for _, label, color, hatch in MIX_CATEGORIES
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper center", bbox_to_anchor=(0.55, 0.825), ncol=4, frameon=False, fontsize=10.5,
        handlelength=1.8, columnspacing=1.6, bbox_transform=fig.transFigure,
    )

    fig.text(
        0.02, 0.965, "Generation mixes shifted in very different ways across major electricity markets",
        fontsize=15, fontweight="bold", ha="left", va="top",
    )
    fig.text(
        0.02, 0.905,
        "Percentage-point change in each fuel category's share of total generation, 2015–2025.",
        fontsize=10.5, color="#444444", ha="left", va="top",
    )
    fig.text(
        0.02, 0.878,
        "Countries ordered by 2025 electricity demand (highest at top).",
        fontsize=10.5, color="#444444", ha="left", va="top",
    )

    fig.text(0.02, 0.015, SOURCE_NOTE, fontsize=8, color="#666666", ha="left", va="bottom")

    out_path = FIGURES_DIR / "fig2_generation_mix_transition.png"
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"Saved {out_path}")


# ---------------------------------------------------------------------------
# Figure 3 -- full 2015-2025 trends for the 4 rule-selected countries
# ---------------------------------------------------------------------------

def make_fig3(summary: pd.DataFrame, clean: pd.DataFrame) -> None:
    selected = summary[summary["selected_for_trend_chart"]].sort_values("demand_2025_twh", ascending=False)
    iso3_list = selected["iso3"].tolist()
    countries = selected["country"].tolist()

    fig, axes = plt.subplots(2, len(iso3_list), figsize=(14, 7.4), dpi=200, sharex=True)
    fig.subplots_adjust(top=0.72, bottom=0.11, left=0.06, right=0.98, hspace=0.35, wspace=0.32)

    for col_idx, (iso3, country) in enumerate(zip(iso3_list, countries)):
        demand_series = clean[
            (clean["iso3"] == iso3) & (clean["electricity_source"] == "Demand")
        ].sort_values("year")
        intensity_series = clean[
            (clean["iso3"] == iso3) & (clean["electricity_source"] == "Total generation")
        ].sort_values("year")

        ax_top = axes[0, col_idx]
        ax_bot = axes[1, col_idx]

        ax_top.plot(
            demand_series["year"], demand_series["generation_twh"],
            marker="o", markersize=4, color="#22313a", linewidth=1.8,
        )
        ax_bot.plot(
            intensity_series["year"], intensity_series["emissions_intensity_gco2e_kwh"],
            marker="o", markersize=4, color="#b5461f", linewidth=1.8,
        )

        ax_top.set_title(country, fontsize=12, fontweight="bold", pad=8)
        ax_top.margins(y=0.18)
        ax_bot.margins(y=0.18)

        for ax in (ax_top, ax_bot):
            ax.set_xticks([2015, 2020, 2025])
            ax.tick_params(axis="x", labelsize=9)
            ax.tick_params(axis="y", labelsize=9)

        if col_idx == 0:
            ax_top.set_ylabel("Demand (TWh)", fontsize=10.5)
            ax_bot.set_ylabel("Emissions intensity\n(gCO2e/kWh)", fontsize=10.5)

    fig.text(
        0.02, 0.965,
        "Annual demand and emissions-intensity trajectories, 2015–2025: the four countries",
        fontsize=14.5, fontweight="bold", ha="left", va="top",
    )
    fig.text(
        0.02, 0.925,
        "selected by the rule-based procedure (highest 2025 demand per occupied quadrant, then fill by demand)",
        fontsize=14.5, fontweight="bold", ha="left", va="top",
    )
    fig.text(
        0.02, 0.875,
        "Each country has its own scale (units are identical across countries; magnitudes are not directly\n"
        "comparable at a glance). Shown to check the 2015–2025 endpoint comparison against the full annual path.",
        fontsize=10, color="#444444", ha="left", va="top",
    )
    fig.text(0.02, 0.02, SOURCE_NOTE, fontsize=8, color="#666666", ha="left", va="bottom")

    out_path = FIGURES_DIR / "fig3_selected_country_trends.png"
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"Saved {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    apply_style()
    summary, clean = load_data()
    counts = validate_before_plotting(summary, clean)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    make_fig1(summary, counts)
    make_fig2(summary)
    make_fig3(summary, clean)

    print("\nAll three figures generated successfully.")


if __name__ == "__main__":
    try:
        main()
    except (VizError, FileNotFoundError) as exc:
        print(f"\nVISUALIZATION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
