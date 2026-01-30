"""Performance analytics page."""

import streamlit as st
import pandas as pd
import plotly.express as px

from hr_dashboard.data_manager import enrich_employee_data
from hr_dashboard.utils.chart_helpers import (
    BU_COLORS,
    create_bar_chart,
    create_line_chart,
    create_heatmap,
)


def render(data: dict[str, pd.DataFrame]) -> None:
    """
    Render the performance page.

    Args:
        data: Filtered HR data dictionary
    """
    if "employee_performance" not in data:
        st.warning("Performance data not available.")
        return

    employees_df = data["employee"]
    if len(employees_df) == 0:
        st.warning("No employees match the current filters.")
        return

    perf_df = data["employee_performance"].copy()
    enriched_df = enrich_employee_data(data)

    # Merge with employee data for business unit info
    perf_enriched = perf_df.merge(
        enriched_df[["employee_id", "business_unit", "seniority_level"]],
        on="employee_id",
        how="left",
    )

    # Summary metrics
    render_performance_kpis(perf_df)

    st.divider()

    # Charts row 1
    col1, col2 = st.columns(2)

    with col1:
        render_rating_distribution(perf_df)

    with col2:
        render_rating_trend(perf_df)

    # Charts row 2
    col3, col4 = st.columns(2)

    with col3:
        render_ratings_by_year_stacked(perf_df)

    with col4:
        render_bu_year_heatmap(perf_enriched)


def render_performance_kpis(perf_df: pd.DataFrame) -> None:
    """Render performance KPI metrics."""
    col1, col2, col3, col4 = st.columns(4)

    ratings = perf_df["rating"]

    with col1:
        st.metric("Avg Rating", f"{ratings.mean():.2f}")

    with col2:
        st.metric("Total Reviews", f"{len(perf_df):,}")

    with col3:
        high_performers = (ratings >= 4).sum()
        high_pct = high_performers / len(perf_df) * 100
        st.metric("High Performers (4+)", f"{high_pct:.1f}%")

    with col4:
        low_performers = (ratings <= 2).sum()
        low_pct = low_performers / len(perf_df) * 100
        st.metric("Needs Improvement (≤2)", f"{low_pct:.1f}%")


def render_rating_distribution(perf_df: pd.DataFrame) -> None:
    """Render rating distribution bar chart."""
    rating_counts = (
        perf_df.groupby("rating")
        .size()
        .reset_index(name="count")
    )

    # Define rating colors (red to green scale)
    rating_colors = {
        1: "#d62728",  # Red
        2: "#ff7f0e",  # Orange
        3: "#ffbb78",  # Light orange
        4: "#98df8a",  # Light green
        5: "#2ca02c",  # Green
    }

    fig = create_bar_chart(
        rating_counts,
        x="rating",
        y="count",
        title="Rating Distribution (1-5 Scale)",
        color="rating",
        color_discrete_map=rating_colors,
    )
    fig.update_layout(showlegend=False, xaxis_title="Rating", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True)


def render_rating_trend(perf_df: pd.DataFrame) -> None:
    """Render average rating trend over years."""
    if "review_year" not in perf_df.columns:
        st.info("Review year data not available")
        return

    yearly_avg = (
        perf_df.groupby("review_year")["rating"]
        .mean()
        .reset_index()
    )

    fig = create_line_chart(
        yearly_avg,
        x="review_year",
        y="rating",
        title="Average Rating Trend by Year",
    )
    fig.update_layout(xaxis_title="Year", yaxis_title="Average Rating")
    fig.update_yaxes(range=[1, 5])
    st.plotly_chart(fig, use_container_width=True)


def render_ratings_by_year_stacked(perf_df: pd.DataFrame) -> None:
    """Render stacked bar chart of ratings by year."""
    if "review_year" not in perf_df.columns:
        st.info("Review year data not available")
        return

    # Count ratings by year
    rating_by_year = (
        perf_df.groupby(["review_year", "rating"])
        .size()
        .reset_index(name="count")
    )

    # Define rating colors
    rating_colors = {
        1: "#d62728",
        2: "#ff7f0e",
        3: "#ffbb78",
        4: "#98df8a",
        5: "#2ca02c",
    }

    fig = px.bar(
        rating_by_year,
        x="review_year",
        y="count",
        color="rating",
        title="Rating Distribution by Year",
        color_discrete_map=rating_colors,
        barmode="stack",
    )
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Count",
        legend_title="Rating",
        plot_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_bu_year_heatmap(perf_enriched: pd.DataFrame) -> None:
    """Render heatmap of average rating by business unit and year."""
    if "review_year" not in perf_enriched.columns or "business_unit" not in perf_enriched.columns:
        st.info("Business unit or review year data not available")
        return

    # Filter out null business units
    df = perf_enriched.dropna(subset=["business_unit"])

    if len(df) == 0:
        st.info("No data available for heatmap")
        return

    fig = create_heatmap(
        df,
        x="review_year",
        y="business_unit",
        z="rating",
        title="Avg Rating: Business Unit × Year",
        color_scale="RdYlGn",
    )
    fig.update_layout(xaxis_title="Year", yaxis_title="Business Unit")
    st.plotly_chart(fig, use_container_width=True)
