-- Bluestock Fintech — Star Schema
-- Run this before loading data

DROP TABLE IF EXISTS fact_portfolio;
DROP TABLE IF EXISTS fact_performance;
DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS fact_nav;
DROP TABLE IF EXISTS fact_aum;
DROP TABLE IF EXISTS fact_sip_industry;
DROP TABLE IF EXISTS fact_category_inflows;
DROP TABLE IF EXISTS fact_folio_count;
DROP TABLE IF EXISTS dim_fund;
DROP TABLE IF EXISTS dim_date;

-- DIMENSIONS

CREATE TABLE dim_fund (
    amfi_code           TEXT    PRIMARY KEY,
    fund_house          TEXT    NOT NULL,
    scheme_name         TEXT    NOT NULL,
    category            TEXT    NOT NULL,
    sub_category        TEXT,
    plan                TEXT    NOT NULL,
    launch_date         DATE,
    benchmark           TEXT,
    expense_ratio_pct   REAL    CHECK (expense_ratio_pct BETWEEN 0.1 AND 2.5),
    exit_load_pct       REAL    DEFAULT 0,
    min_sip_amount      INTEGER,
    min_lumpsum_amount  INTEGER,
    fund_manager        TEXT,
    risk_category       TEXT    CHECK (risk_category IN ('Low','Moderate','Moderately High','High','Very High')),
    sebi_category_code  TEXT
);

CREATE TABLE dim_date (
    date_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    date        DATE    NOT NULL UNIQUE,
    year        INTEGER NOT NULL,
    month       INTEGER NOT NULL,
    quarter     INTEGER NOT NULL,
    month_name  TEXT    NOT NULL,
    is_weekday  INTEGER NOT NULL    -- 1=weekday, 0=weekend
);

-- FACTS

CREATE TABLE fact_nav (
    nav_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code        TEXT    NOT NULL REFERENCES dim_fund(amfi_code),
    date             DATE    NOT NULL,
    nav              REAL    NOT NULL CHECK (nav > 0),
    daily_return_pct REAL,
    UNIQUE (amfi_code, date)
);
CREATE INDEX idx_nav_code_date ON fact_nav (amfi_code, date);

CREATE TABLE fact_transactions (
    tx_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id        TEXT    NOT NULL,
    transaction_date   DATE    NOT NULL,
    amfi_code          TEXT    NOT NULL REFERENCES dim_fund(amfi_code),
    transaction_type   TEXT    NOT NULL CHECK (transaction_type IN ('SIP','Lumpsum','Redemption')),
    amount_inr         INTEGER NOT NULL CHECK (amount_inr > 0),
    state              TEXT,
    city               TEXT,
    city_tier          TEXT    CHECK (city_tier IN ('T30','B30')),
    age_group          TEXT,
    gender             TEXT,
    annual_income_lakh REAL,
    payment_mode       TEXT,
    kyc_status         TEXT    NOT NULL CHECK (kyc_status IN ('Verified','Pending'))
);
CREATE INDEX idx_tx_code ON fact_transactions (amfi_code);
CREATE INDEX idx_tx_date ON fact_transactions (transaction_date);
CREATE INDEX idx_tx_state ON fact_transactions (state);

CREATE TABLE fact_performance (
    perf_id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code                 TEXT    NOT NULL REFERENCES dim_fund(amfi_code),
    as_of_date                DATE    NOT NULL DEFAULT '2025-12-31',
    return_1yr_pct            REAL,
    return_3yr_pct            REAL,
    return_5yr_pct            REAL,
    benchmark_3yr_pct         REAL,
    alpha                     REAL,
    beta                      REAL,
    sharpe_ratio              REAL,
    sortino_ratio             REAL,
    std_dev_ann_pct           REAL,
    max_drawdown_pct          REAL,
    aum_crore                 INTEGER,
    expense_ratio_pct         REAL,
    morningstar_rating        INTEGER CHECK (morningstar_rating BETWEEN 1 AND 5),
    risk_grade                TEXT,
    flag_negative_sharpe      INTEGER DEFAULT 0,
    flag_expense_out_of_range INTEGER DEFAULT 0,
    flag_extreme_drawdown     INTEGER DEFAULT 0,
    UNIQUE (amfi_code, as_of_date)
);

CREATE TABLE fact_aum (
    aum_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    date           DATE    NOT NULL,
    fund_house     TEXT    NOT NULL,
    aum_lakh_crore REAL    NOT NULL,
    aum_crore      INTEGER NOT NULL,
    num_schemes    INTEGER,
    UNIQUE (fund_house, date)
);

CREATE TABLE fact_sip_industry (
    sip_id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    month                     DATE    NOT NULL UNIQUE,
    sip_inflow_crore          INTEGER NOT NULL,
    active_sip_accounts_crore REAL,
    new_sip_accounts_lakh     REAL,
    sip_aum_lakh_crore        REAL,
    yoy_growth_pct            REAL
);

CREATE TABLE fact_category_inflows (
    ci_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    month            DATE    NOT NULL,
    category         TEXT    NOT NULL,
    net_inflow_crore REAL,
    UNIQUE (month, category)
);

CREATE TABLE fact_folio_count (
    fc_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    month               DATE    NOT NULL UNIQUE,
    total_folios_crore  REAL,
    equity_folios_crore REAL,
    debt_folios_crore   REAL,
    hybrid_folios_crore REAL,
    others_folios_crore REAL
);

CREATE TABLE fact_portfolio (
    ph_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code         TEXT    NOT NULL REFERENCES dim_fund(amfi_code),
    stock_symbol      TEXT    NOT NULL,
    stock_name        TEXT,
    sector            TEXT,
    weight_pct        REAL    CHECK (weight_pct BETWEEN 0 AND 100),
    market_value_cr   REAL,
    current_price_inr REAL,
    portfolio_date    DATE    NOT NULL,
    UNIQUE (amfi_code, stock_symbol, portfolio_date)
);
CREATE INDEX idx_portfolio_code ON fact_portfolio (amfi_code);