import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
RAW_FILE = ROOT / "data" / "raw" / "SalesKaggle3.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"

DATABASE_FILE = PROCESSED_DIR / "retail_analytics.db"
ALL_RECORDS_FILE = PROCESSED_DIR / "retail_records_cleaned.csv"
ACTIVE_FILE = PROCESSED_DIR / "active_products.csv"
HISTORICAL_FILE = PROCESSED_DIR / "historical_sales.csv"
REPORT_FILE = REPORT_DIR / "data_quality_report.json"

EXPECTED_COLUMNS = [
    "Order", "File_Type", "SKU_number", "SoldFlag", "SoldCount",
    "MarketingType", "ReleaseNumber", "New_Release_Flag",
    "StrengthFactor", "PriceReg", "ReleaseYear", "ItemCount",
    "LowUserPrice", "LowNetPrice",
]

NUMERIC_COLUMNS = [
    "Order", "SoldFlag", "SoldCount", "ReleaseNumber",
    "New_Release_Flag", "StrengthFactor", "PriceReg",
    "ReleaseYear", "ItemCount", "LowUserPrice", "LowNetPrice",
]


def load_and_validate():
    if not RAW_FILE.is_file():
        raise FileNotFoundError(
            f"Raw CSV not found: {RAW_FILE}\n"
            "Place SalesKaggle3.csv in data/raw/ and rerun."
        )

    # Keep the source CSV unchanged and preserve SKU identifiers as text.
    df = pd.read_csv(
        RAW_FILE,
        low_memory=False,
        dtype={"SKU_number": "string"},
    )

    missing_columns = sorted(set(EXPECTED_COLUMNS) - set(df.columns))
    unexpected_columns = sorted(set(df.columns) - set(EXPECTED_COLUMNS))

    if missing_columns or unexpected_columns:
        raise ValueError(
            f"Column schema mismatch. Missing: {missing_columns}; "
            f"unexpected: {unexpected_columns}"
        )

    if df.empty:
        raise ValueError("The input CSV contains no records.")

    # Convert numeric fields safely. Do not silently turn invalid text into nulls.
    invalid_numeric = {}
    for column in NUMERIC_COLUMNS:
        original = df[column]
        converted = pd.to_numeric(original, errors="coerce")
        invalid_mask = original.notna() & converted.isna()

        if invalid_mask.any():
            invalid_numeric[column] = int(invalid_mask.sum())
        else:
            df[column] = converted

    if invalid_numeric:
        raise ValueError(
            f"Non-numeric values found in numeric columns: {invalid_numeric}"
        )

    allowed_types = {"Active", "Historical"}
    actual_types = set(df["File_Type"].dropna().unique())
    if df["File_Type"].isna().any() or not actual_types.issubset(allowed_types):
        raise ValueError(
            f"Unexpected File_Type values: {sorted(map(str, actual_types))}"
        )

    if df["SKU_number"].isna().any():
        raise ValueError("SKU_number contains missing values.")

    # Validate the observed meaning of sales fields without filling missing data.
    active = df.loc[df["File_Type"].eq("Active")]
    historical = df.loc[df["File_Type"].eq("Historical")]

    if active.empty or historical.empty:
        raise ValueError("Expected both Active and Historical records.")

    if active[["SoldFlag", "SoldCount"]].notna().any().any():
        raise ValueError(
            "Active records contain sales fields. Review the source before proceeding."
        )

    if historical[["SoldFlag", "SoldCount"]].isna().any().any():
        raise ValueError(
            "Historical records have missing sales fields. Review the source."
        )

    if not historical["SoldFlag"].isin([0, 1]).all():
        raise ValueError("Historical SoldFlag must contain only 0 or 1.")

    if (historical["SoldCount"] < 0).any():
        raise ValueError("Historical SoldCount contains negative values.")

    inconsistent_sales = (
        ((historical["SoldFlag"] == 0) & (historical["SoldCount"] != 0))
        | ((historical["SoldFlag"] == 1) & (historical["SoldCount"] <= 0))
    )
    if inconsistent_sales.any():
        raise ValueError(
            f"Found {int(inconsistent_sales.sum())} inconsistent SoldFlag/SoldCount rows."
        )

    if (df["PriceReg"] < 0).any():
        raise ValueError("PriceReg contains negative values.")

    if (df["ItemCount"] < 0).any():
        raise ValueError("ItemCount contains negative values.")

    return df


