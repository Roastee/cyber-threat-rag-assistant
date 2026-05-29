"""
Reusable UI components — Small widgets used across pages.

Provides helper functions for rendering:
    - Metric cards
    - Status badges
    - Dividers
    - Info/warning cards
"""

import streamlit as st


def render_metric_card(label: str, value: str | int, color: str = "#00FF88") -> str:
    """Return HTML for a single metric card.

    Args:
        label: Description text below the value.
        value: The numeric or text value to display.
        color: Accent color for the value.

    Returns:
        HTML string for the metric card.
    """
    return (
        '<div class="metric-card">'
        f'<div class="metric-value" style="color: {color};">{value}</div>'
        f'<div class="metric-label">{label}</div>'
        "</div>"
    )


def render_status_badge(text: str, status: str = "online") -> str:
    """Return HTML for a status badge.

    Args:
        text: Badge text.
        status: "online" or "offline".

    Returns:
        HTML string for the badge.
    """
    css_class = "badge-online" if status == "online" else ""
    dot_class = "online" if status == "online" else "offline"
    return (
        f'<span class="header-badge {css_class}">'
        f'<span class="status-dot {dot_class}"></span>'
        f"{text}</span>"
    )


def render_divider() -> None:
    """Render a styled horizontal divider."""
    st.markdown(
        '<div class="cyber-divider"></div>',
        unsafe_allow_html=True,
    )


def render_info_card(icon: str, title: str, description: str) -> None:
    """Render a centered info/placeholder card.

    Args:
        icon: Emoji icon to display.
        title: Card title.
        description: Card description text.
    """
    st.markdown(
        f'<div class="info-card">'
        f'<div class="icon">{icon}</div>'
        f"<h3>{title}</h3>"
        f"<p>{description}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )
