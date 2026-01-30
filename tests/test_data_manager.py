"""Tests for data_manager module."""

import pytest
import pandas as pd
from hr_data_generator import generate_hr_data


def test_hr_data_generation():
    """Test that hr_data_generator produces expected data structure."""
    data = generate_hr_data(n_employees=10, seed=42)

    # Check expected tables exist
    expected_tables = [
        "employee",
        "employee_job_assignment",
        "employee_org_assignment",
        "employee_compensation",
        "employee_performance",
        "organization_unit",
        "job_role",
        "location",
    ]

    for table in expected_tables:
        assert table in data, f"Missing table: {table}"
        assert isinstance(data[table], pd.DataFrame), f"{table} is not a DataFrame"

    # Check employee count
    assert len(data["employee"]) == 10


def test_employee_has_required_columns():
    """Test that employee table has required columns."""
    data = generate_hr_data(n_employees=5, seed=42)
    employees = data["employee"]

    required_cols = [
        "employee_id",
        "first_name",
        "last_name",
        "gender",
        "hire_date",
        "location_id",
        "employment_type",
    ]

    for col in required_cols:
        assert col in employees.columns, f"Missing column: {col}"


def test_job_role_reference_data():
    """Test job role reference data structure."""
    data = generate_hr_data(n_employees=5, seed=42)
    jobs = data["job_role"]

    required_cols = ["job_id", "job_title", "job_family", "seniority_level"]
    for col in required_cols:
        assert col in jobs.columns, f"Missing column: {col}"

    # Seniority levels should be 1-5
    assert jobs["seniority_level"].min() >= 1
    assert jobs["seniority_level"].max() <= 5


def test_location_has_coordinates():
    """Test that location data includes coordinates."""
    data = generate_hr_data(n_employees=5, seed=42)
    locations = data["location"]

    assert "latitude" in locations.columns
    assert "longitude" in locations.columns
    assert "city" in locations.columns
    assert "country" in locations.columns


def test_compensation_data():
    """Test compensation data structure."""
    data = generate_hr_data(n_employees=5, seed=42)
    comp = data["employee_compensation"]

    assert "employee_id" in comp.columns
    assert "annual_salary" in comp.columns
    assert "effective_date" in comp.columns

    # All salaries should be positive
    assert (comp["annual_salary"] > 0).all()


def test_performance_data():
    """Test performance data structure."""
    data = generate_hr_data(n_employees=5, seed=42)
    perf = data["employee_performance"]

    assert "employee_id" in perf.columns
    assert "rating" in perf.columns
    assert "review_year" in perf.columns

    # Ratings should be 1-5
    assert perf["rating"].min() >= 1
    assert perf["rating"].max() <= 5


def test_reproducibility_with_seed():
    """Test that same seed produces same data."""
    data1 = generate_hr_data(n_employees=10, seed=42)
    data2 = generate_hr_data(n_employees=10, seed=42)

    pd.testing.assert_frame_equal(data1["employee"], data2["employee"])


def test_different_seeds_produce_different_data():
    """Test that different seeds produce different data."""
    data1 = generate_hr_data(n_employees=10, seed=42)
    data2 = generate_hr_data(n_employees=10, seed=123)

    # At least one employee should be different
    assert not data1["employee"]["first_name"].equals(data2["employee"]["first_name"])
