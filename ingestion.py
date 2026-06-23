import psycopg2
import logging


logger = logging.getLogger(__name__)

def load_filing(conn, filing_data, issuer_cik, ticker, accession_number, filing_date):
    """Ingest a filing to the postgres db"""
    cur = conn.cursor()
    try:
        sql = "INSERT INTO issuer (issuer_cik, name, ticker) VALUES (%s, %s, %s) " \
        "ON CONFLICT DO NOTHING;"
        cur.execute(sql, (issuer_cik, filing_data['issuerName'], ticker))
    
        sql = "INSERT INTO insider (insider_cik, name) VALUES (%s, %s) " \
        "ON CONFLICT DO NOTHING;"
        cur.execute(sql, (filing_data["reportingOwnerCik"], filing_data["reportingOwner"]))

        sql = "INSERT INTO filing (accession_number, filing_date, aff10b5One, issuer_cik, insider_cik) " \
        "VALUES (%s, %s, %s, %s, %s) " \
        "ON CONFLICT DO NOTHING;"
        cur.execute(sql, (accession_number, filing_date, filing_data["aff10b5One"], issuer_cik, filing_data["reportingOwnerCik"]))

        
        if cur.rowcount == 0:
            conn.commit()
            return {"skipped": True, "transactions_inserted": 0}
        else:
            count = 0
            for transaction in filing_data["transactions"]:
                sql = "INSERT INTO transactions (accession_number, transaction_code, shares, price, disposed_code) " \
                "VALUES (%s, %s, %s, %s, %s);"
                cur.execute(sql, (accession_number, transaction["code"], transaction['shares'], transaction["price"], transaction["disposed_code"]))
                count += 1
            conn.commit()
            return {"skipped": False, "transactions_inserted": count}

    except psycopg2.DatabaseError as error:
        print(error)
        conn.rollback()