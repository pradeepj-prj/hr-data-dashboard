"""Main Streamlit application entry point."""

import streamlit as st

from hr_dashboard.data_manager import get_hr_data, force_regenerate, get_filtered_data
from hr_dashboard.filters import (
    render_sidebar_filters,
    render_data_summary,
    render_download_buttons,
)
from hr_dashboard.views import overview, compensation, performance, org_chart, org_network, geography


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="HR Data Dashboard",
        page_icon="👥",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("HR Data Dashboard")

    # Initialize session state for employee count
    if "n_employees" not in st.session_state:
        st.session_state["n_employees"] = 100

    # Initial data generation (needed for filters)
    initial_data = get_hr_data(st.session_state["n_employees"])

    # Render sidebar filters
    filters = render_sidebar_filters(initial_data)

    # Handle employee count change or regeneration
    if filters["n_employees"] != st.session_state["n_employees"]:
        st.session_state["n_employees"] = filters["n_employees"]
        data = get_hr_data(filters["n_employees"])
    elif filters["regenerate"]:
        data = force_regenerate(filters["n_employees"])
        st.rerun()
    else:
        data = initial_data

    # Apply filters
    filtered_data = get_filtered_data(
        data,
        business_units=filters["business_units"],
        seniority_levels=filters["seniority_levels"],
        salary_range=filters["salary_range"],
    )

    # Render data summary
    render_data_summary(filtered_data)

    # Render download buttons
    render_download_buttons(filtered_data)

    # Main content tabs
    tab_overview, tab_org, tab_compensation, tab_performance, tab_map = st.tabs([
        "Overview",
        "Organization",
        "Compensation",
        "Performance",
        "Map",
    ])

    with tab_overview:
        overview.render(filtered_data)

    with tab_org:
        org_subtab1, org_subtab2 = st.tabs(["Tree View", "Network View"])
        with org_subtab1:
            org_chart.render(filtered_data)
        with org_subtab2:
            org_network.render(filtered_data)

    with tab_compensation:
        compensation.render(filtered_data)

    with tab_performance:
        performance.render(filtered_data)

    with tab_map:
        geography.render(filtered_data)


if __name__ == "__main__":
    main()
