"""Chart helper utilities."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


# Color palette for consistent theming
COLORS = {
    "primary": "#1f77b4",
    "secondary": "#ff7f0e",
    "success": "#2ca02c",
    "warning": "#d62728",
    "info": "#9467bd",
}

BU_COLORS = {
    "Engineering": "#1f77b4",
    "Sales": "#ff7f0e",
    "Corporate": "#2ca02c",
}

SENIORITY_COLORS = {
    1: "#c7e9c0",  # Entry - light green
    2: "#74c476",  # Junior - medium green
    3: "#31a354",  # Mid - green
    4: "#006d2c",  # Senior - dark green
    5: "#00441b",  # Executive - darkest green
}

GENDER_COLORS = {
    "male": "#1f77b4",
    "female": "#e377c2",
    "na": "#7f7f7f",
}

ATTRITION_COLORS = {
    "Active": "#2ca02c",      # Green
    "Terminated": "#d62728",  # Red
    "Retired": "#ff7f0e",     # Orange
}

TERMINATION_REASON_COLORS = {
    "Resignation - Career Opportunity": "#1f77b4",
    "Resignation - Personal Reasons": "#aec7e8",
    "Resignation - Relocation": "#ffbb78",
    "Retirement": "#ff7f0e",
    "Termination - Performance": "#d62728",
    "Termination - Policy Violation": "#ff9896",
    "Layoff - Restructuring": "#9467bd",
    "Layoff - Cost Reduction": "#c5b0d5",
}


def format_currency(value: float) -> str:
    """Format value as currency."""
    return f"${value:,.0f}"


def create_kpi_card(label: str, value: str | float, delta: str | None = None) -> dict:
    """
    Create KPI card data.

    Args:
        label: KPI label
        value: KPI value
        delta: Optional delta/change indicator

    Returns:
        Dictionary with KPI data
    """
    return {"label": label, "value": value, "delta": delta}


def create_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    color_discrete_map: dict | None = None,
    orientation: str = "v",
    text_auto: bool = True,
) -> go.Figure:
    """
    Create a styled bar chart.

    Args:
        df: DataFrame with data
        x: X-axis column
        y: Y-axis column
        title: Chart title
        color: Column for color encoding
        color_discrete_map: Color mapping dictionary
        orientation: 'v' for vertical, 'h' for horizontal
        text_auto: Show values on bars

    Returns:
        Plotly Figure
    """
    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        color=color,
        color_discrete_map=color_discrete_map,
        orientation=orientation,
        text_auto=text_auto,
    )
    fig.update_layout(
        showlegend=color is not None,
        plot_bgcolor="white",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def create_pie_chart(
    df: pd.DataFrame,
    values: str,
    names: str,
    title: str,
    color_discrete_map: dict | None = None,
    hole: float = 0.4,
) -> go.Figure:
    """
    Create a styled donut/pie chart.

    Args:
        df: DataFrame with data
        values: Column for values
        names: Column for names/labels
        title: Chart title
        color_discrete_map: Color mapping dictionary
        hole: Hole size for donut (0 for pie)

    Returns:
        Plotly Figure
    """
    fig = px.pie(
        df,
        values=values,
        names=names,
        title=title,
        color=names,
        color_discrete_map=color_discrete_map,
        hole=hole,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(margin=dict(l=40, r=40, t=60, b=40))
    return fig


def create_histogram(
    df: pd.DataFrame,
    x: str,
    title: str,
    nbins: int = 30,
    color: str | None = None,
) -> go.Figure:
    """
    Create a styled histogram.

    Args:
        df: DataFrame with data
        x: Column for histogram
        title: Chart title
        nbins: Number of bins
        color: Column for color encoding

    Returns:
        Plotly Figure
    """
    fig = px.histogram(
        df,
        x=x,
        title=title,
        nbins=nbins,
        color=color,
    )
    fig.update_layout(
        plot_bgcolor="white",
        margin=dict(l=40, r=40, t=60, b=40),
        bargap=0.1,
    )
    return fig


def create_box_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    color_discrete_map: dict | None = None,
) -> go.Figure:
    """
    Create a styled box plot.

    Args:
        df: DataFrame with data
        x: X-axis column (category)
        y: Y-axis column (values)
        title: Chart title
        color: Column for color encoding
        color_discrete_map: Color mapping dictionary

    Returns:
        Plotly Figure
    """
    fig = px.box(
        df,
        x=x,
        y=y,
        title=title,
        color=color,
        color_discrete_map=color_discrete_map,
    )
    fig.update_layout(
        plot_bgcolor="white",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def create_heatmap(
    df: pd.DataFrame,
    x: str,
    y: str,
    z: str,
    title: str,
    color_scale: str = "Blues",
) -> go.Figure:
    """
    Create a styled heatmap.

    Args:
        df: DataFrame with data (should be pivoted or aggregated)
        x: X-axis column
        y: Y-axis column
        z: Values column
        title: Chart title
        color_scale: Plotly color scale name

    Returns:
        Plotly Figure
    """
    # Pivot if needed
    pivot_df = df.pivot_table(values=z, index=y, columns=x, aggfunc="mean")

    fig = px.imshow(
        pivot_df,
        title=title,
        color_continuous_scale=color_scale,
        aspect="auto",
    )
    fig.update_layout(margin=dict(l=40, r=40, t=60, b=40))
    return fig


def create_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    markers: bool = True,
) -> go.Figure:
    """
    Create a styled line chart.

    Args:
        df: DataFrame with data
        x: X-axis column
        y: Y-axis column
        title: Chart title
        color: Column for color encoding
        markers: Show markers on line

    Returns:
        Plotly Figure
    """
    fig = px.line(
        df,
        x=x,
        y=y,
        title=title,
        color=color,
        markers=markers,
    )
    fig.update_layout(
        plot_bgcolor="white",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig
