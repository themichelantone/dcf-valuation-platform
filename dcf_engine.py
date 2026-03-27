import pandas as pd
import numpy as np

# ── 1. Load Data ──────────────────────────────────────────────
df = pd.read_csv("nvda_financials.csv", comment="#", index_col=0)
df = df.T
df = df.apply(pd.to_numeric, errors="coerce")

# ── 2. Base Year Values (already in thousands, keep consistent) ──
base_revenue  = df["total_revenue"].iloc[0]
base_cash     = df["cash_and_short_term_investments"].iloc[0]
base_debt     = df["total_debt"].iloc[0]
base_shares   = df["shares_issued"].iloc[0]
base_da_pct   = df["depreciation_amortization"].iloc[0] / base_revenue
base_capex_pct= df["capex"].iloc[0] / base_revenue

# ── 3. Assumptions ────────────────────────────────────────────
revenue_growth  = [0.45, 0.30, 0.20, 0.15, 0.10]
ebit_margin     = 0.55
tax_rate        = 0.15
da_pct          = base_da_pct
capex_pct       = base_capex_pct
nwc_pct_change  = 0.03
wacc            = 0.10
terminal_growth = 0.03

# ── 4. Forecast Revenue ───────────────────────────────────────
revenues = []
rev = base_revenue
for g in revenue_growth:
    rev = rev * (1 + g)
    revenues.append(rev)

# ── 5. Build UFCF ─────────────────────────────────────────────
ufcf_list = []
prev_rev = base_revenue
for rev in revenues:
    ebit      = rev * ebit_margin
    nopat     = ebit * (1 - tax_rate)
    da        = rev * da_pct
    capex     = rev * capex_pct
    delta_nwc = (rev - prev_rev) * nwc_pct_change
    ufcf      = nopat + da - capex - delta_nwc
    ufcf_list.append(ufcf)
    prev_rev  = rev

# ── 6. Discount Cash Flows ────────────────────────────────────
pv_ufcf = [cf / ((1 + wacc) ** (i + 1)) for i, cf in enumerate(ufcf_list)]

# ── 7. Terminal Value ─────────────────────────────────────────
tv    = (ufcf_list[-1] * (1 + terminal_growth)) / (wacc - terminal_growth)
pv_tv = tv / ((1 + wacc) ** 5)

# ── 8. Bridge to Equity ───────────────────────────────────────
ev              = sum(pv_ufcf) + pv_tv
equity_value    = ev + base_cash - base_debt

# equity_value is in thousands, shares in thousands — divide directly
price_per_share = equity_value / base_shares

# ── 9. Output ─────────────────────────────────────────────────
print("=" * 60)
print("NVIDIA DCF VALUATION — BASE CASE")
print("=" * 60)

print("\n--- 5-Year Forecast (in thousands) ---")
for i in range(5):
    print(f"Year {i+1}: Revenue = ${revenues[i]/1e6:,.0f}B | "
          f"UFCF = ${ufcf_list[i]/1e6:,.0f}B | "
          f"PV = ${pv_ufcf[i]/1e6:,.0f}B")

print("\n--- Valuation (in billions) ---")
print(f"PV of Cash Flows:    ${sum(pv_ufcf)/1e6:,.1f}B")
print(f"PV Terminal Value:   ${pv_tv/1e6:,.1f}B")
print(f"Enterprise Value:    ${ev/1e6:,.1f}B")
print(f"+ Cash:              ${base_cash/1e6:,.1f}B")
print(f"- Debt:              ${base_debt/1e6:,.1f}B")
print(f"Equity Value:        ${equity_value/1e6:,.1f}B")
print(f"Shares Outstanding:  {base_shares/1e6:,.2f}B")
print(f"\n>>> Implied Share Price: ${price_per_share:,.2f}")
print("=" * 60)

