import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import date

st.set_page_config(
    page_title="DCF Valuation Platform",
    page_icon="📈",
    layout="wide"
)

# ── Currency Helpers ──────────────────────────────────────────
def get_exchange_rate():
    try:
        rate = yf.Ticker("CAD=X").info.get("regularMarketPrice", 1.36)
        return float(rate)
    except:
        return 1.36

def get_company_currency(info):
    return info.get("currency", "USD")

# ── WACC Calculator ───────────────────────────────────────────
def compute_wacc(ticker_symbol):
    try:
        t    = yf.Ticker(ticker_symbol)
        info = t.info

        beta = float(info.get("beta", 1.0) or 1.0)
        if beta != beta:
            beta = 1.0

        try:
            rf = yf.Ticker("^TNX").info.get("regularMarketPrice", 4.2) / 100
        except:
            rf = 0.042

        erp = 0.055
        ke  = rf + beta * erp

        income = t.financials
        bs     = t.balance_sheet

        def get_val(df, keys):
            for k in keys:
                if k in df.index:
                    v = df.loc[k].iloc[0]
                    if v and v == v:
                        return abs(float(v))
            return None

        interest_exp = get_val(income, ["Interest Expense"])
        total_debt   = get_val(bs,     ["Total Debt"])
        total_equity = get_val(bs,     ["Total Stockholder Equity",
                                         "Stockholders Equity",
                                         "Common Stock Equity"])
        tax_prov     = get_val(income, ["Tax Provision"])
        pretax       = get_val(income, ["Pretax Income"])

        kd = min(interest_exp / total_debt, 0.15) if interest_exp and total_debt and total_debt > 0 else 0.04
        tr = max(0.05, min(tax_prov / pretax, 0.35)) if tax_prov and pretax and pretax > 0 else 0.21

        if total_debt and total_equity:
            total_cap = total_debt + total_equity
            wd, we = total_debt / total_cap, total_equity / total_cap
        else:
            wd, we = 0.10, 0.90

        wacc_val = round(max(6.0, min(((we * ke) + (wd * kd * (1 - tr))) * 100, 18.0)), 1)
        return wacc_val, round(beta, 2), round(rf * 100, 2), round(ke * 100, 2), round(kd * 100, 2)
    except:
        return 10.0, 1.0, 4.2, 9.7, 4.0

# ── Historical Drivers (IMPROVEMENT 2, 3, 4, 6) ──────────────
def compute_historical_drivers(income, bs, cf):
    """Auto-compute EBIT margin, tax rate, NWC%, and revenue CAGR from financials."""
    try:
        def get_row(df, keys):
            for k in keys:
                if k in df.index:
                    return df.loc[k]
            return pd.Series(dtype=float)

        revenue   = get_row(income, ["Total Revenue"]).dropna()
        op_income = get_row(income, ["Operating Income"]).dropna()
        tax_prov  = get_row(income, ["Tax Provision"]).dropna()
        pretax    = get_row(income, ["Pretax Income"]).dropna()
        curr_assets = get_row(bs,   ["Current Assets"]).dropna()
        curr_liab   = get_row(bs,   ["Current Liabilities"]).dropna()

        # EBIT margin — average of last 3 years
        if len(revenue) >= 2 and len(op_income) >= 2:
            margins = []
            for i in range(min(3, len(revenue), len(op_income))):
                if revenue.iloc[i] > 0:
                    margins.append(op_income.iloc[i] / revenue.iloc[i])
            ebit_margin = round(np.mean(margins) * 100, 1) if margins else 25.0
            ebit_margin = max(5.0, min(ebit_margin, 75.0))
        else:
            ebit_margin = 25.0

        # Effective tax rate — average of last 3 years
        if len(tax_prov) >= 1 and len(pretax) >= 1:
            rates = []
            for i in range(min(3, len(tax_prov), len(pretax))):
                if pretax.iloc[i] > 0:
                    rates.append(tax_prov.iloc[i] / pretax.iloc[i])
            tax_rate = round(np.mean(rates) * 100, 1) if rates else 21.0
            tax_rate = max(5.0, min(tax_rate, 35.0))
        else:
            tax_rate = 21.0

        # NWC % of revenue change
        if len(curr_assets) >= 2 and len(curr_liab) >= 2 and len(revenue) >= 2:
            nwc_changes = []
            for i in range(min(3, len(curr_assets)-1, len(curr_liab)-1)):
                nwc_curr = curr_assets.iloc[i] - curr_liab.iloc[i]
                nwc_prev = curr_assets.iloc[i+1] - curr_liab.iloc[i+1]
                rev_curr = revenue.iloc[i]
                rev_prev = revenue.iloc[i+1]
                if rev_curr != rev_prev:
                    nwc_changes.append(abs((nwc_curr - nwc_prev) / (rev_curr - rev_prev)))
            nwc_pct = round(np.mean(nwc_changes) * 100, 1) if nwc_changes else 3.0
            nwc_pct = max(0.0, min(nwc_pct, 15.0))
        else:
            nwc_pct = 3.0

        # Revenue CAGR (last 3 years → Year 1 default growth)
        if len(revenue) >= 2:
            years = min(3, len(revenue) - 1)
            cagr = (revenue.iloc[0] / revenue.iloc[years]) ** (1 / years) - 1
            cagr = round(max(0.0, min(cagr * 100, 80.0)), 1)
        else:
            cagr = 10.0

        return ebit_margin, tax_rate, nwc_pct, cagr

    except:
        return 25.0, 21.0, 3.0, 10.0

