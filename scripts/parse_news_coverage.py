#!/usr/bin/env python3
"""
Extract TV development / greenlights / renewals / cancellations from
Amazon Prime Video news coverage Word documents and display them in a table.
The script scans the ``data/prime_video`` folder for ``*.docx`` files
exported from the quarterly coverage PDFs.

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
pip install pandas tabulate  # pdfplumber no longer required
"""

import re
import pandas as pd
from tabulate import tabulate
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

DOC_DIR = Path("data/prime_video")
OUTPUT_XLSX = Path("data") / "parsed_news_coverage.xlsx"

# Collect all news coverage Word docs in the Prime Video folder.
DOCX_PATHS = sorted(DOC_DIR.glob("*.docx"))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Regex that matches every bullet-pointed title line inside each subsection.
# Handles optional season (S2, S3, etc.) and returns 5 groups:
#   1) title (stripped of brackets like “[working title]”)
#   2) season (e.g. “S3”) or '' if not present
#   3) platform (e.g. “Prime Video”)
#   4) genre (e.g. “fantasy drama”)
#   5) date (mm/dd as shown in the doc)
ITEM_RE = re.compile(
    r"""
    ^(?P<title>.*?)                           # 1. title (lazy)
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
# Scrape all Word docs
# ---------------------------------------------------------------------------

records = []

def iter_docx_lines(path: Path):
    """Yield plain text lines from a ``.docx`` file."""
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    for p in root.findall(".//w:p", ns):
        texts = [t.text for t in p.findall('.//w:t', ns) if t.text]
        if texts:
            yield ''.join(texts)

def parse_docx(path: Path) -> list[dict]:
    """Return a list of item dicts parsed from a single Word document."""
    year_match = re.search(r"(\d{4})", path.name)
    year = year_match.group(1) if year_match else "2025"

    _records = []
    mode = None
    inside_tv = False

    lines = list(iter_docx_lines(path))
    pages_with_text = bool(lines)
    for raw_line in lines:
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

        # Detect subsection headers
        m_header = re.match(r"^•\s+(.*)$", line)
        if m_header:
            header = m_header.group(1).split(":")[0].strip()
            mode = header if header in VALID_MODES else None
            continue
        if line in VALID_MODES:
            mode = line
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

for path in DOCX_PATHS:
    records.extend(parse_docx(path))

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

