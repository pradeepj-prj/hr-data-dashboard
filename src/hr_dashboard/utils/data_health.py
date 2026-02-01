"""Data health validation checks for HR data quality."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd


@dataclass
class HealthCheck:
    """Result of a single health check."""

    name: str
    status: Literal["pass", "warning", "fail"]
    message: str
    details: str | None = None


def run_health_checks(
    data: dict[str, pd.DataFrame],
    start_year: int,
    end_year: int,
    include_hiring: bool = False,
) -> list[HealthCheck]:
    """
    Run all data health checks.

    Args:
        data: HR data dictionary
        start_year: Simulation start year
        end_year: Simulation end year
        include_hiring: Whether hiring is enabled

    Returns:
        List of HealthCheck results
    """
    checks = []

    employees_df = data.get("employee", pd.DataFrame())

    if employees_df.empty:
        return [HealthCheck("Data Available", "fail", "No employee data found")]

    # Run all checks
    checks.append(check_headcount_trend(employees_df, start_year, end_year))
    checks.append(check_attrition_rate(employees_df, start_year, end_year))
    checks.append(check_bu_distribution(data))
    checks.append(check_seniority_pyramid(data))
    checks.append(check_tenure_mix(employees_df))

    if include_hiring:
        checks.append(check_new_hire_seniority(data, start_year, end_year))

    return checks


def check_headcount_trend(
    employees_df: pd.DataFrame, start_year: int, end_year: int
) -> HealthCheck:
    """Check that headcount never goes negative."""
    name = "Headcount Trend"

    for year in range(start_year, end_year + 1):
        year_end = date(year, 12, 31)

        headcount = employees_df[
            (pd.to_datetime(employees_df["hire_date"]) <= pd.Timestamp(year_end))
            & (
                (employees_df.get("termination_date") is None)
                | (employees_df["termination_date"].isna())
                | (pd.to_datetime(employees_df["termination_date"]) > pd.Timestamp(year_end))
            )
        ].shape[0]

        if headcount < 0:
            return HealthCheck(
                name, "fail", f"Negative headcount in {year}",
                f"Headcount: {headcount}"
            )

        if headcount == 0:
            return HealthCheck(
                name, "warning", f"Zero headcount in {year}",
                "All employees terminated before this date"
            )

    return HealthCheck(name, "pass", "Headcount positive throughout")


def check_attrition_rate(
    employees_df: pd.DataFrame, start_year: int, end_year: int
) -> HealthCheck:
    """Check that annual attrition rate is between 5-30%."""
    name = "Attrition Rate"

    if "termination_date" not in employees_df.columns:
        return HealthCheck(name, "pass", "No attrition data (disabled)")

    rates = []
    for year in range(start_year, end_year + 1):
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)

        # Employees active at start of year
        active_start = employees_df[
            (pd.to_datetime(employees_df["hire_date"]) < pd.Timestamp(year_start))
            & (
                (employees_df["termination_date"].isna())
                | (pd.to_datetime(employees_df["termination_date"]) >= pd.Timestamp(year_start))
            )
        ].shape[0]

        if active_start == 0:
            continue

        # Terminations during the year
        terminations = employees_df[
            (employees_df["termination_date"].notna())
            & (pd.to_datetime(employees_df["termination_date"]).dt.year == year)
        ].shape[0]

        rate = terminations / active_start
        rates.append((year, rate))

    if not rates:
        return HealthCheck(name, "pass", "No attrition data available")

    # Check for extreme rates
    high_years = [(y, r) for y, r in rates if r > 0.30]
    low_years = [(y, r) for y, r in rates if r < 0.05 and r > 0]

    if high_years:
        return HealthCheck(
            name, "warning",
            f"High attrition in {len(high_years)} year(s)",
            f"Years with >30%: {[y for y, _ in high_years]}"
        )

    if low_years:
        return HealthCheck(
            name, "warning",
            f"Low attrition in {len(low_years)} year(s)",
            f"Years with <5%: {[y for y, _ in low_years]}"
        )

    avg_rate = sum(r for _, r in rates) / len(rates)
    return HealthCheck(name, "pass", f"Avg rate: {avg_rate:.1%}")


def check_bu_distribution(data: dict[str, pd.DataFrame]) -> HealthCheck:
    """Check that all business units have >5% representation."""
    name = "BU Distribution"

    org_assignments = data.get("employee_org_assignment", pd.DataFrame())

    if org_assignments.empty:
        return HealthCheck(name, "warning", "Org data not available")

    # Get current org assignments (business_unit is already in org_assignments)
    current_orgs = org_assignments.sort_values("start_date", ascending=False).drop_duplicates(
        "employee_id", keep="first"
    )

    # Check if business_unit column exists
    if "business_unit" not in current_orgs.columns:
        # Try to merge with org_units if business_unit not in assignments
        org_units = data.get("organization_unit", pd.DataFrame())
        if org_units.empty or "org_id" not in current_orgs.columns:
            return HealthCheck(name, "warning", "Business unit data not available")
        current_orgs = current_orgs.merge(
            org_units[["org_id", "business_unit"]], on="org_id", how="left"
        )

    # Calculate distribution
    total = len(current_orgs)
    if total == 0:
        return HealthCheck(name, "warning", "No org assignments found")

    bu_counts = current_orgs["business_unit"].value_counts()
    bu_pcts = bu_counts / total

    low_bus = bu_pcts[bu_pcts < 0.05].index.tolist()

    if low_bus:
        return HealthCheck(
            name, "warning",
            f"{len(low_bus)} BU(s) below 5%",
            f"Low BUs: {low_bus}"
        )

    return HealthCheck(name, "pass", f"{len(bu_counts)} BUs well distributed")


def check_seniority_pyramid(data: dict[str, pd.DataFrame]) -> HealthCheck:
    """Check seniority follows pyramid structure (more junior than senior)."""
    name = "Seniority Pyramid"

    job_assignments = data.get("employee_job_assignment", pd.DataFrame())
    job_roles = data.get("job_role", pd.DataFrame())

    if job_assignments.empty or job_roles.empty:
        return HealthCheck(name, "warning", "Job data not available")

    # Get current job assignments
    current_jobs = job_assignments.sort_values("start_date", ascending=False).drop_duplicates(
        "employee_id", keep="first"
    )

    # Get seniority levels
    if "seniority_level" not in current_jobs.columns:
        current_jobs = current_jobs.merge(
            job_roles[["job_id", "seniority_level"]], on="job_id", how="left"
        )

    seniority_counts = current_jobs["seniority_level"].value_counts().sort_index()

    # Check pyramid: L1-L2 should be more than L4-L5
    junior = seniority_counts.get(1, 0) + seniority_counts.get(2, 0)
    senior = seniority_counts.get(4, 0) + seniority_counts.get(5, 0)

    if junior < senior:
        return HealthCheck(
            name, "warning",
            "Inverted pyramid",
            f"Junior (L1-L2): {junior}, Senior (L4-L5): {senior}"
        )

    return HealthCheck(name, "pass", f"Junior: {junior}, Senior: {senior}")


def check_tenure_mix(employees_df: pd.DataFrame) -> HealthCheck:
    """Check for healthy tenure mix (both new and tenured employees)."""
    name = "Tenure Mix"

    if employees_df.empty:
        return HealthCheck(name, "warning", "No employees")

    today = date.today()
    employees_df = employees_df.copy()

    # Calculate tenure
    employees_df["tenure_years"] = employees_df["hire_date"].apply(
        lambda x: (today - x).days / 365.25 if pd.notna(x) else 0
    )

    new_hires = (employees_df["tenure_years"] < 2).sum()
    tenured = (employees_df["tenure_years"] > 5).sum()
    total = len(employees_df)

    if new_hires == 0:
        return HealthCheck(
            name, "warning",
            "No recent hires (<2 years)",
            "Consider enabling hiring simulation"
        )

    if tenured == 0:
        return HealthCheck(
            name, "warning",
            "No tenured employees (>5 years)",
            "Consider increasing years of history"
        )

    new_pct = new_hires / total * 100
    tenured_pct = tenured / total * 100

    return HealthCheck(
        name, "pass",
        f"New: {new_pct:.0f}%, Tenured: {tenured_pct:.0f}%"
    )


def check_new_hire_seniority(
    data: dict[str, pd.DataFrame], start_year: int, end_year: int
) -> HealthCheck:
    """Check that >50% of new hires are L1-L2 (junior)."""
    name = "New Hire Seniority"

    employees_df = data.get("employee", pd.DataFrame())
    job_assignments = data.get("employee_job_assignment", pd.DataFrame())
    job_roles = data.get("job_role", pd.DataFrame())

    if employees_df.empty or job_assignments.empty:
        return HealthCheck(name, "warning", "Data not available")

    # Find employees hired during simulation
    new_hires = employees_df[
        pd.to_datetime(employees_df["hire_date"]).dt.year >= start_year
    ]

    if new_hires.empty:
        return HealthCheck(name, "pass", "No new hires to check")

    # Get their first job assignments
    new_hire_jobs = job_assignments[
        job_assignments["employee_id"].isin(new_hires["employee_id"])
    ].sort_values("start_date").drop_duplicates("employee_id", keep="first")

    if new_hire_jobs.empty:
        return HealthCheck(name, "warning", "No job data for new hires")

    # Get seniority levels
    if "seniority_level" not in new_hire_jobs.columns:
        new_hire_jobs = new_hire_jobs.merge(
            job_roles[["job_id", "seniority_level"]], on="job_id", how="left"
        )

    total = len(new_hire_jobs)
    junior = new_hire_jobs["seniority_level"].isin([1, 2]).sum()
    junior_pct = junior / total * 100 if total > 0 else 0

    if junior_pct < 50:
        return HealthCheck(
            name, "warning",
            f"Only {junior_pct:.0f}% junior hires",
            "Expected >50% to be L1-L2"
        )

    return HealthCheck(name, "pass", f"{junior_pct:.0f}% junior hires (L1-L2)")
