from ingestion import load_filing
from unittest.mock import MagicMock
import psycopg2

def test_load_filing_skipped():
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_conn.cursor.return_value = mock_cur

    mock_cur.rowcount = 0

    filing_data = {
        "issuerName": "Apple Inc.",
        "reportingOwner": "Tim Cook",
        "reportingOwnerCik": 1513142,
        "aff10b5One": True,
        "transactions": []
    }

    result = load_filing(mock_conn, filing_data, 320193, "AAPL", "0000320193-24-000001", "2024-01-01")

    assert result["skipped"] == True
    assert result["transactions_inserted"] == 0

def test_load_filing_inserted():
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_conn.cursor.return_value = mock_cur

    mock_cur.rowcount = 1

    filing_data = {
        "issuerName": "Apple Inc.",
        "reportingOwner": "Tim Cook",
        "reportingOwnerCik": 1513142,
        "aff10b5One": True,
        "transactions": [{"code": "P", "shares": 100.0, "price": 150.00, "disposed_code": "A"}]
    }

    result = load_filing(mock_conn, filing_data, 320193, "AAPL", "0000320193-24-000001", "2024-01-01")

    assert result["skipped"] == False
    assert result["transactions_inserted"] == 1

def test_load_filing_db_error():
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_conn.cursor.return_value = mock_cur
    mock_cur.execute.side_effect = psycopg2.DatabaseError("database failed")

    filing_data = {
        "issuerName": "Apple Inc.",
        "reportingOwner": "Tim Cook",
        "reportingOwnerCik": 1513142,
        "aff10b5One": True,
        "transactions": [{"code": "P", "shares": 100.0, "price": 150.00, "disposed_code": "A"}]
    }

    result = load_filing(mock_conn, filing_data, 320193, "AAPL", "0000320193-24-000001", "2024-01-01")

    assert result is None
    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()