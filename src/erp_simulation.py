"""Clearly labelled simulated ERP inventory data for dashboard demos."""

from pathlib import Path

import numpy as np
import pandas as pd


SIMULATION_LABEL = "SIMULATED - NOT LIVE ERP INVENTORY"
SIMULATED_CATEGORIES = ["Apparel", "Footwear", "Accessories", "Home"]


def generate_simulated_erp_inventory(
    active_products: pd.DataFrame,
    max_products: int = 2000,
    seed: int = 42,
) -> pd.DataFrame:
    """Create reproducible simulated stock records keyed to real source SKUs.

    SKU_number values come from the supplied active-products dataset.
    All quantities, categories, demand, lead times, and stock statuses are
    synthetic assumptions and must not be represented as actual ERP records.
    """
    if "SKU_number" not in active_products.columns:
        raise ValueError("active_products must contain SKU_number.")

    if max_products < 1:
        raise ValueError("max_products must be at least 1.")

    source = active_products[["SKU_number"]].copy()
    source["SKU_number"] = (
        source["SKU_number"].astype("string").str.strip()
    )
    source = source.dropna(subset=["SKU_number"])
    source = source[source["SKU_number"] != ""]
    source = source.drop_duplicates(subset=["SKU_number"])
    source = source.sort_values("SKU_number").reset_index(drop=True)

    if source.empty:
        raise ValueError("No valid SKU_number values were found.")

    sample_size = min(max_products, len(source))
    selected = source.sample(n=sample_size, random_state=seed)
    selected = selected.sort_values("SKU_number").reset_index(drop=True)

    rng = np.random.default_rng(seed)
    result = selected.rename(columns={"SKU_number": "product_id"}).copy()

    result["simulation_label"] = SIMULATION_LABEL
    result["simulated_category"] = rng.choice(
        SIMULATED_CATEGORIES, size=sample_size
    )
    result["simulated_on_hand_units"] = rng.integers(
        0, 251, size=sample_size
    )
    result["simulated_reserved_units"] = np.array([
        rng.integers(0, int(on_hand) + 1)
        for on_hand in result["simulated_on_hand_units"]
    ], dtype="int64")
    result["simulated_available_units"] = (
        result["simulated_on_hand_units"]
        - result["simulated_reserved_units"]
    )
    result["simulated_daily_demand"] = np.round(
        rng.uniform(0.1, 20.0, size=sample_size), 2
    )
    result["simulated_lead_time_days"] = rng.integers(
        1, 22, size=sample_size
    )
    result["simulated_safety_stock_units"] = rng.integers(
        1, 51, size=sample_size
    )
    result["simulated_reorder_point_units"] = np.ceil(
        result["simulated_daily_demand"]
        * result["simulated_lead_time_days"]
        + result["simulated_safety_stock_units"]
    ).astype("int64")
    result["simulated_suggested_reorder_qty"] = (
        result["simulated_reorder_point_units"]
        - result["simulated_available_units"]
    ).clip(lower=0).astype("int64")

    # Stock cover estimates how many days available stock can meet
    # the synthetic daily-demand assumption.
    result["simulated_days_of_cover"] = (
        result["simulated_available_units"]
        / result["simulated_daily_demand"]
    ).round(2)

    # Availability risk compares usable stock with demand during lead time.
    result["simulated_lead_time_demand_units"] = np.ceil(
        result["simulated_daily_demand"]
        * result["simulated_lead_time_days"]
    ).astype("int64")

    result["simulated_availability_risk"] = "Adequate cover"
    result.loc[
        result["simulated_days_of_cover"]
        <= result["simulated_lead_time_days"],
        "simulated_availability_risk",
    ] = "Monitor"
    result.loc[
        result["simulated_available_units"]
        < result["simulated_lead_time_demand_units"],
        "simulated_availability_risk",
    ] = "At risk"
    result.loc[
        result["simulated_available_units"] <= 0,
        "simulated_availability_risk",
    ] = "Critical - Stockout"

    result["simulated_stock_status"] = "Available"
    result.loc[
        result["simulated_available_units"]
        <= result["simulated_reorder_point_units"],
        "simulated_stock_status",
    ] = "Reorder"
    result.loc[
        result["simulated_available_units"] <= 0,
        "simulated_stock_status",
    ] = "Stockout"

    return result
