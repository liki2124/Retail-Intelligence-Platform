from pathlib import Path
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st

from src.inventory import load_inventory, validate_inventory, inventory_summary, score_inventory_risk, calculate_replenishment
from src.erp_simulation import generate_simulated_erp_inventory


PROJECT_ROOT = Path(__file__).resolve().parent
DEPLOYMENT_DB = PROJECT_ROOT / "dashboard_data" / "retail_analytics.db"
LOCAL_DB = PROJECT_ROOT / "data" / "processed" / "retail_analytics.db"
DB_PATH = DEPLOYMENT_DB if DEPLOYMENT_DB.exists() else LOCAL_DB

st.set_page_config(
    page_title="Retail Intelligence Platform",
    page_icon="📊",
    layout="wide",
)

st.title("Retail Intelligence Platform")
st.caption(
    "Interactive retail data exploration powered by Python, SQLite and Plotly"
)


@st.cache_data
def load_table(table_name: str) -> pd.DataFrame:
    """Load a known table from the project SQLite database."""
    allowed_tables = {"all_records", "active_products", "historical_sales"}
    if table_name not in allowed_tables:
        raise ValueError("Unsupported table name.")

    with sqlite3.connect(DB_PATH) as connection:
        return pd.read_sql_query(
            f'SELECT * FROM "{table_name}"',
            connection,
        )


if not DB_PATH.exists():
    st.error(f"Database not found: {DB_PATH}")
    st.info(
        "Run `python build_data_pipeline.py` from the project directory. "
        "If generated outputs already exist, review them before using "
        "`python build_data_pipeline.py --force`."
    )
    st.stop()

try:
    all_records = load_table("all_records")
    active = load_table("active_products")
    historical = load_table("historical_sales")
except Exception as exc:
    st.error(f"Could not load the SQLite database: {exc}")
    st.stop()

if all_records.empty:
    st.warning("The all_records table is empty.")
    st.stop()


# Sidebar filters
st.sidebar.header("Dashboard filters")

marketing_values = sorted(
    all_records["MarketingType"].dropna().astype(str).unique().tolist()
)
selected_marketing = st.sidebar.multiselect(
    "Marketing type",
    options=marketing_values,
    default=marketing_values,
)

year_values = pd.to_numeric(
    all_records["ReleaseYear"], errors="coerce"
).dropna()
if not year_values.empty:
    min_year = int(year_values.min())
    max_year = int(year_values.max())
    if min_year < max_year:
        selected_years = st.sidebar.slider(
            "Release year",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year),
        )
    else:
        selected_years = (min_year, max_year)
else:
    selected_years = None

filtered = all_records[
    all_records["MarketingType"].astype(str).isin(selected_marketing)
].copy()

filtered_years = pd.to_numeric(filtered["ReleaseYear"], errors="coerce")
if selected_years is not None:
    filtered = filtered[
        filtered_years.between(selected_years[0], selected_years[1])
    ].copy()

st.sidebar.caption(
    "Filters affect the overall-record analyses. Active and historical "
    "summary cards use their respective complete tables."
)


# KPI calculations
total_records = len(filtered)
unique_skus = filtered["SKU_number"].nunique(dropna=True)
historical_sold_count = pd.to_numeric(
    historical["SoldCount"], errors="coerce"
).sum()
active_records = len(active)
historical_records = len(historical)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Filtered records", f"{total_records:,}")
k2.metric("Distinct SKUs", f"{unique_skus:,}")
k3.metric("Active records", f"{active_records:,}")
k4.metric("Historical records", f"{historical_records:,}")
k5.metric("Historical SoldCount", f"{historical_sold_count:,.0f}")

st.caption(
    "Record counts are not necessarily unique-product counts. SoldCount is "
    "a recorded dataset measure, not verified revenue or customer conversion."
)

tab_overview, tab_sales, tab_pricing, tab_data, tab_inventory = st.tabs(
    [
        "Overview",
        "Historical indicators",
        "Pricing analysis",
        "Data explorer",
        "Inventory Risk & Availability",
    ]
)


