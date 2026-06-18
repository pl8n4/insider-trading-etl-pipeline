# insider-trading-etl-pipeline

An ETL pipeline that extracts insider-trading data from **SEC EDGAR Form 4** filings,
transforms the XML into structured records, and loads them into a PostgreSQL database.

## How it works

- **Extract** (`extraction.py`) — builds a ticker→CIK lookup, pulls a company's Form 4 filing history, and parses individual filings.
- **Load** (`ingestion.py`) — upserts issuer/insider/filing rows and inserts the associated transactions into Postgres.
- **Config** (`config.py`) — database connection and SEC EDGAR request headers (loaded from environment).
- **Schema** (`schema.sql`) — PostgreSQL table definitions (`issuer`, `insider`, `filing`, `transactions`).
- **Entry point** (`etl.py`) — example wiring extraction + ingestion together.

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
   - `DB_HOST`, `DB_NAME`, `DB_USER` — your PostgreSQL connection details.

3. Create the PostgreSQL database and load the schema:

   ```bash
   createdb insider_signals
   psql -d insider_signals -f schema.sql
   ```

## Usage

```bash
python etl.py
```
