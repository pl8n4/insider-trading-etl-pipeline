import psycopg2
from psycopg2.extras import Json
import logging


logger = logging.getLogger(__name__)

def load_filing(conn, filing_data, issuer_cik, ticker, accession_number, filing_date):
    """Ingest a filing to the postgres db"""
    cur = conn.cursor()
    try:
        actual_issuer_cik = filing_data["issuerCik"] if filing_data["issuerCik"] is not None else issuer_cik
        actual_ticker = filing_data["issuerTradingSymbol"] if filing_data["issuerTradingSymbol"] is not None else ticker

        sql = "INSERT INTO issuer (issuer_cik, name, ticker) VALUES (%s, %s, %s) " \
        "ON CONFLICT DO NOTHING;"
        cur.execute(sql, (actual_issuer_cik, filing_data['issuerName'], actual_ticker))
    
        sql = "INSERT INTO insider (insider_cik, name) VALUES (%s, %s) " \
        "ON CONFLICT DO NOTHING;"
        cur.execute(sql, (filing_data["reportingOwnerCik"], filing_data["reportingOwner"]))

        sql = "INSERT INTO filing (accession_number, filing_date, aff10b5One, issuer_cik, insider_cik, is_director, is_officer, is_ten_percent_owner, is_other, officer_title, footnotes) " \
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) " \
        "ON CONFLICT DO NOTHING;"
        cur.execute(sql, (accession_number, filing_date, filing_data["aff10b5One"], actual_issuer_cik, filing_data["reportingOwnerCik"],
                          filing_data["isDirector"], filing_data["isOfficer"], filing_data["isTenPercentOwner"], filing_data["isOther"],
                          filing_data["officerTitle"], Json(filing_data["footnotes"])))

        
        if cur.rowcount == 0:
            conn.commit()
            return {"skipped": True, "transactions_inserted": 0}
        else:
            count = 0
            for transaction in filing_data["transactions"]:
                sql = "INSERT INTO transactions (accession_number, transaction_code, security_title, shares, price, disposed_code, shares_owned_following, direct_or_indirect_ownership, footnote_ids) " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
                cur.execute(sql, (accession_number, transaction["code"], transaction["securityTitle"], transaction['shares'], transaction["price"],
                                  transaction["disposed_code"], transaction["sharesOwnedFollowing"], transaction["directOrIndirectOwnership"],
                                  transaction["footnoteIds"]))
                count += 1
            conn.commit()
            return {"skipped": False, "transactions_inserted": count}

    except psycopg2.DatabaseError as error:
        print(error)
        conn.rollback()
