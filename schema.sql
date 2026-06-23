create table issuer(
    issuer_cik INT PRIMARY KEY,
    name TEXT,
    ticker TEXT
);

create table insider(
    insider_cik INT PRIMARY KEY,
    name TEXT
);

create table filing(
    accession_number TEXT PRIMARY KEY,
    filing_date DATE,
    aff10b5One BOOLEAN,
    issuer_cik INT NOT NULL,
    insider_cik INT NOT NULL,
    is_director BOOLEAN,
    is_officer BOOLEAN,
    is_ten_percent_owner BOOLEAN,
    is_other BOOLEAN,
    officer_title TEXT,
    footnotes JSONB,
    CONSTRAINT fk_filing_issuer_cik FOREIGN KEY (issuer_cik) REFERENCES issuer(issuer_cik)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_filing_insider_cik FOREIGN KEY (insider_cik) REFERENCES insider(insider_cik)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

create table transactions(
    transaction_id SERIAL PRIMARY KEY,
    accession_number TEXT NOT NULL,
    transaction_code CHAR(1),
    security_title TEXT,
    shares NUMERIC(15, 4),
    price NUMERIC(15, 4),
    disposed_code CHAR(1),
    shares_owned_following NUMERIC(15, 4),
    direct_or_indirect_ownership CHAR(1),
    footnote_ids TEXT[],
    CONSTRAINT fk_filing_accession_number
        FOREIGN KEY (accession_number) REFERENCES filing(accession_number)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);
