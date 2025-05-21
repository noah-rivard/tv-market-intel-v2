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

