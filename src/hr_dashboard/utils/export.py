"""Data export utilities for HR data."""

import io
import zipfile
from typing import Literal

import pandas as pd

# Attempt to import pyarrow for parquet support
try:
    import pyarrow  # noqa: F401

    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False


def export_to_csv(df: pd.DataFrame) -> bytes:
    """
    Export DataFrame to CSV bytes.

    Args:
        df: DataFrame to export

    Returns:
        CSV data as bytes
    """
    return df.to_csv(index=False).encode("utf-8")


def export_to_parquet(df: pd.DataFrame) -> bytes:
    """
    Export DataFrame to Parquet bytes.

    Args:
        df: DataFrame to export

    Returns:
        Parquet data as bytes

    Raises:
        ImportError: If pyarrow is not installed
    """
    if not PARQUET_AVAILABLE:
        raise ImportError("pyarrow is required for Parquet export. Install with: pip install pyarrow")

    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, engine="pyarrow")
    return buffer.getvalue()


def create_zip_download(
    data: dict[str, pd.DataFrame],
    format: Literal["csv", "parquet"] = "parquet",
) -> bytes:
    """
    Create a ZIP file containing all tables.

    Args:
        data: Dictionary of table names to DataFrames
        format: Export format ("csv" or "parquet")

    Returns:
        ZIP file as bytes
    """
    buffer = io.BytesIO()
    extension = ".csv" if format == "csv" else ".parquet"
    export_func = export_to_csv if format == "csv" else export_to_parquet

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, df in data.items():
            file_data = export_func(df)
            zf.writestr(f"{name}{extension}", file_data)

    return buffer.getvalue()


def get_export_size_comparison(data: dict[str, pd.DataFrame]) -> dict[str, dict[str, float]]:
    """
    Calculate file sizes for different export formats.

    Args:
        data: Dictionary of table names to DataFrames

    Returns:
        Dictionary with format -> {table_name: size_mb}
    """
    sizes = {"csv": {}, "parquet": {}}

    for name, df in data.items():
        # CSV size
        csv_bytes = export_to_csv(df)
        sizes["csv"][name] = len(csv_bytes) / (1024 * 1024)

        # Parquet size (if available)
        if PARQUET_AVAILABLE:
            try:
                parquet_bytes = export_to_parquet(df)
                sizes["parquet"][name] = len(parquet_bytes) / (1024 * 1024)
            except Exception:
                sizes["parquet"][name] = 0

    return sizes


def get_total_export_size(data: dict[str, pd.DataFrame], format: Literal["csv", "parquet"]) -> float:
    """
    Calculate total export size in MB for a format.

    Args:
        data: Dictionary of table names to DataFrames
        format: Export format

    Returns:
        Total size in MB
    """
    sizes = get_export_size_comparison(data)
    return sum(sizes.get(format, {}).values())
