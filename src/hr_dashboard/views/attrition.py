"""Attrition page with turnover analysis and visualizations."""

import streamlit as st
import pandas as pd
from datetime import date

from hr_dashboard.data_manager import enrich_employee_data
from hr_dashboard.utils.chart_helpers import (
    BU_COLORS,
    SENIORITY_COLORS,
    ATTRITION_COLORS,
    TERMINATION_REASON_COLORS,
    create_bar_chart,
    create_pie_chart,
    create_line_chart,
)


def render(data: dict[str, pd.DataFrame]) -> None:
    """
    Render the attrition page.

    Args:
        data: Filtered HR data dictionary
    """
    employees_df = data["employee"]

    if len(employees_df) == 0:
        st.warning("No employees match the current filters.")
        return

    # Check if attrition data exists
    if "employment_status" not in employees_df.columns:
        st.info("Attrition data is not available. Enable attrition in the sidebar settings.")
        return

    enriched_df = enrich_employee_data(data)

    # Check if there are any terminated/retired employees
    status_counts = employees_df["employment_status"].value_counts()
    has_attrition = any(
        status in status_counts.index for status in ["Terminated", "Retired"]
    )

    if not has_attrition:
        st.info("No attrition data found. All employees are currently active.")
        render_kpis(enriched_df, employees_df)
        return

    # KPI Row
    render_kpis(enriched_df, employees_df)

    st.divider()

    # Charts row 1
    col1, col2 = st.columns(2)

    with col1:
        render_termination_reasons(employees_df)

    with col2:
        render_attrition_by_business_unit(enriched_df)

    # Charts row 2
    col3, col4 = st.columns(2)

    with col3:
        render_attrition_by_performance(enriched_df, data)

    with col4:
        render_attrition_by_tenure(enriched_df)

    # Charts row 3
    col5, col6 = st.columns(2)

    with col5:
        render_attrition_by_seniority(enriched_df)

    with col6:
        render_attrition_timeline(employees_df)


def render_kpis(enriched_df: pd.DataFrame, employees_df: pd.DataFrame) -> None:
    """Render KPI metrics row."""
    col1, col2, col3, col4, col5 = st.columns(5)

    total_employees = len(employees_df)
    status_counts = employees_df["employment_status"].value_counts()

    active_count = status_counts.get("Active", 0)
    terminated_count = status_counts.get("Terminated", 0)
    retired_count = status_counts.get("Retired", 0)

    # Attrition Rate
    with col1:
        attrition_rate = (terminated_count + retired_count) / total_employees * 100
        st.metric("Attrition Rate", f"{attrition_rate:.1f}%")

    # Active / Terminated / Retired counts
    with col2:
        st.metric("Active", active_count)

    with col3:
        st.metric("Terminated", terminated_count)

    with col4:
        st.metric("Retired", retired_count)

    with col5:
        # Voluntary vs Involuntary
        if "termination_reason" in employees_df.columns:
            termed_df = employees_df[employees_df["employment_status"].isin(["Terminated", "Retired"])]
            if len(termed_df) > 0:
                voluntary_reasons = [
                    "Resignation - Career Opportunity",
                    "Resignation - Personal Reasons",
                    "Resignation - Relocation",
                    "Retirement",
                ]
                voluntary = termed_df["termination_reason"].isin(voluntary_reasons).sum()
                involuntary = len(termed_df) - voluntary
                voluntary_pct = voluntary / len(termed_df) * 100
                st.metric("Voluntary", f"{voluntary_pct:.0f}%", delta=f"{involuntary} involuntary")
            else:
                st.metric("Voluntary", "N/A")
        else:
            st.metric("Voluntary", "N/A")


