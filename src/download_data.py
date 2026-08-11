"""
download_data.py

Downloads Ember's Yearly Electricity Data (global CSV) and caches it under
data/raw/. Verifies the response actually looks like the expected dataset
before trusting it, and reports the information needed to keep
data/raw/PROVENANCE.md accurate.

Source:  https://ember-energy.org/data/yearly-electricity-data/
License: CC BY 4.0 (Ember Energy Research CIC)

Usage:
    python src/download_data.py

This script does not overwrite data/raw/PROVENANCE.md automatically -- it
prints the values (URL, access date, size, sha256) so they can be compared
against what's already recorded there. If they differ (Ember re-releases
the file between now and when you run this), update PROVENANCE.md by hand
and re-run the rest of the pipeline, rather than silently trusting a new
file against old documentation.
"""

from __future__ import annotations

import hashlib
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import requests

SOURCE_URL = (
    "https://files.ember-energy.org/public-downloads/generation/outputs/"
    "release_generation_yearly_global.csv"
)

# Column we expect to see first in the header row. If Ember changes their
# schema, this check fails loudly instead of letting a differently-shaped
# file flow silently into the rest of the pipeline.
EXPECTED_HEADER_PREFIX = "Area,ISO 3 code,Year,Area type,Electricity source"

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
OUTPUT_PATH = RAW_DIR / "release_generation_yearly_global.csv"


def download(url: str = SOURCE_URL, output_path: Path = OUTPUT_PATH) -> Path:
    """Download the Ember CSV and save it to output_path. Returns the path."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Downloading: {url}")
    response = requests.get(url, timeout=60, stream=True)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)

    return output_path


def verify(path: Path) -> dict:
    """
    Sanity-check the downloaded file and return a small provenance record.
    Raises if the file doesn't look like the dataset we expect.
    """
    if not path.exists():
        raise FileNotFoundError(f"Expected downloaded file at {path}, found nothing.")

    with open(path, "r", encoding="utf-8", errors="strict") as f:
        header = f.readline().strip()

    if not header.startswith(EXPECTED_HEADER_PREFIX):
        raise ValueError(
            "Downloaded file does not start with the expected header. "
            "Ember may have changed the schema -- do not proceed to "
            "clean_data.py until this is investigated.\n"
            f"Expected prefix: {EXPECTED_HEADER_PREFIX!r}\n"
            f"Got:              {header!r}"
        )

    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(chunk)

    size_bytes = path.stat().st_size
    with open(path, "r", encoding="utf-8", errors="strict") as f:
        row_count = sum(1 for _ in f) - 1  # exclude header

    return {
        "url": SOURCE_URL,
        "access_date": date.today().isoformat(),
        "size_bytes": size_bytes,
        "sha256": sha256.hexdigest(),
        "row_count": row_count,
    }


def main() -> None:
    path = download()
    info = verify(path)

    print()
    print("Download verified. Compare these values against data/raw/PROVENANCE.md:")
    print(f"  URL:          {info['url']}")
    print(f"  Access date:  {info['access_date']}")
    print(f"  Size (bytes): {info['size_bytes']:,}")
    print(f"  SHA-256:      {info['sha256']}")
    print(f"  Data rows:    {info['row_count']:,}")
    print()
    print(f"Saved to: {path}")


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        print(f"Download failed: {exc}", file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        print(f"Schema check failed: {exc}", file=sys.stderr)
        sys.exit(1)
