"""
Header component — App banner with status indicators.

Renders the top banner with:
    - App title and subtitle
    - Online status badge (pulsing green dot)
    - Version badge
"""

import streamlit as st

from src.core.config import app_config


def render_header() -> None:
    """Render the application header with status badges."""
    st.markdown(
        f"""
        <div class="app-header">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem;">
                <div>
                    <h1>{app_config.APP_TITLE}</h1>
                    <p class="subtitle">{app_config.APP_DESCRIPTION}</p>
                </div>
                <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                    <span class="header-badge badge-online">
                        <span class="status-dot online"></span>
                        SYSTEM ONLINE
                    </span>
                    <span class="header-badge badge-version">
                        v{app_config.APP_VERSION}
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
