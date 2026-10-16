from pathlib import Path
import pandas as pd

EXPECTED_STATUSES = {
    "Full Price",
    "Markdown T1",
    "Markdown T2",
    "Clearance",
}

REQUIRED_COLUMNS = {"product_id", "category", "status", "units"}


def load_inventory(path: str | Path) -> pd.DataFrame:
    """Load a retail inventory CSV."""
    df = pd.read_csv(path, encoding="utf-8-sig")

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df["product_id"] = df["product_id"].astype("string").str.strip()
    df["category"] = df["category"].astype("string").str.strip()
    df["status"] = df["status"].astype("string").str.strip()
    df["units"] = pd.to_numeric(df["units"], errors="raise")

    return df


def validate_inventory(df: pd.DataFrame) -> list[str]:
    """Return data-quality issues; an empty list means no issues found."""
    issues = []

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        return [f"Missing required columns: {sorted(missing)}"]

    if df[list(REQUIRED_COLUMNS)].isna().any().any():
        issues.append("Required fields contain missing values")

    if df["product_id"].astype("string").str.strip().eq("").any():
        issues.append("Product IDs contain blank values")

    if df["status"].notna().any() and not df["status"].dropna().isin(
        EXPECTED_STATUSES
    ).all():
        issues.append("Unknown inventory status found")

    if not pd.api.types.is_numeric_dtype(df["units"]):
        issues.append("Units must be numeric")
    elif (df["units"].dropna() < 0).any():
        issues.append("Negative inventory units found")

    if df.duplicated().any():
        issues.append("Duplicate rows found")

    return issues


def inventory_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarise records and units by inventory status."""
    return (
        df.groupby("status", dropna=False)
        .agg(
            inventory_records=("product_id", "size"),
            unique_products=("product_id", "nunique"),
            total_units=("units", "sum"),
        )
        .reset_index()
        .sort_values("total_units", ascending=False)
        .reset_index(drop=True)
    )
