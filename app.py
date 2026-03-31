import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import date

# ── Page Config ───────────────────────────────────────────────
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

# ── WACC / Cost of Equity Calculator ─────────────────────────
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

        if len(annual_divs) >= 4:
            d_start = float(annual_divs.iloc[-4])
            years   = 3
        else:
            d_start = float(annual_divs.iloc[0])
            years   = len(annual_divs) - 1

        if d_start <= 0 or years <= 0:
            g = 0.03
        else:
            g = (d0 / d_start) ** (1 / years) - 1
            g = max(0.01, min(g, 0.10))

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
                   tax_rate=0.15, nwc_pct=0.03):
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
                      base_da_pct, base_capex_pct, growth_rates, ebit_margin):
    wacc_range = [0.08, 0.09, 0.10, 0.11, 0.12]
    tg_range   = [0.02, 0.025, 0.03, 0.035, 0.04]
    rows = {}
    for tg in tg_range:
        row = {}
        for w in wacc_range:
            _, _, _, _, _, _, p = run_dcf_engine(
                base_revenue, base_cash, base_debt, base_shares,
                base_da_pct, base_capex_pct, growth_rates, ebit_margin, w, tg)
            row[f"{w*100:.1f}%"] = round(p, 2)
        rows[f"{tg*100:.1f}%"] = row
    return pd.DataFrame(rows).T

# ── Financial Sector Detection ────────────────────────────────
FINANCIAL_SECTORS = ["Financial Services", "Insurance"]

def is_financial(sector):
    return sector in FINANCIAL_SECTORS

# ── Header ────────────────────────────────────────────────────
st.title("📈 DCF Valuation Platform")
st.markdown("*Automated DCF & DDM valuation for any public company*")
st.divider()

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
        default_growth      = [55, 40, 30, 20, 15]
        ebit_margin_default = 60
    elif scenario == "Bear Case":
        default_growth      = [20, 15, 10, 8, 5]
        ebit_margin_default = 40
    else:
        default_growth      = [45, 30, 20, 15, 10]
        ebit_margin_default = 55

    yr1 = st.slider("Year 1 Growth (%)", 0, 100, default_growth[0])
    yr2 = st.slider("Year 2 Growth (%)", 0, 80,  default_growth[1])
    yr3 = st.slider("Year 3 Growth (%)", 0, 60,  default_growth[2])
    yr4 = st.slider("Year 4 Growth (%)", 0, 40,  default_growth[3])
    yr5 = st.slider("Year 5 Growth (%)", 0, 30,  default_growth[4])
    ebit_margin = st.slider("EBIT Margin (%)", 5, 80, ebit_margin_default) / 100

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

        except Exception as e:
            st.error(f"Error fetching data: {e}")
            st.stop()

    # ── Company Header ────────────────────────────────────────
    st.subheader(f"{name} ({ticker_input})")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Sector",   sector)
    col2.metric("Industry", industry)
    col3.metric("Scenario", scenario)
    col4.metric("Currency", fx_note)

    if use_ddm:
        st.info("🏦 **Financial company detected** — using Dividend Discount Model (DDM)")
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

            st.subheader("📊 DDM Valuation Results")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("DDM Implied Price", f"{curr_symbol}{display_ddm_price:,.2f}")
            m2.metric("Market Price",       f"{curr_symbol}{display_market_price:,.2f}")
            m3.metric("Upside / Downside",  f"{upside:+.1f}%",
                      delta=f"{upside:+.1f}%", delta_color="normal")
            m4.metric("Div Growth Rate",    f"{div_growth:.1f}%")

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
                    marker_color="#1F4E79",
                    name="Annual Dividend"
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
        with st.spinner("Running DCF valuation..."):
            try:
                income = ticker.financials
                bs     = ticker.balance_sheet
                cf     = ticker.cashflow

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
                shares    = get_row(bs,     ["Share Issued", "Ordinary Shares Number"])

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

                growth_rates = [yr1/100, yr2/100, yr3/100, yr4/100, yr5/100]

                revenues, ufcf_list, pv_list, pv_tv, ev, eq, price = run_dcf_engine(
                    base_revenue, base_cash, base_debt, base_shares,
                    base_da_pct, base_capex_pct,
                    growth_rates, ebit_margin, wacc, tg
                )

                display_price = price * fx_rate
                display_ev    = ev * fx_rate
                upside        = (display_price - display_market_price) / display_market_price * 100

                hist_rev   = valid_rev.sort_index().tolist()
                hist_years = [str(y)[:4] for y in valid_rev.sort_index().index.tolist()]
                hist_ebit  = op_income.dropna().sort_index().tolist()

            except Exception as e:
                st.error(f"DCF Error: {e}")
                st.stop()

        st.subheader("📊 Valuation Results")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Implied Share Price", f"{curr_symbol}{display_price:,.2f}")
        m2.metric("Market Price",         f"{curr_symbol}{display_market_price:,.2f}")
        m3.metric("Upside / Downside",    f"{upside:+.1f}%",
                  delta=f"{upside:+.1f}%", delta_color="normal")
        m4.metric("Enterprise Value",     f"{curr_symbol}{display_ev/1e9:,.1f}B")

        st.divider()

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

        st.subheader("🎯 Sensitivity Analysis")
        st.caption(f"Implied Share Price ({curr_symbol}) | Rows = Terminal Growth | Cols = WACC")

        sens_df = build_sensitivity(
            base_revenue, base_cash, base_debt, base_shares,
            base_da_pct, base_capex_pct, growth_rates, ebit_margin
        )

        if fx_rate != 1.0:
            sens_df = sens_df * fx_rate

        st.dataframe(
            sens_df.style.background_gradient(cmap="RdYlGn", axis=None)
                         .format(f"{curr_symbol}{{:.2f}}"),
            use_container_width=True
        )

        st.subheader("📋 DCF Forecast Table")
        dcf_table = pd.DataFrame({
            "Year":                         forecast_years,
            f"Revenue ({curr_symbol}B)":    [f"{curr_symbol}{r*fx_rate/1e9:,.1f}" for r in revenues],
            f"EBIT ({curr_symbol}B)":       [f"{curr_symbol}{r*ebit_margin*fx_rate/1e9:,.1f}" for r in revenues],
            f"UFCF ({curr_symbol}B)":       [f"{curr_symbol}{u*fx_rate/1e9:,.1f}" for u in ufcf_list],
            f"PV of UFCF ({curr_symbol}B)": [f"{curr_symbol}{p*fx_rate/1e9:,.1f}" for p in pv_list],
        })
        st.dataframe(dcf_table, use_container_width=True, hide_index=True)

        st.divider()
        st.caption(
            f"Valuation Date: {date.today()} | Model: DCF | "
            f"WACC: {wacc*100:.1f}% | "
            f"Terminal Growth: {tg*100:.1f}% | "
            f"EBIT Margin: {ebit_margin*100:.1f}% | "
            f"Currency: {fx_note}"
        )
