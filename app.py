import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import sqlite3
from datetime import date
import io
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="DCF Valuation Platform",
    page_icon="📈",
    layout="wide"
)

# ── Header ────────────────────────────────────────────────────
st.title("📈 DCF Valuation Platform")
st.markdown("*Automated Discounted Cash Flow analysis for any public company*")
st.divider()

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    ticker_input = st.text_input(
        "Enter Ticker Symbol",
        value="NVDA",
        placeholder="e.g. AAPL, MSFT, NVDA"
    ).upper().strip()

    st.subheader("Scenario")
    scenario = st.selectbox(
        "Select Scenario",
        ["Base Case", "Bull Case", "Bear Case"]
    )

    st.subheader("DCF Assumptions")
    wacc = st.slider("WACC (%)", 6.0, 15.0, 10.0, 0.5) / 100
    tg   = st.slider("Terminal Growth (%)", 1.0, 5.0, 3.0, 0.5) / 100

    st.subheader("Growth Assumptions")
    if scenario == "Bull Case":
        default_growth = [55, 40, 30, 20, 15]
        ebit_margin_default = 60
    elif scenario == "Bear Case":
        default_growth = [20, 15, 10, 8, 5]
        ebit_margin_default = 40
    else:
        default_growth = [45, 30, 20, 15, 10]
        ebit_margin_default = 55

    yr1 = st.slider("Year 1 Growth (%)", 0, 100, default_growth[0])
    yr2 = st.slider("Year 2 Growth (%)", 0, 80,  default_growth[1])
    yr3 = st.slider("Year 3 Growth (%)", 0, 60,  default_growth[2])
    yr4 = st.slider("Year 4 Growth (%)", 0, 40,  default_growth[3])
    yr5 = st.slider("Year 5 Growth (%)", 0, 30,  default_growth[4])
    ebit_margin = st.slider("EBIT Margin (%)", 5, 80, ebit_margin_default) / 100

    run_button = st.button("🚀 Run DCF", type="primary", use_container_width=True)

# ── DCF Engine ────────────────────────────────────────────────
def run_dcf_engine(base_revenue, base_cash, base_debt, base_shares,
                   base_da_pct, base_capex_pct,
                   growth_rates, ebit_margin, wacc, tg,
                   tax_rate=0.15, nwc_pct=0.03):

    revenues, ufcf_list, pv_list = [], [], []
    rev = base_revenue
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

