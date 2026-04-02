import streamlit as st

st.set_page_config(
    page_title="About — DCF Valuation Platform",
    page_icon="👤",
    layout="wide"
)

st.title("👤 About This Project")
st.divider()

# ── About ─────────────────────────────────────────────────────
st.subheader("Background")
st.markdown("""
This platform was built by a finance student pursuing a major in Finance 
with a focus on investment analysis and valuation.

The motivation was straightforward: institutional-grade valuation tools exist — 
Bloomberg, FactSet, Capital IQ — but they are expensive, inaccessible, and require 
significant training. This platform was built to close that gap, making real financial 
analysis available to any student or investor with an internet connection.

Every analytical feature is grounded in finance theory — from the DCF engine and WACC 
calculator to the DDM model for financial institutions and the multi-method bank 
valuation framework. The platform grows as the coursework progresses.
""")

st.divider()

# ── Who This Is For ───────────────────────────────────────────
st.subheader("Who This Is For")
st.markdown("""
This platform is built for anyone who wants to understand how companies are valued — 
not just finance students, but retail investors, early-career analysts, and anyone 
curious about what a stock is actually worth beyond its market price.

No Bloomberg terminal required. No finance degree required. Just a ticker symbol.
""")

st.divider()

# ── Project Evolution ─────────────────────────────────────────
st.subheader("Project Evolution")

v1, v2, v3, v4 = st.columns(4)

with v1:
    st.markdown("**V1 — Python Pipeline**")
    st.markdown("""
- DCF engine from scratch
- SQLite database
- Excel export
- NVIDIA as first test case
    """)

with v2:
    st.markdown("**V2 — Web Application**")
    st.markdown("""
- Streamlit UI
- Interactive sliders
- Bull/Base/Bear scenarios
- Live charts
- Sensitivity matrix
    """)

with v3:
    st.markdown("**V3 — Production**")
    st.markdown("""
- Publicly deployed
- Automated WACC calculator
- Canadian dollar support
- DDM engine for banks
- Auto sector detection
    """)

with v4:
    st.markdown("**V4 — Depth** *(current)*")
    st.markdown("""
- Multi-page architecture
- 9 model improvements
- Auto-computed assumptions
- Multi-method bank valuation
- Extended company data
- Education page
    """)

st.divider()

# ── Vision ────────────────────────────────────────────────────
st.subheader("Long-Term Vision")
st.markdown("""
The long-term vision is a **financial education and analysis platform** — where 
someone can learn a concept, practice applying it, and run a live valuation in 
the same place.

The goal is to sit at the intersection of financial education, investment analysis, 
and community — built for finance students and investors everywhere, completely free.

As additional coursework is completed — portfolio management, mergers and acquisitions, 
derivatives — each discipline will add a new analytical layer to the platform.
""")

st.divider()

# ── Tech Stack ────────────────────────────────────────────────
st.subheader("Tech Stack")
t1, t2, t3, t4 = st.columns(4)
t1.metric("Language",  "Python")
t2.metric("Frontend",  "Streamlit")
t3.metric("Database",  "SQLite")
t4.metric("Charts",    "Plotly")

st.divider()

# ── Contact ───────────────────────────────────────────────────
st.subheader("Contact")
st.markdown("""
For questions, feedback, collaboration opportunities, or general inquiries:

📧 **michel.m.antone@gmail.com**

All messages are welcome — whether it's a bug report, a feature idea, 
an academic question, or a conversation about finance and technology.
""")

st.divider()

# ── Links ─────────────────────────────────────────────────────
st.subheader("Links")
st.markdown("""
- 💻 **GitHub:** [github.com/themichelantone/dcf-valuation-platform](https://github.com/themichelantone/dcf-valuation-platform)
- 🌐 **Live App:** [dcf-valuation-platform-financity.streamlit.app](https://dcf-valuation-platform-financity.streamlit.app)
""")

st.divider()
st.caption("Built by Michel Antone — Montreal, QC")
