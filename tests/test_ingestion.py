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
        "issuerCik": 320193,
        "issuerTradingSymbol": "AAPL",
        "reportingOwner": "Tim Cook",
        "reportingOwnerCik": 1513142,
        "isDirector": True,
        "isOfficer": True,
        "isTenPercentOwner": False,
        "isOther": False,
        "officerTitle": "Chief Executive Officer",
        "aff10b5One": True,
        "footnotes": {},
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
        "issuerCik": 320193,
        "issuerTradingSymbol": "AAPL",
        "reportingOwner": "Tim Cook",
        "reportingOwnerCik": 1513142,
        "isDirector": True,
        "isOfficer": True,
        "isTenPercentOwner": False,
        "isOther": False,
        "officerTitle": "Chief Executive Officer",
        "aff10b5One": True,
        "footnotes": {"F1": "Open-market purchase."},
        "transactions": [{"code": "P",
                          "securityTitle": "Common Stock",
                          "shares": 100.0,
                          "price": 150.00,
                          "disposed_code": "A",
                          "sharesOwnedFollowing": 5000.0,
                          "directOrIndirectOwnership": "D",
                          "footnoteIds": ["F1"]}]
    }

    result = load_filing(mock_conn, filing_data, 320193, "AAPL", "0000320193-24-000001", "2024-01-01")

    assert result["skipped"] == False
    assert result["transactions_inserted"] == 1
    assert mock_cur.execute.call_args_list[0].args[1] == (320193, "Apple Inc.", "AAPL")
    assert mock_cur.execute.call_args_list[3].args[1] == ("0000320193-24-000001", "P", "Common Stock", 100.0, 150.00, "A", 5000.0, "D", ["F1"])

def test_load_filing_uses_xml_issuer():
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_conn.cursor.return_value = mock_cur

    mock_cur.rowcount = 0

    filing_data = {
        "issuerName": "Aditxt Inc.",
        "issuerCik": 1726711,
        "issuerTradingSymbol": "ADTX",
        "reportingOwner": "BANK OF AMERICA CORP /DE/",
        "reportingOwnerCik": 70858,
        "isDirector": False,
        "isOfficer": False,
        "isTenPercentOwner": True,
        "isOther": False,
        "officerTitle": None,
        "aff10b5One": None,
        "footnotes": {},
        "transactions": []
    }

    load_filing(mock_conn, filing_data, 70858, "BAC", "0000070858-26-000336", "2026-06-01")

    assert mock_cur.execute.call_args_list[0].args[1] == (1726711, "Aditxt Inc.", "ADTX")

def test_load_filing_db_error():
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_conn.cursor.return_value = mock_cur
    mock_cur.execute.side_effect = psycopg2.DatabaseError("database failed")

    filing_data = {
        "issuerName": "Apple Inc.",
        "issuerCik": 320193,
        "issuerTradingSymbol": "AAPL",
        "reportingOwner": "Tim Cook",
        "reportingOwnerCik": 1513142,
        "isDirector": True,
        "isOfficer": True,
        "isTenPercentOwner": False,
        "isOther": False,
        "officerTitle": "Chief Executive Officer",
        "aff10b5One": True,
        "footnotes": {},
        "transactions": [{"code": "P",
                          "securityTitle": "Common Stock",
                          "shares": 100.0,
                          "price": 150.00,
                          "disposed_code": "A",
                          "sharesOwnedFollowing": 5000.0,
                          "directOrIndirectOwnership": "D",
                          "footnoteIds": []}]
    }

    result = load_filing(mock_conn, filing_data, 320193, "AAPL", "0000320193-24-000001", "2024-01-01")

    assert result is None
    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()