# ── DDM Engine ────────────────────────────────────────────────
def run_ddm_engine(ticker_symbol):
    try:
        t    = yf.Ticker(ticker_symbol)
        info = t.info

        _, beta, rf, ke, _ = compute_wacc(ticker_symbol)
        ke_decimal = ke / 100

        divs = t.dividends
        if divs is None or len(divs) < 4:
            return None, None, None, None, None, "Insufficient dividend history"

        annual_divs = divs.resample("YE").sum()
        if len(annual_divs) < 2:
            return None, None, None, None, None, "Insufficient annual dividend data"

        d0 = float(annual_divs.iloc[-1])
        if d0 <= 0:
            return None, None, None, None, None, "No dividends paid"

        # IMPROVEMENT 8 — extended lookback for dividend growth
        if len(annual_divs) >= 6:
            d_start = float(annual_divs.iloc[-6])
            years   = 5
        elif len(annual_divs) >= 4:
            d_start = float(annual_divs.iloc[-4])
            years   = 3
        else:
            d_start = float(annual_divs.iloc[0])
            years   = len(annual_divs) - 1

        if d_start <= 0 or years <= 0:
            g = 0.04
        else:
            g = (d0 / d_start) ** (1 / years) - 1
            # IMPROVEMENT 8 — removed aggressive 1% floor, now 2%
            g = max(0.02, min(g, 0.10))

        if ke_decimal <= g:
            ke_decimal = g + 0.02

        d1    = d0 * (1 + g)
        value = d1 / (ke_decimal - g)

        pe_ratio = info.get("trailingPE", None)
        pb_ratio = info.get("priceToBook", None)

        return round(value, 2), round(g * 100, 2), round(d0, 4), pe_ratio, pb_ratio, None

    except Exception as e:
        return None, None, None, None, None, str(e)

# ── DCF Engine ────────────────────────────────────────────────
def run_dcf_engine(base_revenue, base_cash, base_debt, base_shares,
                   base_da_pct, base_capex_pct,
                   growth_rates, ebit_margin, wacc, tg,
                   tax_rate=0.21, nwc_pct=0.03):
    revenues, ufcf_list, pv_list = [], [], []
    rev      = base_revenue
    prev_rev = base_revenue

    for i, g in enumerate(growth_rates):
        rev      = rev * (1 + g)
        nopat    = rev * ebit_margin * (1 - tax_rate)
        da       = rev * base_da_pct
        capex    = rev * base_capex_pct
        dnwc     = (rev - prev_rev) * nwc_pct
        ufcf     = nopat + da - capex - dnwc
        pv       = ufcf / ((1 + wacc) ** (i + 1))
        revenues.append(rev)
        ufcf_list.append(ufcf)
        pv_list.append(pv)
        prev_rev = rev

    tv    = (ufcf_list[-1] * (1 + tg)) / (wacc - tg)
    pv_tv = tv / ((1 + wacc) ** 5)
    ev    = sum(pv_list) + pv_tv
    eq    = ev + base_cash - base_debt
    price = eq / base_shares
    return revenues, ufcf_list, pv_list, pv_tv, ev, eq, price