with tab_overview:
    st.subheader("Records by marketing type")

    if filtered.empty:
        st.info("No records match the selected filters.")
    else:
        marketing_summary = (
            filtered.groupby("MarketingType", dropna=False)
            .agg(
                Record_Count=("SKU_number", "size"),
                Distinct_SKUs=("SKU_number", "nunique"),
            )
            .reset_index()
        )
        marketing_summary["MarketingType"] = (
            marketing_summary["MarketingType"]
            .fillna("Missing")
            .astype(str)
        )

        fig = px.bar(
            marketing_summary,
            x="MarketingType",
            y="Record_Count",
            color="MarketingType",
            title="Record count by marketing type",
            labels={
                "MarketingType": "Marketing type",
                "Record_Count": "Records",
            },
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            marketing_summary.sort_values("Record_Count", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Records by release year")
    year_summary = filtered.copy()
    year_summary["ReleaseYear"] = pd.to_numeric(
        year_summary["ReleaseYear"], errors="coerce"
    )
    year_summary = year_summary.dropna(subset=["ReleaseYear"])
    year_summary["ReleaseYear"] = year_summary["ReleaseYear"].astype(int)

    if year_summary.empty:
        st.info("No valid release years are available for these filters.")
    else:
        year_summary = (
            year_summary.groupby("ReleaseYear")
            .agg(
                Record_Count=("SKU_number", "size"),
                Distinct_SKUs=("SKU_number", "nunique"),
            )
            .reset_index()
            .sort_values("ReleaseYear")
        )
        fig = px.line(
            year_summary,
            x="ReleaseYear",
            y="Record_Count",
            markers=True,
            title="Records by release year",
            labels={
                "ReleaseYear": "Release year",
                "Record_Count": "Records",
            },
        )
        st.plotly_chart(fig, use_container_width=True)


with tab_sales:
    st.subheader("Historical sales indicators")
    st.caption(
        "These are historical source-record indicators, not transaction-level "
        "sales over time."
    )

    sold = historical.copy()
    sold["SoldCount"] = pd.to_numeric(sold["SoldCount"], errors="coerce")
    sold["SoldFlag"] = pd.to_numeric(sold["SoldFlag"], errors="coerce")

    s1, s2, s3 = st.columns(3)
    s1.metric("Historical records", f"{len(sold):,}")
    s2.metric(
        "Records with SoldFlag = 1",
        f"{int(sold['SoldFlag'].eq(1).sum()):,}",
    )
    s3.metric(
        "Sum of recorded SoldCount",
        f"{sold['SoldCount'].sum():,.0f}",
    )

    sales_by_marketing = (
        sold.groupby("MarketingType", dropna=False)
        .agg(
            Record_Count=("SKU_number", "size"),
            SoldCount_Total=("SoldCount", "sum"),
        )
        .reset_index()
    )
    sales_by_marketing["MarketingType"] = (
        sales_by_marketing["MarketingType"].fillna("Missing").astype(str)
    )

    fig = px.bar(
        sales_by_marketing,
        x="MarketingType",
        y="SoldCount_Total",
        title="Recorded SoldCount by marketing type",
        labels={
            "MarketingType": "Marketing type",
            "SoldCount_Total": "Sum of SoldCount",
        },
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(sales_by_marketing, use_container_width=True, hide_index=True)


with tab_pricing:
    st.subheader("Price distributions and relationships")

    price_columns = [
        column
        for column in ["PriceReg", "LowUserPrice", "LowNetPrice"]
        if column in filtered.columns
    ]

    if not price_columns:
        st.warning("No supported price columns were found.")
    else:
        chosen_price = st.selectbox(
            "Choose a price field",
            options=price_columns,
        )
        prices = pd.to_numeric(filtered[chosen_price], errors="coerce")
        price_data = pd.DataFrame({"Price": prices}).dropna()
        price_data = price_data[price_data["Price"] >= 0]

        if price_data.empty:
            st.info("No non-negative numeric prices match these filters.")
        else:
            p1, p2, p3 = st.columns(3)
            p1.metric("Records with price", f"{len(price_data):,}")
            p2.metric("Median price", f"{price_data['Price'].median():,.2f}")
            p3.metric("Mean price", f"{price_data['Price'].mean():,.2f}")

            fig = px.histogram(
                price_data,
                x="Price",
                nbins=50,
                title=f"Distribution of {chosen_price}",
                labels={"Price": chosen_price},
            )
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("SQL-aligned pricing quality review")

    # Reuse the same source table as sql/analytics/05_price_quality_flags.sql.
    pricing_review = historical.copy()

    pricing_review = pricing_review[
        pricing_review["MarketingType"].astype(str).isin(selected_marketing)
    ].copy()

    if selected_years is not None:
        review_years = pd.to_numeric(
            pricing_review["ReleaseYear"], errors="coerce"
        )
        pricing_review = pricing_review[
            review_years.between(selected_years[0], selected_years[1])
        ].copy()

    price_fields = ["PriceReg", "LowUserPrice", "LowNetPrice"]
    for column in price_fields:
        pricing_review[column] = pd.to_numeric(
            pricing_review[column], errors="coerce"
        )

    # Match the six CASE rules in 05_price_quality_flags.sql.
    pricing_review["zero_regular_price_flag"] = (
        pricing_review["PriceReg"].eq(0).astype(int)
    )
    pricing_review["high_regular_price_review_flag"] = (
        pricing_review["PriceReg"].gt(500).astype(int)
    )
    pricing_review["low_user_above_regular_flag"] = (
        pricing_review["LowUserPrice"].gt(pricing_review["PriceReg"]).astype(int)
    )
    pricing_review["low_net_above_regular_flag"] = (
        pricing_review["LowNetPrice"].gt(pricing_review["PriceReg"]).astype(int)
    )
    pricing_review["extreme_low_user_price_review_flag"] = (
        pricing_review["LowUserPrice"].gt(1000).astype(int)
    )
    pricing_review["extreme_low_net_price_review_flag"] = (
        pricing_review["LowNetPrice"].gt(1000).astype(int)
    )

    flag_columns = [
        "zero_regular_price_flag",
        "high_regular_price_review_flag",
        "low_user_above_regular_flag",
        "low_net_above_regular_flag",
        "extreme_low_user_price_review_flag",
        "extreme_low_net_price_review_flag",
    ]

    pricing_review["Any_Review_Flag"] = (
        pricing_review[flag_columns].max(axis=1)
    )

    # Preserve the prioritisation used in the SQL ORDER BY clause.
    pricing_review["review_priority"] = 4
    pricing_review.loc[
        pricing_review["PriceReg"].gt(500), "review_priority"
    ] = 3

    above_regular = (
        pricing_review["LowUserPrice"].gt(pricing_review["PriceReg"])
        | pricing_review["LowNetPrice"].gt(pricing_review["PriceReg"])
    )
    pricing_review.loc[above_regular, "review_priority"] = 2
    pricing_review.loc[
        pricing_review["PriceReg"].eq(0), "review_priority"
    ] = 1

    extreme_price = (
        pricing_review["LowUserPrice"].gt(1000)
        | pricing_review["LowNetPrice"].gt(1000)
    )
    pricing_review.loc[extreme_price, "review_priority"] = 0

    pricing_review["extreme_price_sort"] = pricing_review[
        "LowUserPrice"
    ].where(
        pricing_review["LowUserPrice"].gt(1000),
        pricing_review["LowNetPrice"].where(
            pricing_review["LowNetPrice"].gt(1000), 0
        ),
    )

    flagged = pricing_review[
        pricing_review["Any_Review_Flag"].eq(1)
    ].sort_values(
        ["review_priority", "extreme_price_sort"],
        ascending=[True, False],
    )

    st.metric("Historical records reviewed", f"{len(pricing_review):,}")
    st.metric("Records flagged for review", f"{len(flagged):,}")

    st.caption(
        "These six flags match the conditions in "
        "sql/analytics/05_price_quality_flags.sql. They identify records "
        "for investigation, not confirmed pricing errors. Sidebar filters "
        "apply to marketing type and release year."
    )

    st.dataframe(
        flagged[
            [
                "SKU_number",
                "MarketingType",
                "SoldFlag",
                "SoldCount",
                "PriceReg",
                "LowUserPrice",
                "LowNetPrice",
                *flag_columns,
            ]
        ].head(500),
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download pricing review as CSV",
        data=flagged.to_csv(index=False).encode("utf-8-sig"),
        file_name="retail_pricing_quality_review.csv",
        mime="text/csv",
    )

with tab_data:
    st.subheader("Filtered data explorer")
    st.write(f"Showing {len(filtered):,} filtered records.")

    display_columns = [
        column
        for column in [
            "SKU_number",
            "MarketingType",
            "ReleaseYear",
            "SoldFlag",
            "SoldCount",
            "PriceReg",
            "LowUserPrice",
            "LowNetPrice",
        ]
        if column in filtered.columns
    ]

    st.dataframe(
        filtered[display_columns].head(1000),
        use_container_width=True,
        hide_index=True,
    )
    st.caption("The table previews up to 1,000 rows for browser performance.")

    csv_bytes = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Download filtered records as CSV",
        data=csv_bytes,
        file_name="retail_filtered_records.csv",
        mime="text/csv",
    )


with tab_inventory:
    st.subheader("Inventory Risk & Availability")
    st.caption(
        "Sample inventory demonstration using data/sample/inventory_sample.csv. "
        "This is not live ERP stock and does not represent the full retail dataset."
    )

    st.divider()
    st.subheader("Simulated ERP Inventory - Availability & Replenishment")
    st.warning(
        "SIMULATED DATA - NOT LIVE ERP INVENTORY. Product IDs are taken from "
        "the real active-products dataset. Stock quantities, reservations, "
        "categories, demand, lead times, safety stock, and recommendations "
        "are generated assumptions, not actual ERP records."
    )

    active_products_path = (
        PROJECT_ROOT / "data" / "processed" / "active_products.csv"
    )

    if not active_products_path.exists():
        st.info(
            "The active-products dataset was not found. Run the existing "
            "data pipeline before using the simulated ERP section."
        )
    else:
        try:
            active_products_for_simulation = pd.read_csv(
                active_products_path,
                usecols=["SKU_number"],
                dtype={"SKU_number": "string"},
            )
            simulated_erp = generate_simulated_erp_inventory(
                active_products_for_simulation,
                max_products=2000,
                seed=42,
            )

            sim_stockouts = int(
                (simulated_erp["simulated_stock_status"] == "Stockout").sum()
            )
            sim_reorders = int(
                (simulated_erp["simulated_stock_status"] == "Reorder").sum()
            )
            sim_available_units = int(
                simulated_erp["simulated_available_units"].sum()
            )

            sim1, sim2, sim3, sim4 = st.columns(4)
            sim1.metric("Simulated products", f"{len(simulated_erp):,}")
            sim2.metric("Available units", f"{sim_available_units:,}")
            sim3.metric("Stockouts", f"{sim_stockouts:,}")
            sim4.metric("Reorder candidates", f"{sim_reorders:,}")

            risk_counts = simulated_erp["simulated_availability_risk"].value_counts()
            risk1, risk2, risk3, risk4 = st.columns(4)
            risk1.metric("Critical stockouts", int(risk_counts.get("Critical - Stockout", 0)))
            risk2.metric("At-risk products", int(risk_counts.get("At risk", 0)))
            risk3.metric("Monitor products", int(risk_counts.get("Monitor", 0)))
            risk4.metric("Adequate cover", int(risk_counts.get("Adequate cover", 0)))

            st.markdown("**Stock availability and days of cover**")
            st.caption(
                "Days of cover = available units / simulated daily demand. "
                "Risk levels compare simulated stock with simulated demand "
                "during supplier lead time; they are demonstration values."
            )

            risk_filter = st.multiselect(
                "Availability risk",
                options=[
                    "Critical - Stockout",
                    "At risk",
                    "Monitor",
                    "Adequate cover",
                ],
                default=[
                    "Critical - Stockout",
                    "At risk",
                    "Monitor",
                    "Adequate cover",
                ],
                key="simulated_erp_risk_filter",
            )
            risk_filtered = simulated_erp[
                simulated_erp["simulated_availability_risk"].isin(risk_filter)
            ].copy()

            st.dataframe(
                risk_filtered.sort_values(
                    ["simulated_days_of_cover", "product_id"],
                    ascending=[True, True],
                ).head(100),
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                "A deterministic sample of up to 2,000 unique active SKUs is "
                "used for dashboard performance. The same seed reproduces the "
                "same synthetic values. These metrics are a demonstration, "
                "not a measurement of actual retail stock."
            )

            st.markdown("**Product-level simulated ERP drill-down**")
            status_filter = st.multiselect(
                "Simulated stock status",
                options=["Stockout", "Reorder", "Available"],
                default=["Stockout", "Reorder", "Available"],
                key="simulated_erp_status_filter",
            )
            simulated_filtered = simulated_erp[
                simulated_erp["simulated_stock_status"].isin(status_filter)
            ].copy()

            st.dataframe(
                simulated_filtered.sort_values(
                    ["simulated_available_units", "product_id"],
                    ascending=[True, True],
                ).head(100),
                use_container_width=True,
                hide_index=True,
            )
            st.caption(
                "The table displays up to 100 products matching the selected "
                "stock-status filter. The CSV contains all products matching "
                "that filter."
            )
            st.download_button(
                "Download simulated ERP inventory CSV",
                data=simulated_filtered.to_csv(index=False).encode("utf-8-sig"),
                file_name="simulated_erp_inventory.csv",
                mime="text/csv",
                key="download_simulated_erp_inventory",
            )
        except Exception as exc:
            st.error(f"Could not generate simulated ERP inventory: {exc}")

    inventory_path = PROJECT_ROOT / "data" / "sample" / "inventory_sample.csv"

    if not inventory_path.exists():
        st.error(f"Sample inventory file not found: {inventory_path}")
    else:
        try:
            inventory = load_inventory(inventory_path)
            issues = validate_inventory(inventory)
        except Exception as exc:
            st.error(f"Could not load sample inventory: {exc}")
            inventory = pd.DataFrame()
            issues = []

        if not inventory.empty:
            if issues:
                st.warning("Inventory data-quality checks found issues:")
                for issue in issues:
                    st.write(f"- {issue}")
            else:
                st.success("Inventory validation passed.")

            max_units = max(100, int(inventory["units"].max()) + 1)

            filter_col1, filter_col2, filter_col3 = st.columns(3)

            categories = sorted(
                inventory["category"].dropna().astype(str).unique().tolist()
            )
            statuses = sorted(
                inventory["status"].dropna().astype(str).unique().tolist()
            )

            with filter_col1:
                selected_categories = st.multiselect(
                    "Category",
                    options=categories,
                    default=categories,
                    key="inventory_category_filter",
                )

            with filter_col2:
                selected_statuses = st.multiselect(
                    "Inventory status",
                    options=statuses,
                    default=statuses,
                    key="inventory_status_filter",
                )

            with filter_col3:
                low_stock_threshold = st.slider(
                    "Low-stock threshold (units)",
                    min_value=0,
                    max_value=max_units,
                    value=min(30, max_units),
                    step=5 if max_units >= 5 else 1,
                    help=(
                        "A configurable demonstration threshold, not an "
                        "ERP-approved reorder point."
                    ),
                    key="inventory_low_stock_threshold",
                )

            product_query = st.text_input(
                "Search product ID",
                placeholder="For example, P001",
                key="inventory_product_search",
            ).strip().casefold()

            filtered_inventory = inventory[
                inventory["category"].isin(selected_categories)
                & inventory["status"].isin(selected_statuses)
            ].copy()

            if product_query:
                filtered_inventory = filtered_inventory[
                    filtered_inventory["product_id"]
                    .astype(str)
                    .str.casefold()
                    .str.contains(product_query, regex=False)
                ]

            filtered_inventory["risk_indicator"] = "Within threshold"
            filtered_inventory.loc[
                filtered_inventory["units"] <= low_stock_threshold,
                "risk_indicator",
            ] = "Low stock"
            filtered_inventory.loc[
                filtered_inventory["units"] <= 0,
                "risk_indicator",
            ] = "Zero stock"

            filtered_inventory = score_inventory_risk(
                filtered_inventory, low_stock_threshold
            )

            total_units = filtered_inventory["units"].sum()
            product_count = filtered_inventory["product_id"].nunique()
            zero_stock_rows = int((filtered_inventory["units"] <= 0).sum())
            low_stock_rows = int(
                (
                    (filtered_inventory["units"] > 0)
                    & (filtered_inventory["units"] <= low_stock_threshold)
                ).sum()
            )

            metric1, metric2, metric3, metric4 = st.columns(4)
            metric1.metric("Products", f"{product_count:,}")
            metric2.metric("Total units", f"{total_units:,.0f}")
            metric3.metric("Low-stock records", f"{low_stock_rows:,}")
            metric4.metric("Zero-stock records", f"{zero_stock_rows:,}")

            markdown_statuses = ["Markdown T1", "Markdown T2", "Clearance"]
            markdown_units = filtered_inventory.loc[
                filtered_inventory["status"].isin(markdown_statuses), "units"
            ].sum()
            markdown_share = (
                100 * markdown_units / total_units if total_units > 0 else 0
            )
            high_priority_count = int(
                filtered_inventory["risk_priority"].isin(["High", "Critical"]).sum()
            )

            exposure1, exposure2, exposure3 = st.columns(3)
            exposure1.metric("Markdown / clearance units", f"{markdown_units:,.0f}")
            exposure2.metric("Markdown / clearance share", f"{markdown_share:.1f}%")
            exposure3.metric("High / critical priority", f"{high_priority_count:,}")

            st.caption(
                "Markdown exposure is based on units in Markdown T1, Markdown T2, "
                "and Clearance statuses. It is not a measure of financial loss."
            )

            st.caption(
                f"Low stock means 1 to {low_stock_threshold} units; "
                "zero stock means 0 or fewer units. Negative units are "
                "also a data-quality issue."
            )

            if filtered_inventory.empty:
                st.info("No inventory records match the selected filters.")
            else:
                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
                    summary = inventory_summary(filtered_inventory)
                    st.plotly_chart(
                        px.bar(
                            summary,
                            x="status",
                            y="total_units",
                            title="Units by inventory status",
                            labels={
                                "status": "Inventory status",
                                "total_units": "Total units",
                            },
                        ),
                        use_container_width=True,
                    )

                with chart_col2:
                    category_summary = (
                        filtered_inventory.groupby("category", as_index=False)
                        .agg(total_units=("units", "sum"))
                        .sort_values("total_units", ascending=False)
                    )
                    st.plotly_chart(
                        px.bar(
                            category_summary,
                            x="category",
                            y="total_units",
                            title="Units by category",
                            labels={
                                "category": "Category",
                                "total_units": "Total units",
                            },
                        ),
                        use_container_width=True,
                    )

                st.subheader("Product-level inventory detail")
                st.dataframe(
                    filtered_inventory.sort_values(
                        ["units", "product_id"], ascending=[True, True]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

                st.download_button(
                    "Download filtered inventory CSV",
                    data=filtered_inventory.to_csv(index=False).encode("utf-8-sig"),
                    file_name="retail_inventory_risk_review.csv",
                    mime="text/csv",
                    key="download_inventory_risk",
                )

                risk_records = filtered_inventory[
                    (filtered_inventory["risk_priority"] != "Low")
                    | (filtered_inventory["status"] != "Full Price")
                ]
                st.subheader("Inventory records requiring review")
                if risk_records.empty:
                    st.info(
                        "No inventory records meet the current review rules."
                    )
                else:
                    st.dataframe(
                        risk_records,
                        use_container_width=True,
                        hide_index=True,
                    )
                    st.download_button(
                        "Download inventory risk records",
                        data=risk_records.to_csv(index=False).encode("utf-8-sig"),
                        file_name="retail_inventory_risk_records.csv",
                        mime="text/csv",
                        key="download_inventory_risk_only",
                    )

                st.subheader("Demand-aware replenishment planner")
                st.caption(
                    "Enter validated demand and supplier assumptions for each "
                    "product. Blank inputs are intentionally not estimated. "
                    "The current sample is illustrative, not live ERP stock."
                )

                planning_inputs = filtered_inventory[
                    ["product_id", "category", "status", "units"]
                ].copy()

                planning_inputs["average_daily_demand"] = float("nan")
                planning_inputs["lead_time_days"] = float("nan")
                planning_inputs["safety_stock_units"] = float("nan")

                st.markdown("**Editable planning assumptions**")
                edited_inputs = st.data_editor(
                    planning_inputs,
                    hide_index=True,
                    use_container_width=True,
                    key="replenishment_inputs_editor",
                    disabled=["product_id", "category", "status", "units"],
                    column_config={
                        "product_id": st.column_config.TextColumn(
                            "Product ID"
                        ),
                        "category": st.column_config.TextColumn("Category"),
                        "status": st.column_config.TextColumn("Price status"),
                        "units": st.column_config.NumberColumn(
                            "Current units", format="%d"
                        ),
                        "average_daily_demand": st.column_config.NumberColumn(
                            "Avg daily demand",
                            help="Units per day from validated demand data.",
                            min_value=0.0,
                            step=0.1,
                            format="%.2f",
                        ),
                        "lead_time_days": st.column_config.NumberColumn(
                            "Lead time (days)",
                            help="Supplier lead time in days.",
                            min_value=0,
                            step=1,
                            format="%d",
                        ),
                        "safety_stock_units": st.column_config.NumberColumn(
                            "Safety stock (units)",
                            help="Extra units held as a buffer.",
                            min_value=0,
                            step=1,
                            format="%d",
                        ),
                    },
                )

                replenishment_results = calculate_replenishment(edited_inputs)

                st.markdown("**Replenishment results**")
                status_counts = replenishment_results[
                    "replenishment_status"
                ].value_counts()

                metric1, metric2, metric3 = st.columns(3)
                metric1.metric(
                    "Products to reorder",
                    int(status_counts.get("Reorder", 0)),
                )
                metric2.metric(
                    "Insufficient inputs",
                    int(status_counts.get("Insufficient inputs", 0)),
                )
                metric3.metric(
                    "Input issues",
                    int(status_counts.get("Review invalid inputs", 0)),
                )

                result_columns = [
                    "product_id",
                    "category",
                    "status",
                    "units",
                    "average_daily_demand",
                    "lead_time_days",
                    "safety_stock_units",
                    "reorder_point_units",
                    "suggested_reorder_qty",
                    "replenishment_status",
                ]

                st.dataframe(
                    replenishment_results[result_columns],
                    use_container_width=True,
                    hide_index=True,
                )

                st.download_button(
                    "Download replenishment plan as CSV",
                    data=replenishment_results.to_csv(
                        index=False
                    ).encode("utf-8-sig"),
                    file_name="retail_replenishment_plan.csv",
                    mime="text/csv",
                    key="download_replenishment_plan",
                )

                st.caption(
                    "Reorder point = average daily demand × lead time + "
                    "safety stock. Suggested quantity = the positive "
                    "difference between reorder point and current units, "
                    "rounded up. These calculations are planning estimates, "
                    "not automated purchase orders."
                )

                st.info(
                    "These flags are simple quantity-based indicators. "
                    "Reliable reorder recommendations require additional "
                    "information such as demand, supplier lead time, safety "
                    "stock, and replenishment rules."
                )


st.divider()
st.caption(
    "Retail Intelligence Platform | Python · SQLite · SQL · Streamlit · Plotly"
)
