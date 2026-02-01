"""Attrition and Workforce Dynamics page with turnover analysis and visualizations."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

from hr_dashboard.data_manager import enrich_employee_data
from hr_dashboard.utils.chart_helpers import (
    BU_COLORS,
    SENIORITY_COLORS,
    ATTRITION_COLORS,
    TERMINATION_REASON_COLORS,
    COLORS,
    create_bar_chart,
    create_pie_chart,
    create_line_chart,
    CHART_BGCOLOR,
    CHART_PAPER_BGCOLOR,
    CHART_FONT_COLOR,
)


def render(
    data: dict[str, pd.DataFrame],
    include_hiring: bool = False,
    start_year: int | None = None,
    end_year: int | None = None,
) -> None:
    """
    Render the attrition/workforce dynamics page.

    Args:
        data: Filtered HR data dictionary
        include_hiring: Whether hiring simulation is enabled
        start_year: Start year of simulation
        end_year: End year of simulation
    """
    employees_df = data["employee"]

    if len(employees_df) == 0:
        st.warning("No employees match the current filters.")
        return

    # Check if attrition data exists
    if "employment_status" not in employees_df.columns:
        st.info("Attrition data is not available. Enable attrition in the sidebar settings.")
        return

    enriched_df = enrich_employee_data(data)

    # Check if there are any terminated/retired employees
    status_counts = employees_df["employment_status"].value_counts()
    has_attrition = any(
        status in status_counts.index for status in ["Terminated", "Retired"]
    )

    # Show workforce dynamics section if hiring is enabled
    if include_hiring:
        render_workforce_dynamics(employees_df, enriched_df, data, start_year, end_year)
        st.divider()
        st.subheader("Attrition Details")

    if not has_attrition:
        st.info("No attrition data found. All employees are currently active.")
        if not include_hiring:
            render_kpis(enriched_df, employees_df)
        return

    # KPI Row (only if not showing workforce dynamics which has its own KPIs)
    if not include_hiring:
        render_kpis(enriched_df, employees_df)
        st.divider()

    # Charts row 1
    col1, col2 = st.columns(2)

    with col1:
        render_termination_reasons(employees_df)

    with col2:
        render_attrition_by_business_unit(enriched_df)

    # Charts row 2
    col3, col4 = st.columns(2)

    with col3:
        render_attrition_by_performance(enriched_df, data)

    with col4:
        render_attrition_by_tenure(enriched_df)

    # Charts row 3
    col5, col6 = st.columns(2)

    with col5:
        render_attrition_by_seniority(enriched_df)

    with col6:
        render_attrition_timeline(employees_df)


def render_workforce_dynamics(
    employees_df: pd.DataFrame,
    enriched_df: pd.DataFrame,
    data: dict[str, pd.DataFrame],
    start_year: int | None,
    end_year: int | None,
) -> None:
    """Render workforce dynamics section with hires vs attrition analysis."""
    st.subheader("Workforce Dynamics")

    if start_year is None:
        start_year = date.today().year - 5
    if end_year is None:
        end_year = date.today().year

    # Calculate yearly metrics
    yearly_data = calculate_yearly_workforce_metrics(employees_df, start_year, end_year)

    if yearly_data.empty:
        st.info("No hiring or attrition data available for the selected period.")
        return

    # KPI Row for Workforce Dynamics
    total_hires = yearly_data["hires"].sum()
    total_attrition = yearly_data["attrition"].sum()
    net_change = total_hires - total_attrition
    avg_growth_rate = yearly_data["growth_rate"].mean() * 100 if "growth_rate" in yearly_data else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Hires", f"{total_hires:,}")
    with col2:
        st.metric("Total Attrition", f"{total_attrition:,}")
    with col3:
        delta_color = "normal" if net_change >= 0 else "inverse"
        st.metric("Net Change", f"{net_change:+,}", delta_color=delta_color)
    with col4:
        st.metric("Avg Growth Rate", f"{avg_growth_rate:.1f}%")

    st.divider()

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        render_hires_vs_attrition_chart(yearly_data)

    with col2:
        render_headcount_trend_chart(yearly_data)

    # New hire demographics
    col3, col4 = st.columns(2)

    with col3:
        render_new_hire_seniority(employees_df, enriched_df, data, start_year, end_year)

    with col4:
        render_new_hire_business_unit(employees_df, enriched_df, data, start_year, end_year)


def calculate_yearly_workforce_metrics(
    employees_df: pd.DataFrame, start_year: int, end_year: int
) -> pd.DataFrame:
    """Calculate hires, attrition, and headcount by year."""
    years = list(range(start_year, end_year + 1))
    data = []

    for year in years:
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)

        # Count hires in this year
        hires = employees_df[
            (pd.to_datetime(employees_df["hire_date"]).dt.year == year)
        ].shape[0]

        # Count attrition in this year
        if "termination_date" in employees_df.columns:
            attrition = employees_df[
                (employees_df["termination_date"].notna())
                & (pd.to_datetime(employees_df["termination_date"]).dt.year == year)
            ].shape[0]
        else:
            attrition = 0

        # Calculate headcount at year end
        headcount = employees_df[
            (pd.to_datetime(employees_df["hire_date"]) <= pd.Timestamp(year_end))
            & (
                (employees_df["termination_date"].isna())
                | (pd.to_datetime(employees_df["termination_date"]) > pd.Timestamp(year_end))
            )
        ].shape[0]

        data.append({
            "year": year,
            "hires": hires,
            "attrition": attrition,
            "net_change": hires - attrition,
            "headcount": headcount,
        })

    df = pd.DataFrame(data)

    # Calculate growth rate
    if len(df) > 0:
        df["growth_rate"] = df["headcount"].pct_change().fillna(0)

    return df


def render_hires_vs_attrition_chart(yearly_data: pd.DataFrame) -> None:
    """Render grouped bar chart comparing hires and attrition by year."""
    fig = go.Figure()

    # Hires bars (green)
    fig.add_trace(go.Bar(
        name="Hires",
        x=yearly_data["year"],
        y=yearly_data["hires"],
        marker_color=COLORS["success"],
        text=yearly_data["hires"],
        textposition="auto",
    ))

    # Attrition bars (red)
    fig.add_trace(go.Bar(
        name="Attrition",
        x=yearly_data["year"],
        y=yearly_data["attrition"],
        marker_color=COLORS["error"],
        text=yearly_data["attrition"],
        textposition="auto",
    ))

    # Add net change annotations
    for _, row in yearly_data.iterrows():
        net = int(row["net_change"])
        color = COLORS["success"] if net >= 0 else COLORS["error"]
        fig.add_annotation(
            x=row["year"],
            y=max(row["hires"], row["attrition"]) + 2,
            text=f"Net: {net:+d}",
            showarrow=False,
            font=dict(size=10, color=color),
        )

    fig.update_layout(
        title="Hires vs Attrition by Year",
        barmode="group",
        xaxis_title="Year",
        yaxis_title="Count",
        plot_bgcolor=CHART_BGCOLOR,
        paper_bgcolor=CHART_PAPER_BGCOLOR,
        font=dict(color=CHART_FONT_COLOR),
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_headcount_trend_chart(yearly_data: pd.DataFrame) -> None:
    """Render headcount trend line chart."""
    fig = create_line_chart(
        yearly_data,
        x="year",
        y="headcount",
        title="Headcount Trend",
        markers=True,
    )
    fig.update_traces(line_color=COLORS["primary"])
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Headcount",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_new_hire_seniority(
    employees_df: pd.DataFrame,
    enriched_df: pd.DataFrame,
    data: dict[str, pd.DataFrame],
    start_year: int,
    end_year: int,
) -> None:
    """Render new hire seniority distribution."""
    # Get job assignments
    job_assignments = data.get("employee_job_assignment", pd.DataFrame())
    job_roles = data.get("job_role", pd.DataFrame())

    if job_assignments.empty or job_roles.empty:
        st.info("Job assignment data not available")
        return

    # Find employees hired in the simulation period
    new_hires = employees_df[
        pd.to_datetime(employees_df["hire_date"]).dt.year >= start_year
    ]

    if new_hires.empty:
        st.info("No new hires in the selected period")
        return

    # Get their initial job assignments (closest to hire date)
    new_hire_jobs = []
    for _, emp in new_hires.iterrows():
        emp_jobs = job_assignments[job_assignments["employee_id"] == emp["employee_id"]]
        if not emp_jobs.empty:
            # Get first job assignment
            first_job = emp_jobs.sort_values("start_date").iloc[0]
            new_hire_jobs.append(first_job)

    if not new_hire_jobs:
        st.info("No job assignment data for new hires")
        return

    new_hire_jobs_df = pd.DataFrame(new_hire_jobs)

    # Merge with job roles to get seniority
    if "seniority_level" not in new_hire_jobs_df.columns:
        new_hire_jobs_df = new_hire_jobs_df.merge(
            job_roles[["job_id", "seniority_level"]], on="job_id", how="left"
        )

    # Count by seniority
    seniority_counts = (
        new_hire_jobs_df.groupby("seniority_level")
        .size()
        .reset_index(name="count")
    )
    seniority_counts["seniority_level"] = seniority_counts["seniority_level"].astype(int)

    # Add labels
    seniority_labels = {
        1: "1-Entry",
        2: "2-Junior",
        3: "3-Mid",
        4: "4-Senior",
        5: "5-Executive",
    }
    seniority_counts["level_label"] = seniority_counts["seniority_level"].map(seniority_labels)
    label_colors = {seniority_labels[k]: v for k, v in SENIORITY_COLORS.items()}

    fig = create_bar_chart(
        seniority_counts,
        x="level_label",
        y="count",
        title="New Hire Seniority Distribution",
        color="level_label",
        color_discrete_map=label_colors,
    )
    fig.update_layout(showlegend=False, xaxis_title="Seniority Level", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True)


def render_new_hire_business_unit(
    employees_df: pd.DataFrame,
    enriched_df: pd.DataFrame,
    data: dict[str, pd.DataFrame],
    start_year: int,
    end_year: int,
) -> None:
    """Render new hire business unit distribution."""
    org_assignments = data.get("employee_org_assignment", pd.DataFrame())

    if org_assignments.empty:
        st.info("Organization data not available")
        return

    # Find employees hired in the simulation period
    new_hires = employees_df[
        pd.to_datetime(employees_df["hire_date"]).dt.year >= start_year
    ]

    if new_hires.empty:
        st.info("No new hires in the selected period")
        return

    # Get their org assignments
    new_hire_orgs = org_assignments[
        org_assignments["employee_id"].isin(new_hires["employee_id"])
    ]

    if new_hire_orgs.empty:
        st.info("No org assignment data for new hires")
        return

    # Get first org assignment per employee
    first_orgs = new_hire_orgs.sort_values("start_date").drop_duplicates("employee_id", keep="first")

    # business_unit is already in org_assignments
    if "business_unit" not in first_orgs.columns:
        st.info("Business unit data not available")
        return

    # Count by business unit
    bu_counts = (
        first_orgs.groupby("business_unit")
        .size()
        .reset_index(name="count")
    )

    fig = create_bar_chart(
        bu_counts,
        x="business_unit",
        y="count",
        title="New Hires by Business Unit",
        color="business_unit",
        color_discrete_map=BU_COLORS,
    )
    fig.update_layout(showlegend=False, xaxis_title="Business Unit", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True)


def render_kpis(enriched_df: pd.DataFrame, employees_df: pd.DataFrame) -> None:
    """Render KPI metrics row."""
    col1, col2, col3, col4, col5 = st.columns(5)

    total_employees = len(employees_df)
    status_counts = employees_df["employment_status"].value_counts()

    active_count = status_counts.get("Active", 0)
    terminated_count = status_counts.get("Terminated", 0)
    retired_count = status_counts.get("Retired", 0)

    # Attrition Rate
    with col1:
        attrition_rate = (terminated_count + retired_count) / total_employees * 100
        st.metric("Attrition Rate", f"{attrition_rate:.1f}%")

    # Active / Terminated / Retired counts
    with col2:
        st.metric("Active", active_count)

    with col3:
        st.metric("Terminated", terminated_count)

    with col4:
        st.metric("Retired", retired_count)

    with col5:
        # Voluntary vs Involuntary
        if "termination_reason" in employees_df.columns:
            termed_df = employees_df[employees_df["employment_status"].isin(["Terminated", "Retired"])]
            if len(termed_df) > 0:
                voluntary_reasons = [
                    "Resignation - Career Opportunity",
                    "Resignation - Personal Reasons",
                    "Resignation - Relocation",
                    "Retirement",
                ]
                voluntary = termed_df["termination_reason"].isin(voluntary_reasons).sum()
                involuntary = len(termed_df) - voluntary
                voluntary_pct = voluntary / len(termed_df) * 100
                st.metric("Voluntary", f"{voluntary_pct:.0f}%", delta=f"{involuntary} involuntary")
            else:
                st.metric("Voluntary", "N/A")
        else:
            st.metric("Voluntary", "N/A")


def render_termination_reasons(employees_df: pd.DataFrame) -> None:
    """Render termination reasons pie chart."""
    if "termination_reason" not in employees_df.columns:
        st.info("Termination reason data not available")
        return

    # Filter to only terminated/retired employees
    termed_df = employees_df[
        employees_df["employment_status"].isin(["Terminated", "Retired"])
    ].copy()

    if len(termed_df) == 0:
        st.info("No terminations to display")
        return

    reason_counts = (
        termed_df.groupby("termination_reason")
        .size()
        .reset_index(name="count")
    )

    fig = create_pie_chart(
        reason_counts,
        values="count",
        names="termination_reason",
        title="Termination Reasons",
        color_discrete_map=TERMINATION_REASON_COLORS,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_attrition_by_business_unit(enriched_df: pd.DataFrame) -> None:
    """Render attrition rate by business unit bar chart."""
    if "business_unit" not in enriched_df.columns or "employment_status" not in enriched_df.columns:
        st.info("Business unit or status data not available")
        return

    # Calculate attrition rate by business unit
    bu_stats = enriched_df.groupby("business_unit").agg(
        total=("employee_id", "count"),
        attrition=("employment_status", lambda x: (x.isin(["Terminated", "Retired"])).sum())
    ).reset_index()

    bu_stats["attrition_rate"] = bu_stats["attrition"] / bu_stats["total"] * 100

    fig = create_bar_chart(
        bu_stats,
        x="business_unit",
        y="attrition_rate",
        title="Attrition Rate by Business Unit",
        color="business_unit",
        color_discrete_map=BU_COLORS,
    )
    fig.update_layout(
        showlegend=False,
        xaxis_title="Business Unit",
        yaxis_title="Attrition Rate (%)"
    )
    st.plotly_chart(fig, use_container_width=True)


def render_attrition_by_performance(enriched_df: pd.DataFrame, data: dict[str, pd.DataFrame]) -> None:
    """Render attrition rate by performance rating bar chart."""
    if "employee_performance" not in data or "employment_status" not in enriched_df.columns:
        st.info("Performance or status data not available")
        return

    perf_df = data["employee_performance"]

    # Get latest performance rating per employee
    latest_perf = perf_df.sort_values("review_period_year", ascending=False).drop_duplicates(
        "employee_id", keep="first"
    )[["employee_id", "rating"]]

    # Merge with enriched data
    perf_enriched = enriched_df.merge(latest_perf, on="employee_id", how="left")

    # Filter out employees without ratings
    perf_enriched = perf_enriched[perf_enriched["rating"].notna()]

    if len(perf_enriched) == 0:
        st.info("No performance rating data available")
        return

    # Calculate attrition rate by rating
    rating_stats = perf_enriched.groupby("rating").agg(
        total=("employee_id", "count"),
        attrition=("employment_status", lambda x: (x.isin(["Terminated", "Retired"])).sum())
    ).reset_index()

    rating_stats["attrition_rate"] = rating_stats["attrition"] / rating_stats["total"] * 100
    rating_stats["rating"] = rating_stats["rating"].astype(int)

    fig = create_bar_chart(
        rating_stats,
        x="rating",
        y="attrition_rate",
        title="Attrition Rate by Performance Rating",
    )
    fig.update_layout(
        xaxis_title="Performance Rating (1-5)",
        yaxis_title="Attrition Rate (%)"
    )
    st.plotly_chart(fig, use_container_width=True)


def render_attrition_by_tenure(enriched_df: pd.DataFrame) -> None:
    """Render attrition rate by tenure bucket bar chart."""
    if "hire_date" not in enriched_df.columns or "employment_status" not in enriched_df.columns:
        st.info("Hire date or status data not available")
        return

    df = enriched_df.copy()
    today = date.today()

    # Calculate tenure in years
    df["tenure_years"] = df["hire_date"].apply(
        lambda x: (today - x).days / 365.25 if pd.notna(x) else 0
    )

    # Create tenure buckets
    def tenure_bucket(years):
        if years < 1:
            return "<1 year"
        elif years < 2:
            return "1-2 years"
        elif years < 5:
            return "2-5 years"
        elif years < 10:
            return "5-10 years"
        else:
            return "10+ years"

    df["tenure_bucket"] = df["tenure_years"].apply(tenure_bucket)

    # Calculate attrition rate by tenure bucket
    tenure_stats = df.groupby("tenure_bucket").agg(
        total=("employee_id", "count"),
        attrition=("employment_status", lambda x: (x.isin(["Terminated", "Retired"])).sum())
    ).reset_index()

    tenure_stats["attrition_rate"] = tenure_stats["attrition"] / tenure_stats["total"] * 100

    # Order the buckets
    bucket_order = ["<1 year", "1-2 years", "2-5 years", "5-10 years", "10+ years"]
    tenure_stats["tenure_bucket"] = pd.Categorical(
        tenure_stats["tenure_bucket"],
        categories=bucket_order,
        ordered=True
    )
    tenure_stats = tenure_stats.sort_values("tenure_bucket")

    fig = create_bar_chart(
        tenure_stats,
        x="tenure_bucket",
        y="attrition_rate",
        title="Attrition Rate by Tenure",
    )
    fig.update_layout(
        xaxis_title="Tenure",
        yaxis_title="Attrition Rate (%)"
    )
    st.plotly_chart(fig, use_container_width=True)


def render_attrition_by_seniority(enriched_df: pd.DataFrame) -> None:
    """Render attrition rate by seniority level bar chart."""
    if "seniority_level" not in enriched_df.columns or "employment_status" not in enriched_df.columns:
        st.info("Seniority level or status data not available")
        return

    # Filter out rows without seniority level
    df = enriched_df[enriched_df["seniority_level"].notna()].copy()

    if len(df) == 0:
        st.info("No seniority level data available")
        return

    # Calculate attrition rate by seniority
    seniority_stats = df.groupby("seniority_level").agg(
        total=("employee_id", "count"),
        attrition=("employment_status", lambda x: (x.isin(["Terminated", "Retired"])).sum())
    ).reset_index()

    seniority_stats["attrition_rate"] = seniority_stats["attrition"] / seniority_stats["total"] * 100
    seniority_stats["seniority_level"] = seniority_stats["seniority_level"].astype(int)

    # Add labels
    seniority_labels = {
        1: "1-Entry",
        2: "2-Junior",
        3: "3-Mid",
        4: "4-Senior",
        5: "5-Executive",
    }
    seniority_stats["level_label"] = seniority_stats["seniority_level"].map(seniority_labels)

    # Create color mapping for labels
    label_colors = {seniority_labels[k]: v for k, v in SENIORITY_COLORS.items()}

    fig = create_bar_chart(
        seniority_stats,
        x="level_label",
        y="attrition_rate",
        title="Attrition Rate by Seniority Level",
        color="level_label",
        color_discrete_map=label_colors,
    )
    fig.update_layout(
        showlegend=False,
        xaxis_title="Seniority Level",
        yaxis_title="Attrition Rate (%)"
    )
    st.plotly_chart(fig, use_container_width=True)


def render_attrition_timeline(employees_df: pd.DataFrame) -> None:
    """Render attrition timeline by year."""
    if "termination_date" not in employees_df.columns:
        st.info("Termination date data not available")
        return

    # Filter to terminated/retired employees with valid termination dates
    termed_df = employees_df[
        (employees_df["employment_status"].isin(["Terminated", "Retired"])) &
        (employees_df["termination_date"].notna())
    ].copy()

    if len(termed_df) == 0:
        st.info("No termination timeline data available")
        return

    # Extract year from termination date
    termed_df["termination_year"] = pd.to_datetime(termed_df["termination_date"]).dt.year

    # Count by year
    yearly_counts = (
        termed_df.groupby("termination_year")
        .size()
        .reset_index(name="count")
    )

    fig = create_line_chart(
        yearly_counts,
        x="termination_year",
        y="count",
        title="Attrition Timeline",
        markers=True,
    )
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Terminations"
    )
    st.plotly_chart(fig, use_container_width=True)
