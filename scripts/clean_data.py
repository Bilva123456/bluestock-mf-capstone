"""
Bluestock Fintech — Day 2: Data Cleaning
Reads from data/raw/, writes cleaned files to data/processed/
"""

import pandas as pd
import numpy as np
from pathlib import Path

RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(f"  {msg}")


# ── 01: fund_master ─────────────────────────────────────
print("Cleaning 01_fund_master.csv ...")
fm = pd.read_csv(RAW / "01_fund_master.csv")
fm["amfi_code"] = fm["amfi_code"].astype(str)
fm["launch_date"] = pd.to_datetime(fm["launch_date"])
out_of_range = fm[(fm["expense_ratio_pct"] < 0.1) | (fm["expense_ratio_pct"] > 2.5)]
if not out_of_range.empty:
    log(f"WARNING: {len(out_of_range)} funds with expense_ratio out of [0.1, 2.5]")
fm = fm.drop_duplicates()
fm.to_csv(OUT / "01_fund_master.csv", index=False)
log(f"Saved {len(fm)} rows")


# ── 02: nav_history (main cleaning) ─────────────────────
print("\nCleaning 02_nav_history.csv ...")
nav = pd.read_csv(RAW / "02_nav_history.csv")
nav["amfi_code"] = nav["amfi_code"].astype(str)
nav["date"] = pd.to_datetime(nav["date"])

before = len(nav)
nav = nav.drop_duplicates(subset=["amfi_code", "date"])
log(f"Removed {before - len(nav)} duplicate rows")

invalid_nav = nav[nav["nav"] <= 0]
if not invalid_nav.empty:
    log(f"Dropping {len(invalid_nav)} rows with nav <= 0")
    nav = nav[nav["nav"] > 0]

# Forward-fill weekends/holidays per fund
nav = nav.sort_values(["amfi_code", "date"])
full_date_range = pd.date_range(nav["date"].min(), nav["date"].max(), freq="D")

groups = []
for code, grp in nav.groupby("amfi_code"):
    grp = grp.set_index("date").reindex(full_date_range)
    grp["amfi_code"] = code
    grp["nav"] = grp["nav"].ffill()
    grp = grp.dropna(subset=["nav"])
    grp.index.name = "date"
    grp = grp.reset_index()
    groups.append(grp)

nav_filled = pd.concat(groups, ignore_index=True)
nav_filled = nav_filled[["amfi_code", "date", "nav"]]
nav_filled = nav_filled.sort_values(["amfi_code", "date"])
log(f"Rows before: {before:,}  →  After forward-fill: {len(nav_filled):,}")
nav_filled.to_csv(OUT / "02_nav_history.csv", index=False)
log(f"Saved {len(nav_filled)} rows")


# ── 03: aum_by_fund_house ───────────────────────────────
print("\nCleaning 03_aum_by_fund_house.csv ...")
aum = pd.read_csv(RAW / "03_aum_by_fund_house.csv")
aum["date"] = pd.to_datetime(aum["date"])
aum = aum.drop_duplicates()
aum.to_csv(OUT / "03_aum_by_fund_house.csv", index=False)
log(f"Saved {len(aum)} rows")


# ── 04: monthly_sip_inflows ─────────────────────────────
print("\nCleaning 04_monthly_sip_inflows.csv ...")
sip = pd.read_csv(RAW / "04_monthly_sip_inflows.csv")
sip["month"] = pd.to_datetime(sip["month"] + "-01")
sip = sip.drop_duplicates()
sip.to_csv(OUT / "04_monthly_sip_inflows.csv", index=False)
log(f"Saved {len(sip)} rows")


# ── 05: category_inflows ────────────────────────────────
print("\nCleaning 05_category_inflows.csv ...")
cat = pd.read_csv(RAW / "05_category_inflows.csv")
cat["month"] = pd.to_datetime(cat["month"] + "-01")
cat = cat.drop_duplicates()
cat.to_csv(OUT / "05_category_inflows.csv", index=False)
log(f"Saved {len(cat)} rows")


# ── 06: industry_folio_count ────────────────────────────
print("\nCleaning 06_industry_folio_count.csv ...")
folio = pd.read_csv(RAW / "06_industry_folio_count.csv")
folio["month"] = pd.to_datetime(folio["month"] + "-01")
folio = folio.drop_duplicates()
folio.to_csv(OUT / "06_industry_folio_count.csv", index=False)
log(f"Saved {len(folio)} rows")


