import requests
import time
import xml.etree.ElementTree as ET
from config import EDGAR_HEADERS


def build_cik_lookup():
    """Build issuer CIK lookup"""
    response = requests.get("https://www.sec.gov/files/company_tickers.json", headers=EDGAR_HEADERS).json()
    cik_lookup = {}
    for entry in response.values():
        cik_lookup[entry["ticker"]] = int(entry["cik_str"])

    return cik_lookup

def get_cik(ticker, lookup):
    """Get a specific issuer CIK from a ticker"""
    try: 
        return lookup[ticker]
    except KeyError as e:
        print(f"{ticker} is invalid or not in the lookup table.")


def get_filing_history(cik, start_date="2024-01-01"):
    """Get form 4 filing history for a specific company via CIK """
    response = requests.get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", headers=EDGAR_HEADERS).json()
    time.sleep(0.1)
    
    results = []
    for i, form_type in enumerate(response['filings']['recent']['form']):
        if form_type == '4' and response['filings']['recent']['filingDate'][i] >= start_date:
            results.append({'accessionNumber' : response['filings']['recent']['accessionNumber'][i],
                            'filingDate' : response['filings']['recent']['filingDate'][i],
                            'form' : response['filings']['recent']['form'][i],
                            'primaryDocument' : response['filings']['recent']['primaryDocument'][i]})
    return results

def get_filing(cik, accession_number, primary_document):
    """Get and parse a specific form 4 filing."""
    return parse_filing(get_filing_xml(cik, accession_number, primary_document))


def get_filing_xml(cik, accession_number, primary_document):
    """Get the raw XML for a specific form 4 filing."""
    accession_number = accession_number.replace("-", "")
    if "/" in primary_document:
        primary_document = primary_document.split("/")[1]
    
    response = requests.get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{primary_document}", headers=EDGAR_HEADERS)
    time.sleep(0.1)
    return response.text


def parse_filing(xml_text):
    """Parses a form 4 filing xml in string format"""

    root = ET.fromstring(xml_text)

    issuer = root.find("issuer/issuerName").text

    issuer_cik_el = root.find("issuer/issuerCik")
    issuer_cik = int(issuer_cik_el.text) if issuer_cik_el is not None else None

    issuer_trading_symbol_el = root.find("issuer/issuerTradingSymbol")
    issuer_trading_symbol = issuer_trading_symbol_el.text if issuer_trading_symbol_el is not None else None

    reportingOwner = root.find("reportingOwner/reportingOwnerId/rptOwnerName").text
    reportingOwnerCik = root.find("reportingOwner/reportingOwnerId/rptOwnerCik").text

    isDirector_el = root.find("reportingOwner/reportingOwnerRelationship/isDirector")
    isDirector = isDirector_el.text == "true" if isDirector_el is not None else None

    isOfficer_el = root.find("reportingOwner/reportingOwnerRelationship/isOfficer")
    isOfficer = isOfficer_el.text == "true" if isOfficer_el is not None else None

    isTenPercentOwner_el = root.find("reportingOwner/reportingOwnerRelationship/isTenPercentOwner")
    isTenPercentOwner = isTenPercentOwner_el.text == "true" if isTenPercentOwner_el is not None else None

    isOther_el = root.find("reportingOwner/reportingOwnerRelationship/isOther")
    isOther = isOther_el.text == "true" if isOther_el is not None else None

    officerTitle_el = root.find("reportingOwner/reportingOwnerRelationship/officerTitle")
    officerTitle = officerTitle_el.text if officerTitle_el is not None else None

    aff10b5One_el = root.find("aff10b5One")
    aff10b5One = aff10b5One_el.text == "true" if aff10b5One_el is not None else None
    
    result = {"issuerName" : issuer,
              "issuerCik": issuer_cik,
              "issuerTradingSymbol": issuer_trading_symbol,
              "reportingOwner": reportingOwner,
              "reportingOwnerCik" : int(reportingOwnerCik),
              "isDirector": isDirector,
              "isOfficer": isOfficer,
              "isTenPercentOwner": isTenPercentOwner,
              "isOther": isOther,
              "officerTitle": officerTitle,
              "aff10b5One": aff10b5One,
              "footnotes": {},
              "transactions": []}

    for footnote in root.findall("footnotes/footnote"):
        footnote_id = footnote.attrib.get("id")
        if footnote_id:
            result["footnotes"][footnote_id] = footnote.text

    transactions = root.findall("nonDerivativeTable/nonDerivativeTransaction")
    for transaction in transactions:
        security_title_el = transaction.find("securityTitle/value")
        security_title = security_title_el.text if security_title_el is not None else None

        code = transaction.find("transactionCoding/transactionCode").text

        shares = transaction.find("transactionAmounts/transactionShares/value").text
        if shares is not None:
            shares = float(shares)

        price_el = transaction.find("transactionAmounts/transactionPricePerShare/value")
        price = float(price_el.text) if price_el is not None else None

        disposed_code = transaction.find("transactionAmounts/transactionAcquiredDisposedCode/value").text

        shares_owned_following_el = transaction.find("postTransactionAmounts/sharesOwnedFollowingTransaction/value")
        shares_owned_following = float(shares_owned_following_el.text) if shares_owned_following_el is not None else None

        direct_or_indirect_ownership_el = transaction.find("ownershipNature/directOrIndirectOwnership/value")
        direct_or_indirect_ownership = direct_or_indirect_ownership_el.text if direct_or_indirect_ownership_el is not None else None

        footnote_ids = [
            footnote.attrib["id"]
            for footnote in transaction.findall(".//footnoteId")
            if "id" in footnote.attrib
        ]

        result['transactions'].append({"code" : code,
                                       "securityTitle": security_title,
                                       "shares" : shares,
                                       "price" : price,
                                       "disposed_code" : disposed_code,
                                       "sharesOwnedFollowing": shares_owned_following,
                                       "directOrIndirectOwnership": direct_or_indirect_ownership,
                                       "footnoteIds": footnote_ids}) 

    return result


if __name__ == "__main__": # pragma: no cover
    # Quick smoke test against the live SEC EDGAR API.
    lookup = build_cik_lookup()
    cik = get_cik("AAPL", lookup)
    filings = get_filing_history(cik)
    xml_text = get_filing_xml(cik, filings[0]['accessionNumber'], filings[0]['primaryDocument'])
    print(xml_text)
