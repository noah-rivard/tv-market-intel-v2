# TV Market Intel

This project aims to gather and analyze strategic insights across the television landscape. At the moment the data focuses solely on **Amazon Prime Video** news coverage over the last year.

## Repository structure

- `data/prime_video/` – Raw news coverage PDFs and spreadsheets for Prime Video.
- `scripts/` – Utility scripts for parsing and analyzing the data.
- `docs/` – Additional documentation.
- `src/` – Future Python modules for the analysis app.

## Getting started

Install dependencies:

```bash
pip install -r requirements.txt
```

Then run the parser script:

```bash
python scripts/parse_news_coverage.py
```

## Development

Validate the code and run tests:

```bash
python -m py_compile scripts/parse_news_coverage.py
pytest -q
```

`pytest` is included for future tests and will currently report that no tests are found.

## TODO

Create a dynamic dashboard-style app to surface strategic insights about the TV landscape.
This tool should eventually allow users to answer questions such as:

- Where are studios sourcing their series from (overall deals, first-look deals, pod deals)?
- What genres and formats are over- and under-indexed?
- What percentage of orders come from proven creators vs. emerging voices?
- What is the makeup of new series, returning series and cancelled series in the past 12/24 months?

These insights will be derived from parsed data on series pickups, renewals, greenlights and development activity.

## Known Limitations

Older Amazon Prime Video PDFs in `data/prime_video/` are scans without selectable
text. The parser skips these files and therefore currently extracts data only
from digital PDFs. Adding OCR support would enable pulling data from the scanned
documents as well.

