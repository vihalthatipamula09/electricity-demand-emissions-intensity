# Data folder

## `raw/`

Holds a cached copy of the Ember Yearly Electricity Data CSV as downloaded by
`src/download_data.py`, plus `PROVENANCE.md`, which records exactly what was
downloaded, from where, and when.

The raw CSV itself is **not committed to this repository** (see `.gitignore`).
It is a large, mechanically reproducible file that Ember updates on its own
schedule — committing a snapshot would let the repo silently drift out of
sync with what `PROVENANCE.md` claims, and would bloat the repository with
data that isn't ours. Anyone cloning this repo regenerates it by running
`python src/download_data.py`, which will fetch the same dataset described
in `PROVENANCE.md` (or a newer one, in which case the provenance file should
be updated and the analysis re-run).

`PROVENANCE.md` and this README *are* committed, so the data source is fully
documented even without the raw file present.

## `processed/`

Holds the cleaned, filtered, analysis-ready dataset produced by
`src/clean_data.py` — restricted to the 10 selected countries and the
2015–2025 window, with standardized country names and validated fields.
This file is small enough to commit and is what `src/analyze.py` reads.

## Licensing note

All data in this folder originates from Ember (Ember Energy Research CIC),
licensed under CC BY 4.0. This repository's own MIT license (see
`/LICENSE`) covers the code that downloads, cleans, and analyzes the data —
not the data itself.
