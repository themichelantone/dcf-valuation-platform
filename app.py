import streamlit as st

st.set_page_config(
    page_title="DCF Valuation Platform",
    page_icon="📈",
    layout="wide"
)

st.title("📈 DCF Valuation Platform")
st.markdown("*Built by Michel Antone — Finance Student, Concordia University JMSB*")
st.divider()

st.markdown("""
### Welcome

This platform provides institutional-grade valuation analysis for any publicly traded company — 
built from the ground up using Python, SQL, and Streamlit.

---

### What You Can Do Here

📊 **Value any company** — DCF for operating companies, DDM for banks and insurers

🇨🇦 **Canadian companies supported** — live USD/CAD conversion

📐 **Automated WACC** — computed from beta, Treasury yield, and capital structure

🎯 **Sensitivity analysis** — see how assumptions drive valuation

---

### Navigate Using the Sidebar →

Use the pages in the left sidebar to get started.
""")

st.divider()
st.caption("V3 — Deployed March 2026 | github.com/themichelantone/dcf-valuation-platform")
