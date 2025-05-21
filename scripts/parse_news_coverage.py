#!/usr/bin/env python3
"""
Extract TV development / greenlights / renewals / cancellations from
all available Amazon Prime Video news coverage PDFs and display them in a table.
The script scans the ``data/prime_video`` folder for files named
``*_Amazon_News_Coverage.pdf``. Some older PDFs are scans without selectable
text, so they are skipped unless OCR is added.

TODO: Refactor this script into a dynamic dashboard that surfaces insights
about series pickups, renewals, greenlights and projects in development.
The dashboard should help answer questions around deal sourcing, genre trends,
creator experience levels and the mix of new vs. returning shows.

TODO: Refactor this script into a dynamic dashboard that surfaces insights
about series pickups, renewals, greenlights and projects in development.
The dashboard should help answer questions around deal sourcing, genre trends,
creator experience levels and the mix of new vs. returning shows.

Requirements
------------
pip install pdfplumber pandas tabulate
"""

import re
import pdfplumber
import pandas as pd
from tabulate import tabulate
from pathlib import Path

PDF_DIR = Path("data/prime_video")
OUTPUT_XLSX = Path("data") / "parsed_news_coverage.xlsx"

# Collect all news coverage PDFs in the Prime Video folder. Some older PDFs are
# scans with no extractable text, so parsing them will yield zero results.
PDF_PATHS = sorted(PDF_DIR.glob("*_Amazon_News_Coverage.pdf"))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Regex that matches every bullet-pointed title line inside each subsection.
# Handles optional season (S2, S3, etc.) and returns 5 groups:
#   1) title (stripped of brackets like “[working title]”)
#   2) season (e.g. “S3”) or '' if not present
#   3) platform (e.g. “Prime Video”)
#   4) genre (e.g. “fantasy drama”)
#   5) date (mm/dd as shown in the PDF)
ITEM_RE = re.compile(
    r"""
    ^\s*o\s+                                  # leading bullet
    (?P<title>.*?)                            # 1. title (lazy)
    (?:\s+(?P<season>S\d+))?                  # 2. optional “S#”
    \s*:\s*                                   # colon separator
    (?P<platform>[^,]+?)                      # 3. platform (up to first comma)
    ,\s*(?P<genre>.*?)\s*                     # 4. genre
    \((?P<date>\d{1,2}/\d{1,2})\)             # 5. (mm/dd)
    """,
    re.VERBOSE,
)

# Sub-sections we care about
VALID_MODES = {
    "Development",
    "Greenlights",
    "Renewals",
    "Cancellations",
}

# ---------------------------------------------------------------------------
# Scrape all PDFs
# ---------------------------------------------------------------------------

records = []

def parse_pdf(path: Path) -> list[dict]:
    """Return a list of item dicts parsed from a single PDF."""
    year_match = re.search(r"(\d{4})", path.name)
    year = year_match.group(1) if year_match else "2025"

    _records = []
    mode = None
    inside_tv = False

    with pdfplumber.open(path) as pdf:
        pages_with_text = False
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            pages_with_text = True
            for raw_line in text.splitlines():
                line = raw_line.strip()

                # Enter / leave the TV section
                if re.match(r"^TV$", line):
                    inside_tv = True
                    continue
                if inside_tv and re.match(r"^(International|Sports|Deals|Strategy)", line):
                    inside_tv = False  # exited TV section
                    continue
                if not inside_tv:
                    continue

                # Detect subsection headers (bulleted with '•')
                m_header = re.match(r"^•\s+(.*)$", line)
                if m_header:
                    header = m_header.group(1).split(":")[0].strip()
                    mode = header if header in VALID_MODES else None
                    continue

                # If we’re in a relevant subsection, try to parse an item line
                if mode in VALID_MODES:
                    match = ITEM_RE.match(line)
                    if match:
                        title = re.sub(r"\[.*?\]", "", match["title"]).strip()
                        _records.append(
                            {
                                "Title": title,
                                "Season #": (match["season"] or "").lstrip("S"),
                                "Platform": match["platform"].strip(),
                                "Genre": match["genre"].strip(),
                                "Date Announced": f"{match['date'].strip()}/{year}",
                            }
                        )

    if not pages_with_text:
        print(f"Warning: no extractable text in {path.name}, skipping")
    return _records

for path in PDF_PATHS:
    records.extend(parse_pdf(path))

# ---------------------------------------------------------------------------
# Present results
# ---------------------------------------------------------------------------

df = pd.DataFrame(records)
if not df.empty:
    df["_sort_date"] = pd.to_datetime(df["Date Announced"], errors="coerce")
    df = df.sort_values("_sort_date").drop(columns="_sort_date")

df.to_excel(OUTPUT_XLSX, index=False)
print(f"Saved results to {OUTPUT_XLSX}")

print(tabulate(df, headers="keys", showindex=False, tablefmt="github"))

