"""Sidebar filter components."""

import io
import zipfile
from datetime import date

import streamlit as st
import pandas as pd
from typing import Any

from hr_dashboard.utils.data_health import run_health_checks
from hr_dashboard.utils.export import (
    PARQUET_AVAILABLE,
    create_zip_download,
    get_total_export_size,
    export_to_csv,
    export_to_parquet,
)


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

    # Hiring Settings
    st.sidebar.subheader("Hiring Simulation")

    filters["enable_hiring"] = st.sidebar.checkbox(
        "Enable Hiring",
        value=st.session_state.get("enable_hiring", False),
        help="Generate new hires each year based on growth and backfill needs",
    )

    if filters["enable_hiring"]:
        filters["growth_rate"] = st.sidebar.slider(
            "Growth Rate (%)",
            min_value=0,
            max_value=15,
            value=st.session_state.get("growth_rate_pct", 5),
            help="Base annual workforce growth rate",
        )

        filters["backfill_rate"] = st.sidebar.slider(
            "Backfill Rate (%)",
            min_value=0,
            max_value=100,
            value=st.session_state.get("backfill_rate_pct", 85),
            help="Percentage of departing employees to replace",
        )
    else:
        filters["growth_rate"] = 5
        filters["backfill_rate"] = 85

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


def render_health_panel(
    data: dict[str, pd.DataFrame],
    start_year: int,
    end_year: int,
    include_hiring: bool = False,
) -> None:
    """
    Render data health checks in sidebar.

    Args:
        data: HR data dictionary
        start_year: Simulation start year
        end_year: Simulation end year
        include_hiring: Whether hiring is enabled
    """
    st.sidebar.divider()
    st.sidebar.subheader("Data Health")

    checks = run_health_checks(data, start_year, end_year, include_hiring)

    for check in checks:
        if check.status == "pass":
            st.sidebar.success(f"**{check.name}**: {check.message}")
        elif check.status == "warning":
            with st.sidebar.expander(f"**{check.name}**: {check.message}", expanded=False):
                if check.details:
                    st.caption(check.details)
        else:  # fail
            st.sidebar.error(f"**{check.name}**: {check.message}")


def get_download_data(
    data: dict[str, pd.DataFrame], format: str = "csv"
) -> dict[str, bytes]:
    """
    Prepare data for download.

    Args:
        data: HR data dictionary
        format: Export format ("csv" or "parquet")

    Returns:
        Dictionary of table names to file bytes
    """
    downloads = {}
    export_func = export_to_csv if format == "csv" else export_to_parquet

    for name, df in data.items():
        try:
            downloads[name] = export_func(df)
        except Exception:
            # Fall back to CSV if parquet fails
            downloads[name] = export_to_csv(df)

    return downloads


def render_download_buttons(data: dict[str, pd.DataFrame]) -> None:
    """
    Render download buttons for data export.

    Args:
        data: HR data dictionary
    """
    st.sidebar.divider()
    st.sidebar.subheader("Export Data")

    # Format toggle
    format_options = ["CSV"]
    if PARQUET_AVAILABLE:
        format_options.append("Parquet (Recommended)")

    selected_format = st.sidebar.radio(
        "Export Format",
        options=format_options,
        index=1 if PARQUET_AVAILABLE else 0,
        help="Parquet is smaller and faster for HANA Cloud import",
        horizontal=True,
    )

    export_format = "parquet" if "Parquet" in selected_format else "csv"

    # Show size comparison
    csv_size = get_total_export_size(data, "csv")
    if PARQUET_AVAILABLE and export_format == "parquet":
        parquet_size = get_total_export_size(data, "parquet")
        savings = ((csv_size - parquet_size) / csv_size) * 100 if csv_size > 0 else 0
        st.sidebar.caption(
            f"Parquet: {parquet_size:.1f} MB vs CSV: {csv_size:.1f} MB ({savings:.0f}% smaller)"
        )
    else:
        st.sidebar.caption(f"Total size: {csv_size:.1f} MB")

    # Download All button
    extension = "csv" if export_format == "csv" else "parquet"
    zip_data = create_zip_download(data, export_format)

    st.sidebar.download_button(
        label=f"Download All ({extension.upper()})",
        data=zip_data,
        file_name=f"hr_data_{extension}.zip",
        mime="application/zip",
        use_container_width=True,
        type="primary",
    )

    # Individual table downloads (collapsed)
    with st.sidebar.expander("Individual Tables"):
        downloads = get_download_data(data, export_format)
        mime_type = "text/csv" if export_format == "csv" else "application/octet-stream"

        for name, file_bytes in downloads.items():
            st.download_button(
                label=f"{name}.{extension}",
                data=file_bytes,
                file_name=f"{name}.{extension}",
                mime=mime_type,
                use_container_width=True,
            )
