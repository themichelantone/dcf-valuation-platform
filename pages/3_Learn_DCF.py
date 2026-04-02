import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Learn DCF — DCF Valuation Platform",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Learn DCF — From Zero to Valuation")
st.markdown("*A practical guide to understanding how companies are valued*")
st.divider()

# ── Navigation ────────────────────────────────────────────────
st.markdown("""
**Jump to a section:**
[1. What is Value?](#1-what-is-value) · 
[2. Financial Statements](#2-the-three-financial-statements) · 
[3. Time Value of Money](#3-time-value-of-money) · 
[4. What is a DCF?](#4-what-is-a-dcf) · 
[5. WACC](#5-wacc-the-discount-rate) · 
[6. Putting It Together](#6-putting-it-all-together) · 
[7. DDM](#7-the-dividend-discount-model-ddm) · 
[8. EV vs Equity Value](#8-enterprise-value-vs-equity-value) · 
[9. Sensitivity Table](#9-how-to-read-a-sensitivity-table)
""")
st.divider()

# ══════════════════════════════════════════════════════════════
# SECTION 1 — WHAT IS VALUE
# ══════════════════════════════════════════════════════════════
st.header("1. What is Value?")
st.markdown("""
Before building any model, you need to understand what you're actually trying to measure.

**The market price of a stock is not the same as its value.**

The market price is what someone is willing to pay for a share right now — driven by 
sentiment, news, momentum, fear, and greed. The **intrinsic value** is what the company 
is actually worth based on the cash it will generate over its lifetime.

The entire field of investment analysis is built on one idea:

> *"Price is what you pay. Value is what you get."* — Warren Buffett

When the market price is below intrinsic value, the stock may be undervalued — 
a potential buying opportunity. When it's above, it may be overvalued.

**Three main approaches to valuation:**
""")

a1, a2, a3 = st.columns(3)
with a1:
    st.markdown("**📊 Intrinsic Value (DCF)**")
    st.markdown("""
Value based on the company's own cash flows. Ask: *what cash will this business 
generate, and what is that worth today?*

Best for: stable, cash-generating companies.
    """)
with a2:
    st.markdown("**📈 Relative Valuation (Comps)**")
    st.markdown("""
Value based on how similar companies are priced. Ask: *if competitors trade at 
15x earnings, what should this company be worth?*

Best for: cross-checking DCF results.
    """)
with a3:
    st.markdown("**💰 Asset-Based Valuation**")
    st.markdown("""
Value based on what the company owns minus what it owes. Ask: *what would this 
business be worth if we sold everything today?*

Best for: asset-heavy or distressed companies.
    """)

st.divider()

# ══════════════════════════════════════════════════════════════
# SECTION 2 — FINANCIAL STATEMENTS
# ══════════════════════════════════════════════════════════════
st.header("2. The Three Financial Statements")
st.markdown("""
Every valuation starts with reading financial statements. There are three, and each 
tells you something different about the company.
""")

tab1, tab2, tab3 = st.tabs([
    "📋 Income Statement",
    "🏦 Balance Sheet",
    "💵 Cash Flow Statement"
])

with tab1:
    st.subheader("Income Statement — The Scorecard")
    st.markdown("""
The income statement shows how much money the company made and spent over a period 
(usually a quarter or a year). Think of it as the company's report card.

**Key line items:**
- **Revenue** — total sales
- **Cost of Revenue** — direct costs to produce goods/services
- **Gross Profit** = Revenue − Cost of Revenue
- **Operating Expenses** — salaries, rent, marketing, R&D
- **EBIT** (Earnings Before Interest & Tax) — operating profit
- **Net Income** — what's left after everything, including taxes and interest

**Why it matters for DCF:**
EBIT is the starting point for calculating free cash flow — the core of any DCF model.

**NVIDIA Example (FY2026):**
    """)
    nvda_income = {
        "Line Item": ["Revenue", "Cost of Revenue", "Gross Profit",
                      "Operating Income (EBIT)", "Net Income"],
        "Amount": ["$215.9B", "$62.5B", "$153.5B", "$130.4B", "$120.1B"],
        "Margin": ["100%", "28.9%", "71.1%", "60.4%", "55.6%"]
    }
    st.dataframe(pd.DataFrame(nvda_income), hide_index=True, use_container_width=True)

