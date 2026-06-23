# insider-trading-etl-pipeline

An ETL pipeline that extracts insider-trading data from **SEC EDGAR Form 4** filings,
transforms the XML into structured records, and loads them into a PostgreSQL database.

## How it works

- **Extract** (`extraction.py`) — builds a ticker→CIK lookup, pulls a company's Form 4 filing history, and parses individual filings, including owner relationship flags, footnotes, security title, and ownership nature.
- **Load** (`ingestion.py`) — upserts issuer/insider/filing rows and inserts the associated transactions into Postgres. The loader uses the issuer CIK/ticker from the filing XML when present, which avoids labeling reporting-owner filings as the wrong issuer.
- **Config** (`config.py`) — database connection and SEC EDGAR request headers (loaded from environment).
- **Schema** (`schema.sql`) — PostgreSQL table definitions (`issuer`, `insider`, `filing`, `transactions`).
- **Entry point** (`etl.py`) — runs the configured ticker list through extraction and ingestion, logging progress to the console and `pipeline.log`.
- **Tests** (`tests/`) — unit tests for extraction and ingestion behavior using mocks for SEC and database calls.

## Setup

1. Clone the repo and create a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy the example environment file and fill in your values:

   ```bash
   cp .env.example .env
   ```

   - `EDGAR_CONTACT` — SEC EDGAR **requires** a contact email in the `User-Agent`
     header (format: `"Your Name your.email@example.com"`).
   - `DB_HOST`, `DB_NAME`, `DB_USER` — your PostgreSQL connection details. If omitted,
     the app defaults to `localhost`, `insider_signals`, and the user configured in
     `config.py`.

3. Create the PostgreSQL database and load the schema:

   ```bash
   createdb insider_signals
   psql -d insider_signals -f schema.sql
   ```

## Usage

```bash
python etl.py
```

By default, `etl.py` processes the ticker list defined in the file and loads Form 4
filings dated on or after `2026-01-01`.

## Tests

```bash
pytest
```

The tests mock external SEC requests and database connections, so they can run
without network access or a running PostgreSQL instance.
