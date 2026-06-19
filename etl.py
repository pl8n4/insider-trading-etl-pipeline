from config import get_connection
from extraction import get_filing, get_filing_history, build_cik_lookup
from ingestion import load_filing

TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "JPM", "BAC", "GS", "WFC", "MS",
    "JNJ", "PFE", "UNH", "MRK", "ABBV"
    ]

conn = None

try:
    conn = get_connection()

    lookup = build_cik_lookup()

    for ticker in TICKERS:
        issuer_cik = lookup[ticker]
        filings = get_filing_history(issuer_cik, "2026-01-01")

        for filing in filings:
            filing_data = get_filing(issuer_cik, filing['accessionNumber'], filing['primaryDocument'])
        
            load_filing(conn, filing_data, issuer_cik, ticker, filing['accessionNumber'], filing['filingDate'])
finally:
    if conn is not None:
        conn.close()
