import pandas as pd
from src.inventory import calculate_replenishment


def test_reorder_point_and_quantity_are_calculated():
    df = pd.DataFrame([{
        "product_id": "P1",
        "units": 10,
        "average_daily_demand": 2,
        "lead_time_days": 5,
        "safety_stock_units": 4,
    }])

    result = calculate_replenishment(df)

    assert result.loc[0, "reorder_point_units"] == 14
    assert result.loc[0, "suggested_reorder_qty"] == 4
    assert result.loc[0, "replenishment_status"] == "Reorder"


def test_no_reorder_when_units_exceed_reorder_point():
    df = pd.DataFrame([{
        "product_id": "P2",
        "units": 30,
        "average_daily_demand": 2,
        "lead_time_days": 5,
        "safety_stock_units": 4,
    }])

    result = calculate_replenishment(df)

    assert result.loc[0, "reorder_point_units"] == 14
    assert result.loc[0, "suggested_reorder_qty"] == 0
    assert result.loc[0, "replenishment_status"] == "No reorder needed"


def test_missing_demand_does_not_create_estimate():
    df = pd.DataFrame([{
        "product_id": "P3",
        "units": 5,
    }])

    result = calculate_replenishment(df)

    assert pd.isna(result.loc[0, "reorder_point_units"])
    assert pd.isna(result.loc[0, "suggested_reorder_qty"])
    assert result.loc[0, "replenishment_status"] == "Insufficient inputs"


def test_negative_inputs_are_flagged():
    df = pd.DataFrame([{
        "product_id": "P4",
        "units": 10,
        "average_daily_demand": -2,
        "lead_time_days": 5,
        "safety_stock_units": 4,
    }])

    result = calculate_replenishment(df)

    assert result.loc[0, "replenishment_status"] == "Review invalid inputs"
