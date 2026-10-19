# Retail Intelligence Platform

An end-to-end retail analytics and decision-support platform combining Python data processing, SQL analytics, SQLite, interactive Streamlit dashboards, data-quality validation, and inventory risk analysis.

The project demonstrates how retail product data can be transformed into structured analytical datasets and used to explore pricing, historical sales indicators, stock availability scenarios, and replenishment decisions.

> **Data transparency:** The product and historical records come from the available retail dataset. The ERP-style inventory quantities, demand estimates, lead times, and replenishment recommendations are simulated for demonstration. They do not represent live ERP data or verified real-world stock levels.

## Project Highlights

- **Data engineering:** Build a repeatable Python pipeline to clean and transform retail records.
- **SQL analytics:** Explore sales indicators, marketing categories, release years, and pricing-quality flags using SQLite.
- **Interactive dashboard:** Navigate retail metrics and product data through a Streamlit application.
- **Inventory decision support:** Explore simulated stock availability, stockout risk, days of cover, lead-time demand, and reorder recommendations.
- **Data quality and testing:** Use automated tests to validate processing and inventory-related logic.
- **Reproducible setup:** Manage dependencies through a pinned `requirements.txt` file.

## Technology Stack

| Area | Technologies |
|---|---|
| Programming and data processing | Python, Pandas |
| Analytics and storage | SQL, SQLite |
| Dashboard and visualisation | Streamlit, Plotly |
| Testing | Pytest |
| Development and version control | Git, GitHub, PowerShell |

## Dashboard

Run the application locally to explore its five analytical areas:

1. **Overview** — high-level retail dataset indicators.
2. **Historical Indicators** — analysis of available historical product and sales fields.
3. **Pricing Analysis** — product pricing patterns and pricing-quality flags.
4. **Data Explorer** — inspect and explore available records.
5. **Inventory Risk & Availability** — examine the existing inventory risk analysis and a separate simulated ERP inventory scenario.

### Simulated ERP Inventory Analysis

The simulated inventory section uses product identifiers from the source data and generates demonstration values for inventory and replenishment analysis.

It includes:

- Simulated on-hand, reserved, and available units.
- Estimated daily demand and supplier lead times.
- Reorder points and suggested reorder quantities.
- Stock status categories, including stockout and reorder candidates.
- Days of cover and lead-time demand.
- Availability-risk categories and interactive filters.
- Product-level drill-downs and CSV export of filtered simulated records.

**Important:** These outputs are scenario-analysis results, not actual stock availability, supplier commitments, or live ERP recommendations. The source dataset does not provide the verified inventory and dated transaction data required to calculate these business measures from real operations.

## Data and Limitations

The current pipeline uses a replacement retail dataset because the original notebook dataset was unavailable.

The source dataset contains **198,917 records across 14 columns**:

| Dataset indicator | Records |
|---|---:|
| Active records | 122,921 |
| Historical records | 75,996 |
| Historical `SoldCount` total | 24,494 |

These figures describe the available dataset and its recorded fields; they should not be interpreted as verified revenue, customer conversion, or current stock.

Key limitations:

- The source does not contain sufficient transaction dates to establish a reliable time-based sales trend.
- `SoldFlag` is a source field and must not be interpreted as a customer-conversion rate.
- Verified realised revenue, cost of goods sold, returns, and actual on-hand inventory are unavailable in the current source.
- The meaning of `ItemCount` has not been verified as an on-hand inventory quantity.
- Pricing-quality flags identify records for investigation; they do not independently prove that a price is incorrect.
- Inventory quantities, daily demand, lead times, safety stock, availability risks, and reorder suggestions in the ERP-style analysis are simulated.

These limitations are intentional parts of the project's data documentation. They help distinguish source-supported findings from illustrative scenarios.

## Project Structure

```text
Retail-Intelligence-Platform/
├── app.py                         # Streamlit dashboard
├── build_data_pipeline.py         # Data-processing pipeline
├── requirements.txt               # Pinned Python dependencies
├── sql/
│   └── analytics/                 # SQL analytics scripts
├── src/
│   ├── inventory.py               # Inventory analysis logic
│   └── erp_simulation.py          # Simulated ERP inventory generator
├── tests/                         # Automated tests
├── data/
│   ├── raw/                       # Local source data
│   └── processed/                 # Generated datasets and database
├── reports/                       # Generated data-quality reports
└── notebooks/                     # Exploratory analysis
```

The exact files present in each directory may evolve as the project develops. Local raw data and generated artefacts may be excluded from version control.

## Getting Started

### 1. Requirements

Install a compatible Python version and Git. The project dependencies are pinned in `requirements.txt`.

### 2. Create a virtual environment

From the project root, run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, use an approved activation method for your environment or run the Python executable inside `.venv` directly.

### 3. Build the data pipeline

```powershell
python build_data_pipeline.py
```

The pipeline generates processed datasets and a SQLite database. If the outputs already exist, review the pipeline's overwrite behaviour before rebuilding them. Use `--force` only when you intentionally want to rebuild existing generated outputs.

Expected outputs include:

- `data/processed/retail_records_cleaned.csv`
- `data/processed/active_products.csv`
- `data/processed/historical_sales.csv`
- `data/processed/retail_analytics.db`
- `reports/data_quality_report.json`

The source data must be available locally for the pipeline to run successfully.

### 4. Launch the dashboard

```powershell
streamlit run app.py
```

Streamlit will provide a local URL in the terminal. Open that URL in your browser to explore the dashboard.

### 5. Run the tests

```powershell
python -m pytest -v
```

Run the tests after modifying the pipeline, inventory logic, or dashboard-related analytical functions.

## SQL Analytics

The `sql/analytics/` directory contains analytical SQL scripts covering:

1. Sales performance indicators.
2. Marketing analysis.
3. Release-year analysis.
4. Pricing analysis.
5. Pricing-quality flags.

These analyses are designed around the SQLite database generated by the main pipeline. Some helper scripts may use a separate sample database, so check their configured database paths before running them.

## Potential Improvements

- Add a documented methodology for inventory risk and replenishment assumptions.
- Connect a validated, dated transaction dataset to support genuine demand analysis.
- Integrate a real inventory or ERP data source when access is available.
- Add data-quality monitoring and pipeline execution logging.
- Extend automated testing for edge cases and business rules.
- Improve dashboard screenshots and documentation for easier portfolio review.
- Explore containerisation and cloud deployment for reproducible delivery.

## Author

**Likitha Shivananjegowda**

Data Analytics · Data Engineering · Cloud & DevOps

