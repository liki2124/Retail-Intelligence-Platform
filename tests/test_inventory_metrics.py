from src.inventory import inventory_summary


def test_total_inventory_units(inventory_df):
    assert inventory_df["units"].sum() == 230


def test_inventory_summary_units(inventory_df):
    summary = inventory_summary(inventory_df)
    assert summary["total_units"].sum() == 230


def test_inventory_summary_contains_all_statuses(inventory_df):
    summary = inventory_summary(inventory_df)
    assert set(summary["status"]) == set(inventory_df["status"])


def test_unique_product_count(inventory_df):
    assert inventory_df["product_id"].nunique() == 4