# ── Main App ──────────────────────────────────────────────────
if run_button or True:
    with st.spinner(f"Fetching data for {ticker_input}..."):
        try:
            ticker = yf.Ticker(ticker_input)
            info   = ticker.info
            name   = info.get("longName", ticker_input)
            market_price = info.get("currentPrice", 0)
            sector = info.get("sector", "N/A")
            industry = info.get("industry", "N/A")

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
            net_inc   = get_row(income, ["Net Income"])
            da        = get_row(cf,     ["Depreciation And Amortization",
                                          "Depreciation Amortization Depletion"])
            capex     = get_row(cf,     ["Capital Expenditure"])
            fcf       = get_row(cf,     ["Free Cash Flow"])
            cash      = get_row(bs,     ["Cash And Cash Equivalents",
                                          "Cash Cash Equivalents And Short Term Investments"])
            debt      = get_row(bs,     ["Total Debt"])
            shares    = get_row(bs,     ["Share Issued","Ordinary Shares Number"])

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

            upside = (price - market_price) / market_price * 100

            # Historical data
            hist_rev    = valid_rev.sort_index().tolist()
            hist_years  = [str(y)[:4] for y in valid_rev.sort_index().index.tolist()]
            hist_ebit   = op_income.dropna().sort_index().tolist()
            hist_fcf    = fcf.dropna().sort_index().tolist()

        except Exception as e:
            st.error(f"Error fetching data: {e}")
            st.stop()

    # ── Company Header ────────────────────────────────────────
    st.subheader(f"{name} ({ticker_input})")
    col1, col2, col3 = st.columns(3)
    col1.metric("Sector", sector)
    col2.metric("Industry", industry)
    col3.metric("Scenario", scenario)

    st.divider()

    # ── Key Metrics ───────────────────────────────────────────
    st.subheader("📊 Valuation Results")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Implied Share Price", f"${price:,.2f}")
    m2.metric("Market Price", f"${market_price:,.2f}")
    m3.metric("Upside / Downside", f"{upside:+.1f}%",
              delta=f"{upside:+.1f}%",
              delta_color="normal")
    m4.metric("Enterprise Value", f"${ev/1e9:,.1f}B")

    st.divider()

    # ── Charts Row 1 ──────────────────────────────────────────
    st.subheader("📈 Historical Performance")
    c1, c2 = st.columns(2)

    with c1:
        fig_rev = go.Figure()
        fig_rev.add_bar(
            x=hist_years,
            y=[r/1e9 for r in hist_rev],
            marker_color="#1F4E79",
            name="Revenue"
        )
        fig_rev.update_layout(
            title="Revenue ($B)",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#EEEEEE")
        )
        st.plotly_chart(fig_rev, use_container_width=True)

    with c2:
        ebit_margins = [e/r*100 for e, r in
                        zip(hist_ebit, hist_rev[:len(hist_ebit)])]
        fig_margin = go.Figure()
        fig_margin.add_scatter(
            x=hist_years[:len(ebit_margins)],
            y=ebit_margins,
            mode="lines+markers",
            line=dict(color="#F4B942", width=3),
            marker=dict(size=8)
        )
        fig_margin.update_layout(
            title="EBIT Margin (%)",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#EEEEEE")
        )
        st.plotly_chart(fig_margin, use_container_width=True)

    # ── Charts Row 2 ──────────────────────────────────────────
    st.subheader("🔮 5-Year Forecast")
    forecast_years = ["2027E", "2028E", "2029E", "2030E", "2031E"]

    c3, c4 = st.columns(2)

    with c3:
        fig_fcst = go.Figure()
        fig_fcst.add_bar(
            x=forecast_years,
            y=[r/1e9 for r in revenues],
            marker_color="#1F4E79",
            name="Revenue"
        )
        fig_fcst.update_layout(
            title="Forecast Revenue ($B)",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#EEEEEE")
        )
        st.plotly_chart(fig_fcst, use_container_width=True)

    with c4:
        fig_ufcf = go.Figure()
        fig_ufcf.add_bar(
            x=forecast_years,
            y=[u/1e9 for u in ufcf_list],
            marker_color="#2ECC71",
            name="UFCF"
        )
        fig_ufcf.update_layout(
            title="Forecast UFCF ($B)",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#EEEEEE")
        )
        st.plotly_chart(fig_ufcf, use_container_width=True)

    # ── Valuation Bridge ──────────────────────────────────────
    st.subheader("🌉 Valuation Bridge")
    fig_wf = go.Figure(go.Waterfall(
        name="Bridge",
        orientation="v",
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
        height=350,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#EEEEEE", title="$B")
    )
    st.plotly_chart(fig_wf, use_container_width=True)

    # ── Sensitivity Table ─────────────────────────────────────
    st.subheader("🎯 Sensitivity Analysis")
    st.caption("Implied Share Price ($) | Rows = Terminal Growth | Cols = WACC")

    sens_df = build_sensitivity(
        base_revenue, base_cash, base_debt, base_shares,
        base_da_pct, base_capex_pct, growth_rates, ebit_margin
    )

    st.dataframe(
        sens_df.style.background_gradient(cmap="RdYlGn", axis=None)
        .format("${:.2f}"),
        use_container_width=True
    )

    # ── DCF Table ─────────────────────────────────────────────
    st.subheader("📋 DCF Forecast Table")
    dcf_table = pd.DataFrame({
        "Year":           forecast_years,
        "Revenue ($B)":   [f"${r/1e9:,.1f}" for r in revenues],
        "EBIT ($B)":      [f"${r*ebit_margin/1e9:,.1f}" for r in revenues],
        "UFCF ($B)":      [f"${u/1e9:,.1f}" for u in ufcf_list],
        "PV of UFCF ($B)":[f"${p/1e9:,.1f}" for p in pv_list],
    })
    st.dataframe(dcf_table, use_container_width=True, hide_index=True)

    st.divider()
    st.caption(f"Valuation Date: {date.today()} | "
               f"WACC: {wacc*100:.1f}% | "
               f"Terminal Growth: {tg*100:.1f}% | "
               f"EBIT Margin: {ebit_margin*100:.1f}%")
