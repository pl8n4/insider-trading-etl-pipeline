from config import get_connection
from extraction import get_cik, get_filing, get_filing_histroy, build_cik_lookup
from ingestion import load_filing

filing_data = {
    "issuerName": "Apple Inc.",
    "reportingOwner": "LEVINSON ARTHUR D",
    "reportingOwnerCik": 1214128,
    "aff10b5One": False,
    "transactions": [
        {"code": "P", "shares": 1000.0, "price": 180.50, "disposed_code": "A"},
        {"code": "S", "shares": 500.0, "price": 182.00, "disposed_code": "D"}
    ]
}

#conn = get_connection()
#load_filing(conn, filing_data, 320193, "AAPL", "0000320193-24-000001", "2024-01-15")
#conn.close()

lookup = build_cik_lookup()

filings = get_filing_histroy(cik)
print(get_filing(cik, filings[0]['accessionNumber'], filings[0]['primaryDocument']))