with tab2:
    st.subheader("Balance Sheet — The Snapshot")
    st.markdown("""
The balance sheet shows what the company **owns** (assets) and what it **owes** 
(liabilities) at a specific point in time. The difference is equity — what belongs 
to shareholders.

**The fundamental equation:**
> Assets = Liabilities + Equity

**Key items:**
- **Current Assets** — cash, receivables, inventory (liquid within 1 year)
- **Non-Current Assets** — property, equipment, goodwill
- **Current Liabilities** — debt due within 1 year, accounts payable
- **Total Debt** — all borrowings
- **Shareholders' Equity** — book value of the company

**Why it matters for DCF:**
- Cash and debt are used in the EV → equity value bridge
- Working capital changes affect free cash flow
- Shares outstanding convert equity value to per-share price
    """)

with tab3:
    st.subheader("Cash Flow Statement — The Reality Check")
    st.markdown("""
The cash flow statement shows actual cash moving in and out of the business. 
This is the most important statement for valuation because **cash is real — 
accounting earnings can be manipulated.**

**Three sections:**
- **Operating Cash Flow** — cash generated from the core business
- **Investing Cash Flow** — capex, acquisitions, asset sales
- **Financing Cash Flow** — debt issuance/repayment, dividends, buybacks

**Key items for DCF:**
- **D&A** (Depreciation & Amortization) — non-cash expense added back
- **Capital Expenditures (Capex)** — investment in long-term assets
- **Free Cash Flow** = Operating Cash Flow − Capex

**Why it matters:**
Free Cash Flow is what's left after running the business and maintaining assets. 
This is the cash available to all investors — the foundation of DCF valuation.
    """)

st.divider()

