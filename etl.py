from config import TICKERS, get_connection
from extraction import get_filing, get_filing_history, build_cik_lookup
from ingestion import load_filing

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pipeline.log")
    ]
)

logger = logging.getLogger(__name__)


conn = None

try:
    conn = get_connection()
    
    logger.info("Starting pipeline run")
    logger.info("Building CIK lookup table")
    
    lookup = build_cik_lookup()

    filings_inserted = 0
    filings_skipped = 0
    transactions_inserted = 0
    error_count = 0

    for ticker in TICKERS:
        logger.info(f"Processing ticker: {ticker}")
        issuer_cik = lookup[ticker]
        # Change starting date to modify how far back the filings ingested go
        filings = get_filing_history(issuer_cik, "2026-01-01")

        for filing in filings:
            try: 
                filing_data = get_filing(issuer_cik, filing['accessionNumber'], filing['primaryDocument'])
                result = load_filing(conn, filing_data, issuer_cik, ticker, filing['accessionNumber'], filing['filingDate'])
                if result["skipped"]:
                    filings_skipped += 1
                    logger.info(f" Skipped (duplicate): {filing['accessionNumber']}")
                else:
                    filings_inserted += 1
                    transactions_inserted += result["transactions_inserted"]
                    logger.info(f" Inserted: {filing['accessionNumber']} - {result['transactions_inserted']} transactions")
            except Exception as e:
                logger.error(f" Error on {filing['accessionNumber']}: {e}")
                error_count += 1

    
    logger.info("Pipeline run complete")
    logger.info(f"Filings inserted: {filings_inserted} | Skipped: {filings_skipped} | Transactions inserted: {transactions_inserted} | Errors: {error_count}")
finally:
    if conn is not None:
        conn.close()
