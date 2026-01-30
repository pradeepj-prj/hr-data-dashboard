"""Organization network graph page using Pyvis."""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import networkx as nx
from pyvis.network import Network
import tempfile
import os

from hr_dashboard.data_manager import enrich_employee_data
from hr_dashboard.utils.chart_helpers import SENIORITY_COLORS, BU_COLORS


def render(data: dict[str, pd.DataFrame]) -> None:
    """
    Render the organization network graph page.

    Args:
        data: Filtered HR data dictionary
    """
    employees_df = data["employee"]
    if len(employees_df) == 0:
        st.warning("No employees match the current filters.")
        return

    enriched_df = enrich_employee_data(data)

    st.subheader("Organization Hierarchy - Network View")

    # Configuration options
    col1, col2, col3 = st.columns(3)

    with col1:
        color_by = st.selectbox(
            "Color nodes by",
            options=["Seniority Level", "Business Unit"],
            index=0,
            key="network_color",
        )

    with col2:
        physics_enabled = st.checkbox("Enable physics simulation", value=True)

    with col3:
        show_labels = st.checkbox("Show employee names", value=True)

    # Limit for performance
    max_nodes = st.slider(
        "Maximum nodes to display",
        min_value=10,
        max_value=min(200, len(enriched_df)),
        value=min(50, len(enriched_df)),
        help="Limit nodes for better performance",
    )

    # Build and render network
    render_manager_network(enriched_df, color_by, physics_enabled, show_labels, max_nodes)


def render_manager_network(
    enriched_df: pd.DataFrame,
    color_by: str,
    physics_enabled: bool,
    show_labels: bool,
    max_nodes: int,
) -> None:
    """Render the manager hierarchy network graph."""
    # Check required columns
    if "manager_id" not in enriched_df.columns:
        st.warning("Manager hierarchy data not available")
        return

    # Limit data for performance
    df = enriched_df.head(max_nodes).copy()

    # Create NetworkX graph
    G = nx.DiGraph()

    # Add nodes
    for _, row in df.iterrows():
        emp_id = row["employee_id"]

        # Determine node color
        if color_by == "Seniority Level" and "seniority_level" in row:
            level = row.get("seniority_level", 3)
            if pd.notna(level):
                color = SENIORITY_COLORS.get(int(level), "#999999")
            else:
                color = "#999999"
        elif color_by == "Business Unit" and "business_unit" in row:
            bu = row.get("business_unit", "")
            color = BU_COLORS.get(bu, "#999999")
        else:
            color = "#999999"

        # Node label
        if show_labels:
            label = f"{row.get('first_name', '')} {row.get('last_name', '')}"
        else:
            label = emp_id

        # Node title (hover text)
        title = f"""
        <b>{row.get('first_name', '')} {row.get('last_name', '')}</b><br>
        ID: {emp_id}<br>
        Job: {row.get('job_title', 'N/A')}<br>
        Org: {row.get('org_name', 'N/A')}<br>
        Level: {row.get('seniority_level', 'N/A')}<br>
        """

        # Node size based on seniority
        level = row.get("seniority_level", 3)
        if pd.notna(level):
            size = 10 + int(level) * 5
        else:
            size = 15

        G.add_node(
            emp_id,
            label=label,
            title=title,
            color=color,
            size=size,
        )

    # Add edges (manager relationships)
    employee_ids = set(df["employee_id"])
    for _, row in df.iterrows():
        emp_id = row["employee_id"]
        manager_id = row.get("manager_id")

        if pd.notna(manager_id) and manager_id in employee_ids:
            G.add_edge(manager_id, emp_id)

    # Create Pyvis network
    net = Network(
        height="600px",
        width="100%",
        directed=True,
        bgcolor="#ffffff",
        font_color="#000000",
    )

    # Configure physics
    if physics_enabled:
        net.force_atlas_2based(
            gravity=-50,
            central_gravity=0.01,
            spring_length=100,
            spring_strength=0.08,
            damping=0.4,
        )
    else:
        net.toggle_physics(False)

    # Add NetworkX graph to Pyvis
    net.from_nx(G)

    # Configure options
    net.set_options("""
    {
        "nodes": {
            "font": {
                "size": 12,
                "face": "arial"
            },
            "borderWidth": 2
        },
        "edges": {
            "arrows": {
                "to": {
                    "enabled": true,
                    "scaleFactor": 0.5
                }
            },
            "color": {
                "color": "#cccccc",
                "highlight": "#000000"
            },
            "smooth": {
                "type": "continuous"
            }
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "navigationButtons": true,
            "keyboard": true
        }
    }
    """)

    # Save and display
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        net.save_graph(f.name)
        html_content = open(f.name, "r").read()
        os.unlink(f.name)

    components.html(html_content, height=650, scrolling=True)

    # Legend
    st.divider()
    render_legend(color_by)


def render_legend(color_by: str) -> None:
    """Render color legend."""
    st.caption("Color Legend:")

    if color_by == "Seniority Level":
        cols = st.columns(5)
        labels = {1: "Entry", 2: "Junior", 3: "Mid", 4: "Senior", 5: "Executive"}
        for i, (level, label) in enumerate(labels.items()):
            color = SENIORITY_COLORS[level]
            with cols[i]:
                st.markdown(
                    f'<div style="background-color: {color}; '
                    f'padding: 5px; text-align: center; border-radius: 3px;">'
                    f'{level} - {label}</div>',
                    unsafe_allow_html=True,
                )
    else:
        cols = st.columns(len(BU_COLORS))
        for i, (bu, color) in enumerate(BU_COLORS.items()):
            with cols[i]:
                st.markdown(
                    f'<div style="background-color: {color}; color: white; '
                    f'padding: 5px; text-align: center; border-radius: 3px;">'
                    f'{bu}</div>',
                    unsafe_allow_html=True,
                )