# ══════════════════════════════════════════════════════════════
# SECTION 3 — TIME VALUE OF MONEY
# ══════════════════════════════════════════════════════════════
st.header("3. Time Value of Money")
st.markdown("""
This is the most fundamental concept in all of finance. Everything else builds on it.

**The core idea:** $1 today is worth more than $1 in the future.

Why? Because $1 today can be invested and grow. If you can earn 10% per year, 
$1 today becomes $1.10 next year. So $1.10 next year is only worth $1 today.

This is called **discounting** — converting future cash flows back to their value today.
""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Future Value (compounding forward):**")
    st.latex(r"FV = PV \times (1 + r)^n")
    st.markdown("""
- PV = present value (today)
- r = interest/discount rate
- n = number of periods

*Example: $100 today at 10% for 3 years = $133.10*
    """)

with col2:
    st.markdown("**Present Value (discounting back):**")
    st.latex(r"PV = \frac{FV}{(1 + r)^n}")
    st.markdown("""
- FV = future cash flow
- r = discount rate (WACC)
- n = year of the cash flow

*Example: $133.10 in 3 years at 10% = $100 today*
    """)

st.markdown("**See it in action — how $100 grows over time:**")
rate = st.slider("Annual Return (%)", 1, 20, 10, 1)
years = list(range(1, 21))
values = [100 * (1 + rate/100) ** y for y in years]

fig = go.Figure()
fig.add_scatter(x=years, y=values, mode="lines+markers",
                line=dict(color="#1F4E79", width=3),
                marker=dict(size=6))
fig.update_layout(
    title=f"$100 growing at {rate}% per year",
    height=300,
    margin=dict(l=20, r=20, t=40, b=20),
    plot_bgcolor="white",
    xaxis=dict(title="Years", gridcolor="#EEEEEE"),
    yaxis=dict(title="Value ($)", gridcolor="#EEEEEE")
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════
# SECTION 4 — WHAT IS A DCF
# ══════════════════════════════════════════════════════════════
st.header("4. What is a DCF?")
st.markdown("""
A **Discounted Cash Flow (DCF)** model estimates a company's intrinsic value by 
forecasting its future free cash flows and discounting them back to today.

The logic is simple: a company is worth the sum of all the cash it will ever generate, 
expressed in today's dollars.
""")

st.markdown("**The DCF formula:**")
st.latex(r"Value = \sum_{t=1}^{n} \frac{UFCF_t}{(1+WACC)^t} + \frac{TV}{(1+WACC)^n}")

st.markdown("""
Where:
- **UFCF** = Unlevered Free Cash Flow (cash available to all investors)
- **WACC** = Weighted Average Cost of Capital (the discount rate)
- **TV** = Terminal Value (value of all cash flows beyond the forecast period)
- **n** = forecast horizon (typically 5 years)
""")

st.markdown("**How UFCF is calculated:**")
st.latex(r"UFCF = NOPAT + D\&A - Capex - \Delta NWC")

ufcf_steps = {
    "Step": ["EBIT", "× (1 − Tax Rate)", "= NOPAT",
             "+ D&A", "− Capex", "− ΔNWC", "= UFCF"],
    "What it means": [
        "Operating profit before interest and taxes",
        "Remove tax obligation",
        "Net Operating Profit After Tax — cash earnings from operations",
        "Add back non-cash depreciation charge",
        "Subtract investment in long-term assets",
        "Subtract increase in working capital needs",
        "Unlevered Free Cash Flow — available to all investors"
    ]
}
st.dataframe(pd.DataFrame(ufcf_steps), hide_index=True, use_container_width=True)

st.subheader("Terminal Value")
st.markdown("""
You can't forecast cash flows forever — so after year 5, you estimate a **Terminal Value** 
that captures all future cash flows beyond the forecast period.

The most common method is the **Gordon Growth Model:**
""")
st.latex(r"TV = \frac{UFCF_5 \times (1+g)}{WACC - g}")
st.markdown("""
Where **g** is the perpetual growth rate — typically set close to long-run GDP growth 
(2-3%). This assumption has a massive impact on valuation, which is why sensitivity 
analysis across different WACC and g combinations is essential.

**Important:** In most DCF models, terminal value represents 60-80% of total enterprise 
value. This means your terminal growth assumption matters more than your 5-year forecast.
""")

st.divider()

# ══════════════════════════════════════════════════════════════
# SECTION 5 — WACC
# ══════════════════════════════════════════════════════════════
st.header("5. WACC — The Discount Rate")
st.markdown("""
WACC stands for **Weighted Average Cost of Capital**. It represents the minimum return 
a company must generate to satisfy all its investors — both equity holders and debt holders.

It's used to discount future cash flows because it reflects the opportunity cost of 
investing in this company versus alternatives of similar risk.
""")

st.latex(r"WACC = \frac{E}{V} \times K_e + \frac{D}{V} \times K_d \times (1 - T)")

st.markdown("""
Where:
- **E/V** = equity as a proportion of total capital
- **D/V** = debt as a proportion of total capital
- **Ke** = cost of equity
- **Kd** = cost of debt (pre-tax)
- **T** = corporate tax rate
- **V** = E + D = total capital
""")

w1, w2 = st.columns(2)

with w1:
    st.subheader("Cost of Equity (Ke)")
    st.markdown("""
The return equity investors require for taking on the risk of owning the stock.
Calculated using the **Capital Asset Pricing Model (CAPM):**
    """)
    st.latex(r"K_e = R_f + \beta \times ERP")
    st.markdown("""
- **Rf** = Risk-free rate (10-year Treasury yield, currently ~4.2%)
- **β (Beta)** = sensitivity of the stock to market movements
    - β = 1.0 → moves with the market
    - β > 1.0 → more volatile than market (e.g. NVIDIA β = 2.38)
    - β < 1.0 → less volatile than market (e.g. utilities)
- **ERP** = Equity Risk Premium (~5.5% historically)

*NVIDIA example:*
Ke = 4.2% + 2.38 × 5.5% = **17.3%**
    """)

with w2:
    st.subheader("Cost of Debt (Kd)")
    st.markdown("""
The effective interest rate a company pays on its borrowings — adjusted for the 
tax deductibility of interest (the "tax shield").
    """)
    st.latex(r"K_d \text{ (after-tax)} = K_d \times (1 - T)")
    st.markdown("""
- **Kd** = Interest Expense / Total Debt
- Debt is cheaper than equity because:
    1. Debt holders have priority in bankruptcy
    2. Interest payments are tax-deductible
    3. Debt holders don't share in upside

This tax shield is why companies use some debt in their capital structure — 
up to the point where financial distress risk outweighs the benefit.
    """)

st.subheader("Interactive WACC Calculator")
st.markdown("Adjust the inputs to see how WACC changes:")

ic1, ic2 = st.columns(2)
with ic1:
    i_beta = st.slider("Beta (β)", 0.5, 3.0, 1.5, 0.1)
    i_rf   = st.slider("Risk-Free Rate (%)", 2.0, 6.0, 4.2, 0.1)
    i_erp  = st.slider("Equity Risk Premium (%)", 4.0, 7.0, 5.5, 0.1)

with ic2:
    i_kd   = st.slider("Cost of Debt (%)", 2.0, 10.0, 4.0, 0.1)
    i_tax  = st.slider("Tax Rate (%)", 10.0, 35.0, 21.0, 0.5)
    i_de   = st.slider("Debt / Total Capital (%)", 0.0, 60.0, 20.0, 1.0)

i_ke   = i_rf + i_beta * i_erp
i_we   = 1 - i_de / 100
i_wd   = i_de / 100
i_wacc = i_we * i_ke + i_wd * i_kd * (1 - i_tax/100)

r1, r2, r3 = st.columns(3)
r1.metric("Cost of Equity (Ke)", f"{i_ke:.2f}%")
r2.metric("After-Tax Cost of Debt", f"{i_kd * (1 - i_tax/100):.2f}%")
r3.metric("WACC", f"{i_wacc:.2f}%")

st.divider()

# ══════════════════════════════════════════════════════════════
# SECTION 6 — PUTTING IT TOGETHER
# ══════════════════════════════════════════════════════════════
st.header("6. Putting It All Together")
st.markdown("""
Once you have your UFCF forecasts and WACC, the final steps are:
""")

steps = {
    "Step": [
        "1. Discount each year's UFCF",
        "2. Sum all discounted cash flows",
        "3. Add terminal value (discounted)",
        "4. = Enterprise Value (EV)",
        "5. + Cash & equivalents",
        "6. − Total debt",
        "7. = Equity Value",
        "8. ÷ Diluted shares outstanding",
        "9. = Implied Share Price"
    ],
    "What it represents": [
        "PV of each year's free cash flow",
        "Total PV of forecast period cash flows",
        "PV of all cash flows beyond year 5",
        "Total value of the business to all investors",
        "Cash is already owned — add it back",
        "Debt must be repaid — subtract it",
        "What belongs to equity shareholders",
        "Distribute equity value across all shares",
        "Your DCF valuation per share"
    ]
}
st.dataframe(pd.DataFrame(steps), hide_index=True, use_container_width=True)

st.subheader("Why Sensitivity Analysis Matters")
st.markdown("""
A DCF is only as good as its assumptions. Small changes in WACC or terminal growth 
rate can move the implied price dramatically.

This is why professional analysts always present a **sensitivity table** — showing 
how the implied price changes across a range of WACC and terminal growth combinations.

In this platform, every valuation includes a 25-scenario sensitivity matrix. 
The goal is not to find one "right" number, but to understand the range of reasonable values.
""")

st.subheader("Common Mistakes to Avoid")
m1, m2, m3 = st.columns(3)
with m1:
    st.markdown("**❌ Extrapolating growth forever**")
    st.markdown("No company grows at 50% forever. Growth rates must decay toward a sustainable long-run rate.")

with m2:
    st.markdown("**❌ Ignoring terminal value sensitivity**")
    st.markdown("TV often represents 70-80% of EV. A 0.5% change in terminal growth can move your price by 20%.")

with m3:
    st.markdown("**❌ Using the wrong model**")
    st.markdown("DCF doesn't work for banks — use DDM or P/B multiples. This platform handles that automatically.")

st.divider()

# ══════════════════════════════════════════════════════════════
# SECTION 7 — DDM
# ══════════════════════════════════════════════════════════════
st.header("7. The Dividend Discount Model (DDM)")
st.markdown("""
The DCF model values a company based on its free cash flows. But for banks and 
financial institutions, free cash flow is difficult to define — debt is a raw 
material, not just a financing choice.

For these companies, analysts use the **Dividend Discount Model (DDM)** instead.

**The core idea:** A stock is worth the present value of all future dividends it will pay.
""")

st.latex(r"Value = \frac{D_1}{K_e - g}")

st.markdown("""
Where:
- **D1** = next year's expected dividend = D0 × (1 + g)
- **Ke** = cost of equity (required return)
- **g** = dividend growth rate (sustainable long-run rate)
- **Ke − g** = the spread between required return and growth

**When to use DDM:**
- Banks, insurance companies, financial institutions
- Companies with stable, predictable dividend histories
- When free cash flow is difficult to isolate from financing activities

**When NOT to use DDM:**
- Companies that don't pay dividends (e.g. Amazon, Berkshire Hathaway)
- High-growth companies reinvesting all earnings
- Companies where dividends are far below Free Cash Flow to Equity

**Why DDM alone understates bank valuations:**
Banks retain significant earnings beyond what they pay as dividends. TD Bank earns 
~$8-9 per share but pays ~$2.23 in dividends. DDM only sees the $2.23 and misses 
the rest. This is why this platform uses a **multi-method approach** for banks — 
combining DDM with P/B and P/E multiples for a more complete picture.
""")

st.divider()

# ══════════════════════════════════════════════════════════════
# SECTION 8 — EV VS EQUITY VALUE
# ══════════════════════════════════════════════════════════════
st.header("8. Enterprise Value vs. Equity Value")
st.markdown("""
One of the most commonly confused concepts in valuation is the difference between 
**Enterprise Value (EV)** and **Equity Value**.

**Enterprise Value** is the total value of the business — what it would cost to 
buy the entire company, including taking on its debt and receiving its cash.

**Equity Value** is what belongs specifically to shareholders after accounting 
for the company's financial obligations.
""")

st.latex(r"Equity\ Value = Enterprise\ Value + Cash - Debt")

bridge = {
    "Step": [
        "Enterprise Value",
        "+ Cash & Equivalents",
        "− Total Debt",
        "= Equity Value",
        "÷ Diluted Shares Outstanding",
        "= Implied Share Price"
    ],
    "Why": [
        "Total value of the operating business to all investors",
        "Cash already belongs to shareholders — add it back",
        "Debt must be repaid before shareholders get anything",
        "What equity investors actually own",
        "Spread equity value across all shares including diluted shares",
        "Your per-share intrinsic value estimate"
    ]
}
st.dataframe(pd.DataFrame(bridge), hide_index=True, use_container_width=True)

st.markdown("""
**A simple analogy:**

Imagine buying a house worth $500,000 (Enterprise Value). There's a $300,000 
mortgage on it (Debt), but there's also $20,000 cash sitting inside (Cash).

The equity value — what you actually own net of obligations:
$500,000 + $20,000 − $300,000 = **$220,000**

That's exactly the EV → equity bridge.

**Why it matters:**
Two companies can have the same Enterprise Value but very different equity values 
depending on how much cash and debt they carry. NVIDIA has $62.6B in cash — 
that gets added back. A heavily indebted company might have most of its EV 
absorbed by debt before shareholders see anything.
""")

st.divider()

# ══════════════════════════════════════════════════════════════
# SECTION 9 — READING A SENSITIVITY TABLE
# ══════════════════════════════════════════════════════════════
st.header("9. How to Read a Sensitivity Table")
st.markdown("""
Every valuation in this platform includes a **sensitivity table** — a grid showing 
how the implied share price changes across different combinations of WACC and 
terminal growth rate.

This is one of the most important outputs of any DCF model, and most people don't 
know how to use it properly.
""")

s1, s2 = st.columns(2)

with s1:
    st.subheader("What the table shows")
    st.markdown("""
- **Rows** = different terminal growth rate assumptions (2% to 4%)
- **Columns** = different WACC assumptions (8% to 12%)
- **Each cell** = the implied share price under that combination
- **Gold cell** = your base case assumption
- **Green** = higher implied prices (lower WACC or higher growth)
- **Red** = lower implied prices (higher WACC or lower growth)
    """)

with s2:
    st.subheader("How to use it")
    st.markdown("""
1. **Find the base case** — the gold highlighted cell
2. **Look at the range** — what's the spread from lowest to highest?
3. **Compare to market price** — at what assumptions does the model justify current price?
4. **Identify the break-even** — which WACC/growth combination matches market price exactly?
5. **Ask what you believe** — do your assumptions sit in green or red territory?
    """)

st.markdown("""
**The key insight:**

A DCF doesn't give you one answer — it gives you a **range of reasonable values** 
depending on your assumptions. The sensitivity table makes that range visible.

If the entire table is below market price, the stock is likely priced for perfection — 
the market is pricing in assumptions more optimistic than any cell in your table. 
If the entire table is above market price, the stock may be significantly undervalued 
under almost any reasonable assumption.

**Why terminal growth and WACC matter so much:**

Terminal value represents 60-80% of most DCF valuations. A 0.5% change in terminal 
growth rate can move the implied price by 15-25%. This is why the sensitivity table 
focuses on these two variables specifically — they are the two biggest sources of 
uncertainty in any long-term valuation.
""")


st.divider()
st.info("💡 **Ready to apply this?** Head to the **Valuation** page and try valuing a company yourself. Start with something familiar — Apple, NVIDIA, or a Canadian bank.")
st.caption("Content based on Damodaran (2025) Investment Valuation — Wiley, 4th University Edition")
