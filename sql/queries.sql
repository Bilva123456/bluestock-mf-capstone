-- Q1: Top 5 fund houses by latest AUM
SELECT fund_house, aum_lakh_crore, aum_crore, num_schemes
FROM fact_aum
WHERE date = (SELECT MAX(date) FROM fact_aum)
ORDER BY aum_lakh_crore DESC
LIMIT 5;

-- Q2: Average NAV per month across all funds
SELECT
    strftime('%Y-%m', date) AS month,
    ROUND(AVG(nav), 2)      AS avg_nav,
    COUNT(DISTINCT amfi_code) AS num_funds
FROM fact_nav
GROUP BY strftime('%Y-%m', date)
ORDER BY month;

-- Q3: SIP inflow year-on-year growth
SELECT
    strftime('%Y', month)         AS year,
    SUM(sip_inflow_crore)         AS total_sip_crore,
    ROUND(AVG(yoy_growth_pct), 2) AS avg_yoy_pct
FROM fact_sip_industry
GROUP BY strftime('%Y', month)
ORDER BY year;

-- Q4: Total transaction amount by state
SELECT
    state,
    COUNT(*)               AS num_transactions,
    SUM(amount_inr)        AS total_amount_inr,
    ROUND(AVG(amount_inr)) AS avg_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;

-- Q5: Funds with expense ratio below 1%
SELECT
    f.amfi_code, f.scheme_name, f.fund_house,
    f.expense_ratio_pct, p.sharpe_ratio, p.return_3yr_pct
FROM dim_fund f
LEFT JOIN fact_performance p ON f.amfi_code = p.amfi_code
WHERE f.expense_ratio_pct < 1.0
ORDER BY f.expense_ratio_pct;

-- Q6: Top 10 funds by Sharpe ratio
SELECT
    f.scheme_name, f.fund_house, f.category,
    p.sharpe_ratio, p.return_3yr_pct, p.alpha, p.max_drawdown_pct
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.sharpe_ratio DESC
LIMIT 10;

-- Q7: Monthly net flow (SIP + Lumpsum − Redemption)
SELECT
    strftime('%Y-%m', transaction_date) AS month,
    SUM(CASE WHEN transaction_type='SIP'        THEN amount_inr ELSE 0 END) AS sip_inflow,
    SUM(CASE WHEN transaction_type='Lumpsum'    THEN amount_inr ELSE 0 END) AS lumpsum_inflow,
    SUM(CASE WHEN transaction_type='Redemption' THEN amount_inr ELSE 0 END) AS redemption_outflow,
    SUM(CASE WHEN transaction_type IN ('SIP','Lumpsum') THEN  amount_inr
             WHEN transaction_type = 'Redemption'       THEN -amount_inr
             ELSE 0 END)                                                     AS net_flow
FROM fact_transactions
GROUP BY strftime('%Y-%m', transaction_date)
ORDER BY month;

-- Q8: Average SIP amount by investor age group
SELECT
    age_group,
    COUNT(*)                    AS num_sip,
    ROUND(AVG(amount_inr))      AS avg_sip_amount,
    COUNT(DISTINCT investor_id) AS unique_investors
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY age_group
ORDER BY avg_sip_amount DESC;

-- Q9: Top sectors by portfolio market value
SELECT
    sector,
    COUNT(DISTINCT stock_symbol)   AS num_stocks,
    ROUND(AVG(weight_pct), 2)      AS avg_weight_pct,
    ROUND(SUM(market_value_cr))    AS total_market_value_cr
FROM fact_portfolio
GROUP BY sector
ORDER BY total_market_value_cr DESC;

-- Q10: Category net inflow ranking FY 2024-25
SELECT
    category,
    ROUND(SUM(net_inflow_crore))  AS total_net_inflow_crore,
    ROUND(AVG(net_inflow_crore))  AS avg_monthly_inflow
FROM fact_category_inflows
WHERE month >= '2024-04-01' AND month <= '2025-03-31'
GROUP BY category
ORDER BY total_net_inflow_crore DESC;