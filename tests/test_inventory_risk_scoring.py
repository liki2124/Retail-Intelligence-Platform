import pandas as pd
import pytest

from src.inventory import score_inventory_risk


def test_zero_stock_and_clearance_are_highest_priority():
    df = pd.DataFrame([
        {"product_id": "P1", "category": "Shoes", "status": "Clearance", "units": 0},
    ])
    result = score_inventory_risk(df, low_stock_threshold=30)
    assert result.loc[0, "risk_indicator"] == "Zero stock"
    assert result.loc[0, "risk_score"] == 100
    assert result.loc[0, "risk_priority"] == "Critical"


def test_low_stock_uses_configured_threshold():
    df = pd.DataFrame([
        {"product_id": "P1", "category": "Shoes", "status": "Full Price", "units": 20},
        {"product_id": "P2", "category": "Shoes", "status": "Full Price", "units": 40},
    ])
    result = score_inventory_risk(df, low_stock_threshold=30)
    assert result.loc[0, "risk_indicator"] == "Low stock"
    assert result.loc[0, "risk_score"] == 40
    assert result.loc[1, "risk_indicator"] == "Within threshold"


def test_markdown_status_adds_points_and_reason():
    df = pd.DataFrame([
        {"product_id": "P1", "category": "Shoes", "status": "Markdown T2", "units": 50},
    ])
    result = score_inventory_risk(df, low_stock_threshold=30)
    assert result.loc[0, "risk_score"] == 20
    assert result.loc[0, "risk_priority"] == "Medium"
    assert "Markdown T2" in result.loc[0, "risk_reason"]


def test_missing_units_are_flagged_for_data_review():
    df = pd.DataFrame([
        {"product_id": "P1", "category": "Shoes", "status": "Full Price", "units": None},
    ])
    result = score_inventory_risk(df, low_stock_threshold=30)
    assert result.loc[0, "risk_indicator"] == "Data issue"
    assert result.loc[0, "risk_priority"] == "Review data"


def test_negative_threshold_is_rejected():
    df = pd.DataFrame([
        {"product_id": "P1", "category": "Shoes", "status": "Full Price", "units": 5},
    ])
    with pytest.raises(ValueError):
        score_inventory_risk(df, low_stock_threshold=-1)
