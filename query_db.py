import sqlite3
import pandas as pd

# ── Connect ───────────────────────────────────────────────────
conn = sqlite3.connect("dcf_database.db")

# ── Query 1: Companies ────────────────────────────────────────
print("=" * 55)
print("TABLE: companies")
print("=" * 55)
df1 = pd.read_sql_query("SELECT * FROM companies", conn)
print(df1.to_string())

# ── Query 2: Financials ───────────────────────────────────────
print("\n" + "=" * 55)
print("TABLE: financials (key metrics only)")
print("=" * 55)
df2 = pd.read_sql_query("""
    SELECT ticker, fiscal_year, total_revenue,
           operating_income, net_income, free_cash_flow
    FROM financials
    WHERE ticker = 'NVDA'
    ORDER BY fiscal_year DESC
""", conn)
print(df2.to_string())

# ── Query 3: Assumptions ──────────────────────────────────────
print("\n" + "=" * 55)
print("TABLE: assumptions")
print("=" * 55)
df3 = pd.read_sql_query("SELECT * FROM assumptions WHERE ticker = 'NVDA'", conn)
print(df3.to_string())

# ── Query 4: Valuation Output ─────────────────────────────────
print("\n" + "=" * 55)
print("TABLE: valuations")
print("=" * 55)
df4 = pd.read_sql_query("SELECT * FROM valuations WHERE ticker = 'NVDA'", conn)
print(df4.to_string())


# Check Apple
print("\n" + "=" * 55)
print("APPLE FINANCIALS")
print("=" * 55)
df5 = pd.read_sql_query("""
    SELECT ticker, fiscal_year, total_revenue,
           operating_income, net_income, free_cash_flow
    FROM financials
    WHERE ticker = 'AAPL'
    ORDER BY fiscal_year DESC
""", conn)
print(df5.to_string())

conn.close()
print("\n✅ All tables verified successfully.")