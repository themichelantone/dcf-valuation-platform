import pandas as pd

# ── 1. Load data ──────────────────────────────────────────────
df = pd.read_csv("nvda_financials.csv", comment="#", index_col=0)
df = df.T
df = df.apply(pd.to_numeric, errors="coerce")

# ── 2. Historical Margins ─────────────────────────────────────
df["revenue_growth"]    = df["total_revenue"].pct_change() * 100
df["ebit_margin"]       = df["operating_income"] / df["total_revenue"] * 100
df["net_income_margin"] = df["net_income"] / df["total_revenue"] * 100
df["da_pct_revenue"]    = df["depreciation_amortization"] / df["total_revenue"] * 100
df["capex_pct_revenue"] = df["capex"] / df["total_revenue"] * 100
df["fcf_margin"]        = df["free_cash_flow"] / df["total_revenue"] * 100

# ── 3. Print results ──────────────────────────────────────────
print("=" * 60)
print("NVIDIA HISTORICAL FINANCIAL DRIVERS")
print("=" * 60)

metrics = df[[
    "total_revenue",
    "revenue_growth",
    "ebit_margin",
    "net_income_margin",
    "da_pct_revenue",
    "capex_pct_revenue",
    "fcf_margin"
]].round(2)

print(metrics.to_string())
print("\nProcess complete.")