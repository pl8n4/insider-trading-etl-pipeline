from extraction import get_cik, parse_filing, get_filing, build_cik_lookup, get_filing_history
from unittest.mock import patch, MagicMock
from config import EDGAR_HEADERS

SAMPLE_XML = """<ownershipDocument>
    <issuer>
        <issuerCik>0000320193</issuerCik>
        <issuerName>Apple Inc.</issuerName>
        <issuerTradingSymbol>AAPL</issuerTradingSymbol>
    </issuer>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerName>Tim Cook</rptOwnerName>
            <rptOwnerCik>0001513142</rptOwnerCik>
        </reportingOwnerId>
        <reportingOwnerRelationship>
            <isDirector>true</isDirector>
            <isOfficer>true</isOfficer>
            <isTenPercentOwner>false</isTenPercentOwner>
            <isOther>false</isOther>
            <officerTitle>Chief Executive Officer</officerTitle>
        </reportingOwnerRelationship>
    </reportingOwner>
    <aff10b5One>true</aff10b5One>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <securityTitle>
                <value>Common Stock</value>
            </securityTitle>
            <transactionCoding>
                <transactionCode>P</transactionCode>
            </transactionCoding>
            <transactionAmounts>
                <transactionShares>
                    <value>100.0</value>
                </transactionShares>
                <transactionPricePerShare>
                    <value>150.00</value>
                </transactionPricePerShare>
                <transactionAcquiredDisposedCode>
                    <value>A</value>
                </transactionAcquiredDisposedCode>
            </transactionAmounts>
            <postTransactionAmounts>
                <sharesOwnedFollowingTransaction>
                    <value>5000</value>
                </sharesOwnedFollowingTransaction>
            </postTransactionAmounts>
            <ownershipNature>
                <directOrIndirectOwnership>
                    <value>D</value>
                </directOrIndirectOwnership>
            </ownershipNature>
            <footnoteId id="F1"/>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
    <footnotes>
        <footnote id="F1">Open-market purchase.</footnote>
    </footnotes>
</ownershipDocument>"""

SAMPLE_TICKERS_JSON = {
    "0": {"ticker": "AAPL", "cik_str": "320193"},
    "1": {"ticker": "MSFT", "cik_str": "789019"}
}

SAMPLE_CIK = 320193

SAMPLE_SUBMISSIONS = {
    "filings": {
        "recent": {
            "form":            ["4",                    "10-K",                 "4"],
            "filingDate":      ["2026-03-01",           "2026-03-01",           "2025-12-01"],
            "accessionNumber": ["0000320193-26-000001", "0000320193-26-000002", "0000320193-25-000003"],
            "primaryDocument": ["form4.xml",            "10k.htm",              "form4old.xml"]
        }
    }
}

def test_get_cik_valid_ticker():
    lookup = {"AAPL": 320193, "MSFT": 789019}
    assert get_cik("AAPL", lookup) == 320193

def test_get_cik_invalid_ticker():
    lookup = {"AAPL": 320193, "MSFT": 789019}
    assert get_cik("INVALID", lookup) is None


def test_parse_filing_normal():
    result = parse_filing(SAMPLE_XML)
    assert result['issuerName'] == 'Apple Inc.'
    assert result['issuerCik'] == 320193
    assert result['issuerTradingSymbol'] == 'AAPL'
    assert result['reportingOwner'] == 'Tim Cook'
    assert result['reportingOwnerCik'] == 1513142
    assert result['isDirector'] == True
    assert result['isOfficer'] == True
    assert result['isTenPercentOwner'] == False
    assert result['isOther'] == False
    assert result['officerTitle'] == 'Chief Executive Officer'
    assert result['footnotes'] == {'F1': 'Open-market purchase.'}
    assert len(result['transactions']) == 1
    assert result['transactions'][0]['code'] == 'P'
    assert result['transactions'][0]['securityTitle'] == 'Common Stock'
    assert result['transactions'][0]['shares'] == 100.0
    assert result['transactions'][0]['price'] == 150.00
    assert result['transactions'][0]['disposed_code'] == 'A'
    assert result['transactions'][0]['sharesOwnedFollowing'] == 5000.0
    assert result['transactions'][0]['directOrIndirectOwnership'] == 'D'
    assert result['transactions'][0]['footnoteIds'] == ['F1']

def test_parse_filing_no_aff10b5one():
    SAMPLE_XML_no_aff10b5One = SAMPLE_XML.replace("<aff10b5One>true</aff10b5One>", "")
    assert parse_filing(SAMPLE_XML_no_aff10b5One)['aff10b5One'] == None

def test_parse_filing_false_aff10b5one():
    SAMPLE_XML_false_aff10b5One = SAMPLE_XML.replace("<aff10b5One>true</aff10b5One>", "<aff10b5One>false</aff10b5One>")
    assert parse_filing(SAMPLE_XML_false_aff10b5One)['aff10b5One'] == False

def test_parse_filing_no_price():
    SAMPLE_XML_no_price = SAMPLE_XML.replace("<value>150.00</value>", "")
    assert parse_filing(SAMPLE_XML_no_price)['transactions'][0]['price'] == None

def test_get_filing_URL():
    mock_response = MagicMock()
    mock_response.text = SAMPLE_XML

    with patch("extraction.requests.get", return_value=mock_response) as mock_get:
        get_filing(320193, "0000320193-24-000001", "form4.xml")

    mock_get.assert_called_once_with(
        "https://www.sec.gov/Archives/edgar/data/320193/000032019324000001/form4.xml",
        headers=EDGAR_HEADERS)

def test_build_cik_lookup():
    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_TICKERS_JSON

    with patch("extraction.requests.get", return_value=mock_response) as mock_get:
        lookup = build_cik_lookup()
    mock_get.assert_called_once_with("https://www.sec.gov/files/company_tickers.json", headers=EDGAR_HEADERS)

    assert lookup["AAPL"] == 320193

def test_get_filing_history():
    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_SUBMISSIONS

    with patch("extraction.requests.get", return_value=mock_response):
        results = get_filing_history(320193, "2026-01-01")
    
    assert len(results) == 1
    assert results[0]["accessionNumber"] == "0000320193-26-000001"
