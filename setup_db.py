import sqlite3

# ── Create / connect to database ──────────────────────────────
conn = sqlite3.connect("dcf_database.db")
cursor = conn.cursor()

# ── Table 1: Companies ────────────────────────────────────────
cursor.execute("""
CREATE TABLE IF NOT EXISTS companies (
    ticker          TEXT PRIMARY KEY,
    company_name    TEXT,
    sector          TEXT,
    industry        TEXT
)
""")

# ── Table 2: Financials ───────────────────────────────────────
cursor.execute("""
CREATE TABLE IF NOT EXISTS financials (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker                      TEXT,
    fiscal_year                 TEXT,
    total_revenue               REAL,
    cost_of_revenue             REAL,
    gross_profit                REAL,
    operating_income            REAL,
    net_income                  REAL,
    ebit                        REAL,
    ebitda                      REAL,
    depreciation_amortization   REAL,
    capex                       REAL,
    free_cash_flow              REAL,
    cash_and_short_term_investments REAL,
    total_debt                  REAL,
    shares_issued               REAL,
    working_capital             REAL,
    operating_cash_flow         REAL,
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
)
""")

# ── Table 3: Valuation Outputs ────────────────────────────────
cursor.execute("""
CREATE TABLE IF NOT EXISTS valuations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker              TEXT,
    valuation_date      TEXT,
    wacc                REAL,
    terminal_growth     REAL,
    ebit_margin         REAL,
    enterprise_value    REAL,
    equity_value        REAL,
    implied_share_price REAL,
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
)
""")

# ── Table 4: Assumptions ──────────────────────────────────────
cursor.execute("""
CREATE TABLE IF NOT EXISTS assumptions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker              TEXT,
    wacc                REAL,
    terminal_growth     REAL,
    ebit_margin         REAL,
    tax_rate            REAL,
    nwc_pct_change      REAL,
    yr1_growth          REAL,
    yr2_growth          REAL,
    yr3_growth          REAL,
    yr4_growth          REAL,
    yr5_growth          REAL,
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
)
""")

conn.commit()
conn.close()

print("=" * 50)
print("✅ Database created successfully!")
print("   File: dcf_database.db")
print("   Tables: companies, financials, valuations, assumptions")
print("=" * 50)
