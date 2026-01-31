"""Sidebar filter components."""

import streamlit as st
import pandas as pd
from typing import Any


def render_sidebar_filters(data: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """
    Render sidebar filter components.

    Args:
        data: Raw HR data dictionary (unfiltered)

    Returns:
        Dictionary of filter values
    """
    filters = {}

    st.sidebar.header("Generation Settings")

    # Employee count slider (for regeneration)
    filters["n_employees"] = st.sidebar.slider(
        "Employee Count",
        min_value=10,
        max_value=10000,
        value=st.session_state.get("n_employees", 100),
        step=10,
        help="Number of employees to generate",
    )

    # Years of history slider
    filters["years_of_history"] = st.sidebar.slider(
        "Years of History",
        min_value=1,
        max_value=20,
        value=st.session_state.get("years_of_history", 5),
        help="Number of years of historical data to generate",
    )

    # Attrition Settings
    st.sidebar.subheader("Attrition Settings")

    filters["enable_attrition"] = st.sidebar.checkbox(
        "Enable Attrition",
        value=st.session_state.get("enable_attrition", True),
        help="Generate employee termination and attrition data",
    )

    filters["attrition_rate"] = st.sidebar.slider(
        "Attrition Rate (%)",
        min_value=0,
        max_value=30,
        value=st.session_state.get("attrition_rate_pct", 12),
        help="Base annual attrition rate",
    )

    filters["noise_std"] = st.sidebar.slider(
        "ML Difficulty (Noise)",
        min_value=0.0,
        max_value=0.5,
        value=st.session_state.get("noise_std", 0.2),
        step=0.05,
        help="Low=easy ML (~90%), Medium=realistic (~80%), High=hard (~70%)",
    )

    # Regenerate button
    filters["regenerate"] = st.sidebar.button(
        "Regenerate Data",
        help="Generate new random data",
        use_container_width=True,
    )

    st.sidebar.divider()
    st.sidebar.header("View Filters")

    # Business Unit filter
    org_units = data["organization_unit"]
    business_units = sorted(org_units["business_unit"].dropna().unique().tolist())
    filters["business_units"] = st.sidebar.multiselect(
        "Business Unit",
        options=business_units,
        default=business_units,
        help="Filter by business unit",
    )

    # Country filter
    locations = data["location"]
    countries = sorted(locations["country"].dropna().unique().tolist())
    filters["countries"] = st.sidebar.multiselect(
        "Country",
        options=countries,
        default=countries,
        help="Filter by country",
    )

    # Seniority Level filter
    job_roles = data["job_role"]
    seniority_levels = sorted(job_roles["seniority_level"].dropna().unique().tolist())
    seniority_labels = {
        1: "1 - Entry",
        2: "2 - Junior",
        3: "3 - Mid",
        4: "4 - Senior",
        5: "5 - Executive",
    }
    seniority_options = [seniority_labels.get(s, str(s)) for s in seniority_levels]

    selected_seniority = st.sidebar.multiselect(
        "Seniority Level",
        options=seniority_options,
        default=seniority_options,
        help="Filter by seniority level",
    )
    # Convert back to integers
    filters["seniority_levels"] = [
        int(s.split(" - ")[0]) for s in selected_seniority
    ]

    # Salary Range filter (if compensation data exists)
    if "employee_compensation" in data:
        comp_df = data["employee_compensation"]
        min_salary = float(comp_df["base_salary"].min())
        max_salary = float(comp_df["base_salary"].max())

        salary_range = st.sidebar.slider(
            "Salary Range",
            min_value=min_salary,
            max_value=max_salary,
            value=(min_salary, max_salary),
            format="$%.0f",
            help="Filter by salary range",
        )
        filters["salary_range"] = salary_range
    else:
        filters["salary_range"] = None

    return filters


def render_data_summary(data: dict[str, pd.DataFrame]) -> None:
    """
    Render data summary in sidebar.

    Args:
        data: Filtered HR data dictionary
    """
    st.sidebar.divider()
    st.sidebar.subheader("Data Summary")

    employees_df = data["employee"]
    n_employees = len(employees_df)

    st.sidebar.metric("Total Employees", n_employees)

    if "employee_compensation" in data:
        comp_df = data["employee_compensation"]
        # Get current compensation
        current_comp = comp_df.sort_values("start_date", ascending=False).drop_duplicates(
            "employee_id", keep="first"
        )
        avg_salary = current_comp["base_salary"].mean()
        st.sidebar.metric("Avg Salary", f"${avg_salary:,.0f}")

    # Gender distribution
    gender_counts = employees_df["gender"].value_counts()
    gender_str = ", ".join([f"{k}: {v}" for k, v in gender_counts.items()])
    st.sidebar.caption(f"Gender: {gender_str}")


def get_download_data(data: dict[str, pd.DataFrame]) -> dict[str, bytes]:
    """
    Prepare data for CSV download.

    Args:
        data: HR data dictionary

    Returns:
        Dictionary of table names to CSV bytes
    """
    downloads = {}
    for name, df in data.items():
        downloads[name] = df.to_csv(index=False).encode("utf-8")
    return downloads


def render_download_buttons(data: dict[str, pd.DataFrame]) -> None:
    """
    Render download buttons for data export.

    Args:
        data: HR data dictionary
    """
    st.sidebar.divider()
    st.sidebar.subheader("Export Data")

    downloads = get_download_data(data)

    for name, csv_bytes in downloads.items():
        st.sidebar.download_button(
            label=f"Download {name}.csv",
            data=csv_bytes,
            file_name=f"{name}.csv",
            mime="text/csv",
            use_container_width=True,
        )
