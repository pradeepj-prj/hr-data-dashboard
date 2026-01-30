"""Organization chart (treemap) page."""

import streamlit as st
import pandas as pd
import plotly.express as px

from hr_dashboard.data_manager import enrich_employee_data
from hr_dashboard.utils.chart_helpers import BU_COLORS, SENIORITY_COLORS


def render(data: dict[str, pd.DataFrame]) -> None:
    """
    Render the organization chart (treemap) page.

    Args:
        data: Filtered HR data dictionary
    """
    employees_df = data["employee"]
    if len(employees_df) == 0:
        st.warning("No employees match the current filters.")
        return

    enriched_df = enrich_employee_data(data)

    st.subheader("Organization Hierarchy - Tree View")

    # View options
    col1, col2 = st.columns([1, 3])
    with col1:
        color_by = st.selectbox(
            "Color by",
            options=["Business Unit", "Seniority Level"],
            index=0,
        )

    # Prepare data for treemap
    render_org_treemap(enriched_df, color_by)

    # Also show summary table
    st.divider()
    render_org_summary_table(enriched_df, data)


def render_org_treemap(enriched_df: pd.DataFrame, color_by: str) -> None:
    """Render organization treemap."""
    # Build hierarchy: Business Unit -> Org Name -> Employee
    df = enriched_df.copy()

    # Filter out rows with missing hierarchy data
    required_cols = ["business_unit", "org_name", "employee_id", "first_name", "last_name"]
    for col in required_cols:
        if col not in df.columns:
            st.info(f"Column {col} not available for treemap")
            return

    df = df.dropna(subset=["business_unit", "org_name"])

    if len(df) == 0:
        st.info("No data available for treemap after filtering")
        return

    # Create full name
    df["full_name"] = df["first_name"] + " " + df["last_name"]

    # Determine color column and mapping
    if color_by == "Business Unit":
        color_col = "business_unit"
        color_map = BU_COLORS
    else:
        # Seniority level
        if "seniority_level" not in df.columns:
            st.info("Seniority level data not available")
            color_col = "business_unit"
            color_map = BU_COLORS
        else:
            # Convert seniority to string labels for better display
            seniority_labels = {
                1: "1-Entry",
                2: "2-Junior",
                3: "3-Mid",
                4: "4-Senior",
                5: "5-Executive",
            }
            df["seniority_label"] = df["seniority_level"].map(seniority_labels)
            color_col = "seniority_label"
            color_map = {seniority_labels[k]: v for k, v in SENIORITY_COLORS.items()}

    # Create treemap
    fig = px.treemap(
        df,
        path=["business_unit", "org_name", "full_name"],
        title="Organization Structure",
        color=color_col,
        color_discrete_map=color_map,
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=60, b=10),
        height=600,
    )
    fig.update_traces(
        textinfo="label",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_org_summary_table(enriched_df: pd.DataFrame, data: dict[str, pd.DataFrame]) -> None:
    """Render organization summary statistics table."""
    st.subheader("Organization Summary")

    org_units = data["organization_unit"]

    # Calculate headcount by org
    if "org_id" in enriched_df.columns:
        org_headcount = (
            enriched_df.groupby("org_id")
            .agg(
                headcount=("employee_id", "count"),
                avg_salary=("annual_salary", "mean") if "annual_salary" in enriched_df.columns else ("employee_id", "count"),
            )
            .reset_index()
        )

        # Merge with org names
        org_summary = org_units.merge(org_headcount, on="org_id", how="left")
        org_summary["headcount"] = org_summary["headcount"].fillna(0).astype(int)

        # Select and order columns
        display_cols = ["org_id", "org_name", "business_unit", "headcount"]
        if "avg_salary" in org_summary.columns and "annual_salary" in enriched_df.columns:
            org_summary["avg_salary"] = org_summary["avg_salary"].round(0)
            display_cols.append("avg_salary")

        # Filter to orgs with headcount > 0
        org_summary = org_summary[org_summary["headcount"] > 0]

        # Sort by headcount
        org_summary = org_summary.sort_values("headcount", ascending=False)

        st.dataframe(
            org_summary[display_cols],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Organization data not available")
