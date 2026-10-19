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


def score_inventory_risk(
    df: pd.DataFrame,
    low_stock_threshold: int,
) -> pd.DataFrame:
    """Return a copy with transparent, rule-based inventory risk indicators."""
    if low_stock_threshold < 0:
        raise ValueError("low_stock_threshold must be zero or greater.")

    required = {"product_id", "status", "units"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    result = df.copy()
    units = pd.to_numeric(result["units"], errors="coerce")
    status = result["status"].astype("string").fillna("Unknown")

    result["risk_indicator"] = "Within threshold"
    result.loc[units.isna(), "risk_indicator"] = "Data issue"
    result.loc[units.notna() & (units <= low_stock_threshold),
               "risk_indicator"] = "Low stock"
    result.loc[units.notna() & (units <= 0),
               "risk_indicator"] = "Zero stock"

    availability_points = pd.Series(0, index=result.index, dtype="int64")
    availability_points.loc[units.notna() & (units <= low_stock_threshold)] = 40
    availability_points.loc[units.notna() & (units <= 0)] = 70

    markdown_points = status.map({
        "Full Price": 0,
        "Markdown T1": 10,
        "Markdown T2": 20,
        "Clearance": 30,
    }).fillna(0).astype("int64")

    result["risk_score"] = (
        availability_points + markdown_points
    ).clip(upper=100)

    result["risk_priority"] = "Low"
    result.loc[result["risk_score"] >= 20, "risk_priority"] = "Medium"
    result.loc[result["risk_score"] >= 60, "risk_priority"] = "High"
    result.loc[result["risk_score"] >= 90, "risk_priority"] = "Critical"
    result.loc[units.isna(), "risk_priority"] = "Review data"

    reasons = []
    for idx in result.index:
        row_reasons = []
        value = units.loc[idx]
        indicator = result.loc[idx, "risk_indicator"]
        row_status = status.loc[idx]

        if pd.isna(value):
            row_reasons.append("Missing or invalid units")
        elif value <= 0:
            row_reasons.append("Zero or negative quantity")
        elif value <= low_stock_threshold:
            row_reasons.append("Quantity at or below configured threshold")

        if row_status == "Markdown T1":
            row_reasons.append("Markdown T1 commercial review")
        elif row_status == "Markdown T2":
            row_reasons.append("Markdown T2 commercial review")
        elif row_status == "Clearance":
            row_reasons.append("Clearance commercial review")

        if not row_reasons and indicator == "Within threshold":
            row_reasons.append("No configured risk rule triggered")

        reasons.append("; ".join(row_reasons))

    result["risk_reason"] = reasons
    return result

def calculate_replenishment(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate reorder recommendations only when required inputs exist.

    Required inputs:
      product_id, units, average_daily_demand, lead_time_days,
      safety_stock_units

    Demand and lead time must be supplied from validated data or explicit
    planning assumptions. Missing inputs never produce a numeric estimate.
    """
    import math

    result = df.copy()
    required = {
        "product_id",
        "units",
        "average_daily_demand",
        "lead_time_days",
        "safety_stock_units",
    }

    for column in required - set(result.columns):
        result[column] = float("nan")

    numeric_columns = [
        "units",
        "average_daily_demand",
        "lead_time_days",
        "safety_stock_units",
    ]
    for column in numeric_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce")

    result["reorder_point_units"] = float("nan")
    result["suggested_reorder_qty"] = float("nan")
    result["replenishment_status"] = "Insufficient inputs"

    for idx, row in result.iterrows():
        units = row["units"]
        demand = row["average_daily_demand"]
        lead_time = row["lead_time_days"]
        safety_stock = row["safety_stock_units"]

        values = [units, demand, lead_time, safety_stock]
        if any(pd.isna(value) for value in values):
            continue

        if units < 0 or demand < 0 or lead_time < 0 or safety_stock < 0:
            result.at[idx, "replenishment_status"] = "Review invalid inputs"
            continue

        reorder_point = demand * lead_time + safety_stock
        reorder_qty = max(0, math.ceil(reorder_point - units))

        result.at[idx, "reorder_point_units"] = reorder_point
        result.at[idx, "suggested_reorder_qty"] = reorder_qty
        result.at[idx, "replenishment_status"] = (
            "Reorder" if units <= reorder_point else "No reorder needed"
        )

    return result
