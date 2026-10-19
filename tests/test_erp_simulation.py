import numpy as np
import pandas as pd
import pytest

from src.erp_simulation import (
    SIMULATION_LABEL,
    generate_simulated_erp_inventory,
)


@pytest.fixture
def active_products():
    return pd.DataFrame({
        "SKU_number": ["1003", "1001", "1002", "1002", None, " "],
        "File_Type": ["Active"] * 6,
    })


def test_uses_unique_real_source_skus(active_products):
    result = generate_simulated_erp_inventory(active_products, max_products=20)

    assert result["product_id"].is_unique
    assert set(result["product_id"]).issubset({"1001", "1002", "1003"})
    assert len(result) == 3


def test_is_reproducible(active_products):
    first = generate_simulated_erp_inventory(active_products, seed=17)
    second = generate_simulated_erp_inventory(active_products, seed=17)

    pd.testing.assert_frame_equal(first, second)


def test_available_units_equal_on_hand_minus_reserved(active_products):
    result = generate_simulated_erp_inventory(active_products)

    assert (
        result["simulated_available_units"]
        == result["simulated_on_hand_units"]
        - result["simulated_reserved_units"]
    ).all()
    assert (result["simulated_available_units"] >= 0).all()


def test_reorder_quantity_and_status_are_consistent(active_products):
    result = generate_simulated_erp_inventory(active_products)

    expected_qty = (
        result["simulated_reorder_point_units"]
        - result["simulated_available_units"]
    ).clip(lower=0)

    assert (result["simulated_suggested_reorder_qty"] == expected_qty).all()

    stockout = result["simulated_available_units"] <= 0
    reorder = (
        (result["simulated_available_units"] > 0)
        & (
            result["simulated_available_units"]
            <= result["simulated_reorder_point_units"]
        )
    )
    available = (
        result["simulated_available_units"]
        > result["simulated_reorder_point_units"]
    )

    assert (result.loc[stockout, "simulated_stock_status"] == "Stockout").all()
    assert (result.loc[reorder, "simulated_stock_status"] == "Reorder").all()
    assert (result.loc[available, "simulated_stock_status"] == "Available").all()


def test_simulation_is_explicitly_labelled(active_products):
    result = generate_simulated_erp_inventory(active_products)

    assert result["simulation_label"].eq(SIMULATION_LABEL).all()


def test_invalid_inputs_raise_clear_errors():
    with pytest.raises(ValueError, match="SKU_number"):
        generate_simulated_erp_inventory(pd.DataFrame({"other": [1]}))

    with pytest.raises(ValueError, match="at least 1"):
        generate_simulated_erp_inventory(
            pd.DataFrame({"SKU_number": ["1001"]}),
            max_products=0,
        )

    with pytest.raises(ValueError, match="No valid SKU"):
        generate_simulated_erp_inventory(
            pd.DataFrame({"SKU_number": [None, " "]})
        )


def test_days_of_cover_and_availability_risk_are_consistent(active_products):
    result = generate_simulated_erp_inventory(active_products)

    expected_cover = (
        result["simulated_available_units"]
        / result["simulated_daily_demand"]
    ).round(2)
    pd.testing.assert_series_equal(
        result["simulated_days_of_cover"],
        expected_cover,
        check_names=False,
    )

    assert (result["simulated_days_of_cover"] >= 0).all()
    assert result["simulated_availability_risk"].isin(
        ["Critical - Stockout", "At risk", "Monitor", "Adequate cover"]
    ).all()

    stockout = result["simulated_available_units"] <= 0
    assert (
        result.loc[stockout, "simulated_availability_risk"]
        == "Critical - Stockout"
    ).all()

    at_risk = (
        (result["simulated_available_units"] > 0)
        & (
            result["simulated_available_units"]
            < result["simulated_lead_time_demand_units"]
        )
    )
    assert (
        result.loc[at_risk, "simulated_availability_risk"] == "At risk"
    ).all()


def test_lead_time_demand_is_rounded_up(active_products):
    result = generate_simulated_erp_inventory(active_products)
    expected = np.ceil(
        result["simulated_daily_demand"]
        * result["simulated_lead_time_days"]
    ).astype("int64")

    pd.testing.assert_series_equal(
        result["simulated_lead_time_demand_units"],
        expected,
        check_names=False,
    )
