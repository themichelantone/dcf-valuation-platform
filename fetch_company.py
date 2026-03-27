import yfinance as yf
import sqlite3
import pandas as pd
from datetime import date

def fetch_and_store(ticker_symbol):

    print(f"\n{'='*55}")
    print(f"Fetching data for: {ticker_symbol}")
    print(f"{'='*55}")

    # ── 1. Pull from Yahoo Finance ────────────────────────────
    ticker = yf.Ticker(ticker_symbol)

    # Company info
    info    = ticker.info
    name    = info.get("longName", ticker_symbol)
    sector  = info.get("sector", "Unknown")
    industry= info.get("industry", "Unknown")

    print(f"✅ Company:  {name}")
    print(f"   Sector:   {sector}")
    print(f"   Industry: {industry}")

    # Financial statements
    income_stmt  = ticker.financials          # annual income statement
    balance_sheet= ticker.balance_sheet       # annual balance sheet
    cash_flow    = ticker.cashflow            # annual cash flow

    # ── 2. Extract key metrics ────────────────────────────────
    def get_row(df, possible_keys):
        for key in possible_keys:
            if key in df.index:
                return df.loc[key]
        return pd.Series(dtype=float)

    revenue    = get_row(income_stmt,   ["Total Revenue"])
    op_income  = get_row(income_stmt,   ["Operating Income", "EBIT"])
    net_income = get_row(income_stmt,   ["Net Income"])
    ebit       = get_row(income_stmt,   ["EBIT", "Operating Income"])
    ebitda     = get_row(income_stmt,   ["EBITDA", "Normalized EBITDA"])
    cost_rev   = get_row(income_stmt,   ["Cost Of Revenue"])
    gross_prof = get_row(income_stmt,   ["Gross Profit"])

    da         = get_row(cash_flow,     ["Depreciation And Amortization",
                                         "Depreciation Amortization Depletion"])
    capex      = get_row(cash_flow,     ["Capital Expenditure"])
    fcf        = get_row(cash_flow,     ["Free Cash Flow"])
    op_cf      = get_row(cash_flow,     ["Operating Cash Flow"])

    cash       = get_row(balance_sheet, ["Cash And Cash Equivalents",
                                         "Cash Cash Equivalents And Short Term Investments"])
    debt       = get_row(balance_sheet, ["Total Debt"])
    shares     = get_row(balance_sheet, ["Share Issued", "Ordinary Shares Number"])
    wc         = get_row(balance_sheet, ["Working Capital"])

    # ── 3. Store in database ──────────────────────────────────
    conn   = sqlite3.connect("dcf_database.db")
    cursor = conn.cursor()

    # Insert company
    cursor.execute("""
        INSERT OR REPLACE INTO companies (ticker, company_name, sector, industry)
        VALUES (?, ?, ?, ?)
    """, (ticker_symbol, name, sector, industry))

    # Insert financials for each year
    years = revenue.index if len(revenue) > 0 else []
    count = 0
    for year in years:
        def safe(series):
            try:
                v = series[year]
                return float(v) if pd.notna(v) else None
            except:
                return None

        # Capex flip to positive
        capex_val = safe(capex)
        if capex_val is not None:
            capex_val = abs(capex_val)

        cursor.execute("""
            INSERT INTO financials (
                ticker, fiscal_year, total_revenue, cost_of_revenue,
                gross_profit, operating_income, net_income, ebit, ebitda,
                depreciation_amortization, capex, free_cash_flow,
                cash_and_short_term_investments, total_debt, shares_issued,
                working_capital, operating_cash_flow
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker_symbol,
            str(year)[:10],
            safe(revenue),
            safe(cost_rev),
            safe(gross_prof),
            safe(op_income),
            safe(net_income),
            safe(ebit),
            safe(ebitda),
            safe(da),
            capex_val,
            safe(fcf),
            safe(cash),
            safe(debt),
            safe(shares),
            safe(wc),
            safe(op_cf)
        ))
        count += 1

    # Default assumptions
    cursor.execute("""
        INSERT INTO assumptions (
            ticker, wacc, terminal_growth, ebit_margin,
            tax_rate, nwc_pct_change,
            yr1_growth, yr2_growth, yr3_growth, yr4_growth, yr5_growth
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ticker_symbol, 0.10, 0.03, 0.20, 0.21, 0.03,
          0.10, 0.08, 0.07, 0.06, 0.05))

    conn.commit()
    conn.close()

    print(f"✅ {count} years of financials stored")
    print(f"✅ Saved to database: dcf_database.db")
    print(f"{'='*55}\n")

    # ── Run it ────────────────────────────────────────────────────
fetch_and_store("AAPL")