def build_report(df):
    active = df.loc[df["File_Type"].eq("Active")]
    historical = df.loc[df["File_Type"].eq("Historical")]

    active_skus = set(active["SKU_number"].dropna())
    historical_skus = set(historical["SKU_number"].dropna())

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": "data/raw/SalesKaggle3.csv",
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": list(df.columns),
        "file_type_counts": {
            str(k): int(v)
            for k, v in df["File_Type"].value_counts(dropna=False).items()
        },
        "missing_values_by_column": {
            str(k): int(v)
            for k, v in df.isna().sum().items()
            if v > 0
        },
        "exact_duplicate_rows": int(df.duplicated().sum()),
        "duplicate_skus_within_file_type": int(
            df.duplicated(subset=["File_Type", "SKU_number"]).sum()
        ),
        "active_records": int(len(active)),
        "historical_records": int(len(historical)),
        "active_skus": int(active["SKU_number"].nunique()),
        "historical_skus": int(historical["SKU_number"].nunique()),
        "skus_in_both_groups": int(len(active_skus & historical_skus)),
        "active_only_skus": int(len(active_skus - historical_skus)),
        "historical_only_skus": int(len(historical_skus - active_skus)),
        "historical_sold_flag_counts": {
            str(k): int(v)
            for k, v in historical["SoldFlag"].value_counts().sort_index().items()
        },
        "historical_total_sold_count": int(historical["SoldCount"].sum()),
        "sales_fields_missing_on_active_records": int(
            active[["SoldFlag", "SoldCount"]].isna().all(axis=1).sum()
        ),
        "validation_status": "passed",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate and prepare the retail dataset for SQL and BI."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow existing pipeline output files to be replaced.",
    )
    args = parser.parse_args()

    output_files = [
        DATABASE_FILE,
        ALL_RECORDS_FILE,
        ACTIVE_FILE,
        HISTORICAL_FILE,
        REPORT_FILE,
    ]

    existing = [str(p.relative_to(ROOT)) for p in output_files if p.exists()]
    if existing and not args.force:
        raise FileExistsError(
            "Output files already exist; nothing was overwritten:\n"
            + "\n".join(existing)
            + "\nReview them first, or rerun with --force to replace them."
        )

    print("Loading and validating source data...")
    df = load_and_validate()

    active = df.loc[df["File_Type"].eq("Active")].copy()
    historical = df.loc[df["File_Type"].eq("Historical")].copy()
    report = build_report(df)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Write distinct outputs; the raw CSV is never modified.
    df.to_csv(ALL_RECORDS_FILE, index=False)
    active.to_csv(ACTIVE_FILE, index=False)
    historical.to_csv(HISTORICAL_FILE, index=False)

    with sqlite3.connect(DATABASE_FILE) as connection:
        df.to_sql("all_records", connection, if_exists="replace", index=False)
        active.to_sql("active_products", connection, if_exists="replace", index=False)
        historical.to_sql("historical_sales", connection, if_exists="replace", index=False)

        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_all_records_sku "
            "ON all_records (SKU_number)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_all_records_file_type "
            "ON all_records (File_Type)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_historical_sold_flag "
            "ON historical_sales (SoldFlag)"
        )

    REPORT_FILE.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\n=== PIPELINE COMPLETED ===")
    print(f"Rows processed: {len(df):,}")
    print(f"Active records: {len(active):,}")
    print(f"Historical records: {len(historical):,}")
    print(f"Historical SoldCount total: {historical['SoldCount'].sum():,.0f}")
    print("\nCreated outputs:")
    for path in output_files:
        print(f"  {path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")
    print("\nSQLite tables:")
    print("  all_records")
    print("  active_products")
    print("  historical_sales")
    print("\nRaw source file was not modified.")


if __name__ == "__main__":
    main()
