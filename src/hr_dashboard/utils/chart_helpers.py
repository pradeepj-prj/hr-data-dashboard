"""Chart helper utilities."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


# SAP Fiori-inspired color palette (Horizon Theme)
COLORS = {
    "primary": "#0A6ED1",      # SAP Blue
    "secondary": "#E9730C",    # SAP Gold/Accent
    "success": "#107E3E",      # SAP Green
    "warning": "#DF6E0C",      # SAP Orange
    "error": "#BB0000",        # SAP Red
    "info": "#0A6ED1",         # SAP Blue
}

BU_COLORS = {
    "Engineering": "#0A6ED1",  # SAP Blue
    "Sales": "#E9730C",        # SAP Gold
    "Corporate": "#107E3E",    # SAP Green
}

SENIORITY_COLORS = {
    1: "#BDD6F2",  # Lightest blue
    2: "#89B8E6",  # Light blue
    3: "#5599D9",  # Medium blue
    4: "#0A6ED1",  # SAP Blue
    5: "#085294",  # Dark blue
}

GENDER_COLORS = {
    "male": "#0A6ED1",    # SAP Blue
    "female": "#E9730C",  # SAP Gold
    "na": "#6A6D70",      # Neutral gray
}

ATTRITION_COLORS = {
    "Active": "#107E3E",      # SAP Green
    "Terminated": "#BB0000",  # SAP Red
    "Retired": "#DF6E0C",     # SAP Orange
}

TERMINATION_REASON_COLORS = {
    "Resignation - Career Opportunity": "#0A6ED1",
    "Resignation - Personal Reasons": "#5599D9",
    "Resignation - Relocation": "#89B8E6",
    "Retirement": "#DF6E0C",
    "Termination - Performance": "#BB0000",
    "Termination - Policy Violation": "#E34D4D",
    "Layoff - Restructuring": "#6A6D70",
    "Layoff - Cost Reduction": "#8D9094",
}

# SAP Fiori chart styling defaults
CHART_BGCOLOR = "#FFFFFF"
CHART_PAPER_BGCOLOR = "#FFFFFF"
CHART_FONT_COLOR = "#32363A"


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
        plot_bgcolor=CHART_BGCOLOR,
        paper_bgcolor=CHART_PAPER_BGCOLOR,
        font=dict(color=CHART_FONT_COLOR),
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
    fig.update_layout(
        paper_bgcolor=CHART_PAPER_BGCOLOR,
        font=dict(color=CHART_FONT_COLOR),
        margin=dict(l=40, r=40, t=60, b=40),
    )
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
        plot_bgcolor=CHART_BGCOLOR,
        paper_bgcolor=CHART_PAPER_BGCOLOR,
        font=dict(color=CHART_FONT_COLOR),
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
        plot_bgcolor=CHART_BGCOLOR,
        paper_bgcolor=CHART_PAPER_BGCOLOR,
        font=dict(color=CHART_FONT_COLOR),
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
    fig.update_layout(
        paper_bgcolor=CHART_PAPER_BGCOLOR,
        font=dict(color=CHART_FONT_COLOR),
        margin=dict(l=40, r=40, t=60, b=40),
    )
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
        plot_bgcolor=CHART_BGCOLOR,
        paper_bgcolor=CHART_PAPER_BGCOLOR,
        font=dict(color=CHART_FONT_COLOR),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig
