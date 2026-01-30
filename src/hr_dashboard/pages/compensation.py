"""Compensation analytics page."""

import streamlit as st
import pandas as pd

from hr_dashboard.data_manager import enrich_employee_data
from hr_dashboard.utils.chart_helpers import (
    BU_COLORS,
    SENIORITY_COLORS,
    create_histogram,
    create_box_plot,
    create_pie_chart,
)


def render(data: dict[str, pd.DataFrame]) -> None:
    """
    Render the compensation page.

    Args:
        data: Filtered HR data dictionary
    """
    if "employee_compensation" not in data:
        st.warning("Compensation data not available.")
        return

    employees_df = data["employee"]
    if len(employees_df) == 0:
        st.warning("No employees match the current filters.")
        return

    comp_df = data["employee_compensation"]
    enriched_df = enrich_employee_data(data)

    # Summary metrics
    render_compensation_kpis(enriched_df, comp_df)

    st.divider()

    # Charts row 1
    col1, col2 = st.columns(2)

    with col1:
        render_salary_distribution(enriched_df)

    with col2:
        render_salary_by_seniority(enriched_df)

    # Charts row 2
    col3, col4 = st.columns(2)

    with col3:
        render_salary_by_business_unit(enriched_df)

    with col4:
        render_change_reasons(comp_df)


def render_compensation_kpis(enriched_df: pd.DataFrame, comp_df: pd.DataFrame) -> None:
    """Render compensation KPI metrics."""
    col1, col2, col3, col4 = st.columns(4)

    if "annual_salary" not in enriched_df.columns:
        return

    salaries = enriched_df["annual_salary"].dropna()

    with col1:
        st.metric("Median Salary", f"${salaries.median():,.0f}")

    with col2:
        st.metric("Min Salary", f"${salaries.min():,.0f}")

    with col3:
        st.metric("Max Salary", f"${salaries.max():,.0f}")

    with col4:
        salary_range = salaries.max() - salaries.min()
        st.metric("Salary Range", f"${salary_range:,.0f}")


def render_salary_distribution(enriched_df: pd.DataFrame) -> None:
    """Render salary distribution histogram."""
    if "annual_salary" not in enriched_df.columns:
        st.info("Salary data not available")
        return

    fig = create_histogram(
        enriched_df,
        x="annual_salary",
        title="Salary Distribution",
        nbins=25,
    )
    fig.update_layout(xaxis_title="Annual Salary", yaxis_title="Count")
    fig.update_xaxes(tickformat="$,.0f")
    st.plotly_chart(fig, use_container_width=True)


def render_salary_by_seniority(enriched_df: pd.DataFrame) -> None:
    """Render salary box plot by seniority level."""
    if "annual_salary" not in enriched_df.columns or "seniority_level" not in enriched_df.columns:
        st.info("Salary or seniority data not available")
        return

    # Add seniority labels
    seniority_labels = {
        1: "1-Entry",
        2: "2-Junior",
        3: "3-Mid",
        4: "4-Senior",
        5: "5-Executive",
    }
    df = enriched_df.copy()
    df["level_label"] = df["seniority_level"].map(seniority_labels)

    # Create color mapping for labels
    label_colors = {seniority_labels[k]: v for k, v in SENIORITY_COLORS.items()}

    fig = create_box_plot(
        df,
        x="level_label",
        y="annual_salary",
        title="Salary by Seniority Level",
        color="level_label",
        color_discrete_map=label_colors,
    )
    fig.update_layout(showlegend=False, xaxis_title="Seniority Level", yaxis_title="Annual Salary")
    fig.update_yaxes(tickformat="$,.0f")
    st.plotly_chart(fig, use_container_width=True)


def render_salary_by_business_unit(enriched_df: pd.DataFrame) -> None:
    """Render salary box plot by business unit."""
    if "annual_salary" not in enriched_df.columns or "business_unit" not in enriched_df.columns:
        st.info("Salary or business unit data not available")
        return

    fig = create_box_plot(
        enriched_df,
        x="business_unit",
        y="annual_salary",
        title="Salary by Business Unit",
        color="business_unit",
        color_discrete_map=BU_COLORS,
    )
    fig.update_layout(showlegend=False, xaxis_title="Business Unit", yaxis_title="Annual Salary")
    fig.update_yaxes(tickformat="$,.0f")
    st.plotly_chart(fig, use_container_width=True)


def render_change_reasons(comp_df: pd.DataFrame) -> None:
    """Render compensation change reasons pie chart."""
    if "change_reason" not in comp_df.columns:
        st.info("Change reason data not available")
        return

    reason_counts = (
        comp_df.groupby("change_reason")
        .size()
        .reset_index(name="count")
    )

    fig = create_pie_chart(
        reason_counts,
        values="count",
        names="change_reason",
        title="Compensation Change Reasons",
    )
    st.plotly_chart(fig, use_container_width=True)
