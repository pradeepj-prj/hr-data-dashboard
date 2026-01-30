"""Geographic map page using Plotly."""

import streamlit as st
import pandas as pd
import plotly.express as px

from hr_dashboard.data_manager import enrich_employee_data


def render(data: dict[str, pd.DataFrame]) -> None:
    """
    Render the geography page with interactive map.

    Args:
        data: Filtered HR data dictionary
    """
    employees_df = data["employee"]
    if len(employees_df) == 0:
        st.warning("No employees match the current filters.")
        return

    enriched_df = enrich_employee_data(data)

    st.subheader("Employee Geographic Distribution")

    # Check for location data
    if "latitude" not in enriched_df.columns or "longitude" not in enriched_df.columns:
        st.warning("Geographic location data not available")
        return

    # Filter out rows with missing coordinates
    df = enriched_df.dropna(subset=["latitude", "longitude"]).copy()

    if len(df) == 0:
        st.warning("No employees with valid location data")
        return

    # Render map and summary
    col1, col2 = st.columns([2, 1])

    with col1:
        render_employee_map(df)

    with col2:
        render_location_summary(df)


def render_employee_map(df: pd.DataFrame) -> None:
    """Render the Plotly scatter map."""
    # Aggregate by location for sizing
    agg_dict = {"employee_id": "count"}
    if "base_salary" in df.columns:
        agg_dict["base_salary"] = "mean"

    location_stats = (
        df.groupby(["city", "country", "latitude", "longitude"])
        .agg(**{
            "headcount": ("employee_id", "count"),
            **({" avg_salary": ("base_salary", "mean")} if "base_salary" in df.columns else {}),
        })
        .reset_index()
    )

    # Rename column if it exists
    if " avg_salary" in location_stats.columns:
        location_stats = location_stats.rename(columns={" avg_salary": "avg_salary"})

    # Create hover text
    if "avg_salary" in location_stats.columns:
        location_stats["hover_text"] = location_stats.apply(
            lambda row: f"<b>{row['city']}, {row['country']}</b><br>"
                       f"Headcount: {row['headcount']}<br>"
                       f"Avg Salary: ${row['avg_salary']:,.0f}",
            axis=1,
        )
    else:
        location_stats["hover_text"] = location_stats.apply(
            lambda row: f"<b>{row['city']}, {row['country']}</b><br>"
                       f"Headcount: {row['headcount']}",
            axis=1,
        )

    # Create Plotly scatter mapbox
    fig = px.scatter_mapbox(
        location_stats,
        lat="latitude",
        lon="longitude",
        size="headcount",
        color="headcount",
        hover_name="city",
        hover_data={
            "country": True,
            "headcount": True,
            "latitude": False,
            "longitude": False,
        },
        color_continuous_scale="Blues",
        size_max=30,
        zoom=2,
        center={"lat": location_stats["latitude"].mean(), "lon": location_stats["longitude"].mean()},
    )

    # Use OpenStreetMap tiles (no API key required)
    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=500,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_location_summary(df: pd.DataFrame) -> None:
    """Render location summary statistics."""
    st.markdown("### Location Summary")

    # By country
    st.markdown("**By Country**")
    country_stats = (
        df.groupby("country")
        .agg(
            headcount=("employee_id", "count"),
        )
        .reset_index()
        .sort_values("headcount", ascending=False)
    )
    st.dataframe(country_stats, use_container_width=True, hide_index=True)

    # By city (top 10)
    st.markdown("**Top Cities**")
    city_stats = (
        df.groupby(["city", "country"])
        .agg(
            headcount=("employee_id", "count"),
        )
        .reset_index()
        .sort_values("headcount", ascending=False)
        .head(10)
    )
    st.dataframe(city_stats, use_container_width=True, hide_index=True)

    # Total unique locations
    st.metric("Unique Locations", df["city"].nunique())
    st.metric("Countries Represented", df["country"].nunique())
