"""Main Streamlit application entry point."""

from datetime import date

import streamlit as st

from hr_dashboard.data_manager import get_hr_data, force_regenerate, get_filtered_data
from hr_dashboard.filters import (
    render_sidebar_filters,
    render_data_summary,
    render_download_buttons,
    render_health_panel,
)
from hr_dashboard.views import overview, compensation, performance, org_chart, org_network, geography, attrition, data_tables


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="HR Data Dashboard",
        page_icon="👥",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("HR Data Dashboard")

    # Initialize session state with defaults for pending settings
    # These are the settings shown in the UI, not necessarily what data was generated with
    if "n_employees" not in st.session_state:
        st.session_state["n_employees"] = 100
    if "years_of_history" not in st.session_state:
        st.session_state["years_of_history"] = 5
    if "enable_attrition" not in st.session_state:
        st.session_state["enable_attrition"] = True
    if "attrition_rate_pct" not in st.session_state:
        st.session_state["attrition_rate_pct"] = 12
    if "noise_std" not in st.session_state:
        st.session_state["noise_std"] = 0.2
    if "enable_hiring" not in st.session_state:
        st.session_state["enable_hiring"] = False
    if "growth_rate_pct" not in st.session_state:
        st.session_state["growth_rate_pct"] = 5
    if "backfill_rate_pct" not in st.session_state:
        st.session_state["backfill_rate_pct"] = 85

    # Generate initial data if not cached (first load only)
    # Uses current session state values as defaults
    if "hr_data" not in st.session_state:
        end_date = date.today()
        start_date = date(end_date.year - st.session_state["years_of_history"], 1, 1)
        data = get_hr_data(
            st.session_state["n_employees"],
            include_attrition=st.session_state["enable_attrition"],
            attrition_rate=st.session_state["attrition_rate_pct"] / 100,
            noise_std=st.session_state["noise_std"],
            start_date=start_date,
            end_date=end_date,
            include_hiring=st.session_state["enable_hiring"],
            base_growth_rate=st.session_state["growth_rate_pct"] / 100,
            backfill_rate=st.session_state["backfill_rate_pct"] / 100,
        )
    else:
        data = st.session_state["hr_data"]

    # Render sidebar filters (uses cached data for filter options)
    filters = render_sidebar_filters(data)

    # Update pending settings in session state (but don't regenerate yet)
    st.session_state["n_employees"] = filters["n_employees"]
    st.session_state["enable_attrition"] = filters["enable_attrition"]
    st.session_state["attrition_rate_pct"] = filters["attrition_rate"]
    st.session_state["noise_std"] = filters["noise_std"]
    st.session_state["years_of_history"] = filters["years_of_history"]
    st.session_state["enable_hiring"] = filters["enable_hiring"]
    st.session_state["growth_rate_pct"] = filters["growth_rate"]
    st.session_state["backfill_rate_pct"] = filters["backfill_rate"]

    # Only regenerate when user explicitly clicks "Regenerate Data" button
    if filters["regenerate"]:
        years = filters["years_of_history"]
        end_date = date.today()
        start_date = date(end_date.year - years, 1, 1)
        data = force_regenerate(
            filters["n_employees"],
            include_attrition=filters["enable_attrition"],
            attrition_rate=filters["attrition_rate"] / 100,
            noise_std=filters["noise_std"],
            start_date=start_date,
            end_date=end_date,
            include_hiring=filters["enable_hiring"],
            base_growth_rate=filters["growth_rate"] / 100,
            backfill_rate=filters["backfill_rate"] / 100,
        )
        st.rerun()

    # Get the actual generation parameters from the cached data
    # (stored in session state by data_manager when data was generated)
    start_date = st.session_state.get("hr_data_start_date", date.today().replace(month=1, day=1))
    end_date = st.session_state.get("hr_data_end_date", date.today())
    data_include_hiring = st.session_state.get("hr_data_include_hiring", False)

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

    # Render health panel (uses actual data generation params, not pending settings)
    render_health_panel(
        filtered_data,
        start_year=start_date.year,
        end_year=end_date.year,
        include_hiring=data_include_hiring,
    )

    # Render download buttons
    render_download_buttons(filtered_data)

    # Main content tabs (tab label reflects actual data, not pending settings)
    tab_overview, tab_org, tab_compensation, tab_performance, tab_attrition, tab_map, tab_data = st.tabs([
        "Overview",
        "Organization",
        "Compensation",
        "Performance",
        "Workforce Dynamics" if data_include_hiring else "Attrition",
        "Map",
        "📋 Data Tables",
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
        attrition.render(
            filtered_data,
            include_hiring=data_include_hiring,
            start_year=start_date.year,
            end_year=end_date.year,
        )

    with tab_map:
        geography.render(filtered_data)

    with tab_data:
        data_tables.render(filtered_data)


if __name__ == "__main__":
    main()