# ── Sensitivity ───────────────────────────────────────────────
def build_sensitivity(base_revenue, base_cash, base_debt, base_shares,
                      base_da_pct, base_capex_pct, growth_rates,
                      ebit_margin, tax_rate, nwc_pct):
    wacc_range = [0.08, 0.09, 0.10, 0.11, 0.12]
    tg_range   = [0.02, 0.025, 0.03, 0.035, 0.04]
    rows = {}
    for tg in tg_range:
        row = {}
        for w in wacc_range:
            _, _, _, _, _, _, p = run_dcf_engine(
                base_revenue, base_cash, base_debt, base_shares,
                base_da_pct, base_capex_pct, growth_rates,
                ebit_margin, w, tg, tax_rate, nwc_pct)
            row[f"{w*100:.1f}%"] = round(p, 2)
        rows[f"{tg*100:.1f}%"] = row
    return pd.DataFrame(rows).T

# ── Financial Sector Detection ────────────────────────────────
FINANCIAL_SECTORS = ["Financial Services", "Insurance"]

def is_financial(sector):
    return sector in FINANCIAL_SECTORS

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    ticker_input = st.text_input(
        "Enter Ticker Symbol",
        value="NVDA",
        placeholder="e.g. AAPL, MSFT, NVDA, RY.TO, TD"
    ).upper().strip()

    currency_display = st.radio(
        "Display Currency",
        ["USD", "CAD"],
        horizontal=True
    )

    st.subheader("Scenario")
    scenario = st.selectbox(
        "Select Scenario",
        ["Base Case", "Bull Case", "Bear Case"]
    )

    st.subheader("DCF Assumptions")

    computed_wacc, beta, rf, ke, kd = compute_wacc(ticker_input)

    with st.expander("📐 WACC Calculator (auto-computed)"):
        w1, w2 = st.columns(2)
        w1.metric("Beta",           f"{beta}")
        w2.metric("Risk-Free Rate", f"{rf}%")
        w1.metric("Cost of Equity", f"{ke}%")
        w2.metric("Cost of Debt",   f"{kd}%")
        st.caption("CAPM: Ke = Rf + β × ERP (5.5%) | Kd = Interest Expense / Total Debt")

    wacc = st.slider("WACC (%)", 6.0, 18.0, float(computed_wacc), 0.5) / 100
    tg   = st.slider("Terminal Growth (%)", 1.0, 5.0, 3.0, 0.5) / 100

    st.subheader("Growth Assumptions")
    if scenario == "Bull Case":
        growth_multiplier   = 1.3
        ebit_boost          = 5.0
    elif scenario == "Bear Case":
        growth_multiplier   = 0.6
        ebit_boost          = -5.0
    else:
        growth_multiplier   = 1.0
        ebit_boost          = 0.0

    run_button = st.button("🚀 Run Valuation", type="primary", use_container_width=True)

