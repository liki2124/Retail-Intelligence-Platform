# Retail Intelligence Platform

An end-to-end retail data engineering and analytics project combining Python data processing, data-quality validation, SQLite, SQL analytics, automated tests, and reproducible reporting.

## Project Overview

This project processes retail product and historical sales records, validates data-quality rules, creates reusable analytical datasets, stores results in SQLite, and provides SQL analyses covering sales patterns, marketing categories, release years, and pricing-quality flags.

The workflow demonstrates how raw retail data can be transformed into structured, testable outputs for analysis.

## Technology Stack

- Python
- Pandas
- SQLite
- SQL
- Pytest
- PowerShell
- Git and GitHub

## Project Structure

```text
Retail-Intelligence-Platform/
├── data/
│   ├── raw/                  # Local source data; excluded from Git
│   └── processed/            # Generated datasets and SQLite database
├── reports/                  # Generated data-quality report
├── sql/
│   └── analytics/
│       ├── 01_sales_performance.sql
│       ├── 02_marketing_analysis.sql
│       ├── 03_pricing_analysis.sql
│       ├── 04_release_year_analysis.sql
│       └── 05_price_quality_flags.sql
├── tests/
│   └── test_retail_pipeline.py
├── build_data_pipeline.py
├── sql_utils.py
├── run_sql_file.py
└── run_markdown_analysis.py
```

## Dataset and Limitations

The pipeline currently uses a replacement Kaggle retail dataset because the original notebook dataset was unavailable.

The raw dataset contains 198,917 records across 14 columns:

- 122,921 active records
- 75,996 historical records

The historical data contains 24,494 units recorded in `SoldCount`.

Important limitations:

- The available data does not contain transaction dates sufficient to establish a time-based sales trend.
- `SoldFlag` is a dataset field; its rate should not be interpreted as customer conversion.
- Verified realised revenue, cost of goods sold, returns, and actual on-hand inventory are not available in the current source.
- Pricing-quality flags identify records for further review; they do not independently prove that a price is incorrect.

Results should therefore be interpreted within the limits of the available dataset.

## Setup

Use Python 3.10 or a compatible version supported by the project's dependencies.

Install the required packages:

```powershell
python -m pip install pandas pytest
```

Run commands from the project root directory.

## Build the Data Pipeline

Build the processed datasets and SQLite database:

```powershell
python build_data_pipeline.py
```

If generated outputs already exist and you intentionally want to rebuild them, use:

```powershell
python build_data_pipeline.py --force
```

The `--force` option rebuilds existing generated outputs. Ensure you do not have local changes to generated files that you need to preserve.

The pipeline generates:

- `data/processed/retail_records_cleaned.csv`
- `data/processed/active_products.csv`
- `data/processed/historical_sales.csv`
- `data/processed/retail_analytics.db`
- `reports/data_quality_report.json`

The raw dataset and generated processed files are excluded from Git.

## SQL Analytics

The `sql/analytics/` directory contains five analytical SQL scripts:

1. Sales performance
2. Marketing analysis
3. Pricing analysis
4. Release-year analysis
5. Pricing-quality flags

These scripts are designed to run against the SQLite database produced by the main pipeline.

The helper scripts `run_sql_file.py` and `run_markdown_analysis.py` also support a separate sample-database workflow. Check their configured database paths before using them; they do not automatically target the main pipeline database.

## Data Quality and Testing

Run the automated test suite:

```powershell
python -m pytest -v
```

The current validated test result is **16 passing tests**.

The pipeline and tests cover data processing and validation behaviour. Re-run the tests after modifying pipeline logic or SQL-related utilities.

## Current Pipeline Results

The most recent successful pipeline run processed:

| Metric | Result |
|---|---:|
| Total records processed | 198,917 |
| Active records | 122,921 |
| Historical records | 75,996 |
| Historical `SoldCount` total | 24,494 |
| Automated tests | 16 passed |

These results describe the current replacement dataset and should not be presented as verified business revenue or customer-conversion metrics.

## Potential Improvements

- Add a documented dependency file for reproducible environment setup.
- Introduce additional automated checks for data types, missing values, and business rules.
- Add visualisations for validated SQL outputs.
- Extend the pipeline when a suitable transaction-level dataset becomes available.
- Integrate the analytical outputs into a reporting dashboard.

## Author

**Likitha Shivananjegowda**

Data analytics, data engineering, and cloud-oriented projects.
