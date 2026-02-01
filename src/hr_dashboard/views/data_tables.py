"""Data Tables view for raw data inspection before export."""

import streamlit as st
import pandas as pd


def render(data: dict[str, pd.DataFrame]) -> None:
    """
    Render the data tables inspection view.

    Args:
        data: HR data dictionary
    """
    st.subheader("Raw Data Inspection")
    st.caption("Inspect data before exporting to SAP BTP / HANA Cloud")

    # Table selector
    table_names = list(data.keys())
    selected_table = st.selectbox(
        "Select Table",
        options=table_names,
        format_func=lambda x: f"{x} ({len(data[x]):,} rows)",
    )

    if selected_table:
        df = data[selected_table]
        render_table_details(df, selected_table)


def render_table_details(df: pd.DataFrame, table_name: str) -> None:
    """Render detailed table information and preview."""
    # Table metrics row
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Rows", f"{len(df):,}")
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        st.metric("Memory", f"{memory_mb:.2f} MB")

    # Column info expander
    with st.expander("Column Information", expanded=False):
        col_info = []
        for col in df.columns:
            null_pct = (df[col].isna().sum() / len(df)) * 100 if len(df) > 0 else 0
            col_info.append({
                "Column": col,
                "Type": str(df[col].dtype),
                "Non-Null": f"{len(df) - df[col].isna().sum():,}",
                "Null %": f"{null_pct:.1f}%",
                "Unique": f"{df[col].nunique():,}",
            })

        col_df = pd.DataFrame(col_info)
        st.dataframe(col_df, use_container_width=True, hide_index=True)

    st.divider()

    # Search/filter section
    col1, col2 = st.columns([2, 1])

    with col1:
        search_text = st.text_input(
            "Search",
            placeholder="Filter rows containing this text...",
            key=f"search_{table_name}",
        )

    with col2:
        preview_rows = st.slider(
            "Preview Rows",
            min_value=10,
            max_value=100,
            value=25,
            step=5,
            key=f"rows_{table_name}",
        )

    # Filter data if search text provided
    display_df = df.copy()
    if search_text:
        mask = pd.Series([False] * len(display_df))
        for col in display_df.columns:
            try:
                mask |= display_df[col].astype(str).str.contains(
                    search_text, case=False, na=False
                )
            except Exception:
                pass
        display_df = display_df[mask]
        st.caption(f"Showing {len(display_df):,} of {len(df):,} rows matching '{search_text}'")

    # Data preview
    st.subheader("Data Preview")

    if len(display_df) == 0:
        st.info("No rows match the search criteria.")
    else:
        st.dataframe(
            display_df.head(preview_rows),
            use_container_width=True,
            hide_index=True,
        )

        if len(display_df) > preview_rows:
            st.caption(f"Showing first {preview_rows} of {len(display_df):,} rows")

    # Sample statistics for numeric columns
    numeric_cols = display_df.select_dtypes(include=["number"]).columns.tolist()
    if numeric_cols:
        with st.expander("Numeric Column Statistics", expanded=False):
            stats_df = display_df[numeric_cols].describe().T
            stats_df = stats_df.round(2)
            st.dataframe(stats_df, use_container_width=True)

    # Value counts for categorical columns
    categorical_cols = display_df.select_dtypes(include=["object", "category"]).columns.tolist()
    if categorical_cols:
        with st.expander("Categorical Value Counts", expanded=False):
            selected_cat_col = st.selectbox(
                "Select Column",
                options=categorical_cols,
                key=f"cat_col_{table_name}",
            )
            if selected_cat_col:
                value_counts = display_df[selected_cat_col].value_counts().head(20)
                st.bar_chart(value_counts)
