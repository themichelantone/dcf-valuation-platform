import sqlite3
import pandas as pd
from datetime import date

# ── 1. Connect to database ────────────────────────────────────
conn = sqlite3.connect("dcf_database.db")
cursor = conn.cursor()

# ── 2. Load NVIDIA CSV ────────────────────────────────────────
df = pd.read_csv("nvda_financials.csv", comment="#", index_col=0)
df = df.T
df = df.apply(pd.to_numeric, errors="coerce")

# ── 3. Insert company info ────────────────────────────────────
cursor.execute("""
    INSERT OR REPLACE INTO companies (ticker, company_name, sector, industry)
    VALUES (?, ?, ?, ?)
""", ("NVDA", "NVIDIA Corporation", "Technology", "Semiconductors"))

# ── 4. Insert financials for each year ───────────────────────
for fiscal_year, row in df.iterrows():
    cursor.execute("""
        INSERT INTO financials (
            ticker, fiscal_year, total_revenue, cost_of_revenue,
            gross_profit, operating_income, net_income, ebit, ebitda,
            depreciation_amortization, capex, free_cash_flow,
            cash_and_short_term_investments, total_debt, shares_issued,
            working_capital, operating_cash_flow
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "NVDA",
        fiscal_year,
        row.get("total_revenue"),
        row.get("cost_of_revenue"),
        row.get("gross_profit"),
        row.get("operating_income"),
        row.get("net_income"),
        row.get("ebit"),
        row.get("ebitda"),
        row.get("depreciation_amortization"),
        row.get("capex"),
        row.get("free_cash_flow"),
        row.get("cash_and_short_term_investments"),
        row.get("total_debt"),
        row.get("shares_issued"),
        row.get("working_capital"),
        row.get("operating_cash_flow")
    ))

# ── 5. Insert assumptions ─────────────────────────────────────
cursor.execute("""
    INSERT INTO assumptions (
        ticker, wacc, terminal_growth, ebit_margin,
        tax_rate, nwc_pct_change,
        yr1_growth, yr2_growth, yr3_growth, yr4_growth, yr5_growth
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", ("NVDA", 0.10, 0.03, 0.55, 0.15, 0.03,
      0.45, 0.30, 0.20, 0.15, 0.10))

# ── 6. Insert valuation output ────────────────────────────────
cursor.execute("""
    INSERT INTO valuations (
        ticker, valuation_date, wacc, terminal_growth,
        ebit_margin, enterprise_value, equity_value, implied_share_price
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", ("NVDA", str(date.today()), 0.10, 0.03,
      0.55, 3325414916, 3376930916, 138.95))

conn.commit()
conn.close()

print("=" * 55)
print("✅ NVIDIA data stored in database successfully!")
print("   Tables updated: companies, financials, assumptions, valuations")
print("=" * 55)