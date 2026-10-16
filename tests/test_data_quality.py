from src.inventory import validate_inventory


def test_valid_inventory_has_no_issues(inventory_df):
    assert validate_inventory(inventory_df) == []


def test_negative_units_are_flagged(inventory_df):
    inventory_df.loc[0, "units"] = -5
    assert "Negative inventory units found" in validate_inventory(inventory_df)


def test_unknown_status_is_flagged(inventory_df):
    inventory_df.loc[0, "status"] = "Unknown"
    assert "Unknown inventory status found" in validate_inventory(inventory_df)


def test_duplicate_rows_are_flagged(inventory_df):
    duplicate = inventory_df.iloc[[0]]
    inventory_df = __import__("pandas").concat(
        [inventory_df, duplicate], ignore_index=True
    )
    assert "Duplicate rows found" in validate_inventory(inventory_df)


def test_missing_required_values_are_flagged(inventory_df):
    inventory_df.loc[0, "product_id"] = None
    assert "Required fields contain missing values" in validate_inventory(inventory_df)