def render_termination_reasons(employees_df: pd.DataFrame) -> None:
    """Render termination reasons pie chart."""
    if "termination_reason" not in employees_df.columns:
        st.info("Termination reason data not available")
        return

    # Filter to only terminated/retired employees
    termed_df = employees_df[
        employees_df["employment_status"].isin(["Terminated", "Retired"])
    ].copy()

    if len(termed_df) == 0:
        st.info("No terminations to display")
        return

    reason_counts = (
        termed_df.groupby("termination_reason")
        .size()
        .reset_index(name="count")
    )

    fig = create_pie_chart(
        reason_counts,
        values="count",
        names="termination_reason",
        title="Termination Reasons",
        color_discrete_map=TERMINATION_REASON_COLORS,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_attrition_by_business_unit(enriched_df: pd.DataFrame) -> None:
    """Render attrition rate by business unit bar chart."""
    if "business_unit" not in enriched_df.columns or "employment_status" not in enriched_df.columns:
        st.info("Business unit or status data not available")
        return

    # Calculate attrition rate by business unit
    bu_stats = enriched_df.groupby("business_unit").agg(
        total=("employee_id", "count"),
        attrition=("employment_status", lambda x: (x.isin(["Terminated", "Retired"])).sum())
    ).reset_index()

    bu_stats["attrition_rate"] = bu_stats["attrition"] / bu_stats["total"] * 100

    fig = create_bar_chart(
        bu_stats,
        x="business_unit",
        y="attrition_rate",
        title="Attrition Rate by Business Unit",
        color="business_unit",
        color_discrete_map=BU_COLORS,
    )
    fig.update_layout(
        showlegend=False,
        xaxis_title="Business Unit",
        yaxis_title="Attrition Rate (%)"
    )
    st.plotly_chart(fig, use_container_width=True)


def render_attrition_by_performance(enriched_df: pd.DataFrame, data: dict[str, pd.DataFrame]) -> None:
    """Render attrition rate by performance rating bar chart."""
    if "employee_performance" not in data or "employment_status" not in enriched_df.columns:
        st.info("Performance or status data not available")
        return

    perf_df = data["employee_performance"]

    # Get latest performance rating per employee
    latest_perf = perf_df.sort_values("review_period_year", ascending=False).drop_duplicates(
        "employee_id", keep="first"
    )[["employee_id", "rating"]]

    # Merge with enriched data
    perf_enriched = enriched_df.merge(latest_perf, on="employee_id", how="left")

    # Filter out employees without ratings
    perf_enriched = perf_enriched[perf_enriched["rating"].notna()]

    if len(perf_enriched) == 0:
        st.info("No performance rating data available")
        return

    # Calculate attrition rate by rating
    rating_stats = perf_enriched.groupby("rating").agg(
        total=("employee_id", "count"),
        attrition=("employment_status", lambda x: (x.isin(["Terminated", "Retired"])).sum())
    ).reset_index()

    rating_stats["attrition_rate"] = rating_stats["attrition"] / rating_stats["total"] * 100
    rating_stats["rating"] = rating_stats["rating"].astype(int)

    fig = create_bar_chart(
        rating_stats,
        x="rating",
        y="attrition_rate",
        title="Attrition Rate by Performance Rating",
    )
    fig.update_layout(
        xaxis_title="Performance Rating (1-5)",
        yaxis_title="Attrition Rate (%)"
    )
    st.plotly_chart(fig, use_container_width=True)


def render_attrition_by_tenure(enriched_df: pd.DataFrame) -> None:
    """Render attrition rate by tenure bucket bar chart."""
    if "hire_date" not in enriched_df.columns or "employment_status" not in enriched_df.columns:
        st.info("Hire date or status data not available")
        return

    df = enriched_df.copy()
    today = date.today()

    # Calculate tenure in years
    df["tenure_years"] = df["hire_date"].apply(
        lambda x: (today - x).days / 365.25 if pd.notna(x) else 0
    )

    # Create tenure buckets
    def tenure_bucket(years):
        if years < 1:
            return "<1 year"
        elif years < 2:
            return "1-2 years"
        elif years < 5:
            return "2-5 years"
        elif years < 10:
            return "5-10 years"
        else:
            return "10+ years"

    df["tenure_bucket"] = df["tenure_years"].apply(tenure_bucket)

    # Calculate attrition rate by tenure bucket
    tenure_stats = df.groupby("tenure_bucket").agg(
        total=("employee_id", "count"),
        attrition=("employment_status", lambda x: (x.isin(["Terminated", "Retired"])).sum())
    ).reset_index()

    tenure_stats["attrition_rate"] = tenure_stats["attrition"] / tenure_stats["total"] * 100

    # Order the buckets
    bucket_order = ["<1 year", "1-2 years", "2-5 years", "5-10 years", "10+ years"]
    tenure_stats["tenure_bucket"] = pd.Categorical(
        tenure_stats["tenure_bucket"],
        categories=bucket_order,
        ordered=True
    )
    tenure_stats = tenure_stats.sort_values("tenure_bucket")

    fig = create_bar_chart(
        tenure_stats,
        x="tenure_bucket",
        y="attrition_rate",
        title="Attrition Rate by Tenure",
    )
    fig.update_layout(
        xaxis_title="Tenure",
        yaxis_title="Attrition Rate (%)"
    )
    st.plotly_chart(fig, use_container_width=True)


def render_attrition_by_seniority(enriched_df: pd.DataFrame) -> None:
    """Render attrition rate by seniority level bar chart."""
    if "seniority_level" not in enriched_df.columns or "employment_status" not in enriched_df.columns:
        st.info("Seniority level or status data not available")
        return

    # Filter out rows without seniority level
    df = enriched_df[enriched_df["seniority_level"].notna()].copy()

    if len(df) == 0:
        st.info("No seniority level data available")
        return

    # Calculate attrition rate by seniority
    seniority_stats = df.groupby("seniority_level").agg(
        total=("employee_id", "count"),
        attrition=("employment_status", lambda x: (x.isin(["Terminated", "Retired"])).sum())
    ).reset_index()

    seniority_stats["attrition_rate"] = seniority_stats["attrition"] / seniority_stats["total"] * 100
    seniority_stats["seniority_level"] = seniority_stats["seniority_level"].astype(int)

    # Add labels
    seniority_labels = {
        1: "1-Entry",
        2: "2-Junior",
        3: "3-Mid",
        4: "4-Senior",
        5: "5-Executive",
    }
    seniority_stats["level_label"] = seniority_stats["seniority_level"].map(seniority_labels)

    # Create color mapping for labels
    label_colors = {seniority_labels[k]: v for k, v in SENIORITY_COLORS.items()}

    fig = create_bar_chart(
        seniority_stats,
        x="level_label",
        y="attrition_rate",
        title="Attrition Rate by Seniority Level",
        color="level_label",
        color_discrete_map=label_colors,
    )
    fig.update_layout(
        showlegend=False,
        xaxis_title="Seniority Level",
        yaxis_title="Attrition Rate (%)"
    )
    st.plotly_chart(fig, use_container_width=True)


def render_attrition_timeline(employees_df: pd.DataFrame) -> None:
    """Render attrition timeline by year."""
    if "termination_date" not in employees_df.columns:
        st.info("Termination date data not available")
        return

    # Filter to terminated/retired employees with valid termination dates
    termed_df = employees_df[
        (employees_df["employment_status"].isin(["Terminated", "Retired"])) &
        (employees_df["termination_date"].notna())
    ].copy()

    if len(termed_df) == 0:
        st.info("No termination timeline data available")
        return

    # Extract year from termination date
    termed_df["termination_year"] = pd.to_datetime(termed_df["termination_date"]).dt.year

    # Count by year
    yearly_counts = (
        termed_df.groupby("termination_year")
        .size()
        .reset_index(name="count")
    )

    fig = create_line_chart(
        yearly_counts,
        x="termination_year",
        y="count",
        title="Attrition Timeline",
        markers=True,
    )
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Terminations"
    )
    st.plotly_chart(fig, use_container_width=True)