# ── Main App ──────────────────────────────────────────────────
if run_button or True:
    with st.spinner(f"Fetching data for {ticker_input}..."):
        try:
            ticker       = yf.Ticker(ticker_input)
            info         = ticker.info
            name         = info.get("longName", ticker_input)
            market_price = info.get("currentPrice", 0)
            sector       = info.get("sector", "N/A")
            industry     = info.get("industry", "N/A")

            company_currency = get_company_currency(info)
            usd_cad_rate     = get_exchange_rate()

            if currency_display == "CAD" and company_currency == "USD":
                fx_rate     = usd_cad_rate
                fx_note     = f"Displaying in CAD (rate: {usd_cad_rate:.4f})"
                curr_symbol = "CA$"
            elif currency_display == "USD" and company_currency == "CAD":
                fx_rate     = 1 / usd_cad_rate
                fx_note     = f"Displaying in USD (rate: {1/usd_cad_rate:.4f})"
                curr_symbol = "$"
            else:
                fx_rate     = 1.0
                fx_note     = company_currency
                curr_symbol = "CA$" if company_currency == "CAD" else "$"

            display_market_price = market_price * fx_rate
            use_ddm = is_financial(sector)

            # Pull financials for driver computation
            income = ticker.financials
            bs     = ticker.balance_sheet
            cf     = ticker.cashflow

            # IMPROVEMENTS 2, 3, 4, 6 — auto-compute drivers
            auto_ebit_margin, auto_tax_rate, auto_nwc_pct, auto_cagr = \
                compute_historical_drivers(income, bs, cf)

        except Exception as e:
            st.error(f"Error fetching data: {e}")
            st.stop()

    # ── Company Header ────────────────────────────────────────
    st.title("📈 DCF Valuation Platform")
    st.markdown("*Automated DCF & DDM valuation for any public company*")
    st.divider()

    st.subheader(f"{name} ({ticker_input})")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Sector",   sector)
    col2.metric("Industry", industry)
    col3.metric("Scenario", scenario)
    col4.metric("Currency", fx_note)

    if use_ddm:
        st.info("🏦 **Financial company detected** — using Multi-Method Valuation (DDM + P/B + P/E)")
    st.divider()

    # ══════════════════════════════════════════════════════════
    # DDM PATH
    # ══════════════════════════════════════════════════════════
    if use_ddm:
        with st.spinner("Running DDM valuation..."):
            ddm_price, div_growth, d0, pe_ratio, pb_ratio, error = run_ddm_engine(ticker_input)

        if error:
            st.error(f"DDM Error: {error}")
            st.warning("This company may not pay dividends or has insufficient history.")
        else:
            display_ddm_price = ddm_price * fx_rate
            upside = (display_ddm_price - display_market_price) / display_market_price * 100

            # ── P/B and P/E implied prices ────────────────────
            pb_ratio = info.get("priceToBook", None)
            pe_ratio = info.get("trailingPE", None)
            bvps = info.get("bookValue", None)
            eps = info.get("trailingEps", None)

            # Sector average P/B and P/E for banks
            sector_avg_pb = 1.5
            sector_avg_pe = 12.0

            pb_implied = round(bvps * sector_avg_pb * fx_rate, 2) if bvps else None
            pe_implied = round(eps * sector_avg_pe * fx_rate, 2) if eps else None

            # Blended average
            valid_prices = [p for p in [display_ddm_price, pb_implied, pe_implied] if p and p > 0]
            blended = round(sum(valid_prices) / len(valid_prices), 2) if valid_prices else None
            blended_upside = (blended - display_market_price) / display_market_price * 100 if blended else None

            st.subheader("📊 Financial Company Valuation — Multi-Method")
            st.caption(
                "Banks are valued using DDM + P/B + P/E multiples. DDM alone understates value because banks retain significant earnings beyond dividends.")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("DDM Implied", f"{curr_symbol}{display_ddm_price:,.2f}",
                      help="Dividend Discount Model — conservative floor value")
            m2.metric("P/B Implied", f"{curr_symbol}{pb_implied:,.2f}" if pb_implied else "N/A",
                      help=f"Book Value × Sector Avg P/B ({sector_avg_pb}x)")
            m3.metric("P/E Implied", f"{curr_symbol}{pe_implied:,.2f}" if pe_implied else "N/A",
                      help=f"EPS × Sector Avg P/E ({sector_avg_pe}x)")
            m4.metric("Blended Value", f"{curr_symbol}{blended:,.2f}" if blended else "N/A",
                      help="Simple average of DDM, P/B, and P/E implied prices")

            st.divider()

            b1, b2, b3 = st.columns(3)
            b1.metric("Market Price", f"{curr_symbol}{display_market_price:,.2f}")
            b2.metric("Upside (Blended)", f"{blended_upside:+.1f}%" if blended_upside else "N/A",
                      delta=f"{blended_upside:+.1f}%" if blended_upside else None,
                      delta_color="normal")
            b3.metric("Div Growth Rate", f"{div_growth:.1f}%")

            st.divider()

            st.subheader("📋 Key Metrics")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Annual Dividend (D0)", f"{curr_symbol}{d0 * fx_rate:,.4f}")
            k2.metric("Cost of Equity (Ke)",  f"{ke:.2f}%")
            k3.metric("P/E Ratio",             f"{pe_ratio:.1f}x" if pe_ratio else "N/A")
            k4.metric("P/B Ratio",             f"{pb_ratio:.2f}x" if pb_ratio else "N/A")

            st.divider()

            st.subheader("🎯 DDM Sensitivity Analysis")
            st.caption("Implied Share Price | Rows = Dividend Growth Rate | Cols = Cost of Equity")

            ke_range = [ke-2, ke-1, ke, ke+1, ke+2]
            g_range  = [max(1, div_growth-2), max(1, div_growth-1),
                        div_growth, div_growth+1, div_growth+2]

            ddm_rows = {}
            for g_val in g_range:
                row = {}
                for ke_val in ke_range:
                    if ke_val <= g_val:
                        row[f"{ke_val:.1f}%"] = "N/A"
                    else:
                        d1_val = d0 * (1 + g_val/100)
                        v = round((d1_val / (ke_val/100 - g_val/100)) * fx_rate, 2)
                        row[f"{ke_val:.1f}%"] = v
                ddm_rows[f"{g_val:.1f}%"] = row

            ddm_sens = pd.DataFrame(ddm_rows).T
            st.dataframe(
                ddm_sens.style.background_gradient(cmap="RdYlGn", axis=None),
                use_container_width=True
            )

            st.divider()

            st.subheader("📈 Dividend History")
            try:
                divs        = yf.Ticker(ticker_input).dividends
                annual_divs = divs.resample("YE").sum()
                fig_div = go.Figure()
                fig_div.add_bar(
                    x=[str(y)[:4] for y in annual_divs.index],
                    y=(annual_divs * fx_rate).tolist(),
                    marker_color="#1F4E79"
                )
                fig_div.update_layout(
                    title=f"Annual Dividends Per Share ({curr_symbol})",
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    plot_bgcolor="white",
                    yaxis=dict(gridcolor="#EEEEEE")
                )
                st.plotly_chart(fig_div, use_container_width=True)
            except:
                st.warning("Could not load dividend history chart.")

            st.divider()
            st.caption(
                f"Valuation Date: {date.today()} | Model: DDM | "
                f"D0: {curr_symbol}{d0*fx_rate:.4f} | "
                f"Div Growth: {div_growth:.1f}% | "
                f"Ke: {ke:.2f}% | Currency: {fx_note}"
            )

    # ══════════════════════════════════════════════════════════
    # DCF PATH
    # ══════════════════════════════════════════════════════════
    else:
        # ── Sliders with auto-computed defaults ───────────────
        with st.sidebar:
            st.subheader("📊 Model Assumptions")
            st.caption("Auto-computed from historical financials — adjust as needed")

            if scenario == "Bull Case":
                default_yr1  = min(auto_cagr * 1.3, 80.0)
                default_ebit = min(auto_ebit_margin + 5.0, 75.0)
            elif scenario == "Bear Case":
                default_yr1  = max(auto_cagr * 0.6, 0.0)
                default_ebit = max(auto_ebit_margin - 5.0, 5.0)
            else:
                default_yr1  = auto_cagr
                default_ebit = auto_ebit_margin

            yr1 = st.slider("Year 1 Growth (%)", 0.0, 100.0, float(round(default_yr1, 1)), 0.5)
            yr2 = st.slider("Year 2 Growth (%)", 0.0, 80.0,  float(round(default_yr1 * 0.75, 1)), 0.5)
            yr3 = st.slider("Year 3 Growth (%)", 0.0, 60.0,  float(round(default_yr1 * 0.55, 1)), 0.5)
            yr4 = st.slider("Year 4 Growth (%)", 0.0, 40.0,  float(round(default_yr1 * 0.40, 1)), 0.5)
            yr5 = st.slider("Year 5 Growth (%)", 0.0, 30.0,  float(round(default_yr1 * 0.28, 1)), 0.5)

            ebit_margin = st.slider(
                "EBIT Margin (%)", 1.0, 80.0,
                float(round(default_ebit, 1)), 0.5
            ) / 100

            # IMPROVEMENT 3 — tax rate slider with auto default
            tax_rate_input = st.slider(
                "Tax Rate (%)", 5.0, 35.0,
                float(round(auto_tax_rate, 1)), 0.5
            ) / 100

            # IMPROVEMENT 4 — NWC slider with auto default
            nwc_pct_input = st.slider(
                "NWC % of Rev Change", 0.0, 15.0,
                float(round(auto_nwc_pct, 1)), 0.5
            ) / 100

        with st.spinner("Running DCF valuation..."):
            try:
                def get_row(df, keys):
                    for k in keys:
                        if k in df.index:
                            return df.loc[k]
                    return pd.Series(dtype=float)

                revenue   = get_row(income, ["Total Revenue"])
                op_income = get_row(income, ["Operating Income"])
                da        = get_row(cf,     ["Depreciation And Amortization",
                                              "Depreciation Amortization Depletion"])
                capex     = get_row(cf,     ["Capital Expenditure"])
                cash      = get_row(bs,     ["Cash And Cash Equivalents",
                                              "Cash Cash Equivalents And Short Term Investments"])
                debt      = get_row(bs,     ["Total Debt"])

                # IMPROVEMENT 1 — use diluted shares
                diluted_shares = get_row(income, ["Diluted Average Shares"])
                basic_shares   = get_row(bs,     ["Share Issued", "Ordinary Shares Number"])
                shares = diluted_shares if len(diluted_shares.dropna()) > 0 else basic_shares

                valid_rev = revenue.dropna()
                if len(valid_rev) < 2:
                    st.error("Not enough data for this ticker.")
                    st.stop()

                base_revenue   = float(valid_rev.iloc[0])
                base_cash      = abs(float(cash.dropna().iloc[0]))
                base_debt      = abs(float(debt.dropna().iloc[0]))
                base_shares    = abs(float(shares.dropna().iloc[0]))
                base_da_pct    = abs(float(da.dropna().iloc[0])) / base_revenue
                base_capex_pct = abs(float(capex.dropna().iloc[0])) / base_revenue

                # IMPROVEMENT 9 — buyback adjustment
                try:
                    buybacks = get_row(cf, ["Repurchase Of Capital Stock",
                                             "Common Stock Payments"]).dropna()
                    if len(buybacks) >= 2:
                        avg_buyback = abs(float(buybacks.iloc[0]))
                        buyback_pct = avg_buyback / (base_shares * market_price) if market_price > 0 else 0
                        buyback_pct = min(buyback_pct, 0.05)
                        adjusted_shares = base_shares * ((1 - buyback_pct) ** 3)
                    else:
                        adjusted_shares = base_shares
                except:
                    adjusted_shares = base_shares

                growth_rates = [yr1/100, yr2/100, yr3/100, yr4/100, yr5/100]

                revenues, ufcf_list, pv_list, pv_tv, ev, eq, price = run_dcf_engine(
                    base_revenue, base_cash, base_debt, adjusted_shares,
                    base_da_pct, base_capex_pct,
                    growth_rates, ebit_margin, wacc, tg,
                    tax_rate_input, nwc_pct_input
                )

                display_price = price * fx_rate# Floor — equity value cannot be negative
                if eq < 0:
                    st.warning(
                        f"⚠️ **{name}** has negative UFCF under current assumptions — "
                        f"this typically indicates a capex-heavy business model "
                        f"(e.g. Amazon, Tesla) where standard DCF understates value. "
                        f"Try raising the EBIT margin or lowering capex assumptions."
                    )
                    st.stop()

                display_price = price * fx_rate
                display_ev    = ev * fx_rate
                upside        = (display_price - display_market_price) / display_market_price * 100

                # IMPROVEMENT 5 — TV as % of EV
                tv_pct_of_ev  = (pv_tv / ev * 100) if ev > 0 else 0

                hist_rev   = valid_rev.sort_index().tolist()
                hist_years = [str(y)[:4] for y in valid_rev.sort_index().index.tolist()]
                hist_ebit  = op_income.dropna().sort_index().tolist()

            except Exception as e:
                st.error(f"DCF Error: {e}")
                st.stop()

        # ── Key Metrics ───────────────────────────────────────
        st.subheader("📊 Valuation Results")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Implied Share Price", f"{curr_symbol}{display_price:,.2f}")
        m2.metric("Market Price",         f"{curr_symbol}{display_market_price:,.2f}")
        m3.metric("Upside / Downside",    f"{upside:+.1f}%",
                  delta=f"{upside:+.1f}%", delta_color="normal")
        m4.metric("Enterprise Value",     f"{curr_symbol}{display_ev/1e9:,.1f}B")
        # IMPROVEMENT 5 — show TV % of EV
        m5.metric("Terminal Value % of EV", f"{tv_pct_of_ev:.1f}%",
                  help="The higher this is, the more sensitive your valuation is to terminal growth assumptions")

        st.divider()

        # ── Model Assumptions Used ────────────────────────────
        with st.expander("📋 Model Assumptions Used"):
            a1, a2, a3, a4 = st.columns(4)
            a1.metric("EBIT Margin",  f"{ebit_margin*100:.1f}%",
                      help="3-year historical average")
            a2.metric("Tax Rate",     f"{tax_rate_input*100:.1f}%",
                      help="Effective rate from financials")
            a3.metric("NWC % Rev Δ", f"{nwc_pct_input*100:.1f}%",
                      help="Historical NWC change as % of revenue change")
            a4.metric("Yr1 Growth",  f"{yr1:.1f}%",
                      help="Anchored to 3-year revenue CAGR")

        st.divider()

        # ── Charts Row 1 ──────────────────────────────────────
        st.subheader("📈 Historical Performance")
        c1, c2 = st.columns(2)

        with c1:
            fig_rev = go.Figure()
            fig_rev.add_bar(x=hist_years, y=[r/1e9 for r in hist_rev],
                            marker_color="#1F4E79", name="Revenue")
            fig_rev.update_layout(
                title=f"Revenue ({curr_symbol}B)", height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                plot_bgcolor="white", yaxis=dict(gridcolor="#EEEEEE"))
            st.plotly_chart(fig_rev, use_container_width=True)

        with c2:
            ebit_margins = [e/r*100 for e, r in zip(hist_ebit, hist_rev[:len(hist_ebit)])]
            fig_margin = go.Figure()
            fig_margin.add_scatter(
                x=hist_years[:len(ebit_margins)], y=ebit_margins,
                mode="lines+markers",
                line=dict(color="#F4B942", width=3), marker=dict(size=8))
            fig_margin.update_layout(
                title="EBIT Margin (%)", height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                plot_bgcolor="white", yaxis=dict(gridcolor="#EEEEEE"))
            st.plotly_chart(fig_margin, use_container_width=True)

        # ── Charts Row 2 ──────────────────────────────────────
        st.subheader("🔮 5-Year Forecast")
        forecast_years = ["2027E", "2028E", "2029E", "2030E", "2031E"]
        c3, c4 = st.columns(2)

        with c3:
            fig_fcst = go.Figure()
            fig_fcst.add_bar(x=forecast_years, y=[r/1e9 for r in revenues],
                             marker_color="#1F4E79", name="Revenue")
            fig_fcst.update_layout(
                title=f"Forecast Revenue ({curr_symbol}B)", height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                plot_bgcolor="white", yaxis=dict(gridcolor="#EEEEEE"))
            st.plotly_chart(fig_fcst, use_container_width=True)

        with c4:
            fig_ufcf = go.Figure()
            fig_ufcf.add_bar(x=forecast_years, y=[u/1e9 for u in ufcf_list],
                             marker_color="#2ECC71", name="UFCF")
            fig_ufcf.update_layout(
                title=f"Forecast UFCF ({curr_symbol}B)", height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                plot_bgcolor="white", yaxis=dict(gridcolor="#EEEEEE"))
            st.plotly_chart(fig_ufcf, use_container_width=True)

        # ── Valuation Bridge ──────────────────────────────────
        st.subheader("🌉 Valuation Bridge")
        fig_wf = go.Figure(go.Waterfall(
            name="Bridge", orientation="v",
            measure=["relative","relative","total","relative","relative","total"],
            x=["PV Cash Flows","PV Terminal Value","Enterprise Value",
               "+ Cash","- Debt","Equity Value"],
            y=[sum(pv_list)/1e9, pv_tv/1e9, 0,
               base_cash/1e9, -base_debt/1e9, 0],
            connector={"line": {"color": "#CCCCCC"}},
            increasing={"marker": {"color": "#1F4E79"}},
            decreasing={"marker": {"color": "#E74C3C"}},
            totals={"marker": {"color": "#F4B942"}}
        ))
        fig_wf.update_layout(
            height=350, margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#EEEEEE", title=f"{curr_symbol}B"))
        st.plotly_chart(fig_wf, use_container_width=True)

        # ── Sensitivity Table ─────────────────────────────────
        st.subheader("🎯 Sensitivity Analysis")
        st.caption(f"Implied Share Price ({curr_symbol}) | Rows = Terminal Growth | Cols = WACC")

        sens_df = build_sensitivity(
            base_revenue, base_cash, base_debt, adjusted_shares,
            base_da_pct, base_capex_pct, growth_rates,
            ebit_margin, tax_rate_input, nwc_pct_input
        )

        if fx_rate != 1.0:
            sens_df = sens_df * fx_rate

        st.dataframe(
            sens_df.style.background_gradient(cmap="RdYlGn", axis=None)
                         .format(f"{curr_symbol}{{:.2f}}"),
            use_container_width=True
        )

        # ── DCF Table ─────────────────────────────────────────
        st.subheader("📋 DCF Forecast Table")
        dcf_table = pd.DataFrame({
            "Year":                         forecast_years,
            f"Revenue ({curr_symbol}B)":    [f"{curr_symbol}{r*fx_rate/1e9:,.1f}" for r in revenues],
            f"EBIT ({curr_symbol}B)":       [f"{curr_symbol}{r*ebit_margin*fx_rate/1e9:,.1f}" for r in revenues],
            f"UFCF ({curr_symbol}B)":       [f"{curr_symbol}{u*fx_rate/1e9:,.1f}" for u in ufcf_list],
            f"PV of UFCF ({curr_symbol}B)": [f"{curr_symbol}{p*fx_rate/1e9:,.1f}" for p in pv_list],
        })
        st.dataframe(dcf_table, use_container_width=True, hide_index=True)

        # ── Extended Company Data (IMPROVEMENT — bonus) ───────
        with st.expander("➕ More Company Data"):
            st.subheader("Profitability")
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Gross Margin",  f"{info.get('grossMargins', 0)*100:.1f}%" if info.get('grossMargins') else "N/A")
            p2.metric("Net Margin",    f"{info.get('profitMargins', 0)*100:.1f}%" if info.get('profitMargins') else "N/A")
            p3.metric("ROE",           f"{info.get('returnOnEquity', 0)*100:.1f}%" if info.get('returnOnEquity') else "N/A")
            p4.metric("ROA",           f"{info.get('returnOnAssets', 0)*100:.1f}%" if info.get('returnOnAssets') else "N/A")

            st.subheader("Valuation Multiples")
            v1, v2, v3, v4 = st.columns(4)
            v1.metric("P/E Ratio",    f"{info.get('trailingPE', 0):.1f}x" if info.get('trailingPE') else "N/A")
            v2.metric("Forward P/E",  f"{info.get('forwardPE', 0):.1f}x" if info.get('forwardPE') else "N/A")
            v3.metric("EV/EBITDA",    f"{info.get('enterpriseToEbitda', 0):.1f}x" if info.get('enterpriseToEbitda') else "N/A")
            v4.metric("P/B Ratio",    f"{info.get('priceToBook', 0):.1f}x" if info.get('priceToBook') else "N/A")

            st.subheader("Liquidity")
            l1, l2, l3, l4 = st.columns(4)
            l1.metric("Current Ratio", f"{info.get('currentRatio', 0):.2f}" if info.get('currentRatio') else "N/A")
            l2.metric("Quick Ratio",   f"{info.get('quickRatio', 0):.2f}" if info.get('quickRatio') else "N/A")
            l3.metric("Rev Growth",    f"{info.get('revenueGrowth', 0)*100:.1f}%" if info.get('revenueGrowth') else "N/A")
            l4.metric("EPS Growth",    f"{info.get('earningsGrowth', 0)*100:.1f}%" if info.get('earningsGrowth') else "N/A")

        st.divider()
        st.caption(
            f"Valuation Date: {date.today()} | Model: DCF | "
            f"WACC: {wacc*100:.1f}% | "
            f"Terminal Growth: {tg*100:.1f}% | "
            f"EBIT Margin: {ebit_margin*100:.1f}% | "
            f"Tax Rate: {tax_rate_input*100:.1f}% | "
            f"Currency: {fx_note}"
        )
