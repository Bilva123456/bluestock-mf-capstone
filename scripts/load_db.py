"""
Bluestock Fintech — Day 2: Load cleaned CSVs into SQLite
"""

import pandas as pd
import sqlite3
from pathlib import Path

PROCESSED = Path("data/processed")
DB_PATH   = Path("data/db/bluestock_mf.db")
SCHEMA    = Path("sql/schema.sql")

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA foreign_keys=ON")

print("Applying schema ...")
with open(SCHEMA) as f:
    conn.executescript(f.read())
print("  Schema applied ✓\n")


def load(df, table, conn):
    df.to_sql(table, conn, if_exists="append", index=False)
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  {table}: {count:,} rows")


# dim_date — generated from NAV date range
print("Building dim_date ...")
nav_dates = pd.read_csv(PROCESSED / "02_nav_history.csv", usecols=["date"], parse_dates=["date"])
all_dates = pd.date_range(nav_dates["date"].min(), nav_dates["date"].max(), freq="D")
dim_date = pd.DataFrame({
    "date":       all_dates,
    "year":       all_dates.year,
    "month":      all_dates.month,
    "quarter":    all_dates.quarter,
    "month_name": all_dates.strftime("%B"),
    "is_weekday": (all_dates.dayofweek < 5).astype(int),
})
load(dim_date, "dim_date", conn)

# dim_fund
print("\nLoading dimensions ...")
fm = pd.read_csv(PROCESSED / "01_fund_master.csv")
fm["amfi_code"] = fm["amfi_code"].astype(str)
load(fm, "dim_fund", conn)

# fact_nav — compute daily return on the way in
print("\nLoading fact tables ...")
nav = pd.read_csv(PROCESSED / "02_nav_history.csv", parse_dates=["date"])
nav["amfi_code"] = nav["amfi_code"].astype(str)
nav = nav.sort_values(["amfi_code", "date"])
nav["daily_return_pct"] = nav.groupby("amfi_code")["nav"].pct_change() * 100
load(nav, "fact_nav", conn)

# fact_aum
aum = pd.read_csv(PROCESSED / "03_aum_by_fund_house.csv", parse_dates=["date"])
load(aum, "fact_aum", conn)

# fact_sip_industry
sip = pd.read_csv(PROCESSED / "04_monthly_sip_inflows.csv", parse_dates=["month"])
load(sip, "fact_sip_industry", conn)

# fact_category_inflows
ci = pd.read_csv(PROCESSED / "05_category_inflows.csv", parse_dates=["month"])
load(ci, "fact_category_inflows", conn)

# fact_folio_count
folio = pd.read_csv(PROCESSED / "06_industry_folio_count.csv", parse_dates=["month"])
load(folio, "fact_folio_count", conn)

# fact_performance
perf = pd.read_csv(PROCESSED / "07_scheme_performance.csv")
perf["amfi_code"] = perf["amfi_code"].astype(str)
perf["as_of_date"] = "2025-12-31"
perf = perf.drop(columns=["scheme_name", "fund_house", "category", "plan"], errors="ignore")
for col in ["flag_negative_sharpe", "flag_expense_out_of_range", "flag_extreme_drawdown"]:
    if col in perf.columns:
        perf[col] = perf[col].astype(int)
load(perf, "fact_performance", conn)

# fact_transactions
tx = pd.read_csv(PROCESSED / "08_investor_transactions.csv", parse_dates=["transaction_date"])
tx["amfi_code"] = tx["amfi_code"].astype(str)
load(tx, "fact_transactions", conn)

# fact_portfolio
ph = pd.read_csv(PROCESSED / "09_portfolio_holdings.csv", parse_dates=["portfolio_date"])
ph["amfi_code"] = ph["amfi_code"].astype(str)
load(ph, "fact_portfolio", conn)

conn.commit()
conn.close()

print(f"\n✅ Database ready → {DB_PATH}")
print(f"   Size: {DB_PATH.stat().st_size / 1024 / 1024:.1f} MB")