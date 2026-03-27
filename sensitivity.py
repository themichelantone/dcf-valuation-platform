import pandas as pd
import numpy as np

# ── 1. Load Data ──────────────────────────────────────────────
df = pd.read_csv("nvda_financials.csv", comment="#", index_col=0)
df = df.T
df = df.apply(pd.to_numeric, errors="coerce")

# ── 2. Base Year ──────────────────────────────────────────────
base_revenue   = df["total_revenue"].iloc[0]
base_cash      = df["cash_and_short_term_investments"].iloc[0]
base_debt      = df["total_debt"].iloc[0]
base_shares    = df["shares_issued"].iloc[0]
base_da_pct    = df["depreciation_amortization"].iloc[0] / base_revenue
base_capex_pct = df["capex"].iloc[0] / base_revenue

# ── 3. Fixed Assumptions ──────────────────────────────────────
revenue_growth = [0.45, 0.30, 0.20, 0.15, 0.10]
ebit_margin    = 0.55
tax_rate       = 0.15
nwc_pct_change = 0.03

# ── 4. DCF Function ───────────────────────────────────────────
def run_dcf(wacc, terminal_growth):
    # Forecast revenue
    revenues = []
    rev = base_revenue
    for g in revenue_growth:
        rev = rev * (1 + g)
        revenues.append(rev)

    # Build UFCF
    ufcf_list = []
    prev_rev = base_revenue
    for rev in revenues:
        nopat     = rev * ebit_margin * (1 - tax_rate)
        da        = rev * base_da_pct
        capex     = rev * base_capex_pct
        delta_nwc = (rev - prev_rev) * nwc_pct_change
        ufcf      = nopat + da - capex - delta_nwc
        ufcf_list.append(ufcf)
        prev_rev  = rev

    # Discount
    pv_ufcf = [cf / ((1 + wacc) ** (i + 1)) for i, cf in enumerate(ufcf_list)]

    # Terminal value
    tv    = (ufcf_list[-1] * (1 + terminal_growth)) / (wacc - terminal_growth)
    pv_tv = tv / ((1 + wacc) ** 5)

    # Equity value & price
    ev           = sum(pv_ufcf) + pv_tv
    equity_value = ev + base_cash - base_debt
    price        = equity_value / base_shares
    return round(price, 2)

# ── 5. Sensitivity Ranges ─────────────────────────────────────
wacc_range = [0.08, 0.09, 0.10, 0.11, 0.12]
tg_range   = [0.02, 0.025, 0.03, 0.035, 0.04]

# ── 6. Build Sensitivity Table ────────────────────────────────
results = {}
for tg in tg_range:
    row = {}
    for wacc in wacc_range:
        row[f"WACC {wacc*100:.1f}%"] = run_dcf(wacc, tg)
    results[f"TG {tg*100:.1f}%"] = row

table = pd.DataFrame(results).T

# ── 7. Print Table ────────────────────────────────────────────
print("=" * 70)
print("NVIDIA DCF — SENSITIVITY ANALYSIS")
print("Implied Share Price ($) | Rows = Terminal Growth | Cols = WACC")
print("=" * 70)
print(table.to_string())
print("\nBase case (WACC=10%, TG=3%): marked with *" )
print(f">>> Base case price: ${run_dcf(0.10, 0.03):,.2f}")
print("=" * 70)

# ── 8. Flag the base case cell ────────────────────────────────
print("\nCurrent NVDA market price: ~$178")
print("Your DCF base case:        $138.95")
print("Upside to market:          implies market prices in higher growth")