# ── 07: scheme_performance ──────────────────────────────
print("\nCleaning 07_scheme_performance.csv ...")
perf = pd.read_csv(RAW / "07_scheme_performance.csv")
perf["amfi_code"] = perf["amfi_code"].astype(str)

numeric_cols = [
    "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
    "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
    "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct", "expense_ratio_pct"
]
for col in numeric_cols:
    perf[col] = pd.to_numeric(perf[col], errors="coerce")

# Anomaly flags (kept as columns, NOT dropped)
perf["flag_expense_out_of_range"] = ~perf["expense_ratio_pct"].between(0.1, 2.5)
perf["flag_negative_sharpe"]      = perf["sharpe_ratio"] < 0
perf["flag_extreme_drawdown"]     = perf["max_drawdown_pct"] < -60

n_flags = perf[["flag_expense_out_of_range","flag_negative_sharpe","flag_extreme_drawdown"]].any(axis=1).sum()
log(f"Flagged {n_flags} anomalous rows")
log(f"Expense ratio range: {perf['expense_ratio_pct'].min():.2f}% – {perf['expense_ratio_pct'].max():.2f}%")

perf = perf.drop_duplicates(subset=["amfi_code"])
perf.to_csv(OUT / "07_scheme_performance.csv", index=False)
log(f"Saved {len(perf)} rows")


# ── 08: investor_transactions ───────────────────────────
print("\nCleaning 08_investor_transactions.csv ...")
tx = pd.read_csv(RAW / "08_investor_transactions.csv")
tx["amfi_code"] = tx["amfi_code"].astype(str)
tx["transaction_date"] = pd.to_datetime(tx["transaction_date"])

# Standardise transaction_type to exactly: SIP / Lumpsum / Redemption
VALID_TX = {"SIP", "Lumpsum", "Redemption"}
tx["transaction_type"] = tx["transaction_type"].str.strip().str.title()
tx_map = {
    "Sip": "SIP",
    "Systematic Investment Plan": "SIP",
    "Lump Sum": "Lumpsum",
    "Redeem": "Redemption",
}
tx["transaction_type"] = tx["transaction_type"].replace(tx_map)
# Fix SIP back — str.title() converts "SIP" → "Sip"
tx["transaction_type"] = tx["transaction_type"].replace({"Sip": "SIP"})

invalid = tx[~tx["transaction_type"].isin(VALID_TX)]
if not invalid.empty:
    log(f"WARNING: {len(invalid)} rows with unrecognised transaction_type")

# Validate amount > 0
bad = tx[tx["amount_inr"] <= 0]
if not bad.empty:
    log(f"Dropping {len(bad)} rows with amount <= 0")
    tx = tx[tx["amount_inr"] > 0]

# Validate KYC enum
VALID_KYC = {"Verified", "Pending"}
tx["kyc_status"] = tx["kyc_status"].str.strip().str.title()
invalid_kyc = tx[~tx["kyc_status"].isin(VALID_KYC)]
if not invalid_kyc.empty:
    log(f"WARNING: {len(invalid_kyc)} rows with invalid kyc_status")

tx = tx.drop_duplicates()
log(f"Transaction types: {tx['transaction_type'].value_counts().to_dict()}")
log(f"KYC status:        {tx['kyc_status'].value_counts().to_dict()}")
tx.to_csv(OUT / "08_investor_transactions.csv", index=False)
log(f"Saved {len(tx)} rows")


# ── 09: portfolio_holdings ──────────────────────────────
print("\nCleaning 09_portfolio_holdings.csv ...")
ph = pd.read_csv(RAW / "09_portfolio_holdings.csv")
ph["amfi_code"] = ph["amfi_code"].astype(str)
ph["portfolio_date"] = pd.to_datetime(ph["portfolio_date"])
ph = ph.drop_duplicates()
ph.to_csv(OUT / "09_portfolio_holdings.csv", index=False)
log(f"Saved {len(ph)} rows")


# ── 10: benchmark_indices ───────────────────────────────
print("\nCleaning 10_benchmark_indices.csv ...")
bm = pd.read_csv(RAW / "10_benchmark_indices.csv")
bm["date"] = pd.to_datetime(bm["date"])
bm = bm.drop_duplicates()
bm.to_csv(OUT / "10_benchmark_indices.csv", index=False)
log(f"Saved {len(bm)} rows")

print("\n✅ All 10 datasets cleaned → data/processed/")