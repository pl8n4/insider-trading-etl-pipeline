import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

# SEC EDGAR requires a contact email in the User-Agent header.
# Set EDGAR_CONTACT in your .env (see .env.example).
EDGAR_HEADERS = {"User-Agent": os.environ.get("EDGAR_CONTACT", "")}

HOST = os.environ.get("DB_HOST", "localhost")
DBNAME = os.environ.get("DB_NAME", "insider_signals")
USER = os.environ.get("DB_USER", "pablolasarte")

def get_connection():
    return psycopg2.connect(host=HOST, dbname=DBNAME, user=USER)