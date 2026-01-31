"""Main Streamlit application entry point."""

from datetime import date

import streamlit as st

from hr_dashboard.data_manager import get_hr_data, force_regenerate, get_filtered_data
from hr_dashboard.filters import (
    render_sidebar_filters,
    render_data_summary,
    render_download_buttons,
)
from hr_dashboard.views import overview, compensation, performance, org_chart, org_network, geography, attrition


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="HR Data Dashboard",
        page_icon="👥",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("HR Data Dashboard")

    # Initialize session state for employee count and years of history
    if "n_employees" not in st.session_state:
        st.session_state["n_employees"] = 100
    if "years_of_history" not in st.session_state:
        st.session_state["years_of_history"] = 5

    # Calculate date range from years of history
    end_date = date.today()
    start_date = date(end_date.year - st.session_state["years_of_history"], 1, 1)

    # Initial data generation (needed for filters)
    initial_data = get_hr_data(
        st.session_state["n_employees"],
        start_date=start_date,
        end_date=end_date,
    )

    # Render sidebar filters
    filters = render_sidebar_filters(initial_data)

    # Store settings in session state
    st.session_state["enable_attrition"] = filters["enable_attrition"]
    st.session_state["attrition_rate_pct"] = filters["attrition_rate"]
    st.session_state["noise_std"] = filters["noise_std"]
    st.session_state["years_of_history"] = filters["years_of_history"]

    # Recalculate date range based on filter value
    years = filters["years_of_history"]
    end_date = date.today()
    start_date = date(end_date.year - years, 1, 1)

    # Handle employee count change or regeneration
    if filters["n_employees"] != st.session_state["n_employees"]:
        st.session_state["n_employees"] = filters["n_employees"]
        data = get_hr_data(
            filters["n_employees"],
            include_attrition=filters["enable_attrition"],
            attrition_rate=filters["attrition_rate"] / 100,
            noise_std=filters["noise_std"],
            start_date=start_date,
            end_date=end_date,
        )
    elif filters["regenerate"]:
        data = force_regenerate(
            filters["n_employees"],
            include_attrition=filters["enable_attrition"],
            attrition_rate=filters["attrition_rate"] / 100,
            noise_std=filters["noise_std"],
            start_date=start_date,
            end_date=end_date,
        )
        st.rerun()
    else:
        # Check if settings changed
        current_attrition = st.session_state.get("hr_data_include_attrition")
        current_rate = st.session_state.get("hr_data_attrition_rate")
        current_noise = st.session_state.get("hr_data_noise_std")
        current_start_date = st.session_state.get("hr_data_start_date")
        current_end_date = st.session_state.get("hr_data_end_date")

        if (current_attrition != filters["enable_attrition"] or
            current_rate != filters["attrition_rate"] / 100 or
            current_noise != filters["noise_std"] or
            current_start_date != start_date or
            current_end_date != end_date):
            data = get_hr_data(
                filters["n_employees"],
                include_attrition=filters["enable_attrition"],
                attrition_rate=filters["attrition_rate"] / 100,
                noise_std=filters["noise_std"],
                start_date=start_date,
                end_date=end_date,
            )
        else:
            data = initial_data

    # Apply filters
    filtered_data = get_filtered_data(
        data,
        business_units=filters["business_units"],
        seniority_levels=filters["seniority_levels"],
        salary_range=filters["salary_range"],
        countries=filters["countries"],
    )

    # Render data summary
    render_data_summary(filtered_data)

    # Render download buttons
    render_download_buttons(filtered_data)

    # Main content tabs
    tab_overview, tab_org, tab_compensation, tab_performance, tab_attrition, tab_map = st.tabs([
        "Overview",
        "Organization",
        "Compensation",
        "Performance",
        "Attrition",
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

    with tab_attrition:
        attrition.render(filtered_data)

    with tab_map:
        geography.render(filtered_data)


if __name__ == "__main__":
    main()
