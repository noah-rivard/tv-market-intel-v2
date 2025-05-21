#!/usr/bin/env python3
"""
Extract TV development / greenlights / renewals / cancellations from
the latest Amazon Prime Video news coverage PDF and display them in a table.

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

PDF_PATH = Path("data/prime_video/2025_Q1_Amazon_News_Coverage.pdf")
OUTPUT_XLSX = Path("data") / "parsed_news_coverage.xlsx"

# Determine the year from the filename (fallback to 2025 if not found)
_match = re.search(r"(\d{4})", PDF_PATH.name)
YEAR = _match.group(1) if _match else "2025"

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
# Scrape the PDF
# ---------------------------------------------------------------------------

records = []
mode = None
inside_tv = False

with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        for raw_line in text.splitlines():
            line = raw_line.strip()

            # Enter / leave the TV section
            if re.match(r"^TV$", line):
                inside_tv = True
                continue
            if inside_tv and re.match(r"^(International|Sports|Deals|Strategy)", line):
                inside_tv = False     # exited TV section
                continue
            if not inside_tv:
                continue

            # Detect subsection headers (bulleted with '•')
            m_header = re.match(r"^•\s+(.*)$", line)
            if m_header:
                header = m_header.group(1).split(":")[0].strip()  # remove any tail
                mode = header if header in VALID_MODES else None
                continue

            # If we’re in a relevant subsection, try to parse an item line
            if mode in VALID_MODES:
                match = ITEM_RE.match(line)
                if match:
                    title = re.sub(r"\[.*?\]", "", match["title"]).strip()
                    records.append(
                        {
                            "Title": title,
                            "Season #": (match["season"] or "").lstrip("S"),
                            "Platform": match["platform"].strip(),
                            "Genre": match["genre"].strip(),
                            "Date Announced": match["date"].strip(),
                        }
                    )

# ---------------------------------------------------------------------------
# Present results
# ---------------------------------------------------------------------------

df = pd.DataFrame(records)
df = df.sort_values(
    "Date Announced", key=lambda s: pd.to_datetime(s + f"/{YEAR}")
)

df.to_excel(OUTPUT_XLSX, index=False)
print(f"Saved results to {OUTPUT_XLSX}")

print(tabulate(df, headers="keys", showindex=False, tablefmt="github"))

