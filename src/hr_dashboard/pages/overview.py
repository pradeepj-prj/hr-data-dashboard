"""Overview page with KPI metrics and summary charts."""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

from hr_dashboard.data_manager import enrich_employee_data
from hr_dashboard.utils.chart_helpers import (
    BU_COLORS,
    SENIORITY_COLORS,
    GENDER_COLORS,
    create_bar_chart,
    create_pie_chart,
)


def render(data: dict[str, pd.DataFrame]) -> None:
    """
    Render the overview page.

    Args:
        data: Filtered HR data dictionary
    """
    employees_df = data["employee"]
    enriched_df = enrich_employee_data(data)

    if len(employees_df) == 0:
        st.warning("No employees match the current filters.")
        return

    # KPI Row
    render_kpis(enriched_df, data)

    st.divider()

    # Charts row 1
    col1, col2 = st.columns(2)

    with col1:
        render_seniority_distribution(enriched_df)

    with col2:
        render_employment_type_breakdown(employees_df)

    # Charts row 2
    col3, col4 = st.columns(2)

    with col3:
        render_business_unit_distribution(enriched_df)

    with col4:
        render_gender_distribution(employees_df)


def render_kpis(enriched_df: pd.DataFrame, data: dict[str, pd.DataFrame]) -> None:
    """Render KPI metrics row."""
    col1, col2, col3, col4 = st.columns(4)

    # Total Employees
    with col1:
        st.metric("Total Employees", len(enriched_df))

    # Average Salary
    with col2:
        if "annual_salary" in enriched_df.columns:
            avg_salary = enriched_df["annual_salary"].mean()
            st.metric("Avg Salary", f"${avg_salary:,.0f}")
        else:
            st.metric("Avg Salary", "N/A")

    # Average Tenure
    with col3:
        today = date.today()
        enriched_df["tenure_years"] = enriched_df["hire_date"].apply(
            lambda x: (today - x).days / 365.25 if pd.notna(x) else 0
        )
        avg_tenure = enriched_df["tenure_years"].mean()
        st.metric("Avg Tenure", f"{avg_tenure:.1f} years")

    # Gender Split
    with col4:
        gender_counts = enriched_df["gender"].value_counts()
        female_pct = gender_counts.get("female", 0) / len(enriched_df) * 100
        male_pct = gender_counts.get("male", 0) / len(enriched_df) * 100
        st.metric("Gender Split", f"F: {female_pct:.0f}% / M: {male_pct:.0f}%")


def render_seniority_distribution(enriched_df: pd.DataFrame) -> None:
    """Render seniority level distribution bar chart."""
    if "seniority_level" not in enriched_df.columns:
        st.info("Seniority level data not available")
        return

    seniority_counts = (
        enriched_df.groupby("seniority_level")
        .size()
        .reset_index(name="count")
    )

    # Add labels
    seniority_labels = {
        1: "1-Entry",
        2: "2-Junior",
        3: "3-Mid",
        4: "4-Senior",
        5: "5-Executive",
    }
    seniority_counts["level_label"] = seniority_counts["seniority_level"].map(seniority_labels)

    # Create color mapping for labels
    label_colors = {seniority_labels[k]: v for k, v in SENIORITY_COLORS.items()}

    fig = create_bar_chart(
        seniority_counts,
        x="level_label",
        y="count",
        title="Seniority Level Distribution",
        color="level_label",
        color_discrete_map=label_colors,
    )
    fig.update_layout(showlegend=False, xaxis_title="Seniority Level", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True)


def render_employment_type_breakdown(employees_df: pd.DataFrame) -> None:
    """Render employment type pie chart."""
    emp_type_counts = (
        employees_df.groupby("employment_type")
        .size()
        .reset_index(name="count")
    )

    fig = create_pie_chart(
        emp_type_counts,
        values="count",
        names="employment_type",
        title="Employment Type Breakdown",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_business_unit_distribution(enriched_df: pd.DataFrame) -> None:
    """Render business unit distribution bar chart."""
    if "business_unit" not in enriched_df.columns:
        st.info("Business unit data not available")
        return

    bu_counts = (
        enriched_df.groupby("business_unit")
        .size()
        .reset_index(name="count")
    )

    fig = create_bar_chart(
        bu_counts,
        x="business_unit",
        y="count",
        title="Headcount by Business Unit",
        color="business_unit",
        color_discrete_map=BU_COLORS,
    )
    fig.update_layout(showlegend=False, xaxis_title="Business Unit", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True)


def render_gender_distribution(employees_df: pd.DataFrame) -> None:
    """Render gender distribution pie chart."""
    gender_counts = (
        employees_df.groupby("gender")
        .size()
        .reset_index(name="count")
    )

    fig = create_pie_chart(
        gender_counts,
        values="count",
        names="gender",
        title="Gender Distribution",
        color_discrete_map=GENDER_COLORS,
    )
    st.plotly_chart(fig, use_container_width=True)
