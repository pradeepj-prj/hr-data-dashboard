"""Geographic map page using Pydeck."""

import streamlit as st
import pandas as pd
import pydeck as pdk

from hr_dashboard.data_manager import enrich_employee_data
from hr_dashboard.utils.chart_helpers import BU_COLORS


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
    """Render the Pydeck scatter map."""
    # Aggregate by location for sizing
    location_stats = (
        df.groupby(["city", "country", "latitude", "longitude"])
        .agg(
            headcount=("employee_id", "count"),
            avg_salary=("annual_salary", "mean") if "annual_salary" in df.columns else ("employee_id", "count"),
        )
        .reset_index()
    )

    # Normalize headcount for radius scaling
    max_count = location_stats["headcount"].max()
    min_radius = 5000
    max_radius = 50000
    location_stats["radius"] = (
        location_stats["headcount"] / max_count * (max_radius - min_radius) + min_radius
    )

    # Create tooltip text
    if "avg_salary" in location_stats.columns:
        location_stats["tooltip_text"] = location_stats.apply(
            lambda row: f"{row['city']}, {row['country']}\nHeadcount: {row['headcount']}\nAvg Salary: ${row['avg_salary']:,.0f}",
            axis=1,
        )
    else:
        location_stats["tooltip_text"] = location_stats.apply(
            lambda row: f"{row['city']}, {row['country']}\nHeadcount: {row['headcount']}",
            axis=1,
        )

    # Calculate center point
    center_lat = location_stats["latitude"].mean()
    center_lon = location_stats["longitude"].mean()

    # Create Pydeck layer
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=location_stats,
        get_position=["longitude", "latitude"],
        get_radius="radius",
        get_fill_color=[31, 119, 180, 180],  # Blue with alpha
        pickable=True,
        auto_highlight=True,
    )

    # Create text layer for city labels
    text_layer = pdk.Layer(
        "TextLayer",
        data=location_stats,
        get_position=["longitude", "latitude"],
        get_text="city",
        get_size=12,
        get_color=[0, 0, 0, 200],
        get_angle=0,
        get_alignment_baseline="'bottom'",
    )

    # Create view state
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=3,
        pitch=0,
    )

    # Create tooltip
    tooltip = {
        "html": "<b>{tooltip_text}</b>",
        "style": {
            "backgroundColor": "steelblue",
            "color": "white",
            "padding": "10px",
            "borderRadius": "5px",
        },
    }

    # Create deck
    deck = pdk.Deck(
        layers=[scatter_layer, text_layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/light-v10",
    )

    st.pydeck_chart(deck, use_container_width=True)


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
