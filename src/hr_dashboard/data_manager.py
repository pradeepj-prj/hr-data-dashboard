"""Data generation and caching manager."""

import streamlit as st
import pandas as pd
from hr_data_generator import generate_hr_data


def get_hr_data(n_employees: int, seed: int | None = None) -> dict[str, pd.DataFrame]:
    """
    Generate or retrieve cached HR data.

    Uses Streamlit session state to cache generated data.
    Data is only regenerated when n_employees changes or explicitly requested.

    Args:
        n_employees: Number of employees to generate
        seed: Random seed for reproducibility

    Returns:
        Dictionary of DataFrames from hr_data_generator
    """
    cache_key = "hr_data"
    count_key = "hr_data_n_employees"
    seed_key = "hr_data_seed"

    # Check if we need to regenerate
    needs_regeneration = (
        cache_key not in st.session_state
        or st.session_state.get(count_key) != n_employees
        or st.session_state.get(seed_key) != seed
    )

    if needs_regeneration:
        with st.spinner(f"Generating data for {n_employees} employees..."):
            data = generate_hr_data(n_employees=n_employees, seed=seed)
            st.session_state[cache_key] = data
            st.session_state[count_key] = n_employees
            st.session_state[seed_key] = seed

    return st.session_state[cache_key]


def force_regenerate(n_employees: int, seed: int | None = None) -> dict[str, pd.DataFrame]:
    """
    Force regeneration of HR data with a new seed.

    Args:
        n_employees: Number of employees to generate
        seed: Random seed (if None, generates random data)

    Returns:
        Dictionary of DataFrames from hr_data_generator
    """
    # Clear cache to force regeneration
    if "hr_data" in st.session_state:
        del st.session_state["hr_data"]
    if "hr_data_n_employees" in st.session_state:
        del st.session_state["hr_data_n_employees"]
    if "hr_data_seed" in st.session_state:
        del st.session_state["hr_data_seed"]

    return get_hr_data(n_employees, seed)


def get_filtered_data(
    data: dict[str, pd.DataFrame],
    business_units: list[str] | None = None,
    seniority_levels: list[int] | None = None,
    date_range: tuple[pd.Timestamp, pd.Timestamp] | None = None,
    salary_range: tuple[float, float] | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Apply filters to HR data.

    Args:
        data: Raw HR data dictionary
        business_units: Filter by business units (e.g., ["Engineering", "Sales"])
        seniority_levels: Filter by seniority levels (1-5)
        date_range: Filter by date range (start, end)
        salary_range: Filter by salary range (min, max)

    Returns:
        Filtered dictionary of DataFrames
    """
    result = {}

    # Get employee IDs that pass all filters
    employees_df = data["employee"].copy()
    job_assignments = data["employee_job_assignment"].copy()
    org_assignments = data["employee_org_assignment"].copy()
    job_roles = data["job_role"]
    org_units = data["organization_unit"]

    # Get current job assignments (most recent)
    current_jobs = job_assignments.sort_values("start_date", ascending=False).drop_duplicates(
        "employee_id", keep="first"
    )

    # Get current org assignments (most recent)
    current_orgs = org_assignments.sort_values("start_date", ascending=False).drop_duplicates(
        "employee_id", keep="first"
    )

    # Merge for filtering
    employees_enriched = employees_df.merge(
        current_jobs[["employee_id", "job_id"]], on="employee_id", how="left"
    )
    employees_enriched = employees_enriched.merge(
        job_roles[["job_id", "seniority_level"]], on="job_id", how="left"
    )
    employees_enriched = employees_enriched.merge(
        current_orgs[["employee_id", "org_id"]], on="employee_id", how="left"
    )
    employees_enriched = employees_enriched.merge(
        org_units[["org_id", "business_unit"]], on="org_id", how="left"
    )

    # Apply filters
    mask = pd.Series([True] * len(employees_enriched), index=employees_enriched.index)

    if business_units:
        mask &= employees_enriched["business_unit"].isin(business_units)

    if seniority_levels:
        mask &= employees_enriched["seniority_level"].isin(seniority_levels)

    # Filter for salary range using compensation data
    if salary_range and "employee_compensation" in data:
        comp_df = data["employee_compensation"].copy()
        current_comp = comp_df.sort_values("effective_date", ascending=False).drop_duplicates(
            "employee_id", keep="first"
        )
        salary_mask = (current_comp["annual_salary"] >= salary_range[0]) & (
            current_comp["annual_salary"] <= salary_range[1]
        )
        valid_emp_ids = current_comp.loc[salary_mask, "employee_id"]
        mask &= employees_enriched["employee_id"].isin(valid_emp_ids)

    # Get filtered employee IDs
    filtered_emp_ids = employees_enriched.loc[mask, "employee_id"]

    # Filter all tables
    result["employee"] = employees_df[employees_df["employee_id"].isin(filtered_emp_ids)]
    result["employee_job_assignment"] = job_assignments[
        job_assignments["employee_id"].isin(filtered_emp_ids)
    ]
    result["employee_org_assignment"] = org_assignments[
        org_assignments["employee_id"].isin(filtered_emp_ids)
    ]

    if "employee_compensation" in data:
        result["employee_compensation"] = data["employee_compensation"][
            data["employee_compensation"]["employee_id"].isin(filtered_emp_ids)
        ]

    if "employee_performance" in data:
        result["employee_performance"] = data["employee_performance"][
            data["employee_performance"]["employee_id"].isin(filtered_emp_ids)
        ]

    # Reference tables stay unfiltered
    result["organization_unit"] = data["organization_unit"]
    result["job_role"] = data["job_role"]
    result["location"] = data["location"]

    return result


def enrich_employee_data(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Create enriched employee DataFrame with current job, org, and compensation info.

    Args:
        data: HR data dictionary

    Returns:
        Enriched employee DataFrame
    """
    employees_df = data["employee"].copy()
    job_assignments = data["employee_job_assignment"]
    org_assignments = data["employee_org_assignment"]
    job_roles = data["job_role"]
    org_units = data["organization_unit"]
    locations = data["location"]

    # Get current assignments
    current_jobs = job_assignments.sort_values("start_date", ascending=False).drop_duplicates(
        "employee_id", keep="first"
    )
    current_orgs = org_assignments.sort_values("start_date", ascending=False).drop_duplicates(
        "employee_id", keep="first"
    )

    # Merge job info
    employees_df = employees_df.merge(
        current_jobs[["employee_id", "job_id"]], on="employee_id", how="left"
    )
    employees_df = employees_df.merge(
        job_roles[["job_id", "job_title", "job_family", "job_level", "seniority_level"]],
        on="job_id",
        how="left",
    )

    # Merge org info
    employees_df = employees_df.merge(
        current_orgs[["employee_id", "org_id"]], on="employee_id", how="left"
    )
    employees_df = employees_df.merge(
        org_units[["org_id", "org_name", "business_unit"]], on="org_id", how="left"
    )

    # Merge location info
    employees_df = employees_df.merge(
        locations[["location_id", "city", "country", "region", "latitude", "longitude"]],
        on="location_id",
        how="left",
    )

    # Add compensation if available
    if "employee_compensation" in data:
        comp_df = data["employee_compensation"]
        current_comp = comp_df.sort_values("effective_date", ascending=False).drop_duplicates(
            "employee_id", keep="first"
        )
        employees_df = employees_df.merge(
            current_comp[["employee_id", "annual_salary", "currency"]],
            on="employee_id",
            how="left",
        )

    return employees_df
