# DCF Valuation Platform

A fully automated Discounted Cash Flow (DCF) valuation web application for publicly traded companies, built with Python, SQL, Streamlit, and Excel.

## Version 2 — Web Application (March 2026)
Added a full Streamlit web app with interactive sliders, Bull/Base/Bear scenarios, live charts, and a color-coded sensitivity matrix.

Run the app with:
streamlit run app.py

## Version 1 — Python Pipeline (March 2026)
Automated DCF engine with Excel export and SQLite database.

Run the pipeline with:
python run_dcf.py

## Features
- Live financial data ingestion via Yahoo Finance (yfinance)
- Bull / Base / Bear scenario selector
- Interactive WACC and growth rate sliders
- 5-year UFCF forecast engine
- Waterfall valuation bridge chart
- 25-scenario sensitivity matrix with color gradient
- SQLite database storing financials, assumptions, and valuation outputs
- Automated Excel export with formatted tabs
- Supports any publicly traded company with one line

## Companies Valued
| Company | Implied Price | Market Price |
|---------|--------------|--------------|
| NVIDIA  | $138.95      | ~$178        |
| Apple   | $119.41      | ~$249        |
| Microsoft | $134.14    | ~$357        |
| Alphabet | $42.91      | ~$274        |

## Tech Stack
- Python (pandas, numpy, openpyxl, yfinance, streamlit, plotly)
- SQLite
- Excel

## Project Structure
| File | Purpose |
|------|---------|
| app.py | V2 Streamlit web application |
| run_dcf.py | V1 automated pipeline |
| dcf_engine.py | Core DCF valuation engine |
| sensitivity.py | Sensitivity analysis |
| export_excel.py | Excel export |
| fetch_company.py | Yahoo Finance data pull |
| setup_db.py | Database setup |
| store_data.py | Data storage |
| query_db.py | Database queries |
| nvda_financials.csv | NVIDIA historical data |
