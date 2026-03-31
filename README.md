# DCF Valuation Platform

A fully automated DCF & DDM valuation web application for any publicly traded company, built with Python, SQL, Streamlit, and Excel.

## 🌐 Live App
**[dcf-valuation-platform-financity.streamlit.app](https://dcf-valuation-platform-financity.streamlit.app)**

---

## Versions

### Version 3 — Production Platform (March 2026)
- Deployed to Streamlit Cloud — publicly accessible via URL, no installation needed
- Automated WACC calculator pulling live beta, Treasury yield, cost of debt, and capital structure
- Canadian dollar support with live USD/CAD exchange rate and auto-detection of CAD companies
- DDM engine for financial companies with automatic sector-based model selection
- Banks and insurers now valued with Dividend Discount Model instead of DCF

### Version 2 — Web Application (March 2026)
- Full Streamlit web app with interactive sliders and live charts
- Bull / Base / Bear scenario selector
- Waterfall valuation bridge chart
- Color-coded 25-scenario sensitivity matrix
- Run with: `streamlit run app.py`

### Version 1 — Python Pipeline (March 2026)
- Automated DCF engine with Excel export and SQLite database
- Single-command pipeline for any public company
- Run with: `python run_dcf.py`

---

## Features
- Live financial data ingestion via Yahoo Finance (yfinance)
- Automated WACC calculator — beta, risk-free rate, CAPM, cost of debt
- Bull / Base / Bear scenario selector with pre-set assumptions
- Interactive WACC, growth rate, and margin sliders
- 5-year UFCF forecast engine with normalized margin assumptions
- Waterfall valuation bridge (EV → equity value → implied share price)
- 25-scenario sensitivity matrix (WACC × terminal growth)
- DDM engine for banks and insurers with dividend growth sensitivity table
- Multi-currency support — USD and CAD with live exchange rates
- SQLite database storing financials, assumptions, and valuation outputs
- Automated Excel export with formatted tabs

---

## Companies Valued

| Company | Model | Implied Price | Market Price |
|---------|-------|--------------|--------------|
| NVIDIA  | DCF   | $138.95      | ~$178        |
| Apple   | DCF   | $119.41      | ~$249        |
| Microsoft | DCF | $134.14     | ~$357        |
| Alphabet | DCF  | $42.91      | ~$274        |
| Royal Bank of Canada | DDM | CA$53.67 | ~CA$223 |
| TD Bank | DDM  | CA$39.38     | ~CA$128      |
| BMO     | DDM  | CA$49.92     | ~CA$186      |

---

## Tech Stack
- Python (pandas, numpy, openpyxl, yfinance, streamlit, plotly, matplotlib)
- SQLite
- Excel

---

## How to Run

### Web App (recommended)
```
pip install -r requirements.txt
streamlit run app.py
```

### Pipeline only
```
python setup_db.py
python run_dcf.py
```

---

## Project Structure

| File | Purpose |
|------|---------|
| `app.py` | V3 Streamlit web application — DCF + DDM + CAD |
| `run_dcf.py` | V1 automated pipeline |
| `dcf_engine.py` | Core DCF valuation engine |
| `sensitivity.py` | Sensitivity analysis |
| `export_excel.py` | Excel export |
| `fetch_company.py` | Yahoo Finance data pull |
| `setup_db.py` | Database setup |
| `store_data.py` | Data storage |
| `query_db.py` | Database queries |
| `nvda_financials.csv` | NVIDIA historical data |
| `requirements.txt` | Python dependencies |
| `runtime.txt` | Python version for deployment |
