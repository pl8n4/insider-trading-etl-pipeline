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

# print(f"{get_cik("DJP", lookup)}")


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
    """Get a specific form 4 filing"""
    accession_number = accession_number.replace("-", "")
    if "/" in primary_document:
        primary_document = primary_document.split("/")[1]
    
    response = requests.get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{primary_document}", headers=EDGAR_HEADERS)
    time.sleep(0.1)
    root = ET.fromstring(response.text)

    issuer = root.find("issuer/issuerName").text
    reportingOwner = root.find("reportingOwner/reportingOwnerId/rptOwnerName").text
    reportingOwnerCik = root.find("reportingOwner/reportingOwnerId/rptOwnerCik").text
    aff10b5One_el = root.find("aff10b5One")
    aff10b5One = aff10b5One_el.text == 'true' if aff10b5One_el is not None else None
    result = {"issuerName" : issuer,
              "reportingOwner": reportingOwner,
              "aff10b5One": aff10b5One,
              "reportingOwnerCik" : int(reportingOwnerCik),
              "transactions": []}

    transactions = root.findall("nonDerivativeTable/nonDerivativeTransaction")
    for transaction in transactions:
        code = transaction.find("transactionCoding/transactionCode").text
        shares = transaction.find("transactionAmounts/transactionShares/value").text
        if shares is not None: 
            shares = float(shares) 
        price_el = transaction.find("transactionAmounts/transactionPricePerShare/value")
        price = float(price_el.text) if price_el is not None else None
        disposed_code = transaction.find("transactionAmounts/transactionAcquiredDisposedCode/value").text
        result['transactions'].append({"code" : code,
                                       "shares" : shares,
                                       "price" : price,
                                       "disposed_code" : disposed_code}) 

    return result

if __name__ == "__main__":
    # Quick smoke test against the live SEC EDGAR API.
    lookup = build_cik_lookup()
    cik = get_cik("AAPL", lookup)
    filings = get_filing_history(cik)
    print(get_filing(cik, filings[0]['accessionNumber'], filings[0]['primaryDocument']))