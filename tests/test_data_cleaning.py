from src.inventory import load_inventory, validate_inventory


def test_sample_csv_loads_without_quality_issues():
    df = load_inventory("data/sample/inventory_sample.csv")
    assert len(df) == 6
    assert validate_inventory(df) == []


def test_sample_csv_has_expected_columns():
    df = load_inventory("data/sample/inventory_sample.csv")
    assert {"product_id", "category", "status", "units"}.issubset(df.columns)
